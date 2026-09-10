from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.models import Article, Utilisateur, AuditActionEnum, AuditEntiteEnum
from app.schemas.schemas import ArticleCreate, ArticleUpdate, ArticleResponse
from app.core.security import get_current_user_optional
from app.core.audit_service import log_action, diff_valeurs

router = APIRouter(prefix="/api/articles", tags=["Articles"])


@router.get("/", response_model=list[ArticleResponse])
def get_articles(
    search: Optional[str] = Query(None),
    actif_only: Optional[bool] = Query(None),
    type_contrat: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Recuperer la liste des articles avec recherche et filtrage par type de contrat optionnels."""
    query = db.query(Article)

    if search:
        search_lower = f"%{search.lower()}%"
        query = query.filter(
            (func.lower(Article.code).like(search_lower)) |
            (func.lower(Article.titre).like(search_lower))
        )

    if actif_only is not None:
        query = query.filter(Article.est_actif == actif_only)

    articles = query.order_by(Article.code).all()

    if type_contrat:
        tc = type_contrat.strip().upper()
        articles = [
            a for a in articles
            if not a.types_contrat or len(a.types_contrat) == 0 or tc in [str(t).upper() for t in a.types_contrat]
        ]

    return articles


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(article_id: int, db: Session = Depends(get_db)):
    """Recuperer un article par son ID."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article non trouve"
        )
    return article


@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
def create_article(
    article_data: ArticleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[Utilisateur] = Depends(get_current_user_optional)
):
    """Creer un nouvel article."""
    # Verifier unicite du code
    existing = db.query(Article).filter(
        func.lower(Article.code) == article_data.code.strip().lower()
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Un article avec le code '{article_data.code}' existe deja."
        )

    tc_list = None
    if article_data.types_contrat is not None:
        tc_list = [str(t).strip().upper() for t in article_data.types_contrat if str(t).strip()]
        if len(tc_list) == 0:
            tc_list = None

    new_article = Article(
        code=article_data.code.strip().upper(),
        titre=article_data.titre.strip(),
        contenu_par_defaut=article_data.contenu_par_defaut,
        types_contrat=tc_list,
        est_actif=True,
        modifie_le=datetime.utcnow()
    )
    db.add(new_article)
    db.commit()
    db.refresh(new_article)

    log_action(
        db=db,
        utilisateur_id=current_user.id if current_user else None,
        action=AuditActionEnum.CREATE.value,
        entite=AuditEntiteEnum.ARTICLE.value,
        entite_id=new_article.id,
        description=f"Création de l'article {new_article.code} - {new_article.titre}",
        nouvelles_valeurs={
            "code": new_article.code,
            "titre": new_article.titre,
            "est_actif": new_article.est_actif,
            "types_contrat": new_article.types_contrat,
        },
        request=request,
    )

    return new_article


@router.put("/{article_id}", response_model=ArticleResponse)
def update_article(
    article_id: int,
    article_data: ArticleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[Utilisateur] = Depends(get_current_user_optional)
):
    """Modifier un article existant."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article non trouve"
        )

    avant = {
        "code": article.code,
        "titre": article.titre,
        "contenu_par_defaut": article.contenu_par_defaut,
        "est_actif": article.est_actif,
        "types_contrat": article.types_contrat,
    }

    if article_data.code is not None:
        # Verifier unicite du nouveau code
        existing = db.query(Article).filter(
            func.lower(Article.code) == article_data.code.strip().lower(),
            Article.id != article_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Un article avec le code '{article_data.code}' existe deja."
            )
        article.code = article_data.code.strip().upper()

    if article_data.titre is not None:
        article.titre = article_data.titre.strip()
    if article_data.contenu_par_defaut is not None:
        article.contenu_par_defaut = article_data.contenu_par_defaut
    if article_data.est_actif is not None:
        article.est_actif = article_data.est_actif
    if article_data.types_contrat is not None:
        tc_list = [str(t).strip().upper() for t in article_data.types_contrat if str(t).strip()]
        article.types_contrat = tc_list if len(tc_list) > 0 else None

    article.modifie_le = datetime.utcnow()

    db.commit()
    db.refresh(article)

    apres = {
        "code": article.code,
        "titre": article.titre,
        "contenu_par_defaut": article.contenu_par_defaut,
        "est_actif": article.est_actif,
    }
    anciennes, nouvelles = diff_valeurs(avant, apres)

    log_action(
        db=db,
        utilisateur_id=current_user.id if current_user else None,
        action=AuditActionEnum.UPDATE.value,
        entite=AuditEntiteEnum.ARTICLE.value,
        entite_id=article.id,
        description=f"Modification de l'article {article.code}",
        anciennes_valeurs=anciennes,
        nouvelles_valeurs=nouvelles,
        request=request,
    )

    return article


@router.delete("/{article_id}")
def delete_article(
    article_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[Utilisateur] = Depends(get_current_user_optional)
):
    """Supprimer un article."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article non trouve"
        )

    code, titre, article_id_captured = article.code, article.titre, article.id

    db.delete(article)
    db.commit()

    log_action(
        db=db,
        utilisateur_id=current_user.id if current_user else None,
        action=AuditActionEnum.DELETE.value,
        entite=AuditEntiteEnum.ARTICLE.value,
        entite_id=article_id_captured,
        description=f"Suppression de l'article {code} - {titre}",
        request=request,
    )
    return {"message": "Article supprime avec succes"}


@router.patch("/{article_id}/toggle", response_model=ArticleResponse)
def toggle_article(
    article_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[Utilisateur] = Depends(get_current_user_optional)
):
    """Activer/Desactiver un article (toggle)."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article non trouve"
        )

    article.est_actif = not article.est_actif
    article.modifie_le = datetime.utcnow()
    db.commit()
    db.refresh(article)

    action = AuditActionEnum.ACTIVATE.value if article.est_actif else AuditActionEnum.DEACTIVATE.value
    verbe = "Activation" if article.est_actif else "Désactivation"

    log_action(
        db=db,
        utilisateur_id=current_user.id if current_user else None,
        action=action,
        entite=AuditEntiteEnum.ARTICLE.value,
        entite_id=article.id,
        description=f"{verbe} de l'article {article.code}",
        request=request,
    )

    return article
