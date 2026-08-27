from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.models.models import *
from app.routes.auth import router as auth_router
from app.routes.employes import router as employes_router
from app.routes.espace_employe import router as espace_employe_router
from app.routes.articles import router as articles_router
from app.routes.contrats import router as contrats_router
from app.routes.audit import router as audit_router
from app.routes.ai import router as ai_router
from app.routes.notifications import router as notifications_router

# Créer les tables de la base de données
Base.metadata.create_all(bind=engine)

# Initialiser l'application FastAPI
app = FastAPI(
    title="Gestion RH API",
    description="API pour la gestion des ressources humaines",
    version="1.0.0"
)

# Configurer CORS pour le frontend
origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrer les routes
app.include_router(auth_router)
app.include_router(employes_router)
app.include_router(espace_employe_router)
app.include_router(articles_router)
app.include_router(contrats_router)
app.include_router(audit_router)
app.include_router(ai_router)
app.include_router(notifications_router)

# Route de test
@app.get("/")
async def root():
    return {"message": "Bienvenue dans l'API Gestion RH"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
