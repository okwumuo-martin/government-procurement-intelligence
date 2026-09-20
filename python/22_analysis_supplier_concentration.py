"""
Analysis 02: Supplier Concentration & Diversification

Purpose
-------
Analyze supplier concentration using the normalized supplier relationship
table rather than the award-level supplier_names field.

Method
------
- Use latest award versions only.
- Join awards to normalized supplier relationships.
- Exclude obvious supplier-reference/source-text records.
- Allocate each award's value equally across its usable suppliers.
- Aggregate allocated value to supplier level.
- Analyze concentration, supplier diversification, supplier size bands,
  multi-supplier awards, and supplier data quality.

Important
---------
Allocated supplier value is an analytical allocation, not actual supplier
payment/spend. For multi-supplier awards, value is divided equally among
usable suppliers to prevent double-counting.
"""

from pathlib import Path
import pandas as pd
import numpy as np


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

AWARDS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "final"
    / "award_versions_2025.csv"
)

SUPPLIER_REL_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "final"
    / "award_suppliers_2025.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "analysis"
    / "supplier_concentration"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

REFERENCE_PATTERNS = [
    "successful supplier",
    "supplier list",
    "see webpage",
    "contract award details",
    "attachments",
    "please see",
]


def is_reference_text(series):
    """
    Identify supplier-name records that are actually source/reference text
    rather than supplier identities.
    """

    text = (
        series
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    pattern = "|".join(
        pattern.replace(" ", r"\s+")
        for pattern in REFERENCE_PATTERNS
    )

    return text.str.contains(pattern, regex=True, na=False)


def print_section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ---------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------

print("=" * 70)
print("GOVERNMENT PROCUREMENT INTELLIGENCE")
print("ANALYSIS 02: SUPPLIER CONCENTRATION & DIVERSIFICATION")
print("=" * 70)

print_section("Loading datasets")

awards = pd.read_csv(AWARDS_FILE, low_memory=False)
supplier_rel = pd.read_csv(SUPPLIER_REL_FILE, low_memory=False)

print(f"Award-version records loaded:        {len(awards):,}")
print(f"Supplier relationship rows loaded:   {len(supplier_rel):,}")


# ---------------------------------------------------------------------
# Validate required columns
# ---------------------------------------------------------------------

required_award_columns = {
    "award_id",
    "release_id",
    "award_value",
    "is_latest_award_version",
}

required_supplier_columns = {
    "award_id",
    "release_id",
    "supplier_key",
    "canonical_supplier_name",
    "supplier_name",
    "supplier_id",
    "supplier_identity_flag",
    "identity_review_flag",
}

missing_award = required_award_columns - set(awards.columns)
missing_supplier = required_supplier_columns - set(supplier_rel.columns)

if missing_award:
    raise ValueError(
        f"Missing required award columns: {sorted(missing_award)}"
    )

if missing_supplier:
    raise ValueError(
        f"Missing required supplier columns: {sorted(missing_supplier)}"
    )


# ---------------------------------------------------------------------
# Keep latest award versions
# ---------------------------------------------------------------------

print_section("Preparing latest award versions")

awards["is_latest_award_version"] = pd.to_numeric(
    awards["is_latest_award_version"],
    errors="coerce"
)

latest_awards = awards[
    awards["is_latest_award_version"] == 1
].copy()

latest_awards["award_value"] = pd.to_numeric(
    latest_awards["award_value"],
    errors="coerce"
)

latest_awards = latest_awards[
    latest_awards["award_value"].notna()
    & (latest_awards["award_value"] >= 0)
].copy()

print(f"Latest awards with valid value: {len(latest_awards):,}")
print(
    f"Total award value represented: "
    f"£{latest_awards['award_value'].sum():,.2f}"
)


# ---------------------------------------------------------------------
# Prepare supplier relationships
# ---------------------------------------------------------------------

print_section("Preparing supplier relationships")

supplier_rel["supplier_reference_text_flag"] = is_reference_text(
    supplier_rel["canonical_supplier_name"]
)

# Fall back to reported supplier name if canonical name is missing.
missing_canonical = (
    supplier_rel["canonical_supplier_name"]
    .isna()
    | (
        supplier_rel["canonical_supplier_name"]
        .astype(str)
        .str.strip()
        == ""
    )
)

supplier_rel.loc[
    missing_canonical,
    "supplier_reference_text_flag"
] = is_reference_text(
    supplier_rel.loc[missing_canonical, "supplier_name"]
)

# A usable supplier must have a supplier key and a canonical name,
# and must not be obvious source/reference text.
supplier_rel["usable_supplier_flag"] = (
    supplier_rel["supplier_key"].notna()
    & supplier_rel["canonical_supplier_name"].notna()
    & (
        supplier_rel["canonical_supplier_name"]
        .astype(str)
        .str.strip()
        != ""
    )
    & (~supplier_rel["supplier_reference_text_flag"])
)

print(
    "Usable supplier relationship rows: "
    f"{supplier_rel['usable_supplier_flag'].sum():,}"
)

print(
    "Reference/source-text relationship rows: "
    f"{supplier_rel['supplier_reference_text_flag'].sum():,}"
)

print(
    "Missing/unusable supplier relationship rows: "
    f"{(~supplier_rel['usable_supplier_flag']).sum():,}"
)


# ---------------------------------------------------------------------
# Join supplier relationships to latest awards
# ---------------------------------------------------------------------

print_section("Joining suppliers to latest awards")

award_keys = latest_awards[
    [
        "award_id",
        "release_id",
        "ocid",
        "award_value",
    ]
].copy()

supplier_analysis = supplier_rel.merge(
    award_keys,
    on=["award_id", "release_id"],
    how="inner",
    validate="many_to_one",
)

print(
    f"Supplier relationships matched to latest awards: "
    f"{len(supplier_analysis):,}"
)


# ---------------------------------------------------------------------
# Keep usable suppliers
# ---------------------------------------------------------------------

supplier_analysis = supplier_analysis[
    supplier_analysis["usable_supplier_flag"]
].copy()

print(
    f"Usable supplier relationships matched to latest awards: "
    f"{len(supplier_analysis):,}"
)


# ---------------------------------------------------------------------
# Count suppliers per award
# ---------------------------------------------------------------------

print_section("Calculating multi-supplier allocation")

supplier_counts = (
    supplier_analysis
    .groupby(
        ["award_id", "release_id"],
        as_index=False
    )
    .agg(
        usable_supplier_count=(
            "supplier_key",
            "nunique"
        )
    )
)

supplier_analysis = supplier_analysis.merge(
    supplier_counts,
    on=["award_id", "release_id"],
    how="left",
    validate="many_to_one",
)

supplier_analysis["allocated_award_value"] = (
    supplier_analysis["award_value"]
    / supplier_analysis["usable_supplier_count"]
)

supplier_analysis["supplier_structure"] = np.where(
    supplier_analysis["usable_supplier_count"] > 1,
    "Multiple suppliers",
    "Single supplier",
)

print(
    f"Single-supplier award relationships: "
    f"{(supplier_analysis['usable_supplier_count'] == 1).sum():,}"
)

print(
    f"Multi-supplier award relationships: "
    f"{(supplier_analysis['usable_supplier_count'] > 1).sum():,}"
)


# ---------------------------------------------------------------------
# Supplier-level aggregation
# ---------------------------------------------------------------------

print_section("Building supplier-level analytical dataset")

supplier_summary = (
    supplier_analysis
    .groupby(
        [
            "supplier_key",
            "canonical_supplier_name",
        ],
        as_index=False
    )
    .agg(
        allocated_award_value=(
            "allocated_award_value",
            "sum"
        ),
        award_count=(
            "award_id",
            "nunique"
        ),
        buyer_count=(
            "buyer_id",
            "nunique"
        ) if "buyer_id" in supplier_analysis.columns
        else ("award_id", "nunique"),
        supplier_id_count=(
            "supplier_id",
            "nunique"
        ),
    )
)

# Add supplier quality information separately.
quality = (
    supplier_analysis
    .groupby("supplier_key", as_index=False)
    .agg(
        supplier_identity_flags=(
            "supplier_identity_flag",
            lambda x: "|".join(
                sorted(
                    set(
                        x.dropna()
                        .astype(str)
                    )
                )
            ),
        ),
        identity_review_flags=(
            "identity_review_flag",
            lambda x: "|".join(
                sorted(
                    set(
                        x.dropna()
                        .astype(str)
                    )
                )
            ),
        ),
    )
)

supplier_summary = supplier_summary.merge(
    quality,
    on="supplier_key",
    how="left",
    validate="one_to_one",
)


# ---------------------------------------------------------------------
# Rank suppliers
# ---------------------------------------------------------------------

supplier_summary = supplier_summary.sort_values(
    "allocated_award_value",
    ascending=False
).reset_index(drop=True)

supplier_summary["supplier_rank"] = (
    supplier_summary.index + 1
)

supplier_summary["value_share"] = (
    supplier_summary["allocated_award_value"]
    / supplier_summary["allocated_award_value"].sum()
)

supplier_summary["cumulative_value_share"] = (
    supplier_summary["value_share"].cumsum()
)

supplier_summary["value_band"] = pd.cut(
    supplier_summary["allocated_award_value"],
    bins=[
        -np.inf,
        100_000,
        1_000_000,
        10_000_000,
        100_000_000,
        1_000_000_000,
        np.inf,
    ],
    labels=[
        "<£100K",
        "£100K–<£1M",
        "£1M–<£10M",
        "£10M–<£100M",
        "£100M–<£1B",
        "£1B+",
    ],
)


# ---------------------------------------------------------------------
# Concentration analysis
# ---------------------------------------------------------------------

print_section("Supplier concentration")

total_supplier_value = supplier_summary[
    "allocated_award_value"
].sum()

supplier_count = len(supplier_summary)

print(f"Usable suppliers: {supplier_count:,}")
print(f"Allocated supplier value: £{total_supplier_value:,.2f}")

concentration_rows = []

for pct in [1, 5, 10, 25, 50]:
    n = max(1, int(np.ceil(supplier_count * pct / 100)))

    value = supplier_summary.head(n)[
        "allocated_award_value"
    ].sum()

    share = (
        value / total_supplier_value * 100
        if total_supplier_value > 0
        else np.nan
    )

    concentration_rows.append(
        {
            "supplier_percentile": f"Top {pct}%",
            "supplier_count": n,
            "allocated_value": value,
            "value_share_percent": share,
        }
    )

    print(
        f"Top {pct:>2}%: "
        f"{n:,} suppliers | "
        f"£{value:,.2f} | "
        f"{share:.2f}% of allocated supplier value"
    )

concentration = pd.DataFrame(concentration_rows)


# ---------------------------------------------------------------------
# Supplier value distribution
# ---------------------------------------------------------------------

print_section("Supplier value distribution")

value_distribution = (
    supplier_summary
    .groupby(
        "value_band",
        observed=False
    )
    .agg(
        supplier_count=(
            "supplier_key",
            "nunique"
        ),
        allocated_value=(
            "allocated_award_value",
            "sum"
        ),
    )
    .reset_index()
)

value_distribution["value_share_percent"] = (
    value_distribution["allocated_value"]
    / total_supplier_value
    * 100
)

print(value_distribution.to_string(index=False))


# ---------------------------------------------------------------------
# Supplier diversification
# ---------------------------------------------------------------------

print_section("Supplier diversification")

supplier_diversification = (
    supplier_analysis
    .groupby(
        [
            "supplier_key",
            "canonical_supplier_name",
        ],
        as_index=False
    )
    .agg(
        award_count=(
            "award_id",
            "nunique"
        ),
        buyer_count=(
            "buyer_id",
            "nunique"
        ) if "buyer_id" in supplier_analysis.columns
        else ("award_id", "nunique"),
        allocated_award_value=(
            "allocated_award_value",
            "sum"
        ),
    )
)

supplier_diversification = (
    supplier_diversification
    .sort_values(
        ["buyer_count", "award_count"],
        ascending=False
    )
    .reset_index(drop=True)
)

print(
    supplier_diversification.head(20).to_string(
        index=False
    )
)


# ---------------------------------------------------------------------
# High-value supplier analysis
# ---------------------------------------------------------------------

print_section("High-value supplier population")

high_value_suppliers = supplier_summary[
    supplier_summary["allocated_award_value"] >= 100_000_000
].copy()

high_value_suppliers = high_value_suppliers.sort_values(
    "allocated_award_value",
    ascending=False
)

print(
    f"Suppliers with allocated value >= £100M: "
    f"{len(high_value_suppliers):,}"
)

print(
    high_value_suppliers.head(20).to_string(
        index=False
    )
)


# ---------------------------------------------------------------------
# Multi-supplier award analysis
# ---------------------------------------------------------------------

print_section("Supplier structure")

award_structure = (
    supplier_counts
    .assign(
        supplier_structure=lambda df: np.where(
            df["usable_supplier_count"] > 1,
            "Multiple suppliers",
            "Single supplier",
        )
    )
)

award_structure_summary = (
    supplier_analysis
    .drop_duplicates(
        ["award_id", "release_id"]
    )
    .groupby(
        "supplier_structure",
        as_index=False
    )
    .agg(
        award_count=("award_id", "nunique"),
        allocated_value=(
            "award_value",
            "sum"
        ),
    )
)

award_structure_summary["award_share_percent"] = (
    award_structure_summary["award_count"]
    / award_structure_summary["award_count"].sum()
    * 100
)

award_structure_summary["value_share_percent"] = (
    award_structure_summary["allocated_value"]
    / award_structure_summary["allocated_value"].sum()
    * 100
)

print(
    award_structure_summary.to_string(
        index=False
    )
)


# ---------------------------------------------------------------------
# Supplier identity/data-quality summary
# ---------------------------------------------------------------------

print_section("Supplier data quality and analytical populations")

# -------------------------------------------------------------
# Population 1: all latest award records
# -------------------------------------------------------------

all_latest_awards = len(
    awards[
        awards["is_latest_award_version"] == 1
    ]
)

# -------------------------------------------------------------
# Population 2: latest awards with valid award value
# -------------------------------------------------------------

valid_value_awards = len(latest_awards)

# -------------------------------------------------------------
# Population 3: latest awards represented by at least one
# usable supplier relationship
# -------------------------------------------------------------

awards_with_usable_suppliers = (
    supplier_analysis[
        ["award_id", "release_id"]
    ]
    .drop_duplicates()
    .shape[0]
)

# -------------------------------------------------------------
# Supplier relationship quality
# -------------------------------------------------------------

identity_review_count = (
    supplier_analysis["identity_review_flag"]
    .astype(str)
    .str.contains(
        "review_name_variation",
        case=False,
        na=False
    )
    .sum()
)

supplier_identity_review_count = (
    supplier_analysis["supplier_identity_flag"]
    .astype(str)
    .str.contains(
        "id_multiple_names_review",
        case=False,
        na=False
    )
    .sum()
)

# Count reference-text records from the original supplier
# relationship dataset, rather than the already-filtered
# analytical dataset.
reference_text_total = int(
    supplier_rel["supplier_reference_text_flag"].sum()
)

# Of those reference-text rows, determine how many belong to
# latest award versions.
reference_text_latest = (
    supplier_rel[
        supplier_rel["supplier_reference_text_flag"]
    ][
        ["award_id", "release_id"]
    ]
    .merge(
        award_keys[
            ["award_id", "release_id"]
        ],
        on=["award_id", "release_id"],
        how="inner"
    )
    .drop_duplicates()
    .shape[0]
)

# Missing/unusable supplier relationships
unusable_supplier_relationships = (
    (~supplier_rel["usable_supplier_flag"])
    .sum()
)

# -------------------------------------------------------------
# Print population summary
# -------------------------------------------------------------

print(
    f"All latest award records: "
    f"{all_latest_awards:,}"
)

print(
    f"Latest awards with valid award value: "
    f"{valid_value_awards:,}"
)

print(
    f"Latest awards with usable supplier information: "
    f"{awards_with_usable_suppliers:,}"
)

print(
    f"Latest awards without usable supplier information: "
    f"{valid_value_awards - awards_with_usable_suppliers:,}"
)

print()

print(
    f"Supplier relationship rows requiring identity review: "
    f"{identity_review_count:,}"
)

print(
    f"Supplier relationship rows with multiple names per ID: "
    f"{supplier_identity_review_count:,}"
)

print(
    f"Reference/source-text rows in full supplier dataset: "
    f"{reference_text_total:,}"
)

print(
    f"Reference/source-text rows linked to latest awards: "
    f"{reference_text_latest:,}"
)

print(
    f"Unusable supplier relationship rows: "
    f"{unusable_supplier_relationships:,}"
)

quality_summary = pd.DataFrame(
    [
        {
            "metric": "all_latest_awards",
            "count": all_latest_awards,
        },
        {
            "metric": "latest_awards_with_valid_value",
            "count": valid_value_awards,
        },
        {
            "metric": "latest_awards_with_usable_supplier",
            "count": awards_with_usable_suppliers,
        },
        {
            "metric": "latest_awards_without_usable_supplier",
            "count": (
                valid_value_awards
                - awards_with_usable_suppliers
            ),
        },
        {
            "metric": "supplier_relationship_identity_review",
            "count": identity_review_count,
        },
        {
            "metric": "supplier_relationship_multiple_names_per_id",
            "count": supplier_identity_review_count,
        },
        {
            "metric": "reference_text_relationships_full_dataset",
            "count": reference_text_total,
        },
        {
            "metric": "reference_text_relationships_latest_awards",
            "count": reference_text_latest,
        },
        {
            "metric": "unusable_supplier_relationships",
            "count": unusable_supplier_relationships,
        },
    ]
)

# ---------------------------------------------------------------------
# Save outputs
# ---------------------------------------------------------------------

print_section("Saving outputs")

supplier_summary.to_csv(
    OUTPUT_DIR / "supplier_summary.csv",
    index=False,
)

concentration.to_csv(
    OUTPUT_DIR / "supplier_concentration.csv",
    index=False,
)

value_distribution.to_csv(
    OUTPUT_DIR / "supplier_value_distribution.csv",
    index=False,
)

supplier_diversification.to_csv(
    OUTPUT_DIR / "supplier_diversification.csv",
    index=False,
)

high_value_suppliers.to_csv(
    OUTPUT_DIR / "high_value_suppliers.csv",
    index=False,
)

award_structure_summary.to_csv(
    OUTPUT_DIR / "supplier_structure_summary.csv",
    index=False,
)

supplier_analysis.to_csv(
    OUTPUT_DIR / "supplier_relationship_analysis.csv",
    index=False,
)

print(f"Output directory: {OUTPUT_DIR}")

print("\nFiles created:")

for file in sorted(OUTPUT_DIR.glob("*.csv")):
    print(f"  - {file.name}")

quality_summary.to_csv(
    OUTPUT_DIR / "supplier_data_quality_summary.csv",
    index=False,
)

# ---------------------------------------------------------------------
# Final checks
# ---------------------------------------------------------------------

print_section("Final validation")

assert len(supplier_summary) > 0
assert supplier_summary["allocated_award_value"].ge(0).all()
assert concentration["value_share_percent"].between(0, 100).all()
assert value_distribution["value_share_percent"].ge(0).all()

print("Supplier summary created")
print("Concentration analysis created")
print("Supplier value distribution created")
print("Diversification analysis created")
print("High-value supplier analysis created")
print("Supplier structure analysis created")
print("Data-quality analysis created")
print("Final validation passed")

print("\nAnalysis 02 completed successfully.")