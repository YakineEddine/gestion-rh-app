# -*- coding: utf-8 -*-
"""
Chapitre 5 : Tests, Validation et Assurance Qualité
Chapitre 6 : Bilan, Compétences et Perspectives
Conclusion Générale, Bibliographie et Annexes
"""

from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from build_report_full import (
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TEXT, COLOR_MUTED, COLOR_ACCENT,
    add_heading_1, add_heading_2, add_heading_3, add_paragraph, add_bullet,
    add_callout, add_styled_table, add_figure
)

def build_chapter_5(doc):
    # =========================================================================
    # CHAPITRE 5 : TESTS, VALIDATION ET ASSURANCE QUALITÉ
    # =========================================================================
    add_heading_1(doc, "CHAPITRE 5 : TESTS, VALIDATION ET ASSURANCE QUALITÉ")

    add_heading_2(doc, "5.1 Introduction")
    add_paragraph(doc,
        "La phase de vérification et de validation constitue une étape déterminante du cycle de vie logiciel. Elle vise à attester de la conformité rigoureuse du système développé vis-à-vis des exigences fonctionnelles et des critères de sécurité formulés lors de la spécification. Ce chapitre expose la stratégie globale de test, détaille les résultats de la campagne d'essais automatisés backend (78 tests réussis avec 100% de succès), analyse la résilience de la sécurité et présente les difficultés techniques surmontées durant l'implémentation.",
        space_after=8)

    add_heading_2(doc, "5.2 Stratégie Globale de Test")
    add_paragraph(doc,
        "Afin d'assurer une couverture exhaustive et d'éliminer tout risque de régression lors de l'évolution des fonctionnalités (notamment lors de l'intégration des nouveaux statuts de contrat et du format structuré de l'IA), nous avons adopté une stratégie pyramidale combinant :",
        space_after=4)
    add_bullet(doc, "Validation unitaire isolée des fonctions critiques (validation des schémas Pydantic, algorithmes de hachage, parsing JSON de l'IA et génération native DOCX).", "Tests Unitaires")
    add_bullet(doc, "Vérification de l'interconnexion entre les composants logiciels (routeurs d'API, requêtes SQLAlchemy en base de données, déduplication des alertes, services externes).", "Tests d'Intégration")
    add_bullet(doc, "Contrôle strict des accès non autorisés, simulation d'attaques par force brute, validation de la révocation des tokens et étanchéité de l'espace collaborateur.", "Tests de Sécurité")

    add_heading_2(doc, "5.3 Tests Backend Automatisés (Pytest / Unittest - 78 tests)")
    add_paragraph(doc,
        "Le backend dispose d'une suite complète de tests automatisés exécutés via le framework Pytest. La campagne de tests exécutée dans l'environnement de développement produit un taux de réussite parfait de 100% sur l'ensemble des 78 cas de test (Tableau 6) :",
        space_after=6)

    test_summary_data = [
        ("test_ai_service.py", "11 / 11", "100%", "Validation du service IA Gemini, support des clauses structurées (paragraphes, tableaux, mixte), fallback transparent et génération de tableau Word natif."),
        ("test_auth_hardening.py", "16 / 16", "100%", "Validation de la politique anti-brute force, verrouillage temporaire après 5 échecs, renouvellement sécurisé par refresh tokens et contrôle RBAC."),
        ("test_contract_status_transitions.py", "16 / 16", "100%", "Validation de la machine à états des contrats : parcours Brouillon → Communiqué → Signé → Actif, fin CDD, démission CDI et rejet des transitions illégales."),
        ("test_direct_access_email.py", "7 / 7", "100%", "Contrôle des liens de consultation directe reçus par email et redirection contextuelle selon la session connectée."),
        ("test_employee_alerts.py", "10 / 10", "100%", "Vérification des calculs d'échéance à 30, 15 et 7 jours, exclusion des CDI sans terme et garantie d'unicité (clé dedup_key)."),
        ("test_employee_profile_security.py", "8 / 8", "100%", "Étanchéité de l'espace collaborateur : lecture seule garantie, impossibilité d'altérer les statuts ou de consulter les données d'autres salariés."),
        ("test_recaptcha_login.py", "10 / 10", "100%", "Validation des contrôles anti-robots reCAPTCHA et résistance des formulaires d'authentification.")
    ]
    add_styled_table(doc, ["Fichier de Test", "Succès", "Taux", "Périmètre Fonctionnel & Technique Validé"], test_summary_data, col_widths=[1.8, 0.7, 0.6, 3.4])

    add_heading_2(doc, "5.4 Tests des Transitions de Statuts et Cohérence des Contrats")
    add_paragraph(doc,
        "Le module test_contract_status_transitions.py vérifie spécifiquement l'intégrité du nouveau workflow contractuel :",
        space_after=4)
    add_bullet(doc, "Vérification qu'un contrat nouvellement créé est obligatoirement initialisé à l'état BROUILLON.", "Test 1 : Création initiale")
    add_bullet(doc, "Validation de la séquence ordonnée : BROUILLON → COMMUNIQUE_EN_COURS → SIGNE → ACTIF.", "Test 2 : Parcours d'activation nominal")
    add_bullet(doc, "Vérification qu'un CDD actif bascule vers FIN_CDD à son échéance, puis vers INACTIF.", "Test 3 : Cycle de fin de CDD")
    add_bullet(doc, "Vérification qu'un CDI actif bascule vers DEMISSION_CDI lors d'une rupture, puis vers INACTIF. Validation de l'interdiction d'appliquer FIN_CDD à un CDI.", "Test 4 : Cycle de rupture CDI")
    add_bullet(doc, "Validation de l'interdiction absolue de régression (ex : ACTIF → BROUILLON renvoie une erreur HTTP 400 Bad Request).", "Test 5 : Blocage des transitions invalides")
    add_bullet(doc, "Contrôle que chaque changement d'état génère un enregistrement immuable dans l'AuditLog avec l'ancien et le nouveau statut.", "Test 6 : Traçabilité dans l'AuditLog")

    add_heading_2(doc, "5.5 Tests du Moteur d'Alertes et Idempotence de la Déduplication")
    add_paragraph(doc,
        "Le module test_employee_alerts.py valide le moteur d'alertes RH :",
        space_after=4)
    add_bullet(doc, "Vérification que seules les dates d'échéance de CDD réelles génèrent des alertes (les CDI sans date de fin et les contrats inactifs/archivés sont ignorés).", "Ciblage précis des contrats")
    add_bullet(doc, "Garantie que deux exécutions consécutives du moteur d'alertes ne produisent aucun doublon grâce à la contrainte d'unicité dedup_key en base de données.", "Idempotence & Déduplication")

    add_heading_2(doc, "5.6 Tests du Service IA et Robustesse des Clauses Structurées")
    add_paragraph(doc,
        "Le module test_ai_service.py atteste de la fiabilité des fonctionnalités d'Intelligence Artificielle :",
        space_after=4)
    add_bullet(doc, "Vérification de la conformité du payload JSON généré (présence du type 'table' ou 'mixed', liste de colonnes headers et lignes rows).", "Validation structurelle")
    add_bullet(doc, "Vérification du fallback transparent vers le format paragraphe textuel standard en cas de réponse non conforme du modèle.", "Résilience et Fallback")
    add_bullet(doc, "Validation de l'insertion de véritables tableaux Word natifs par le document_generator sans altération des anciens articles texte.", "Génération DOCX native")

    add_heading_2(doc, "5.7 Tests de Sécurité et Résistance aux Attaques")
    add_paragraph(doc,
        "La sécurité a fait l'objet de vérifications approfondies :",
        space_after=4)
    add_bullet(doc, "Simulation de 5 saisies consécutives de mots de passe erronés : le compte est automatiquement verrouillé et l'API renvoie HTTP 423 Locked jusqu'à expiration du délai de 15 minutes.", "Verrouillage de compte (Lockout)")
    add_bullet(doc, "Vérification que l'accès aux routes d'administration (/api/contrats, /api/employes, /api/audit) avec un jeton porteur du rôle 'EMPLOYE' est systématiquement rejeté par une erreur HTTP 403 Forbidden.", "Étanchéité des privilèges (RBAC)")

    add_heading_2(doc, "5.8 Tests d'Intégration Frontend et Validation Ergonomique")
    add_paragraph(doc,
        "L'interface utilisateur React a été validée au moyen de tests multi-résolutions et multi-navigateurs (Chrome, Firefox, Edge). Les formulaires intègrent des validations réactives empêchant la soumission de données incohérentes (ex: date de fin antérieure à la date de début). La compilation du bundle de production via Vite (npm run build) a été exécutée avec un résultat sans aucune erreur ni avertissement.",
        space_after=6)

    add_heading_2(doc, "5.9 Synthèse des Résultats Obtenus")
    add_paragraph(doc, "Le Tableau 7 récapitule la matrice de couverture fonctionnelle et technique :", space_after=6)

    matrice_data = [
        ("Authentification & Sécurité", "Bcrypt, JWT, Refresh Tokens, Lockout 5 tentatives, Protection RBAC", "100%", "Validé sans réserve"),
        ("Gestion des Collaborateurs", "CRUD complet, pagination, recherche, matricule unique", "100%", "Validé sans réserve"),
        ("Bibliothèque d'Articles", "Catalogue de clauses, commutateur d'activation, édition modale", "100%", "Validé sans réserve"),
        ("Assistant IA (Gemini)", "Génération en langage naturel, format structuré (tableaux), fallback", "100%", "Validé sans réserve"),
        ("Cycle de Vie des Contrats", "Transitions Brouillon → Communiqué → Signé → Actif, Fin CDD, Démission", "100%", "Validé sans réserve"),
        ("Moteur d'Alertes & Emails", "Échéances 30/15/7 jours, déduplication dedup_key, API Brevo", "100%", "Validé sans réserve"),
        ("Génération Bureautique", "Génération automatique DOCX, tableaux natifs stylisés, téléchargement", "100%", "Validé sans réserve"),
        ("Journal d'Audit", "Traçabilité complète, capture des deltas JSONB, filtres avancés", "100%", "Validé sans réserve"),
        ("Espace Collaborateur", "Consultation profil et contrat actif en lecture seule, téléchargement", "100%", "Validé sans réserve")
    ]
    add_styled_table(doc, ["Module Métier", "Composants et Mécanismes Testés", "Couverture", "Statut de Recette"], matrice_data, col_widths=[1.5, 2.7, 0.9, 1.4])

    add_heading_2(doc, "5.10 Problèmes Rencontrés et Solutions Apportées")
    add_paragraph(doc,
        "Durant la phase de réalisation, plusieurs défis techniques majeurs ont été surmontés avec succès :",
        space_after=4)

    add_paragraph(doc,
        "Par nature probabiliste, un modèle de langage (LLM) peut occasionnellement dévier du format JSON demandé. Pour garantir une fiabilité absolue, nous avons combiné un prompt système contraignant exigeant un schéma JSON précis, un validateur Pydantic côté backend et une fonction de fallback convertissant toute réponse atypique en texte brut exploitable sans blocage.",
        bold_prefix="• Variabilité des réponses de l'IA générative :", space_after=5)

    add_paragraph(doc,
        "L'exécution répétée ou concurrente du script d'analyse des dates d'échéance risquait de saturer la table des notifications de messages identiques. Ce problème a été résolu en concevant une clé de déduplication déterministe (dedup_key = f'CONTRACT_EXPIRING_{contract_id}_{days_left}d_{year_month}') indexée de manière unique en base de données.",
        bold_prefix="• Risque de doublons dans le moteur d'alertes :", space_after=5)

    add_paragraph(doc,
        "Lorsqu'un utilisateur cliquait sur le lien d'un email d'alerte pour consulter son contrat, le système devait gérer intelligemment l'état de session : si la session active correspondait à un compte administrateur, l'application évitait une redirection erronée en invitant courtoisement l'utilisateur à se connecter avec le compte collaborateur concerné.",
        bold_prefix="• Conflit de session lors de l'accès direct par email :", space_after=6)

    add_heading_2(doc, "5.11 Conclusion du Chapitre")
    add_paragraph(doc,
        "La rigueur de la stratégie de qualification et le succès intégral des 78 tests automatisés attestent de la robustesse, de la sécurité et de la maturité opérationnelle de l'application. Le chapitre suivant dresse le bilan du stage et esquisse les perspectives d'évolution future.",
        space_after=10)

    doc.add_page_break()

