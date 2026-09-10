# -*- coding: utf-8 -*-
"""
Chapitre 3 : Conception et Architecture Technique
Chapitre 4 : Réalisation et Mise en Œuvre de l'Application
"""

from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from build_report_full import (
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TEXT, COLOR_MUTED, COLOR_ACCENT,
    add_heading_1, add_heading_2, add_heading_3, add_paragraph, add_bullet,
    add_callout, add_styled_table, add_figure
)

def build_chapter_3(doc):
    # =========================================================================
    # CHAPITRE 3 : CONCEPTION ET ARCHITECTURE TECHNIQUE
    # =========================================================================
    add_heading_1(doc, "CHAPITRE 3 : CONCEPTION ET ARCHITECTURE TECHNIQUE")

    add_heading_2(doc, "3.1 Introduction")
    add_paragraph(doc,
        "La phase de conception constitue la clé de voûte de tout projet d'ingénierie logicielle. Elle traduit les exigences fonctionnelles et non fonctionnelles en une architecture robuste, modulaire et extensible. Ce chapitre détaille l'architecture globale trois-tiers du système, analyse les choix structurels du backend FastAPI et du frontend React 18, expose la modélisation statique au travers du diagramme de classes UML complet, illustre les dynamiques comportementales par des diagrammes de séquence et modélise la machine à états finis des contrats de travail.",
        space_after=8)

    add_heading_2(doc, "3.2 Architecture Globale 3-Tiers du Système")
    add_paragraph(doc,
        "L'application repose sur un modèle d'architecture découplée en trois tiers (Figure 2), garantissant une séparation nette des responsabilités, une grande flexibilité de maintenance et une évolutivité aisée :",
        space_after=4)

    add_bullet(doc, "Implémenté sous la forme d'une Single Page Application (SPA) réactive avec React 18 et packagée par Vite. Ce tiers s'exécute dans le navigateur de l'utilisateur, gère les interactions ergonomiques, l'état applicatif local (AuthContext) et communique avec le serveur via des requêtes HTTP asynchrones au format JSON.", "1. Le Tiers Présentation (Frontend)")
    add_bullet(doc, "Conçu avec le framework Python FastAPI. Ce tiers expose une API RESTful haute performance, implémente l'ensemble des règles métier, assure le contrôle d'accès sécurisé (RBAC, JWT, Bcrypt), orchestre les services externes (Google Gemini pour l'IA, Brevo pour les emails) et gère le moteur d'alertes et de génération de documents.", "2. Le Tiers Application (Backend REST API)")
    add_bullet(doc, "Repose sur le système de gestion de bases de données relationnelles PostgreSQL. Ce tiers assure la persistance fiable, l'intégrité référentielle et la conformité ACID des données (utilisateurs, contrats, clauses, notifications et journaux d'audit).", "3. Le Tiers Persistance (Base de Données)")

    add_figure(doc, "fig_architecture_3tiers.png", "Figure 2 — Architecture Globale 3-Tiers de l'Application RH", width=5.6)

    add_heading_2(doc, "3.3 Architecture Détaillée du Backend FastAPI")
    add_paragraph(doc,
        "Le backend a été conçu selon les meilleures pratiques de développement modulaire en Python. Il est articulé autour des couches logicielles suivantes :",
        space_after=4)
    add_bullet(doc, "Endpoints REST organisés par domaine métier (auth.py, employes.py, contrats.py, articles.py, ai.py, notifications.py, audit.py, espace_employe.py).", "Couche Routeurs (app/routes/)")
    add_bullet(doc, "Modèles Pydantic assurant la validation stricte des entrées/sorties HTTP, la désérialisation sécurisée et la documentation interactive automatique (OpenAPI / Swagger UI).", "Couche Schémas (app/schemas/)")
    add_bullet(doc, "Logique métier spécialisée (ai_service.py pour Gemini, email_service.py pour Brevo, notification_service.py pour les alertes, document_generator.py pour la génération Word, security.py pour les tokens et le hachage).", "Couche Services Métier (app/core/)")
    add_bullet(doc, "Entités SQLAlchemy modélisant les tables relationnelles, les contraintes et les jointures.", "Couche Modèles ORM (app/models/)")

    add_heading_2(doc, "3.4 Architecture Détaillée du Frontend React")
    add_paragraph(doc,
        "Le frontend React 18 s'appuie sur une structure claire et modulaire :",
        space_after=4)
    add_bullet(doc, "Routage déclaratif avec React Router DOM v6, intégrant des composants de protection d'accès (ProtectedRoute) qui filtrent la navigation en fonction du rôle authentifié (RH ou Employé).", "Routage & Sécurité")
    add_bullet(doc, "Gestion centralisée de la session utilisateur via un contexte React (AuthContext), stockant l'état d'authentification et les jetons JWT.", "Gestion d'État (Context API)")
    add_bullet(doc, "Stylisation personnalisée en CSS Vanilla et CSS Modules, adoptant les principes contemporains du Glassmorphism (effets de flou d'arrière-plan, transparence maîtrisée, contrastes étudiés, badges colorés et micro-animations).", "Design System & Glassmorphism")

    add_heading_2(doc, "3.5 Modélisation des Données et Diagramme de Classes UML")
    add_paragraph(doc,
        "Le modèle de données a été élaboré pour traduire avec une fidélité absolue les relations complexes entre les collaborateurs, leurs contrats et les clauses applicables. Le diagramme de classes UML (Figure 3) détaille les entités du domaine :",
        space_after=6)

    add_figure(doc, "fig_class_diagram.png", "Figure 3 — Diagramme de Classes Métier UML et Schéma ORM", width=5.8)

    add_paragraph(doc, "Les entités majeures du modèle sont définies comme suit :", space_after=4)
    add_bullet(doc, "Représente tout utilisateur du système (Administrateur RH ou Employé). Elle stocke les données d'identité, les coordonnées, le département, le poste, le hash du mot de passe (Bcrypt), ainsi que les compteurs de sécurité pour la politique de verrouillage.", "Utilisateur")
    add_bullet(doc, "Représente l'engagement juridique d'un collaborateur. Il contient la référence unique, le type (CDI, CDD, STAGE, ALTERNANCE), les dates d'effet, le salaire et le statut métier.", "Contrat")
    add_bullet(doc, "Représente une clause contractuelle type. L'attribut contenu_par_defaut peut contenir du texte standard ou une structure JSON complexe comprenant des tableaux de données.", "Article")
    add_bullet(doc, "Table d'association Many-to-Many entre Contrat et Article, enrichie d'une colonne ordre garantissant l'ordonnancement exact des clauses lors de la génération du document.", "contrat_articles")
    add_bullet(doc, "Entité de traçabilité enregistrant chaque opération sensible, son auteur, l'entité ciblée, l'adresse IP et les états avant/après au format JSONB.", "AuditLog")
    add_bullet(doc, "Stocke les alertes d'expiration et notifications système. Comporte un champ dedup_key unique garantissant l'absence de doublons.", "Notification")

    add_heading_2(doc, "3.6 Conception Dynamique et Diagrammes de Séquence")
    add_paragraph(doc,
        "Pour décrire le comportement temporel du système, nous présentons deux diagrammes de séquence illustrant des cas critiques.",
        space_after=4)

    add_paragraph(doc,
        "Le premier scénario (Figure 4) modélise la procédure d'authentification sécurisée : vérification du mot de passe avec Bcrypt, contrôle du verrouillage de compte (lockout) et émission conjointe d'un Access Token (durée courte) et d'un Refresh Token (durée longue, stocké de manière sécurisée).",
        bold_prefix="1. Authentification Sécurisée & Émission des Tokens :", space_after=6)
    
    add_figure(doc, "fig_sequence_auth.png", "Figure 4 — Diagramme de Séquence : Authentification Sécurisée JWT", width=5.5)

    add_paragraph(doc,
        "Le second scénario (Figure 5) détaille le flux innovant de rédaction d'une clause contractuelle assistée par l'IA : transmission du prompt du responsable RH à l'API FastAPI, interconnexion avec Google Gemini avec un schéma JSON strict, journalisation automatique dans l'AuditLog et retour d'un payload enrichi (paragraphes et tableaux) visualisable en direct dans la modale React.",
        bold_prefix="2. Rédaction Assistée par l'Assistant IA :", space_after=6)

    add_figure(doc, "fig_sequence_ai_clause.png", "Figure 5 — Diagramme de Séquence : Rédaction de Clause via l'Assistant IA", width=5.5)

    add_heading_2(doc, "3.7 Modélisation du Cycle de Vie des Contrats (Machine à États)")
    add_paragraph(doc,
        "La gestion des statuts de contrat a fait l'objet d'une conception rigoureuse sous la forme d'une machine à états finis (Figure 6). Contrairement à une simple sélection libre de statuts, le système n'autorise que les transitions strictement logiques et conformes au droit social :",
        space_after=6)

    add_figure(doc, "fig_contract_lifecycle.png", "Figure 6 — Machine à États & Cycle de Vie des Statuts de Contrats", width=5.6)

    add_paragraph(doc, "Le Tableau 4 synthétise la sémantique et les règles appliquées à chaque statut :", space_after=6)

    statuts_data = [
        ("BROUILLON", "Brouillon", "Contrat en cours de composition ou de révision. Modifiable librement.", "COMMUNIQUE_EN_COURS, PAS_DISCUTE"),
        ("COMMUNIQUE_EN_COURS", "Communiqué (en cours)", "Contrat transmis au salarié pour lecture et examen.", "SIGNE, BROUILLON"),
        ("SIGNE", "Signé", "Contrat paraphé et signé par les deux parties prenantes.", "ACTIF"),
        ("ACTIF", "Actif", "Contrat en vigueur. Déclenche l'envoi d'un email d'activation. Fait foi juridiquement.", "FIN_CDD (si CDD), DEMISSION_CDI (si CDI)"),
        ("FIN_CDD", "Fin CDD", "Terme légal atteint pour un contrat à durée déterminée.", "INACTIF"),
        ("DEMISSION_CDI", "Démission (CDI)", "Rupture du contrat à durée indéterminée à l'initiative du collaborateur.", "INACTIF"),
        ("PAS_DISCUTE", "Pas discuté", "Statut spécifique réservé aux situations contractuelles non arbitrées.", "BROUILLON, COMMUNIQUE_EN_COURS"),
        ("INACTIF", "Inactif (archivé)", "Contrat historisé et clos. Ne génère aucune alerte et ne figure plus comme actif.", "État final (Archivé)")
    ]
    add_styled_table(doc, ["Code Enum", "Libellé Interface", "Définition Métier & Portée Juridique", "Transitions Autorisées"], statuts_data, col_widths=[1.4, 1.4, 2.3, 1.7])

    add_heading_2(doc, "3.8 Sécurité, Authentification et Contrôle d'Accès (RBAC)")
    add_paragraph(doc,
        "La sécurité des données RH constituant un impératif absolu, le système déploie un ensemble de mécanismes de défense en profondeur :",
        space_after=4)
    add_bullet(doc, "Chaque mot de passe est haché avec l'algorithme Bcrypt (sel cryptographique dynamique de coût 12), rendant impossible toute rétro-ingénierie.", "Hachage robuste des secrets")
    add_bullet(doc, "Après 5 échecs consécutifs d'authentification sur un même compte, l'accès est automatiquement bloqué pendant 15 minutes, neutralisant les attaques par dictionnaire.", "Protection Anti-Brute Force")
    add_bullet(doc, "L'Access Token est émis avec une durée de validité réduite (30 minutes). Le renouvellement transparent de session est assuré par un Refresh Token sécurisé à rotation systématique.", "Jetons JWT éphémères et Refresh Tokens")
    add_bullet(doc, "Chaque route d'API vérifie les droits du jeton via le système d'injection de dépendances de FastAPI (ex: Depends(require_role([RoleEnum.ADMIN, RoleEnum.RH]))).", "Contrôle d'accès basé sur les rôles (RBAC)")

    add_heading_2(doc, "3.9 Justification des Choix Technologiques")
    add_paragraph(doc, "Le Tableau 5 détaille les arguments comparatifs ayant présidé au choix des composants de la stack technique :", space_after=6)

    tech_data = [
        ("Backend", "FastAPI (Python)", "Django, Flask", "Performance asynchrone exceptionnelle (ASGI), typage statique puissant via Pydantic prévenant les anomalies à l'exécution, documentation interactive Swagger native."),
        ("Frontend", "React 18 & Vite", "Angular, Vue.js", "Écosystème riche de composants, temps de compilation quasi instantané grâce à Vite (ESBuild), gestion élégante de l'état par hooks et Context API."),
        ("Base de Données", "PostgreSQL", "MySQL, MongoDB", "Robustesse ACID reconnue, support natif du format JSONB pour les articles structurés et les deltas d'audit, puissance des contraintes relationnelles."),
        ("Intelligence Artificielle", "Google Gemini 1.5", "OpenAI GPT-4, Grok", "Excellente compréhension du français juridique, capacité à respecter strictement des contraintes de schéma JSON (function calling/structured outputs), rapidité de traitement."),
        ("Emails Transactionnels", "Brevo API", "SMTP Standard", "Délivrabilité optimale, suivi en temps réel du statut de distribution des emails, élimination des risques de blocage par les filtres anti-spam."),
        ("Génération DOCX", "python-docx", "Weasyprint (PDF)", "Permet au service RH de modifier ou annoter le document généré sous Word avant impression, support natif des tableaux stylisés.")
    ]
    add_styled_table(doc, ["Domaine", "Technologie Retenue", "Alternatives Comparées", "Justification Technique & Bénéfices Métiers"], tech_data, col_widths=[1.0, 1.3, 1.2, 3.3])

    add_heading_2(doc, "3.10 Conclusion du Chapitre")
    add_paragraph(doc,
        "La conception architecturale et la modélisation UML présentées dans ce chapitre établissent un cadre rigoureux et évolutif. Le chapitre suivant expose la réalisation technique et l'implémentation concrète de chaque composant au sein de l'application.",
        space_after=10)

    doc.add_page_break()

