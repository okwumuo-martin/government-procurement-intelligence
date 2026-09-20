import pandas as pd
from pathlib import Path

# --------------------------------------------------
# 1. Locate the raw dataset
# --------------------------------------------------

file_path = Path("data/raw/Contracts Finder OCDS 2025-01-02.csv")

print("\nLoading dataset...")
df = pd.read_csv(file_path, low_memory=False)

# --------------------------------------------------
# 2. Basic dataset information
# --------------------------------------------------

print("\n" + "=" * 60)
print("DATASET OVERVIEW")
print("=" * 60)

print(f"Rows: {df.shape[0]:,}")
print(f"Columns: {df.shape[1]:,}")

# --------------------------------------------------
# 3. Column names
# --------------------------------------------------

print("\n" + "=" * 60)
print("COLUMN NAMES")
print("=" * 60)

for i, column in enumerate(df.columns, start=1):
    print(f"{i:3}. {column}")

# --------------------------------------------------
# 4. Data types
# --------------------------------------------------

print("\n" + "=" * 60)
print("DATA TYPES")
print("=" * 60)

print(df.dtypes)

# --------------------------------------------------
# 5. First five records
# --------------------------------------------------

print("\n" + "=" * 60)
print("FIRST 5 RECORDS")
print("=" * 60)

print(df.head())

# --------------------------------------------------
# 6. Missing values
# --------------------------------------------------

print("\n" + "=" * 60)
print("MISSING VALUES")
print("=" * 60)

missing = df.isnull().sum()

missing_summary = pd.DataFrame({
    "missing_count": missing,
    "missing_percentage": (missing / len(df) * 100).round(2)
})

print(
    missing_summary
    .sort_values("missing_count", ascending=False)
    .head(30)
)

# --------------------------------------------------
# 7. Duplicate rows
# --------------------------------------------------

print("\n" + "=" * 60)
print("DUPLICATES")
print("=" * 60)

print(f"Duplicate rows: {df.duplicated().sum():,}")

print("\nInspection complete.")