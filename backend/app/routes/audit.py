import math
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.models import AuditLog, Utilisateur
from app.schemas.schemas import AuditLogResponse, AuditLogPaginatedResponse
from app.core.security import require_any_role

router = APIRouter(prefix="/api/audit", tags=["Audit"])


def _to_response(log: AuditLog) -> AuditLogResponse:
    return AuditLogResponse(
        id=log.id,
        utilisateur_id=log.utilisateur_id,
        utilisateur_nom=f"{log.utilisateur.prenom} {log.utilisateur.nom}" if log.utilisateur else None,
        action=log.action,
        entite=log.entite,
        entite_id=log.entite_id,
        description=log.description,
        anciennes_valeurs=log.anciennes_valeurs,
        nouvelles_valeurs=log.nouvelles_valeurs,
        date_action=log.date_action,
        ip_address=log.ip_address,
    )


@router.get("/", response_model=AuditLogPaginatedResponse)
def lister_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: Optional[str] = Query(None),
    entite: Optional[str] = Query(None),
    utilisateur_id: Optional[int] = Query(None),
    date_debut: Optional[date] = Query(None),
    date_fin: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_any_role("RH", "ADMIN")),
):
    """
    Lister l'historique des activites avec pagination et filtres.
    Reserve aux roles RH et ADMIN.
    """
    query = db.query(AuditLog).options(joinedload(AuditLog.utilisateur))

    if action:
        query = query.filter(AuditLog.action == action)
    if entite:
        query = query.filter(AuditLog.entite == entite)
    if utilisateur_id:
        query = query.filter(AuditLog.utilisateur_id == utilisateur_id)
    if date_debut:
        query = query.filter(AuditLog.date_action >= datetime.combine(date_debut, datetime.min.time()))
    if date_fin:
        query = query.filter(AuditLog.date_action <= datetime.combine(date_fin, datetime.max.time()))
    if search:
        search_lower = f"%{search.lower()}%"
        query = query.filter(func.lower(AuditLog.description).like(search_lower))

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    page = min(page, total_pages)

    logs = (
        query.order_by(AuditLog.date_action.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return AuditLogPaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=[_to_response(log) for log in logs],
    )


@router.get("/{log_id}", response_model=AuditLogResponse)
def get_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_any_role("RH", "ADMIN")),
):
    """Consulter le detail d'une entree d'audit. Reserve aux roles RH et ADMIN."""
    log = db.query(AuditLog).options(joinedload(AuditLog.utilisateur)).filter(AuditLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entree d'audit non trouvee")
    return _to_response(log)
