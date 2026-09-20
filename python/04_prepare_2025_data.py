import pandas as pd
from pathlib import Path

# ============================================================
# Government Procurement Intelligence
# Step 4: Prepare 2025 procurement data
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("GOVERNMENT PROCUREMENT INTELLIGENCE")
print("2025 DATA PREPARATION")
print("=" * 70)

# ------------------------------------------------------------
# 1. Find CSV files
# ------------------------------------------------------------

files = sorted(RAW_DIR.glob("*.csv"))

if not files:
    raise FileNotFoundError(
        "No CSV files were found in data/raw/"
    )

print(f"\nCSV files found: {len(files)}")

for file in files:
    print(f" - {file.name}")

# ------------------------------------------------------------
# 2. Read files
# ------------------------------------------------------------

dataframes = []

for file in files:

    print(f"\nReading: {file.name}")

    df = pd.read_csv(
        file,
        low_memory=False
    )

    print(
        f"Rows: {len(df):,} | "
        f"Columns: {len(df.columns):,}"
    )

    dataframes.append(df)

# ------------------------------------------------------------
# 3. Combine files
# ------------------------------------------------------------

print("\nCombining files...")

combined = pd.concat(
    dataframes,
    ignore_index=True,
    sort=False
)

print(
    f"\nCombined rows: {len(combined):,}"
)

print(
    f"Combined columns: {len(combined.columns):,}"
)

# ------------------------------------------------------------
# 4. Check OCID duplicates
# ------------------------------------------------------------

ocid_column = "releases/0/ocid"

if ocid_column in combined.columns:

    duplicate_ocids = (
        combined[ocid_column]
        .duplicated()
        .sum()
    )

    print(
        f"\nDuplicate OCIDs: "
        f"{duplicate_ocids:,}"
    )

# ------------------------------------------------------------
# 5. Save combined raw-stage file
# ------------------------------------------------------------

output_file = (
    PROCESSED_DIR /
    "contracts_finder_2025_combined.csv"
)

combined.to_csv(
    output_file,
    index=False
)

print("\n")
print("=" * 70)
print("DATA PREPARATION COMPLETE")
print("=" * 70)

print(f"\nOutput:")
print(output_file)