# -*- coding: utf-8 -*-
"""
Script Principal d'Assemblage du Rapport de Stage
Auteur : Sahli Yakine Eddine
Encadrante : Mme Kharbech Rayen
Établissement : ESPRIT
Entreprise : CSI Digital
Sujet : "Conception et développement d'une application web RH permettant de gérer les employés et les contrats de travail."
Fichier de sortie : Rapport_de_Stage_Sahli_Yakine_Eddine_CSI_Digital.docx
"""

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from build_report_full import (
    BASE_DIR, ASSETS_DIR, OUTPUT_PATH,
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TEXT, COLOR_MUTED,
    add_page_number, add_total_pages
)
from report_sections_front import build_front_matter
from report_sections_ch1_ch2 import build_chapter_1, build_chapter_2
from report_sections_ch3_ch4 import build_chapter_3, build_chapter_4
from report_sections_ch5_ch6 import build_chapter_5, build_chapter_6

def assemble_report():
    print("=" * 70)
    print("INITIALISATION DE L'ASSEMBLAGE DU RAPPORT DE STAGE")
    print("Auteur : Sahli Yakine Eddine")
    print("Encadrante : Mme Kharbech Rayen")
    print("Établissement : ESPRIT | Entreprise : CSI Digital")
    print("=" * 70)

    doc = docx.Document()

    # Configuration des marges A4 (2.4 cm = 0.95 in)
    for section in doc.sections:
        section.top_margin = Inches(0.9)
        section.bottom_margin = Inches(0.9)
        section.left_margin = Inches(0.95)
        section.right_margin = Inches(0.95)
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.different_first_page_header_footer = True

        # En-tête courant (pages 2+)
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("Rapport de Stage — Sahli Yakine Eddine | ESPRIT — CSI Digital")
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = COLOR_MUTED
        hrun.font.name = "Calibri"

        # Pied de page courant (pages 2+)
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        frun1 = fp.add_run("Application Web RH & Contrats de Travail       |       Page ")
        frun1.font.size = Pt(8.5)
        frun1.font.color.rgb = COLOR_MUTED
        frun1.font.name = "Calibri"
        
        prun = fp.add_run()
        prun.font.size = Pt(8.5)
        prun.font.bold = True
        prun.font.color.rgb = COLOR_PRIMARY
        add_page_number(prun)

        frun2 = fp.add_run(" / ")
        frun2.font.size = Pt(8.5)
        frun2.font.color.rgb = COLOR_MUTED
        
        nrun = fp.add_run()
        nrun.font.size = Pt(8.5)
        nrun.font.color.rgb = COLOR_MUTED
        add_total_pages(nrun)

    # Style par défaut du document
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Calibri'
    style_normal.font.size = Pt(10)
    style_normal.font.color.rgb = COLOR_TEXT
    style_normal.paragraph_format.line_spacing = 1.15
    style_normal.paragraph_format.space_after = Pt(4)

    # 1. Front Matter (Page de garde, Remerciements, Résumé, Abstract, Sommaire, Listes, Intro)
    print("1/4 Construction du Front Matter (Page de garde, Remerciements, Résumé, Sommaire, Listes, Intro)...")
    build_front_matter(doc)

    # 2. Chapitres 1 & 2 (Contexte, Analyse et Besoins)
    print("2/4 Construction des Chapitres 1 & 2 (Contexte général, Analyse et Spécification des Besoins)...")
    build_chapter_1(doc)
    build_chapter_2(doc)

    # 3. Chapitres 3 & 4 (Conception, Architecture, Réalisation)
    print("3/4 Construction des Chapitres 3 & 4 (Conception, Architecture 3-Tiers, Modélisations UML, Réalisation)...")
    build_chapter_3(doc)
    build_chapter_4(doc)

    # 4. Chapitres 5 & 6, Conclusion, Bibliographie et Annexes
    print("4/4 Construction des Chapitres 5 & 6 (Tests et Validation, Bilan, Conclusion, Bibliographie, Annexes)...")
    build_chapter_5(doc)
    build_chapter_6(doc)

    # Sauvegarde du document Word
    doc.save(OUTPUT_PATH)
    print(f"\nDOCUMENT CRÉÉ AVEC SUCCÈS : {OUTPUT_PATH}")
    print(f"Taille du fichier : {os.path.getsize(OUTPUT_PATH) / 1024:.1f} Ko")

if __name__ == "__main__":
    assemble_report()
