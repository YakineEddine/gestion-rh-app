"""
Script pour migrer la base de données en ajoutant les nouvelles colonnes
à la table utilisateurs.
Exécuter : py migrate.py
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "gestion_rh_db")

conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
)
cursor = conn.cursor()

# Ajout des nouvelles colonnes si elles n'existent pas déjà
migrations = [
    "ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS date_naissance DATE",
    "ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS telephone VARCHAR",
    "ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS departement VARCHAR",
    "ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS poste VARCHAR",
]

for migration in migrations:
    print(f"Exécution : {migration}")
    cursor.execute(migration)

conn.commit()
cursor.close()
conn.close()

print("\n✅ Migration terminée avec succès !")
