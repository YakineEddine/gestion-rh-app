"""
Routes API pour l'assistant IA de generation de clauses contractuelles.
Accessibles uniquement aux roles RH et ADMIN.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Utilisateur, AuditActionEnum, AuditEntiteEnum
from app.core.security import require_any_role
from app.core.audit_service import log_action
from app.core.ai_service import generate_clause, is_configured

router = APIRouter(prefix="/api/ai", tags=["Assistant IA"])


class AIGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="Description de la clause à générer")


class AIGenerateResponse(BaseModel):
    title: str
    content: str
    category: str


@router.get("/status")
def ai_status():
    """Vérifie si le service IA est configuré (sans exposer la clé)."""
    return {"configured": is_configured()}


@router.post("/articles/generate", response_model=AIGenerateResponse)
def generate_article_clause(
    payload: AIGenerateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_any_role("RH", "ADMIN")),
):
    """
    Génère une proposition de clause contractuelle via l'IA.
    Le résultat N'EST PAS enregistré automatiquement :
    le RH doit relire, modifier si nécessaire, puis enregistrer manuellement.
    """
    try:
        result = generate_clause(payload.prompt)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    # Audit : tracer la génération IA (sans le contenu complet ni la clé API)
    log_action(
        db=db,
        utilisateur_id=current_user.id,
        action=AuditActionEnum.AI_GENERATE.value,
        entite=AuditEntiteEnum.ARTICLE.value,
        description=f"Proposition de clause générée par IA : \"{result['title']}\"",
        nouvelles_valeurs={
            "titre_genere": result["title"],
            "categorie": result["category"],
            "prompt_resume": payload.prompt[:100] + ("..." if len(payload.prompt) > 100 else ""),
        },
        request=request,
    )

    return AIGenerateResponse(**result)
