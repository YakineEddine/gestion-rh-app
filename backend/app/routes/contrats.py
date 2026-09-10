from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional, List
from datetime import date

from app.database import get_db
from app.models.models import Contrat, Article, Utilisateur, TypeContratEnum, StatutContratEnum, AuditActionEnum, AuditEntiteEnum
from app.schemas.schemas import ContratCreate, ContratUpdate, ContratResponse
from app.core.security import require_role, create_direct_access_token
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
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("RH"))
):
    """Lister tous les contrats avec filtres optionnels."""
    query = db.query(Contrat).options(
        joinedload(Contrat.employe),
        joinedload(Contrat.articles)
    )

    if statut:
        norm_statut = normaliser_statut(statut)
        query = query.filter((Contrat.statut == statut) | (Contrat.statut == norm_statut))

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
                detail="Le statut 'Démission (CDI)' ne s'applique pas à un contrat CDD, STAGE ou ALTERNANCE."
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

    # Regle metier : coherence type_contrat / date_fin, verifiee sur l'etat final
    # du contrat (que les champs impactes aient ete envoyes ou non dans cette requete).
    if contrat.type_contrat == TypeContratEnum.CDI.value:
        contrat.date_fin = None
    else:
        if not contrat.date_fin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La date de fin est obligatoire pour un contrat CDD, STAGE ou ALTERNANCE."
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


@router.delete("/{contrat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contrat(
    contrat_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("RH"))
):
    """Supprimer un contrat."""
    contrat = db.query(Contrat).filter(Contrat.id == contrat_id).first()
    if not contrat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat non trouvé")

    reference, contrat_id_captured = contrat.reference, contrat.id

    db.delete(contrat)
    db.commit()

    log_action(
        db=db,
        utilisateur_id=current_user.id,
        action=AuditActionEnum.DELETE.value,
        entite=AuditEntiteEnum.CONTRAT.value,
        entite_id=contrat_id_captured,
        description=f"Suppression du contrat {reference}",
        request=request,
    )
    return None