def build_chapter_6(doc):
    # =========================================================================
    # CHAPITRE 6 : BILAN, COMPÉTENCES ET PERSPECTIVES
    # =========================================================================
    add_heading_1(doc, "CHAPITRE 6 : BILAN, COMPÉTENCES ET PERSPECTIVES")

    add_heading_2(doc, "6.1 Bilan Global du Projet")
    add_paragraph(doc,
        "Le projet réalisé dans le cadre de ce stage de fin d'études chez CSI Digital a permis d'atteindre avec succès l'ensemble des objectifs fixés dans le cahier des charges initial. L'application web RH développée constitue une solution opérationnelle, moderne et intégrée, répondant aux défis quotidiens de gestion du personnel et de sécurisation du cycle de vie contractuel.",
        space_after=6)
    add_paragraph(doc,
        "En substituant une plateforme centralisée et automatisée aux anciens processus manuels dispersés (fichiers tableurs et copier-coller bureautique), le système procure des gains d'efficacité immédiats : réduction drastique du temps d'élaboration des contrats grâce aux articles modulaires et à l'Assistant IA, élimination des erreurs humaines de ressaisie, anticipation proactive des échéances de fin de CDD et garantie d'une conformité légale et sécuritaire absolue.",
        space_after=8)

    add_heading_2(doc, "6.2 Compétences Techniques et Humaines Acquises")
    add_paragraph(doc,
        "Ce projet a été le creuset d'un enrichissement professionnel et personnel déterminant, favorisant l'acquisition et le perfectionnement de compétences variées :",
        space_after=4)

    add_paragraph(doc,
        "Maîtrise approfondie du framework asynchrone FastAPI, conception de modèles de données relationnels optimisés avec PostgreSQL et SQLAlchemy 2.0, intégration d'APIs tierces de premier plan (Google Gemini AI, Brevo Email API), mise en œuvre de mécanismes de sécurité avancés (Bcrypt, JWT avec rotation de refresh tokens, politiques anti-brute force) et écriture de suites de tests automatisés avec Pytest.",
        bold_prefix="• Compétences Techniques Backend :", space_after=5)

    add_paragraph(doc,
        "Maîtrise de React 18 et de son outillage moderne (Vite), gestion efficace du routage et des contextes d'authentification, conception d'une interface responsive élégante en CSS Vanilla et Glassmorphism, et modélisation de composants dynamiques et ergonomiques.",
        bold_prefix="• Compétences Techniques Frontend :", space_after=5)

    add_paragraph(doc,
        "Application concrète des cérémonies et des principes de la méthodologie agile Scrum, planification des sprints, rédaction de cahiers des charges précis, modélisation UML rigoureuse et utilisation professionnelle du gestionnaire de versions Git.",
        bold_prefix="• Compétences Méthodologiques & Génie Logiciel :", space_after=5)

    add_paragraph(doc,
        "Développement de l'autonomie, de la rigueur intellectuelle, de la capacité d'écoute et de restitution face aux exigences métiers de l'encadrement en entreprise, ainsi qu'une aptitude renforcée à la communication technique.",
        bold_prefix="• Compétences Humaines et Relationnelles :", space_after=8)

    add_heading_2(doc, "6.3 Limites Actuelles de la Solution")
    add_paragraph(doc,
        "Bien que l'application soit pleinement fonctionnelle et prête pour un déploiement en environnement de pré-production, elle présente certaines limites délimitant son périmètre actuel :",
        space_after=4)
    add_bullet(doc, "Le système génère des documents Word prêts pour signature manuscrite mais n'intègre pas encore de connecteur natif vers des plateformes de signature électronique légalement certifiées (ex : DocuSign ou Yousign conforme eIDAS).", "Absence de signature électronique certifiée")
    add_bullet(doc, "L'application gère les rémunérations contractuelles mais ne comprend pas de module complet d'édition de fiches de paie mensuelles ni de calcul des cotisations sociales.", "Périmètre paie non couvert")
    add_bullet(doc, "L'accès est actuellement optimisé pour les navigateurs web de bureau et tablettes, sans application mobile dédiée.", "Absence d'application mobile native")

    add_heading_2(doc, "6.4 Perspectives d'Évolution et Travaux Futurs")
    add_paragraph(doc,
        "Pour prolonger les acquis de ce travail et enrichir la valeur apportée aux directions des ressources humaines, plusieurs pistes d'évolution prometteuses sont envisagées :",
        space_after=4)
    add_bullet(doc, "Intégrer une solution de signature électronique cryptographique directement dans l'application, permettant au salarié de signer son contrat en ligne avec valeur probante dès la transition vers le statut SIGNÉ.", "Intégration de la Signature Électronique eIDAS")
    add_bullet(doc, "Développer un module complémentaire permettant aux employés de poser leurs demandes de congés payés et aux managers de les valider en ligne.", "Module de Gestion des Congés et Absences")
    add_bullet(doc, "Créer une application mobile (ex: avec Flutter ou React Native) offrant aux collaborateurs un accès immédiat à leurs notifications, alertes et documents administratifs sur smartphone.", "Application Mobile Collaborateur")
    add_bullet(doc, "Développer des connecteurs d'exportation standardisés (formats DSN, CSV, API) vers les principaux logiciels de gestion de paie du marché (ex : Sage, Cegid).", "Interopérabilité avec les Logiciels de Paie")

    add_heading_2(doc, "6.5 Conclusion du Chapitre")
    add_paragraph(doc,
        "Ce dernier chapitre a permis de dresser un bilan global très positif des travaux entrepris, d'objectiver les compétences techniques et humaines acquises et d'ouvrir des perspectives d'évolution concrètes pour transformer ce projet en une solution RH encore plus globale.",
        space_after=10)

    doc.add_page_break()

    # =========================================================================
    # CONCLUSION GÉNÉRALE
    # =========================================================================
    add_heading_1(doc, "CONCLUSION GÉNÉRALE")
    
    add_paragraph(doc,
        "Ce travail de fin d'études, réalisé au sein de la société CSI Digital, s'inscrit au cœur des défis contemporains de la transformation digitale des ressources humaines. L'objectif initial était ambitieux : concevoir et développer une application web RH globale, modulaire, sécurisée et intelligente, capable de rationaliser l'intégralité du cycle de vie des employés et de leurs contrats de travail.",
        space_after=6)

    add_paragraph(doc,
        "À l'issue de cette période d'ingénierie, les résultats obtenus sont pleinement satisfaisants et opérationnels. Grâce à une démarche d'analyse minutieuse et à l'adoption d'une architecture moderne découplée en trois tiers, le système combine la réactivité du framework React 18, la puissance asynchrone et le typage strict de FastAPI (Python), et la fiabilité transactionnelle de PostgreSQL.",
        space_after=6)

    add_paragraph(doc,
        "L'application se distingue par des apports méthodologiques et techniques notables :",
        space_after=4)
    add_bullet(doc, "Une bibliothèque de clauses modulaires éliminant la dispersion et la redondance des modèles traditionnels.", "Modularité contractuelle")
    add_bullet(doc, "L'introduction novatrice d'un Assistant IA basé sur Google Gemini, capable de rédiger et de structurer des clauses contractuelles complexes incluant des tableaux natifs de rémunération, sous contrôle permanent du responsable RH.", "Assistance par Intelligence Artificielle")
    add_bullet(doc, "Une machine à états finis garantissant des transitions de statuts de contrats irréversibles et juridiquement cohérentes (Brouillon, Communiqué, Signé, Actif, Fin CDD, Démission CDI, Pas discuté, Inactif).", "Sécurisation du cycle de vie")
    add_bullet(doc, "L'automatisation sans faille de la génération Word (.docx), du moteur d'alertes d'expiration dédupliquées à 30, 15 et 7 jours, et de l'envoi d'emails transactionnels via Brevo.", "Automatisation proactive")
    add_bullet(doc, "Une traçabilité intégrale assurée par un journal d'audit granulaire et une sécurité d'accès durcie protégeant l'espace collaborateur.", "Confidentialité et Auditabilité")

    add_paragraph(doc,
        "La validation rigoureuse assurée par les 78 tests automatisés (100% de réussite) confère au produit une robustesse industrielle incontestable.",
        space_after=6)

    add_paragraph(doc,
        "Sur le plan personnel, ce stage a constitué une expérience charnière dans mon parcours d'élève ingénieur à ESPRIT. Il m'a permis de mettre en pratique les compétences acquises au cours de mon cursus académique, de me confronter aux réalités exigeantes d'un projet d'entreprise et d'affirmer ma vocation pour l'architecture logicielle, le développement web full-stack et l'intégration raisonnée de l'Intelligence Artificielle au service des processus métiers.",
        space_after=14)

    doc.add_page_break()

    # =========================================================================
    # BIBLIOGRAPHIE ET WEBOGRAPHIE
    # =========================================================================
    add_heading_1(doc, "BIBLIOGRAPHIE ET WEBOGRAPHIE")

    add_heading_2(doc, "Ouvrages et Publications Académiques")
    add_paragraph(doc,
        "[1] Sommerville, I. (2016). Software Engineering (10th ed.). Pearson Education. Guide de référence en génie logiciel, cycle de vie et spécification des exigences.",
        space_after=4)
    add_paragraph(doc,
        "[2] Martin, R. C. (2017). Clean Architecture: A Craftsman's Guide to Software Structure and Design. Prentice Hall. Principes d'architecture découplée et de séparation des responsabilités.",
        space_after=4)
    add_paragraph(doc,
        "[3] Fowler, M. (2002). Patterns of Enterprise Application Architecture. Addison-Wesley. Modélisation ORM, patterns de domaine et persistance relationnelle.",
        space_after=4)
    add_paragraph(doc,
        "[4] Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). Design Patterns: Elements of Reusable Object-Oriented Software. Addison-Wesley.",
        space_after=8)

    add_heading_2(doc, "Documentations Techniques et Références Web")
    add_paragraph(doc,
        "[5] Documentation officielle de FastAPI : https://fastapi.tiangolo.com/ — Architecture asynchrone, injection de dépendances et intégration OpenAPI.",
        space_after=4)
    add_paragraph(doc,
        "[6] Documentation officielle de React 18 : https://react.dev/ — Single Page Applications, Virtual DOM, hooks d'état et Context API.",
        space_after=4)
    add_paragraph(doc,
        "[7] Documentation officielle de PostgreSQL : https://www.postgresql.org/docs/ — Gestion des contraintes relationnelles, transactions ACID et format JSONB.",
        space_after=4)
    add_paragraph(doc,
        "[8] Documentation de l'API Google Gemini : https://ai.google.dev/ — Intégration de modèles de langage, prompts structurés et function calling.",
        space_after=4)
    add_paragraph(doc,
        "[9] Documentation officielle de l'API Brevo : https://developers.brevo.com/ — Intégration d'emails transactionnels RESTful.",
        space_after=4)
    add_paragraph(doc,
        "[10] Guide de sécurité OWASP (Open Web Application Security Project) : https://owasp.org/www-project-top-ten/ — Recommandations de sécurité web, protection contre les injections, XSS, CSRF et failles d'authentification.",
        space_after=4)
    add_paragraph(doc,
        "[11] Documentation de python-docx : https://python-docx.readthedocs.io/ — Manipulation programmée et génération de documents Microsoft Word conformes OOXML.",
        space_after=8)

    doc.add_page_break()

    # =========================================================================
    # ANNEXES
    # =========================================================================
    add_heading_1(doc, "ANNEXES")

    add_heading_2(doc, "Annexe A : Matrice des Principaux Endpoints de l'API REST")
    add_paragraph(doc, "Le Tableau 8 recense les principaux points d'entrée de l'API REST développée sous FastAPI :", space_after=6)

    api_data = [
        ("POST", "/api/auth/login", "Public", "Authentification utilisateur, émission Access Token & Refresh Token"),
        ("POST", "/api/auth/refresh", "Public", "Renouvellement transparent de l'Access Token via Refresh Token"),
        ("POST", "/api/auth/logout", "Authentifié", "Révocation de la session courante et invalidation des tokens"),
        ("GET", "/api/employes", "Admin / RH", "Liste paginée des employés avec recherche multicritères"),
        ("POST", "/api/employes", "Admin / RH", "Création d'une nouvelle fiche collaborateur"),
        ("PUT", "/api/employes/{id}", "Admin / RH", "Mise à jour des informations administratives d'un employé"),
        ("GET", "/api/contrats", "Admin / RH", "Liste de l'ensemble des contrats de travail avec filtres de statut"),
        ("POST", "/api/contrats", "Admin / RH", "Création et assemblage d'un contrat (sélection articles)"),
        ("PUT", "/api/contrats/{id}/statut", "Admin / RH", "Transition contrôlée du statut d'un contrat (machine à états)"),
        ("GET", "/api/contrats/{id}/docx", "Admin / RH", "Génération automatique et téléchargement du contrat Word"),
        ("GET", "/api/articles", "Admin / RH", "Consultation de la bibliothèque des clauses contractuelles"),
        ("POST", "/api/articles", "Admin / RH", "Ajout d'un nouvel article (texte standard ou tableau structuré)"),
        ("POST", "/api/ai/articles/generate-structured", "Admin / RH", "Génération assistée de clause via Google Gemini"),
        ("GET", "/api/notifications", "Admin / RH", "Consultation des alertes RH d'échéance CDD dédupliquées"),
        ("GET", "/api/audit", "Admin / RH", "Consultation et filtrage du journal d'audit immuable"),
        ("GET", "/api/espace-employe/mon-contrat", "Employé", "Consultation en lecture seule du contrat actif du salarié"),
        ("GET", "/api/espace-employe/mon-contrat/docx", "Employé", "Téléchargement par l'employé de son document contractuel")
    ]
    add_styled_table(doc, ["Méthode", "Endpoint REST", "Accès RBAC", "Rôle & Description de l'Opération"], api_data, col_widths=[0.8, 2.3, 1.0, 2.7])

    add_heading_2(doc, "Annexe B : Variables d'Environnement et Configuration")
    add_paragraph(doc,
        "La configuration de l'application est externalisée selon le standard des Twelve-Factor Apps via un fichier .env sécurisé :",
        space_after=4)
    add_bullet(doc, "postgresql://user:password@localhost:5432/gestion_rh_db (Chaîne de connexion SQLAlchemy).", "DATABASE_URL")
    add_bullet(doc, "Clé secrète de 256 bits pour la signature cryptographique des jetons JWT.", "SECRET_KEY")
    add_bullet(doc, "HS256 (Algorithme de signature symétrique).", "ALGORITHM")
    add_bullet(doc, "30 minutes pour l'Access Token et 7 jours pour le Refresh Token.", "ACCESS_TOKEN_EXPIRE_MINUTES")
    add_bullet(doc, "Clé d'authentification API pour le service d'Intelligence Artificielle Google Gemini.", "GEMINI_API_KEY")
    add_bullet(doc, "Clé d'accès à l'API transactionnelle Brevo pour l'acheminement des notifications par email.", "BREVO_API_KEY")
    add_bullet(doc, "Adresse d'expédition officielle pour les emails RH (ex: rh@csidigital.com).", "MAIL_FROM")

    sp_end = doc.add_paragraph()
    sp_end.paragraph_format.space_before = Pt(14)
    p_fin = doc.add_paragraph()
    p_fin.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_fin = p_fin.add_run("— FIN DU DOCUMENT —")
    r_fin.font.name = "Calibri"
    r_fin.font.bold = True
    r_fin.font.size = Pt(10)
    r_fin.font.color.rgb = COLOR_MUTED

print("Chapters 5, 6, Conclusion, Bibliography and Annexes generated successfully.")
