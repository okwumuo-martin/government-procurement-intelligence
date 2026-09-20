
"""
25_consolidate_dashboard_metrics.py

Government Procurement Intelligence
Final Dashboard Consolidation Layer

Purpose
-------
Combine the already-validated analytical outputs into one controlled,
dashboard-ready package.

Important methodological rules
------------------------------
1. Do NOT independently recreate the Procurement Review Indicator (PRI).
   The authoritative PRI values come from:
       data/processed/analysis/procurement_analytical_dataset.csv

2. Supplier concentration is based on allocated supplier value among
   awards with usable supplier relationships.

3. Multi-supplier award value is allocated equally across usable
   supplier relationships.

4. Buyer analysis uses buyer entities / buyer_key rather than raw
   buyer names.

5. Allocated award value represents award value in the dataset.
   It is NOT actual supplier payment or government expenditure.

6. PRI categories are screening indicators only. They do not establish
   fraud, corruption, wrongdoing, or probability of wrongdoing.

Output
------
All dashboard-ready files are written to:

    data/processed/analysis/dashboard/
"""

from pathlib import Path

import numpy as np
import pandas as pd


# =====================================================================
# 1. PROJECT PATHS
# =====================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ANALYSIS_DIR = PROJECT_ROOT / "data" / "processed" / "analysis"

OUTPUT_DIR = ANALYSIS_DIR / "dashboard"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ANALYTICAL_FILE = (
    ANALYSIS_DIR / "procurement_analytical_dataset.csv"
)

SUPPLIER_DIR = ANALYSIS_DIR / "supplier_concentration"

BUYER_DIR = ANALYSIS_DIR / "buyer_organisation"

ACTIVITY_DIR = (
    ANALYSIS_DIR / "buyer_activity_segmentation"
)


# =====================================================================
# 2. EXPECTED VALIDATED BASELINE
# =====================================================================

EXPECTED_AWARDS = 45_011

EXPECTED_BUYERS = 5_980

EXPECTED_VALUE = 449_812_420_123.60

EXPECTED_PRIORITY = 4

EXPECTED_HIGH = 51


# =====================================================================
# 3. INPUT FILES
# =====================================================================

SUPPLIER_CONCENTRATION_FILE = (
    SUPPLIER_DIR / "supplier_concentration.csv"
)

SUPPLIER_STRUCTURE_FILE = (
    SUPPLIER_DIR / "supplier_structure_summary.csv"
)

SUPPLIER_VALUE_DIST_FILE = (
    SUPPLIER_DIR / "supplier_value_distribution.csv"
)

SUPPLIER_SUMMARY_FILE = (
    SUPPLIER_DIR / "supplier_summary.csv"
)

BUYER_OVERVIEW_FILE = (
    BUYER_DIR / "buyer_overview.csv"
)

BUYER_TOP_VALUE_FILE = (
    BUYER_DIR / "top_buyers_by_value.csv"
)

BUYER_TOP_COUNT_FILE = (
    BUYER_DIR / "top_buyers_by_count.csv"
)

BUYER_METHOD_FILE = (
    BUYER_DIR / "buyer_procurement_method.csv"
)

BUYER_DIRECT_LIMITED_FILE = (
    BUYER_DIR / "buyer_direct_limited_exposure.csv"
)

BUYER_LONG_DURATION_FILE = (
    BUYER_DIR / "buyer_long_duration_exposure.csv"
)

BUYER_DATA_QUALITY_FILE = (
    BUYER_DIR / "buyer_data_quality.csv"
)

ACTIVITY_BAND_FILE = (
    ACTIVITY_DIR / "buyer_activity_band_summary.csv"
)

ACTIVITY_SEGMENT_FILE = (
    ACTIVITY_DIR / "buyer_activity_segment_summary.csv"
)

ACTIVITY_MATRIX_FILE = (
    ACTIVITY_DIR / "buyer_activity_value_matrix.csv"
)

ACTIVITY_OUTLIER_FILE = (
    ACTIVITY_DIR / "buyer_activity_outliers.csv"
)

ACTIVITY_KPI_FILE = (
    ACTIVITY_DIR / "dashboard_ready_metrics.csv"
)


# =====================================================================
# 4. HELPER FUNCTIONS
# =====================================================================

def require_file(path):
    """Stop immediately if a required input file is missing."""
    if not path.exists():
        raise FileNotFoundError(
            f"\nRequired input file not found:\n{path}"
        )


