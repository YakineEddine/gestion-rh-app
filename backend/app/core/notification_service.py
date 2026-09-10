"""
Service centralise de gestion des alertes / notifications RH.

Point d'entree unique pour :
  - generer automatiquement les alertes liees aux contrats
  - creer une notification en evitant les doublons (dedup_key)
  - lister / compter / marquer comme lue(s)

Preparation pour une future integration email (non implementee ici) :

    verifier_alertes_contrats()  ->  Notification creee en base
                                       -> (etape future) EmailService.envoyer(notification)

Aucun appel a un fournisseur externe n'est effectue a ce stade.
"""
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.models import (
    AuditActionEnum,
    AuditEntiteEnum,
    Contrat,
    Notification,
    NotificationPrioriteEnum,
    NotificationTypeEnum,
    RoleEnum,
    StatutContratEnum,
    TypeContratEnum,
    Utilisateur,
)
from app.core.audit_service import log_action
from app.core.security import create_direct_access_token
from app.core.email_service import (
    send_email,
    template_contract_expiring,
    template_contract_expired,
    template_contract_expiring_employe,
    template_contract_expired_employe,
)

# Seuils d'alerte pour l'expiration d'un contrat (en jours restants avant date_fin)
SEUILS_EXPIRATION_JOURS = [30, 15, 7]

# Nombre de jours au-dela desquels un contrat encore en "Brouillon" declenche une alerte
SEUIL_BROUILLON_JOURS = 7

# ─────────────────────────────────────────────────────────────────────────
# NOTE IMPORTANTE - Periode d'essai (NotificationTypeEnum.PROBATION_ENDING) :
#
# Ni le modele Contrat ni le modele Utilisateur ne stockent de duree ou de
# date de fin de periode d'essai reelle. Generer une alerte PROBATION_ENDING
# necessiterait donc d'inventer cette donnee (duree fictive), ce qui est
# explicitement interdit par les exigences du projet.
#
# Le type NotificationTypeEnum.PROBATION_ENDING est neanmoins defini pour
# que l'architecture (API, frontend, filtres) soit prete a l'accueillir dès
# qu'un champ reel (ex: duree_periode_essai sur Contrat) sera ajoute au
# modele de donnees. Aucune detection automatique n'est implementee ici.
# ─────────────────────────────────────────────────────────────────────────


def _destinataires_rh(db: Session) -> List[Utilisateur]:
    """Les alertes RH sont envoyees a tous les comptes RH et ADMIN existants."""
    return db.query(Utilisateur).filter(
        Utilisateur.role.in_([RoleEnum.RH, RoleEnum.ADMIN])
    ).all()


def _creer_si_absente(
    db: Session,
    utilisateur_id: int,
    type_notif: str,
    titre: str,
    message: str,
    priorite: str,
    entite: Optional[str],
    entite_id: Optional[int],
    dedup_key: str,
    date_expiration: Optional[datetime] = None,
) -> Optional[Notification]:
    """
    Cree une notification uniquement si aucune n'existe deja avec la meme
    dedup_key. Retourne la notification creee, ou None si elle existait deja
    (strategie anti-doublon principale, en plus de la contrainte UNIQUE en base).
    """
    existante = db.query(Notification).filter(Notification.dedup_key == dedup_key).first()
    if existante:
        return None

    notif = Notification(
        utilisateur_id=utilisateur_id,
        type=type_notif,
        titre=titre,
        message=message,
        priorite=priorite,
        entite=entite,
        entite_id=entite_id,
        est_lue=False,
        dedup_key=dedup_key,
        date_expiration=date_expiration,
    )
    db.add(notif)
    try:
        db.commit()
        db.refresh(notif)
        return notif
    except IntegrityError:
        # Filet de securite : une autre execution concurrente a cree la
        # meme alerte entre la verification et l'insertion.
        db.rollback()
        return None


