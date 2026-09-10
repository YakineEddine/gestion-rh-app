from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional, List
from datetime import date, datetime

from app.database import get_db
from app.models.models import Contrat, Article, Utilisateur, AuditLog, Notification, TypeContratEnum, StatutContratEnum, AuditActionEnum, AuditEntiteEnum
from app.schemas.schemas import ContratCreate, ContratUpdate, ContratResponse, ContratHistoriqueStatutResponse
from app.core.security import require_role, require_any_role, create_direct_access_token
from app.core.document_generator import generer_contrat_word
from app.core.audit_service import log_action, diff_valeurs
from app.core.notification_service import verifier_alertes_contrats
from app.core.email_service import send_email, template_contract_activated, template_contract_status_change

router = APIRouter(prefix="/api/contrats", tags=["Contrats"])


def _rafraichir_alertes(db: Session) -> None:
    """
    Relance immediatement la detection des alertes apres une creation/
    modification de contrat, en complement de la tache periodique de fond
    (voir app/main.py) et du declenchement manuel RH (/notifications/generer).

    Sans ce declenchement immediat, un contrat cree ou modifie entre deux
    executions de la tache planifiee (jusqu'a 6h d'ecart) ne generait aucune
    alerte tant que la boucle de fond ou un appel manuel n'avait pas ete
    execute depuis. Ne doit jamais faire echouer l'operation sur le contrat.
    """
    try:
        verifier_alertes_contrats(db)
    except Exception as e:
        print(f"[alertes] Echec de la verification immediate apres modification de contrat : {e}")


def generer_reference(db: Session) -> str:
    """Générer une référence unique au format CTR-YYYY-NNNN."""
    annee = date.today().year
    dernier = db.query(Contrat).filter(
        Contrat.reference.like(f"CTR-{annee}-%")
    ).order_by(Contrat.reference.desc()).first()

    if dernier:
        try:
            num = int(dernier.reference.split("-")[-1]) + 1
        except (ValueError, IndexError):
            num = 1
    else:
        num = 1

    return f"CTR-{annee}-{num:04d}"


@router.get("/", response_model=List[ContratResponse])
def get_contrats(
    statut: Optional[str] = Query(None),
    employe_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    archivage: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("RH"))
):
    """Lister tous les contrats avec filtres optionnels (archivage: ACTIFS, ARCHIVES, TOUS)."""
    query = db.query(Contrat).options(
        joinedload(Contrat.employe),
        joinedload(Contrat.articles)
    )

    if statut:
        norm_statut = normaliser_statut(statut)
        query = query.filter((Contrat.statut == statut) | (Contrat.statut == norm_statut))
    elif archivage == "ARCHIVES":
        query = query.filter(Contrat.statut == StatutContratEnum.INACTIF.value)
    elif archivage == "TOUS":
        pass  # Ne pas filtrer par archivage
    else:
        # Par defaut ("ACTIFS"), masquer les contrats inactifs/archives
        query = query.filter(Contrat.statut != StatutContratEnum.INACTIF.value)

    if employe_id:
        query = query.filter(Contrat.employe_id == employe_id)

    if search:
        search_lower = f"%{search.lower()}%"
        matching_employe_ids = [
            row[0] for row in db.query(Utilisateur.id).filter(
                func.lower(Utilisateur.nom).like(search_lower) |
                func.lower(Utilisateur.prenom).like(search_lower) |
                func.lower(Utilisateur.matricule).like(search_lower)
            ).all()
        ]
        query = query.filter(
            func.lower(Contrat.reference).like(search_lower) |
            Contrat.employe_id.in_(matching_employe_ids)
        )

    return query.order_by(Contrat.reference.desc()).all()


