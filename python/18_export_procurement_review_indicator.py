from pathlib import Path
import sqlite3
import pandas as pd
import re

# ============================================================
# EXPORT QUERY 13 — PROCUREMENT REVIEW INDICATOR
# ============================================================

# Project paths
project_root = Path(__file__).resolve().parents[1]

db_path = project_root / "data" / "database" / "procurement_2025.db"
sql_path = project_root / "sql" / "05_risk_analysis.sql"

output_dir = project_root / "data" / "processed" / "analysis"
output_dir.mkdir(parents=True, exist_ok=True)

output_path = output_dir / "procurement_review_indicator.csv"

print("=" * 70)
print("EXPORT PROCUREMENT REVIEW INDICATOR")
print("=" * 70)

# ------------------------------------------------------------
# 1. Check required files
# ------------------------------------------------------------

if not db_path.exists():
    raise FileNotFoundError(f"Database not found: {db_path}")

if not sql_path.exists():
    raise FileNotFoundError(f"SQL file not found: {sql_path}")

print(f"\nDatabase:")
print(db_path)

print(f"\nSQL file:")
print(sql_path)

# ------------------------------------------------------------
# 2. Read SQL file
# ------------------------------------------------------------

sql_text = sql_path.read_text(encoding="utf-8")

# Extract Query 13
match = re.search(
    r"--\s*QUERY\s+13\b(.*?)(?=--\s*QUERY\s+14\b|\Z)",
    sql_text,
    flags=re.IGNORECASE | re.DOTALL
)

if not match:
    raise ValueError(
        "Could not locate QUERY 13 in 05_risk_analysis.sql"
    )

query_13 = match.group(1).strip()

print("\nQuery 13 successfully extracted.")

# ------------------------------------------------------------
# 3. Execute Query 13
# ------------------------------------------------------------

print("\nExecuting Query 13...")

conn = sqlite3.connect(db_path)

try:
    result = pd.read_sql_query(query_13, conn)
finally:
    conn.close()

# ------------------------------------------------------------
# 4. Validate result
# ------------------------------------------------------------

print("\nQuery 13 result:")
print(f"Rows:    {len(result):,}")
print(f"Columns: {len(result.columns):,}")

if len(result) == 0:
    raise ValueError("Query 13 returned zero rows.")

# ------------------------------------------------------------
# 5. Display PRI category distribution
# ------------------------------------------------------------

if "pri_category" in result.columns:

    print("\nPRI category distribution:")

    category_counts = (
        result["pri_category"]
        .value_counts(dropna=False)
        .rename_axis("pri_category")
        .reset_index(name="count")
    )

    category_counts["percentage"] = (
        category_counts["count"]
        / len(result)
        * 100
    )

    print(category_counts.to_string(index=False))

# ------------------------------------------------------------
# 6. Display PRI score distribution
# ------------------------------------------------------------

if "pri_score" in result.columns:

    print("\nPRI score distribution:")

    score_counts = (
        result["pri_score"]
        .value_counts()
        .sort_index()
        .rename_axis("pri_score")
        .reset_index(name="count")
    )

    score_counts["percentage"] = (
        score_counts["count"]
        / len(result)
        * 100
    )

    print(score_counts.to_string(index=False))

# ------------------------------------------------------------
# 7. Save complete result
# ------------------------------------------------------------

result.to_csv(output_path, index=False)

print("\n" + "=" * 70)
print("EXPORT COMPLETE")
print("=" * 70)

print(f"\nSaved to:")
print(output_path)

print(f"\nRows exported: {len(result):,}")
print(f"Columns exported: {len(result.columns):,}")

print("\nFile exists:", output_path.exists())