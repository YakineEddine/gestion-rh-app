import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.database import get_db
from app.models.models import RefreshToken, ResetToken, Utilisateur

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "cle_secrete_par_defaut")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
LOGIN_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
LOGIN_LOCKOUT_MINUTES = int(os.getenv("LOGIN_LOCKOUT_MINUTES", "15"))
PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))

# Schéma OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
# Variante qui ne leve pas d'erreur si aucun token n'est fourni (routes publiques
# pouvant neanmoins identifier l'utilisateur si un token est present, ex: audit).
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _token_hash(raw_token: str) -> str:
    """Haché déterministe d'un token opaque (refresh ou reset)."""
    return hmac.new(SECRET_KEY.encode("utf-8"), raw_token.encode("utf-8"), hashlib.sha256).hexdigest()


def _generate_opaque_token(prefix: str = "") -> str:
    """Génère un token opaque cryptographiquement sécurisé."""
    return f"{prefix}{secrets.token_urlsafe(32)}"


def hash_password(password: str) -> str:
    """Hacher un mot de passe en clair avec bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifier un mot de passe en clair contre son hash bcrypt."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def validate_password(password: str) -> tuple[bool, str]:
    """
    Vérifie la robustesse minimale du mot de passe.
    Retourne (True, "") si valide, sinon (False, message_explicite).
    """
    if not password:
        return False, "Le mot de passe est obligatoire."
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Le mot de passe doit contenir au moins {PASSWORD_MIN_LENGTH} caractères."
    if not re.search(r"[A-Z]", password):
        return False, "Le mot de passe doit contenir au moins une majuscule."
    if not re.search(r"[a-z]", password):
        return False, "Le mot de passe doit contenir au moins une minuscule."
    if not re.search(r"[0-9]", password):
        return False, "Le mot de passe doit contenir au moins un chiffre."
    if not re.search(r"[^A-Za-z0-9]", password):
        return False, "Le mot de passe doit contenir au moins un caractère spécial."
    return True, ""


def is_account_locked(user: Utilisateur) -> tuple[bool, Optional[datetime]]:
    """Indique si le compte est actuellement bloqué et jusqu'à quand."""
    if user.locked_until and user.locked_until > datetime.utcnow():
        return True, user.locked_until
    return False, None


def record_failed_login(user: Utilisateur, db: Session) -> bool:
    """
    Incrémente le compteur d'échecs et bloque le compte si le seuil est atteint.
    Retourne True si le compte vient d'être bloqué.
    """
    user.login_attempts = (user.login_attempts or 0) + 1
    user.last_failed_login = datetime.utcnow()

    if user.login_attempts >= LOGIN_MAX_ATTEMPTS:
        user.locked_until = datetime.utcnow() + timedelta(minutes=LOGIN_LOCKOUT_MINUTES)
        return True
    return False