@router.get("/employe/{employe_id}/historique-statuts", response_model=List[ContratHistoriqueStatutResponse])
def get_historique_statuts_employe(
    employe_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_any_role("RH", "ADMIN"))
):
    """
    Récupérer l'historique chronologique des modifications de statut
    pour l'ensemble des contrats d'un employé.
    """
    employe = db.query(Utilisateur).filter(Utilisateur.id == employe_id).first()
    if not employe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")

    contrats = db.query(Contrat).filter(Contrat.employe_id == employe_id).all()
    contrat_map = {c.id: c for c in contrats}
    contrat_ids = list(contrat_map.keys())

    if not contrat_ids:
        return []

    logs = (
        db.query(AuditLog)
        .options(joinedload(AuditLog.utilisateur))
        .filter(
            AuditLog.entite == AuditEntiteEnum.CONTRAT.value,
            AuditLog.entite_id.in_(contrat_ids),
            AuditLog.action.in_([
                AuditActionEnum.STATUS_CHANGE.value,
                AuditActionEnum.CREATE.value,
                AuditActionEnum.UPDATE.value,
            ])
        )
        .order_by(AuditLog.date_action.desc())
        .all()
    )

    result = []
    contrats_with_creation_log = set()

    for log in logs:
        ancien_statut = None
        nouveau_statut = None

        if log.action == AuditActionEnum.STATUS_CHANGE.value:
            if log.anciennes_valeurs and "statut" in log.anciennes_valeurs:
                ancien_statut = log.anciennes_valeurs["statut"]
            if log.nouvelles_valeurs and "statut" in log.nouvelles_valeurs:
                nouveau_statut = log.nouvelles_valeurs["statut"]
            if not nouveau_statut and "→" in (log.description or ""):
                parts = log.description.split("→")
                if len(parts) == 2:
                    nouveau_statut = parts[1].strip()
                    ancien_statut = parts[0].split(":")[-1].strip()
        elif log.action == AuditActionEnum.CREATE.value:
            contrats_with_creation_log.add(log.entite_id)
            if log.nouvelles_valeurs and "statut" in log.nouvelles_valeurs:
                nouveau_statut = log.nouvelles_valeurs["statut"]
            elif log.entite_id in contrat_map:
                nouveau_statut = contrat_map[log.entite_id].statut
            else:
                nouveau_statut = "Brouillon"
            ancien_statut = None
        elif log.action == AuditActionEnum.UPDATE.value:
            if (log.nouvelles_valeurs and "statut" in log.nouvelles_valeurs) or (log.anciennes_valeurs and "statut" in log.anciennes_valeurs):
                nouveau_statut = log.nouvelles_valeurs.get("statut") if log.nouvelles_valeurs else None
                ancien_statut = log.anciennes_valeurs.get("statut") if log.anciennes_valeurs else None
            else:
                continue

        if not ancien_statut and not nouveau_statut:
            continue

        contrat_obj = contrat_map.get(log.entite_id)
        ref = contrat_obj.reference if contrat_obj else f"CTR-{log.entite_id}"
        nom_auteur = f"{log.utilisateur.prenom} {log.utilisateur.nom}" if log.utilisateur else "Système"

        result.append(ContratHistoriqueStatutResponse(
            id=log.id,
            contrat_id=log.entite_id,
            contrat_reference=ref,
            action=log.action,
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            description=log.description or f"Changement de statut: {ancien_statut} → {nouveau_statut}",
            date_action=log.date_action,
            utilisateur_id=log.utilisateur_id,
            utilisateur_nom=nom_auteur,
        ))

    for c in contrats:
        if c.id not in contrats_with_creation_log:
            c_date = datetime.combine(c.date_creation, datetime.min.time()) if isinstance(c.date_creation, date) else c.date_creation
            result.append(ContratHistoriqueStatutResponse(
                id=c.id * 1000000,
                contrat_id=c.id,
                contrat_reference=c.reference,
                action="CREATE",
                ancien_statut=None,
                nouveau_statut=c.statut,
                description=f"Création du contrat {c.reference} (Statut initial: {c.statut})",
                date_action=c_date,
                utilisateur_id=None,
                utilisateur_nom="Système",
            ))

    result.sort(key=lambda x: x.date_action, reverse=True)
    return result