def build_chapter_4(doc):
    # =========================================================================
    # CHAPITRE 4 : RÉALISATION ET MISE EN ŒUVRE DE L'APPLICATION
    # =========================================================================
    add_heading_1(doc, "CHAPITRE 4 : RÉALISATION ET MISE EN ŒUVRE DE L'APPLICATION")

    add_heading_2(doc, "4.1 Introduction")
    add_paragraph(doc,
        "Ce chapitre est consacré à la phase de réalisation concrète de l'application web RH. Il détaille les environnements techniques et outils déployés, puis présente chronologiquement l'implémentation des différents modules fonctionnels : authentification, gestion des collaborateurs, catalogue d'articles, Assistant IA, gestion du cycle de vie des contrats, génération Word, moteur d'alertes dédupliquées, journal d'audit et espace collaborateur. Il s'achève par une galerie commentée des interfaces représentatives.",
        space_after=8)

    add_heading_2(doc, "4.2 Environnement de Développement et Outillage")
    add_paragraph(doc, "Le développement du projet a mobilisé des outils et frameworks de pointe :", space_after=4)
    add_bullet(doc, "Python 3.10, FastAPI 0.110+, SQLAlchemy 2.0, Pydantic v2, Alembic, python-docx, Pytest 9.1.", "Environnement Backend")
    add_bullet(doc, "Node.js v20+, React 18, Vite 5, React Router DOM v6, Lucide-React, Axios.", "Environnement Frontend")
    add_bullet(doc, "PostgreSQL 15, PgAdmin 4, Docker.", "Environnement Données")
    add_bullet(doc, "Visual Studio Code, Antigravity IDE, Git & GitHub pour le versionnement rigoureux du code source.", "Outils de Développement")

    add_heading_2(doc, "4.3 Module d'Authentification et Gestion des Sessions")
    add_paragraph(doc,
        "L'accès à l'application débute par une mire de connexion épurée et sécurisée. Le formulaire capture l'identifiant (email) et le mot de passe, soumis via une requête sécurisée à l'endpoint /api/auth/login. Le composant gère les retours visuels interactifs : affichage d'un indicateur de chargement, notification explicite en cas d'identifiants incorrects ou avertissement si le compte fait l'objet d'un verrouillage temporaire.",
        space_after=6)

    add_heading_2(doc, "4.4 Module de Gestion des Dossiers Collaborateurs")
    add_paragraph(doc,
        "Le module de gestion des employés offre une vue d'ensemble ergonomique du capital humain de l'entreprise. L'interface propose un tableau paginé affichant le matricule, le nom, le prénom, l'adresse email professionnelle, le département d'affectation, le poste occupé et la date d'embauche. Des filtres dynamiques permettent une recherche instantanée par nom ou département. Un formulaire modal dédié permet d'ajouter un nouveau collaborateur ou d'éditer ses informations, avec validation immédiate des formats de téléphone et d'email.",
        space_after=6)

    add_heading_2(doc, "4.5 Bibliothèque d'Articles Contractuels Réutilisables")
    add_paragraph(doc,
        "L'un des points forts fonctionnels de l'application réside dans la modularité de ses clauses. Le responsable RH accède à une bibliothèque centralisée d'articles types (clause de confidentialité, période d'essai, télétravail, rémunération, non-concurrence). Chaque article est identifié par un code normalisé, un titre explicite et un contenu éditable. Un commutateur permet d'activer ou de désactiver une clause sans jamais supprimer l'historique des contrats qui y font référence.",
        space_after=6)

    add_heading_2(doc, "4.6 Assistant IA pour la Rédaction de Clauses Contractuelles")
    add_paragraph(doc,
        "Pour apporter une assistance opérationnelle à forte valeur ajoutée, l'application intègre un Assistant d'Intelligence Artificielle générative exploitant l'API Google Gemini 1.5, spécialement configuré pour la rédaction de clauses juridiques en droit social.",
        space_after=4)
    
    add_paragraph(doc,
        "L'administrateur RH saisit une consigne en langage naturel (ex : 'Rédige une clause de télétravail prévoyant 2 jours par semaine sous droit français/tunisien'). L'assistant génère alors une proposition de clause claire, précise et professionnellement formulée.",
        bold_prefix="• Principe d'assistance :", space_after=4)

    add_paragraph(doc,
        "L'assistant dépasse la simple génération de texte brut en prenant en charge des structures complexes comprenant des paragraphes, des tableaux natifs (particulièrement pertinents pour formaliser des grilles de salaire ou des barèmes d'objectifs) ou un mélange harmonieux des deux (format mixte).",
        bold_prefix="• Prise en charge des tableaux de rémunération :", space_after=4)

    add_paragraph(doc,
        "L'Assistant IA est conçu comme un outil d'assistance à la rédaction et non comme un juriste autonome. Le responsable RH conserve la pleine maîtrise éditoriale : il peut relire la clause générée, modifier ses valeurs chiffrées dans un éditeur dédié et ne l'enregistre dans la bibliothèque qu'après validation explicite.",
        bold_prefix="• Validation humaine obligatoire :", space_after=6)

    add_callout(doc,
        "Le service IA dispose d'un mécanisme de secours (fallback) automatique : si le modèle ne renvoie pas la structure JSON attendue, le moteur convertit automatiquement la réponse en un format paragraphe standard et trame l'opération dans le journal d'audit (AuditAction.AI_GENERATE).",
        title="Garantie de robustesse du service IA")

    add_heading_2(doc, "4.7 Gestion des Contrats et Nouveaux Workflows de Statuts")
    add_paragraph(doc,
        "Le module des contrats orchestre l'ensemble du cycle de vie juridique. Lors de la création, le responsable RH sélectionne un collaborateur dans la liste déroulante et spécifie le type de contrat (CDI, CDD, Stage, Alternance). L'interface adapte dynamiquement ses champs : la date de fin devient obligatoire pour un CDD alors qu'elle est désactivée pour un CDI.",
        space_after=6)
    add_paragraph(doc,
        "Le système implémente avec rigueur les nouveaux statuts demandés : BROUILLON, COMMUNIQUE_EN_COURS, SIGNE, ACTIF, FIN_CDD, DEMISSION_CDI, PAS_DISCUTE et INACTIF. Les badges visuels affichent des couleurs sémantiques immédiates (orange pour Brouillon, bleu pour Communiqué, violet pour Signé, vert pour Actif, rouge pour Démission, gris pour Inactif). Les sélecteurs de transition empêchent toute régression illogique (ex : impossible de repasser un contrat Actif à Brouillon).",
        space_after=6)

    add_heading_2(doc, "4.8 Moteur de Génération Automatique des Documents Word (.docx)")
    add_paragraph(doc,
        "L'application intègre un moteur de rendu bureautique haute fidélité basé sur python-docx. En cliquant sur le bouton « Générer le contrat », le serveur extrait les données administratives de l'employé et l'ensemble des articles associés au contrat selon leur ordre défini.",
        space_after=6)
    add_paragraph(doc,
        "Le document généré respecte la charte graphique de CSI Digital : en-tête avec logos, typographie Calibri soignée, paragraphes justifiés, et conversion directe des clauses structurées en véritables tableaux Word natifs dotés d'en-têtes foncés et de bordures élégantes. Le document est immédiatement téléchargeable par l'administrateur RH ou par l'employé.",
        space_after=6)

    add_heading_2(doc, "4.9 Système de Traçabilité et Journal d'Audit (Audit Logs)")
    add_paragraph(doc,
        "La traçabilité de l'application est assurée par un composant d'audit centralisé. Chaque opération critique (changement de statut de contrat, mise à jour d'un employé, connexion échouée, génération de clause par l'IA) fait l'objet d'un enregistrement immuable dans la table audit_logs. L'interface d'audit permet au responsable RH de filtrer les événements par utilisateur, par type d'action ou par plage de dates, et d'inspecter les deltas JSON (anciennes vs nouvelles valeurs) pour une transparence totale.",
        space_after=6)

    add_heading_2(doc, "4.10 Moteur d'Alertes RH et Notifications Dédupliquées")
    add_paragraph(doc,
        "Le suivi des échéances de contrats CDD est automatisé par un moteur d'arrière-plan analysant quotidiennement les dates de fin de contrat. Des alertes prioritaires sont levées aux paliers cruciaux de 30 jours, 15 jours et 7 jours précédant le terme du contrat.",
        space_after=6)
    add_paragraph(doc,
        "Pour éliminer tout risque d'inondation de notifications ou d'envois multiples lors d'exécutions concurrentes, le système génère une clé d'idempotence unique (dedup_key) combinant l'identifiant du contrat, le type d'alerte et le palier de jours. L'interface d'alertes regroupe ces notifications avec un code couleur d'urgence (Information, Avertissement, Critique).",
        space_after=6)

    add_heading_2(doc, "4.11 Service Transactionnel d'Emails (API Brevo)")
    add_paragraph(doc,
        "L'application est interconnectée avec la plateforme professionnelle Brevo via son API REST transactionnelle. Des emails au format HTML élégant et charté sont automatiquement expédiés :",
        space_after=4)
    add_bullet(doc, "Un email est envoyé au collaborateur pour l'informer de la prise d'effet de son contrat et l'inviter à se connecter à son espace.", "Activation du contrat (SIGNE → ACTIF)")
    add_bullet(doc, "Des alertes par email sont adressées au responsable RH afin d'anticiper le renouvellement ou la clôture administrative du collaborateur.", "Alertes d'échéance CDD")

    add_heading_2(doc, "4.12 Espace Dédié Collaborateur (Self-Service)")
    add_paragraph(doc,
        "L'employé bénéficie d'un espace personnel restreint. Dès son authentification, il accède à son tableau de bord affichant ses informations administratives et son contrat en vigueur. L'employé peut consulter les articles composant son engagement et télécharger son contrat officiel au format Word. Les fonctionnalités d'écriture, de modification de statuts ou d'accès aux dossiers des tiers lui sont rigoureusement inaccessibles.",
        space_after=6)

    add_heading_2(doc, "4.13 Galerie Commentée des Interfaces Utilisateur")
    add_paragraph(doc,
        "Les figures 7 à 16 ci-après présentent les principales interfaces opérationnelles développées au sein de l'application RH :",
        space_after=6)

    add_figure(doc, "screen_login.png", "Figure 7 — Interface de Connexion Sécurisée (Authentification JWT & Protection Lockout)", width=5.2)
    add_figure(doc, "screen_dashboard.png", "Figure 8 — Tableau de Bord & Gestion Administrative des Collaborateurs", width=5.5)
    add_figure(doc, "screen_articles.png", "Figure 9 — Bibliothèque des Articles Contractuels Réutilisables avec Badges de Structure", width=5.5)
    add_figure(doc, "screen_article_editor.png", "Figure 10 — Modale d'Édition et de Création d'un Nouvel Article Contractuel", width=5.5)
    add_figure(doc, "screen_ai_modal.png", "Figure 11 — Assistant IA : Saisie du Prompt et Paramétrage de la Clause", width=5.5)
    add_figure(doc, "screen_ai_structured.png", "Figure 12 — Assistant IA : Rendu Structuré avec Grille de Rémunération en Tableau", width=5.5)
    add_figure(doc, "screen_contrats.png", "Figure 13 — Gestion des Contrats de Travail avec Nouveaux Badges de Statuts et Actions", width=5.5)
    add_figure(doc, "screen_alertes.png", "Figure 14 — Centre de Suivi des Alertes d'Expiration et Notifications RH Dédupliquées", width=5.5)
    add_figure(doc, "screen_audit.png", "Figure 15 — Journal d'Audit Centralisé (Traçabilité des Actions et Deltas JSONB)", width=5.2)
    add_figure(doc, "screen_espace_employe.png", "Figure 16 — Espace Dédié Collaborateur (Consultation en Lecture Seule du Contrat Actif)", width=5.5)

    add_heading_2(doc, "4.14 Conclusion du Chapitre")
    add_paragraph(doc,
        "La réalisation technique de l'application web RH concrétise fidèlement l'ensemble des spécifications fonctionnelles, tout en intégrant des innovations à forte valeur ajoutée telles que l'Assistant IA pour la rédaction de clauses et un cycle de vie contractuel hautement sécurisé. Le chapitre suivant présente la démarche de validation, la suite de tests et les résultats obtenus.",
        space_after=10)

    doc.add_page_break()

print("Chapters 3 and 4 generated successfully.")