def read_csv(path):
    """Read a required CSV file."""
    require_file(path)
    return pd.read_csv(path)


def save_csv(df, filename):
    """Save a dataframe into the final dashboard directory."""
    path = OUTPUT_DIR / filename
    df.to_csv(path, index=False)
    print(f"Created: {path}")
    return path


def find_column(df, candidates, description):
    """
    Find the first available column from a list of candidates.
    """
    for column in candidates:
        if column in df.columns:
            return column

    raise KeyError(
        f"\nCould not find {description}.\n"
        f"Tried: {candidates}\n"
        f"Available columns: {list(df.columns)}"
    )


def money(value):
    """Format GBP value for console output."""
    return f"£{value:,.2f}"


# =====================================================================
# 5. START
# =====================================================================

print("=" * 78)
print("FINAL DASHBOARD CONSOLIDATION")
print("=" * 78)


# =====================================================================
# 6. LOAD AUTHORITATIVE ANALYTICAL DATASET
# =====================================================================

print("\n[1/15] Loading authoritative analytical dataset...")

analytical = read_csv(ANALYTICAL_FILE)

print(f"Records loaded: {len(analytical):,}")


# =====================================================================
# 7. VALIDATE ANALYTICAL DATASET
# =====================================================================

print("\n[2/15] Validating analytical baseline...")

if len(analytical) != EXPECTED_AWARDS:
    raise ValueError(
        f"Award count mismatch.\n"
        f"Expected: {EXPECTED_AWARDS:,}\n"
        f"Found:    {len(analytical):,}"
    )


if "award_value" not in analytical.columns:
    raise KeyError(
        "The analytical dataset does not contain 'award_value'."
    )


analytical["award_value"] = pd.to_numeric(
    analytical["award_value"],
    errors="coerce"
)

valid_award_value = analytical["award_value"].dropna()

total_award_value = valid_award_value.sum()


if not np.isclose(
    total_award_value,
    EXPECTED_VALUE,
    atol=0.01
):
    raise ValueError(
        f"Allocated value mismatch.\n"
        f"Expected: {EXPECTED_VALUE:,.2f}\n"
        f"Found:    {total_award_value:,.2f}"
    )


print(
    f"Validated awards:        {len(analytical):,}"
)

print(
    f"Validated allocated value: {money(total_award_value)}"
)

print("Analytical baseline validation: PASSED")


# =====================================================================
# 8. CREATE EXECUTIVE KPI FILE
# =====================================================================

print("\n[3/15] Creating dashboard KPI layer...")

# PRI must come directly from the authoritative analytical dataset.

if "pri_category" not in analytical.columns:
    raise KeyError(
        "Authoritative PRI category column 'pri_category' "
        "is missing from the analytical dataset."
    )


pri_score = pd.to_numeric(
    analytical.get("pri_score"),
    errors="coerce"
)


priority_count = int(
    analytical["pri_category"].eq("Priority review").sum()
)

high_count = int(
    analytical["pri_category"].eq("High review").sum()
)


if priority_count != EXPECTED_PRIORITY:
    raise ValueError(
        f"Priority PRI count mismatch. "
        f"Expected {EXPECTED_PRIORITY}, found {priority_count}."
    )


if high_count != EXPECTED_HIGH:
    raise ValueError(
        f"High PRI count mismatch. "
        f"Expected {EXPECTED_HIGH}, found {high_count}."
    )