@router.get("/{contrat_id}/historique-statuts", response_model=List[ContratHistoriqueStatutResponse])
def get_historique_statuts_contrat(
    contrat_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_any_role("RH", "ADMIN"))
):
    """
    Récupérer l'historique chronologique des modifications de statut
    pour un contrat spécifique.
    """
    contrat = db.query(Contrat).filter(Contrat.id == contrat_id).first()
    if not contrat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat non trouvé")

    logs = (
        db.query(AuditLog)
        .options(joinedload(AuditLog.utilisateur))
        .filter(
            AuditLog.entite == AuditEntiteEnum.CONTRAT.value,
            AuditLog.entite_id == contrat_id,
            AuditLog.action.in_([
                AuditActionEnum.STATUS_CHANGE.value,
                AuditActionEnum.CREATE.value,
                AuditActionEnum.UPDATE.value,
            ])
        )
        .order_by(AuditLog.date_action.desc())
        .all()
    )

    result = []
    has_creation_log = False

    for log in logs:
        ancien_statut = None
        nouveau_statut = None

        if log.action == AuditActionEnum.STATUS_CHANGE.value:
            if log.anciennes_valeurs and "statut" in log.anciennes_valeurs:
                ancien_statut = log.anciennes_valeurs["statut"]
            if log.nouvelles_valeurs and "statut" in log.nouvelles_valeurs:
                nouveau_statut = log.nouvelles_valeurs["statut"]
            if not nouveau_statut and "→" in (log.description or ""):
                parts = log.description.split("→")
                if len(parts) == 2:
                    nouveau_statut = parts[1].strip()
                    ancien_statut = parts[0].split(":")[-1].strip()
        elif log.action == AuditActionEnum.CREATE.value:
            has_creation_log = True
            if log.nouvelles_valeurs and "statut" in log.nouvelles_valeurs:
                nouveau_statut = log.nouvelles_valeurs["statut"]
            else:
                nouveau_statut = contrat.statut
            ancien_statut = None
        elif log.action == AuditActionEnum.UPDATE.value:
            if (log.nouvelles_valeurs and "statut" in log.nouvelles_valeurs) or (log.anciennes_valeurs and "statut" in log.anciennes_valeurs):
                nouveau_statut = log.nouvelles_valeurs.get("statut") if log.nouvelles_valeurs else None
                ancien_statut = log.anciennes_valeurs.get("statut") if log.anciennes_valeurs else None
            else:
                continue

        if not ancien_statut and not nouveau_statut:
            continue

        nom_auteur = f"{log.utilisateur.prenom} {log.utilisateur.nom}" if log.utilisateur else "Système"
        result.append(ContratHistoriqueStatutResponse(
            id=log.id,
            contrat_id=contrat_id,
            contrat_reference=contrat.reference,
            action=log.action,
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            description=log.description or f"Changement de statut: {ancien_statut} → {nouveau_statut}",
            date_action=log.date_action,
            utilisateur_id=log.utilisateur_id,
            utilisateur_nom=nom_auteur,
        ))

    if not has_creation_log:
        c_date = datetime.combine(contrat.date_creation, datetime.min.time()) if isinstance(contrat.date_creation, date) else contrat.date_creation
        result.append(ContratHistoriqueStatutResponse(
            id=contrat.id * 1000000,
            contrat_id=contrat.id,
            contrat_reference=contrat.reference,
            action="CREATE",
            ancien_statut=None,
            nouveau_statut=contrat.statut,
            description=f"Création du contrat {contrat.reference} (Statut initial: {contrat.statut})",
            date_action=c_date,
            utilisateur_id=None,
            utilisateur_nom="Système",
        ))

    result.sort(key=lambda x: x.date_action, reverse=True)
    return result


@router.get("/{contrat_id}", response_model=ContratResponse)
def get_contrat(
    contrat_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("RH"))
):
    """Récupérer un contrat par son ID."""
    contrat = db.query(Contrat).options(
        joinedload(Contrat.employe),
        joinedload(Contrat.articles)
    ).filter(Contrat.id == contrat_id).first()

    if not contrat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat non trouvé")
    return contrat



def verifier_compatibilite_articles(articles: List[Article], type_contrat: str) -> None:
    """
    Vérifie que chaque article est compatible avec le type de contrat spécifié.
    Un article sans restriction (types_contrat None ou vide) est compatible avec tous les types.
    """
    if not articles:
        return
    tc_val = type_contrat.value if hasattr(type_contrat, "value") else str(type_contrat).upper()
    incompatibles = []
    for art in articles:
        if art.types_contrat:
            types_compatibles = [t.upper() for t in art.types_contrat]
            if tc_val not in types_compatibles:
                incompatibles.append(f"'{art.titre}' (compatible : {', '.join(types_compatibles)})")
    if incompatibles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Articles incompatibles avec le type de contrat {tc_val} : {'; '.join(incompatibles)}"
        )


