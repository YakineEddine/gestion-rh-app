"""
Tests d'integration pour les transitions de statut des contrats.
Couvre les 10 scénarios demandés.
"""
import os
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token, hash_password
from app.database import Base, get_db
from app.main import app
from app.models.models import (
    AuditActionEnum,
    AuditLog,
    Contrat,
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


def create_user(db, email, prenom, nom, role=RoleEnum.RH):
    user = Utilisateur(
        nom=nom,
        prenom=prenom,
        email=email,
        mot_de_passe_hash=hash_password("Password123!"),
        matricule=f"MAT-{email.split('@')[0]}",
        role=role,
        est_actif=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_contrat(db, employe_id, statut="Brouillon"):
    c = Contrat(
        reference="CTR-2026-0001",
        type_contrat=TypeContratEnum.CDI.value,
        date_creation=date.today(),
        date_debut=date.today(),
        date_fin=None,
        salaire_mensuel=3500,
        statut=statut,
        employe_id=employe_id,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# ─── 1. BROUILLON → ACTIF ✅ ──────────────────────────────────────────────────
def test_transition_brouillon_to_actif(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="Brouillon")

    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    with patch("app.routes.contrats.send_email", return_value=True):
        resp = client.put(
            f"/api/contrats/{contrat.id}",
            json={"statut": "Actif"},
            headers={"Authorization": f"Bearer {token_rh}"},
        )
        assert resp.status_code == 200
        assert resp.json()["statut"] == "Actif"

    db.refresh(contrat)
    assert contrat.statut == "Actif"


# ─── 2. ACTIF → SUSPENDU ✅ ───────────────────────────────────────────────────
def test_transition_actif_to_suspendu(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="Actif")

    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    resp = client.put(
        f"/api/contrats/{contrat.id}",
        json={"statut": "Suspendu"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 200
    assert resp.json()["statut"] == "Suspendu"

    db.refresh(contrat)
    assert contrat.statut == "Suspendu"


# ─── 3. SUSPENDU → ACTIF ✅ ───────────────────────────────────────────────────
def test_transition_suspendu_to_actif(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="Suspendu")

    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    with patch("app.routes.contrats.send_email", return_value=True):
        resp = client.put(
            f"/api/contrats/{contrat.id}",
            json={"statut": "Actif"},
            headers={"Authorization": f"Bearer {token_rh}"},
        )
        assert resp.status_code == 200
        assert resp.json()["statut"] == "Actif"

    db.refresh(contrat)
    assert contrat.statut == "Actif"


# ─── 4. ACTIF → TERMINÉ ✅ ────────────────────────────────────────────────────
def test_transition_actif_to_termine(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="Actif")

    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    resp = client.put(
        f"/api/contrats/{contrat.id}",
        json={"statut": "Terminé"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 200
    assert resp.json()["statut"] == "Terminé"

    db.refresh(contrat)
    assert contrat.statut == "Terminé"


# ─── 5. ACTIF → BROUILLON ❌ (Interdit) ───────────────────────────────────────
def test_transition_actif_to_brouillon_forbidden(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="Actif")

    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    resp = client.put(
        f"/api/contrats/{contrat.id}",
        json={"statut": "Brouillon"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 400
    assert "non autorisée" in resp.json()["detail"]

    # Vérifier que le statut n'a PAS été modifié en base
    db.refresh(contrat)
    assert contrat.statut == "Actif"


# ─── 6. TERMINÉ → BROUILLON ❌ (Interdit) ─────────────────────────────────────
def test_transition_termine_to_brouillon_forbidden(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="Terminé")

    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    resp = client.put(
        f"/api/contrats/{contrat.id}",
        json={"statut": "Brouillon"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 400
    assert "non autorisée" in resp.json()["detail"]

    db.refresh(contrat)
    assert contrat.statut == "Terminé"


# ─── 7. EXPIRÉ → ACTIF ❌ (Interdit) ──────────────────────────────────────────
def test_transition_expire_to_actif_forbidden(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="Expiré")

    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    resp = client.put(
        f"/api/contrats/{contrat.id}",
        json={"statut": "Actif"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 400
    assert "non autorisée" in resp.json()["detail"]

    db.refresh(contrat)
    assert contrat.statut == "Expiré"


# ─── 8. Vérifier qu'une tentative interdite ne modifie pas les autres champs ──
def test_forbidden_transition_does_not_modify_database(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="Actif")
    original_salary = contrat.salaire_mensuel

    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    # Tentative d'envoyer statut Brouillon avec un salaire modifié
    resp = client.put(
        f"/api/contrats/{contrat.id}",
        json={"statut": "Brouillon", "salaire_mensuel": 9999},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 400

    # Vérification en base
    db.refresh(contrat)
    assert contrat.statut == "Actif"
    assert contrat.salaire_mensuel == original_salary


# ─── 9. Vérifier l'audit des transitions valides ──────────────────────────────
def test_valid_status_transition_creates_audit_log(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="Brouillon")

    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    with patch("app.routes.contrats.send_email", return_value=True):
        client.put(
            f"/api/contrats/{contrat.id}",
            json={"statut": "Actif"},
            headers={"Authorization": f"Bearer {token_rh}"},
        )

    # Vérifier l'audit log
    log = db.query(AuditLog).filter(
        AuditLog.entite_id == contrat.id,
        AuditLog.action == AuditActionEnum.STATUS_CHANGE.value,
    ).first()
    assert log is not None
    assert log.anciennes_valeurs == {"statut": "Brouillon"}
    assert log.nouvelles_valeurs == {"statut": "Actif"}


# ─── 10. Vérifier qu'aucune régression n'est introduite ───────────────────────
def test_no_regression_on_contract_creation_and_fields_update(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)

    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    # Création normale -> statut Brouillon initial
    resp_create = client.post(
        "/api/contrats/",
        json={
            "employe_id": emp.id,
            "type_contrat": "CDI",
            "date_debut": date.today().isoformat(),
            "salaire_mensuel": 4000,
        },
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp_create.status_code == 201
    contrat_id = resp_create.json()["id"]
    assert resp_create.json()["statut"] == "Brouillon"

    # Modification de salaire sans toucher au statut
    resp_update = client.put(
        f"/api/contrats/{contrat_id}",
        json={"salaire_mensuel": 4500},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp_update.status_code == 200
    assert resp_update.json()["salaire_mensuel"] == 4500
    assert resp_update.json()["statut"] == "Brouillon"
