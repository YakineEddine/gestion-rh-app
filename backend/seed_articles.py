import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "gestion_rh_db")

articles_to_seed = [
    {
        "code": "ART-001",
        "titre": "Obligation de discrétion et de confidentialité",
        "contenu": "L'employé s'engage à observer la discrétion la plus absolue professionnelle sur toutes les informations, procédés, designs, données financières ou secrets d'affaires dont il pourrait avoir connaissance dans l'exercice de ses fonctions au sein de l'entreprise."
    },
    {
        "code": "ART-002",
        "titre": "Période d'essai",
        "contenu": "Le présent contrat n'deviendra définitif qu'à l'issue d'une période d'essai de 3 mois. Durant cette période, chacune des parties pourra rompre le contrat à tout moment, sans indemnité, sous réserve du respect du délai de prévenance légal en vigueur."
    },
    {
        "code": "ART-003",
        "titre": "Clause de non-concurrence",
        "contenu": "Compte tenu des fonctions sensibles de l'employé et de son accès aux clients et savoir-faire clés, il lui est interdit, en cas de rupture du contrat, de s'engager ou de collaborer directement ou indirectement avec une entreprise concurrente directe sur le territoire national pendant une durée de 1 an."
    },
    {
        "code": "ART-004",
        "titre": "Propriété intellectuelle",
        "contenu": "Tous les logiciels, codes sources, documentations, designs ou travaux réalisés par l'employé dans le cadre ou à l'occasion de ses fonctions professionnelles sont la propriété exclusive et entière de l'entreprise, qui détient la totalité des droits patrimoniaux associés."
    },
    {
        "code": "ART-005",
        "titre": "Durée de travail et horaires",
        "contenu": "L'employé effectuera ses fonctions selon la durée légale ou réglementaire de travail applicable au sein de l'entreprise, soit 40 heures par semaine, réparties conformément aux horaires de présence collective du département d'affectation."
    },
    {
        "code": "ART-006",
        "titre": "Rémunération et avantages",
        "contenu": "En contrepartie de l'accomplissement de ses obligations professionnelles, l'employé percevra une rémunération mensuelle fixe brute telle que stipulée dans ses conditions particulières de recrutement, versée en fin de chaque mois civil."
    }
]

try:
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cursor = conn.cursor()

    # Vider la table pour eviter les doublons et repartir a neuf
    print("Nettoyage de la table articles...")
    cursor.execute("TRUNCATE TABLE articles RESTART IDENTITY CASCADE;")

    inserted_count = 0
    for art in articles_to_seed:
        cursor.execute("""
            INSERT INTO articles (code, titre, contenu_par_defaut, est_actif)
            VALUES (%s, %s, %s, %s)
        """, (art["code"], art["titre"], art["contenu"], True))
        inserted_count += 1

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Succes : {inserted_count} articles contractuels de base inseres sous la nomenclature ART-XXX !")
except Exception as e:
    print(f"Erreur lors de l'insertion des articles : {e}")
