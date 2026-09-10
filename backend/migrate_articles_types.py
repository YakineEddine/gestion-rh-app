from app.database import engine
from sqlalchemy import text
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

engines = [
    ("Main DB (gestion_rh_db)", engine),
    ("Test DB (gestion_rh_test_db)", create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/gestion_rh_test_db"))
]

for name, eng in engines:
    try:
        with eng.connect() as conn:
            # Check if types_contrat exists
            check = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'articles' AND column_name = 'types_contrat'
            """)).fetchall()
            
            if not check:
                conn.execute(text("ALTER TABLE articles ADD COLUMN types_contrat JSONB DEFAULT NULL"))
                conn.commit()
                print(f"[{name}] Added column 'types_contrat' (JSONB) to 'articles'")
            else:
                print(f"[{name}] Column 'types_contrat' already exists.")
    except Exception as e:
        print(f"[{name}] Error: {e}")
