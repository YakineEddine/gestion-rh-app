"""
Tests unitaires et d'intégration pour :
1. Type de contrat CIVP (création, validation date_fin obligatoire, transitions de statut).
2. Liaison dynamique Type de contrat <-> Articles (compatibilité, rejet backend, filtrage API).
"""
import os
from datetime import date, timedelta

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token, hash_password
from app.database import Base, get_db
from app.main import app
from app.models.models import (
    Article,
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
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        db.query(Contrat).delete()
        db.query(Article).delete()
        db.query(Utilisateur).delete()
        db.commit()

        rh_user = Utilisateur(
            matricule="RH_CIVP_TEST",
            nom="Admin",
            prenom="RH",
            email="rh_civp_test@example.com",
            mot_de_passe_hash=hash_password("Secret123!"),
            role=RoleEnum.RH.value,
            est_actif=True,
        )
        employe_user = Utilisateur(
            matricule="EMP_CIVP_TEST",
            nom="Testeur",
            prenom="CIVP",
            email="emp_civp_test@example.com",
            mot_de_passe_hash=hash_password("Secret123!"),
            role=RoleEnum.EMPLOYE.value,
            est_actif=True,
        )
        db.add_all([rh_user, employe_user])
        db.commit()
    finally:
        db.close()

    yield

    db = TestSessionLocal()
    try:
        db.query(Contrat).delete()
        db.query(Article).delete()
        db.query(Utilisateur).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def rh_token():
    return create_access_token(data={"sub": "rh_civp_test@example.com", "role": RoleEnum.RH.value})


@pytest.fixture
def employe_id():
    db = TestSessionLocal()
    try:
        u = db.query(Utilisateur).filter(Utilisateur.matricule == "EMP_CIVP_TEST").first()
        return u.id
    finally:
        db.close()


# ─── Tests CIVP ─────────────────────────────────────────────────────────────

def test_create_civp_contract_success(rh_token, employe_id):
    """Créer un contrat CIVP avec date de fin valide."""
    debut = date.today()
    fin = debut + timedelta(days=365)
    resp = client.post(
        "/api/contrats/",
        json={
            "employe_id": employe_id,
            "type_contrat": "CIVP",
            "date_debut": debut.isoformat(),
            "date_fin": fin.isoformat(),
            "salaire_mensuel": 850,
        },
        headers={"Authorization": f"Bearer {rh_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["type_contrat"] == "CIVP"
    assert data["statut"] == "BROUILLON"
    assert data["date_fin"] == fin.isoformat()


def test_create_civp_without_date_fin_fails(rh_token, employe_id):
    """Un contrat CIVP requiert obligatoirement une date de fin."""
    debut = date.today()
    resp = client.post(
        "/api/contrats/",
        json={
            "employe_id": employe_id,
            "type_contrat": "CIVP",
            "date_debut": debut.isoformat(),
            "salaire_mensuel": 850,
        },
        headers={"Authorization": f"Bearer {rh_token}"},
    )
    assert resp.status_code == 422
    assert "date de fin est obligatoire" in resp.text


def test_create_civp_date_fin_before_date_debut_fails(rh_token, employe_id):
    """date_fin <= date_debut doit être rejeté."""
    debut = date.today()
    fin = debut - timedelta(days=1)
    resp = client.post(
        "/api/contrats/",
        json={
            "employe_id": employe_id,
            "type_contrat": "CIVP",
            "date_debut": debut.isoformat(),
            "date_fin": fin.isoformat(),
            "salaire_mensuel": 850,
        },
        headers={"Authorization": f"Bearer {rh_token}"},
    )
    assert resp.status_code == 422
    assert "posterieure" in resp.text or "postérieure" in resp.text


def test_civp_status_transitions_and_forbidden_demission(rh_token, employe_id):
    """CIVP suit les transitions déterminées (Fin CDD, pas de Démission CDI)."""
    debut = date.today()
    fin = debut + timedelta(days=180)
    # 1. Création
    c_resp = client.post(
        "/api/contrats/",
        json={
            "employe_id": employe_id,
            "type_contrat": "CIVP",
            "date_debut": debut.isoformat(),
            "date_fin": fin.isoformat(),
            "salaire_mensuel": 900,
        },
        headers={"Authorization": f"Bearer {rh_token}"},
    )
    cid = c_resp.json()["id"]

    # 2. Brouillon -> Communiqué -> Signé -> Actif
    client.put(f"/api/contrats/{cid}", json={"statut": "COMMUNIQUE_EN_COURS"}, headers={"Authorization": f"Bearer {rh_token}"})
    client.put(f"/api/contrats/{cid}", json={"statut": "SIGNE"}, headers={"Authorization": f"Bearer {rh_token}"})
    up = client.put(f"/api/contrats/{cid}", json={"statut": "ACTIF"}, headers={"Authorization": f"Bearer {rh_token}"})
    assert up.status_code == 200
    assert up.json()["statut"] == "ACTIF"

    # 3. Tentative Démission CDI sur contrat CIVP -> Rejeté 400
    bad = client.put(f"/api/contrats/{cid}", json={"statut": "DEMISSION_CDI"}, headers={"Authorization": f"Bearer {rh_token}"})
    assert bad.status_code == 400
    assert "Démission (CDI)" in bad.json()["detail"]

    # 4. Actif -> FIN_CDD -> OK
    fin_cdd = client.put(f"/api/contrats/{cid}", json={"statut": "FIN_CDD"}, headers={"Authorization": f"Bearer {rh_token}"})
    assert fin_cdd.status_code == 200
    assert fin_cdd.json()["statut"] == "FIN_CDD"


# ─── Tests Articles & Compatibilité ─────────────────────────────────────────

def test_article_types_contrat_crud_and_filtering(rh_token):
    """Créer des articles avec types_contrat et tester le filtrage par paramètre de requête."""
    # 1. Article générique (compatible tous types)
    a1 = client.post(
        "/api/articles/",
        json={
            "code": "ART-GEN-01",
            "titre": "Article Générique Tous Contrats",
            "contenu_par_defaut": "Texte générique",
            "types_contrat": None,
        },
        headers={"Authorization": f"Bearer {rh_token}"},
    )
    assert a1.status_code == 201
    assert a1.json()["types_contrat"] is None

    # 2. Article exclusif CIVP & STAGE
    a2 = client.post(
        "/api/articles/",
        json={
            "code": "ART-CIVP-01",
            "titre": "Clause Spécifique CIVP / STAGE",
            "contenu_par_defaut": "Convention de formation CIVP",
            "types_contrat": ["CIVP", "STAGE"],
        },
        headers={"Authorization": f"Bearer {rh_token}"},
    )
    assert a2.status_code == 201
    assert a2.json()["types_contrat"] == ["CIVP", "STAGE"]

    # 3. Article exclusif CDI
    a3 = client.post(
        "/api/articles/",
        json={
            "code": "ART-CDI-01",
            "titre": "Clause Non-Concurrence CDI",
            "contenu_par_defaut": "Non-concurrence renforcée",
            "types_contrat": ["CDI"],
        },
        headers={"Authorization": f"Bearer {rh_token}"},
    )
    assert a3.status_code == 201
    assert a3.json()["types_contrat"] == ["CDI"]

    # 4. Requête filtrée pour CIVP
    f_civp = client.get("/api/articles/?type_contrat=CIVP", headers={"Authorization": f"Bearer {rh_token}"})
    assert f_civp.status_code == 200
    codes_civp = [art["code"] for art in f_civp.json()]
    assert "ART-GEN-01" in codes_civp
    assert "ART-CIVP-01" in codes_civp
    assert "ART-CDI-01" not in codes_civp

    # 5. Requête filtrée pour CDI
    f_cdi = client.get("/api/articles/?type_contrat=CDI", headers={"Authorization": f"Bearer {rh_token}"})
    assert f_cdi.status_code == 200
    codes_cdi = [art["code"] for art in f_cdi.json()]
    assert "ART-GEN-01" in codes_cdi
    assert "ART-CDI-01" in codes_cdi
    assert "ART-CIVP-01" not in codes_cdi


def test_contract_creation_rejects_incompatible_article(rh_token, employe_id):
    """Créer un contrat CIVP avec un article CDI doit être rejeté par le backend avec HTTP 400."""
    # Récupérer l'ID de l'article CDI
    res_cdi = client.get("/api/articles/?search=ART-CDI-01", headers={"Authorization": f"Bearer {rh_token}"})
    art_cdi_id = res_cdi.json()[0]["id"]

    debut = date.today()
    fin = debut + timedelta(days=180)
    resp = client.post(
        "/api/contrats/",
        json={
            "employe_id": employe_id,
            "type_contrat": "CIVP",
            "date_debut": debut.isoformat(),
            "date_fin": fin.isoformat(),
            "salaire_mensuel": 900,
            "article_ids": [art_cdi_id],
        },
        headers={"Authorization": f"Bearer {rh_token}"},
    )
    assert resp.status_code == 400
    assert "Articles incompatibles avec le type de contrat CIVP" in resp.json()["detail"]


def test_contract_creation_accepts_compatible_and_generic_articles(rh_token, employe_id):
    """Créer un contrat CIVP avec un article CIVP et un article générique fonctionne parfaitement."""
    res_gen = client.get("/api/articles/?search=ART-GEN-01", headers={"Authorization": f"Bearer {rh_token}"})
    res_civp = client.get("/api/articles/?search=ART-CIVP-01", headers={"Authorization": f"Bearer {rh_token}"})
    art_gen_id = res_gen.json()[0]["id"]
    art_civp_id = res_civp.json()[0]["id"]

    debut = date.today()
    fin = debut + timedelta(days=180)
    resp = client.post(
        "/api/contrats/",
        json={
            "employe_id": employe_id,
            "type_contrat": "CIVP",
            "date_debut": debut.isoformat(),
            "date_fin": fin.isoformat(),
            "salaire_mensuel": 950,
            "article_ids": [art_gen_id, art_civp_id],
        },
        headers={"Authorization": f"Bearer {rh_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    contrat_art_ids = [a["id"] for a in data["articles"]]
    assert art_gen_id in contrat_art_ids
    assert art_civp_id in contrat_art_ids


def test_contract_update_rejects_incompatible_article(rh_token, employe_id):
    """Mettre à jour un contrat avec des articles incompatibles doit être rejeté avec HTTP 400."""
    res_gen = client.get("/api/articles/?search=ART-GEN-01", headers={"Authorization": f"Bearer {rh_token}"})
    res_cdi = client.get("/api/articles/?search=ART-CDI-01", headers={"Authorization": f"Bearer {rh_token}"})
    art_gen_id = res_gen.json()[0]["id"]
    art_cdi_id = res_cdi.json()[0]["id"]

    debut = date.today()
    fin = debut + timedelta(days=180)
    # 1. Création initiale valide CIVP
    c_resp = client.post(
        "/api/contrats/",
        json={
            "employe_id": employe_id,
            "type_contrat": "CIVP",
            "date_debut": debut.isoformat(),
            "date_fin": fin.isoformat(),
            "salaire_mensuel": 900,
            "article_ids": [art_gen_id],
        },
        headers={"Authorization": f"Bearer {rh_token}"},
    )
    cid = c_resp.json()["id"]

    # 2. Tentative d'ajouter l'article CDI au contrat CIVP -> Rejet 400
    up_bad = client.put(
        f"/api/contrats/{cid}",
        json={"article_ids": [art_gen_id, art_cdi_id]},
        headers={"Authorization": f"Bearer {rh_token}"},
    )
    assert up_bad.status_code == 400
    assert "Articles incompatibles avec le type de contrat CIVP" in up_bad.json()["detail"]
