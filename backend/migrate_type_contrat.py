"""
Migration : ajout de la colonne type_contrat à la table contrats.
Exécuter : py migrate_type_contrat.py
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

    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'contrats' AND column_name = 'type_contrat';
    """)
    exists = cursor.fetchone()

    if exists:
        print("✅ La colonne 'type_contrat' existe déjà dans la table contrats. Aucune modification nécessaire.")
    else:
        print("Ajout de la colonne 'type_contrat' à la table contrats...")
        cursor.execute("ALTER TABLE contrats ADD COLUMN type_contrat VARCHAR;")

        # Retro-compatibilite : les contrats existants n'ont pas de type_contrat.
        # On deduit une valeur coherente a partir de la date de fin :
        # - pas de date de fin => CDI
        # - date de fin presente => CDD (valeur par defaut la plus prudente)
        cursor.execute("""
            UPDATE contrats
            SET type_contrat = CASE WHEN date_fin IS NULL THEN 'CDI' ELSE 'CDD' END
            WHERE type_contrat IS NULL;
        """)

        cursor.execute("ALTER TABLE contrats ALTER COLUMN type_contrat SET NOT NULL;")
        cursor.execute("ALTER TABLE contrats ALTER COLUMN type_contrat SET DEFAULT 'CDI';")

        conn.commit()
        print("✅ Colonne 'type_contrat' ajoutée et contrats existants mis à jour.")

    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'contrats'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    print("\nStructure de la table contrats :")
    for col in columns:
        print(f"  - {col[0]} ({col[1]}, nullable={col[2]})")

    cursor.close()
    conn.close()
    print("\n✅ Migration terminée avec succès !")

except Exception as e:
    print(f"❌ Erreur lors de la migration : {e}")