def verifier_alertes_contrats(db: Session) -> int:
    """
    Analyse tous les contrats et genere les alertes manquantes concernant :
      - l'expiration prochaine (30 / 15 / 7 jours restants)
      - l'expiration deja survenue
      - les contrats restes en "Brouillon" trop longtemps

    Ne genere jamais de doublon : chaque combinaison (type, contrat, seuil,
    destinataire) n'est creee qu'une seule fois, quel que soit le nombre
    d'executions (redemarrage du serveur, tache planifiee, appel manuel).

    Retourne le nombre total de nouvelles notifications creees.
    """
    aujourdhui = date.today()
    destinataires = _destinataires_rh(db)
    if not destinataires:
        return 0

    total_creees = 0

    # ─── Contrats avec date de fin (CDD / STAGE / ALTERNANCE uniquement :
    #     un CDI n'a jamais de date_fin, il est donc naturellement exclu).
    #     Exclut également les contrats INACTIFS, FIN_CDD, DEMISSION_CDI. ───
    statuts_exclus = [
        "INACTIF", "FIN_CDD", "DEMISSION_CDI",
        "Terminé", "Termine", "Expiré", "Expire", "Inactif"
    ]
    contrats_a_echeance = db.query(Contrat).filter(
        Contrat.date_fin.isnot(None),
        Contrat.type_contrat != TypeContratEnum.CDI.value,
        Contrat.statut.notin_(statuts_exclus),
    ).all()

    for contrat in contrats_a_echeance:
        jours_restants = (contrat.date_fin - aujourdhui).days

        # Employé lié au contrat (pour alertes personnelles employé)
        employe_user = None
        if contrat.employe_id and contrat.statut not in ["BROUILLON", "Brouillon"]:
            employe_user = db.query(Utilisateur).filter(Utilisateur.id == contrat.employe_id).first()

        if jours_restants < 0:
            titre_rh = f"Contrat {contrat.reference} expiré"
            message_rh = (
                f"Le contrat {contrat.reference} est arrivé à expiration "
                f"le {contrat.date_fin.strftime('%d/%m/%Y')}."
            )
            cree_pour_qqun = False

            # 1. Alerte RH
            for dest in destinataires:
                notif = _creer_si_absente(
                    db, dest.id,
                    NotificationTypeEnum.CONTRACT_EXPIRED.value,
                    titre_rh, message_rh, NotificationPrioriteEnum.CRITICAL.value,
                    AuditEntiteEnum.CONTRAT.value, contrat.id,
                    dedup_key=f"CONTRACT_EXPIRED:CONTRAT:{contrat.id}:{dest.id}",
                )
                if notif:
                    total_creees += 1
                    cree_pour_qqun = True
                    # Envoi de l'email d'alerte au RH
                    if dest.email:
                        html = template_contract_expired(
                            prenom=dest.prenom,
                            reference=contrat.reference,
                            date_fin=contrat.date_fin.strftime('%d/%m/%Y'),
                        )
                        email_ok = send_email(
                            to=dest.email,
                            subject=f"[Alerte RH] {titre_rh}",
                            html_content=html,
                        )
                        if email_ok:
                            log_action(
                                db=db, utilisateur_id=dest.id,
                                action=AuditActionEnum.EMAIL_SENT.value,
                                entite=AuditEntiteEnum.CONTRAT.value, entite_id=contrat.id,
                                description=f"Email d'expiration envoyé à {dest.email} pour le contrat {contrat.reference}",
                            )

            # 2. Alerte Employé personnel (si non-brouillon)
            if employe_user:
                titre_emp = f"Contrat {contrat.reference} expiré"
                message_emp = (
                    f"Votre contrat {contrat.reference} est arrivé à expiration "
                    f"le {contrat.date_fin.strftime('%d/%m/%Y')}."
                )
                notif_emp = _creer_si_absente(
                    db, employe_user.id,
                    NotificationTypeEnum.CONTRACT_EXPIRED.value,
                    titre_emp, message_emp, NotificationPrioriteEnum.CRITICAL.value,
                    AuditEntiteEnum.CONTRAT.value, contrat.id,
                    dedup_key=f"CONTRACT_EXPIRED:CONTRAT:{contrat.id}:{employe_user.id}",
                )
                if notif_emp:
                    total_creees += 1
                    cree_pour_qqun = True
                    # Envoi email employé
                    if employe_user.email:
                        direct_tok = create_direct_access_token(employe_user.id, employe_user.email)
                        html_emp = template_contract_expired_employe(
                            prenom=employe_user.prenom,
                            nom=employe_user.nom,
                            reference=contrat.reference,
                            date_fin=contrat.date_fin.strftime('%d/%m/%Y'),
                            direct_token=direct_tok,
                        )
                        email_ok = send_email(
                            to=employe_user.email,
                            subject="Votre contrat est arrivé à expiration",
                            html_content=html_emp,
                        )
                        if email_ok:
                            log_action(
                                db=db, utilisateur_id=employe_user.id,
                                action=AuditActionEnum.EMAIL_SENT.value,
                                entite=AuditEntiteEnum.CONTRAT.value, entite_id=contrat.id,
                                description=f"Email d'expiration envoyé à l'employé {employe_user.email} pour le contrat {contrat.reference}",
                            )

            if cree_pour_qqun:
                log_action(
                    db=db, utilisateur_id=None,
                    action=AuditActionEnum.ALERT_GENERATED.value,
                    entite=AuditEntiteEnum.CONTRAT.value, entite_id=contrat.id,
                    description=titre_rh,
                )
        else:
            # Trouver le seuil le plus serré qui s'applique.
            # Ex: si jours_restants = 5, on matche 30, 15 et 7 → on ne garde que 7.
            seuil_applicable = None
            for seuil in sorted(SEUILS_EXPIRATION_JOURS):  # [7, 15, 30]
                if jours_restants <= seuil:
                    seuil_applicable = seuil
                    break  # le plus petit seuil qui matche = le plus pertinent

            if seuil_applicable is not None:
                priorite = (
                    NotificationPrioriteEnum.CRITICAL.value
                    if seuil_applicable <= 7 else NotificationPrioriteEnum.WARNING.value
                )
                titre_rh = f"Contrat {contrat.reference} bientôt expiré"
                message_rh = (
                    f"Ce contrat expire dans {jours_restants} jour(s) "
                    f"(le {contrat.date_fin.strftime('%d/%m/%Y')})."
                )
                cree_pour_qqun = False

                # 1. Alerte RH
                for dest in destinataires:
                    dedup_base = f"CONTRACT_EXPIRING:CONTRAT:{contrat.id}:{dest.id}"

                    anciennes = db.query(Notification).filter(
                        Notification.dedup_key.like(f"CONTRACT_EXPIRING:CONTRAT:{contrat.id}:J%:{dest.id}")
                    ).all()
                    for anc in anciennes:
                        db.delete(anc)
                    if anciennes:
                        db.commit()

                    existante = db.query(Notification).filter(
                        Notification.dedup_key == dedup_base
                    ).first()

                    should_send_email = False
                    if existante:
                        if existante.priorite != priorite or existante.message != message_rh:
                            if existante.priorite != priorite:
                                should_send_email = True
                            existante.priorite = priorite
                            existante.titre = titre_rh
                            existante.message = message_rh
                            existante.est_lue = False
                            existante.date_creation = datetime.utcnow()
                            existante.date_lecture = None
                            db.commit()
                            cree_pour_qqun = True
                    else:
                        notif = _creer_si_absente(
                            db, dest.id,
                            NotificationTypeEnum.CONTRACT_EXPIRING.value,
                            titre_rh, message_rh, priorite,
                            AuditEntiteEnum.CONTRAT.value, contrat.id,
                            dedup_key=dedup_base,
                            date_expiration=datetime.combine(contrat.date_fin, datetime.min.time()),
                        )
                        if notif:
                            total_creees += 1
                            cree_pour_qqun = True
                            should_send_email = True

                    if should_send_email and dest.email:
                        html = template_contract_expiring(
                            prenom=dest.prenom,
                            reference=contrat.reference,
                            date_fin=contrat.date_fin.strftime('%d/%m/%Y'),
                            jours_restants=jours_restants,
                            priorite=priorite,
                        )
                        email_ok = send_email(
                            to=dest.email,
                            subject=f"[Alerte RH - {priorite}] {titre_rh}",
                            html_content=html,
                        )
                        if email_ok:
                            log_action(
                                db=db, utilisateur_id=dest.id,
                                action=AuditActionEnum.EMAIL_SENT.value,
                                entite=AuditEntiteEnum.CONTRAT.value, entite_id=contrat.id,
                                description=f"Email d'alerte ({priorite}) envoyé à {dest.email} pour le contrat {contrat.reference}",
                            )

                # 2. Alerte Employé personnel (si non-brouillon)
                if employe_user:
                    dedup_base_emp = f"CONTRACT_EXPIRING:CONTRAT:{contrat.id}:{employe_user.id}"
                    titre_emp = f"Contrat {contrat.reference} bientôt expiré"
                    message_emp = (
                        f"Votre contrat {contrat.reference} arrive à expiration dans {jours_restants} jour(s) "
                        f"(le {contrat.date_fin.strftime('%d/%m/%Y')})."
                    )

                    anciennes_emp = db.query(Notification).filter(
                        Notification.dedup_key.like(f"CONTRACT_EXPIRING:CONTRAT:{contrat.id}:J%:{employe_user.id}")
                    ).all()
                    for anc in anciennes_emp:
                        db.delete(anc)
                    if anciennes_emp:
                        db.commit()

                    existante_emp = db.query(Notification).filter(
                        Notification.dedup_key == dedup_base_emp
                    ).first()

                    should_send_email_emp = False
                    if existante_emp:
                        if existante_emp.priorite != priorite or existante_emp.message != message_emp:
                            if existante_emp.priorite != priorite:
                                should_send_email_emp = True
                            existante_emp.priorite = priorite
                            existante_emp.titre = titre_emp
                            existante_emp.message = message_emp
                            existante_emp.est_lue = False
                            existante_emp.date_creation = datetime.utcnow()
                            existante_emp.date_lecture = None
                            db.commit()
                            cree_pour_qqun = True
                    else:
                        notif_emp = _creer_si_absente(
                            db, employe_user.id,
                            NotificationTypeEnum.CONTRACT_EXPIRING.value,
                            titre_emp, message_emp, priorite,
                            AuditEntiteEnum.CONTRAT.value, contrat.id,
                            dedup_key=dedup_base_emp,
                            date_expiration=datetime.combine(contrat.date_fin, datetime.min.time()),
                        )
                        if notif_emp:
                            total_creees += 1
                            cree_pour_qqun = True
                            should_send_email_emp = True

                    if should_send_email_emp and employe_user.email:
                        direct_tok = create_direct_access_token(employe_user.id, employe_user.email)
                        html_emp = template_contract_expiring_employe(
                            prenom=employe_user.prenom,
                            nom=employe_user.nom,
                            reference=contrat.reference,
                            date_fin=contrat.date_fin.strftime('%d/%m/%Y'),
                            jours_restants=jours_restants,
                            priorite=priorite,
                            direct_token=direct_tok,
                        )
                        email_ok = send_email(
                            to=employe_user.email,
                            subject="Votre contrat arrive bientôt à expiration",
                            html_content=html_emp,
                        )
                        if email_ok:
                            log_action(
                                db=db, utilisateur_id=employe_user.id,
                                action=AuditActionEnum.EMAIL_SENT.value,
                                entite=AuditEntiteEnum.CONTRAT.value, entite_id=contrat.id,
                                description=f"Email d'alerte expiration ({priorite}) envoyé à l'employé {employe_user.email} pour le contrat {contrat.reference}",
                            )

                if cree_pour_qqun:
                    log_action(
                        db=db, utilisateur_id=None,
                        action=AuditActionEnum.ALERT_GENERATED.value,
                        entite=AuditEntiteEnum.CONTRAT.value, entite_id=contrat.id,
                        description=titre_rh,
                    )

    # ─── Contrats restes en "Brouillon" depuis trop longtemps ───
    contrats_brouillon = db.query(Contrat).filter(Contrat.statut.in_(["BROUILLON", "Brouillon"])).all()
    for contrat in contrats_brouillon:
        age_jours = (aujourdhui - contrat.date_creation).days
        if age_jours >= SEUIL_BROUILLON_JOURS:
            titre = f"Contrat {contrat.reference} toujours en brouillon"
            message = f"Le contrat {contrat.reference} est en statut Brouillon depuis {age_jours} jour(s)."
            cree_pour_qqun = False
            for dest in destinataires:
                notif = _creer_si_absente(
                    db, dest.id,
                    NotificationTypeEnum.DRAFT_CONTRACT.value,
                    titre, message, NotificationPrioriteEnum.WARNING.value,
                    AuditEntiteEnum.CONTRAT.value, contrat.id,
                    dedup_key=f"DRAFT_CONTRACT:CONTRAT:{contrat.id}:{dest.id}",
                )
                if notif:
                    total_creees += 1
                    cree_pour_qqun = True
            if cree_pour_qqun:
                log_action(
                    db=db, utilisateur_id=None,
                    action=AuditActionEnum.ALERT_GENERATED.value,
                    entite=AuditEntiteEnum.CONTRAT.value, entite_id=contrat.id,
                    description=titre,
                )

    return total_creees


