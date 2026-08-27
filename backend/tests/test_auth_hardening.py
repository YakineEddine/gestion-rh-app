"""
Tests d'integration pour le renforcement de l'authentification.
Couvrent les scenarios obligatoires A-P de l'etape 4.
"""
import secrets
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_reset_token,
    hash_password,
    _token_hash,
)
from app.database import Base, get_db
from app.main import app
from app.models.models import (
    AuditActionEnum,
    AuditEntiteEnum,
    AuditLog,
    RefreshToken,
    ResetToken,
    RoleEnum,
    Utilisateur,
)

import os
from dotenv import load_dotenv

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


def create_user(
    db,
    email="test@example.com",
    role=RoleEnum.RH,
    password="Admin123!",
    est_actif=True,
    prenom="Test",
    nom="User",
):
    user = Utilisateur(
        email=email,
        prenom=prenom,
        nom=nom,
        mot_de_passe_hash=hash_password(password),
        matricule=f"TST-{secrets.token_hex(4).upper()}",
        role=role,
        est_actif=est_actif,
        login_attempts=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "mot_de_passe": password})


# ---------------------------------------------------------------------------
# A. Connexion correcte -> LOGIN enregistre
# ---------------------------------------------------------------------------
def test_login_success_and_audit(client, db):
    email = "success@example.com"
    password = "Admin123!"
    create_user(db, email=email, password=password)

    resp = login(client, email, password)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email

    audit = db.query(AuditLog).filter(AuditLog.action == AuditActionEnum.LOGIN.value).first()
    assert audit is not None
    assert "Connexion" in audit.description


# ---------------------------------------------------------------------------
# B. Mauvais mot de passe -> LOGIN_FAILED enregistre
# ---------------------------------------------------------------------------
def test_login_failed_audit(client, db):
    email = "failed@example.com"
    create_user(db, email=email, password="Admin123!")

    resp = login(client, email, "WrongPass1!")
    assert resp.status_code == 401
    assert "incorrect" in resp.json()["detail"].lower() or "email" in resp.json()["detail"].lower()

    audit = db.query(AuditLog).filter(
        AuditLog.action == AuditActionEnum.LOGIN_FAILED.value
    ).first()
    assert audit is not None


# ---------------------------------------------------------------------------
# C. 5 mauvais mots de passe -> compte temporairement bloque
# D. Tentative pendant le blocage -> connexion refusee
# ---------------------------------------------------------------------------
def test_account_lockout_after_failed_attempts(client, db):
    email = "lockout@example.com"
    create_user(db, email=email, password="Admin123!")

    for i in range(5):
        resp = login(client, email, f"WrongPass{i}!")
        assert resp.status_code == 401

    # 5eme echec doit declencher le blocage
    last = login(client, email, "WrongPass5!")
    assert last.status_code == 401
    assert "bloqu" in last.json()["detail"].lower()

    lock_audit = db.query(AuditLog).filter(
        AuditLog.action == AuditActionEnum.ACCOUNT_LOCKED.value
    ).first()
    assert lock_audit is not None

    # D: tentative supplémentaire pendant le blocage -> refusee
    resp = login(client, email, "Admin123!")
    assert resp.status_code == 401
    assert "bloqu" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# E. Connexion correcte apres expiration du blocage
# ---------------------------------------------------------------------------
def test_login_after_lockout_expires(client, db):
    email = "unlock@example.com"
    password = "Admin123!"
    user = create_user(db, email=email, password=password)

    # Simuler 5 echecs puis un blocage passe
    for i in range(5):
        login(client, email, f"WrongPass{i}!")

    # Forcer l'expiration du blocage
    user.locked_until = datetime.utcnow() - timedelta(minutes=1)
    db.commit()

    resp = login(client, email, password)
    assert resp.status_code == 200

    unlock_audit = db.query(AuditLog).filter(
        AuditLog.action == AuditActionEnum.ACCOUNT_UNLOCKED.value
    ).first()
    assert unlock_audit is not None

    # Le compteur est reinitialise
    db.refresh(user)
    assert user.login_attempts == 0
    assert user.locked_until is None