kpi_rows = [
    {
        "metric": "unique_buyer_entities",
        "value": EXPECTED_BUYERS,
        "definition": (
            "Unique buyer entities in the validated buyer-level analysis."
        ),
    },
    {
        "metric": "total_awards",
        "value": len(analytical),
        "definition": (
            "Award records in the final analytical dataset."
        ),
    },
    {
        "metric": "allocated_award_value",
        "value": total_award_value,
        "definition": (
            "Award value represented in the analytical dataset; "
            "not actual payments."
        ),
    },
    {
        "metric": "median_award_value",
        "value": valid_award_value.median(),
        "definition": "Median allocated award value.",
    },
    {
        "metric": "mean_award_value",
        "value": valid_award_value.mean(),
        "definition": "Mean allocated award value.",
    },
    {
        "metric": "maximum_award_value",
        "value": valid_award_value.max(),
        "definition": "Maximum allocated award value.",
    },
    {
        "metric": "awards_with_missing_value",
        "value": int(
            analytical["award_value"].isna().sum()
        ),
        "definition": "Awards with missing award value.",
    },
    {
        "metric": "priority_review_records",
        "value": priority_count,
        "definition": (
            "PRI records classified Priority; "
            "screening population only."
        ),
    },
    {
        "metric": "high_review_records",
        "value": high_count,
        "definition": (
            "PRI records classified High; "
            "screening population only."
        ),
    },
    {
        "metric": "high_priority_review_records",
        "value": priority_count + high_count,
        "definition": (
            "Combined High and Priority PRI screening population."
        ),
    },
    {
        "metric": "maximum_pri_score",
        "value": pri_score.max(),
        "definition": (
            "Maximum Procurement Review Indicator score "
            "in the authoritative dataset."
        ),
    },
    {
        "metric": "missing_procurement_method",
        "value": int(
            analytical["procurement_method"].isna().sum()
        ),
        "definition": "Awards missing procurement method.",
    },
    {
        "metric": "missing_procurement_category",
        "value": int(
            analytical["procurement_category"].isna().sum()
        ),
        "definition": "Awards missing procurement category.",
    },
    {
        "metric": "missing_supplier_information",
        "value": int(
            analytical["supplier_names"].isna().sum()
        ),
        "definition": (
            "Awards without usable supplier information."
        ),
    },
]


kpi_df = pd.DataFrame(kpi_rows)

save_csv(
    kpi_df,
    "dashboard_kpis.csv"
)


# =====================================================================
# 9. PROCUREMENT METHOD SUMMARY
# =====================================================================

print("\n[4/15] Creating procurement method layer...")

if "procurement_method_group" not in analytical.columns:
    raise KeyError(
        "procurement_method_group is missing from "
        "the analytical dataset."
    )


method_df = analytical.copy()

method_df["procurement_method_group"] = (
    method_df["procurement_method_group"]
    .fillna("Unknown")
)


method_summary = (
    method_df
    .groupby("procurement_method_group", dropna=False)
    .agg(
        award_count=("award_value", "size"),
        allocated_value=("award_value", "sum"),
        median_award_value=("award_value", "median"),
    )
    .reset_index()
)


method_summary["award_share_percent"] = (
    method_summary["award_count"]
    / len(analytical)
    * 100
)


method_summary["value_share_percent"] = (
    method_summary["allocated_value"]
    / total_award_value
    * 100
)


method_summary = method_summary.sort_values(
    "allocated_value",
    ascending=False
)


save_csv(
    method_summary,
    "dashboard_procurement_method.csv"
)


# =====================================================================
# 10. AWARD VALUE DISTRIBUTION
# =====================================================================

print("\n[5/15] Creating award value distribution...")

value_bins = [
    -np.inf,
    100_000,
    1_000_000,
    10_000_000,
    100_000_000,
    1_000_000_000,
    np.inf,
]

value_labels = [
    "<£100K",
    "£100K-<£1M",
    "£1M-<£10M",
    "£10M-<£100M",
    "£100M-<£1B",
    "£1B+",
]


value_df = analytical.copy()

value_df["award_value_band"] = pd.cut(
    value_df["award_value"],
    bins=value_bins,
    labels=value_labels,
    right=False,
)

value_df["award_value_band"] = (
    value_df["award_value_band"]
    .astype("object")
    .fillna("Unknown")
)


value_distribution = (
    value_df
    .groupby(
        "award_value_band",
        observed=False
    )
    .agg(
        award_count=("award_value", "size"),
        allocated_value=("award_value", "sum"),
    )
    .reset_index()
)


value_distribution["award_share_percent"] = (
    value_distribution["award_count"]
    / len(analytical)
    * 100
)


value_distribution["value_share_percent"] = (
    value_distribution["allocated_value"]
    / total_award_value
    * 100
)


save_csv(
    value_distribution,
    "dashboard_value_distribution.csv"
)


# =====================================================================
# 11. CONTRACT DURATION DISTRIBUTION
# =====================================================================

print("\n[6/15] Creating contract duration distribution...")

if "contract_duration_years" not in analytical.columns:
    raise KeyError(
        "contract_duration_years is missing from "
        "the analytical dataset."
    )


duration_bins = [
    -np.inf,
    1,
    3,
    5,
    10,
    20,
    np.inf,
]

