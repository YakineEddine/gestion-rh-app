"""
Tests d'intégration pour les transitions de statut des contrats (nouveaux statuts).
Couvre l'ensemble des scénarios demandés dans la spécification du workflow :
1. Création d'un CDD en BROUILLON
2. BROUILLON → COMMUNIQUE_EN_COURS
3. COMMUNIQUE_EN_COURS → SIGNE
4. SIGNE → ACTIF (avec email d'activation)
5. CDD ACTIF → FIN_CDD
6. CDI ACTIF → DEMISSION_CDI
7. FIN_CDD → INACTIF
8. DEMISSION_CDI → INACTIF
9. CDI sans date de fin obligatoire
10. CDD sans date de fin refusé
11. ACTIF → BROUILLON refusé (interdit)
12. Audit / Historique : STATUS_CHANGE bien enregistré
13. Incompatibilités de type : FIN_CDD sur CDI interdit, DEMISSION_CDI sur CDD interdit
14. PAS_DISCUTE disponible et transitions valides
15. Génération Word (DOCX) fonctionnelle
16. Espace Employé : sécurité, affichage et téléchargement
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
    StatutContratEnum,
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


import uuid


def create_contrat(db, employe_id, statut="BROUILLON", type_contrat="CDI", date_fin=None):
    ref = f"CTR-2026-{uuid.uuid4().hex[:6].upper()}"
    c = Contrat(
        reference=ref,
        type_contrat=type_contrat,
        date_creation=date.today(),
        date_debut=date.today(),
        date_fin=date_fin,
        salaire_mensuel=3500,
        statut=statut,
        employe_id=employe_id,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# ─── 1. Création d'un CDD en BROUILLON ─────────────────────────────────────────
def test_creation_cdd_brouillon(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    date_fin_cdd = (date.today() + timedelta(days=180)).isoformat()

    resp = client.post(
        "/api/contrats/",
        json={
            "employe_id": emp.id,
            "type_contrat": "CDD",
            "date_debut": date.today().isoformat(),
            "date_fin": date_fin_cdd,
            "salaire_mensuel": 3200,
        },
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 201
    assert resp.json()["statut"] in ["BROUILLON", "Brouillon"]
    assert resp.json()["type_contrat"] == "CDD"


# ─── 2. BROUILLON → COMMUNIQUE_EN_COURS ───────────────────────────────────────
def test_transition_brouillon_to_communique(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="BROUILLON")
    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    resp = client.put(
        f"/api/contrats/{contrat.id}",
        json={"statut": "COMMUNIQUE_EN_COURS"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 200
    assert resp.json()["statut"] == "COMMUNIQUE_EN_COURS"

    db.refresh(contrat)
    assert contrat.statut == "COMMUNIQUE_EN_COURS"


# ─── 3. COMMUNIQUE_EN_COURS → SIGNE ───────────────────────────────────────────
def test_transition_communique_to_signe(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="COMMUNIQUE_EN_COURS")
    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    resp = client.put(
        f"/api/contrats/{contrat.id}",
        json={"statut": "SIGNE"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 200
    assert resp.json()["statut"] == "SIGNE"

    db.refresh(contrat)
    assert contrat.statut == "SIGNE"


# ─── 4. SIGNE → ACTIF (avec email d'activation) ───────────────────────────────
def test_transition_signe_to_actif_with_email(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="SIGNE")
    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    with patch("app.routes.contrats.send_email", return_value=True) as mock_email:
        resp = client.put(
            f"/api/contrats/{contrat.id}",
            json={"statut": "ACTIF"},
            headers={"Authorization": f"Bearer {token_rh}"},
        )
        assert resp.status_code == 200
        assert resp.json()["statut"] == "ACTIF"
        assert mock_email.called

    db.refresh(contrat)
    assert contrat.statut == "ACTIF"


# ─── 5. CDD ACTIF → FIN_CDD ───────────────────────────────────────────────────
def test_cdd_actif_to_fin_cdd(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    date_fin = date.today() + timedelta(days=90)
    contrat = create_contrat(db, emp.id, statut="ACTIF", type_contrat="CDD", date_fin=date_fin)
    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    resp = client.put(
        f"/api/contrats/{contrat.id}",
        json={"statut": "FIN_CDD"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 200
    assert resp.json()["statut"] == "FIN_CDD"

    db.refresh(contrat)
    assert contrat.statut == "FIN_CDD"


# ─── 6. CDI ACTIF → DEMISSION_CDI ─────────────────────────────────────────────
def test_cdi_actif_to_demission_cdi(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="ACTIF", type_contrat="CDI")
    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    resp = client.put(
        f"/api/contrats/{contrat.id}",
        json={"statut": "DEMISSION_CDI"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 200
    assert resp.json()["statut"] == "DEMISSION_CDI"

    db.refresh(contrat)
    assert contrat.statut == "DEMISSION_CDI"


# ─── 7. FIN_CDD → INACTIF ─────────────────────────────────────────────────────
def test_fin_cdd_to_inactif(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    date_fin = date.today() + timedelta(days=90)
    contrat = create_contrat(db, emp.id, statut="FIN_CDD", type_contrat="CDD", date_fin=date_fin)
    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    resp = client.put(
        f"/api/contrats/{contrat.id}",
        json={"statut": "INACTIF"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 200
    assert resp.json()["statut"] == "INACTIF"

    db.refresh(contrat)
    assert contrat.statut == "INACTIF"


# ─── 8. DEMISSION_CDI → INACTIF ───────────────────────────────────────────────
def test_demission_cdi_to_inactif(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="DEMISSION_CDI", type_contrat="CDI")
    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    resp = client.put(
        f"/api/contrats/{contrat.id}",
        json={"statut": "INACTIF"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 200
    assert resp.json()["statut"] == "INACTIF"

    db.refresh(contrat)
    assert contrat.statut == "INACTIF"


# ─── 9. CDI : pas de date de fin obligatoire ──────────────────────────────────
def test_cdi_no_end_date_required(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    resp = client.post(
        "/api/contrats/",
        json={
            "employe_id": emp.id,
            "type_contrat": "CDI",
            "date_debut": date.today().isoformat(),
            "salaire_mensuel": 4000,
        },
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 201
    assert resp.json()["date_fin"] is None


# ─── 10. CDD : date de fin obligatoire ─────────────────────────────────────────
def test_cdd_end_date_mandatory(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    resp = client.post(
        "/api/contrats/",
        json={
            "employe_id": emp.id,
            "type_contrat": "CDD",
            "date_debut": date.today().isoformat(),
            "date_fin": None,
            "salaire_mensuel": 3000,
        },
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code in [400, 422]


# ─── 11. ACTIF → BROUILLON ❌ (Interdit) ───────────────────────────────────────
def test_actif_to_brouillon_forbidden(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="ACTIF")
    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    resp = client.put(
        f"/api/contrats/{contrat.id}",
        json={"statut": "BROUILLON"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 400
    assert "non autorisée" in resp.json()["detail"]

    db.refresh(contrat)
    assert contrat.statut == "ACTIF"


# ─── 12. Incompatibilités de type de contrat ─────────────────────────────────
def test_type_and_status_incompatibilities(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    # CDI ne peut pas passer à FIN_CDD
    cdi = create_contrat(db, emp.id, statut="ACTIF", type_contrat="CDI")
    resp = client.put(
        f"/api/contrats/{cdi.id}",
        json={"statut": "FIN_CDD"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 400
    assert "Fin CDD" in resp.json()["detail"]

    # CDD ne peut pas passer à DEMISSION_CDI
    cdd = create_contrat(db, emp.id, statut="ACTIF", type_contrat="CDD", date_fin=date.today() + timedelta(days=60))
    resp = client.put(
        f"/api/contrats/{cdd.id}",
        json={"statut": "DEMISSION_CDI"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 400
    assert "Démission" in resp.json()["detail"]


# ─── 13. Audit / Historique : STATUS_CHANGE ───────────────────────────────────
def test_status_change_creates_audit_log(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="BROUILLON")
    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    client.put(
        f"/api/contrats/{contrat.id}",
        json={"statut": "COMMUNIQUE_EN_COURS"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )

    log = db.query(AuditLog).filter(
        AuditLog.entite_id == contrat.id,
        AuditLog.action == AuditActionEnum.STATUS_CHANGE.value,
    ).first()
    assert log is not None
    assert log.anciennes_valeurs == {"statut": "BROUILLON"}
    assert log.nouvelles_valeurs == {"statut": "COMMUNIQUE_EN_COURS"}


# ─── 14. PAS_DISCUTE disponible ───────────────────────────────────────────────
def test_pas_discute_workflow(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="BROUILLON")
    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    # BROUILLON -> PAS_DISCUTE
    resp = client.put(
        f"/api/contrats/{contrat.id}",
        json={"statut": "PAS_DISCUTE"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 200
    assert resp.json()["statut"] == "PAS_DISCUTE"

    # PAS_DISCUTE -> INACTIF
    resp2 = client.put(
        f"/api/contrats/{contrat.id}",
        json={"statut": "INACTIF"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["statut"] == "INACTIF"


# ─── 15. Génération Word (DOCX) ───────────────────────────────────────────────
def test_generer_word_contrat(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    contrat = create_contrat(db, emp.id, statut="BROUILLON")
    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    resp = client.post(
        f"/api/contrats/{contrat.id}/generer-word",
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert len(resp.content) > 0


# ─── 16. Espace Employé : sécurité et accès contrat ───────────────────────────
def test_espace_employe_contrat_visibility(db, client):
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    token_emp = create_access_token({"sub": emp.email, "role": emp.role.value})

    # Contrat en BROUILLON ne doit PAS être listé
    brouillon = create_contrat(db, emp.id, statut="BROUILLON")
    resp = client.get("/api/mon-espace/contrats", headers={"Authorization": f"Bearer {token_emp}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 0

    # Contrat ACTIF doit être listé
    brouillon.statut = "ACTIF"
    db.commit()

    resp2 = client.get("/api/mon-espace/contrats", headers={"Authorization": f"Bearer {token_emp}"})
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1
    assert resp2.json()[0]["reference"] == brouillon.reference

    # Téléchargement par l'employé
    resp3 = client.get(
        f"/api/mon-espace/contrats/{brouillon.id}/telecharger",
        headers={"Authorization": f"Bearer {token_emp}"},
    )
    assert resp3.status_code == 200
    assert len(resp3.content) > 0
