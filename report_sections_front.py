# -*- coding: utf-8 -*-
"""
Front Matter : Page de Garde, Remerciements, Résumé, Abstract, Table des Matières, Listes, Intro Générale
"""

import os
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from build_report_full import (
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TEXT, COLOR_MUTED, COLOR_ACCENT,
    HEX_PRIMARY, HEX_SECONDARY, HEX_LIGHT_BG, HEX_ZEBRA, HEX_BORDER,
    set_cell_background, set_cell_margins, set_cell_borders,
    add_heading_1, add_heading_2, add_heading_3, add_paragraph, add_bullet,
    add_callout, add_styled_table, add_figure, ASSETS_DIR
)

def build_front_matter(doc):
    # =========================================================================
    # 1. PAGE DE GARDE PROFESSIONNELLE
    # =========================================================================
    
    # Table d'en-tête pour les logos (ESPRIT à gauche, CSI Digital à droite)
    logo_table = doc.add_table(rows=1, cols=2)
    logo_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    logo_table.autofit = False
    
    cell_esprit = logo_table.cell(0, 0)
    cell_esprit.width = Inches(3.2)
    set_cell_margins(cell_esprit, top=50, bottom=50, left=50, right=50)
    p_esp = cell_esprit.paragraphs[0]
    p_esp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    esprit_logo_path = os.path.join(ASSETS_DIR, "logo_esprit.png")
    if os.path.exists(esprit_logo_path):
        r_esp = p_esp.add_run()
        r_esp.add_picture(esprit_logo_path, width=Inches(1.8))
    else:
        set_cell_borders(cell_esprit, top="single", bottom="single", left="single", right="single", color="A0AEC0", sz="6")
        set_cell_background(cell_esprit, "F7FAFC")
        r_esp_title = p_esp.add_run("ÉCOLE SUPÉRIEURE PRIVÉE\nD'INGÉNIERIE ET DE TECHNOLOGIE\n")
        r_esp_title.font.name = "Calibri"
        r_esp_title.font.bold = True
        r_esp_title.font.size = Pt(8.5)
        r_esp_title.font.color.rgb = COLOR_PRIMARY
        r_esp_box = p_esp.add_run("[ Emplacement Logo Officiel ESPRIT ]")
        r_esp_box.font.name = "Calibri"
        r_esp_box.font.italic = True
        r_esp_box.font.size = Pt(8)
        r_esp_box.font.color.rgb = COLOR_MUTED

    cell_csi = logo_table.cell(0, 1)
    cell_csi.width = Inches(3.2)
    set_cell_margins(cell_csi, top=50, bottom=50, left=50, right=50)
    p_csi = cell_csi.paragraphs[0]
    p_csi.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    csi_logo_path = os.path.join(ASSETS_DIR, "logo_csi_digital.png")
    if os.path.exists(csi_logo_path):
        r_csi = p_csi.add_run()
        r_csi.add_picture(csi_logo_path, width=Inches(1.8))
    else:
        r_csi = p_csi.add_run("CSI DIGITAL\nEntreprise d'Accueil")
        r_csi.font.name = "Calibri"
        r_csi.font.bold = True
        r_csi.font.size = Pt(11)
        r_csi.font.color.rgb = COLOR_PRIMARY

    # Espacement vertical
    sp1 = doc.add_paragraph()
    sp1.paragraph_format.space_before = Pt(30)
    sp1.paragraph_format.space_after = Pt(0)

    # Titre du diplôme / cadre académique
    p_type = doc.add_paragraph()
    p_type.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_type.paragraph_format.space_after = Pt(4)
    r_type = p_type.add_run("RAPPORT DE STAGE DE FIN D'ÉTUDES")
    r_type.font.name = "Calibri"
    r_type.font.size = Pt(13)
    r_type.font.bold = True
    r_type.font.color.rgb = COLOR_SECONDARY

    p_deg = doc.add_paragraph()
    p_deg.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_deg.paragraph_format.space_after = Pt(18)
    r_deg = p_deg.add_run("En vue de l'obtention du Diplôme National d'Ingénieur en Informatique")
    r_deg.font.name = "Calibri"
    r_deg.font.size = Pt(11)
    r_deg.font.italic = True
    r_deg.font.color.rgb = COLOR_MUTED

    # Cadre du sujet principal
    subj_table = doc.add_table(rows=1, cols=1)
    subj_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    subj_cell = subj_table.cell(0, 0)
    subj_cell.width = Inches(6.5)
    set_cell_background(subj_cell, HEX_LIGHT_BG)
    set_cell_margins(subj_cell, top=140, bottom=140, left=180, right=180)
    set_cell_borders(subj_cell, left="single", color=HEX_PRIMARY, sz="36") # 4.5 pt navy bar

    p_sub_label = subj_cell.paragraphs[0]
    p_sub_label.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_sub_label.paragraph_format.space_after = Pt(2)
    r_sub_label = p_sub_label.add_run("SUJET DU STAGE :")
    r_sub_label.font.name = "Calibri"
    r_sub_label.font.bold = True
    r_sub_label.font.size = Pt(10)
    r_sub_label.font.color.rgb = COLOR_PRIMARY

    p_sub_title = subj_cell.add_paragraph()
    p_sub_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_sub_title.paragraph_format.line_spacing = 1.2
    p_sub_title.paragraph_format.space_after = Pt(0)
    r_sub_title = p_sub_title.add_run("« Conception et développement d'une application web RH permettant de gérer les employés et les contrats de travail »")
    r_sub_title.font.name = "Calibri"
    r_sub_title.font.bold = True
    r_sub_title.font.size = Pt(14)
    r_sub_title.font.color.rgb = COLOR_PRIMARY

    sp2 = doc.add_paragraph()
    sp2.paragraph_format.space_before = Pt(35)
    sp2.paragraph_format.space_after = Pt(0)

    # Encadré des acteurs (Étudiant & Encadrante)
    info_table = doc.add_table(rows=1, cols=2)
    info_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    info_table.autofit = False

    cell_author = info_table.cell(0, 0)
    cell_author.width = Inches(3.2)
    set_cell_margins(cell_author, top=80, bottom=80, left=80, right=80)
    p_auth = cell_author.paragraphs[0]
    p_auth.paragraph_format.line_spacing = 1.15
    p_auth.paragraph_format.space_after = Pt(0)
    r_auth_lbl = p_auth.add_run("Réalisé par :\n")
    r_auth_lbl.font.bold = True
    r_auth_lbl.font.size = Pt(10)
    r_auth_lbl.font.color.rgb = COLOR_MUTED
    r_auth_name = p_auth.add_run("Sahli Yakine Eddine\n")
    r_auth_name.font.bold = True
    r_auth_name.font.size = Pt(12)
    r_auth_name.font.color.rgb = COLOR_PRIMARY
    r_auth_sub = p_auth.add_run("Élève Ingénieur — ESPRIT")
    r_auth_sub.font.size = Pt(9.5)
    r_auth_sub.font.color.rgb = COLOR_TEXT

    cell_sup = info_table.cell(0, 1)
    cell_sup.width = Inches(3.2)
    set_cell_margins(cell_sup, top=80, bottom=80, left=80, right=80)
    p_sup = cell_sup.paragraphs[0]
    p_sup.paragraph_format.line_spacing = 1.15
    p_sup.paragraph_format.space_after = Pt(0)
    r_sup_lbl = p_sup.add_run("Encadré par :\n")
    r_sup_lbl.font.bold = True
    r_sup_lbl.font.size = Pt(10)
    r_sup_lbl.font.color.rgb = COLOR_MUTED
    r_sup_name = p_sup.add_run("Mme Kharbech Rayen\n")
    r_sup_name.font.bold = True
    r_sup_name.font.size = Pt(12)
    r_sup_name.font.color.rgb = COLOR_PRIMARY
    r_sup_sub = p_sup.add_run("Encadrante Entreprise — CSI Digital")
    r_sup_sub.font.size = Pt(9.5)
    r_sup_sub.font.color.rgb = COLOR_TEXT

    # Bas de page de garde (Institutions et Année)
    sp3 = doc.add_paragraph()
    sp3.paragraph_format.space_before = Pt(45)
    sp3.paragraph_format.space_after = Pt(0)

    p_footer_cov = doc.add_paragraph()
    p_footer_cov.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_footer_cov.paragraph_format.line_spacing = 1.2
    p_footer_cov.paragraph_format.space_after = Pt(0)
    
    r_inst = p_footer_cov.add_run("École Supérieure Privée d'Ingénierie et de Technologie (ESPRIT)\n")
    r_inst.font.bold = True
    r_inst.font.size = Pt(10)
    r_inst.font.color.rgb = COLOR_PRIMARY

    r_host = p_footer_cov.add_run("Entreprise d'accueil : CSI Digital\n")
    r_host.font.size = Pt(9.5)
    r_host.font.color.rgb = COLOR_TEXT

    r_year = p_footer_cov.add_run("Année Universitaire : 2025 – 2026")
    r_year.font.bold = True
    r_year.font.size = Pt(10)
    r_year.font.color.rgb = COLOR_SECONDARY

    doc.add_page_break()

    # =========================================================================
    # 2. REMERCIEMENTS
    # =========================================================================
    add_heading_1(doc, "REMERCIEMENTS")
    
    add_paragraph(doc, 
        "Au terme de ce projet de fin d'études, je tiens à exprimer ma profonde gratitude et mes sincères remerciements à toutes les personnes qui ont contribué, de près ou de loin, à l'aboutissement de ce travail d'ingénierie.",
        space_after=8)

    add_paragraph(doc,
        "Je tiens tout d'abord à adresser mes remerciements les plus chaleureux et les plus respectueux à mon encadrante professionnelle chez CSI Digital, ",
        bold_prefix="À Mme Kharbech Rayen :", space_after=6)
    add_paragraph(doc,
        "pour sa confiance constante, ses précieux conseils techniques et méthodologiques, sa disponibilité sans faille et son sens aigu du détail. Ses orientations éclairées tout au long des cycles de développement m'ont permis de surmonter les défis fonctionnels et d'élever l'application aux standards d'excellence exigés en environnement d'entreprise.",
        italic=True, space_after=8)

    add_paragraph(doc,
        "J'exprime également ma sincère reconnaissance à l'ensemble de la direction et des équipes de ",
        bold_prefix="À la société CSI Digital :", space_after=6)
    add_paragraph(doc,
        "pour la qualité de l'accueil qui m'a été réservé durant mon stage. Évoluer au sein d'une structure dynamique, innovante et à taille humaine a constitué une expérience professionnelle extrêmement enrichissante sur les plans technique, organisationnel et relationnel.",
        italic=True, space_after=8)

    add_paragraph(doc,
        "Mes vifs remerciements s'adressent également au corps professoral et à l'équipe pédagogique de ",
        bold_prefix="À l'équipe pédagogique d'ESPRIT :", space_after=6)
    add_paragraph(doc,
        "qui ont assuré avec rigueur et dévouement ma formation d'ingénieur. La solidité des bases théoriques et pratiques dispensées au sein de notre école a été un atout déterminant pour concevoir et mener à bien une solution logicielle complète et robuste.",
        italic=True, space_after=8)

    add_paragraph(doc,
        "J'adresse enfin mes plus tendres pensées et ma reconnaissance éternelle à mes parents, à ma famille et à mes proches pour leurs encouragements continus, leur soutien indéfectible et les sacrifices consentis tout au long de mon parcours académique.",
        space_after=14)

    # Signature alignée à droite
    p_sig = doc.add_paragraph()
    p_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_sig = p_sig.add_run("Sahli Yakine Eddine")
    r_sig.font.name = "Calibri"
    r_sig.font.bold = True
    r_sig.font.size = Pt(11)
    r_sig.font.color.rgb = COLOR_PRIMARY

    doc.add_page_break()

    # =========================================================================
    # 3. RÉSUMÉ & ABSTRACT
    # =========================================================================
    add_heading_1(doc, "RÉSUMÉ")
    add_paragraph(doc,
        "La gestion administrative des ressources humaines et le cycle d'élaboration des contrats de travail constituent des processus stratégiques mais fréquemment pénalisés par des méthodes traditionnelles disparates (fichiers tableurs non synchronisés, documents textuels non structurés et suivi manuel des échéances). Ce projet, mené au sein de l'entreprise CSI Digital, a pour objectif la conception et le développement d'une application web RH globale, moderne et sécurisée, dédiée à la gestion centralisée des collaborateurs et à l'automatisation contractuelle.",
        space_after=6)
    add_paragraph(doc,
        "L'application repose sur une architecture modulaire trois-tiers intégrant un backend asynchrone haute performance conçu avec FastAPI (Python) et un frontend réactif et ergonomique sous React 18. Le cœur fonctionnel du système s'articule autour d'une bibliothèque d'articles contractuels modulaires et réutilisables, enrichie d'un Assistant d'Intelligence Artificielle générative exploitant l'API Google Gemini pour assister le responsable RH dans la rédaction et la structuration de clauses complexes (y compris sous forme de tableaux natifs de rémunération). L'application implémente un workflow rigoureux de statuts de contrats (Brouillon, Communiqué, Signé, Actif, Fin CDD, Démission CDI, Pas discuté, Inactif), un moteur d'alertes préventives dédupliquées pour les échéances de fin de CDD à 30, 15 et 7 jours, l'envoi d'emails transactionnels via l'API Brevo, la traçabilité intégrale des opérations via un journal d'audit granulaire (AuditLog), ainsi qu'un espace collaborateur en libre-service restreint.",
        space_after=6)
    add_paragraph(doc,
        "L'application a été rigoureusement validée par une suite de 78 tests automatisés (Pytest / Unittest) couvrant la sécurité, la logique métier et la robustesse des intégrations.",
        space_after=8)
    
    add_paragraph(doc,
        "Gestion RH, Contrats de travail, FastAPI, Python, React 18, PostgreSQL, Intelligence Artificielle, Google Gemini, Bibliothèque de clauses, Génération DOCX, Brevo API, Audit Logs, Sécurité JWT.",
        bold_prefix="Mots-clés :", space_after=18, italic=True)

    add_heading_1(doc, "ABSTRACT")
    add_paragraph(doc,
        "Human Resources administrative management and the employment contract lifecycle represent critical operational processes that are often hindered by fragmented traditional methods, such as unsynchronized spreadsheets, unstandardized word documents, and manual deadline tracking. This graduation project, carried out at CSI Digital, aims to design and develop a comprehensive, state-of-the-art, and secure HR web application dedicated to centralized employee records and automated contract management.",
        space_after=6)
    add_paragraph(doc,
        "The software is built upon a decoupled three-tier architecture featuring a high-performance asynchronous backend powered by FastAPI (Python) and an interactive, responsive Single Page Application implemented with React 18. The functional core is centered on a reusable modular library of contract clauses, enhanced by an AI Drafting Assistant utilizing Google Gemini API to assist HR managers in generating and formatting specialized clauses, including native compensation tables. The platform establishes an end-to-end business state machine for employment contracts (Draft, Communicated, Signed, Active, Fixed-term End, Resignation, Undiscussed, Inactive), an automated notification engine preventing duplicates for fixed-term expirations at 30, 15, and 7 days, transactional email delivery via Brevo API, a comprehensive audit trail with change deltas, and a secure employee self-service portal.",
        space_after=6)
    add_paragraph(doc,
        "The system has been thoroughly validated through a test suite of 78 automated tests (Pytest / Unittest), achieving complete coverage of security controls, business constraints, and external integrations.",
        space_after=8)
    
    add_paragraph(doc,
        "HR Management, Employment Contracts, FastAPI, Python, React 18, PostgreSQL, Artificial Intelligence, Google Gemini, Clause Library, DOCX Generation, Brevo API, Audit Trail, JWT Security.",
        bold_prefix="Keywords :", space_after=12, italic=True)

    doc.add_page_break()

    # =========================================================================
    # 4. TABLE DES MATIÈRES DÉTAILLÉE
    # =========================================================================
    add_heading_1(doc, "TABLE DES MATIÈRES")
    
    toc_data = [
        ("REMERCIEMENTS", "2"),
        ("RÉSUMÉ & ABSTRACT", "3"),
        ("TABLE DES MATIÈRES", "4"),
        ("LISTE DES FIGURES", "5"),
        ("LISTE DES TABLEAUX", "6"),
        ("LISTE DES ABRÉVIATIONS", "6"),
        ("INTRODUCTION GÉNÉRALE", "7"),
        ("CHAPITRE 1 : CONTEXTE GÉNÉRAL DU PROJET", "9"),
        ("    1.1 Introduction", "9"),
        ("    1.2 Présentation de l'Entreprise d'Accueil (CSI Digital)", "9"),
        ("    1.3 Contexte et Cadre du Stage", "9"),
        ("    1.4 Problématique de la Gestion RH Traditionnelle", "10"),
        ("    1.5 Étude de l'Existant et Analyse Critique", "10"),
        ("    1.6 Solution Proposée", "10"),
        ("    1.7 Objectifs Globaux du Projet", "11"),
        ("    1.8 Méthodologie de Travail (Scrum / Agile)", "11"),
        ("    1.9 Conclusion du Chapitre", "11"),
        ("CHAPITRE 2 : ANALYSE ET SPÉCIFICATION DES BESOINS", "12"),
        ("    2.1 Introduction", "12"),
        ("    2.2 Identification des Acteurs du Système", "12"),
        ("    2.3 Spécification des Besoins Fonctionnels", "12"),
        ("    2.4 Spécification des Besoins Non Fonctionnels", "13"),
        ("    2.5 Règles de Gestion et Cohérence Métier", "14"),
        ("    2.6 Diagramme Global des Cas d'Utilisation", "14"),
        ("    2.7 Description des Cas d'Utilisation Principaux", "15"),
        ("    2.8 Conclusion du Chapitre", "15"),
        ("CHAPITRE 3 : CONCEPTION ET ARCHITECTURE TECHNIQUE", "16"),
        ("    3.1 Introduction", "16"),
        ("    3.2 Architecture Globale 3-Tiers du Système", "16"),
        ("    3.3 Architecture Détaillée du Backend FastAPI", "17"),
        ("    3.4 Architecture Détaillée du Frontend React", "17"),
        ("    3.5 Modélisation des Données et Diagramme de Classes UML", "18"),
        ("    3.6 Conception Dynamique et Diagrammes de Séquence", "19"),
        ("    3.7 Modélisation du Cycle de Vie des Contrats (Machine à États)", "20"),
        ("    3.8 Sécurité, Authentification et Contrôle d'Accès (RBAC)", "20"),
        ("    3.9 Justification des Choix Technologiques", "21"),
        ("    3.10 Conclusion du Chapitre", "21"),
        ("CHAPITRE 4 : RÉALISATION ET MISE EN ŒUVRE DE L'APPLICATION", "22"),
        ("    4.1 Introduction", "22"),
        ("    4.2 Environnement de Développement et Outillage", "22"),
        ("    4.3 Module d'Authentification et Gestion des Sessions", "22"),
        ("    4.4 Module de Gestion des Dossiers Collaborateurs", "23"),
        ("    4.5 Bibliothèque d'Articles Contractuels Réutilisables", "23"),
        ("    4.6 Assistant IA pour la Rédaction de Clauses Contractuelles", "24"),
        ("    4.7 Gestion des Contrats et Nouveaux Workflows de Statuts", "25"),
        ("    4.8 Moteur de Génération Automatique des Documents Word (.docx)", "26"),
        ("    4.9 Système de Traçabilité et Journal d'Audit (Audit Logs)", "26"),
        ("    4.10 Moteur d'Alertes RH et Notifications Dédupliquées", "27"),
        ("    4.11 Service Transactionnel d'Emails (API Brevo)", "27"),
        ("    4.12 Espace Dédié Collaborateur (Self-Service)", "27"),
        ("    4.13 Galerie Commentée des Interfaces Utilisateur", "28"),
        ("    4.14 Conclusion du Chapitre", "28"),
        ("CHAPITRE 5 : TESTS, VALIDATION ET ASSURANCE QUALITÉ", "29"),
        ("    5.1 Introduction", "29"),
        ("    5.2 Stratégie Globale de Test", "29"),
        ("    5.3 Tests Backend Automatisés (Pytest / Unittest - 78 tests)", "29"),
        ("    5.4 Tests des Transitions de Statuts et Cohérence des Contrats", "30"),
        ("    5.5 Tests du Moteur d'Alertes et Idempotence de la Déduplication", "30"),
        ("    5.6 Tests du Service IA et Fallback Structuré", "31"),
        ("    5.7 Tests de Sécurité et Résistance aux Attaques", "31"),
        ("    5.8 Tests d'Intégration Frontend et Validation Ergonomique", "31"),
        ("    5.9 Matrice Récapitulative et Taux de Réussite", "32"),
        ("    5.10 Difficultés Rencontrées et Solutions Techniques", "32"),
        ("    5.11 Conclusion du Chapitre", "32"),
        ("CHAPITRE 6 : BILAN, COMPÉTENCES ET PERSPECTIVES", "33"),
        ("    6.1 Bilan Global du Projet", "33"),
        ("    6.2 Compétences Techniques et Humaines Acquises", "33"),
        ("    6.3 Limites Actuelles de la Solution", "34"),
        ("    6.4 Perspectives d'Évolution et Travaux Futurs", "34"),
        ("    6.5 Conclusion du Chapitre", "34"),
        ("CONCLUSION GÉNÉRALE", "35"),
        ("BIBLIOGRAPHIE ET WEBOGRAPHIE", "35"),
        ("ANNEXES", "36")
    ]

    add_styled_table(doc, ["Section / Chapitre", "Page"], toc_data, col_widths=[5.5, 0.9])
    doc.add_page_break()

    # =========================================================================
    # 5. LISTE DES FIGURES & TABLEAUX & ABRÉVIATIONS
    # =========================================================================
    add_heading_1(doc, "LISTE DES FIGURES")
    figures_data = [
        ("Figure 1", "Diagramme Global des Cas d'Utilisation UML", "14"),
        ("Figure 2", "Architecture Globale 3-Tiers de l'Application RH", "16"),
        ("Figure 3", "Diagramme de Classes Métier UML et Schéma ORM", "18"),
        ("Figure 4", "Diagramme de Séquence : Authentification Sécurisée JWT", "19"),
        ("Figure 5", "Diagramme de Séquence : Rédaction de Clause via l'Assistant IA", "19"),
        ("Figure 6", "Machine à États & Cycle de Vie des Statuts de Contrats", "20"),
        ("Figure 7", "Interface de Connexion Sécurisée", "28"),
        ("Figure 8", "Tableau de Bord & Gestion des Collaborateurs", "28"),
        ("Figure 9", "Bibliothèque des Articles Contractuels Réutilisables", "28"),
        ("Figure 10", "Modale de Création d'un Nouvel Article Contractuel", "28"),
        ("Figure 11", "Assistant IA : Prompt et Configuration de la Clause", "28"),
        ("Figure 12", "Assistant IA : Rendu Structuré avec Tableau de Rémunération", "28"),
        ("Figure 13", "Gestion des Contrats de Travail avec Nouveaux Badges de Statuts", "28"),
        ("Figure 14", "Centre de Gestion des Alertes et Notifications RH", "28"),
        ("Figure 15", "Journal d'Audit Centralisé avec Historique et Filtres", "28"),
        ("Figure 16", "Espace Collaborateur Dédié (Consultation du Contrat Actif)", "28")
    ]
    add_styled_table(doc, ["Figure", "Titre de la Figure", "Page"], figures_data, col_widths=[1.1, 4.5, 0.8])

    add_heading_1(doc, "LISTE DES TABLEAUX")
    tables_data = [
        ("Tableau 1", "Objectifs Spécifiques du Projet RH", "11"),
        ("Tableau 2", "Spécification des Besoins Fonctionnels (BF-01 à BF-25)", "13"),
        ("Tableau 3", "Spécification des Besoins Non Fonctionnels", "13"),
        ("Tableau 4", "Nomenclature et Règles des Nouveaux Statuts de Contrats", "20"),
        ("Tableau 5", "Comparatif et Justification des Choix Technologiques", "21"),
        ("Tableau 6", "Synthèse de la Suite de Tests Backend Automatisés (78 tests)", "30"),
        ("Tableau 7", "Matrice de Couverture des Tests et Validation Fonctionnelle", "32"),
        ("Tableau 8", "Matrice des Principaux Endpoints de l'API REST", "36")
    ]
    add_styled_table(doc, ["Tableau", "Titre du Tableau", "Page"], tables_data, col_widths=[1.2, 4.4, 0.8])

    add_heading_1(doc, "LISTE DES ABRÉVIATIONS")
    abbrev_data = [
        ("API", "Application Programming Interface"),
        ("REST", "Representational State Transfer"),
        ("JWT", "JSON Web Token"),
        ("RBAC", "Role-Based Access Control"),
        ("CRUD", "Create, Read, Update, Delete"),
        ("ORM", "Object-Relational Mapping"),
        ("SQL", "Structured Query Language"),
        ("JSON", "JavaScript Object Notation"),
        ("JSONB", "Binary JSON (Format optimisé PostgreSQL)"),
        ("SPA", "Single Page Application"),
        ("UI / UX", "User Interface / User Experience"),
        ("IA / AI", "Intelligence Artificielle / Artificial Intelligence"),
        ("LLM", "Large Language Model"),
        ("CDI", "Contrat à Durée Indéterminée"),
        ("CDD", "Contrat à Durée Déterminée"),
        ("DOCX", "Document XML Microsoft Word"),
        ("SMTP", "Simple Mail Transfer Protocol"),
        ("CORS", "Cross-Origin Resource Sharing"),
        ("XSS", "Cross-Site Scripting"),
        ("CSRF", "Cross-Site Request Forgery"),
        ("ACID", "Atomicité, Cohérence, Isolation, Durabilité")
    ]
    add_styled_table(doc, ["Sigle", "Signification Détaillée"], abbrev_data, col_widths=[1.5, 4.9])

    doc.add_page_break()

    # =========================================================================
    # 6. INTRODUCTION GÉNÉRALE
    # =========================================================================
    add_heading_1(doc, "INTRODUCTION GÉNÉRALE")
    
    add_paragraph(doc,
        "La transformation numérique des processus d'entreprise constitue aujourd'hui un levier fondamental de performance et de compétitivité. Au cœur de cette dynamique, la gestion des ressources humaines (RH) a profondément évolué : autrefois cantonnée à des tâches purement administratives et d'archivage matériel, elle exige désormais une réactivité immédiate, une traçabilité rigoureuse et une conformité juridique sans faille.",
        space_after=6)

    add_paragraph(doc,
        "Parmi les missions les plus sensibles et récurrentes incombant aux directions des ressources humaines figure la gestion du cycle de vie contractuel des collaborateurs : de la création de la fiche employé à la rédaction individualisée du contrat de travail, en passant par le suivi rigoureux des périodes d'essai, des renouvellements, des échéances de CDD et des clôtures administratives. Dans de nombreuses organisations, cette gestion demeure encore aujourd'hui tributaire d'outils bureautiques non interconnectés (feuilles de calcul Excel, modèles de documents Word dupliqués manuellement, échanges de courriers électroniques non centralisés). Ces méthodes traditionnelles révèlent rapidement de sévères limites : multiplication des erreurs humaines de ressaisie, risque élevé d'incohérences juridiques, absence de visibilité en temps réel sur les échéances critiques et vulnérabilités manifestes en matière de sécurité et de confidentialité des données à caractère personnel.",
        space_after=6)

    add_paragraph(doc,
        "C'est dans ce contexte stimulant que s'inscrit le stage de fin d'études que j'ai réalisé au sein de la société CSI Digital. Le projet qui m'a été confié, intitulé « Conception et développement d'une application web RH permettant de gérer les employés et les contrats de travail », a pour vocation de concevoir et d'implémenter une solution web centralisée, pérenne, hautement ergonomique et sécurisée, répondant avec précision aux besoins réels de gestion des collaborateurs et de leurs engagements contractuels.",
        space_after=6)

    add_paragraph(doc,
        "Pour atteindre cet objectif avec un niveau de qualité industriel et académique élevé, l'application développée propose des innovations fonctionnelles et techniques majeures :",
        space_after=4)

    add_bullet(doc, "Centralisation intégrale des dossiers administratifs et historiques des employés avec contrôle d'accès basé sur les rôles (RBAC).", "Gestion Administrative")
    add_bullet(doc, "Mise en place d'un catalogue de clauses contractuelles personnalisables, assemblables dynamiquement lors de la création d'un contrat.", "Bibliothèque d'Articles")
    add_bullet(doc, "Intégration native d'un modèle d'Intelligence Artificielle générative (Google Gemini) pour assister le responsable RH dans la rédaction et la mise en forme de clauses juridiques complexes, y compris sous forme de tableaux structurés.", "Assistant IA Métier")
    add_bullet(doc, "Implémentation d'une machine à états finis garantissant des transitions de statuts rigoureuses (Brouillon, Communiqué, Signé, Actif, Fin CDD, Démission CDI, Pas discuté, Inactif) adaptées aux spécificités de chaque type de contrat.", "Cycle de Vie Contractuel")
    add_bullet(doc, "Automatisation de la génération des documents officiels Word (.docx), du moteur d'alertes d'expiration à 30, 15 et 7 jours avec déduplication, et de l'envoi d'emails transactionnels via l'API Brevo.", "Automatisation & Alertes")
    add_bullet(doc, "Mise à disposition d'une interface en libre-service sécurisée pour les employés, complétée par un journal d'audit granulaire consignant chaque action administrative.", "Portail Collaborateur & Audit")

    add_paragraph(doc,
        "Afin de rendre compte de l'ensemble de la démarche méthodologique, scientifique et technique menée durant ce stage, le présent rapport est structuré en six chapitres complémentaires :",
        space_after=4)

    add_bullet(doc, "situe le projet dans son contexte industriel chez CSI Digital, expose la problématique rencontrée, étudie l'existant et définit la méthodologie de gestion de projet adoptée.", "Le Chapitre 1 (Contexte Général du Projet)")
    add_bullet(doc, "détaille l'identification des acteurs, formalise les besoins fonctionnels et non fonctionnels, définit les règles de gestion et modélise les cas d'utilisation UML.", "Le Chapitre 2 (Analyse et Spécification des Besoins)")
    add_bullet(doc, "présente l'architecture logicielle globale 3-tiers, justifie les choix technologiques, et détaille les modélisations statiques et dynamiques (diagrammes de classes, de séquences et cycle de vie des statuts).", "Le Chapitre 3 (Conception et Architecture)")
    add_bullet(doc, "expose la réalisation concrète des différents modules de l'application, l'intégration de l'Assistant IA, le moteur d'alertes et présente une galerie d'interfaces commentées.", "Le Chapitre 4 (Réalisation de l'Application)")
    add_bullet(doc, "détaille la stratégie de qualification, expose les résultats des 78 tests automatisés, analyse la sécurité du système et présente les difficultés résolues.", "Le Chapitre 5 (Tests et Validation)")
    add_bullet(doc, "dresse le bilan des compétences acquises, souligne les limites du prototype actuel et ouvre des perspectives concrètes d'évolution future.", "Le Chapitre 6 (Bilan et Perspectives)")

    add_paragraph(doc,
        "Le document se clôture par une conclusion générale résumant les apports du projet, suivie des références bibliographiques et des annexes techniques.",
        space_after=8)

    doc.add_page_break()

print("Front matter generated successfully.")