@router.post("/", response_model=ContratResponse, status_code=status.HTTP_201_CREATED)
def create_contrat(
    data: ContratCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("RH"))
):
    """Créer un nouveau contrat."""
    employe = db.query(Utilisateur).filter(Utilisateur.id == data.employe_id).first()
    if not employe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")

    reference = generer_reference(db)

    # data.date_fin est deja normalisee a None pour un CDI par le schema ContratCreate
    init_statut = StatutContratEnum.BROUILLON.value
    if getattr(data, "statut", None):
        init_statut = normaliser_statut(data.statut)

    contrat = Contrat(
        reference=reference,
        type_contrat=data.type_contrat.value,
        date_creation=date.today(),
        date_debut=data.date_debut,
        date_fin=data.date_fin,
        salaire_mensuel=data.salaire_mensuel,
        statut=init_statut,
        employe_id=data.employe_id
    )
    db.add(contrat)
    db.flush()

    if data.article_ids:
        articles = db.query(Article).filter(Article.id.in_(data.article_ids)).all()
        verifier_compatibilite_articles(articles, data.type_contrat.value)
        contrat.articles = articles

    db.commit()

    contrat = db.query(Contrat).options(
        joinedload(Contrat.employe),
        joinedload(Contrat.articles)
    ).filter(Contrat.id == contrat.id).first()

    log_action(
        db=db,
        utilisateur_id=current_user.id,
        action=AuditActionEnum.CREATE.value,
        entite=AuditEntiteEnum.CONTRAT.value,
        entite_id=contrat.id,
        description=f"Création du contrat {contrat.reference}",
        nouvelles_valeurs={
            "type_contrat": contrat.type_contrat,
            "date_debut": contrat.date_debut,
            "date_fin": contrat.date_fin,
            "salaire_mensuel": contrat.salaire_mensuel,
            "statut": contrat.statut,
        },
        request=request,
    )

    _rafraichir_alertes(db)

    return contrat


# Correspondance et normalisation des statuts
STATUS_MAPPING = {
    "BROUILLON": StatutContratEnum.BROUILLON.value,
    "Brouillon": StatutContratEnum.BROUILLON.value,
    "COMMUNIQUE_EN_COURS": StatutContratEnum.COMMUNIQUE_EN_COURS.value,
    "Communiqué (en cours)": StatutContratEnum.COMMUNIQUE_EN_COURS.value,
    "SIGNE": StatutContratEnum.SIGNE.value,
    "Signé": StatutContratEnum.SIGNE.value,
    "ACTIF": StatutContratEnum.ACTIF.value,
    "Actif": StatutContratEnum.ACTIF.value,
    "FIN_CDD": StatutContratEnum.FIN_CDD.value,
    "Fin CDD": StatutContratEnum.FIN_CDD.value,
    "DEMISSION_CDI": StatutContratEnum.DEMISSION_CDI.value,
    "Démission (CDI)": StatutContratEnum.DEMISSION_CDI.value,
    "PAS_DISCUTE": StatutContratEnum.PAS_DISCUTE.value,
    "Pas discuté": StatutContratEnum.PAS_DISCUTE.value,
    "INACTIF": StatutContratEnum.INACTIF.value,
    "Inactif (archivé)": StatutContratEnum.INACTIF.value,
    "Inactif": StatutContratEnum.INACTIF.value,
    "Suspendu": StatutContratEnum.INACTIF.value,
    "Terminé": StatutContratEnum.INACTIF.value,
    "Termine": StatutContratEnum.INACTIF.value,
    "Expiré": StatutContratEnum.FIN_CDD.value,
    "Expire": StatutContratEnum.FIN_CDD.value,
}


def normaliser_statut(s: Optional[str]) -> str:
    if not s:
        return StatutContratEnum.BROUILLON.value
    clean = str(s).strip()
    return STATUS_MAPPING.get(clean, clean)


