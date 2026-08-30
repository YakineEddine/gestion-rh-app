from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.models import Utilisateur, Contrat, AuditActionEnum, AuditEntiteEnum
from app.schemas.schemas import UtilisateurResponse, UtilisateurUpdate, ContratResponse
from app.core.security import get_current_user, require_any_role
from app.core.document_generator import generer_contrat_word
from app.core.audit_service import log_action

router = APIRouter(prefix="/api/mon-espace", tags=["Espace Employe"])


@router.get("/profil", response_model=UtilisateurResponse)
def get_mon_profil(current_user: Utilisateur = Depends(get_current_user)):
    """Recuperer le profil de l'employe connecte."""
    return UtilisateurResponse(
        id=current_user.id,
        nom=current_user.nom,
        prenom=current_user.prenom,
        email=current_user.email,
        matricule=current_user.matricule,
        date_embauche=current_user.date_embauche,
        date_naissance=current_user.date_naissance,
        telephone=current_user.telephone,
        departement=current_user.departement,
        poste=current_user.poste,
        role=current_user.role.value
    )


@router.put("/profil", response_model=UtilisateurResponse)
def modifier_mon_profil(
    data: UtilisateurUpdate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_any_role("RH", "ADMIN"))
):
    """
    Seuls les administrateurs et RH sont autorises a modifier les coordonnees.
    Un utilisateur avec le role EMPLOYE recoit un refus HTTP 403 Forbidden.
    """
    # L'employe ne peut modifier que des champs limites
    if data.telephone is not None:
        current_user.telephone = data.telephone
    if data.email is not None:
        existing = db.query(Utilisateur).filter(
            Utilisateur.email == data.email,
            Utilisateur.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cet email est deja utilise."
            )
        current_user.email = data.email

    db.commit()
    db.refresh(current_user)

    return UtilisateurResponse(
        id=current_user.id,
        nom=current_user.nom,
        prenom=current_user.prenom,
        email=current_user.email,
        matricule=current_user.matricule,
        date_embauche=current_user.date_embauche,
        date_naissance=current_user.date_naissance,
        telephone=current_user.telephone,
        departement=current_user.departement,
        poste=current_user.poste,
        role=current_user.role.value
    )


@router.get("/contrats", response_model=list[ContratResponse])
def get_mes_contrats(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Recuperer les contrats de l'employe connecte, avec les articles associes.

    Regle metier : un contrat au statut BROUILLON n'est jamais visible ni
    accessible par l'employe. Seuls les contrats finalises (Actif, Suspendu,
    Termine, Expire, ...) sont retournes.
    """
    contrats = db.query(Contrat).options(
        joinedload(Contrat.articles)
    ).filter(
        Contrat.employe_id == current_user.id,
        Contrat.statut != "Brouillon"
    ).order_by(Contrat.date_creation.desc()).all()
    return contrats


@router.get("/contrats/{contrat_id}/telecharger")
def telecharger_mon_contrat(
    contrat_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Telecharger son propre contrat au format Word (.docx)."""
    contrat = db.query(Contrat).options(
        joinedload(Contrat.employe),
        joinedload(Contrat.articles)
    ).filter(Contrat.id == contrat_id).first()

    if not contrat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat non trouve")

    # Securite : l'employe ne peut telecharger que son propre contrat
    if contrat.employe_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'etes pas autorise a acceder a ce contrat"
        )

    # Regle metier : un contrat BROUILLON n'est jamais telechargeable par l'employe,
    # meme s'il en connait l'ID.
    if contrat.statut == "Brouillon":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce contrat n'est pas encore disponible."
        )

    buffer = generer_contrat_word(contrat)
    filename = f"Contrat_{contrat.reference}.docx"

    log_action(
        db=db,
        utilisateur_id=current_user.id,
        action=AuditActionEnum.DOWNLOAD.value,
        entite=AuditEntiteEnum.CONTRAT.value,
        entite_id=contrat.id,
        description=f"Téléchargement du contrat {contrat.reference} par l'employé",
        request=request,
    )

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
