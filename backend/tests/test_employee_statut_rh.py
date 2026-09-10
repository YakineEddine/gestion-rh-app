"""
Tests pour la détermination automatique du statut RH de l'employé :
- 'Employé' si l'utilisateur possède un contrat avec statut ACTIF.
- 'Candidat' s'il n'a aucun contrat ou si aucun de ses contrats n'est ACTIF (Brouillon, Communiqué, Signé, Fin CDD, Démission CDI, Inactif).
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
    Utilisateur,
    Contrat,
    RoleEnum,
    StatutContratEnum,
    TypeContratEnum,
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
        db.query(Utilisateur).delete()
        db.commit()

        rh_user = Utilisateur(
            matricule="RH_STATUT_TEST",
            nom="RH",
            prenom="Directeur",
            email="rh_statut_test@example.com",
            mot_de_passe_hash=hash_password("Secret123!"),
            role=RoleEnum.RH.value,
            est_actif=True,
        )
        # Candidat sans contrat
        candidat1 = Utilisateur(
            matricule="EMP-STATUT-001",
            nom="Mansour",
            prenom="Sami",
            email="sami.mansour@example.com",
            mot_de_passe_hash=hash_password("Secret123!"),
            role=RoleEnum.EMPLOYE.value,
            est_actif=True,
        )
        # Candidat avec contrat Brouillon
        candidat2 = Utilisateur(
            matricule="EMP-STATUT-002",
            nom="Trabelsi",
            prenom="Nadia",
            email="nadia.trabelsi@example.com",
            mot_de_passe_hash=hash_password("Secret123!"),
            role=RoleEnum.EMPLOYE.value,
            est_actif=True,
        )
        # Employé avec contrat Actif
        employe_actif = Utilisateur(
            matricule="EMP-STATUT-003",
            nom="Gharbi",
            prenom="Karim",
            email="karim.gharbi@example.com",
            mot_de_passe_hash=hash_password("Secret123!"),
            role=RoleEnum.EMPLOYE.value,
            est_actif=True,
        )
        db.add_all([rh_user, candidat1, candidat2, employe_actif])
        db.commit()

        # Contrat BROUILLON pour candidat2
        ctr_brouillon = Contrat(
            reference="CTR-TEST-BROUILLON",
            type_contrat=TypeContratEnum.CDI.value,
            date_creation=date.today(),
            date_debut=date.today(),
            salaire_mensuel=1500,
            statut=StatutContratEnum.BROUILLON.value,
            employe_id=candidat2.id,
        )
        # Contrat ACTIF pour employe_actif
        ctr_actif = Contrat(
            reference="CTR-TEST-ACTIF",
            type_contrat=TypeContratEnum.CDI.value,
            date_creation=date.today(),
            date_debut=date.today(),
            salaire_mensuel=2000,
            statut=StatutContratEnum.ACTIF.value,
            employe_id=employe_actif.id,
        )
        db.add_all([ctr_brouillon, ctr_actif])
        db.commit()
    finally:
        db.close()

    yield

    db = TestSessionLocal()
    try:
        db.query(Contrat).delete()
        db.query(Utilisateur).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def rh_token():
    return create_access_token(data={"sub": "rh_statut_test@example.com", "role": RoleEnum.RH.value})


def test_statut_rh_in_employes_list(rh_token):
    """Vérifier que la liste des employés renvoie 'Employé' pour contrat actif et 'Candidat' sinon."""
    resp = client.get("/api/employes/", headers={"Authorization": f"Bearer {rh_token}"})
    assert resp.status_code == 200
    data = resp.json()

    # Retrouver les utilisateurs
    emp_map = {e["matricule"]: e for e in data}

    # 1. Candidat sans contrat -> 'Candidat'
    assert "EMP-STATUT-001" in emp_map
    assert emp_map["EMP-STATUT-001"]["statut_rh"] == "Candidat"

    # 2. Candidat avec contrat Brouillon -> 'Candidat'
    assert "EMP-STATUT-002" in emp_map
    assert emp_map["EMP-STATUT-002"]["statut_rh"] == "Candidat"

    # 3. Collaborateur avec contrat Actif -> 'Employé'
    assert "EMP-STATUT-003" in emp_map
    assert emp_map["EMP-STATUT-003"]["statut_rh"] == "Employé"


def test_statut_rh_transition_when_contract_becomes_active(rh_token):
    """Quand le contrat d'un candidat passe à ACTIF, son statut_rh devient automatiquement 'Employé'."""
    db = TestSessionLocal()
    try:
        c2 = db.query(Utilisateur).filter(Utilisateur.matricule == "EMP-STATUT-002").first()
        ctr = db.query(Contrat).filter(Contrat.employe_id == c2.id).first()
        cid = ctr.id
    finally:
        db.close()

    # Passage du contrat de c2 à ACTIF
    client.put(f"/api/contrats/{cid}", json={"statut": "COMMUNIQUE_EN_COURS"}, headers={"Authorization": f"Bearer {rh_token}"})
    client.put(f"/api/contrats/{cid}", json={"statut": "SIGNE"}, headers={"Authorization": f"Bearer {rh_token}"})
    client.put(f"/api/contrats/{cid}", json={"statut": "ACTIF"}, headers={"Authorization": f"Bearer {rh_token}"})

    # Vérification de l'employé
    resp = client.get(f"/api/employes/{c2.id}", headers={"Authorization": f"Bearer {rh_token}"})
    assert resp.status_code == 200
    assert resp.json()["statut_rh"] == "Employé"

    # Si le contrat passe à DEMISSION_CDI puis INACTIF
    client.put(f"/api/contrats/{cid}", json={"statut": "DEMISSION_CDI"}, headers={"Authorization": f"Bearer {rh_token}"})
    client.put(f"/api/contrats/{cid}", json={"statut": "INACTIF"}, headers={"Authorization": f"Bearer {rh_token}"})

    # L'utilisateur redevient un candidat (plus de contrat actif)
    resp2 = client.get(f"/api/employes/{c2.id}", headers={"Authorization": f"Bearer {rh_token}"})
    assert resp2.status_code == 200
    assert resp2.json()["statut_rh"] == "Candidat"