# ---------------------------------------------------------------------------
# F. JWT expire -> acces refuse
# ---------------------------------------------------------------------------
def test_expired_jwt_rejected(client, db):
    user = create_user(db, email="expired@example.com")
    expired_token = create_access_token(
        data={"sub": user.email, "role": user.role.value},
        expires_delta=timedelta(seconds=-1),
    )

    resp = client.get(
        "/api/employes",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# G. JWT invalide -> acces refuse
# ---------------------------------------------------------------------------
def test_invalid_jwt_rejected(client):
    resp = client.get(
        "/api/employes",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# H. Utilisateur desactive -> connexion refusee et JWT valide refuse
# ---------------------------------------------------------------------------
def test_disabled_user_cannot_login_or_use_token(client, db):
    email = "disabled@example.com"
    password = "Admin123!"
    user = create_user(db, email=email, password=password)

    token = create_access_token(data={"sub": user.email, "role": user.role.value})

    # Acces avec un JWT valide mais compte desactive -> refuse
    user.est_actif = False
    db.commit()

    resp = client.get(
        "/api/employes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401

    resp_login = login(client, email, password)
    assert resp_login.status_code == 401


# ---------------------------------------------------------------------------
# I. Réinitialisation du mot de passe -> e-mail envoyé (message generique)
# ---------------------------------------------------------------------------
@patch("app.routes.auth.envoyer_email_reinitialisation", return_value=True)
def test_forgot_password_sends_email_and_generic_message(mock_email, client, db):
    email = "forgot@example.com"
    create_user(db, email=email)

    resp = client.post("/api/auth/forgot-password", json={"email": email})
    assert resp.status_code == 200
    data = resp.json()
    assert "réinitialisation" in data["message"].lower()
    mock_email.assert_called_once()

    # Un e-mail inexistant retourne le meme message generique
    resp_unknown = client.post("/api/auth/forgot-password", json={"email": "unknown@example.com"})
    assert resp_unknown.status_code == 200
    assert resp_unknown.json()["message"] == data["message"]


# ---------------------------------------------------------------------------
# J. Token de reset expire -> refuse
# ---------------------------------------------------------------------------
def test_reset_token_expired_rejected(client, db):
    user = create_user(db, email="resetexp@example.com")
    raw_token = f"rp_{secrets.token_urlsafe(32)}"
    token_hash = _token_hash(raw_token)

    rt = ResetToken(
        utilisateur_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() - timedelta(minutes=1),
    )
    db.add(rt)
    db.commit()

    resp = client.post("/api/auth/reset-password", json={
        "token": raw_token,
        "nouveau_mot_de_passe": "NewPass123!",
    })
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# K. Token de reset deja utilise -> refuse
# ---------------------------------------------------------------------------
def test_reset_token_already_used_rejected(client, db):
    user = create_user(db, email="resetused@example.com")
    raw_token = create_reset_token(user, db)

    # Marquer comme utilise
    rt = db.query(ResetToken).filter(ResetToken.utilisateur_id == user.id).first()
    rt.used_at = datetime.utcnow()
    db.commit()

    resp = client.post("/api/auth/reset-password", json={
        "token": raw_token,
        "nouveau_mot_de_passe": "NewPass123!",
    })
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# L. Nouveau mot de passe non conforme -> refuse
# ---------------------------------------------------------------------------
def test_reset_password_weak_rejected(client, db):
    user = create_user(db, email="weakreset@example.com")
    raw_token = create_reset_token(user, db)

    resp = client.post("/api/auth/reset-password", json={
        "token": raw_token,
        "nouveau_mot_de_passe": "12345",
    })
    assert resp.status_code in (400, 422)


# ---------------------------------------------------------------------------
# M. Nouveau mot de passe conforme -> accepte
# ---------------------------------------------------------------------------
def test_reset_password_strong_accepted(client, db):
    email = "strongreset@example.com"
    user = create_user(db, email=email, password="OldPass123!")
    raw_token = create_reset_token(user, db)
    new_password = "NewStrongPass1!"

    resp = client.post("/api/auth/reset-password", json={
        "token": raw_token,
        "nouveau_mot_de_passe": new_password,
    })
    assert resp.status_code == 200

    audit = db.query(AuditLog).filter(
        AuditLog.action == AuditActionEnum.PASSWORD_RESET.value
    ).first()
    assert audit is not None

    # Connexion avec le nouveau mot de passe fonctionne
    resp_login = login(client, email, new_password)
    assert resp_login.status_code == 200


# ---------------------------------------------------------------------------
# N. Aucun mot de passe, JWT ou token sensible ne doit apparaitre dans l'audit
# ---------------------------------------------------------------------------
def test_audit_does_not_contain_secrets(client, db):
    email = "secrets@example.com"
    password = "Admin123!"
    user = create_user(db, email=email, password=password)

    # Produire quelques evenements
    login(client, email, password)
    login(client, email, "WrongPass1!")

    raw_reset = create_reset_token(user, db)
    client.post("/api/auth/reset-password", json={
        "token": raw_reset,
        "nouveau_mot_de_passe": "NewAuditPass1!",
    })

    # Recuperer tous les audits et verifier qu'aucun secret n'y figure
    logs = db.query(AuditLog).all()
    audit_text = " ".join(
        str(log.description) + " " + str(log.anciennes_valeurs) + " " + str(log.nouvelles_valeurs)
        for log in logs
    )

    forbidden = [
        password,
        "Admin123!",
        "NewAuditPass1!",
        user.mot_de_passe_hash,
        raw_reset,
    ]
    for secret in forbidden:
        assert secret not in audit_text, f"Secret trouve dans l'audit: {secret[:20]}"

    # Les JWT et refresh tokens ne doivent pas etre dans l'audit non plus
    assert "access_token" not in audit_text
    assert "refresh_token" not in audit_text


# ---------------------------------------------------------------------------
# O. Verifier qu'ADMIN/RH/EMPLOYE conservent leurs permissions actuelles
# ---------------------------------------------------------------------------
def test_role_permissions_preserved(client, db):
    rh_user = create_user(db, email="rh@example.com", role=RoleEnum.RH)
    emp_user = create_user(db, email="emp@example.com", role=RoleEnum.EMPLOYE)
    admin_user = create_user(db, email="admin@example.com", role=RoleEnum.ADMIN)

    # RH peut lister les employes
    rh_token = create_access_token(data={"sub": rh_user.email, "role": rh_user.role.value})
    resp = client.get("/api/employes", headers={"Authorization": f"Bearer {rh_token}"})
    assert resp.status_code == 200

    # EMPLOYE ne peut pas acceder aux employes (route reservee RH)
    emp_token = create_access_token(data={"sub": emp_user.email, "role": emp_user.role.value})
    resp = client.get("/api/employes", headers={"Authorization": f"Bearer {emp_token}"})
    assert resp.status_code == 403

    # ADMIN peut acceder a l'audit (RH ou ADMIN)
    admin_token = create_access_token(data={"sub": admin_user.email, "role": admin_user.role.value})
    resp = client.get("/api/audit", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200

    # EMPLOYE ne peut pas acceder a l'audit
    resp = client.get("/api/audit", headers={"Authorization": f"Bearer {emp_token}"})
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# P. Verifier qu'aucun module existant n'est casse
# ---------------------------------------------------------------------------
def test_existing_modules_not_broken(client, db):
    rh_user = create_user(db, email="modules@example.com", role=RoleEnum.RH)
    token = create_access_token(data={"sub": rh_user.email, "role": rh_user.role.value})
    headers = {"Authorization": f"Bearer {token}"}

    # Employes
    resp = client.get("/api/employes", headers=headers)
    assert resp.status_code == 200

    # Contrats
    resp = client.get("/api/contrats", headers=headers)
    assert resp.status_code == 200

    # Articles CRUD
    resp = client.post("/api/articles", json={
        "code": "ART-TEST-01",
        "titre": "Article test",
        "contenu_par_defaut": "Contenu",
    }, headers=headers)
    assert resp.status_code == 201
    article_id = resp.json()["id"]

    resp = client.get("/api/articles", headers=headers)
    assert resp.status_code == 200

    resp = client.get(f"/api/articles/{article_id}", headers=headers)
    assert resp.status_code == 200

    resp = client.put(f"/api/articles/{article_id}", json={
        "code": "ART-TEST-01",
        "titre": "Article modifie",
        "contenu_par_defaut": "Contenu modifie",
    }, headers=headers)
    assert resp.status_code == 200

    resp = client.delete(f"/api/articles/{article_id}", headers=headers)
    assert resp.status_code == 200

    # Audit
    resp = client.get("/api/audit", headers=headers)
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Refresh token : rotation et revocation
# ---------------------------------------------------------------------------
def test_refresh_token_rotation_and_logout_revocation(client, db):
    email = "refresh@example.com"
    password = "Admin123!"
    create_user(db, email=email, password=password)

    resp = login(client, email, password)
    assert resp.status_code == 200
    refresh = resp.json()["refresh_token"]

    # Refresh valide -> nouvel access token + nouveau refresh token
    resp = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    new_refresh = resp.json()["refresh_token"]

    # Ancien refresh token doit etre invalide (rotation)
    resp = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 401

    # Nouveau refresh token fonctionne
    resp = client.post("/api/auth/refresh", json={"refresh_token": new_refresh})
    assert resp.status_code == 200
    access = resp.json()["access_token"]

    # Logout revoque les refresh tokens
    resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {access}"})
    assert resp.status_code == 200

    # Tous les refresh tokens sont revoques
    resp = client.post("/api/auth/refresh", json={"refresh_token": resp.json().get("refresh_token", new_refresh)})
    assert resp.status_code == 401