def marquer_comme_lue(db: Session, notification_id: int, utilisateur_id: int) -> Optional[Notification]:
    """
    Marque une notification comme lue. Un utilisateur ne peut marquer que
    SES PROPRES notifications (filtre par utilisateur_id) : retourne None
    si la notification n'existe pas ou n'appartient pas a l'utilisateur.
    """
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.utilisateur_id == utilisateur_id,
    ).first()
    if not notif:
        return None
    if not notif.est_lue:
        notif.est_lue = True
        notif.date_lecture = datetime.utcnow()
        db.commit()
        db.refresh(notif)
    return notif


def marquer_toutes_comme_lues(db: Session, utilisateur_id: int) -> int:
    """Marque toutes les notifications non lues de l'utilisateur comme lues."""
    notifs = db.query(Notification).filter(
        Notification.utilisateur_id == utilisateur_id,
        Notification.est_lue.is_(False),
    ).all()
    maintenant = datetime.utcnow()
    for n in notifs:
        n.est_lue = True
        n.date_lecture = maintenant
    db.commit()
    return len(notifs)


def compter_non_lues(db: Session, utilisateur_id: int) -> int:
    return db.query(Notification).filter(
        Notification.utilisateur_id == utilisateur_id,
        Notification.est_lue.is_(False),
    ).count()
