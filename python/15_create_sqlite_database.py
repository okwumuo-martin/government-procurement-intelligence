import sqlite3
from pathlib import Path
import pandas as pd


# ============================================================
# CONTRACTS FINDER 2025
# SQLITE ANALYTICAL DATABASE CREATION
# ============================================================

print("=" * 70)
print("CONTRACTS FINDER 2025")
print("SQLITE ANALYTICAL DATABASE CREATION")
print("=" * 70)


# ============================================================
# 1. PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FINAL_DIR = PROJECT_ROOT / "data" / "processed" / "final"
DATABASE_DIR = PROJECT_ROOT / "data" / "database"

DATABASE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "procurement_2025.db"


# ============================================================
# 2. INPUT FILES
# ============================================================

FILES = {
    "procurements": FINAL_DIR / "procurements_2025.csv",
    "releases": FINAL_DIR / "releases_2025.csv",
    "award_versions": FINAL_DIR / "award_versions_2025.csv",
    "award_suppliers": FINAL_DIR / "award_suppliers_2025.csv",
    "suppliers": FINAL_DIR / "suppliers_2025.csv",
}


print("\nChecking input files...")

for table, path in FILES.items():
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found for table '{table}': {path}"
        )

    print(f"  [OK] {table}: {path.name}")


# ============================================================
# 3. REMOVE EXISTING DATABASE
# ============================================================

if DATABASE_PATH.exists():
    print("\nExisting database found.")
    print("Replacing it with a fresh database...")

    DATABASE_PATH.unlink()

    print("  [OK] Existing database removed.")


# ============================================================
# 4. CREATE DATABASE CONNECTION
# ============================================================

print("\nCreating SQLite database...")

conn = sqlite3.connect(DATABASE_PATH)

cursor = conn.cursor()

# Improve SQLite performance while loading data.
cursor.execute("PRAGMA journal_mode = WAL;")
cursor.execute("PRAGMA foreign_keys = ON;")

print(f"  [OK] Database created: {DATABASE_PATH}")


# ============================================================
# 5. CREATE TABLES
# ============================================================

print("\nCreating database tables...")


# ------------------------------------------------------------
# PROCUREMENT TABLE
# One row per procurement / OCID
# ------------------------------------------------------------

cursor.execute("""
CREATE TABLE procurements (
    ocid TEXT PRIMARY KEY,
    tender_title TEXT,
    tender_status TEXT,
    buyer_name TEXT,
    buyer_id TEXT,
    procurement_method TEXT,
    procurement_category TEXT,
    cpv_code TEXT,
    tender_value REAL,
    tender_currency TEXT
);
""")


# ------------------------------------------------------------
# RELEASE TABLE
# One row per unique release_id
# ------------------------------------------------------------

cursor.execute("""
CREATE TABLE releases (
    release_id TEXT PRIMARY KEY,
    ocid TEXT NOT NULL,
    release_date TEXT NOT NULL,
    release_tag TEXT,
    initiation_type TEXT,
    tender_id TEXT,
    tender_title TEXT,
    tender_description TEXT,
    tender_status TEXT,
    tender_value REAL,
    tender_currency TEXT,
    procurement_method TEXT,
    procurement_method_details TEXT,
    procurement_category TEXT,
    tender_period_start TEXT,
    tender_period_end TEXT,
    buyer_id TEXT,
    buyer_name TEXT,
    cpv_scheme TEXT,
    cpv_code TEXT,
    cpv_description TEXT,
    vcse_suitability TEXT,
    sme_suitability TEXT,
    source_file TEXT,

    FOREIGN KEY (ocid)
        REFERENCES procurements(ocid)
);
""")


# ------------------------------------------------------------
# AWARD VERSION TABLE
# One row per award_id + release_id
# ------------------------------------------------------------

