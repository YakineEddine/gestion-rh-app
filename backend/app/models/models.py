from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, ForeignKey, Text, Boolean, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class RoleEnum(str, enum.Enum):
    RH = "RH"
    EMPLOYE = "EMPLOYE"
    ADMIN = "ADMIN"


class TypeContratEnum(str, enum.Enum):
    CDI = "CDI"
    CDD = "CDD"
    STAGE = "STAGE"
    ALTERNANCE = "ALTERNANCE"
    CIVP = "CIVP"


class StatutContratEnum(str, enum.Enum):
    BROUILLON = "BROUILLON"
    COMMUNIQUE_EN_COURS = "COMMUNIQUE_EN_COURS"
    SIGNE = "SIGNE"
    ACTIF = "ACTIF"
    FIN_CDD = "FIN_CDD"
    DEMISSION_CDI = "DEMISSION_CDI"
    PAS_DISCUTE = "PAS_DISCUTE"
    INACTIF = "INACTIF"



class AuditActionEnum(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    PASSWORD_RESET = "PASSWORD_RESET"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_UNLOCKED = "ACCOUNT_UNLOCKED"
    ACTIVATE = "ACTIVATE"
    DEACTIVATE = "DEACTIVATE"
    DOWNLOAD = "DOWNLOAD"
    GENERATE = "GENERATE"
    STATUS_CHANGE = "STATUS_CHANGE"
    ALERT_GENERATED = "ALERT_GENERATED"
    EMAIL_SENT = "EMAIL_SENT"
    AI_GENERATE = "AI_GENERATE"


class AuditEntiteEnum(str, enum.Enum):
    EMPLOYE = "EMPLOYE"
    ARTICLE = "ARTICLE"
    CONTRAT = "CONTRAT"
    AUTH = "AUTH"


class NotificationTypeEnum(str, enum.Enum):
    CONTRACT_EXPIRING = "CONTRACT_EXPIRING"
    CONTRACT_EXPIRED = "CONTRACT_EXPIRED"
    PROBATION_ENDING = "PROBATION_ENDING"
    DRAFT_CONTRACT = "DRAFT_CONTRACT"


class NotificationPrioriteEnum(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


# Table d'association Many-to-Many entre Contrat et Article
contrat_articles = Table(
    "contrat_articles",
    Base.metadata,
    Column("contrat_id", Integer, ForeignKey("contrats.id", ondelete="CASCADE"), primary_key=True),
    Column("article_id", Integer, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    Column("ordre", Integer, default=0),
)


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, index=True, nullable=False)
    prenom = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    mot_de_passe_hash = Column(String, nullable=False)
    matricule = Column(String, unique=True, index=True, nullable=False)
    date_embauche = Column(Date, nullable=True)
    date_naissance = Column(Date, nullable=True)
    telephone = Column(String, nullable=True)
    departement = Column(String, nullable=True)
    poste = Column(String, nullable=True)
    role = Column(Enum(RoleEnum), default=RoleEnum.EMPLOYE)
    est_actif = Column(Boolean, default=True, nullable=False)
    login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    last_failed_login = Column(DateTime, nullable=True)

    contrats = relationship("Contrat", back_populates="employe")
    refresh_tokens = relationship("RefreshToken", back_populates="utilisateur", cascade="all, delete-orphan")
    reset_tokens = relationship("ResetToken", back_populates="utilisateur", cascade="all, delete-orphan")


class Contrat(Base):
    __tablename__ = "contrats"

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True, nullable=False)
    type_contrat = Column(String, nullable=False, default=TypeContratEnum.CDI.value)
    date_creation = Column(Date, nullable=False)
    date_debut = Column(Date, nullable=False)
    date_fin = Column(Date, nullable=True)
    salaire_mensuel = Column(Integer, nullable=False)
    statut = Column(String, default=StatutContratEnum.BROUILLON.value)
    document_path = Column(String, nullable=True)

    employe_id = Column(Integer, ForeignKey("utilisateurs.id"))
    employe = relationship("Utilisateur", back_populates="contrats")
    articles = relationship("Article", secondary=contrat_articles, backref="contrats", order_by=contrat_articles.c.ordre)


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    titre = Column(String, nullable=False)
    contenu_par_defaut = Column(Text, nullable=True)
    est_actif = Column(Boolean, default=True)
    types_contrat = Column(JSONB, nullable=True, default=None)
    modifie_le = Column(DateTime, nullable=True, default=datetime.utcnow)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked = Column(Boolean, default=False, nullable=False)

    utilisateur = relationship("Utilisateur", back_populates="refresh_tokens")


class ResetToken(Base):
    __tablename__ = "reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    utilisateur = relationship("Utilisateur", back_populates="reset_tokens")


class AuditLog(Base):
    """
    Journal d'audit centralise : trace les actions importantes effectuees
    dans l'application (creation, modification, suppression, connexion, ...).
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String, nullable=False, index=True)
    entite = Column(String, nullable=False, index=True)
    entite_id = Column(Integer, nullable=True, index=True)
    description = Column(String, nullable=False)
    anciennes_valeurs = Column(JSONB, nullable=True)
    nouvelles_valeurs = Column(JSONB, nullable=True)
    date_action = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    ip_address = Column(String, nullable=True)

    utilisateur = relationship("Utilisateur")


class Notification(Base):
    """
    Notification / alerte RH generee automatiquement par le systeme.
    La colonne dedup_key (UNIQUE) empeche les doublons meme en cas
    d'executions concurrentes du moteur d'alertes.
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String, nullable=False, index=True)
    titre = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    priorite = Column(String, nullable=False, default=NotificationPrioriteEnum.INFO.value)
    entite = Column(String, nullable=True)
    entite_id = Column(Integer, nullable=True)
    est_lue = Column(Boolean, default=False, index=True)
    date_creation = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    date_lecture = Column(DateTime, nullable=True)
    date_expiration = Column(DateTime, nullable=True)
    dedup_key = Column(String, unique=True, nullable=True, index=True)

    utilisateur = relationship("Utilisateur")
