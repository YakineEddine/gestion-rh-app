"""
Service centralise d'audit / historique des activites.

Objectif : offrir un point d'entree unique pour enregistrer les actions
importantes effectuees dans l'application (creation, modification,
suppression, connexion, generation de documents, etc.) sans dupliquer
la logique dans chaque route.

Regle de securite : ne jamais enregistrer de mots de passe, de tokens JWT,
de refresh tokens ou toute autre information sensible dans les logs.
"""
import enum
from datetime import date, datetime
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.models import AuditLog


def _serialize(value):
    """Rend une valeur compatible JSON (dates, enums, etc.)."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, enum.Enum):
        return value.value
    return value


def diff_valeurs(avant: dict, apres: dict) -> tuple[Optional[dict], Optional[dict]]:
    """
    Compare deux instantanes de champs et ne conserve que ceux qui ont
    reellement change. Evite d'enregistrer des objets complets dans l'audit.

    Retourne (anciennes_valeurs, nouvelles_valeurs), ou (None, None) si rien
    n'a change, pour eviter d'afficher des sections vides inutilement.
    """
    anciennes: dict = {}
    nouvelles: dict = {}
    for cle in apres:
        ancienne_val = _serialize(avant.get(cle))
        nouvelle_val = _serialize(apres.get(cle))
        if ancienne_val != nouvelle_val:
            anciennes[cle] = ancienne_val
            nouvelles[cle] = nouvelle_val
    if not anciennes and not nouvelles:
        return None, None
    return anciennes, nouvelles


def log_action(
    db: Session,
    utilisateur_id: Optional[int],
    action: str,
    entite: str,
    entite_id: Optional[int] = None,
    description: str = "",
    anciennes_valeurs: Optional[dict] = None,
    nouvelles_valeurs: Optional[dict] = None,
    request: Optional[Request] = None,
) -> Optional[AuditLog]:
    """
    Enregistre une entree dans le journal d'audit.

    Un echec d'enregistrement de l'audit ne doit JAMAIS faire echouer
    l'operation metier principale : les erreurs sont capturees et la
    transaction d'audit est annulee isolement, sans propager l'exception.
    """
    ip_address = None
    if request is not None:
        try:
            ip_address = request.client.host if request.client else None
        except Exception:
            ip_address = None

    try:
        entry = AuditLog(
            utilisateur_id=utilisateur_id,
            action=action,
            entite=entite,
            entite_id=entite_id,
            description=description,
            anciennes_valeurs={k: _serialize(v) for k, v in anciennes_valeurs.items()} if anciennes_valeurs else None,
            nouvelles_valeurs={k: _serialize(v) for k, v in nouvelles_valeurs.items()} if nouvelles_valeurs else None,
            ip_address=ip_address,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    except Exception:
        db.rollback()
        return None