cursor.execute("""
CREATE TABLE award_versions (
    award_id TEXT NOT NULL,
    release_id TEXT NOT NULL,
    ocid TEXT NOT NULL,
    release_date TEXT,
    award_index INTEGER,
    award_status TEXT,
    award_date TEXT,
    award_value REAL,
    award_currency TEXT,
    award_title TEXT,
    award_description TEXT,
    contract_start TEXT,
    contract_end TEXT,
    source_file TEXT,
    award_version_number INTEGER,
    award_version_count INTEGER,
    is_latest_award_version INTEGER,

    PRIMARY KEY (award_id, release_id),

    FOREIGN KEY (release_id)
        REFERENCES releases(release_id),

    FOREIGN KEY (ocid)
        REFERENCES procurements(ocid)
);
""")


# ------------------------------------------------------------
# SUPPLIER MASTER
# One row per analytical supplier_key
# ------------------------------------------------------------

cursor.execute("""
CREATE TABLE suppliers (
    supplier_key TEXT PRIMARY KEY,
    supplier_id TEXT,
    canonical_supplier_name TEXT,
    reported_name_count INTEGER,
    relationship_count INTEGER,
    supplier_id_quality TEXT,
    identity_review_flag TEXT
);
""")


# ------------------------------------------------------------
# AWARD-SUPPLIER RELATIONSHIPS
# One row per supplier relationship observation
# ------------------------------------------------------------

cursor.execute("""
CREATE TABLE award_suppliers (
    relationship_observation_key TEXT PRIMARY KEY,
    ocid TEXT NOT NULL,
    release_id TEXT NOT NULL,
    award_id TEXT NOT NULL,
    award_index INTEGER,
    supplier_index INTEGER,
    supplier_id TEXT,
    supplier_name TEXT,
    supplier_name_normalized TEXT,
    source_file TEXT,
    supplier_id_quality TEXT,
    supplier_key TEXT NOT NULL,
    supplier_id_name_count INTEGER,
    supplier_identity_flag TEXT,
    canonical_supplier_name TEXT,
    identity_review_flag TEXT,

    FOREIGN KEY (release_id)
        REFERENCES releases(release_id),

    FOREIGN KEY (ocid)
        REFERENCES procurements(ocid),

    FOREIGN KEY (award_id, release_id)
        REFERENCES award_versions(award_id, release_id),

    FOREIGN KEY (supplier_key)
        REFERENCES suppliers(supplier_key)
);
""")


conn.commit()

print("  [OK] procurements")
print("  [OK] releases")
print("  [OK] award_versions")
print("  [OK] suppliers")
print("  [OK] award_suppliers")


# ============================================================
# 6. LOAD CSV DATA
# ============================================================

print("\nLoading analytical datasets...")


def load_csv_to_sqlite(csv_path, table_name):
    """
    Load a validated CSV into the corresponding SQLite table.
    """

    print(f"\nLoading {table_name}...")

    df = pd.read_csv(csv_path, low_memory=False)

    print(f"  Rows:    {len(df):,}")
    print(f"  Columns: {len(df.columns)}")

    # Convert pandas NaN values to Python None so SQLite stores
    # them as SQL NULL.
    df = df.where(pd.notnull(df), None)

    # SQLite does not have a native boolean type.
    # Convert the latest-award flag explicitly to integer.
    if table_name == "award_versions":
        if "is_latest_award_version" in df.columns:
            df["is_latest_award_version"] = (
                df["is_latest_award_version"]
                .astype(str)
                .str.lower()
                .map({
                    "true": 1,
                    "false": 0,
                    "1": 1,
                    "0": 0
                })
            )

    # Explicit integer fields.
    integer_columns = {
        "award_versions": [
            "award_index",
            "award_version_number",
            "award_version_count",
            "is_latest_award_version"
        ],
        "award_suppliers": [
            "award_index",
            "supplier_index",
            "supplier_id_name_count"
        ],
        "suppliers": [
            "reported_name_count",
            "relationship_count"
        ]
    }

    for column in integer_columns.get(table_name, []):
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # Numeric monetary fields.
    numeric_columns = {
        "procurements": ["tender_value"],
        "releases": ["tender_value"],
        "award_versions": ["award_value"]
    }

    for column in numeric_columns.get(table_name, []):
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # Ensure the CSV column order exactly matches the SQLite table.
    cursor.execute(f"PRAGMA table_info({table_name});")

    db_columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    missing_columns = [
        col for col in db_columns
        if col not in df.columns
    ]

    extra_columns = [
        col for col in df.columns
        if col not in db_columns
    ]

    if missing_columns:
        raise ValueError(
            f"{table_name}: Missing required columns: "
            f"{missing_columns}"
        )

    if extra_columns:
        print(
            f"  Warning: extra CSV columns ignored: "
            f"{extra_columns}"
        )

    df = df[db_columns]

    # Load into SQLite.
    df.to_sql(
        table_name,
        conn,
        if_exists="append",
        index=False
    )

    print(f"  [OK] Loaded {len(df):,} rows")