def get_allowed_transitions(statut_actuel: str, type_contrat: str) -> List[str]:
    """
    Règles métier de transition de statut :
    - BROUILLON -> COMMUNIQUE_EN_COURS, PAS_DISCUTE
    - COMMUNIQUE_EN_COURS -> SIGNE
    - SIGNE -> ACTIF
    - ACTIF :
        - CDD / STAGE / ALTERNANCE -> FIN_CDD
        - CDI -> DEMISSION_CDI
        - Retour vers BROUILLON strictement interdit
    - FIN_CDD -> INACTIF
    - DEMISSION_CDI -> INACTIF
    - PAS_DISCUTE -> COMMUNIQUE_EN_COURS, INACTIF
    - INACTIF -> Statut terminal archivé
    """
    statut = normaliser_statut(statut_actuel)
    tc = type_contrat.upper() if type_contrat else "CDI"

    if statut == StatutContratEnum.BROUILLON.value:
        return [
            StatutContratEnum.BROUILLON.value,
            StatutContratEnum.COMMUNIQUE_EN_COURS.value,
            StatutContratEnum.PAS_DISCUTE.value,
        ]
    elif statut == StatutContratEnum.COMMUNIQUE_EN_COURS.value:
        return [
            StatutContratEnum.COMMUNIQUE_EN_COURS.value,
            StatutContratEnum.SIGNE.value,
        ]
    elif statut == StatutContratEnum.SIGNE.value:
        return [
            StatutContratEnum.SIGNE.value,
            StatutContratEnum.ACTIF.value,
        ]
    elif statut == StatutContratEnum.ACTIF.value:
        if tc == TypeContratEnum.CDI.value:
            return [
                StatutContratEnum.ACTIF.value,
                StatutContratEnum.DEMISSION_CDI.value,
            ]
        else:
            return [
                StatutContratEnum.ACTIF.value,
                StatutContratEnum.FIN_CDD.value,
            ]
    elif statut == StatutContratEnum.FIN_CDD.value:
        return [
            StatutContratEnum.FIN_CDD.value,
            StatutContratEnum.INACTIF.value,
        ]
    elif statut == StatutContratEnum.DEMISSION_CDI.value:
        return [
            StatutContratEnum.DEMISSION_CDI.value,
            StatutContratEnum.INACTIF.value,
        ]
    elif statut == StatutContratEnum.PAS_DISCUTE.value:
        return [
            StatutContratEnum.PAS_DISCUTE.value,
            StatutContratEnum.COMMUNIQUE_EN_COURS.value,
            StatutContratEnum.INACTIF.value,
        ]
    elif statut == StatutContratEnum.INACTIF.value:
        return [StatutContratEnum.INACTIF.value]

    return [statut]


