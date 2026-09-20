"""
Analysis 03B: Buyer Activity Segmentation
Government Procurement Intelligence

Purpose:
    Segment buyer organisations by procurement activity and allocated value.

Activity bands:
    1 award
    2-9 awards
    10-49 awards
    50-199 awards
    200+ awards

Value bands:
    <£100K
    £100K-<£1M
    £1M-<£10M
    £10M-<£100M
    £100M-<£1B
    £1B+

Outputs:
    buyer_activity_band_summary.csv
    buyer_activity_segments.csv
    buyer_activity_value_matrix.csv
    buyer_activity_segment_summary.csv
    buyer_activity_outliers.csv
    dashboard_ready_metrics.csv

Authoritative source:
    data/processed/analysis/buyer_organisation/buyer_overview.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# 1. PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "analysis"
    / "buyer_organisation"
    / "buyer_overview.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "analysis"
    / "buyer_activity_segmentation"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. EXPECTED BASELINE
# ============================================================

EXPECTED_BUYERS = 5_980
EXPECTED_AWARDS = 45_011
EXPECTED_VALUE = 449_812_420_123.60


# ============================================================
# 3. LOAD DATA
# ============================================================

print("=" * 70)
print("ANALYSIS 03B: BUYER ACTIVITY SEGMENTATION")
print("=" * 70)

print("\nLoading buyer overview...")

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"\nInput file not found:\n{INPUT_FILE}\n\n"
        "Check that Analysis 03 was completed successfully."
    )

df = pd.read_csv(INPUT_FILE)

print(f"Buyer records loaded: {len(df):,}")
print(f"Columns available: {len(df.columns)}")


# ============================================================
# 4. STANDARDISE COLUMN NAMES
# ============================================================

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_", regex=False)
)


# ============================================================
# 5. CHECK SOURCE SCHEMA
# ============================================================

required_columns = [
    "buyer_key",
    "buyer_name",
    "award_count",
    "allocated_award_value"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        "\nMissing required columns:\n"
        f"{missing_columns}\n\n"
        "Available columns are:\n"
        f"{df.columns.tolist()}"
    )

print("Source schema validation: PASSED")


# ============================================================
# 6. STANDARDISE ANALYTICAL VALUE COLUMN
# ============================================================

df = df.rename(
    columns={
        "allocated_award_value": "allocated_value"
    }
)


# ============================================================
# 7. CLEAN NUMERIC FIELDS
# ============================================================

df["award_count"] = pd.to_numeric(
    df["award_count"],
    errors="coerce"
)

df["allocated_value"] = pd.to_numeric(
    df["allocated_value"],
    errors="coerce"
)

if df["award_count"].isna().any():
    missing_count = df["award_count"].isna().sum()

    raise ValueError(
        f"award_count contains {missing_count:,} missing values."
    )

if df["allocated_value"].isna().any():
    missing_value = df["allocated_value"].isna().sum()

    print(
        f"Warning: allocated_value contains "
        f"{missing_value:,} missing values. "
        "These will be treated as zero."
    )

    df["allocated_value"] = df["allocated_value"].fillna(0)


# ============================================================
# 8. VALIDATE BUYER GRAIN
# ============================================================

print("\nValidating buyer grain...")

duplicate_keys = df["buyer_key"].duplicated().sum()

if duplicate_keys > 0:
    raise ValueError(
        f"buyer_key is not unique. "
        f"Duplicate records: {duplicate_keys:,}"
    )

print("Buyer key uniqueness: PASSED")


# ============================================================
# 9. BASELINE VALIDATION
# ============================================================

buyer_count = len(df)
award_total = int(df["award_count"].sum())
value_total = float(df["allocated_value"].sum())

print("\nBaseline totals:")
print(f"Unique buyer entities: {buyer_count:,}")
print(f"Total awards:          {award_total:,}")
print(f"Allocated value:       £{value_total:,.2f}")


if buyer_count != EXPECTED_BUYERS:
    raise ValueError(
        f"Unexpected buyer count: {buyer_count:,}. "
        f"Expected {EXPECTED_BUYERS:,}."
    )


if award_total != EXPECTED_AWARDS:
    raise ValueError(
        f"Unexpected award count: {award_total:,}. "
        f"Expected {EXPECTED_AWARDS:,}."
    )


if not np.isclose(
    value_total,
    EXPECTED_VALUE,
    rtol=0,
    atol=1
):
    raise ValueError(
        f"Unexpected allocated value: £{value_total:,.2f}. "
        f"Expected £{EXPECTED_VALUE:,.2f}."
    )


print("Baseline validation: PASSED")


# ============================================================
# 10. CREATE ACTIVITY BANDS
# ============================================================

def create_activity_band(award_count):
    """
    Assign a buyer to an operational activity band.
    """

    if award_count == 1:
        return "1 award"

    if 2 <= award_count <= 9:
        return "2-9 awards"

    if 10 <= award_count <= 49:
        return "10-49 awards"

    if 50 <= award_count <= 199:
        return "50-199 awards"

    return "200+ awards"


df["activity_band"] = (
    df["award_count"]
    .apply(create_activity_band)
)


activity_order = [
    "1 award",
    "2-9 awards",
    "10-49 awards",
    "50-199 awards",
    "200+ awards"
]

df["activity_band"] = pd.Categorical(
    df["activity_band"],
    categories=activity_order,
    ordered=True
)


# ============================================================
# 11. CREATE VALUE BANDS
# ============================================================

def create_value_band(value):
    """
    Assign a buyer to a value band based on
    total allocated award value.
    """

    if value < 100_000:
        return "<£100K"

    if value < 1_000_000:
        return "£100K-<£1M"

    if value < 10_000_000:
        return "£1M-<£10M"

    if value < 100_000_000:
        return "£10M-<£100M"

    if value < 1_000_000_000:
        return "£100M-<£1B"

    return "£1B+"


df["value_band"] = (
    df["allocated_value"]
    .apply(create_value_band)
)


value_order = [
    "<£100K",
    "£100K-<£1M",
    "£1M-<£10M",
    "£10M-<£100M",
    "£100M-<£1B",
    "£1B+"
]

df["value_band"] = pd.Categorical(
    df["value_band"],
    categories=value_order,
    ordered=True
)


# ============================================================
# 12. ACTIVITY BAND SUMMARY
# ============================================================

print("\nCreating activity-band summary...")

activity_summary = (
    df.groupby(
        "activity_band",
        observed=False
    )
    .agg(
        buyer_count=("buyer_key", "nunique"),
        award_count=("award_count", "sum"),
        allocated_value=("allocated_value", "sum"),
        median_buyer_value=("allocated_value", "median"),
        mean_buyer_value=("allocated_value", "mean"),
        median_awards_per_buyer=("award_count", "median"),
        mean_awards_per_buyer=("award_count", "mean")
    )
    .reset_index()
)

activity_summary["buyer_share"] = (
    activity_summary["buyer_count"]
    / buyer_count
    * 100
)

activity_summary["award_share"] = (
    activity_summary["award_count"]
    / award_total
    * 100
)

activity_summary["value_share"] = (
    activity_summary["allocated_value"]
    / value_total
    * 100
)


# ============================================================
# 13. ACTIVITY × VALUE MATRIX
# ============================================================

print("\nCreating activity × value matrix...")

activity_value_matrix = (
    df.groupby(
        ["activity_band", "value_band"],
        observed=False
    )
    .agg(
        buyer_count=("buyer_key", "nunique"),
        award_count=("award_count", "sum"),
        allocated_value=("allocated_value", "sum")
    )
    .reset_index()
)

activity_value_matrix["buyer_share"] = (
    activity_value_matrix["buyer_count"]
    / buyer_count
    * 100
)

activity_value_matrix["award_share"] = (
    activity_value_matrix["award_count"]
    / award_total
    * 100
)

activity_value_matrix["value_share"] = (
    activity_value_matrix["allocated_value"]
    / value_total
    * 100
)


# ============================================================
# 14. CREATE BUYER-LEVEL SEGMENTS
# ============================================================

def create_buyer_segment(row):
    """
    Combine activity and value into four business segments.

    High activity:
        50+ awards

    High value:
        £100M+ allocated value
    """

    high_activity = row["activity_band"] in [
        "50-199 awards",
        "200+ awards"
    ]

    high_value = row["value_band"] in [
        "£100M-<£1B",
        "£1B+"
    ]

    if high_activity and high_value:
        return "High activity / High value"

    if high_activity and not high_value:
        return "High activity / Lower value"

    if not high_activity and high_value:
        return "Lower activity / High value"

    return "Lower activity / Lower value"


df["buyer_segment"] = df.apply(
    create_buyer_segment,
    axis=1
)


segment_order = [
    "High activity / High value",
    "High activity / Lower value",
    "Lower activity / High value",
    "Lower activity / Lower value"
]


# ============================================================
# 15. BUYER SEGMENT SUMMARY
# ============================================================

print("\nCreating buyer segment summary...")

segment_summary = (
    df.groupby(
        "buyer_segment",
        observed=False
    )
    .agg(
        buyer_count=("buyer_key", "nunique"),
        award_count=("award_count", "sum"),
        allocated_value=("allocated_value", "sum"),
        median_awards_per_buyer=("award_count", "median"),
        median_buyer_value=("allocated_value", "median")
    )
    .reset_index()
)

segment_summary["buyer_share"] = (
    segment_summary["buyer_count"]
    / buyer_count
    * 100
)

segment_summary["award_share"] = (
    segment_summary["award_count"]
    / award_total
    * 100
)

segment_summary["value_share"] = (
    segment_summary["allocated_value"]
    / value_total
    * 100
)

segment_summary["segment_order"] = (
    segment_summary["buyer_segment"]
    .map(
        {
            segment: position
            for position, segment
            in enumerate(segment_order)
        }
    )
)

segment_summary = (
    segment_summary
    .sort_values("segment_order")
    .drop(columns="segment_order")
)


# ============================================================
# 16. BUYER OUTLIERS
# ============================================================

print("\nIdentifying buyer-level outliers...")

outliers = df[
    df["buyer_segment"].isin(
        [
            "High activity / High value",
            "Lower activity / High value",
            "High activity / Lower value"
        ]
    )
].copy()

outliers = outliers.sort_values(
    ["allocated_value", "award_count"],
    ascending=[False, False]
)

outliers = outliers[
    [
        "buyer_key",
        "buyer_name",
        "award_count",
        "allocated_value",
        "activity_band",
        "value_band",
        "buyer_segment"
    ]
]


# ============================================================
# 17. DASHBOARD-READY METRICS
# ============================================================

print("\nCreating dashboard-ready metrics...")

metrics = []


def add_metric(
    metric,
    value,
    unit,
    definition
):
    metrics.append(
        {
            "metric": metric,
            "value": value,
            "unit": unit,
            "definition": definition
        }
    )


add_metric(
    "Unique buyer entities",
    buyer_count,
    "count",
    "Distinct buyer entities represented in the buyer analytical layer."
)

add_metric(
    "Total awards",
    award_total,
    "count",
    "Total award records represented in the buyer analytical layer."
)

add_metric(
    "Allocated award value",
    value_total,
    "GBP",
    "Total allocated award value represented in the buyer analytical layer."
)

add_metric(
    "Median awards per buyer",
    df["award_count"].median(),
    "awards",
    "Median number of awards associated with a buyer entity."
)

add_metric(
    "Median allocated value per buyer",
    df["allocated_value"].median(),
    "GBP",
    "Median allocated award value associated with a buyer entity."
)

add_metric(
    "One-award buyers",
    int(
        (
            df["activity_band"]
            == "1 award"
        ).sum()
    ),
    "buyers",
    "Buyer entities associated with exactly one award."
)

add_metric(
    "High-activity buyers",
    int(
        df["activity_band"].isin(
            [
                "50-199 awards",
                "200+ awards"
            ]
        ).sum()
    ),
    "buyers",
    "Buyer entities associated with at least 50 awards."
)

add_metric(
    "Very-high-activity buyers",
    int(
        (
            df["activity_band"]
            == "200+ awards"
        ).sum()
    ),
    "buyers",
    "Buyer entities associated with 200 or more awards."
)

add_metric(
    "High-value buyers",
    int(
        df["value_band"].isin(
            [
                "£100M-<£1B",
                "£1B+"
            ]
        ).sum()
    ),
    "buyers",
    "Buyer entities with at least £100M in allocated award value."
)

add_metric(
    "£1B+ buyers",
    int(
        (
            df["value_band"]
            == "£1B+"
        ).sum()
    ),
    "buyers",
    "Buyer entities with at least £1B in allocated award value."
)

add_metric(
    "High activity / High value buyers",
    int(
        (
            df["buyer_segment"]
            == "High activity / High value"
        ).sum()
    ),
    "buyers",
    "Buyer entities with at least 50 awards and at least £100M allocated value."
)

add_metric(
    "Lower activity / High value buyers",
    int(
        (
            df["buyer_segment"]
            == "Lower activity / High value"
        ).sum()
    ),
    "buyers",
    "Buyer entities with fewer than 50 awards but at least £100M allocated value."
)


dashboard_metrics = pd.DataFrame(metrics)


# ============================================================
# 18. VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

summary_buyers = int(
    activity_summary["buyer_count"].sum()
)

summary_awards = int(
    activity_summary["award_count"].sum()
)

summary_value = float(
    activity_summary["allocated_value"].sum()
)

print(
    f"Activity bands — buyers: {summary_buyers:,}"
)

print(
    f"Activity bands — awards: {summary_awards:,}"
)

print(
    f"Activity bands — value: £{summary_value:,.2f}"
)


if summary_buyers != buyer_count:
    raise ValueError(
        "Activity-band buyer counts do not reconcile."
    )

if summary_awards != award_total:
    raise ValueError(
        "Activity-band award counts do not reconcile."
    )

if not np.isclose(
    summary_value,
    value_total,
    rtol=0,
    atol=1
):
    raise ValueError(
        "Activity-band allocated value does not reconcile."
    )


segment_buyers = int(
    segment_summary["buyer_count"].sum()
)

segment_awards = int(
    segment_summary["award_count"].sum()
)

segment_value = float(
    segment_summary["allocated_value"].sum()
)


if segment_buyers != buyer_count:
    raise ValueError(
        "Buyer segment counts do not reconcile."
    )

if segment_awards != award_total:
    raise ValueError(
        "Buyer segment award counts do not reconcile."
    )

if not np.isclose(
    segment_value,
    value_total,
    rtol=0,
    atol=1
):
    raise ValueError(
        "Buyer segment value does not reconcile."
    )


print("Activity-band reconciliation: PASSED")
print("Buyer-segment reconciliation: PASSED")


# ============================================================
# 19. SAVE OUTPUTS
# ============================================================

activity_summary.to_csv(
    OUTPUT_DIR
    / "buyer_activity_band_summary.csv",
    index=False
)

df.to_csv(
    OUTPUT_DIR
    / "buyer_activity_segments.csv",
    index=False
)

activity_value_matrix.to_csv(
    OUTPUT_DIR
    / "buyer_activity_value_matrix.csv",
    index=False
)

segment_summary.to_csv(
    OUTPUT_DIR
    / "buyer_activity_segment_summary.csv",
    index=False
)

outliers.to_csv(
    OUTPUT_DIR
    / "buyer_activity_outliers.csv",
    index=False
)

dashboard_metrics.to_csv(
    OUTPUT_DIR
    / "dashboard_ready_metrics.csv",
    index=False
)


# ============================================================
# 20. PRINT ACTIVITY SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("BUYER ACTIVITY BAND SUMMARY")
print("=" * 70)

display_summary = activity_summary.copy()

display_summary["allocated_value"] = (
    display_summary["allocated_value"]
    .map(lambda x: f"£{x:,.2f}")
)

display_summary["buyer_share"] = (
    display_summary["buyer_share"]
    .map(lambda x: f"{x:.2f}%")
)

display_summary["award_share"] = (
    display_summary["award_share"]
    .map(lambda x: f"{x:.2f}%")
)

display_summary["value_share"] = (
    display_summary["value_share"]
    .map(lambda x: f"{x:.2f}%")
)

print(
    display_summary[
        [
            "activity_band",
            "buyer_count",
            "award_count",
            "allocated_value",
            "buyer_share",
            "award_share",
            "value_share"
        ]
    ].to_string(index=False)
)


# ============================================================
# 21. PRINT BUYER SEGMENTS
# ============================================================

print("\n" + "=" * 70)
print("BUYER VALUE × ACTIVITY SEGMENTS")
print("=" * 70)

display_segments = segment_summary.copy()

display_segments["allocated_value"] = (
    display_segments["allocated_value"]
    .map(lambda x: f"£{x:,.2f}")
)

display_segments["buyer_share"] = (
    display_segments["buyer_share"]
    .map(lambda x: f"{x:.2f}%")
)

display_segments["award_share"] = (
    display_segments["award_share"]
    .map(lambda x: f"{x:.2f}%")
)

display_segments["value_share"] = (
    display_segments["value_share"]
    .map(lambda x: f"{x:.2f}%")
)

print(
    display_segments[
        [
            "buyer_segment",
            "buyer_count",
            "award_count",
            "allocated_value",
            "buyer_share",
            "award_share",
            "value_share"
        ]
    ].to_string(index=False)
)


# ============================================================
# 22. PRINT TOP OUTLIERS
# ============================================================

print("\n" + "=" * 70)
print("TOP BUYER OUTLIERS")
print("=" * 70)

print(
    outliers
    .head(15)
    .to_string(index=False)
)


# ============================================================
# 23. PRINT DASHBOARD METRICS
# ============================================================

print("\n" + "=" * 70)
print("DASHBOARD-READY KPI METRICS")
print("=" * 70)

for _, row in dashboard_metrics.iterrows():

    value = row["value"]

    if row["unit"] == "GBP":
        formatted = f"£{value:,.2f}"

    elif row["unit"] in ["count", "buyers"]:
        formatted = f"{int(value):,}"

    elif row["unit"] == "awards":
        formatted = f"{value:,.2f}"

    else:
        formatted = str(value)

    print(
        f"{row['metric']}: {formatted}"
    )


# ============================================================
# 24. COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("ANALYSIS 03B COMPLETE")
print("=" * 70)

print(
    "\nOutputs saved to:"
)

print(OUTPUT_DIR)