# Load in dependency order.
load_csv_to_sqlite(FILES["procurements"], "procurements")
load_csv_to_sqlite(FILES["releases"], "releases")
load_csv_to_sqlite(FILES["award_versions"], "award_versions")
load_csv_to_sqlite(FILES["suppliers"], "suppliers")
load_csv_to_sqlite(FILES["award_suppliers"], "award_suppliers")


# ============================================================
# 7. CREATE INDEXES
# ============================================================

print("\nCreating analytical indexes...")


indexes = [

    # Procurement lookups
    """
    CREATE INDEX idx_procurements_buyer
    ON procurements(buyer_id);
    """,

    """
    CREATE INDEX idx_procurements_category
    ON procurements(procurement_category);
    """,

    """
    CREATE INDEX idx_procurements_method
    ON procurements(procurement_method);
    """,

    # Release lookups
    """
    CREATE INDEX idx_releases_ocid
    ON releases(ocid);
    """,

    """
    CREATE INDEX idx_releases_date
    ON releases(release_date);
    """,

    """
    CREATE INDEX idx_releases_buyer
    ON releases(buyer_id);
    """,

    # Award analysis
    """
    CREATE INDEX idx_awards_ocid
    ON award_versions(ocid);
    """,

    """
    CREATE INDEX idx_awards_date
    ON award_versions(award_date);
    """,

    """
    CREATE INDEX idx_awards_value
    ON award_versions(award_value);
    """,

    """
    CREATE INDEX idx_awards_latest
    ON award_versions(is_latest_award_version);
    """,

    # Supplier relationships
    """
    CREATE INDEX idx_relationships_award
    ON award_suppliers(award_id, release_id);
    """,

    """
    CREATE INDEX idx_relationships_supplier
    ON award_suppliers(supplier_key);
    """,

    """
    CREATE INDEX idx_relationships_supplier_id
    ON award_suppliers(supplier_id);
    """,

    # Supplier master
    """
    CREATE INDEX idx_suppliers_id
    ON suppliers(supplier_id);
    """,

    """
    CREATE INDEX idx_suppliers_quality
    ON suppliers(supplier_id_quality);
    """
]


for statement in indexes:
    cursor.execute(statement)


conn.commit()

print(f"  [OK] Created {len(indexes)} indexes")


# ============================================================
# 8. DATABASE VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("DATABASE VALIDATION")
print("=" * 70)


expected_counts = {
    "procurements": 50_359,
    "releases": 50_380,
    "award_versions": 45_015,
    "award_suppliers": 57_311,
    "suppliers": 36_848
}

validation_failures = 0


for table, expected in expected_counts.items():

    result = cursor.execute(
        f"SELECT COUNT(*) FROM {table};"
    ).fetchone()[0]

    status = "PASS" if result == expected else "FAIL"

    if result != expected:
        validation_failures += 1

    print(
        f"{table:<20} "
        f"Expected: {expected:>8,}  "
        f"Actual: {result:>8,}  "
        f"{status}"
    )


# ============================================================
# 9. REFERENTIAL INTEGRITY CHECKS
# ============================================================

print("\nReferential integrity checks...")