@router.put("/{contrat_id}", response_model=ContratResponse)
def update_contrat(
    contrat_id: int,
    data: ContratUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("RH"))
):
    """Modifier un contrat existant."""
    contrat = db.query(Contrat).filter(Contrat.id == contrat_id).first()
    if not contrat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat non trouvé")

    avant = {
        "type_contrat": contrat.type_contrat,
        "date_debut": contrat.date_debut,
        "date_fin": contrat.date_fin,
        "salaire_mensuel": contrat.salaire_mensuel,
        "statut": contrat.statut,
    }

    update_data = data.model_dump(exclude_unset=True)

    # Validation stricte des transitions de statut
    if "statut" in update_data and update_data["statut"] is not None:
        nouveau_statut = normaliser_statut(update_data["statut"])
        statut_actuel = normaliser_statut(contrat.statut or StatutContratEnum.BROUILLON.value)

        # Déterminer le type de contrat effectif (après éventuel update)
        tc_final = contrat.type_contrat
        if "type_contrat" in update_data and update_data["type_contrat"] is not None:
            tc = update_data["type_contrat"]
            tc_final = tc.value if hasattr(tc, "value") else str(tc)

        # Validation spécifique métier : incompatibilité type contrat
        if nouveau_statut == StatutContratEnum.FIN_CDD.value and tc_final == TypeContratEnum.CDI.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le statut 'Fin CDD' ne s'applique pas à un contrat de type CDI."
            )
        if nouveau_statut == StatutContratEnum.DEMISSION_CDI.value and tc_final != TypeContratEnum.CDI.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le statut 'Démission (CDI)' ne s'applique pas à un contrat CDD, STAGE, ALTERNANCE ou CIVP."
            )

        autorises = get_allowed_transitions(statut_actuel, tc_final)
        if nouveau_statut not in autorises:
            if statut_actuel == StatutContratEnum.ACTIF.value and nouveau_statut == StatutContratEnum.BROUILLON.value:
                detail_msg = "Transition de statut non autorisée : impossible de repasser un contrat Actif en Brouillon."
            else:
                detail_msg = f"Transition de statut non autorisée : impossible de passer de '{statut_actuel}' à '{nouveau_statut}'."
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail_msg
            )
        contrat.statut = nouveau_statut

    if "type_contrat" in update_data and update_data["type_contrat"] is not None:
        tc = update_data["type_contrat"]
        contrat.type_contrat = tc.value if hasattr(tc, "value") else tc
    if "date_debut" in update_data and update_data["date_debut"] is not None:
        contrat.date_debut = update_data["date_debut"]
    if "date_fin" in update_data:
        contrat.date_fin = update_data["date_fin"]
    if "salaire_mensuel" in update_data and update_data["salaire_mensuel"] is not None:
        contrat.salaire_mensuel = update_data["salaire_mensuel"]
    if "article_ids" in update_data:
        ids = update_data["article_ids"] or []
        contrat.articles = db.query(Article).filter(Article.id.in_(ids)).all() if ids else []

    if "article_ids" in update_data or "type_contrat" in update_data:
        verifier_compatibilite_articles(contrat.articles, contrat.type_contrat)

    # Regle metier : coherence type_contrat / date_fin, verifiee sur l'etat final
    # du contrat (que les champs impactes aient ete envoyes ou non dans cette requete).
    if contrat.type_contrat == TypeContratEnum.CDI.value:
        contrat.date_fin = None
    else:
        if not contrat.date_fin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La date de fin est obligatoire pour un contrat CDD, STAGE, ALTERNANCE ou CIVP."
            )
        if contrat.date_fin <= contrat.date_debut:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La date de fin doit être postérieure à la date de début."
            )

    db.commit()

    contrat = db.query(Contrat).options(
        joinedload(Contrat.employe),
        joinedload(Contrat.articles)
    ).filter(Contrat.id == contrat_id).first()

    apres = {
        "type_contrat": contrat.type_contrat,
        "date_debut": contrat.date_debut,
        "date_fin": contrat.date_fin,
        "salaire_mensuel": contrat.salaire_mensuel,
        "statut": contrat.statut,
    }

    # Un changement de statut est trace separement (STATUS_CHANGE), en plus
    # d'un eventuel UPDATE pour les autres champs modifies.
    if apres["statut"] != avant["statut"]:
        log_action(
            db=db,
            utilisateur_id=current_user.id,
            action=AuditActionEnum.STATUS_CHANGE.value,
            entite=AuditEntiteEnum.CONTRAT.value,
            entite_id=contrat.id,
            description=f"Contrat {contrat.reference} : {avant['statut']} → {apres['statut']}",
            anciennes_valeurs={"statut": avant["statut"]},
            nouvelles_valeurs={"statut": apres["statut"]},
            request=request,
        )

        # Si le contrat devient Actif, informer l'employé par email
        if (
            apres["statut"] in [StatutContratEnum.ACTIF.value, "Actif"]
            and avant["statut"] not in [StatutContratEnum.ACTIF.value, "Actif"]
            and contrat.employe
            and contrat.employe.email
        ):
            direct_tok = create_direct_access_token(contrat.employe.id, contrat.employe.email)
            html = template_contract_activated(
                prenom=contrat.employe.prenom,
                reference=contrat.reference,
                date_debut=contrat.date_debut.strftime("%d/%m/%Y"),
                direct_token=direct_tok,
            )
            email_ok = send_email(
                to=contrat.employe.email,
                subject=f"Votre contrat {contrat.reference} est disponible sur Enterprise RH",
                html_content=html,
            )
            if email_ok:
                log_action(
                    db=db,
                    utilisateur_id=current_user.id,
                    action=AuditActionEnum.EMAIL_SENT.value,
                    entite=AuditEntiteEnum.CONTRAT.value,
                    entite_id=contrat.id,
                    description=f"Email d'activation de contrat envoyé à l'employé ({contrat.employe.email})",
                    request=request,
                )

    avant_sans_statut = {k: v for k, v in avant.items() if k != "statut"}
    apres_sans_statut = {k: v for k, v in apres.items() if k != "statut"}
    anciennes, nouvelles = diff_valeurs(avant_sans_statut, apres_sans_statut)
    if anciennes or nouvelles:
        log_action(
            db=db,
            utilisateur_id=current_user.id,
            action=AuditActionEnum.UPDATE.value,
            entite=AuditEntiteEnum.CONTRAT.value,
            entite_id=contrat.id,
            description=f"Modification du contrat {contrat.reference}",
            anciennes_valeurs=anciennes,
            nouvelles_valeurs=nouvelles,
            request=request,
        )

    _rafraichir_alertes(db)

    return contrat