def reset_login_attempts(user: Utilisateur, db: Session) -> None:
    """Réinitialise le compteur d'échecs et le blocage après une connexion réussie."""
    user.login_attempts = 0
    user.locked_until = None
    user.last_failed_login = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Créer un token JWT d'accès."""
    to_encode = {"type": "access"}
    to_encode.update({k: v for k, v in data.items() if k not in ("mot_de_passe", "password", "mot_de_passe_hash")})
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user: Utilisateur, db: Session) -> str:
    """
    Crée un refresh token opaque, le stocke sous forme de hash et retourne la valeur en clair.
    """
    raw_token = _generate_opaque_token("rt_")
    token_hash = _token_hash(raw_token)
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    rt = RefreshToken(
        utilisateur_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(rt)
    db.commit()
    return raw_token


def verify_refresh_token(raw_token: str, db: Session) -> Optional[RefreshToken]:
    """Vérifie un refresh token et retourne l'entrée correspondante si valide."""
    if not raw_token:
        return None
    token_hash = _token_hash(raw_token)
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if not rt:
        return None
    if rt.revoked or rt.expires_at < datetime.utcnow():
        return None
    return rt


def revoke_refresh_token(raw_token: str, db: Session) -> bool:
    """Révoque un refresh token donné."""
    rt = verify_refresh_token(raw_token, db)
    if not rt:
        return False
    rt.revoked = True
    rt.revoked_at = datetime.utcnow()
    db.commit()
    return True


def revoke_all_user_refresh_tokens(user_id: int, db: Session) -> None:
    """Révoque tous les refresh tokens d'un utilisateur (utile au logout)."""
    db.query(RefreshToken).filter(
        RefreshToken.utilisateur_id == user_id,
        RefreshToken.revoked == False,
    ).update({
        "revoked": True,
        "revoked_at": datetime.utcnow(),
    })
    db.commit()


def rotate_refresh_token(old_token: RefreshToken, db: Session) -> str:
    """Révoque l'ancien refresh token et en génère un nouveau."""
    old_token.revoked = True
    old_token.revoked_at = datetime.utcnow()
    db.commit()
    return create_refresh_token(old_token.utilisateur, db)


def create_reset_token(user: Utilisateur, db: Session) -> str:
    """
    Crée un token de réinitialisation opaque, le stocke sous forme de hash et retourne la valeur en clair.
    """
    raw_token = _generate_opaque_token("rp_")
    token_hash = _token_hash(raw_token)
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    rt = ResetToken(
        utilisateur_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(rt)
    db.commit()
    return raw_token


def verify_reset_token(raw_token: str, db: Session) -> Optional[ResetToken]:
    """Vérifie un token de réinitialisation et retourne l'entrée correspondante si valide."""
    if not raw_token:
        return None
    token_hash = _token_hash(raw_token)
    rt = db.query(ResetToken).filter(ResetToken.token_hash == token_hash).first()
    if not rt:
        return None
    if rt.used_at or rt.expires_at < datetime.utcnow():
        return None
    return rt


def mark_reset_token_used(rt: ResetToken, db: Session) -> None:
    """Marque un token de réinitialisation comme utilisé."""
    rt.used_at = datetime.utcnow()
    db.commit()


def decode_token(token: str) -> dict:
    """Décode et vérifie un JWT. Lève JWTError en cas d'invalidité/expériation."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Utilisateur:
    """Extraire l'utilisateur courant à partir du token JWT et vérifier son état."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        token_type = payload.get("type")
        if token_type != "access":
            raise credentials_exception
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(Utilisateur).filter(Utilisateur.email == email).first()
    if user is None:
        raise credentials_exception

    # Un compte désactivé ne doit pas pouvoir accéder, même avec un JWT valide.
    if not user.est_actif:
        raise credentials_exception

    # Même si un JWT est valide, un compte toujours verrouillé est refusé.
    locked, _ = is_account_locked(user)
    if locked:
        raise credentials_exception

    return user


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
) -> Optional[Utilisateur]:
    """
    Variante non bloquante de get_current_user : retourne None si aucun token
    valide n'est fourni, au lieu de lever une exception 401.
    """
    if not token:
        return None
    try:
        payload = decode_token(token)
        email: str = payload.get("sub")
        if not email or payload.get("type") != "access":
            return None
    except JWTError:
        return None
    user = db.query(Utilisateur).filter(Utilisateur.email == email).first()
    if user is None or not user.est_actif:
        return None
    locked, _ = is_account_locked(user)
    if locked:
        return None
    return user


def require_role(required_role: str):
    """Dépendance pour vérifier le rôle de l'utilisateur."""
    def role_checker(current_user: Utilisateur = Depends(get_current_user)):
        if current_user.role.value != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès refusé. Rôle requis : {required_role}"
            )
        return current_user
    return role_checker


def require_any_role(*allowed_roles: str):
    """Dépendance pour vérifier que l'utilisateur a l'un des rôles autorisés."""
    def role_checker(current_user: Utilisateur = Depends(get_current_user)):
        if current_user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé. Rôle insuffisant."
            )
        return current_user
    return role_checker


def create_direct_access_token(
    user_id: int,
    email: str,
    purpose: str = "contract_notification",
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crée un token JWT signé pour un accès direct depuis un email de notification.
    Permet à l'employé de consulter immédiatement son espace sans être bloqué
    par une session tierce (ex: compte RH/ADMIN précédemment connecté sur le navigateur).
    """
    to_encode = {
        "sub": email,
        "user_id": user_id,
        "purpose": purpose,
        "type": "direct_access",
    }
    expire = datetime.utcnow() + (expires_delta or timedelta(days=14))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_direct_access_token(token: str, db: Session) -> Optional[Utilisateur]:
    """
    Vérifie un direct_access_token et retourne l'utilisateur correspondant s'il est valide et actif.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "direct_access":
            return None
        user_id = payload.get("user_id")
        email = payload.get("sub")
        if not user_id or not email:
            return None
        user = db.query(Utilisateur).filter(
            Utilisateur.id == user_id,
            Utilisateur.email == email,
            Utilisateur.est_actif == True
        ).first()
        return user
    except JWTError:
        return None

