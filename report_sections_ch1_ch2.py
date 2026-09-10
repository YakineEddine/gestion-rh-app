# -*- coding: utf-8 -*-
"""
Chapitre 1 : Contexte Général du Projet
Chapitre 2 : Analyse et Spécification des Besoins
"""

from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from build_report_full import (
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TEXT, COLOR_MUTED, COLOR_ACCENT,
    add_heading_1, add_heading_2, add_heading_3, add_paragraph, add_bullet,
    add_callout, add_styled_table, add_figure
)

def build_chapter_1(doc):
    # =========================================================================
    # CHAPITRE 1 : CONTEXTE GÉNÉRAL DU PROJET
    # =========================================================================
    add_heading_1(doc, "CHAPITRE 1 : CONTEXTE GÉNÉRAL DU PROJET")

    add_heading_2(doc, "1.1 Introduction")
    add_paragraph(doc,
        "Ce premier chapitre pose les bases contextuelles et méthodologiques du projet. Il présente tout d'abord l'organisme d'accueil, CSI Digital, ainsi que le cadre général dans lequel s'est déroulé ce stage de fin d'études. Il expose ensuite de manière détaillée la problématique de la gestion manuelle des ressources humaines, analyse les limites des solutions existantes, formalise les objectifs assignés à la nouvelle application et décrit la démarche méthodologique agile adoptée pour mener à bien les développements.",
        space_after=8)

    add_heading_2(doc, "1.2 Présentation de l'Entreprise d'Accueil (CSI Digital)")
    add_paragraph(doc,
        "CSI Digital est une entreprise innovante spécialisée dans le conseil en technologies de l'information, l'ingénierie logicielle et l'accompagnement à la transformation digitale des organisations. Forte d'une équipe pluridisciplinaire d'ingénieurs et de consultants, l'entreprise conçoit des solutions logicielles sur mesure destinées à optimiser les processus métiers de ses clients dans des secteurs variés (finance, commerce, industrie, services et gestion administrative).",
        space_after=6)
    add_paragraph(doc,
        "Dans le cadre de sa croissance et du renforcement de ses opérations internes, CSI Digital accorde une priorité stratégique à l'excellence opérationnelle et à l'automatisation de ses propres flux de travail. C'est dans cette optique que s'inscrit la volonté de moderniser la gestion interne des ressources humaines et le suivi des contrats de travail de ses collaborateurs.",
        space_after=8)

    add_heading_2(doc, "1.3 Contexte et Cadre du Stage")
    add_paragraph(doc,
        "Le stage de fin d'études s'est déroulé sur une période de plusieurs mois au sein du département d'ingénierie logicielle de CSI Digital, sous la supervision attentive de Mme Kharbech Rayen. Ce projet s'inscrit dans le cadre de la validation du Diplôme National d'Ingénieur en Informatique de l'École Supérieure Privée d'Ingénierie et de Technologie (ESPRIT).",
        space_after=6)
    add_paragraph(doc,
        "Ce projet a offert une opportunité privilégiée de conjuguer rigueur académique (méthodes d'analyse, modélisation UML, génie logiciel) et exigences professionnelles concrètes (respect des délais, contraintes de sécurité en environnement d'entreprise, robustesse logicielle et intégration d'outils modernes tels que l'Intelligence Artificielle générative).",
        space_after=8)

    add_heading_2(doc, "1.4 Problématique de la Gestion RH Traditionnelle")
    add_paragraph(doc,
        "La gestion du capital humain et l'administration des contrats constituent l'épine dorsale de toute organisation. Cependant, de nombreuses entreprises s'appuient encore sur des méthodes artisanales reposant sur des fichiers tableurs (Excel), des modèles bureautiques Word dupliqués manuellement et des dossiers papier éparpillés. Ces pratiques génèrent une série d'écueils majeurs :",
        space_after=5)
    
    add_bullet(doc, "La saisie répétitive et non synchronisée des mêmes données (état civil, matricule, poste, dates, rémunération) sur plusieurs supports provoque de fréquents écarts et inexactitudes entre les dossiers administratifs et les contrats officiels.", "Redondance et erreurs de saisie")
    add_bullet(doc, "La rédaction de chaque contrat à partir d'anciens documents implique des opérations manuelles de copier-coller fastidieuses, chronophages et sources potentielles d'omissions de clauses indispensables.", "Perte de temps en rédaction")
    add_bullet(doc, "Le suivi manuel des dates d'échéance des CDD, des stages et des périodes d'essai s'avère particulièrement défaillant, entraînant parfois le dépassement involontaire de dates limites avec des conséquences juridiques préjudiciables.", "Absence de suivi proactif des échéances")
    add_bullet(doc, "L'absence d'un journal d'audit empêche de savoir qui a créé, modifié ou validé un contrat ou une fiche collaborateur, ce qui pose de graves problèmes de traçabilité interne.", "Manque de traçabilité des opérations")
    add_bullet(doc, "Les données des employés (coordonnées, salaires, contrats) circulent souvent par emails non chiffrés ou sont stockées sur des disques partagés sans contrôle d'accès granulaire, exposant l'entreprise à des risques de fuite de données.", "Vulnérabilités de sécurité et conformité")

    add_heading_2(doc, "1.5 Étude de l'Existant et Limites")
    add_paragraph(doc,
        "L'analyse des pratiques initiales au sein de l'organisation a révélé les limites structurelles suivantes :",
        space_after=4)
    add_bullet(doc, "Fichiers Excel multiples gérés par différentes personnes, créant des versions contradictoires (perte de la source unique de vérité).", "Silos d'informations")
    add_bullet(doc, "Clauses contractuelles rédigées ad-hoc sans bibliothèque standardisée ni réutilisation garantie.", "Hétérogénéité des contrats")
    add_bullet(doc, "Aucune notification automatique à l'approche de la fin d'un contrat CDD.", "Risque légal accru")
    add_bullet(doc, "Impossibilité pour l'employé de consulter en ligne et en temps réel son contrat actif et ses données personnelles.", "Expérience collaborateur inexistante")

    add_heading_2(doc, "1.6 Solution Proposée")
    add_paragraph(doc,
        "Pour surmonter définitivement ces écueils, nous avons proposé de concevoir une application web complète, centralisée et modulaire baptisée « Gestion RH & Contrats ». Cette solution apporte une réponse ciblée à chaque faiblesse constatée :",
        space_after=4)
    add_bullet(doc, "Une base de données relationnelle unique (PostgreSQL) centralisant l'ensemble des collaborateurs, des contrats et des paramètres administratifs.", "Source unique de vérité")
    add_bullet(doc, "Un catalogue structuré de clauses contractuelles réutilisables, activables et sélectionnables lors de la création d'un contrat.", "Bibliothèque d'articles modulaires")
    add_bullet(doc, "Un module d'assistance alimenté par Google Gemini permettant au responsable RH de générer en langage naturel des clauses conformes et structurées (incluant des grilles de salaire sous forme de tableaux natifs).", "Assistant IA Métier")
    add_bullet(doc, "Un moteur d'alerte programmable calculant automatiquement les fins de contrat CDD à 30, 15 et 7 jours, avec déduplication stricte et envoi d'emails transactionnels via Brevo.", "Alertes & Notifications automatiques")
    add_bullet(doc, "Un assemblage instantané des données de l'employé et des articles sélectionnés pour générer un document Word (.docx) prêt à l'impression et à la signature.", "Génération automatisée DOCX")
    add_bullet(doc, "Un contrôle d'accès strict basé sur les rôles (Admin RH vs Employé) et un portail collaborateur dédié en lecture seule.", "Sécurité et Espace Collaborateur")

    add_heading_2(doc, "1.7 Objectifs Globaux du Projet")
    add_paragraph(doc, "Les objectifs spécifiques assignés au projet sont synthétisés dans le Tableau 1 ci-dessous :", space_after=6)
    
    obj_data = [
        ("O1", "Centralisation des Données", "Regrouper toutes les informations des collaborateurs et des contrats dans un système d'information unique et hautement disponible."),
        ("O2", "Gestion Administrative Complète", "Fournir un module CRUD complet et ergonomique pour gérer les fiches employés avec recherche multi-critères et pagination."),
        ("O3", "Modularité Contractuelle", "Concevoir une bibliothèque d'articles réutilisables pouvant être combinés à la volée pour composer des contrats sur mesure."),
        ("O4", "Assistance Intelligente par IA", "Intégrer un modèle d'IA générative pour accélérer et fiabiliser la rédaction de clauses juridiques complexes."),
        ("O5", "Fiabilité du Cycle de Vie", "Mettre en œuvre une machine d'états rigoureuse pour les statuts de contrat (Brouillon, Communiqué, Signé, Actif, Fin CDD, Démission, Inactif)."),
        ("O6", "Sécurité et Auditabilité", "Assurer une sécurité renforcée (JWT, Bcrypt, anti-brute force) et journaliser chaque action administrative dans une table d'audit.")
    ]
    add_styled_table(doc, ["Réf.", "Objectif", "Description Détaillée"], obj_data, col_widths=[0.8, 2.3, 3.4])

    add_heading_2(doc, "1.8 Méthodologie de Travail (Scrum / Agile)")
    add_paragraph(doc,
        "Afin de garantir une flexibilité maximale, une livraison continue de valeur et une adaptation permanente aux retours de l'encadrante, nous avons adopté la méthodologie agile Scrum. Le projet a été découpé en cycles itératifs (Sprints) d'une durée de deux semaines chacun, rythmés par les cérémonies classiques :",
        space_after=4)
    add_bullet(doc, "Recueil initial des exigences, formalisation du backlog produit et priorisation des user stories.", "Sprint 0 (Cadrage & Conception)")
    add_bullet(doc, "Mise en place de l'environnement, conception de la base de données PostgreSQL, développement des APIs d'authentification JWT et de gestion des employés.", "Sprint 1 (Fondations & Employés)")
    add_bullet(doc, "Développement de la bibliothèque d'articles contractuels, intégration de l'Assistant IA Gemini et mise en place du générateur DOCX.", "Sprint 2 (Articles & Assistant IA)")
    add_bullet(doc, "Gestion des contrats, implémentation des statuts et transitions métiers, développement du moteur d'alertes d'expiration et intégration de l'API Brevo.", "Sprint 3 (Contrats, Alertes & Brevo)")
    add_bullet(doc, "Développement de l'espace collaborateur, journalisation d'audit, durcissement de la sécurité (lockout, refresh tokens) et suite de tests automatisés.", "Sprint 4 (Espace Employé & Sécurité)")
    add_bullet(doc, "Campagne globale de tests d'intégration, recette fonctionnelle finale, documentation technique et rédaction du présent rapport.", "Sprint 5 (Recette & Finalisation)")

    add_heading_2(doc, "1.9 Conclusion du Chapitre")
    add_paragraph(doc,
        "Ce premier chapitre a permis de contextualiser le projet au sein de CSI Digital, de mettre en lumière les vulnérabilités inhérentes aux processus RH manuels et d'énoncer les objectifs concrets de la solution développée. Le chapitre suivant est dédié à l'analyse fonctionnelle approfondie et à la spécification des besoins.",
        space_after=10)

    doc.add_page_break()