@router.post("/{contrat_id}/generer-word")
def generer_word_contrat(
    contrat_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("RH"))
):
    """Générer et télécharger le contrat au format Word (.docx)."""
    contrat = db.query(Contrat).options(
        joinedload(Contrat.employe),
        joinedload(Contrat.articles)
    ).filter(Contrat.id == contrat_id).first()

    if not contrat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat non trouvé")

    buffer = generer_contrat_word(contrat)
    filename = f"Contrat_{contrat.reference}.docx"

    log_action(
        db=db,
        utilisateur_id=current_user.id,
        action=AuditActionEnum.GENERATE.value,
        entite=AuditEntiteEnum.CONTRAT.value,
        entite_id=contrat.id,
        description=f"Génération du document Word pour le contrat {contrat.reference}",
        request=request,
    )

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/{contrat_id}/archive", response_model=ContratResponse)
def archiver_contrat(
    contrat_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("RH"))
):
    """
    Archiver logiquement un contrat (statut INACTIF).
    Ne supprime aucune donnee physique, conserve les articles et l'historique d'audit.
    Supprime les alertes associees au contrat pour ne plus generer d'emails ou notifications.
    """
    contrat = db.query(Contrat).options(
        joinedload(Contrat.employe),
        joinedload(Contrat.articles)
    ).filter(Contrat.id == contrat_id).first()

    if not contrat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat non trouvé")

    ancien_statut = contrat.statut

    # Deja archive
    if contrat.statut == StatutContratEnum.INACTIF.value:
        return contrat

    contrat.statut = StatutContratEnum.INACTIF.value
    db.commit()
    db.refresh(contrat)

    # Nettoyer les alertes existantes liees a ce contrat
    try:
        db.query(Notification).filter(
            Notification.entite == AuditEntiteEnum.CONTRAT.value,
            Notification.entite_id == contrat.id
        ).delete()
        db.commit()
    except Exception as e:
        print(f"[contrats] Echec du nettoyage des alertes pour le contrat {contrat.id} : {e}")

    # Enregistrer l'action ARCHIVE dans l'audit
    log_action(
        db=db,
        utilisateur_id=current_user.id,
        action=AuditActionEnum.ARCHIVE.value,
        entite=AuditEntiteEnum.CONTRAT.value,
        entite_id=contrat.id,
        description=f"Archivage du contrat {contrat.reference} (Statut précédent: {ancien_statut})",
        anciennes_valeurs={"statut": ancien_statut},
        nouvelles_valeurs={"statut": contrat.statut},
        request=request,
    )

    # Enregistrer egalement le STATUS_CHANGE pour l'historique des statuts
    log_action(
        db=db,
        utilisateur_id=current_user.id,
        action=AuditActionEnum.STATUS_CHANGE.value,
        entite=AuditEntiteEnum.CONTRAT.value,
        entite_id=contrat.id,
        description=f"Contrat {contrat.reference} : {ancien_statut} → {contrat.statut}",
        anciennes_valeurs={"statut": ancien_statut},
        nouvelles_valeurs={"statut": contrat.statut},
        request=request,
    )

    _rafraichir_alertes(db)
    return contrat


