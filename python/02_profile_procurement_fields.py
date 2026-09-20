import pandas as pd
from pathlib import Path

# ============================================================
# Government Procurement Intelligence
# Step 2: Profile important OCDS procurement fields
# ============================================================

# ------------------------------------------------------------
# 1. Locate the raw data
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

files = list(RAW_DIR.glob("*.csv"))

if not files:
    raise FileNotFoundError(
        "No CSV files were found in data/raw/"
    )

# Use the first CSV file for profiling
file_path = files[0]

print("=" * 70)
print("GOVERNMENT PROCUREMENT INTELLIGENCE")
print("PROCUREMENT FIELD PROFILING")
print("=" * 70)

print(f"\nFile being profiled:")
print(file_path.name)

# ------------------------------------------------------------
# 2. Load data
# ------------------------------------------------------------

df = pd.read_csv(file_path, low_memory=False)

print(f"\nRows: {len(df):,}")
print(f"Columns: {len(df):,}")

# ------------------------------------------------------------
# 3. Important fields
# ------------------------------------------------------------

fields = {
    "OCID": "releases/0/ocid",
    "Release ID": "releases/0/id",
    "Procurement Date": "releases/0/date",
    "Tender Title": "releases/0/tender/title",
    "Tender Status": "releases/0/tender/status",

    "Buyer ID": "releases/0/buyer/id",
    "Buyer Name": "releases/0/buyer/name",

    "Tender Value": "releases/0/tender/value/amount",
    "Tender Currency": "releases/0/tender/value/currency",

    "Procurement Method": "releases/0/tender/procurementMethod",
    "Procurement Method Details": (
        "releases/0/tender/procurementMethodDetails"
    ),

    "Tender End Date": (
        "releases/0/tender/tenderPeriod/endDate"
    ),

    "Contract Start": (
        "releases/0/tender/contractPeriod/startDate"
    ),

    "Contract End": (
        "releases/0/tender/contractPeriod/endDate"
    ),

    "Procurement Category": (
        "releases/0/tender/mainProcurementCategory"
    ),

    "Classification Scheme": (
        "releases/0/tender/classification/scheme"
    ),

    "Classification ID": (
        "releases/0/tender/classification/id"
    ),

    "Classification Description": (
        "releases/0/tender/classification/description"
    ),

    "Award ID": "releases/0/awards/0/id",
    "Award Status": "releases/0/awards/0/status",
    "Award Date": "releases/0/awards/0/date",

    "Award Published Date": (
        "releases/0/awards/0/datePublished"
    ),

    "Award Value": (
        "releases/0/awards/0/value/amount"
    ),

    "Award Currency": (
        "releases/0/awards/0/value/currency"
    ),

    "Supplier ID": (
        "releases/0/awards/0/suppliers/0/id"
    ),

    "Supplier Name": (
        "releases/0/awards/0/suppliers/0/name"
    ),

    "Award Contract Start": (
        "releases/0/awards/0/contractPeriod/startDate"
    ),

    "Award Contract End": (
        "releases/0/awards/0/contractPeriod/endDate"
    )
}

# ------------------------------------------------------------
# 4. Profile each important field
# ------------------------------------------------------------

print("\n")
print("=" * 70)
print("FIELD PROFILE")
print("=" * 70)

profile_rows = []

for label, column in fields.items():

    if column in df.columns:

        series = df[column]

        profile_rows.append({
            "Field": label,
            "Column": column,
            "Data Type": str(series.dtype),
            "Non-null": int(series.notna().sum()),
            "Missing": int(series.isna().sum()),
            "Missing %": round(series.isna().mean() * 100, 2),
            "Unique Values": int(series.nunique(dropna=True))
        })

    else:

        profile_rows.append({
            "Field": label,
            "Column": column,
            "Data Type": "NOT FOUND",
            "Non-null": 0,
            "Missing": len(df),
            "Missing %": 100.0,
            "Unique Values": 0
        })

profile = pd.DataFrame(profile_rows)

print(
    profile.to_string(index=False)
)

# ------------------------------------------------------------
# 5. Show sample values
# ------------------------------------------------------------

print("\n")
print("=" * 70)
print("SAMPLE VALUES")
print("=" * 70)

for label, column in fields.items():

    if column not in df.columns:
        continue

    print(f"\n--- {label} ---")

    values = (
        df[column]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .head(5)
        .tolist()
    )

    if values:
        for value in values:
            print(value)
    else:
        print("NO NON-MISSING VALUES")

# ------------------------------------------------------------
# 6. Numeric field summaries
# ------------------------------------------------------------

numeric_fields = [
    "releases/0/tender/value/amount",
    "releases/0/awards/0/value/amount"
]

print("\n")
print("=" * 70)
print("NUMERIC FIELD SUMMARY")
print("=" * 70)

for column in numeric_fields:

    if column not in df.columns:
        continue

    values = pd.to_numeric(df[column], errors="coerce")

    print(f"\n--- {column} ---")
    print(values.describe())

# ------------------------------------------------------------
# 7. Save profile
# ------------------------------------------------------------

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

output_file = OUTPUT_DIR / "procurement_field_profile.csv"

profile.to_csv(output_file, index=False)

print("\n")
print("=" * 70)
print("PROFILE COMPLETE")
print("=" * 70)

print(f"\nProfile saved to:")
print(output_file)