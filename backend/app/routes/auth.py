from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import Utilisateur, RoleEnum, AuditActionEnum, AuditEntiteEnum
from app.schemas.schemas import (
    LoginRequest, TokenResponse, UtilisateurResponse,
    ForgotPasswordRequest, ResetPasswordRequest,
    RefreshTokenRequest, RefreshTokenResponse
)
from app.core.security import (
    verify_password, create_access_token, hash_password,
    create_reset_token, verify_reset_token, mark_reset_token_used,
    get_current_user, validate_password, is_account_locked,
    record_failed_login, reset_login_attempts,
    create_refresh_token, verify_refresh_token, rotate_refresh_token,
    revoke_all_user_refresh_tokens
)
from app.core.audit_service import log_action
from app.core.email_service import (
    envoyer_email_reinitialisation, envoyer_email_notification
)

router = APIRouter(prefix="/api/auth", tags=["Authentification"])

# Messages génériques communs pour ne pas divulguer l'existence d'un email.
_AUTH_ERROR_GENERIC = "Email ou mot de passe incorrect"


def _build_reset_url(raw_token: str) -> str:
    from app.core.email_service import APP_URL
    return f"{APP_URL}/reset-password?token={raw_token}"


def _notify_password_changed(user: Utilisateur) -> None:
    """Notification non bloquante de changement de mot de passe."""
    try:
        from app.core.email_service import envoyer_email_notification, APP_URL
        envoyer_email_notification(
            destinataire=user.email,
            prenom=user.prenom,
            sujet="Votre mot de passe a été modifié",
            titre="Modification de mot de passe",
            corps=(
                "Votre mot de passe a été modifié avec succès. "
                "Si vous n'êtes pas à l'origine de cette action, veuillez contacter l'administrateur."
            ),
            bouton_text="Accéder à mon espace",
            bouton_url=APP_URL,
        )
    except Exception:
        pass