@router.post("/{contrat_id}/restaurer", response_model=ContratResponse)
def restaurer_contrat(
    contrat_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("RH"))
):
    """
    Restaurer un contrat archive (INACTIF) vers un statut coherent.
    Regle metier stricte :
    - Determine le statut precedant l'archivage via l'historique d'audit.
    - Si le contrat etait ACTIF mais que sa date de fin est depassee (CDD/Stage/etc.),
      il est restaure au statut FIN_CDD (ne pas restaurer automatiquement un contrat expire comme ACTIF).
    - Sinon, le contrat est restaure dans son statut anterieur (ex: BROUILLON, SIGNE, ACTIF, FIN_CDD, DEMISSION_CDI).
    """
    contrat = db.query(Contrat).options(
        joinedload(Contrat.employe),
        joinedload(Contrat.articles)
    ).filter(Contrat.id == contrat_id).first()

    if not contrat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat non trouvé")

    if contrat.statut != StatutContratEnum.INACTIF.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le contrat {contrat.reference} n'est pas archivé (statut actuel: {contrat.statut})."
        )

    # Rechercher le statut precedent dans l'audit
    last_archive_log = (
        db.query(AuditLog)
        .filter(
            AuditLog.entite == AuditEntiteEnum.CONTRAT.value,
            AuditLog.entite_id == contrat.id,
            AuditLog.action.in_([AuditActionEnum.ARCHIVE.value, AuditActionEnum.STATUS_CHANGE.value])
        )
        .order_by(AuditLog.date_action.desc())
        .first()
    )

    statut_cible = None
    if last_archive_log and last_archive_log.anciennes_valeurs and "statut" in last_archive_log.anciennes_valeurs:
        candidat = last_archive_log.anciennes_valeurs["statut"]
        if candidat and candidat != StatutContratEnum.INACTIF.value:
            statut_cible = normaliser_statut(candidat)

    if not statut_cible:
        # Si aucun historique trouve : si contrat avec date_fin echue -> FIN_CDD, sinon BROUILLON
        if contrat.type_contrat != TypeContratEnum.CDI.value and contrat.date_fin and contrat.date_fin < date.today():
            statut_cible = StatutContratEnum.FIN_CDD.value
        else:
            statut_cible = StatutContratEnum.BROUILLON.value

    # Regle metier : Ne pas restaurer un contrat expire en tant qu'ACTIF
    if statut_cible == StatutContratEnum.ACTIF.value:
        if contrat.type_contrat != TypeContratEnum.CDI.value and contrat.date_fin and contrat.date_fin < date.today():
            statut_cible = StatutContratEnum.FIN_CDD.value

    ancien_statut = contrat.statut
    contrat.statut = statut_cible
    db.commit()
    db.refresh(contrat)

    log_action(
        db=db,
        utilisateur_id=current_user.id,
        action=AuditActionEnum.RESTORE.value,
        entite=AuditEntiteEnum.CONTRAT.value,
        entite_id=contrat.id,
        description=f"Restauration du contrat {contrat.reference} vers le statut '{contrat.statut}'",
        anciennes_valeurs={"statut": ancien_statut},
        nouvelles_valeurs={"statut": contrat.statut},
        request=request,
    )

    log_action(
        db=db,
        utilisateur_id=current_user.id,
        action=AuditActionEnum.STATUS_CHANGE.value,
        entite=AuditEntiteEnum.CONTRAT.value,
        entite_id=contrat.id,
        description=f"Contrat {contrat.reference} : {ancien_statut} → {contrat.statut}",
        anciennes_valeurs={"statut": ancien_statut},
        nouvelles_valeurs={"statut": contrat.statut},
        request=request,
    )

    _rafraichir_alertes(db)
    return contrat


@router.delete("/{contrat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contrat(
    contrat_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("RH"))
):
    """
    Remplacement de la suppression definitive par un archivage logique.
    Ne supprime aucune ligne physique en base pour preserver les donnees et l'audit.
    """
    archiver_contrat(contrat_id=contrat_id, request=request, db=db, current_user=current_user)
    return None