duration_labels = [
    "<1 year",
    "1-<3 years",
    "3-<5 years",
    "5-<10 years",
    "10-<20 years",
    "20+ years",
]


duration_df = analytical.copy()

duration_df["contract_duration_years"] = pd.to_numeric(
    duration_df["contract_duration_years"],
    errors="coerce"
)


duration_df["duration_band"] = pd.cut(
    duration_df["contract_duration_years"],
    bins=duration_bins,
    labels=duration_labels,
    right=False,
)


duration_df["duration_band"] = (
    duration_df["duration_band"]
    .astype("object")
    .fillna("Unknown")
)


duration_distribution = (
    duration_df
    .groupby(
        "duration_band",
        observed=False
    )
    .agg(
        award_count=("award_value", "size"),
        allocated_value=("award_value", "sum"),
    )
    .reset_index()
)


duration_distribution["award_share_percent"] = (
    duration_distribution["award_count"]
    / len(analytical)
    * 100
)


duration_distribution["value_share_percent"] = (
    duration_distribution["allocated_value"]
    / total_award_value
    * 100
)


save_csv(
    duration_distribution,
    "dashboard_duration_distribution.csv"
)


# =====================================================================
# 12. SUPPLIER LAYERS
# =====================================================================

print("\n[7/15] Loading supplier analysis outputs...")

supplier_structure = read_csv(
    SUPPLIER_STRUCTURE_FILE
)

supplier_concentration = read_csv(
    SUPPLIER_CONCENTRATION_FILE
)

supplier_value_distribution = read_csv(
    SUPPLIER_VALUE_DIST_FILE
)

supplier_summary = read_csv(
    SUPPLIER_SUMMARY_FILE
)


save_csv(
    supplier_structure,
    "dashboard_supplier_structure.csv"
)

save_csv(
    supplier_concentration,
    "dashboard_supplier_concentration.csv"
)

save_csv(
    supplier_value_distribution,
    "dashboard_supplier_value_distribution.csv"
)

save_csv(
    supplier_summary,
    "dashboard_supplier_summary.csv"
)


# =====================================================================
# 13. BUYER ACTIVITY LAYERS
# =====================================================================

print("\n[8/15] Loading buyer activity outputs...")

activity_band = read_csv(
    ACTIVITY_BAND_FILE
)

activity_segment = read_csv(
    ACTIVITY_SEGMENT_FILE
)

activity_matrix = read_csv(
    ACTIVITY_MATRIX_FILE
)

activity_outliers = read_csv(
    ACTIVITY_OUTLIER_FILE
)


save_csv(
    activity_band,
    "dashboard_buyer_activity_bands.csv"
)

save_csv(
    activity_segment,
    "dashboard_buyer_segments.csv"
)

save_csv(
    activity_matrix,
    "dashboard_buyer_activity_value_matrix.csv"
)

save_csv(
    activity_outliers,
    "dashboard_buyer_outliers.csv"
)


# =====================================================================
# 14. BUYER KPI CROSS-CHECK
# =====================================================================

print("\n[9/15] Validating buyer activity outputs...")

activity_kpis = read_csv(
    ACTIVITY_KPI_FILE
)


metric_column = find_column(
    activity_kpis,
    ["metric", "kpi", "name"],
    "activity KPI name column"
)

value_column = find_column(
    activity_kpis,
    ["value", "metric_value", "count"],
    "activity KPI value column"
)


activity_map = dict(
    zip(
        activity_kpis[metric_column]
        .astype(str)
        .str.strip()
        .str.lower(),
        activity_kpis[value_column],
    )
)


def lookup_metric(*names):
    for name in names:
        key = name.lower()
        if key in activity_map:
            return activity_map[key]
    return None


activity_metric_map = {
    "one_award_buyers": lookup_metric(
        "one-award buyers",
        "one award buyers",
        "one_award_buyers",
    ),
    "high_activity_buyers": lookup_metric(
        "high-activity buyers",
        "high activity buyers",
        "high_activity_buyers",
    ),
    "very_high_activity_buyers": lookup_metric(
        "very-high-activity buyers",
        "very high activity buyers",
        "very_high_activity_buyers",
    ),
    "high_value_buyers": lookup_metric(
        "high-value buyers",
        "high value buyers",
        "high_value_buyers",
    ),
    "billion_plus_buyers": lookup_metric(
        "1b+ buyers",
        "billion-plus buyers",
        "billion_plus_buyers",
    ),
    "high_activity_high_value_buyers": lookup_metric(
        "high activity / high value buyers",
        "high_activity_high_value_buyers",
    ),
    "lower_activity_high_value_buyers": lookup_metric(
        "lower activity / high value buyers",
        "lower_activity_high_value_buyers",
    ),
}


