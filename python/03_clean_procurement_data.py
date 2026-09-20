import pandas as pd
from pathlib import Path

# ============================================================
# Government Procurement Intelligence
# Step 3: Clean and extract procurement data
# ============================================================

# ------------------------------------------------------------
# 1. Project directories
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# 2. Find raw CSV
# ------------------------------------------------------------

files = list(RAW_DIR.glob("*.csv"))

if not files:
    raise FileNotFoundError(
        "No CSV files found in data/raw/"
    )

file_path = files[0]

print("=" * 70)
print("GOVERNMENT PROCUREMENT INTELLIGENCE")
print("DATA CLEANING AND EXTRACTION")
print("=" * 70)

print(f"\nInput file:")
print(file_path.name)

# ------------------------------------------------------------
# 3. Load data
# ------------------------------------------------------------

df = pd.read_csv(
    file_path,
    low_memory=False
)

print(f"\nOriginal rows: {len(df):,}")
print(f"Original columns: {len(df):,}")

# ------------------------------------------------------------
# 4. Define source columns
# ------------------------------------------------------------

column_map = {

    "ocid":
        "releases/0/ocid",

    "release_id":
        "releases/0/id",

    "procurement_date":
        "releases/0/date",

    "buyer_id":
        "releases/0/buyer/id",

    "buyer_name":
        "releases/0/buyer/name",

    "tender_title":
        "releases/0/tender/title",

    "tender_status":
        "releases/0/tender/status",

    "category":
        "releases/0/tender/mainProcurementCategory",

    "cpv_scheme":
        "releases/0/tender/classification/scheme",

    "cpv_code":
        "releases/0/tender/classification/id",

    "cpv_description":
        "releases/0/tender/classification/description",

    "procurement_method":
        "releases/0/tender/procurementMethod",

    "procurement_method_details":
        "releases/0/tender/procurementMethodDetails",

    "tender_value":
        "releases/0/tender/value/amount",

    "tender_currency":
        "releases/0/tender/value/currency",

    "tender_end_date":
        "releases/0/tender/tenderPeriod/endDate",

    "tender_contract_start":
        "releases/0/tender/contractPeriod/startDate",

    "tender_contract_end":
        "releases/0/tender/contractPeriod/endDate",

    "award_id":
        "releases/0/awards/0/id",

    "award_status":
        "releases/0/awards/0/status",

    "award_date":
        "releases/0/awards/0/date",

    "award_published_date":
        "releases/0/awards/0/datePublished",

    "award_value":
        "releases/0/awards/0/value/amount",

    "award_currency":
        "releases/0/awards/0/value/currency",

    "supplier_id":
        "releases/0/awards/0/suppliers/0/id",

    "supplier_name":
        "releases/0/awards/0/suppliers/0/name",

    "contract_start":
        "releases/0/awards/0/contractPeriod/startDate",

    "contract_end":
        "releases/0/awards/0/contractPeriod/endDate"
}

# ------------------------------------------------------------
# 5. Verify source columns
# ------------------------------------------------------------

missing_columns = [
    source_column
    for source_column in column_map.values()
    if source_column not in df.columns
]

if missing_columns:

    print("\nERROR: The following source columns are missing:")

    for column in missing_columns:
        print(f" - {column}")

    raise KeyError(
        "One or more required source columns are missing."
    )

# ------------------------------------------------------------
# 6. Extract analytical fields
# ------------------------------------------------------------

clean = df[
    list(column_map.values())
].copy()

# Rename columns

clean.columns = list(column_map.keys())

# ------------------------------------------------------------
# 7. Convert dates
# ------------------------------------------------------------

date_columns = [
    "procurement_date",
    "tender_end_date",
    "tender_contract_start",
    "tender_contract_end",
    "award_date",
    "award_published_date",
    "contract_start",
    "contract_end"
]

for column in date_columns:

    clean[column] = pd.to_datetime(
        clean[column],
        errors="coerce",
        utc=True
    )

# ------------------------------------------------------------
# 8. Convert numeric fields
# ------------------------------------------------------------

numeric_columns = [
    "tender_value",
    "award_value"
]

