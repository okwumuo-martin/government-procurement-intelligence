from pathlib import Path
import pandas as pd

# ============================================================
# VALIDATE PROCUREMENT REVIEW INDICATOR
# ============================================================

project_root = Path(__file__).resolve().parents[1]

input_path = (
    project_root
    / "data"
    / "processed"
    / "analysis"
    / "procurement_review_indicator.csv"
)

if not input_path.exists():
    raise FileNotFoundError(f"File not found: {input_path}")

df = pd.read_csv(input_path)

print("=" * 70)
print("PROCUREMENT REVIEW INDICATOR VALIDATION")
print("=" * 70)

print(f"\nRecords: {len(df):,}")
print(f"Columns: {len(df.columns):,}")

# ------------------------------------------------------------
# 1. Score distribution
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("1. PRI SCORE DISTRIBUTION")
print("=" * 70)

score_summary = (
    df["pri_score"]
    .value_counts()
    .sort_index()
    .rename_axis("pri_score")
    .reset_index(name="records")
)

score_summary["percentage"] = (
    score_summary["records"]
    / len(df)
    * 100
)

print(score_summary.to_string(index=False))

# ------------------------------------------------------------
# 2. Category distribution
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("2. PRI CATEGORY DISTRIBUTION")
print("=" * 70)

category_summary = (
    df["pri_category"]
    .value_counts()
    .reset_index()
)

category_summary.columns = [
    "pri_category",
    "records"
]

category_summary["percentage"] = (
    category_summary["records"]
    / len(df)
    * 100
)

print(category_summary.to_string(index=False))

# ------------------------------------------------------------
# 3. Score components
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("3. PRI SCORE COMPONENTS")
print("=" * 70)

components = [
    "value_points",
    "duration_points",
    "method_points",
    "single_supplier_points",
    "supplier_data_quality_points"
]

for column in components:

    count = (df[column] > 0).sum()

    print(
        f"{column:<35} "
        f"{count:>7,} records "
        f"({count / len(df) * 100:.2f}%)"
    )

# ------------------------------------------------------------
# 4. Score by component combination
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("4. PRI SCORE COMPONENT COMBINATIONS")
print("=" * 70)

combination_columns = [
    "value_points",
    "duration_points",
    "method_points",
    "single_supplier_points",
    "supplier_data_quality_points"
]

combination_summary = (
    df.groupby(combination_columns)
    .size()
    .reset_index(name="records")
    .sort_values(
        ["records"],
        ascending=False
    )
)

print(
    combination_summary.head(20).to_string(index=False)
)

# ------------------------------------------------------------
# 5. Review categories by procurement method
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("5. REVIEW CATEGORIES BY PROCUREMENT METHOD")
print("=" * 70)

method_review = pd.crosstab(
    df["procurement_method"].fillna("Unknown"),
    df["pri_category"]
)

print(method_review.to_string())

# ------------------------------------------------------------
# 6. Moderate and High review buyers
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("6. TOP BUYERS WITH MODERATE/HIGH REVIEW RECORDS")
print("=" * 70)

review_df = df[
    df["pri_score"] >= 3
].copy()

buyer_review = (
    review_df
    .groupby("buyer_name")
    .agg(
        review_records=("award_id", "count"),
        total_allocated_award_value=("award_value", "sum"),
        max_pri_score=("pri_score", "max")
    )
    .sort_values(
        ["review_records", "total_allocated_award_value"],
        ascending=False
    )
)

print(
    buyer_review.head(25).to_string()
)

# ------------------------------------------------------------
# 7. Supplier data-quality impact
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("7. SUPPLIER DATA-QUALITY FLAGS")
print("=" * 70)

quality_summary = (
    df.groupby(
        "supplier_data_quality_points"
    )
    .agg(
        records=("award_id", "count"),
        average_pri_score=("pri_score", "mean"),
        maximum_pri_score=("pri_score", "max")
    )
)

print(quality_summary.to_string())

# ------------------------------------------------------------
# 8. Top review candidates
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("8. TOP PROCUREMENT REVIEW CANDIDATES")
print("=" * 70)

review_columns = [
    "award_id",
    "buyer_name",
    "procurement_category",
    "procurement_method",
    "award_date",
    "award_value",
    "duration_years",
    "usable_supplier_count",
    "value_points",
    "duration_points",
    "method_points",
    "single_supplier_points",
    "supplier_data_quality_points",
    "pri_score",
    "pri_category"
]

top_candidates = (
    df[df["pri_score"] >= 3]
    [review_columns]
    .sort_values(
        ["pri_score", "award_value"],
        ascending=[False, False]
    )
)

print(
    top_candidates.head(50).to_string(index=False)
)

print("\n" + "=" * 70)
print("VALIDATION COMPLETE")
print("=" * 70)