# Add buyer KPIs to the master KPI file.

for metric, value in activity_metric_map.items():

    if value is None:
        continue

    matching_rows = kpi_df["metric"].eq(metric)

    if matching_rows.any():
        kpi_df.loc[
            matching_rows,
            "value"
        ] = value


save_csv(
    kpi_df,
    "dashboard_kpis.csv"
)


# =====================================================================
# 15. TOP BUYERS
# =====================================================================

print("\n[10/15] Loading top buyer outputs...")

top_buyers_value = read_csv(
    BUYER_TOP_VALUE_FILE
)

top_buyers_count = read_csv(
    BUYER_TOP_COUNT_FILE
)


save_csv(
    top_buyers_value,
    "dashboard_top_buyers_by_value.csv"
)

save_csv(
    top_buyers_count,
    "dashboard_top_buyers_by_count.csv"
)


# =====================================================================
# 16. BUYER PROCUREMENT / EXPOSURE LAYERS
# =====================================================================

print("\n[11/15] Loading buyer exposure outputs...")

buyer_method = read_csv(
    BUYER_METHOD_FILE
)

buyer_direct_limited = read_csv(
    BUYER_DIRECT_LIMITED_FILE
)

buyer_long_duration = read_csv(
    BUYER_LONG_DURATION_FILE
)

buyer_data_quality = read_csv(
    BUYER_DATA_QUALITY_FILE
)


save_csv(
    buyer_method,
    "dashboard_buyer_procurement_method.csv"
)

save_csv(
    buyer_direct_limited,
    "dashboard_buyer_direct_limited.csv"
)

save_csv(
    buyer_long_duration,
    "dashboard_buyer_long_duration.csv"
)

save_csv(
    buyer_data_quality,
    "dashboard_buyer_data_quality.csv"
)


# =====================================================================
# 17. AUTHORITATIVE PRI REVIEW POPULATION
# =====================================================================

print("\n[12/15] Creating PRI review population...")

pri_columns = [
    "award_id",
    "release_id",
    "ocid",
    "release_date",
    "award_date",
    "award_value",
    "award_title",
    "buyer_name",
    "procurement_method",
    "procurement_category",
    "contract_start",
    "contract_end",
    "contract_duration_years",
    "usable_supplier_count",
    "supplier_names",
    "supplier_reference_text_flag",
    "supplier_identity_review_flag",
    "value_points",
    "duration_points",
    "method_points",
    "single_supplier_points",
    "pri_score",
    "pri_category",
    "review_rationale",
]


missing_pri_columns = [
    column
    for column in pri_columns
    if column not in analytical.columns
]


if missing_pri_columns:

    raise KeyError(
        "Authoritative analytical dataset is missing "
        "required PRI columns:\n"
        + "\n".join(
            f"  - {column}"
            for column in missing_pri_columns
        )
    )


review_population = analytical.loc[
    analytical["pri_category"].isin(
    ["High review", "Priority review"]
    ),
    pri_columns,
].copy()


review_population = review_population.sort_values(
    by=[
        "pri_score",
        "award_value",
    ],
    ascending=[
        False,
        False,
    ],
)


save_csv(
    review_population,
    "dashboard_review_population.csv"
)


# =====================================================================
# 18. BUYER OVERVIEW COPY
# =====================================================================

print("\n[13/15] Loading buyer entity overview...")

buyer_overview = read_csv(
    BUYER_OVERVIEW_FILE
)


if len(buyer_overview) != EXPECTED_BUYERS:

    raise ValueError(
        f"Buyer entity count mismatch.\n"
        f"Expected: {EXPECTED_BUYERS:,}\n"
        f"Found:    {len(buyer_overview):,}"
    )


buyer_award_total = pd.to_numeric(
    buyer_overview["award_count"],
    errors="coerce"
).sum()


buyer_value_column = find_column(
    buyer_overview,
    [
        "allocated_award_value",
        "allocated_value",
    ],
    "buyer allocated value"
)


buyer_value_total = pd.to_numeric(
    buyer_overview[buyer_value_column],
    errors="coerce"
).sum()