def build_chapter_2(doc):
    # =========================================================================
    # CHAPITRE 2 : ANALYSE ET SPÉCIFICATION DES BESOINS
    # =========================================================================
    add_heading_1(doc, "CHAPITRE 2 : ANALYSE ET SPÉCIFICATION DES BESOINS")

    add_heading_2(doc, "2.1 Introduction")
    add_paragraph(doc,
        "La réussite d'un projet logiciel repose sur une compréhension exhaustive et rigoureuse des exigences fonctionnelles et des contraintes techniques. Ce chapitre identifie les acteurs intervenant sur le système, détaille l'ensemble des besoins fonctionnels et non fonctionnels, explicite les règles de gestion métier gouvernant les contrats et modélise les interactions au travers des diagrammes de cas d'utilisation UML.",
        space_after=8)

    add_heading_2(doc, "2.2 Identification des Acteurs du Système")
    add_paragraph(doc, "Le système distingue deux acteurs humains principaux interagissant avec l'application :", space_after=4)
    
    add_paragraph(doc,
        "Il s'agit de l'utilisateur principal du système. Il dispose de privilèges complets d'administration lui permettant de gérer le personnel, d'alimenter la bibliothèque d'articles, d'utiliser l'Assistant IA pour rédiger de nouvelles clauses, de créer et modifier les contrats de travail, d'en suivre les statuts, de consulter les alertes d'expiration et de visualiser le journal d'audit de sécurité.",
        bold_prefix="1. L'Administrateur RH / Responsable RH :", space_after=6)
    
    add_paragraph(doc,
        "Il s'agit du salarié de l'entreprise. Disposant d'un compte individuel sécurisé, l'employé possède un accès strictement limité en lecture seule : il peut consulter ses informations personnelles, visualiser son contrat actuellement en vigueur et télécharger son document contractuel officiel.",
        bold_prefix="2. L'Employé / Collaborateur :", space_after=8)

    add_heading_2(doc, "2.3 Spécification des Besoins Fonctionnels")
    add_paragraph(doc, "Les exigences fonctionnelles du système sont classées par modules dans le Tableau 2 :", space_after=6)

    bf_data = [
        ("BF-01", "Connexion sécurisée", "Authentification par email et mot de passe avec hachage Bcrypt et émission d'un token JWT."),
        ("BF-02", "Gestion des rôles (RBAC)", "Distinction stricte entre le profil Administrateur RH et le profil Employé."),
        ("BF-03", "Politique anti-brute force", "Verrouillage temporaire du compte après 5 échecs consécutifs d'authentification."),
        ("BF-04", "Gestion des employés (CRUD)", "Création, modification, archivage, recherche multicritères et pagination des fiches employés."),
        ("BF-05", "Matricule unique", "Génération automatique et garantie d'unicité du matricule collaborateur."),
        ("BF-06", "Bibliothèque d'articles", "Gestion du catalogue de clauses contractuelles réutilisables (activation, modification)."),
        ("BF-07", "Assistant IA de rédaction", "Génération assistée de clauses par Google Gemini à partir d'un prompt en langage naturel."),
        ("BF-08", "Clauses structurées (Tableaux)", "Support des clauses complexes composées de texte brut ou de tableaux natifs de rémunération."),
        ("BF-09", "Création et assemblage de contrat", "Sélection d'un employé, saisie des dates/salaire et association des articles réutilisables."),
        ("BF-10", "Cycle de vie des statuts", "Gestion stricte des statuts : Brouillon, Communiqué, Signé, Actif, Fin CDD, Démission, Pas discuté, Inactif."),
        ("BF-11", "Cohérence des dates CDD/CDI", "Date de fin obligatoire pour les CDD, date de fin optionnelle/interdite à la création pour les CDI."),
        ("BF-12", "Génération Word (.docx)", "Assemblage dynamique et téléchargement du contrat pré-rempli au format Microsoft Word."),
        ("BF-13", "Moteur d'alertes d'expiration", "Détection automatique des contrats CDD arrivant à échéance à 30, 15 et 7 jours."),
        ("BF-14", "Déduplication des alertes", "Garantie d'absence de notifications en double grâce à une clé unique d'idempotence."),
        ("BF-15", "Envoi d'emails transactionnels", "Notification par email via l'API Brevo lors de l'activation d'un contrat ou à l'approche de son terme."),
        ("BF-16", "Journal d'audit de sécurité", "Traçabilité intégrale de toutes les actions (anciennes et nouvelles valeurs au format JSONB)."),
        ("BF-17", "Espace personnel collaborateur", "Interface restreinte permettant à l'employé de consulter son profil et son contrat actif.")
    ]
    add_styled_table(doc, ["Code", "Besoin Fonctionnel", "Description Détaillée"], bf_data, col_widths=[0.9, 2.3, 3.3])

    add_heading_2(doc, "2.4 Spécification des Besoins Non Fonctionnels")
    add_paragraph(doc, "Les exigences non fonctionnelles garantissent la pérennité, la sécurité et la performance de l'application :", space_after=6)

    bnf_data = [
        ("BNF-01", "Performance & Réactivité", "Temps de réponse inférieur à 200 ms pour les requêtes de base de données courantes et inférieur à 3 secondes pour la génération de clauses complexes via l'IA."),
        ("BNF-02", "Sécurité & Confidentialité", "Protection contre les failles OWASP Top 10 (injections SQL prévenues par l'ORM SQLAlchemy, attaques XSS prévenues par l'échappement React, protection CORS et tokens JWT signés numériquement)."),
        ("BNF-03", "Ergonomie & Design Moderne", "Interface intuitive et réactive respectant les principes d'utilisabilité contemporains, avec design épuré, contraste soigné et retours visuels interactifs."),
        ("BNF-04", "Intégrité des Données (ACID)", "Garantie de cohérence transactionnelle assurée par le moteur relationnel PostgreSQL et ses contraintes de clés étrangères en cascade."),
        ("BNF-05", "Maintenabilité & Modularité", "Architecture logicielle découplée favorisant l'évolutivité du code, le typage strict des données (Pydantic) et la couverture par tests unitaires automatisés.")
    ]
    add_styled_table(doc, ["Code", "Caractéristique", "Exigence et Justification Technique"], bnf_data, col_widths=[1.0, 2.2, 3.3])

    add_heading_2(doc, "2.5 Règles de Gestion et Cohérence Métier")
    add_paragraph(doc,
        "La gestion contractuelle est soumise à un ensemble de règles métier strictes régissant la validité des données et des transitions :",
        space_after=4)
    add_bullet(doc, "Un contrat CDD, STAGE ou ALTERNANCE doit impérativement comporter une date de début et une date de fin (date_fin postérieure à date_debut).", "Règle 1 (CDD et Dates)")
    add_bullet(doc, "Un contrat CDI ne doit pas comporter de date de fin obligatoire lors de son émission.", "Règle 2 (CDI et Échéance)")
    add_bullet(doc, "Un contrat nouvellement rédigé débute à l'état BROUILLON. Il peut ensuite être COMMUNIQUÉ, puis SIGNÉ, avant de devenir ACTIF.", "Règle 3 (Workflow d'Activation)")
    add_bullet(doc, "Un contrat ACTIF ne peut en aucun cas régresser vers le statut BROUILLON. La fin d'un CDD passe par FIN_CDD avant archivage en INACTIF. La rupture d'un CDI passe par DEMISSION_CDI avant archivage en INACTIF.", "Règle 4 (Transitions Irréversibles)")
    add_bullet(doc, "Un contrat au statut INACTIF est considéré comme clôturé et archivé : il ne génère aucune alerte d'expiration et n'apparaît plus comme le contrat actif du collaborateur.", "Règle 5 (Archivage Inactif)")

    add_callout(doc, 
        "Les règles de cohérence ci-dessus sont validées à deux niveaux : côté client par des mécanismes de contrôle dans les formulaires React, et côté serveur de manière infranchissable au sein des schémas Pydantic et des services métier FastAPI.",
        title="Validation à double niveau")

    add_heading_2(doc, "2.6 Diagramme Global des Cas d'Utilisation")
    add_paragraph(doc,
        "Le diagramme de cas d'utilisation UML ci-dessous (Figure 1) offre une vue synthétique des interactions entre les acteurs et les fonctionnalités offertes par l'application RH :",
        space_after=6)
    
    add_figure(doc, "fig_use_case.png", "Figure 1 — Diagramme Global des Cas d'Utilisation UML", width=5.6)

    add_heading_2(doc, "2.7 Description des Cas d'Utilisation Principaux")
    add_paragraph(doc,
        "Afin d'illustrer la dynamique fonctionnelle, deux cas d'utilisation majeurs sont détaillés textuellement :",
        space_after=4)

    add_paragraph(doc,
        "L'administrateur RH accède au formulaire de création, sélectionne un employé non rattaché à un contrat actif, choisit le type de contrat (CDD/CDI) et saisit la rémunération ainsi que les dates légales. Il sélectionne ensuite les clauses applicables depuis la bibliothèque d'articles. Lors de la soumission, le contrat est enregistré à l'état BROUILLON et un événement d'audit est consigné.",
        bold_prefix="• Cas d'utilisation « Créer un contrat de travail » :", space_after=6)

    add_paragraph(doc,
        "Depuis l'interface de gestion de la bibliothèque d'articles, le responsable RH ouvre la modale d'assistance et décrit en français la clause souhaitée (ex: 'Rédige une clause de prime sur objectifs avec un tableau trimestriel'). L'IA Gemini traite la requête et retourne une structure JSON validée comprenant un texte introductif et un tableau formaté. Le responsable RH visualise le résultat en direct, procède à d'éventuels ajustements, puis enregistre l'article dans la bibliothèque.",
        bold_prefix="• Cas d'utilisation « Rédiger une clause via l'Assistant IA » :", space_after=8)

    add_heading_2(doc, "2.8 Conclusion du Chapitre")
    add_paragraph(doc,
        "Ce chapitre a permis de formaliser l'ensemble des besoins et des règles encadrant l'application web RH. Sur la base de ces exigences précises, le chapitre suivant présente la conception architecturale et la modélisation technique de la solution.",
        space_after=10)

    doc.add_page_break()

print("Chapters 1 and 2 generated successfully.")
