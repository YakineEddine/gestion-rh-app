# 🏢 Gestion RH App

Application moderne et complète de gestion des Ressources Humaines (RH) intégrant la gestion des employés, contrats, bibliothèque d'articles/clauses avec **Assistant IA** (Google Gemini, xAI Grok, OpenAI), système d'alertes automatiques et service d'emails (SMTP / Brevo).

---

## ✨ Fonctionnalités Principales

- 👥 **Gestion des Employés** : CRUD complet, recherche, filtres par statut et département, pagination.
- 📄 **Gestion des Contrats** : Création de contrats (CDI, CDD, Stage, Freelance), association dynamique de clauses, génération de PDF avec mise en page professionnelle.
- 📚 **Bibliothèque d'Articles & Clauses** : Gestion des clauses contractuelles réutilisables.
- 🤖 **Assistant IA Intégré (Prompt-to-Clause)** :
  - Génération de clauses contractuelles juridiques en langage naturel.
  - Multi-providers supportés : **Google Gemini**, **xAI Grok**, **OpenAI**.
  - Intégration directe dans le formulaire de création avec prévisualisation et édition manuelle avant enregistrement.
- 🔔 **Système d'Alertes RH Automatiques** : Détection des fins de contrat (30j, 15j, 7j, expiré), alertes d'anniversaire d'ancienneté, notifications interactives avec marquage lu/non-lu.
- 📧 **Service d'Emails Centralisé** : Envoi d'e-mails professionnels (SMTP Gmail, Brevo API) avec templates HTML réutilisables.
- 🛡️ **Audit & Historique** : Journalisation détaillée de toutes les actions critiques (création, modification, suppression, génération IA, alertes, emails).
- 🔐 **Sécurité & Rôles** : Authentification JWT, contrôle d'accès basé sur les rôles (ADMIN, RH, EMPLOYE).

---

## 🛠️ Stack Technique

- **Backend** : FastAPI (Python 3.10+), SQLAlchemy, PostgreSQL, Pydantic, Uvicorn, HTTPX, ReportLab.
- **Frontend** : React 18, Vite, React Router, Lucide Icons, Axios, Vanilla CSS moderne & responsive.
- **IA & Intégrations** : Google Generative AI / Gemini REST API, xAI REST API, Brevo API / SMTP.

---

## 🚀 Installation & Démarrage

### 1. Prérequis
- Python 3.10+
- Node.js 18+
- PostgreSQL

### 2. Configuration du Backend

```bash
cd backend
# Créer et activer l'environnement virtuel
python -m venv venv
# Windows :
.\venv\Scripts\activate
# Linux/macOS :
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditez ensuite le fichier .env avec vos identifiants locaux

# Lancer le serveur backend
python -m uvicorn app.main:app --reload --port 8001
```

### 3. Configuration du Frontend

```bash
cd frontend
# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
```

L'application sera accessible sur `http://localhost:5174` (ou `http://localhost:5173`).

---

## 🔒 Sécurité des Données
Le fichier `.env` contenant les clés API, identifiants de base de données et secrets JWT ne doit **jamais** être versionné sur Git. Utilisez le modèle `.env.example`.