if buyer_award_total != EXPECTED_AWARDS:

    raise ValueError(
        "Buyer award reconciliation failed.\n"
        f"Expected: {EXPECTED_AWARDS:,}\n"
        f"Found:    {buyer_award_total:,.0f}"
    )


if not np.isclose(
    buyer_value_total,
    EXPECTED_VALUE,
    atol=0.01,
):

    raise ValueError(
        "Buyer value reconciliation failed.\n"
        f"Expected: {EXPECTED_VALUE:,.2f}\n"
        f"Found:    {buyer_value_total:,.2f}"
    )


save_csv(
    buyer_overview,
    "dashboard_buyer_overview.csv"
)


# =====================================================================
# 19. METRIC DICTIONARY
# =====================================================================

print("\n[14/15] Creating dashboard metric dictionary...")

metric_dictionary = pd.DataFrame(
    [
        {
            "metric": "allocated_award_value",
            "category": "Financial",
            "definition": (
                "Total award value represented in the final "
                "analytical dataset."
            ),
            "unit": "GBP",
            "important_caveat": (
                "Not actual payments or expenditure."
            ),
        },
        {
            "metric": "allocated_supplier_value",
            "category": "Supplier",
            "definition": (
                "Award value allocated across usable "
                "supplier relationships."
            ),
            "unit": "GBP",
            "important_caveat": (
                "Multi-supplier awards are allocated equally "
                "across usable suppliers."
            ),
        },
        {
            "metric": "supplier_concentration_top_1_percent",
            "category": "Supplier",
            "definition": (
                "Share of allocated supplier value represented "
                "by the top 1% of usable supplier entities."
            ),
            "unit": "%",
            "important_caveat": (
                "Calculated only among awards with usable "
                "supplier relationships."
            ),
        },
        {
            "metric": "buyer_activity",
            "category": "Buyer",
            "definition": (
                "Number of awards associated with a buyer entity."
            ),
            "unit": "Count",
            "important_caveat": (
                "Buyer entity uses buyer_key rather than raw buyer name."
            ),
        },
        {
            "metric": "buyer_allocated_value",
            "category": "Buyer",
            "definition": (
                "Total allocated award value associated with "
                "a buyer entity."
            ),
            "unit": "GBP",
            "important_caveat": (
                "Award value, not actual supplier payment."
            ),
        },
        {
            "metric": "pri_score",
            "category": "Review",
            "definition": (
                "User-defined Procurement Review Indicator score."
            ),
            "unit": "Score",
            "important_caveat": (
                "Screening indicator only; not a fraud, corruption, "
                "wrongdoing, or probability score."
            ),
        },
        {
            "metric": "pri_category",
            "category": "Review",
            "definition": (
                "PRI screening category."
            ),
            "unit": "Category",
            "important_caveat": (
                "High/Priority records identify a review population; "
                "they do not establish wrongdoing."
            ),
        },
        {
            "metric": "procurement_method",
            "category": "Procurement",
            "definition": (
                "Recorded procurement method."
            ),
            "unit": "Category",
            "important_caveat": (
                "Missing method values are retained as Unknown."
            ),
        },
        {
            "metric": "contract_duration_years",
            "category": "Contract",
            "definition": (
                "Calculated contract duration."
            ),
            "unit": "Years",
            "important_caveat": (
                "Long duration alone is not evidence of a problem."
            ),
        },
        {
            "metric": "supplier_identity_review_flag",
            "category": "Data quality",
            "definition": (
                "Supplier relationship requiring identity/name "
                "variation review."
            ),
            "unit": "Flag",
            "important_caveat": (
                "Supplier identities should not be automatically merged."
            ),
        },
    ]
)


save_csv(
    metric_dictionary,
    "dashboard_metric_dictionary.csv"
)


# =====================================================================
# 20. DASHBOARD MANIFEST
# =====================================================================

print("\nCreating dashboard manifest...")

