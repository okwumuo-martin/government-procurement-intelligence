import sqlite3
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
db_path = project_root / "data" / "database" / "procurement_2025.db"

conn = sqlite3.connect(db_path)

tables = [
    "suppliers",
    "award_suppliers",
    "award_versions",
    "procurements"
]

print("=" * 70)
print("SUPPLIER ANALYSIS DATABASE SCHEMA")
print("=" * 70)

for table in tables:
    print(f"\n{'=' * 70}")
    print(f"TABLE: {table}")
    print(f"{'=' * 70}")

    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()

    for row in rows:
        column_id, name, data_type, not_null, default_value, primary_key = row

        print(
            f"{column_id:>3} | "
            f"{name:<35} | "
            f"{data_type:<12} | "
            f"PK={primary_key} | "
            f"NOT NULL={not_null}"
        )

conn.close()

print("\n" + "=" * 70)
print("SCHEMA INSPECTION COMPLETE")
print("=" * 70)