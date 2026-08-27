"""
Script de migration pour l'Etape 4 - Authentification Renforcee.
Ajoute les colonnes de blocage brute-force sur utilisateurs et cree les tables refresh_tokens et reset_tokens si elles n'existent pas.
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

migrations = [
    # Colonnes sur utilisateurs
    "ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS login_attempts INTEGER DEFAULT 0 NOT NULL",
    "ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP",
    "ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS last_failed_login TIMESTAMP",
    
    # Table refresh_tokens
    """
    CREATE TABLE IF NOT EXISTS refresh_tokens (
        id SERIAL PRIMARY KEY,
        utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id) ON DELETE CASCADE,
        token_hash VARCHAR NOT NULL UNIQUE,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        revoked_at TIMESTAMP,
        revoked BOOLEAN DEFAULT FALSE NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_refresh_tokens_utilisateur_id ON refresh_tokens (utilisateur_id)",
    "CREATE INDEX IF NOT EXISTS ix_refresh_tokens_token_hash ON refresh_tokens (token_hash)",

    # Table reset_tokens
    """
    CREATE TABLE IF NOT EXISTS reset_tokens (
        id SERIAL PRIMARY KEY,
        utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id) ON DELETE CASCADE,
        token_hash VARCHAR NOT NULL UNIQUE,
        expires_at TIMESTAMP NOT NULL,
        used_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_reset_tokens_utilisateur_id ON reset_tokens (utilisateur_id)",
    "CREATE INDEX IF NOT EXISTS ix_reset_tokens_token_hash ON reset_tokens (token_hash)",
]

for migration in migrations:
    print(f"Exécution : {migration.strip()[:60]}...")
    cursor.execute(migration)

conn.commit()
cursor.close()
conn.close()

print("\nMigration Authentification Renforcee terminee avec succes !")
