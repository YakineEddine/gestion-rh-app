"""
Tests d'integration pour la securisation du profil employe (lecture seule pour EMPLOYE, gestion RH/ADMIN).
Couvrent les 8 scenarios obligatoires.
"""
import os
from datetime import date
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
    RoleEnum,
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


def create_user(db, email, prenom, nom, role=RoleEnum.EMPLOYE, matricule=None, telephone="12345678"):
    user = Utilisateur(
        nom=nom,
        prenom=prenom,
        email=email,
        mot_de_passe_hash=hash_password("Password123!"),
        matricule=matricule or f"MAT-{email.split('@')[0]}",
        role=role,
        telephone=telephone,
        departement="Informatique",
        poste="Développeur",
        est_actif=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ─── 1. EMPLOYE consulte son profil -> visible en lecture ─────────────────────
def test_employee_can_read_own_profile(db, client):
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    token = create_access_token({"sub": emp.email, "role": emp.role.value})

    resp = client.get("/api/mon-espace/profil", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "emp@test.com"
    assert data["nom"] == "Dupont"
    assert data["prenom"] == "Alice"
    assert data["telephone"] == "12345678"


# ─── 2. EMPLOYE tente directement PUT /api/mon-espace/profil -> 403 Forbidden ─
def test_employee_cannot_update_profile_via_mon_espace(db, client):
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE, telephone="12345678")
    token = create_access_token({"sub": emp.email, "role": emp.role.value})

    resp = client.put(
        "/api/mon-espace/profil",
        json={"telephone": "99999999", "email": "nouveau@test.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403

    # Vérifier qu'aucune modification n'a eu lieu en base
    db.refresh(emp)
    assert emp.telephone == "12345678"
    assert emp.email == "emp@test.com"


# ─── 3. RH modifie les coordonnées d'un employé -> SUCCÈS ─────────────────────
def test_rh_can_modify_employee_coordinates(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE, telephone="12345678")
    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    resp = client.put(
        f"/api/employes/{emp.id}",
        json={"telephone": "22334455", "poste": "Lead Développeur"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["telephone"] == "22334455"
    assert data["poste"] == "Lead Développeur"

    db.refresh(emp)
    assert emp.telephone == "22334455"
    assert emp.poste == "Lead Développeur"


# ─── 4. ADMIN modifie les coordonnées d'un employé -> SUCCÈS ──────────────────
def test_admin_can_modify_employee_coordinates(db, client):
    admin = create_user(db, "admin@test.com", "Super", "Admin", role=RoleEnum.ADMIN)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE, telephone="12345678")
    token_admin = create_access_token({"sub": admin.email, "role": admin.role.value})

    resp = client.put(
        f"/api/employes/{emp.id}",
        json={"telephone": "77889900", "departement": "Direction Technique"},
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["telephone"] == "77889900"
    assert data["departement"] == "Direction Technique"

    db.refresh(emp)
    assert emp.telephone == "77889900"
    assert emp.departement == "Direction Technique"


# ─── 5. EMPLOYE tente de modifier son rôle via PUT /api/employes/{id} -> 403 ──
def test_employee_cannot_escalate_role(db, client):
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    token = create_access_token({"sub": emp.email, "role": emp.role.value})

    resp = client.put(
        f"/api/employes/{emp.id}",
        json={"role": "ADMIN"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403

    db.refresh(emp)
    assert emp.role == RoleEnum.EMPLOYE


# ─── 6. EMPLOYE tente de modifier son statut via PUT /api/employes/{id} -> 403 
def test_employee_cannot_modify_account_status(db, client):
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)
    token = create_access_token({"sub": emp.email, "role": emp.role.value})

    resp = client.put(
        f"/api/employes/{emp.id}",
        json={"est_actif": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403

    db.refresh(emp)
    assert emp.est_actif is True


# ─── 7. EMPLOYE tente de modifier son matricule via PUT /api/employes/{id} ────
def test_employee_cannot_modify_matricule(db, client):
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE, matricule="MAT-ORIGINAL")
    token = create_access_token({"sub": emp.email, "role": emp.role.value})

    resp = client.put(
        f"/api/employes/{emp.id}",
        json={"matricule": "MAT-HACKED"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403

    db.refresh(emp)
    assert emp.matricule == "MAT-ORIGINAL"


# ─── 8. Vérifier l'audit et l'absence de faux logs sur tentative interdite ─────
def test_audit_records_rh_update_and_no_fake_update_on_forbidden(db, client):
    rh = create_user(db, "rh@test.com", "RH", "Admin", role=RoleEnum.RH)
    emp = create_user(db, "emp@test.com", "Alice", "Dupont", role=RoleEnum.EMPLOYE)

    token_emp = create_access_token({"sub": emp.email, "role": emp.role.value})
    token_rh = create_access_token({"sub": rh.email, "role": rh.role.value})

    # Tentative interdite par l'employé
    client.put(
        "/api/mon-espace/profil",
        json={"telephone": "99999999"},
        headers={"Authorization": f"Bearer {token_emp}"},
    )

    # Vérifier qu'aucun audit UPDATE n'a été créé
    assert db.query(AuditLog).filter(
        AuditLog.entite_id == emp.id,
        AuditLog.action == AuditActionEnum.UPDATE.value,
    ).count() == 0

    # Modification légitime par le RH
    client.put(
        f"/api/employes/{emp.id}",
        json={"telephone": "55667788"},
        headers={"Authorization": f"Bearer {token_rh}"},
    )

    # Vérifier qu'un audit UPDATE a été créé pour le RH
    audit = db.query(AuditLog).filter(
        AuditLog.entite_id == emp.id,
        AuditLog.action == AuditActionEnum.UPDATE.value,
    ).first()
    assert audit is not None
    assert audit.utilisateur_id == rh.id
    assert "telephone" in audit.nouvelles_valeurs
