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

    # Alter articles.est_actif column to BOOLEAN if it exists and is VARCHAR
    cursor.execute("""
        SELECT data_type 
        FROM information_schema.columns 
        WHERE table_name = 'articles' AND column_name = 'est_actif';
    """)
    res = cursor.fetchone()
    if res:
        current_type = res[0]
        print(f"Current type of articles.est_actif: {current_type}")
        if 'character' in current_type or 'varchar' in current_type:
            print("Converting articles.est_actif to BOOLEAN...")
            cursor.execute("ALTER TABLE articles ALTER COLUMN est_actif TYPE BOOLEAN USING (est_actif::boolean);")
            conn.commit()
            print("Conversion successful!")
        else:
            print("No conversion needed.")
    else:
        print("Table articles does not exist yet. It will be created by SQLAlchemy.")

    cursor.close()
    conn.close()
    print("Migration check complete.")
except Exception as e:
    print(f"Error during migration: {e}")