manifest = pd.DataFrame(
    [
        {
            "file": "dashboard_kpis.csv",
            "dashboard_use": "Executive KPI cards",
        },
        {
            "file": "dashboard_procurement_method.csv",
            "dashboard_use": "Procurement method mix",
        },
        {
            "file": "dashboard_value_distribution.csv",
            "dashboard_use": "Award value distribution",
        },
        {
            "file": "dashboard_duration_distribution.csv",
            "dashboard_use": "Contract duration distribution",
        },
        {
            "file": "dashboard_supplier_structure.csv",
            "dashboard_use": "Single vs multiple supplier structure",
        },
        {
            "file": "dashboard_supplier_concentration.csv",
            "dashboard_use": "Supplier concentration",
        },
        {
            "file": "dashboard_supplier_value_distribution.csv",
            "dashboard_use": "Supplier allocated-value distribution",
        },
        {
            "file": "dashboard_supplier_summary.csv",
            "dashboard_use": "Supplier summary layer",
        },
        {
            "file": "dashboard_buyer_overview.csv",
            "dashboard_use": "Buyer entity overview",
        },
        {
            "file": "dashboard_buyer_activity_bands.csv",
            "dashboard_use": "Buyer activity bands",
        },
        {
            "file": "dashboard_buyer_segments.csv",
            "dashboard_use": "Buyer activity/value segmentation",
        },
        {
            "file": "dashboard_buyer_activity_value_matrix.csv",
            "dashboard_use": "Buyer activity/value matrix",
        },
        {
            "file": "dashboard_buyer_outliers.csv",
            "dashboard_use": "Buyer-level outlier table",
        },
        {
            "file": "dashboard_top_buyers_by_value.csv",
            "dashboard_use": "Top buyers by allocated value",
        },
        {
            "file": "dashboard_top_buyers_by_count.csv",
            "dashboard_use": "Top buyers by award count",
        },
        {
            "file": "dashboard_buyer_procurement_method.csv",
            "dashboard_use": "Buyer procurement-method analysis",
        },
        {
            "file": "dashboard_buyer_direct_limited.csv",
            "dashboard_use": "Buyer direct/limited exposure",
        },
        {
            "file": "dashboard_buyer_long_duration.csv",
            "dashboard_use": "Buyer long-duration exposure",
        },
        {
            "file": "dashboard_buyer_data_quality.csv",
            "dashboard_use": "Buyer data-quality metrics",
        },
        {
            "file": "dashboard_review_population.csv",
            "dashboard_use": "High/Priority PRI review population",
        },
        {
            "file": "dashboard_metric_dictionary.csv",
            "dashboard_use": "Metric definitions and caveats",
        },
    ]
)


save_csv(
    manifest,
    "dashboard_manifest.csv"
)


# =====================================================================
# 21. FINAL RECONCILIATION
# =====================================================================

print("\n[15/15] Running final reconciliation...")

# ---------------------------------------------------------------------
# Award-level reconciliation
# ---------------------------------------------------------------------

assert len(analytical) == EXPECTED_AWARDS

assert np.isclose(
    total_award_value,
    EXPECTED_VALUE,
    atol=0.01,
)


# ---------------------------------------------------------------------
# Buyer-level reconciliation
# ---------------------------------------------------------------------

assert len(buyer_overview) == EXPECTED_BUYERS

assert buyer_award_total == EXPECTED_AWARDS

assert np.isclose(
    buyer_value_total,
    EXPECTED_VALUE,
    atol=0.01,
)


# ---------------------------------------------------------------------
# PRI reconciliation
# ---------------------------------------------------------------------

assert priority_count == EXPECTED_PRIORITY

assert high_count == EXPECTED_HIGH


# ---------------------------------------------------------------------
# Review population reconciliation
# ---------------------------------------------------------------------

assert len(review_population) == (
    EXPECTED_PRIORITY + EXPECTED_HIGH
)


# ---------------------------------------------------------------------
# Print final results
# ---------------------------------------------------------------------

print("\n" + "=" * 78)
print("FINAL CONSOLIDATION VALIDATION")
print("=" * 78)

print(
    f"Buyer entities:             {len(buyer_overview):,}"
)

print(
    f"Award records:              {len(analytical):,}"
)

print(
    f"Allocated award value:      {money(total_award_value)}"
)

print(
    f"Priority PRI records:       {priority_count:,}"
)

print(
    f"High PRI records:           {high_count:,}"
)

print(
    f"High/Priority review pool:  {len(review_population):,}"
)

print(
    f"Dashboard output directory: {OUTPUT_DIR}"
)


print("\n" + "-" * 78)
print("ALL FINAL RECONCILIATION TESTS PASSED")
print("-" * 78)

print(
    "\nThe dashboard should use ONLY the files "
    "inside the dashboard/ directory."
)

print(
    "\nFINAL DASHBOARD CONSOLIDATION COMPLETE."
)
