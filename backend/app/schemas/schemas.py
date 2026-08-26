from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import date, datetime

from app.models.models import TypeContratEnum


# ===== SCHÉMAS AUTHENTIFICATION =====

class LoginRequest(BaseModel):
    email: str
    mot_de_passe: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UtilisateurResponse"


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    nouveau_mot_de_passe: str = Field(..., min_length=4)


# ===== SCHÉMAS UTILISATEUR / EMPLOYÉ =====

class UtilisateurCreate(BaseModel):
    nom: str = Field(..., min_length=2, max_length=100)
    prenom: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5)
    mot_de_passe: str = Field(..., min_length=4)
    matricule: Optional[str] = None
    date_embauche: Optional[date] = None
    date_naissance: Optional[date] = None
    telephone: Optional[str] = None
    departement: Optional[str] = None
    poste: Optional[str] = None
    role: Optional[str] = "EMPLOYE"


class UtilisateurUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[str] = None
    date_embauche: Optional[date] = None
    date_naissance: Optional[date] = None
    telephone: Optional[str] = None
    departement: Optional[str] = None
    poste: Optional[str] = None
    role: Optional[str] = None


class UtilisateurResponse(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str
    matricule: str
    date_embauche: Optional[date] = None
    date_naissance: Optional[date] = None
    telephone: Optional[str] = None
    departement: Optional[str] = None
    poste: Optional[str] = None
    role: str

    class Config:
        from_attributes = True


# ===== SCHÉMAS ARTICLE =====

class ArticleCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=20)
    titre: str = Field(..., min_length=2, max_length=200)
    contenu_par_defaut: Optional[str] = None

class ArticleUpdate(BaseModel):
    code: Optional[str] = None
    titre: Optional[str] = None
    contenu_par_defaut: Optional[str] = None
    est_actif: Optional[bool] = None

class ArticleResponse(BaseModel):
    id: int
    code: str
    titre: str
    contenu_par_defaut: Optional[str] = None
    est_actif: bool
    modifie_le: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== SCHÉMAS CONTRAT =====

class ContratCreate(BaseModel):
    type_contrat: TypeContratEnum
    date_debut: date
    date_fin: Optional[date] = None
    salaire_mensuel: int
    employe_id: int
    article_ids: Optional[List[int]] = []

    @model_validator(mode="after")
    def _valider_date_fin(self):
        """
        Regle metier :
        - CDI : la date de fin doit toujours etre NULL (forcee ici, meme si envoyee).
        - CDD / STAGE / ALTERNANCE : la date de fin est obligatoire et doit etre
          strictement posterieure a la date de debut.
        """
        if self.type_contrat == TypeContratEnum.CDI:
            self.date_fin = None
        else:
            if not self.date_fin:
                raise ValueError(
                    "La date de fin est obligatoire pour un contrat de type CDD, STAGE ou ALTERNANCE."
                )
            if self.date_fin <= self.date_debut:
                raise ValueError("La date de fin doit etre posterieure a la date de debut.")
        return self


class ContratUpdate(BaseModel):
    type_contrat: Optional[TypeContratEnum] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    salaire_mensuel: Optional[int] = None
    statut: Optional[str] = None
    article_ids: Optional[List[int]] = None


class EmployeMinimal(BaseModel):
    id: int
    nom: str
    prenom: str
    matricule: str
    departement: Optional[str] = None
    poste: Optional[str] = None

    class Config:
        from_attributes = True


class ContratResponse(BaseModel):
    id: int
    reference: str
    type_contrat: str
    date_creation: date
    date_debut: date
    date_fin: Optional[date] = None
    salaire_mensuel: int
    statut: str
    document_path: Optional[str] = None
    employe_id: int
    employe: Optional[EmployeMinimal] = None
    articles: Optional[List[ArticleResponse]] = []

    class Config:
        from_attributes = True


# ===== SCHÉMAS AUDIT / HISTORIQUE =====

class AuditLogResponse(BaseModel):
    id: int
    utilisateur_id: Optional[int] = None
    utilisateur_nom: Optional[str] = None
    action: str
    entite: str
    entite_id: Optional[int] = None
    description: str
    anciennes_valeurs: Optional[dict] = None
    nouvelles_valeurs: Optional[dict] = None
    date_action: datetime
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True


class AuditLogPaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[AuditLogResponse]


# ===== SCHÉMAS NOTIFICATIONS / ALERTES =====

class NotificationResponse(BaseModel):
    id: int
    type: str
    titre: str
    message: str
    priorite: str
    entite: Optional[str] = None
    entite_id: Optional[int] = None
    est_lue: bool
    date_creation: datetime
    date_lecture: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationPaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    unread_count: int
    items: List[NotificationResponse]


class UnreadCountResponse(BaseModel):
    unread_count: int


TokenResponse.model_rebuild()

