"""
Migration : ajout de la colonne modifie_le à la table articles.
Exécuter : py migrate_modifie_le.py
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

try:
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cursor = conn.cursor()

    # Vérifier si la colonne existe déjà
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'articles' AND column_name = 'modifie_le';
    """)
    exists = cursor.fetchone()

    if exists:
        print("✅ La colonne 'modifie_le' existe déjà dans la table articles. Aucune modification nécessaire.")
    else:
        print("Ajout de la colonne 'modifie_le' à la table articles...")
        cursor.execute("""
            ALTER TABLE articles
            ADD COLUMN modifie_le TIMESTAMP WITHOUT TIME ZONE;
        """)
        # Initialiser les articles existants avec NOW()
        cursor.execute("""
            UPDATE articles
            SET modifie_le = NOW()
            WHERE modifie_le IS NULL;
        """)
        conn.commit()
        print("✅ Colonne 'modifie_le' ajoutée et articles existants mis à jour avec la date actuelle.")

    # Afficher la structure finale de la table
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'articles'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    print("\nStructure de la table articles :")
    for col in columns:
        print(f"  - {col[0]} ({col[1]}, nullable={col[2]})")

    cursor.close()
    conn.close()
    print("\n✅ Migration terminée avec succès !")

except Exception as e:
    print(f"❌ Erreur lors de la migration : {e}")
