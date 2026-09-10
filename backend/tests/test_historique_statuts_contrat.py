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
from app.models.models import Contrat, RoleEnum, StatutContratEnum, TypeContratEnum, Utilisateur

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
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture
def db_session():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def rh_token(db_session):
    user = db_session.query(Utilisateur).filter(Utilisateur.email == "rh.test.hist@test.com").first()
    if not user:
        user = Utilisateur(
            matricule="RH-HIST-01",
            nom="RH",
            prenom="Test",
            email="rh.test.hist@test.com",
            mot_de_passe_hash=hash_password("Password123!"),
            role=RoleEnum.RH,
            est_actif=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return create_access_token({"sub": user.email, "role": user.role.value, "user_id": user.id})


@pytest.fixture
def employe_cible(db_session):
    emp = db_session.query(Utilisateur).filter(Utilisateur.email == "emp.test.hist@test.com").first()
    if not emp:
        emp = Utilisateur(
            matricule="EMP-HIST-01",
            nom="Martin",
            prenom="Lucas",
            email="emp.test.hist@test.com",
            mot_de_passe_hash=hash_password("Password123!"),
            role=RoleEnum.EMPLOYE,
            est_actif=True,
        )
        db_session.add(emp)
        db_session.commit()
        db_session.refresh(emp)
    return emp


def test_historique_statuts_employe_workflow(rh_token, employe_cible, db_session):
    headers = {"Authorization": f"Bearer {rh_token}"}

    # 1. Créer un contrat pour cet employé
    create_payload = {
        "employe_id": employe_cible.id,
        "type_contrat": "CDD",
        "date_debut": str(date.today()),
        "date_fin": str(date.today() + timedelta(days=180)),
        "salaire_mensuel": 2500,
        "statut": "Brouillon",
        "articles_ids": []
    }
    res = client.post("/api/contrats/", json=create_payload, headers=headers)
    assert res.status_code == 201, res.text
    contrat = res.json()
    contrat_id = contrat["id"]

    # 2. Modifier son statut : Brouillon -> Communiqué (en cours)
    update_payload_1 = {
        "statut": "Communiqué (en cours)",
        "type_contrat": "CDD",
        "date_debut": str(date.today()),
        "date_fin": str(date.today() + timedelta(days=180)),
        "salaire_mensuel": 2500,
    }
    res_update_1 = client.put(f"/api/contrats/{contrat_id}", json=update_payload_1, headers=headers)
    assert res_update_1.status_code == 200

    # 3. Modifier son statut : Communiqué (en cours) -> Signé
    update_payload_2 = {
        "statut": "Signé",
        "type_contrat": "CDD",
        "date_debut": str(date.today()),
        "date_fin": str(date.today() + timedelta(days=180)),
        "salaire_mensuel": 2500,
    }
    res_update_2 = client.put(f"/api/contrats/{contrat_id}", json=update_payload_2, headers=headers)
    assert res_update_2.status_code == 200

    # 4. Consulter l'historique des statuts de l'employé
    res_hist_emp = client.get(f"/api/contrats/employe/{employe_cible.id}/historique-statuts", headers=headers)
    assert res_hist_emp.status_code == 200
    hist_emp = res_hist_emp.json()
    assert len(hist_emp) >= 3  # Création + 2 modifications

    # Vérifier que les statuts et transitions sont présents
    statuts_presents = [h["nouveau_statut"] for h in hist_emp]
    assert any("SIGNE" in s or "Signé" in s for s in statuts_presents)
    assert any("COMMUNIQUE" in s or "Communiqué" in s for s in statuts_presents)
    assert any("BROUILLON" in s or "Brouillon" in s for s in statuts_presents)

    # 5. Consulter l'historique ciblé du contrat
    res_hist_ctr = client.get(f"/api/contrats/{contrat_id}/historique-statuts", headers=headers)
    assert res_hist_ctr.status_code == 200
    hist_ctr = res_hist_ctr.json()
    assert len(hist_ctr) >= 3
    assert hist_ctr[0]["contrat_id"] == contrat_id