checks = {

    "Release OCIDs missing procurement":
        """
        SELECT COUNT(*)
        FROM releases r
        LEFT JOIN procurements p
            ON r.ocid = p.ocid
        WHERE p.ocid IS NULL;
        """,

    "Award OCIDs missing procurement":
        """
        SELECT COUNT(*)
        FROM award_versions a
        LEFT JOIN procurements p
            ON a.ocid = p.ocid
        WHERE p.ocid IS NULL;
        """,

    "Award relationships missing award":
        """
        SELECT COUNT(*)
        FROM award_suppliers s
        LEFT JOIN award_versions a
            ON s.award_id = a.award_id
           AND s.release_id = a.release_id
        WHERE a.award_id IS NULL;
        """,

    "Relationships missing supplier":
        """
        SELECT COUNT(*)
        FROM award_suppliers r
        LEFT JOIN suppliers s
            ON r.supplier_key = s.supplier_key
        WHERE s.supplier_key IS NULL;
        """
}


for description, query in checks.items():

    result = cursor.execute(query).fetchone()[0]

    status = "PASS" if result == 0 else "FAIL"

    if result != 0:
        validation_failures += 1

    print(
        f"{description:<45} "
        f"{result:>8,}  {status}"
    )


# ============================================================
# 10. PRIMARY KEY DUPLICATE CHECKS
# ============================================================

print("\nPrimary key uniqueness checks...")


duplicate_checks = {

    "Duplicate procurement OCIDs":
        """
        SELECT COUNT(*)
        FROM (
            SELECT ocid
            FROM procurements
            GROUP BY ocid
            HAVING COUNT(*) > 1
        );
        """,

    "Duplicate release IDs":
        """
        SELECT COUNT(*)
        FROM (
            SELECT release_id
            FROM releases
            GROUP BY release_id
            HAVING COUNT(*) > 1
        );
        """,

    "Duplicate award versions":
        """
        SELECT COUNT(*)
        FROM (
            SELECT award_id, release_id
            FROM award_versions
            GROUP BY award_id, release_id
            HAVING COUNT(*) > 1
        );
        """,

    "Duplicate supplier keys":
        """
        SELECT COUNT(*)
        FROM (
            SELECT supplier_key
            FROM suppliers
            GROUP BY supplier_key
            HAVING COUNT(*) > 1
        );
        """
}


for description, query in duplicate_checks.items():

    result = cursor.execute(query).fetchone()[0]

    status = "PASS" if result == 0 else "FAIL"

    if result != 0:
        validation_failures += 1

    print(
        f"{description:<35} "
        f"{result:>8,}  {status}"
    )


# ============================================================
# 11. DATABASE SUMMARY
# ============================================================

print("\nDatabase summary...")

db_size_mb = DATABASE_PATH.stat().st_size / (1024 * 1024)

print(f"  Database: {DATABASE_PATH.name}")
print(f"  Size:     {db_size_mb:.2f} MB")


table_count = cursor.execute("""
    SELECT COUNT(*)
    FROM sqlite_master
    WHERE type = 'table'
      AND name NOT LIKE 'sqlite_%';
""").fetchone()[0]

index_count = cursor.execute("""
    SELECT COUNT(*)
    FROM sqlite_master
    WHERE type = 'index'
      AND name NOT LIKE 'sqlite_%';
""").fetchone()[0]

print(f"  Tables:   {table_count}")
print(f"  Indexes:  {index_count}")


# ============================================================
# 12. FINAL RESULT
# ============================================================

conn.commit()

if validation_failures == 0:

    print("\n" + "=" * 70)
    print("DATABASE CREATION COMPLETE")
    print("=" * 70)

    print("\nAll database validation checks PASSED.")

    print("\nSQLite database:")
    print(f"  {DATABASE_PATH}")

else:

    print("\n" + "=" * 70)
    print("DATABASE VALIDATION FAILED")
    print("=" * 70)

    print(
        f"\nValidation failures detected: "
        f"{validation_failures}"
    )

    conn.close()

    raise RuntimeError(
        "SQLite database failed validation."
    )


conn.close()

print("\nConnection closed.")
print("=" * 70)