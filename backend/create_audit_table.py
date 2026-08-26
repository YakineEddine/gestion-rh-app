"""
Creation de la table audit_logs (journal d'audit / historique des activites).

Cette table est entierement nouvelle : elle est creee via
Base.metadata.create_all(), qui ne cree que les tables manquantes et ne
touche jamais aux tables existantes. Aucune donnee existante n'est modifiee.

Exécuter : py create_audit_table.py
"""
import sys
from app.database import engine, Base
from app.models.models import AuditLog  # noqa: F401  (necessaire pour enregistrer le modele)
from sqlalchemy import inspect

try:
    inspector = inspect(engine)
    existed_before = "audit_logs" in inspector.get_table_names()

    if existed_before:
        print("✅ La table 'audit_logs' existe déjà. Aucune modification nécessaire.")
    else:
        print("Création de la table 'audit_logs'...")
        Base.metadata.create_all(bind=engine, tables=[AuditLog.__table__])
        print("✅ Table 'audit_logs' créée avec succès.")

    inspector = inspect(engine)
    columns = inspector.get_columns("audit_logs")
    indexes = inspector.get_indexes("audit_logs")

    print("\nStructure de la table audit_logs :")
    for col in columns:
        print(f"  - {col['name']} ({col['type']}, nullable={col['nullable']})")

    print("\nIndex présents :")
    for idx in indexes:
        print(f"  - {idx['name']} sur {idx['column_names']}")

    print("\n✅ Vérification terminée avec succès !")

except Exception as e:
    print(f"❌ Erreur lors de la création de la table : {e}")
    sys.exit(1)
