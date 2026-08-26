from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import Utilisateur, AuditActionEnum, AuditEntiteEnum
from app.schemas.schemas import LoginRequest, TokenResponse, UtilisateurResponse, ForgotPasswordRequest, ResetPasswordRequest
from app.core.security import verify_password, create_access_token, hash_password, create_reset_token, verify_reset_token, get_current_user
from app.core.audit_service import log_action

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Connexion d'un utilisateur et retour d'un token JWT."""
    clean_email = payload.email.strip().lower()
    user = db.query(Utilisateur).filter(func.lower(Utilisateur.email) == clean_email).first()
    if not user:
        log_action(
            db=db, utilisateur_id=None,
            action=AuditActionEnum.LOGIN_FAILED.value, entite=AuditEntiteEnum.AUTH.value,
            description=f"Tentative de connexion échouée pour '{clean_email}' (utilisateur inconnu)",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Vérifier le mot de passe
    if not verify_password(payload.mot_de_passe, user.mot_de_passe_hash):
        log_action(
            db=db, utilisateur_id=user.id,
            action=AuditActionEnum.LOGIN_FAILED.value, entite=AuditEntiteEnum.AUTH.value, entite_id=user.id,
            description=f"Tentative de connexion échouée pour {user.email} (mot de passe incorrect)",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Créer le token JWT
    access_token = create_access_token(data={"sub": user.email, "role": user.role.value})

    log_action(
        db=db, utilisateur_id=user.id,
        action=AuditActionEnum.LOGIN.value, entite=AuditEntiteEnum.AUTH.value, entite_id=user.id,
        description=f"Connexion de {user.prenom} {user.nom}",
        request=request,
    )
    
    return TokenResponse(
        access_token=access_token,
        user=UtilisateurResponse(
            id=user.id,
            nom=user.nom,
            prenom=user.prenom,
            email=user.email,
            matricule=user.matricule,
            date_embauche=user.date_embauche,
            role=user.role.value
        )
    )


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Enregistrer la deconnexion dans l'audit. Le JWT etant sans etat, aucune
    invalidation serveur n'est necessaire : le frontend supprime le token
    localement apres cet appel.
    """
    log_action(
        db=db, utilisateur_id=current_user.id,
        action=AuditActionEnum.LOGOUT.value, entite=AuditEntiteEnum.AUTH.value, entite_id=current_user.id,
        description=f"Déconnexion de {current_user.prenom} {current_user.nom}",
        request=request,
    )
    return {"message": "Déconnexion enregistrée"}


@router.post("/register", response_model=UtilisateurResponse, status_code=status.HTTP_201_CREATED)
def register(request: dict, db: Session = Depends(get_db)):
    """Créer le premier compte administrateur (à utiliser une seule fois pour l'initialisation)."""
    # Vérifier si un admin existe déjà
    existing = db.query(Utilisateur).filter(Utilisateur.email == request.get("email")).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un utilisateur avec cet email existe déjà"
        )
    
    new_user = Utilisateur(
        nom=request.get("nom"),
        prenom=request.get("prenom"),
        email=request.get("email"),
        mot_de_passe_hash=hash_password(request.get("mot_de_passe")),
        matricule=request.get("matricule", "RH-001"),
        role="RH"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UtilisateurResponse(
        id=new_user.id,
        nom=new_user.nom,
        prenom=new_user.prenom,
        email=new_user.email,
        matricule=new_user.matricule,
        date_embauche=new_user.date_embauche,
        role=new_user.role.value
    )


@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Envoyer un email de reinitialisation de mot de passe."""
    clean_email = request.email.strip().lower()
    user = db.query(Utilisateur).filter(func.lower(Utilisateur.email) == clean_email).first()
    if not user:
        # Ne pas divulguer si l'email existe ou pas
        return {"message": "Si cet email est enregistre, un lien de reinitialisation vous a ete envoye."}

    token = create_reset_token(user.email)
    reset_url = f"http://localhost:5174/reset-password?token={token}"

    # Envoyer le vrai email
    from app.core.email_service import envoyer_email_reinitialisation
    email_sent = envoyer_email_reinitialisation(
        destinataire=user.email,
        prenom=user.prenom,
        reset_url=reset_url
    )

    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible d'envoyer l'email. Veuillez verifier la configuration SMTP."
        )

    return {"message": "Un email de reinitialisation a ete envoye a votre adresse."}


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Réinitialiser le mot de passe à l'aide d'un token valide."""
    email = verify_reset_token(request.token)
    user = db.query(Utilisateur).filter(Utilisateur.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    user.mot_de_passe_hash = hash_password(request.nouveau_mot_de_passe)
    db.commit()

    return {"message": "Votre mot de passe a été réinitialisé avec succès ! Vous pouvez maintenant vous connecter."}

