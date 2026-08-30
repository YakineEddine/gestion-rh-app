from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import date
import random
import string

from app.database import get_db
from app.models.models import Utilisateur, RoleEnum, AuditActionEnum, AuditEntiteEnum
from app.schemas.schemas import UtilisateurCreate, UtilisateurUpdate, UtilisateurResponse
from app.core.security import hash_password, get_current_user, require_any_role
from app.core.audit_service import log_action, diff_valeurs

router = APIRouter(prefix="/api/employes", tags=["Employés"])


def generer_matricule(db: Session) -> str:
    """Générer un matricule unique de format EMP-XXXX."""
    while True:
        annee = date.today().year
        code = ''.join(random.choices(string.digits, k=3))
        matricule = f"EMP-{annee}-{code}"
        existing = db.query(Utilisateur).filter(Utilisateur.matricule == matricule).first()
        if not existing:
            return matricule


def to_response(emp: Utilisateur) -> UtilisateurResponse:
    return UtilisateurResponse(
        id=emp.id,
        nom=emp.nom,
        prenom=emp.prenom,
        email=emp.email,
        matricule=emp.matricule,
        date_embauche=emp.date_embauche,
        date_naissance=emp.date_naissance,
        telephone=emp.telephone,
        departement=emp.departement,
        poste=emp.poste,
        role=emp.role.value
    )


@router.get("/", response_model=List[UtilisateurResponse])
def lister_employes(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_any_role("RH", "ADMIN"))
):
    employes = db.query(Utilisateur).all()
    return [to_response(emp) for emp in employes]


@router.get("/{employe_id}", response_model=UtilisateurResponse)
def lire_employe(
    employe_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_any_role("RH", "ADMIN"))
):
    employe = db.query(Utilisateur).filter(Utilisateur.id == employe_id).first()
    if not employe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")
    return to_response(employe)


@router.post("/", response_model=UtilisateurResponse, status_code=status.HTTP_201_CREATED)
def creer_employe(
    employe: UtilisateurCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_any_role("RH", "ADMIN"))
):
    existing = db.query(Utilisateur).filter(Utilisateur.email == employe.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un employé avec cet email existe déjà")

    matricule = generer_matricule(db)

    new_employe = Utilisateur(
        nom=employe.nom,
        prenom=employe.prenom,
        email=employe.email,
        mot_de_passe_hash=hash_password(employe.mot_de_passe),
        matricule=matricule,
        date_embauche=employe.date_embauche or date.today(),
        date_naissance=employe.date_naissance,
        telephone=employe.telephone,
        departement=employe.departement,
        poste=employe.poste,
        role=employe.role or RoleEnum.EMPLOYE
    )

    db.add(new_employe)
    db.commit()
    db.refresh(new_employe)

    log_action(
        db=db,
        utilisateur_id=current_user.id,
        action=AuditActionEnum.CREATE.value,
        entite=AuditEntiteEnum.EMPLOYE.value,
        entite_id=new_employe.id,
        description=f"Création de l'employé {new_employe.prenom} {new_employe.nom} ({new_employe.matricule})",
        nouvelles_valeurs={
            "nom": new_employe.nom,
            "prenom": new_employe.prenom,
            "email": new_employe.email,
            "departement": new_employe.departement,
            "poste": new_employe.poste,
            "role": new_employe.role.value,
        },
        request=request,
    )

    return to_response(new_employe)


@router.put("/{employe_id}", response_model=UtilisateurResponse)
def modifier_employe(
    employe_id: int,
    employe_data: UtilisateurUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_any_role("RH", "ADMIN"))
):
    employe = db.query(Utilisateur).filter(Utilisateur.id == employe_id).first()
    if not employe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")

    avant = {
        "nom": employe.nom,
        "prenom": employe.prenom,
        "email": employe.email,
        "date_embauche": employe.date_embauche,
        "date_naissance": employe.date_naissance,
        "telephone": employe.telephone,
        "departement": employe.departement,
        "poste": employe.poste,
        "role": employe.role.value if employe.role else None,
    }

    if employe_data.nom is not None: employe.nom = employe_data.nom
    if employe_data.prenom is not None: employe.prenom = employe_data.prenom
    if employe_data.email is not None:
        existing = db.query(Utilisateur).filter(
            Utilisateur.email == employe_data.email, Utilisateur.id != employe_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cet email est déjà utilisé")
        employe.email = employe_data.email
    if employe_data.date_embauche is not None: employe.date_embauche = employe_data.date_embauche
    if employe_data.date_naissance is not None: employe.date_naissance = employe_data.date_naissance
    if employe_data.telephone is not None: employe.telephone = employe_data.telephone
    if employe_data.departement is not None: employe.departement = employe_data.departement
    if employe_data.poste is not None: employe.poste = employe_data.poste
    if employe_data.role is not None: employe.role = employe_data.role

    db.commit()
    db.refresh(employe)

    apres = {
        "nom": employe.nom,
        "prenom": employe.prenom,
        "email": employe.email,
        "date_embauche": employe.date_embauche,
        "date_naissance": employe.date_naissance,
        "telephone": employe.telephone,
        "departement": employe.departement,
        "poste": employe.poste,
        "role": employe.role.value if employe.role else None,
    }
    anciennes, nouvelles = diff_valeurs(avant, apres)

    log_action(
        db=db,
        utilisateur_id=current_user.id,
        action=AuditActionEnum.UPDATE.value,
        entite=AuditEntiteEnum.EMPLOYE.value,
        entite_id=employe.id,
        description=f"Modification de l'employé {employe.prenom} {employe.nom} ({employe.matricule})",
        anciennes_valeurs=anciennes,
        nouvelles_valeurs=nouvelles,
        request=request,
    )

    return to_response(employe)


@router.delete("/{employe_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_employe(
    employe_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_any_role("RH", "ADMIN"))
):
    employe = db.query(Utilisateur).filter(Utilisateur.id == employe_id).first()
    if not employe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")

    nom_complet = f"{employe.prenom} {employe.nom}"
    matricule = employe.matricule

    db.delete(employe)
    db.commit()

    log_action(
        db=db,
        utilisateur_id=current_user.id,
        action=AuditActionEnum.DELETE.value,
        entite=AuditEntiteEnum.EMPLOYE.value,
        entite_id=employe_id,
        description=f"Suppression de l'employé {nom_complet} ({matricule})",
        request=request,
    )
    return None
