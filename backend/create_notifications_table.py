"""
Creation de la table notifications (systeme d'alertes RH).

Cette table est entierement nouvelle : elle est creee via
Base.metadata.create_all(), qui ne cree que les tables manquantes et ne
touche jamais aux tables existantes. Aucune donnee existante n'est modifiee.

Exécuter : py create_notifications_table.py
"""
import sys
from app.database import engine, Base
from app.models.models import Notification  # noqa: F401  (necessaire pour enregistrer le modele)
from sqlalchemy import inspect

try:
    inspector = inspect(engine)
    existed_before = "notifications" in inspector.get_table_names()

    if existed_before:
        print("✅ La table 'notifications' existe déjà. Aucune modification nécessaire.")
    else:
        print("Création de la table 'notifications'...")
        Base.metadata.create_all(bind=engine, tables=[Notification.__table__])
        print("✅ Table 'notifications' créée avec succès.")

    inspector = inspect(engine)
    columns = inspector.get_columns("notifications")
    indexes = inspector.get_indexes("notifications")

    print("\nStructure de la table notifications :")
    for col in columns:
        print(f"  - {col['name']} ({col['type']}, nullable={col['nullable']})")

    print("\nIndex présents :")
    for idx in indexes:
        print(f"  - {idx['name']} sur {idx['column_names']} (unique={idx.get('unique')})")

    print("\n✅ Vérification terminée avec succès !")

except Exception as e:
    print(f"❌ Erreur lors de la création de la table : {e}")
    sys.exit(1)