def _notify_account_locked(user: Utilisateur, locked_until) -> None:
    """Notification non bloquante de blocage temporaire du compte."""
    try:
        from app.core.email_service import envoyer_email_notification, APP_URL
        envoyer_email_notification(
            destinataire=user.email,
            prenom=user.prenom,
            sujet="Compte temporairement bloqué",
            titre="Blocage temporaire de votre compte",
            corps=(
                f"Votre compte a été temporairement bloqué suite à plusieurs tentatives de connexion échouées. "
                f"Vous pourrez réessayer après le {locked_until.strftime('%H:%M')}."
            ),
            bouton_text="Accéder à l'application",
            bouton_url=APP_URL,
        )
    except Exception:
        pass


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Connexion d'un utilisateur et retour d'un access token + refresh token."""
    # 1. Vérification reCAPTCHA obligatoire
    from app.core.recaptcha_service import verify_recaptcha_token

    if not payload.recaptcha_token or not payload.recaptcha_token.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Veuillez confirmer que vous n'êtes pas un robot."
        )

    client_ip = request.client.host if request.client else None
    captcha_ok, error_reason = verify_recaptcha_token(payload.recaptcha_token, client_ip)

    if not captcha_ok:
        if error_reason == "timeout-or-duplicate":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La vérification CAPTCHA a expiré. Veuillez la renouveler."
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La vérification CAPTCHA a échoué. Veuillez réessayer."
        )

    clean_email = payload.email.strip().lower()
    user = db.query(Utilisateur).filter(func.lower(Utilisateur.email) == clean_email).first()

    # Email inconnu : réponse générique, audit LOGIN_FAILED.
    if not user:
        log_action(
            db=db, utilisateur_id=None,
            action=AuditActionEnum.LOGIN_FAILED.value, entite=AuditEntiteEnum.AUTH.value,
            description="Tentative de connexion échouée (utilisateur inconnu)",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_AUTH_ERROR_GENERIC
        )

    # Compte désactivé : réponse générique.
    if not user.est_actif:
        log_action(
            db=db, utilisateur_id=user.id,
            action=AuditActionEnum.LOGIN_FAILED.value, entite=AuditEntiteEnum.AUTH.value, entite_id=user.id,
            description=f"Tentative de connexion échouée (compte désactivé) pour {user.email}",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_AUTH_ERROR_GENERIC
        )

    # Compte temporairement bloqué : message spécifique.
    locked, locked_until = is_account_locked(user)
    if locked:
        log_action(
            db=db, utilisateur_id=user.id,
            action=AuditActionEnum.LOGIN_FAILED.value, entite=AuditEntiteEnum.AUTH.value, entite_id=user.id,
            description=f"Tentative de connexion échouée (compte bloqué jusqu'à {locked_until.isoformat()}) pour {user.email}",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Compte temporairement bloqué. Réessayez après {locked_until.strftime('%H:%M')}."
        )

    # Vérifier le mot de passe
    if not verify_password(payload.mot_de_passe, user.mot_de_passe_hash):
        just_locked = record_failed_login(user, db)
        db.commit()

        if just_locked:
            locked_until = user.locked_until
            log_action(
                db=db, utilisateur_id=user.id,
                action=AuditActionEnum.ACCOUNT_LOCKED.value, entite=AuditEntiteEnum.AUTH.value, entite_id=user.id,
                description=f"Compte bloqué temporairement après {user.login_attempts} tentatives échouées pour {user.email}",
                request=request,
            )
            _notify_account_locked(user, locked_until)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Compte temporairement bloqué. Réessayez après {locked_until.strftime('%H:%M')}."
            )

        log_action(
            db=db, utilisateur_id=user.id,
            action=AuditActionEnum.LOGIN_FAILED.value, entite=AuditEntiteEnum.AUTH.value, entite_id=user.id,
            description=f"Tentative de connexion échouée (mot de passe incorrect) pour {user.email}",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_AUTH_ERROR_GENERIC
        )

    # Connexion réussie : débloquer / réinitialiser les tentatives.
    was_locked = user.locked_until is not None
    reset_login_attempts(user, db)
    db.commit()

    if was_locked:
        log_action(
            db=db, utilisateur_id=user.id,
            action=AuditActionEnum.ACCOUNT_UNLOCKED.value, entite=AuditEntiteEnum.AUTH.value, entite_id=user.id,
            description=f"Déblocage du compte {user.email} suite à une connexion réussie",
            request=request,
        )

    access_token = create_access_token(data={"sub": user.email, "role": user.role.value})
    refresh_token = create_refresh_token(user, db)

    log_action(
        db=db, utilisateur_id=user.id,
        action=AuditActionEnum.LOGIN.value, entite=AuditEntiteEnum.AUTH.value, entite_id=user.id,
        description=f"Connexion de {user.prenom} {user.nom}",
        request=request,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
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


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_token(request_data: RefreshTokenRequest, request: Request, db: Session = Depends(get_db)):
    """Renouvelle un access token à l'aide d'un refresh token valide."""
    rt = verify_refresh_token(request_data.refresh_token, db)
    if not rt:
        log_action(
            db=db, utilisateur_id=None,
            action=AuditActionEnum.LOGIN_FAILED.value, entite=AuditEntiteEnum.AUTH.value,
            description="Tentative de rafraîchissement de token échouée (refresh token invalide, expiré ou révoqué)",
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide ou expiré"
        )

    user = rt.utilisateur
    if not user or not user.est_actif:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalide")

    new_refresh_token = rotate_refresh_token(rt, db)
    access_token = create_access_token(data={"sub": user.email, "role": user.role.value})

    log_action(
        db=db, utilisateur_id=user.id,
        action=AuditActionEnum.LOGIN.value, entite=AuditEntiteEnum.AUTH.value, entite_id=user.id,
        description=f"Rafraîchissement du token d'accès pour {user.email}",
        request=request,
    )

    return RefreshTokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Déconnexion : révoque tous les refresh tokens de l'utilisateur.
    Le frontend supprime également l'access token localement.
    """
    revoke_all_user_refresh_tokens(current_user.id, db)

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
    existing = db.query(Utilisateur).filter(Utilisateur.email == request.get("email")).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un utilisateur avec cet email existe déjà"
        )

    password = request.get("mot_de_passe", "")
    ok, msg = validate_password(password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    new_user = Utilisateur(
        nom=request.get("nom"),
        prenom=request.get("prenom"),
        email=request.get("email").strip().lower() if request.get("email") else None,
        mot_de_passe_hash=hash_password(password),
        matricule=request.get("matricule", "RH-001"),
        role=RoleEnum.RH,
        est_actif=True
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
    """Envoyer un email de réinitialisation de mot de passe."""
    clean_email = request.email.strip().lower()
    user = db.query(Utilisateur).filter(func.lower(Utilisateur.email) == clean_email).first()

    # Ne jamais divulguer si l'email existe ou non.
    if not user:
        return {"message": "Si cet email est enregistré, un lien de réinitialisation vous a été envoyé."}

    if not user.est_actif:
        return {"message": "Si cet email est enregistré, un lien de réinitialisation vous a été envoyé."}

    raw_token = create_reset_token(user, db)
    reset_url = _build_reset_url(raw_token)

    email_sent = envoyer_email_reinitialisation(
        destinataire=user.email,
        prenom=user.prenom,
        reset_url=reset_url
    )

    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible d'envoyer l'email. Veuillez vérifier la configuration SMTP."
        )

    return {"message": "Si cet email est enregistré, un lien de réinitialisation vous a été envoyé."}


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, request_http: Request, db: Session = Depends(get_db)):
    """Réinitialiser le mot de passe à l'aide d'un token valide et à usage unique."""
    rt = verify_reset_token(request.token, db)
    if not rt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le lien de réinitialisation est invalide ou a déjà été utilisé."
        )

    user = rt.utilisateur
    if not user or not user.est_actif:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le lien de réinitialisation est invalide."
        )

    ok, msg = validate_password(request.nouveau_mot_de_passe)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    user.mot_de_passe_hash = hash_password(request.nouveau_mot_de_passe)
    mark_reset_token_used(rt, db)
    reset_login_attempts(user, db)
    db.commit()

    # Révoquer tous les refresh tokens existants pour forcer la reconnexion.
    revoke_all_user_refresh_tokens(user.id, db)

    _notify_password_changed(user)

    log_action(
        db=db, utilisateur_id=user.id,
        action=AuditActionEnum.PASSWORD_RESET.value, entite=AuditEntiteEnum.AUTH.value, entite_id=user.id,
        description=f"Réinitialisation du mot de passe pour {user.email}",
        request=request_http,
    )

    return {"message": "Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter."}
