"""
Tests d'integration pour l'authentification avec verification Google reCAPTCHA v2.
Couvrent les 10 scenarios obligatoires.
"""
import os
from datetime import date
from unittest.mock import patch

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
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


def create_user(db, email, password="Password123!", role=RoleEnum.RH):
    user = Utilisateur(
        nom="TestNom",
        prenom="TestPrenom",
        email=email,
        mot_de_passe_hash=hash_password(password),
        matricule=f"MAT-{email.split('@')[0]}",
        role=role,
        est_actif=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ─── 1. Login sans CAPTCHA → 400 Refusé ──────────────────────────────────────
def test_login_without_captcha_token_rejected(db, client):
    create_user(db, "rh@test.com", "Password123!")

    resp = client.post(
        "/api/auth/login",
        json={"email": "rh@test.com", "mot_de_passe": "Password123!"},
    )
    assert resp.status_code == 400
    assert "robot" in resp.json()["detail"]


# ─── 2. Login avec CAPTCHA valide + mauvais mot de passe → 401 & LOGIN_FAILED ─
def test_login_with_valid_captcha_and_wrong_password_creates_audit(db, client):
    user = create_user(db, "rh@test.com", "Password123!")

    with patch("app.core.recaptcha_service.verify_recaptcha_token", return_value=(True, "")):
        resp = client.post(
            "/api/auth/login",
            json={
                "email": "rh@test.com",
                "mot_de_passe": "WrongPassword999!",
                "recaptcha_token": "valid_token_sample",
            },
        )
        assert resp.status_code == 401

    # Audit log LOGIN_FAILED doit exister
    audit = db.query(AuditLog).filter(
        AuditLog.utilisateur_id == user.id,
        AuditLog.action == AuditActionEnum.LOGIN_FAILED.value,
    ).first()
    assert audit is not None


# ─── 3. Login avec CAPTCHA valide + bon mot de passe → 200 & JWT ─────────────
def test_login_with_valid_captcha_and_correct_password_success(db, client):
    user = create_user(db, "rh@test.com", "Password123!")

    with patch("app.core.recaptcha_service.verify_recaptcha_token", return_value=(True, "")):
        resp = client.post(
            "/api/auth/login",
            json={
                "email": "rh@test.com",
                "mot_de_passe": "Password123!",
                "recaptcha_token": "valid_token_sample",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "rh@test.com"


# ─── 4. CAPTCHA invalide → 403 Refusé ─────────────────────────────────────────
def test_login_with_invalid_captcha_rejected_403(db, client):
    create_user(db, "rh@test.com", "Password123!")

    with patch("app.core.recaptcha_service.verify_recaptcha_token", return_value=(False, "invalid")):
        resp = client.post(
            "/api/auth/login",
            json={
                "email": "rh@test.com",
                "mot_de_passe": "Password123!",
                "recaptcha_token": "invalid_fake_token",
            },
        )
        assert resp.status_code == 403
        assert "échoué" in resp.json()["detail"]

    # Aucun échec de mot de passe ne doit être consigné dans l'audit
    assert db.query(AuditLog).filter(AuditLog.action == AuditActionEnum.LOGIN_FAILED.value).count() == 0


# ─── 5. CAPTCHA expiré (timeout-or-duplicate) → 400 Refusé ────────────────────
def test_login_with_expired_captcha_rejected_400(db, client):
    create_user(db, "rh@test.com", "Password123!")

    with patch("app.core.recaptcha_service.verify_recaptcha_token", return_value=(False, "timeout-or-duplicate")):
        resp = client.post(
            "/api/auth/login",
            json={
                "email": "rh@test.com",
                "mot_de_passe": "Password123!",
                "recaptcha_token": "expired_token_sample",
            },
        )
        assert resp.status_code == 400
        assert "expiré" in resp.json()["detail"]


# ─── 6. Appel direct sans token (chaîne vide ou None) → 400 Refusé ───────────
def test_direct_api_call_empty_token_rejected(db, client):
    create_user(db, "rh@test.com", "Password123!")

    resp = client.post(
        "/api/auth/login",
        json={"email": "rh@test.com", "mot_de_passe": "Password123!", "recaptcha_token": "  "},
    )
    assert resp.status_code == 400
    assert "robot" in resp.json()["detail"]


# ─── 7. Vérifier que RECAPTCHA_SECRET_KEY reste secrète (non exposée) ─────────
def test_recaptcha_secret_key_not_exposed_in_public_routes(client):
    # Les routes publiques ne doivent jamais retourner la clé secrète
    resp = client.get("/docs")
    assert "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe" not in resp.text


# ─── 8. Vérifier l'absence de données sensibles dans les logs d'audit ─────────
def test_audit_logs_contain_no_secrets_no_passwords_no_captcha_tokens(db, client):
    user = create_user(db, "rh@test.com", "Password123!")

    with patch("app.core.recaptcha_service.verify_recaptcha_token", return_value=(True, "")):
        client.post(
            "/api/auth/login",
            json={
                "email": "rh@test.com",
                "mot_de_passe": "Password123!",
                "recaptcha_token": "SECRET_CAPTCHA_TOKEN_12345",
            },
        )

    logs = db.query(AuditLog).all()
    for log in logs:
        text_repr = f"{log.description} {log.anciennes_valeurs} {log.nouvelles_valeurs}"
        assert "SECRET_CAPTCHA_TOKEN" not in text_repr
        assert "Password123!" not in text_repr


# ─── 9. Protection brute-force conservée avec reCAPTCHA ───────────────────────
def test_brute_force_lockout_works_with_recaptcha(db, client):
    user = create_user(db, "target@test.com", "CorrectPassword123!")

    with patch("app.core.recaptcha_service.verify_recaptcha_token", return_value=(True, "")):
        # 5 tentatives infructueuses
        for _ in range(5):
            client.post(
                "/api/auth/login",
                json={
                    "email": "target@test.com",
                    "mot_de_passe": "BadPass123!",
                    "recaptcha_token": "valid_token",
                },
            )

        db.refresh(user)
        assert user.locked_until is not None

        # 6ème tentative avec bon mot de passe -> refusé (compte bloqué)
        resp_locked = client.post(
            "/api/auth/login",
            json={
                "email": "target@test.com",
                "mot_de_passe": "CorrectPassword123!",
                "recaptcha_token": "valid_token",
            },
        )
        assert resp_locked.status_code == 401
        assert "bloqué" in resp_locked.json()["detail"]


# ─── 10. Rôles ADMIN, RH, EMPLOYE se connectent avec reCAPTCHA ────────────────
def test_all_roles_can_login_with_recaptcha(db, client):
    create_user(db, "admin@test.com", "Password123!", role=RoleEnum.ADMIN)
    create_user(db, "rh@test.com", "Password123!", role=RoleEnum.RH)
    create_user(db, "employe@test.com", "Password123!", role=RoleEnum.EMPLOYE)

    with patch("app.core.recaptcha_service.verify_recaptcha_token", return_value=(True, "")):
        for email, role in [("admin@test.com", "ADMIN"), ("rh@test.com", "RH"), ("employe@test.com", "EMPLOYE")]:
            resp = client.post(
                "/api/auth/login",
                json={
                    "email": email,
                    "mot_de_passe": "Password123!",
                    "recaptcha_token": "valid_token",
                },
            )
            assert resp.status_code == 200
            assert resp.json()["user"]["role"] == role
