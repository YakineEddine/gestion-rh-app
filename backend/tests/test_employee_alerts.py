"""
Tests d'integration pour le centre d'alertes personnel Employe et les alertes d'expiration de contrats.
Couvrent les 10 scenarios obligatoires.
"""
import os
from datetime import date, datetime, timedelta
from unittest.mock import patch

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.notification_service import (
    compter_non_lues,
    marquer_comme_lue,
    marquer_toutes_comme_lues,
    verifier_alertes_contrats,
)
from app.core.security import create_access_token, hash_password
from app.database import Base, get_db
from app.main import app
from app.models.models import (
    AuditActionEnum,
    AuditLog,
    Contrat,
    Notification,
    NotificationPrioriteEnum,
    NotificationTypeEnum,
    RoleEnum,
    TypeContratEnum,
    Utilisateur,
)

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

TEST_DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/gestion_rh_test_db"

test_engine = create_engine(TEST_DB_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(scope="function")
def db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db):
    with TestClient(app) as c:
        yield c


def create_user(db, email, prenom, nom, role=RoleEnum.EMPLOYE, matricule=None):
    user = Utilisateur(
        nom=nom,
        prenom=prenom,
        email=email,
        mot_de_passe_hash=hash_password("Password123!"),
        matricule=matricule or f"MAT-{email.split('@')[0]}",
        role=role,
        est_actif=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_contrat(db, employe_id, type_contrat, date_debut, date_fin, statut="Actif", reference=None):
    ref = reference or f"CTR-{type_contrat}-{date_debut.year}-{employe_id}"
    c = Contrat(
        reference=ref,
        type_contrat=type_contrat.value if isinstance(type_contrat, TypeContratEnum) else type_contrat,
        date_creation=date.today() - timedelta(days=2),
        date_debut=date_debut,
        date_fin=date_fin,
        salaire_mensuel=3000,
        statut=statut,
        employe_id=employe_id,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# ─── 1. Employé A possède un CDD expirant dans 7 jours ────────────────────────
def test_cdd_expiring_7_days_creates_rh_and_employee_alerts_and_emails(db):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp_a = create_user(db, "empa@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)

    date_fin_7j = date.today() + timedelta(days=7)
    contrat = create_contrat(db, emp_a.id, TypeContratEnum.CDD, date.today() - timedelta(days=90), date_fin_7j, statut="Actif")

    with patch("app.core.notification_service.send_email", return_value=True) as mock_send_email:
        nb_crees = verifier_alertes_contrats(db)

        assert nb_crees == 2  # 1 pour RH, 1 pour Employé A
        assert mock_send_email.call_count == 2

        # Vérifier notification RH
        notif_rh = db.query(Notification).filter(Notification.utilisateur_id == rh.id).first()
        assert notif_rh is not None
        assert notif_rh.type == NotificationTypeEnum.CONTRACT_EXPIRING.value
        assert notif_rh.priorite == NotificationPrioriteEnum.CRITICAL.value

        # Vérifier notification Employé A
        notif_emp = db.query(Notification).filter(Notification.utilisateur_id == emp_a.id).first()
        assert notif_emp is not None
        assert notif_emp.type == NotificationTypeEnum.CONTRACT_EXPIRING.value
        assert notif_emp.priorite == NotificationPrioriteEnum.CRITICAL.value
        assert contrat.reference in notif_emp.message


# ─── 2. Employé B ne doit voir aucune alerte concernant Employé A ─────────────
def test_employee_b_cannot_see_employee_a_alerts(db, client):
    create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp_a = create_user(db, "empa@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    emp_b = create_user(db, "empb@test.com", "Bob", "Martin", role=RoleEnum.EMPLOYE)

    date_fin_7j = date.today() + timedelta(days=7)
    create_contrat(db, emp_a.id, TypeContratEnum.CDD, date.today() - timedelta(days=90), date_fin_7j, statut="Actif")

    with patch("app.core.notification_service.send_email", return_value=True):
        verifier_alertes_contrats(db)

    token_b = create_access_token({"sub": emp_b.email, "role": emp_b.role.value})
    resp = client.get("/api/notifications/", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0
    assert data["unread_count"] == 0


# ─── 3. Employé A ouvre /notifications dans son espace ─────────────────────────
def test_employee_a_sees_only_own_notifications(db, client):
    create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp_a = create_user(db, "empa@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)

    date_fin_7j = date.today() + timedelta(days=7)
    create_contrat(db, emp_a.id, TypeContratEnum.CDD, date.today() - timedelta(days=90), date_fin_7j, statut="Actif")

    with patch("app.core.notification_service.send_email", return_value=True):
        verifier_alertes_contrats(db)

    token_a = create_access_token({"sub": emp_a.email, "role": emp_a.role.value})
    resp = client.get("/api/notifications/", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["type"] == NotificationTypeEnum.CONTRACT_EXPIRING.value
    assert data["unread_count"] == 1


# ─── 4. Un contrat BROUILLON proche de l'expiration ───────────────────────────
def test_draft_contract_does_not_send_alert_or_email_to_employee(db):
    create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp_a = create_user(db, "empa@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)

    date_fin_5j = date.today() + timedelta(days=5)
    create_contrat(db, emp_a.id, TypeContratEnum.CDD, date.today() - timedelta(days=90), date_fin_5j, statut="Brouillon")

    with patch("app.core.notification_service.send_email", return_value=True) as mock_send:
        verifier_alertes_contrats(db)

        # L'employé ne doit recevoir AUCUNE notification
        notifs_emp = db.query(Notification).filter(Notification.utilisateur_id == emp_a.id).all()
        assert len(notifs_emp) == 0

        # Vérifier qu'aucun email n'a été envoyé à l'employé
        for call_args in mock_send.call_args_list:
            assert call_args[1].get("to") != emp_a.email


# ─── 5. CDI sans date_fin -> aucune alerte d'expiration ───────────────────────
def test_cdi_without_end_date_generates_no_expiration_alert(db):
    create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp_a = create_user(db, "empa@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)

    create_contrat(db, emp_a.id, TypeContratEnum.CDI, date.today() - timedelta(days=365), None, statut="Actif")

    with patch("app.core.notification_service.send_email", return_value=True) as mock_send:
        nb_crees = verifier_alertes_contrats(db)
        assert nb_crees == 0
        assert mock_send.call_count == 0
        assert db.query(Notification).count() == 0


# ─── 6. Double exécution du moteur -> aucun doublon de notification ou email ──
def test_deduplication_prevents_duplicate_notifications_and_emails(db):
    create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp_a = create_user(db, "empa@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)

    date_fin_7j = date.today() + timedelta(days=7)
    create_contrat(db, emp_a.id, TypeContratEnum.CDD, date.today() - timedelta(days=90), date_fin_7j, statut="Actif")

    with patch("app.core.notification_service.send_email", return_value=True) as mock_send:
        # Première exécution
        nb1 = verifier_alertes_contrats(db)
        assert nb1 == 2
        assert mock_send.call_count == 2

        # Deuxième exécution immédiate
        mock_send.reset_mock()
        nb2 = verifier_alertes_contrats(db)
        assert nb2 == 0
        assert mock_send.call_count == 0

        # Vérifier nombre total de notifications
        assert db.query(Notification).count() == 2


# ─── 7. Marquer une alerte comme lue -> compteur mis à jour ───────────────────
def test_mark_notification_as_read_updates_unread_count(db, client):
    create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp_a = create_user(db, "empa@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)

    date_fin_7j = date.today() + timedelta(days=7)
    create_contrat(db, emp_a.id, TypeContratEnum.CDD, date.today() - timedelta(days=90), date_fin_7j, statut="Actif")

    with patch("app.core.notification_service.send_email", return_value=True):
        verifier_alertes_contrats(db)

    token_a = create_access_token({"sub": emp_a.email, "role": emp_a.role.value})

    # Avant marquage
    resp_unread = client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {token_a}"})
    assert resp_unread.json()["unread_count"] == 1

    notif_emp = db.query(Notification).filter(Notification.utilisateur_id == emp_a.id).first()

    # Marquer comme lue
    resp_read = client.post(f"/api/notifications/{notif_emp.id}/read", headers={"Authorization": f"Bearer {token_a}"})
    assert resp_read.status_code == 200
    assert resp_read.json()["est_lue"] is True

    # Après marquage
    resp_unread2 = client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {token_a}"})
    assert resp_unread2.json()["unread_count"] == 0


# ─── 8. Employé tente de marquer la notification d'un autre utilisateur ───────
def test_employee_cannot_mark_other_users_notification_as_read(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp_a = create_user(db, "empa@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    emp_b = create_user(db, "empb@test.com", "Bob", "Martin", role=RoleEnum.EMPLOYE)

    date_fin_7j = date.today() + timedelta(days=7)
    create_contrat(db, emp_a.id, TypeContratEnum.CDD, date.today() - timedelta(days=90), date_fin_7j, statut="Actif")

    with patch("app.core.notification_service.send_email", return_value=True):
        verifier_alertes_contrats(db)

    notif_emp_a = db.query(Notification).filter(Notification.utilisateur_id == emp_a.id).first()
    notif_rh = db.query(Notification).filter(Notification.utilisateur_id == rh.id).first()

    token_b = create_access_token({"sub": emp_b.email, "role": emp_b.role.value})

    # Bob tente de marquer la notification d'Alice
    resp1 = client.post(f"/api/notifications/{notif_emp_a.id}/read", headers={"Authorization": f"Bearer {token_b}"})
    assert resp1.status_code == 404

    # Bob tente de marquer la notification du RH
    resp2 = client.post(f"/api/notifications/{notif_rh.id}/read", headers={"Authorization": f"Bearer {token_b}"})
    assert resp2.status_code == 404


# ─── 9. CDD déjà expiré -> CONTRACT_EXPIRED + email employé ───────────────────
def test_expired_contract_generates_critical_alert_and_email_to_employee(db):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp_a = create_user(db, "empa@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)

    date_fin_passe = date.today() - timedelta(days=3)
    create_contrat(db, emp_a.id, TypeContratEnum.CDD, date.today() - timedelta(days=180), date_fin_passe, statut="Actif")

    with patch("app.core.notification_service.send_email", return_value=True) as mock_send:
        nb_crees = verifier_alertes_contrats(db)
        assert nb_crees == 2  # 1 RH, 1 Employé
        assert mock_send.call_count == 2

        notif_emp = db.query(Notification).filter(Notification.utilisateur_id == emp_a.id).first()
        assert notif_emp is not None
        assert notif_emp.type == NotificationTypeEnum.CONTRACT_EXPIRED.value
        assert notif_emp.priorite == NotificationPrioriteEnum.CRITICAL.value


# ─── 10. Vérifier que les alertes RH existantes continuent de fonctionner ─────
def test_rh_alerts_functionality_preserved(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp_a = create_user(db, "empa@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)

    date_fin_15j = date.today() + timedelta(days=15)
    create_contrat(db, emp_a.id, TypeContratEnum.STAGE, date.today() - timedelta(days=30), date_fin_15j, statut="Actif")

    with patch("app.core.notification_service.send_email", return_value=True):
        verifier_alertes_contrats(db)

    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})
    resp = client.get("/api/notifications/", headers={"Authorization": f"Bearer {token_rh}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["priorite"] == NotificationPrioriteEnum.WARNING.value
    assert "CTR-STAGE" in data["items"][0]["titre"]