for column in numeric_columns:

    clean[column] = pd.to_numeric(
        clean[column],
        errors="coerce"
    )

# ------------------------------------------------------------
# 9. Clean text fields
# ------------------------------------------------------------

text_columns = [
    "buyer_id",
    "buyer_name",
    "tender_title",
    "category",
    "cpv_scheme",
    "cpv_description",
    "procurement_method",
    "procurement_method_details",
    "tender_currency",
    "award_status",
    "award_currency",
    "supplier_id",
    "supplier_name"
]

for column in text_columns:

    clean[column] = (
        clean[column]
        .astype("string")
        .str.strip()
    )

# ------------------------------------------------------------
# 10. Create procurement year/month
# ------------------------------------------------------------

clean["procurement_year"] = (
    clean["procurement_date"]
    .dt.year
)

clean["procurement_month"] = (
    clean["procurement_date"]
    .dt.month
)

clean["procurement_month_name"] = (
    clean["procurement_date"]
    .dt.month_name()
)

# ------------------------------------------------------------
# 11. Calculate contract duration
# ------------------------------------------------------------

clean["contract_duration_days"] = (
    clean["contract_end"] -
    clean["contract_start"]
).dt.days

# ------------------------------------------------------------
# 12. Calculate tender-to-award difference
# ------------------------------------------------------------

clean["tender_to_award_days"] = (
    clean["award_date"] -
    clean["procurement_date"]
).dt.days

# ------------------------------------------------------------
# 13. Create award-to-tender value ratio
# ------------------------------------------------------------

clean["award_to_tender_ratio"] = (
    clean["award_value"] /
    clean["tender_value"]
)

# Prevent infinite values

clean["award_to_tender_ratio"] = (
    clean["award_to_tender_ratio"]
    .replace([float("inf"), -float("inf")], pd.NA)
)

# ------------------------------------------------------------
# 14. Create data-quality flags
# ------------------------------------------------------------

clean["has_award"] = (
    clean["award_id"].notna()
)

clean["has_supplier"] = (
    clean["supplier_name"].notna()
)

clean["has_contract_dates"] = (
    clean["contract_start"].notna() &
    clean["contract_end"].notna()
)

clean["has_award_value"] = (
    clean["award_value"].notna()
)

# ------------------------------------------------------------
# 15. Remove exact duplicate OCIDs
# ------------------------------------------------------------

before = len(clean)

clean = clean.drop_duplicates(
    subset=["ocid"],
    keep="first"
)

after = len(clean)

print(
    f"\nDuplicate OCIDs removed: {before - after:,}"
)

# ------------------------------------------------------------
# 16. Save cleaned dataset
# ------------------------------------------------------------

output_file = (
    PROCESSED_DIR /
    "procurement_records_clean.csv"
)

clean.to_csv(
    output_file,
    index=False
)

# ------------------------------------------------------------
# 17. Print summary
# ------------------------------------------------------------

print("\n")
print("=" * 70)
print("CLEANING COMPLETE")
print("=" * 70)

print(f"\nFinal rows: {len(clean):,}")
print(f"Final columns: {len(clean.columns):,}")

print("\nOutput file:")
print(output_file)

print("\nAward records:")
print(
    clean["has_award"]
    .value_counts(dropna=False)
)

print("\nSupplier records:")
print(
    clean["has_supplier"]
    .value_counts(dropna=False)
)

print("\nProcurement categories:")
print(
    clean["category"]
    .value_counts(dropna=False)
)

print("\nProcurement methods:")
print(
    clean["procurement_method"]
    .value_counts(dropna=False)
)

print("\nTop suppliers:")
print(
    clean["supplier_name"]
    .value_counts()
    .head(10)
)

print("\nTop buyers:")
print(
    clean["buyer_name"]
    .value_counts()
    .head(10)
)

print("\nFirst five cleaned records:")

print(
    clean[
        [
            "ocid",
            "buyer_name",
            "tender_title",
            "category",
            "award_value",
            "supplier_name"
        ]
    ]
    .head()
    .to_string(index=False)
)

print("\n" + "=" * 70)
print("READY FOR SQL DATABASE DESIGN")
print("=" * 70)