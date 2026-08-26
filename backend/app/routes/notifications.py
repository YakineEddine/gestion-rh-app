import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Notification, Utilisateur
from app.schemas.schemas import NotificationPaginatedResponse, NotificationResponse, UnreadCountResponse
from app.core.security import get_current_user, require_role
from app.core.notification_service import (
    compter_non_lues,
    marquer_comme_lue,
    marquer_toutes_comme_lues,
    verifier_alertes_contrats,
)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("/", response_model=NotificationPaginatedResponse)
def lister_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    est_lue: Optional[bool] = Query(None),
    priorite: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
):
    """
    Lister les notifications de l'utilisateur connecte, avec pagination et
    filtres. Un utilisateur ne voit jamais les notifications d'un autre
    utilisateur (filtre systematique par utilisateur_id).
    """
    query = db.query(Notification).filter(Notification.utilisateur_id == current_user.id)

    if est_lue is not None:
        query = query.filter(Notification.est_lue == est_lue)
    if priorite:
        query = query.filter(Notification.priorite == priorite)
    if type:
        query = query.filter(Notification.type == type)

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    page = min(page, total_pages)

    items = (
        query.order_by(Notification.date_creation.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return NotificationPaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        unread_count=compter_non_lues(db, current_user.id),
        items=items,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def unread_count(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
):
    """Nombre d'alertes non lues pour l'utilisateur connecte."""
    return UnreadCountResponse(unread_count=compter_non_lues(db, current_user.id))


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def marquer_lue(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
):
    """Marquer une notification comme lue (uniquement si elle appartient a l'utilisateur)."""
    notif = marquer_comme_lue(db, notification_id, current_user.id)
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification non trouvée")
    return notif


@router.post("/mark-all-read")
def marquer_toutes_lues(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
):
    """Marquer toutes les notifications de l'utilisateur connecte comme lues."""
    nb = marquer_toutes_comme_lues(db, current_user.id)
    return {"message": f"{nb} notification(s) marquée(s) comme lue(s)"}


@router.post("/generer")
def generer_alertes_maintenant(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("RH")),
):
    """
    Declenche manuellement la verification des alertes (utile pour tester
    ou rafraichir a la demande). Le meme moteur tourne aussi automatiquement
    en arriere-plan a intervalles reguliers (voir app/main.py).
    """
    nb = verifier_alertes_contrats(db)
    return {"message": f"{nb} nouvelle(s) alerte(s) générée(s)"}
