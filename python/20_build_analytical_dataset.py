from pathlib import Path
import pandas as pd


# ============================================================
# GOVERNMENT PROCUREMENT INTELLIGENCE
# BUILD FINAL PYTHON ANALYTICAL DATASET
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SQL_RESULT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "sql_results"
    / "05_risk_analysis_query_19.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "analysis"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "procurement_analytical_dataset.csv"
)


print("=" * 70)
print("GOVERNMENT PROCUREMENT INTELLIGENCE")
print("BUILDING FINAL PYTHON ANALYTICAL DATASET")
print("=" * 70)


# ------------------------------------------------------------
# 1. LOAD AUTHORITATIVE SQL ANALYTICAL DATASET
# ------------------------------------------------------------

print("\nLoading authoritative SQL analytical dataset...")

if not SQL_RESULT_FILE.exists():
    raise FileNotFoundError(
        f"Required SQL result not found:\n{SQL_RESULT_FILE}\n\n"
        "Run python/16_run_sql_analysis.py first."
    )

df = pd.read_csv(
    SQL_RESULT_FILE
)

print(
    f"Records loaded: {len(df):,}"
)

print(
    f"Columns loaded: {len(df.columns):,}"
)


# ------------------------------------------------------------
# 2. CONVERT DATE FIELDS
# ------------------------------------------------------------

date_columns = [
    "release_date",
    "award_date",
    "contract_start",
    "contract_end"
]

for column in date_columns:

    if column in df.columns:

        df[column] = pd.to_datetime(
            df[column],
            errors="coerce",
            utc=True
        )


# ------------------------------------------------------------
# 3. ADD BUSINESS-FRIENDLY PROCUREMENT METHOD
# ------------------------------------------------------------

def classify_method(method):

    if pd.isna(method):
        return "Unknown"

    method = str(method).strip().lower()

    if "direct" in method:
        return "Direct"

    if "limited" in method:
        return "Limited"

    if "selective" in method:
        return "Selective"

    if "open" in method:
        return "Open"

    return "Other"


df["procurement_method_group"] = (
    df["procurement_method"]
    .apply(classify_method)
)


# ------------------------------------------------------------
# 4. AWARD VALUE BAND
# ------------------------------------------------------------

def classify_value(value):

    if pd.isna(value):
        return "Unknown"

    if value >= 1_000_000_000:
        return "£1B+"

    if value >= 100_000_000:
        return "£100M–<£1B"

    if value >= 10_000_000:
        return "£10M–<£100M"

    if value >= 1_000_000:
        return "£1M–<£10M"

    if value >= 100_000:
        return "£100K–<£1M"

    return "<£100K"


df["award_value_band"] = (
    df["award_value"]
    .apply(classify_value)
)


# ------------------------------------------------------------
# 5. CONTRACT DURATION BAND
# ------------------------------------------------------------

def classify_duration(years):

    if pd.isna(years):
        return "Unknown"

    if years >= 20:
        return "20+ years"

    if years >= 10:
        return "10–<20 years"

    if years >= 5:
        return "5–<10 years"

    if years >= 3:
        return "3–<5 years"

    if years >= 1:
        return "1–<3 years"

    return "<1 year"


df["contract_duration_band"] = (
    df["contract_duration_years"]
    .apply(classify_duration)
)


# ------------------------------------------------------------
# 6. SUPPLIER STRUCTURE
# ------------------------------------------------------------

df["supplier_structure"] = "No usable supplier"

df.loc[
    df["usable_supplier_count"] == 1,
    "supplier_structure"
] = "Single supplier"

df.loc[
    df["usable_supplier_count"] > 1,
    "supplier_structure"
] = "Multiple suppliers"


# ------------------------------------------------------------
# 7. DATA QUALITY FLAGS
# ------------------------------------------------------------

df["missing_award_value_flag"] = (
    df["award_value"]
    .isna()
    .astype(int)
)

df["missing_contract_dates_flag"] = (
    (
        df["contract_start"].isna()
        |
        df["contract_end"].isna()
    )
    .astype(int)
)

df["missing_procurement_method_flag"] = (
    df["procurement_method"]
    .isna()
    .astype(int)
)

df["missing_procurement_category_flag"] = (
    df["procurement_category"]
    .isna()
    .astype(int)
)

df["missing_tender_value_flag"] = (
    df["tender_value"]
    .isna()
    .astype(int)
)


# ------------------------------------------------------------
# 8. PRI VALIDATION
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("PRI VALIDATION")
print("=" * 70)

print(
    f"\nTotal analytical records: {len(df):,}"
)

print("\nPRI score distribution:")

print(
    df["pri_score"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nPRI category distribution:")

print(
    df["pri_category"]
    .value_counts()
    .to_string()
)


# ------------------------------------------------------------
# 9. HIGH / PRIORITY VALIDATION
# ------------------------------------------------------------

high_priority = df[
    df["pri_score"] >= 4
].copy()

print(
    f"\nHigh/Priority records: "
    f"{len(high_priority):,}"
)


# ------------------------------------------------------------
# 10. SUPPLIER STRUCTURE VALIDATION
# ------------------------------------------------------------

print("\nSupplier structure:")

print(
    df["supplier_structure"]
    .value_counts()
    .to_string()
)


# ------------------------------------------------------------
# 11. PROCUREMENT METHOD VALIDATION
# ------------------------------------------------------------

print("\nProcurement method:")

print(
    df["procurement_method_group"]
    .value_counts()
    .to_string()
)


# ------------------------------------------------------------
# 12. TOP HIGH / PRIORITY RECORDS
# ------------------------------------------------------------

print("\nTop 10 High/Priority records:")

display_columns = [
    "buyer_name",
    "tender_title",
    "award_value",
    "procurement_method_group",
    "contract_duration_years",
    "supplier_names",
    "pri_score",
    "pri_category"
]

print(
    high_priority[
        display_columns
    ]
    .head(10)
    .to_string(index=False)
)


# ------------------------------------------------------------
# 13. DATA QUALITY SUMMARY
# ------------------------------------------------------------

print("\nMissing-value summary:")

missing_summary = (
    df.isna()
    .sum()
    .sort_values(
        ascending=False
    )
)

print(
    missing_summary[
        missing_summary > 0
    ]
    .head(15)
    .to_string()
)


# ------------------------------------------------------------
# 14. SAVE
# ------------------------------------------------------------

# Convert timestamps to ISO strings for portable CSV output.

for column in date_columns:

    if column in df.columns:

        df[column] = (
            df[column]
            .dt.strftime("%Y-%m-%d %H:%M:%S%z")
        )


df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# 15. FINAL VALIDATION
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FINAL DATASET VALIDATION")
print("=" * 70)

print(
    f"\nRows:    {len(df):,}"
)

print(
    f"Columns: {len(df.columns):,}"
)

assert len(df) == 45_011, (
    f"Unexpected row count: {len(df):,}"
)

assert len(high_priority) == 55, (
    f"Unexpected High/Priority count: "
    f"{len(high_priority):,}"
)

assert df["pri_score"].min() == 0

assert df["pri_score"].max() == 6

print("\nValidation checks passed.")

print("\nOutput saved to:")
print(f"  {OUTPUT_FILE}")

print("\n" + "=" * 70)
print("PYTHON ANALYTICAL DATASET READY")
print("=" * 70)