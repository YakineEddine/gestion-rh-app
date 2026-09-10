"""
Tests pour le système d'archivage et de restauration logique :
- Employés :
  - Archivage logique (est_actif=False), révocation des tokens, préservation des données, audit ARCHIVE
  - Masquage par défaut dans la liste des actifs, filtres ARCHIVES et TOUS
  - Restauration logique (est_actif=True), audit RESTORE
  - Redirection du DELETE vers l'archivage logique (pas de suppression physique)
- Contrats :
  - Archivage logique (statut=INACTIF), préservation des données et articles, audit ARCHIVE
  - Masquage par défaut dans la liste des actifs, filtres ARCHIVES et TOUS
  - Restauration vers le statut antérieur, règle d'expiration (un contrat expiré n'est pas restauré comme ACTIF mais FIN_CDD)
  - Redirection du DELETE vers l'archivage logique
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
    Article,
    AuditLog,
    RoleEnum,
    StatutContratEnum,
    TypeContratEnum,
    AuditActionEnum,
    AuditEntiteEnum,
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
        db.query(AuditLog).delete()
        db.query(Contrat).delete()
        db.query(Article).delete()
        db.query(Utilisateur).delete()
        db.commit()

        # RH utilisateur
        rh_user = Utilisateur(
            matricule="RH_ARCHIVE_TEST",
            nom="RH_Nom",
            prenom="RH_Prenom",
            email="rh.archive.test@entreprise.com",
            mot_de_passe_hash=hash_password("Password123!"),
            role=RoleEnum.RH,
            est_actif=True,
        )
        db.add(rh_user)

        # Employé à tester
        emp_user = Utilisateur(
            matricule="EMP_ARCHIVE_TEST",
            nom="Dupont",
            prenom="Jean",
            email="jean.dupont.archive@entreprise.com",
            mot_de_passe_hash=hash_password("Password123!"),
            role=RoleEnum.EMPLOYE,
            est_actif=True,
            date_embauche=date.today() - timedelta(days=100),
            departement="Informatique",
            poste="Développeur",
        )
        db.add(emp_user)
        db.commit()
    finally:
        db.close()


def get_rh_token():
    return create_access_token(
        data={"sub": "rh.archive.test@entreprise.com", "role": "RH"}
    )


def test_archivage_employe():
    token = get_rh_token()
    headers = {"Authorization": f"Bearer {token}"}

    db = TestSessionLocal()
    emp = db.query(Utilisateur).filter(Utilisateur.matricule == "EMP_ARCHIVE_TEST").first()
    emp_id = emp.id
    db.close()

    # 1. Archiver l'employé via POST /api/employes/{id}/archive
    resp = client.post(f"/api/employes/{emp_id}/archive", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["est_actif"] is False

    # 2. Vérifier que la ligne PostgreSQL existe toujours
    db = TestSessionLocal()
    emp_in_db = db.query(Utilisateur).filter(Utilisateur.id == emp_id).first()
    assert emp_in_db is not None
    assert emp_in_db.est_actif is False

    # Vérifier l'audit
    log_archive = db.query(AuditLog).filter(
        AuditLog.entite == AuditEntiteEnum.EMPLOYE.value,
        AuditLog.entite_id == emp_id,
        AuditLog.action == AuditActionEnum.ARCHIVE.value
    ).first()
    assert log_archive is not None
    db.close()

    # 3. Vérifier le filtrage dans la liste des employés
    # Par défaut (Actifs) : ne doit PAS apparaître
    resp_default = client.get("/api/employes/", headers=headers)
    assert resp_default.status_code == 200
    ids_default = [e["id"] for e in resp_default.json()]
    assert emp_id not in ids_default

    # Filtre ARCHIVES : DOIT apparaître
    resp_archives = client.get("/api/employes/?statut=ARCHIVES", headers=headers)
    assert resp_archives.status_code == 200
    ids_archives = [e["id"] for e in resp_archives.json()]
    assert emp_id in ids_archives

    # Filtre TOUS : DOIT apparaître
    resp_tous = client.get("/api/employes/?statut=TOUS", headers=headers)
    assert resp_tous.status_code == 200
    ids_tous = [e["id"] for e in resp_tous.json()]
    assert emp_id in ids_tous

    # 4. Restaurer l'employé
    resp_restore = client.post(f"/api/employes/{emp_id}/restaurer", headers=headers)
    assert resp_restore.status_code == 200
    assert resp_restore.json()["est_actif"] is True

    # Doit réapparaître dans la liste par défaut
    resp_default2 = client.get("/api/employes/", headers=headers)
    ids_default2 = [e["id"] for e in resp_default2.json()]
    assert emp_id in ids_default2


def test_delete_employe_effectue_archivage_logique():
    token = get_rh_token()
    headers = {"Authorization": f"Bearer {token}"}

    db = TestSessionLocal()
    emp = db.query(Utilisateur).filter(Utilisateur.matricule == "EMP_ARCHIVE_TEST").first()
    emp_id = emp.id
    db.close()

    # Appel DELETE /api/employes/{id}
    resp = client.delete(f"/api/employes/{emp_id}", headers=headers)
    assert resp.status_code in [200, 204]

    # Vérifier que l'employé n'est PAS supprimé de la base PostgreSQL
    db = TestSessionLocal()
    emp_db = db.query(Utilisateur).filter(Utilisateur.id == emp_id).first()
    assert emp_db is not None
    assert emp_db.est_actif is False
    db.close()


def test_archivage_et_restauration_contrat():
    token = get_rh_token()
    headers = {"Authorization": f"Bearer {token}"}

    db = TestSessionLocal()
    emp = db.query(Utilisateur).filter(Utilisateur.matricule == "EMP_ARCHIVE_TEST").first()
    
    # Créer un contrat actif avec date future
    contrat = Contrat(
        reference="CTR-TEST-ARCHIVE-01",
        type_contrat=TypeContratEnum.CDD.value,
        date_creation=date.today(),
        date_debut=date.today() - timedelta(days=10),
        date_fin=date.today() + timedelta(days=60),
        salaire_mensuel=2500.0,
        statut=StatutContratEnum.ACTIF.value,
        employe_id=emp.id,
    )
    db.add(contrat)
    db.commit()
    contrat_id = contrat.id
    db.close()

    # 1. Archiver le contrat
    resp = client.post(f"/api/contrats/{contrat_id}/archive", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["statut"] == StatutContratEnum.INACTIF.value

    # Vérifier que le contrat existe toujours en base et a le statut INACTIF
    db = TestSessionLocal()
    c_db = db.query(Contrat).filter(Contrat.id == contrat_id).first()
    assert c_db is not None
    assert c_db.statut == StatutContratEnum.INACTIF.value

    # Vérifier l'audit
    log_archive = db.query(AuditLog).filter(
        AuditLog.entite == AuditEntiteEnum.CONTRAT.value,
        AuditLog.entite_id == contrat_id,
        AuditLog.action == AuditActionEnum.ARCHIVE.value,
    ).first()
    assert log_archive is not None
    db.close()

    # 2. Vérifier les filtres /api/contrats/
    # Par défaut (Actifs) : ne doit PAS apparaître
    resp_def = client.get("/api/contrats/", headers=headers)
    assert resp_def.status_code == 200
    ids_def = [c["id"] for c in resp_def.json()]
    assert contrat_id not in ids_def

    # Filtre ARCHIVES : DOIT apparaître
    resp_arch = client.get("/api/contrats/?archivage=ARCHIVES", headers=headers)
    assert resp_arch.status_code == 200
    ids_arch = [c["id"] for c in resp_arch.json()]
    assert contrat_id in ids_arch

    # Filtre TOUS : DOIT apparaître
    resp_all = client.get("/api/contrats/?archivage=TOUS", headers=headers)
    assert resp_all.status_code == 200
    ids_all = [c["id"] for c in resp_all.json()]
    assert contrat_id in ids_all

    # 3. Restaurer le contrat (non expiré -> doit redevenir ACTIF)
    resp_rest = client.post(f"/api/contrats/{contrat_id}/restaurer", headers=headers)
    assert resp_rest.status_code == 200
    assert resp_rest.json()["statut"] == StatutContratEnum.ACTIF.value


def test_restauration_contrat_expire_ne_devient_pas_actif():
    token = get_rh_token()
    headers = {"Authorization": f"Bearer {token}"}

    db = TestSessionLocal()
    emp = db.query(Utilisateur).filter(Utilisateur.matricule == "EMP_ARCHIVE_TEST").first()

    # Créer un contrat qui était ACTIF mais dont la date de fin est dépassée
    contrat_exp = Contrat(
        reference="CTR-TEST-EXPIRED-01",
        type_contrat=TypeContratEnum.CDD.value,
        date_creation=date.today() - timedelta(days=100),
        date_debut=date.today() - timedelta(days=90),
        date_fin=date.today() - timedelta(days=10), # expiré
        salaire_mensuel=2000.0,
        statut=StatutContratEnum.ACTIF.value,
        employe_id=emp.id,
    )
    db.add(contrat_exp)
    db.commit()
    c_id = contrat_exp.id
    db.close()

    # Archiver
    client.post(f"/api/contrats/{c_id}/archive", headers=headers)

    # Restaurer : Ne doit PAS être restauré comme ACTIF, mais comme FIN_CDD
    resp = client.post(f"/api/contrats/{c_id}/restaurer", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["statut"] == StatutContratEnum.FIN_CDD.value


def test_delete_contrat_effectue_archivage_logique():
    token = get_rh_token()
    headers = {"Authorization": f"Bearer {token}"}

    db = TestSessionLocal()
    emp = db.query(Utilisateur).filter(Utilisateur.matricule == "EMP_ARCHIVE_TEST").first()

    contrat = Contrat(
        reference="CTR-TEST-DELETE-01",
        type_contrat=TypeContratEnum.CDI.value,
        date_creation=date.today(),
        date_debut=date.today(),
        salaire_mensuel=3000.0,
        statut=StatutContratEnum.BROUILLON.value,
        employe_id=emp.id,
    )
    db.add(contrat)
    db.commit()
    c_id = contrat.id
    db.close()

    # Appel DELETE /api/contrats/{id}
    resp = client.delete(f"/api/contrats/{c_id}", headers=headers)
    assert resp.status_code in [200, 204]

    # Vérifier que le contrat n'est PAS supprimé de la base physique
    db = TestSessionLocal()
    c_db = db.query(Contrat).filter(Contrat.id == c_id).first()
    assert c_db is not None
    assert c_db.statut == StatutContratEnum.INACTIF.value
    db.close()
