"""
Migration : Adaptation des statuts de contrat vers les nouveaux statuts.
Nouveaux statuts :
- BROUILLON
- COMMUNIQUE_EN_COURS
- SIGNE
- ACTIF
- FIN_CDD
- DEMISSION_CDI
- PAS_DISCUTE
- INACTIF

Exécuter : py migrate_statuts_contrats.py
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


def migrer_base(dbname):
    print(f"\n--- Migration de la base {dbname} ---")
    try:
        conn = psycopg2.connect(
            dbname=dbname, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        cursor = conn.cursor()

        # 1. Vérifier la colonne statut
        cursor.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'contrats' AND column_name = 'statut';
        """)
        col_info = cursor.fetchone()
        if not col_info:
            print("Table 'contrats' ou colonne 'statut' introuvable.")
            cursor.close()
            conn.close()
            return

        print(f"Colonne 'statut' : type={col_info[1]}, default={col_info[2]}")

        # 2. Lire les contrats existants
        cursor.execute("SELECT id, reference, type_contrat, statut FROM contrats ORDER BY id;")
        contrats = cursor.fetchall()
        print(f"Total contrats trouvés : {len(contrats)}")
        for c in contrats:
            print(f"  ID {c[0]} | Ref {c[1]} | Type {c[2]} | Statut actuel: '{c[3]}'")

        # 3. Mettre à jour les statuts anciens vers les nouveaux statuts
        # - Brouillon -> BROUILLON
        cursor.execute("UPDATE contrats SET statut = 'BROUILLON' WHERE statut IN ('Brouillon', 'brouillon');")

        # - Actif -> ACTIF
        cursor.execute("UPDATE contrats SET statut = 'ACTIF' WHERE statut IN ('Actif', 'actif');")

        # - Suspendu -> INACTIF (archivé / inactif)
        cursor.execute("UPDATE contrats SET statut = 'INACTIF' WHERE statut IN ('Suspendu', 'suspendu');")

        # - Terminé / Termine :
        #   Pour CDI -> DEMISSION_CDI
        #   Pour CDD / autres -> FIN_CDD
        cursor.execute("""
            UPDATE contrats
            SET statut = CASE
                WHEN type_contrat = 'CDI' THEN 'DEMISSION_CDI'
                ELSE 'FIN_CDD'
            END
            WHERE statut IN ('Terminé', 'Termine', 'terminé', 'termine');
        """)

        # - Expiré / Expire -> FIN_CDD
        cursor.execute("""
            UPDATE contrats
            SET statut = 'FIN_CDD'
            WHERE statut IN ('Expiré', 'Expire', 'expiré', 'expire');
        """)

        # 4. Mettre à jour la valeur par défaut de la colonne
        cursor.execute("ALTER TABLE contrats ALTER COLUMN statut SET DEFAULT 'BROUILLON';")

        conn.commit()

        # 5. Vérification
        cursor.execute("SELECT id, reference, type_contrat, statut FROM contrats ORDER BY id;")
        updated = cursor.fetchall()
        print("\nContrats après migration :")
        for c in updated:
            print(f"  ID {c[0]} | Ref {c[1]} | Type {c[2]} | Nouveau statut: '{c[3]}'")

        cursor.close()
        conn.close()
        print(f"[OK] Migration de {dbname} terminee avec succes !")

    except Exception as e:
        print(f"[ERREUR] Erreur lors de la migration de {dbname} : {e}")


if __name__ == "__main__":
    migrer_base(DB_NAME)
    # Migrer aussi la base de test si elle existe
    test_db = os.getenv("TEST_DB_NAME", "gestion_rh_test_db")
    migrer_base(test_db)
