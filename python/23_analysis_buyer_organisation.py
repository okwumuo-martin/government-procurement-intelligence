"""
Government Procurement Intelligence
Analysis 03: Buyer / Organisation Analytics

Purpose
-------
Analyse procurement activity at buyer/organisation level using:

1. The authoritative analytical award-level dataset for:
   - award values
   - procurement methods
   - contract duration
   - supplier structure
   - PRI-related fields

2. The normalized supplier relationship dataset for:
   - distinct supplier entities
   - supplier exposure by buyer
   - supplier relationship quality

Important methodology
---------------------
- Buyer totals use award-level allocated award value.
- Buyer identity is based on buyer_key.
- Buyer names are NOT automatically merged where identity evidence
  is insufficient.
- The most frequently reported buyer name is used only as a
  display name for each buyer_key.
- Supplier counts use normalized supplier_key values.
- Supplier reference/attachment text is excluded from usable
  supplier analysis.
- Buyer review indicators are screening indicators, not official
  risk scores.
"""

from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

ANALYTICAL_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "analysis"
    / "procurement_analytical_dataset.csv"
)

SUPPLIER_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "final"
    / "award_suppliers_2025.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "analysis"
    / "buyer_organisation"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# DISPLAY
# ============================================================

def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ============================================================
# LOAD ANALYTICAL DATASET
# ============================================================

section("GOVERNMENT PROCUREMENT INTELLIGENCE")
print("ANALYSIS 03: BUYER / ORGANISATION ANALYTICS")
print("=" * 70)

section("Loading authoritative analytical dataset")

df = pd.read_csv(ANALYTICAL_FILE)

print(f"Records loaded: {len(df):,}")
print(f"Columns loaded: {len(df.columns)}")


required_columns = [
    "ocid",
    "award_id",
    "release_id",
    "award_value",
    "buyer_name",
    "buyer_id",
    "procurement_method_group",
    "supplier_structure",
    "contract_duration_years",
]

missing = [
    c for c in required_columns
    if c not in df.columns
]

if missing:
    raise ValueError(
        f"Required analytical columns missing: {missing}"
    )


# ============================================================
# PREPARE BUYER FIELDS
# ============================================================

section("Preparing buyer fields")

df["buyer_name"] = (
    df["buyer_name"]
    .fillna("Unknown buyer")
    .astype(str)
    .str.strip()
)

df["buyer_id"] = (
    df["buyer_id"]
    .fillna("")
    .astype(str)
    .str.strip()
)

# Buyer ID is the preferred buyer entity key.
#
# Where buyer ID is missing, normalized buyer name is used
# as a fallback identifier.
#
# IMPORTANT:
# Buyer names are not used to merge different populated
# buyer IDs automatically.

df["buyer_key"] = np.where(
    df["buyer_id"].ne(""),
    "ID:" + df["buyer_id"],
    "NAME:"
    + df["buyer_name"]
    .str.lower()
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

df["award_value"] = pd.to_numeric(
    df["award_value"],
    errors="coerce"
)

df["contract_duration_years"] = pd.to_numeric(
    df["contract_duration_years"],
    errors="coerce"
)

df["procurement_method_group"] = (
    df["procurement_method_group"]
    .fillna("Unknown")
    .astype(str)
)

df["supplier_structure"] = (
    df["supplier_structure"]
    .fillna("No usable supplier")
    .astype(str)
)


# ============================================================
# BUYER RECONCILIATION
# ============================================================

section("Buyer reconciliation checks")

unique_buyer_entities = df["buyer_key"].nunique()

print(
    f"Unique buyer entities: {unique_buyer_entities:,}"
)

print(
    f"Unique buyer names:    "
    f"{df['buyer_name'].nunique():,}"
)

print(
    f"Unique buyer IDs:      "
    f"{df['buyer_id'].replace('', np.nan).nunique():,}"
)

total_awards = df["award_id"].nunique()

total_value = df["award_value"].sum(
    min_count=1
)

print(
    f"Total analytical awards: "
    f"{total_awards:,}"
)

print(
    f"Total allocated award value: "
    f"£{total_value:,.2f}"
)


# ============================================================
# BUYER NAME QUALITY / VARIATION
# ============================================================

section("Buyer name quality / variation")

buyer_name_quality = (
    df.groupby(
        "buyer_key",
        dropna=False
    )
    .agg(
        buyer_name_count=(
            "buyer_name",
            "nunique"
        ),
        buyer_name_variants=(
            "buyer_name",
            lambda x: " | ".join(
                sorted(
                    pd.Series(x)
                    .dropna()
                    .astype(str)
                    .unique()
                )
            )
        ),
    )
    .reset_index()
)

buyer_name_quality["multiple_name_flag"] = (
    buyer_name_quality["buyer_name_count"] > 1
)

multiple_name_entities = (
    buyer_name_quality[
        "multiple_name_flag"
    ].sum()
)

print(
    f"Buyer entities with multiple buyer names: "
    f"{multiple_name_entities:,}"
)


# ============================================================
# SELECT PRIMARY BUYER NAME
# ============================================================

section("Selecting primary buyer display names")

# Count how often each name is reported for each buyer_key.

buyer_name_frequency = (
    df.groupby(
        [
            "buyer_key",
            "buyer_name",
        ],
        dropna=False
    )
    .size()
    .reset_index(
        name="name_frequency"
    )
)

# Select the most frequently reported name.
# Alphabetical order breaks ties consistently.

primary_buyer_names = (
    buyer_name_frequency
    .sort_values(
        [
            "buyer_key",
            "name_frequency",
            "buyer_name",
        ],
        ascending=[
            True,
            False,
            True,
        ]
    )
    .drop_duplicates(
        subset=["buyer_key"],
        keep="first"
    )
    [
        [
            "buyer_key",
            "buyer_name",
        ]
    ]
)

# Attach name-quality information.

buyer_display = (
    primary_buyer_names
    .merge(
        buyer_name_quality[
            [
                "buyer_key",
                "buyer_name_count",
                "buyer_name_variants",
                "multiple_name_flag",
            ]
        ],
        on="buyer_key",
        how="left",
        validate="one_to_one",
    )
)

assert (
    buyer_display["buyer_key"].nunique()
    == len(buyer_display)
), "buyer_display contains duplicate buyer_key values."


# ============================================================
# BUILD BUYER OVERVIEW AT BUYER-ENTITY GRAIN
# ============================================================

section("Building buyer overview")

# IMPORTANT:
# Group ONLY by buyer_key.
#
# Do NOT group by buyer_name because some buyer IDs have
# multiple reported names.

buyer_overview = (
    df.groupby(
        "buyer_key",
        dropna=False
    )
    .agg(
        award_count=(
            "award_id",
            "nunique"
        ),
        allocated_award_value=(
            "award_value",
            "sum"
        ),
        mean_award_value=(
            "award_value",
            "mean"
        ),
        median_award_value=(
            "award_value",
            "median"
        ),
        single_supplier_awards=(
            "supplier_structure",
            lambda x: (
                x == "Single supplier"
            ).sum()
        ),
        multiple_supplier_awards=(
            "supplier_structure",
            lambda x: (
                x == "Multiple suppliers"
            ).sum()
        ),
        no_usable_supplier_awards=(
            "supplier_structure",
            lambda x: (
                x == "No usable supplier"
            ).sum()
        ),
        max_contract_duration_years=(
            "contract_duration_years",
            "max"
        ),
    )
    .reset_index()
)

# Add the primary display name AFTER aggregation.

buyer_overview = buyer_overview.merge(
    buyer_display,
    on="buyer_key",
    how="left",
    validate="one_to_one",
)

buyer_overview[
    "single_supplier_award_share_percent"
] = (
    buyer_overview[
        "single_supplier_awards"
    ]
    / buyer_overview["award_count"]
    * 100
)

buyer_overview[
    "multiple_supplier_award_share_percent"
] = (
    buyer_overview[
        "multiple_supplier_awards"
    ]
    / buyer_overview["award_count"]
    * 100
)

buyer_overview[
    "no_usable_supplier_share_percent"
] = (
    buyer_overview[
        "no_usable_supplier_awards"
    ]
    / buyer_overview["award_count"]
    * 100
)

buyer_overview = buyer_overview.sort_values(
    "allocated_award_value",
    ascending=False
)

buyer_overview["value_rank"] = (
    buyer_overview[
        "allocated_award_value"
    ]
    .rank(
        method="min",
        ascending=False
    )
    .astype(int)
)

buyer_overview["activity_rank"] = (
    buyer_overview[
        "award_count"
    ]
    .rank(
        method="min",
        ascending=False
    )
    .astype(int)
)

print(
    f"Buyer overview entities: "
    f"{len(buyer_overview):,}"
)


# ============================================================
# LOAD NORMALIZED SUPPLIER RELATIONSHIPS
# ============================================================

section("Loading normalized supplier relationships")

supplier_rel = pd.read_csv(
    SUPPLIER_FILE
)

print(
    f"Supplier relationship rows loaded: "
    f"{len(supplier_rel):,}"
)

required_supplier_columns = [
    "ocid",
    "release_id",
    "award_id",
    "supplier_key",
    "canonical_supplier_name",
    "supplier_name",
    "supplier_identity_flag",
    "identity_review_flag",
]

missing_supplier = [
    c
    for c in required_supplier_columns
    if c not in supplier_rel.columns
]

if missing_supplier:
    raise ValueError(
        f"Required supplier columns missing: "
        f"{missing_supplier}"
    )


# ============================================================
# SUPPLIER QUALITY FILTER
# ============================================================

section("Preparing usable supplier relationships")

supplier_rel["supplier_name_clean"] = (
    supplier_rel["supplier_name"]
    .fillna("")
    .astype(str)
    .str.strip()
)

supplier_rel["canonical_supplier_name"] = (
    supplier_rel["canonical_supplier_name"]
    .fillna("")
    .astype(str)
    .str.strip()
)

supplier_rel["supplier_key"] = (
    supplier_rel["supplier_key"]
    .fillna("")
    .astype(str)
    .str.strip()
)

supplier_text = (
    supplier_rel[
        "supplier_name_clean"
    ]
    .str.lower()
)

reference_mask = (
    supplier_text.str.contains(
        "successful supplier",
        na=False
    )
    | supplier_text.str.contains(
        "supplier list",
        na=False
    )
    | supplier_text.str.contains(
        "see webpage",
        na=False
    )
    | supplier_text.str.contains(
        "contract award details",
        na=False
    )
    | supplier_text.str.contains(
        "attachments",
        na=False
    )
    | supplier_text.str.contains(
        "please see",
        na=False
    )
)

valid_supplier_mask = (
    supplier_rel[
        "supplier_key"
    ].ne("")
    & supplier_rel[
        "canonical_supplier_name"
    ].ne("")
    & ~reference_mask
)

usable_supplier_rel = supplier_rel.loc[
    valid_supplier_mask
].copy()

print(
    f"Usable supplier relationship rows: "
    f"{len(usable_supplier_rel):,}"
)

print(
    f"Reference/source-text rows excluded: "
    f"{reference_mask.sum():,}"
)

print(
    f"Unusable/missing supplier rows: "
    f"{len(supplier_rel) - len(usable_supplier_rel):,}"
)


# ============================================================
# BUILD AWARD -> BUYER LOOKUP
# ============================================================

section("Building award-to-buyer lookup")

award_buyer_lookup_raw = df[
    [
        "award_id",
        "release_id",
        "buyer_key",
        "buyer_name",
        "buyer_id",
    ]
].copy()

# Check whether one award version maps to multiple buyer IDs.

buyer_mapping_check = (
    award_buyer_lookup_raw
    .groupby(
        [
            "award_id",
            "release_id",
        ]
    )["buyer_key"]
    .nunique()
)

ambiguous_award_buyer_count = (
    buyer_mapping_check
    .gt(1)
    .sum()
)

print(
    f"Award versions mapping to multiple buyer entities: "
    f"{ambiguous_award_buyer_count:,}"
)

if ambiguous_award_buyer_count > 0:
    raise ValueError(
        "Some award versions map to multiple buyer entities. "
        "The supplier-to-buyer join cannot safely continue."
    )

award_buyer_lookup = (
    award_buyer_lookup_raw
    .drop_duplicates(
        subset=[
            "award_id",
            "release_id",
        ]
    )
)


# ============================================================
# JOIN BUYER INFORMATION TO SUPPLIER RELATIONSHIPS
# ============================================================

section("Linking suppliers to buyers")

supplier_rel_buyer = (
    usable_supplier_rel
    .merge(
        award_buyer_lookup,
        on=[
            "award_id",
            "release_id",
        ],
        how="inner",
        validate="many_to_one",
    )
)

matched_supplier_relationships = (
    len(supplier_rel_buyer)
)

unmatched_supplier_relationships = (
    len(usable_supplier_rel)
    - matched_supplier_relationships
)

print(
    f"Supplier relationships matched to buyer records: "
    f"{matched_supplier_relationships:,}"
)

print(
    f"Usable supplier relationships without buyer match: "
    f"{unmatched_supplier_relationships:,}"
)


# ============================================================
# SUPPLIER EXPOSURE BY BUYER
# ============================================================

section("Building supplier exposure by buyer")

# Again, aggregate by buyer_key only.

supplier_exposure = (
    supplier_rel_buyer
    .groupby(
        "buyer_key",
        dropna=False
    )
    .agg(
        supplier_count=(
            "supplier_key",
            "nunique"
        ),
        supplier_relationship_count=(
            "supplier_key",
            "size"
        ),
        identity_review_relationships=(
            "identity_review_flag",
            lambda x: (
                x.astype(str)
                .str.contains(
                    "review",
                    case=False,
                    na=False
                )
            ).sum()
        ),
    )
    .reset_index()
)

# Add the primary buyer display name here.
#
# This is the merge you were asking about earlier.
#
# supplier_exposure = the metrics
# buyer_display = the readable buyer name
# buyer_key = the matching identifier

supplier_exposure = supplier_exposure.merge(
    buyer_display[
        [
            "buyer_key",
            "buyer_name",
            "buyer_name_count",
            "multiple_name_flag",
        ]
    ],
    on="buyer_key",
    how="left",
    validate="one_to_one",
)


# ============================================================
# CALCULATE SUPPLIER STRUCTURE VALUE BY BUYER
# ============================================================

section("Calculating supplier structure value by buyer")

single_supplier_value = (
    df.loc[
        df["supplier_structure"]
        == "Single supplier"
    ]
    .groupby(
        "buyer_key",
        dropna=False
    )["award_value"]
    .sum()
    .reset_index(
        name="single_supplier_value"
    )
)

multiple_supplier_value = (
    df.loc[
        df["supplier_structure"]
        == "Multiple suppliers"
    ]
    .groupby(
        "buyer_key",
        dropna=False
    )["award_value"]
    .sum()
    .reset_index(
        name="multiple_supplier_value"
    )
)

supplier_exposure = (
    supplier_exposure
    .merge(
        buyer_overview[
            [
                "buyer_key",
                "award_count",
                "allocated_award_value",
                "single_supplier_awards",
                "multiple_supplier_awards",
                "no_usable_supplier_awards",
            ]
        ],
        on="buyer_key",
        how="left",
        validate="one_to_one",
    )
    .merge(
        single_supplier_value,
        on="buyer_key",
        how="left",
        validate="one_to_one",
    )
    .merge(
        multiple_supplier_value,
        on="buyer_key",
        how="left",
        validate="one_to_one",
    )
)

supplier_exposure[
    "single_supplier_value"
] = (
    supplier_exposure[
        "single_supplier_value"
    ]
    .fillna(0)
)

supplier_exposure[
    "multiple_supplier_value"
] = (
    supplier_exposure[
        "multiple_supplier_value"
    ]
    .fillna(0)
)

supplier_exposure[
    "single_supplier_value_share_percent"
] = (
    supplier_exposure[
        "single_supplier_value"
    ]
    / supplier_exposure[
        "allocated_award_value"
    ]
    * 100
)

supplier_exposure[
    "multiple_supplier_value_share_percent"
] = (
    supplier_exposure[
        "multiple_supplier_value"
    ]
    / supplier_exposure[
        "allocated_award_value"
    ]
    * 100
)

supplier_exposure = supplier_exposure.sort_values(
    "allocated_award_value",
    ascending=False
)


# ============================================================
# TOP BUYERS BY VALUE
# ============================================================

section("Top buyers by allocated value")

top_buyers_value = (
    buyer_overview
    .head(25)
    .copy()
)

print(
    top_buyers_value[
        [
            "buyer_name",
            "award_count",
            "allocated_award_value",
            "mean_award_value",
            "median_award_value",
        ]
    ].to_string(index=False)
)


# ============================================================
# TOP BUYERS BY ACTIVITY
# ============================================================

section("Top buyers by award count")

top_buyers_count = (
    buyer_overview
    .sort_values(
        [
            "award_count",
            "allocated_award_value",
        ],
        ascending=[
            False,
            False,
        ]
    )
    .head(25)
    .copy()
)

print(
    top_buyers_count[
        [
            "buyer_name",
            "award_count",
            "allocated_award_value",
            "mean_award_value",
            "median_award_value",
        ]
    ].to_string(index=False)
)


# ============================================================
# PROCUREMENT METHOD BY BUYER
# ============================================================

section("Procurement method by buyer")

buyer_method = (
    df.groupby(
        [
            "buyer_key",
            "procurement_method_group",
        ],
        dropna=False
    )
    .agg(
        award_count=(
            "award_id",
            "nunique"
        ),
        allocated_award_value=(
            "award_value",
            "sum"
        ),
        median_award_value=(
            "award_value",
            "median"
        ),
    )
    .reset_index()
)

buyer_method = buyer_method.merge(
    buyer_display[
        [
            "buyer_key",
            "buyer_name",
        ]
    ],
    on="buyer_key",
    how="left",
    validate="many_to_one",
)

buyer_method[
    "buyer_method_value_share_percent"
] = (
    buyer_method
    .groupby("buyer_key")[
        "allocated_award_value"
    ]
    .transform(
        lambda x: (
            x / x.sum() * 100
        )
    )
)

buyer_method = buyer_method[
    [
        "buyer_key",
        "buyer_name",
        "procurement_method_group",
        "award_count",
        "allocated_award_value",
        "median_award_value",
        "buyer_method_value_share_percent",
    ]
]


# ============================================================
# DIRECT / LIMITED EXPOSURE
# ============================================================

section("Direct / limited procurement exposure")

direct_limited = df[
    df[
        "procurement_method_group"
    ].isin(
        [
            "Direct",
            "Limited",
        ]
    )
].copy()

buyer_direct_limited = (
    direct_limited
    .groupby(
        "buyer_key",
        dropna=False
    )
    .agg(
        direct_limited_awards=(
            "award_id",
            "nunique"
        ),
        direct_limited_value=(
            "award_value",
            "sum"
        ),
    )
    .reset_index()
)

buyer_direct_limited = (
    buyer_direct_limited
    .merge(
        buyer_display[
            [
                "buyer_key",
                "buyer_name",
            ]
        ],
        on="buyer_key",
        how="left",
        validate="one_to_one",
    )
    .merge(
        buyer_overview[
            [
                "buyer_key",
                "award_count",
                "allocated_award_value",
            ]
        ],
        on="buyer_key",
        how="left",
        validate="one_to_one",
    )
)

buyer_direct_limited[
    "direct_limited_award_share_percent"
] = (
    buyer_direct_limited[
        "direct_limited_awards"
    ]
    / buyer_direct_limited[
        "award_count"
    ]
    * 100
)

buyer_direct_limited[
    "direct_limited_value_share_percent"
] = (
    buyer_direct_limited[
        "direct_limited_value"
    ]
    / buyer_direct_limited[
        "allocated_award_value"
    ]
    * 100
)

buyer_direct_limited = (
    buyer_direct_limited
    .sort_values(
        "direct_limited_value",
        ascending=False
    )
)


# ============================================================
# LONG-DURATION EXPOSURE
# ============================================================

section("Long-duration contract exposure")

long_duration = df[
    df[
        "contract_duration_years"
    ] >= 10
].copy()

buyer_long_duration = (
    long_duration
    .groupby(
        "buyer_key",
        dropna=False
    )
    .agg(
        long_duration_awards=(
            "award_id",
            "nunique"
        ),
        long_duration_value=(
            "award_value",
            "sum"
        ),
        maximum_duration_years=(
            "contract_duration_years",
            "max"
        ),
    )
    .reset_index()
)

buyer_long_duration = (
    buyer_long_duration
    .merge(
        buyer_display[
            [
                "buyer_key",
                "buyer_name",
            ]
        ],
        on="buyer_key",
        how="left",
        validate="one_to_one",
    )
    .merge(
        buyer_overview[
            [
                "buyer_key",
                "award_count",
                "allocated_award_value",
            ]
        ],
        on="buyer_key",
        how="left",
        validate="one_to_one",
    )
)

buyer_long_duration[
    "long_duration_value_share_percent"
] = (
    buyer_long_duration[
        "long_duration_value"
    ]
    / buyer_long_duration[
        "allocated_award_value"
    ]
    * 100
)

buyer_long_duration = (
    buyer_long_duration
    .sort_values(
        "long_duration_value",
        ascending=False
    )
)


# ============================================================
# BUYER ACTIVITY / VALUE SEGMENTATION
# ============================================================

section("Buyer activity segmentation")

activity_median = (
    buyer_overview[
        "award_count"
    ].median()
)

value_median = (
    buyer_overview[
        "allocated_award_value"
    ].median()
)

print(
    f"Buyer award-count median: "
    f"{activity_median:,.2f}"
)

print(
    f"Buyer allocated-value median: "
    f"£{value_median:,.2f}"
)

buyer_overview["activity_level"] = np.where(
    buyer_overview["award_count"]
    >= activity_median,
    "High activity",
    "Lower activity"
)

buyer_overview["value_level"] = np.where(
    buyer_overview[
        "allocated_award_value"
    ]
    >= value_median,
    "High value",
    "Lower value"
)

buyer_overview[
    "activity_value_segment"
] = (
    buyer_overview[
        "activity_level"
    ]
    + " / "
    + buyer_overview[
        "value_level"
    ]
)

activity_segments = (
    buyer_overview
    .groupby(
        "activity_value_segment",
        dropna=False
    )
    .agg(
        buyer_count=(
            "buyer_key",
            "nunique"
        ),
        total_award_count=(
            "award_count",
            "sum"
        ),
        allocated_award_value=(
            "allocated_award_value",
            "sum"
        ),
    )
    .reset_index()
)

activity_segments[
    "award_share_percent"
] = (
    activity_segments[
        "total_award_count"
    ]
    / activity_segments[
        "total_award_count"
    ].sum()
    * 100
)

activity_segments[
    "value_share_percent"
] = (
    activity_segments[
        "allocated_award_value"
    ]
    / activity_segments[
        "allocated_award_value"
    ].sum()
    * 100
)

print(
    activity_segments.to_string(
        index=False
    )
)


# ============================================================
# BUYER REVIEW POPULATION
# ============================================================

section("Buyer analytical review population")

review = buyer_overview.copy()

# ------------------------------------------------------------
# Top 5% by allocated value
# ------------------------------------------------------------

value_threshold = review[
    "allocated_award_value"
].quantile(0.95)

review[
    "top_5_percent_value_indicator"
] = (
    review[
        "allocated_award_value"
    ]
    >= value_threshold
)


# ------------------------------------------------------------
# High single-supplier value concentration
# ------------------------------------------------------------

supplier_exposure_lookup = (
    supplier_exposure[
        [
            "buyer_key",
            "single_supplier_value_share_percent",
        ]
    ]
    .drop_duplicates(
        "buyer_key"
    )
)

review = review.merge(
    supplier_exposure_lookup,
    on="buyer_key",
    how="left",
    validate="one_to_one",
)

review[
    "high_single_supplier_value_indicator"
] = (
    review[
        "single_supplier_value_share_percent"
    ]
    >= 90
)


# ------------------------------------------------------------
# Direct / limited exposure
# ------------------------------------------------------------

direct_lookup = (
    buyer_direct_limited[
        [
            "buyer_key",
            "direct_limited_value_share_percent",
        ]
    ]
    .drop_duplicates(
        "buyer_key"
    )
)

review = review.merge(
    direct_lookup,
    on="buyer_key",
    how="left",
    validate="one_to_one",
)

review[
    "high_direct_limited_value_indicator"
] = (
    review[
        "direct_limited_value_share_percent"
    ]
    >= 25
)


# ------------------------------------------------------------
# Long duration
# ------------------------------------------------------------

review[
    "long_duration_indicator"
] = (
    review[
        "max_contract_duration_years"
    ]
    >= 10
)


# ------------------------------------------------------------
# Review indicator count
# ------------------------------------------------------------

indicator_columns = [
    "top_5_percent_value_indicator",
    "high_single_supplier_value_indicator",
    "high_direct_limited_value_indicator",
    "long_duration_indicator",
]

review[
    "review_indicator_count"
] = (
    review[
        indicator_columns
    ]
    .fillna(False)
    .sum(axis=1)
)

review["review_category"] = np.select(
    [
        review[
            "review_indicator_count"
        ] >= 3,

        review[
            "review_indicator_count"
        ] == 2,

        review[
            "review_indicator_count"
        ] == 1,
    ],
    [
        "Higher review attention",
        "Moderate review attention",
        "Lower review attention",
    ],
    default="No additional indicator",
)


def build_review_rationale(row):

    reasons = []

    if row[
        "top_5_percent_value_indicator"
    ]:
        reasons.append(
            "top 5% by allocated value"
        )

    if row[
        "high_single_supplier_value_indicator"
    ]:
        reasons.append(
            "high single-supplier value concentration"
        )

    if row[
        "high_direct_limited_value_indicator"
    ]:
        reasons.append(
            "material direct/limited procurement exposure"
        )

    if row[
        "long_duration_indicator"
    ]:
        reasons.append(
            "contracts of 10+ years"
        )

    if not reasons:
        return (
            "No additional screening indicator"
        )

    return "; ".join(reasons)


review[
    "review_rationale"
] = review.apply(
    build_review_rationale,
    axis=1
)

review = review.sort_values(
    [
        "review_indicator_count",
        "allocated_award_value",
    ],
    ascending=[
        False,
        False,
    ]
)


# ============================================================
# BUYER DATA QUALITY
# ============================================================

section("Buyer data quality")

buyer_quality = pd.DataFrame(
    {
        "metric": [
            "Analytical award records",
            "Unique buyer entities",
            "Unique buyer names",
            "Unique buyer IDs",
            "Records with unknown buyer name",
            "Records without buyer ID",
            "Buyer entities with multiple buyer names",
        ],
        "count": [
            len(df),

            df[
                "buyer_key"
            ].nunique(),

            df[
                "buyer_name"
            ].nunique(),

            df[
                "buyer_id"
            ]
            .replace(
                "",
                np.nan
            )
            .nunique(),

            df[
                "buyer_name"
            ]
            .eq(
                "Unknown buyer"
            )
            .sum(),

            df[
                "buyer_id"
            ]
            .eq("")
            .sum(),

            (
                df.groupby(
                    "buyer_key"
                )[
                    "buyer_name"
                ]
                .nunique()
                .gt(1)
                .sum()
            ),
        ],
    }
)

print(
    buyer_quality.to_string(
        index=False
    )
)


# ============================================================
# FINAL RECONCILIATION
# ============================================================

section("Final validation")

expected_buyers = (
    df["buyer_key"].nunique()
)

expected_awards = (
    df["award_id"].nunique()
)

expected_value = (
    df["award_value"].sum()
)


# ------------------------------------------------------------
# Buyer entity count
# ------------------------------------------------------------

assert (
    len(buyer_overview)
    == expected_buyers
), (
    f"Buyer overview contains "
    f"{len(buyer_overview):,} entities "
    f"but expected "
    f"{expected_buyers:,}."
)


# ------------------------------------------------------------
# Buyer key uniqueness
# ------------------------------------------------------------

assert (
    buyer_overview[
        "buyer_key"
    ].nunique()
    == len(buyer_overview)
), (
    "Duplicate buyer_key values remain "
    "in buyer_overview."
)


# ------------------------------------------------------------
# Award count reconciliation
# ------------------------------------------------------------

buyer_award_total = (
    buyer_overview[
        "award_count"
    ].sum()
)

assert (
    buyer_award_total
    == expected_awards
), (
    f"Buyer award count total "
    f"{buyer_award_total:,} "
    f"does not equal expected "
    f"{expected_awards:,}."
)


# ------------------------------------------------------------
# Award value reconciliation
# ------------------------------------------------------------

buyer_value_total = (
    buyer_overview[
        "allocated_award_value"
    ].sum()
)

assert np.isclose(
    buyer_value_total,
    expected_value,
    rtol=1e-9,
    atol=1,
), (
    f"Buyer value total "
    f"£{buyer_value_total:,.2f} "
    f"does not reconcile with expected "
    f"£{expected_value:,.2f}."
)


# ------------------------------------------------------------
# Activity segmentation reconciliation
# ------------------------------------------------------------

assert (
    activity_segments[
        "buyer_count"
    ].sum()
    == expected_buyers
), (
    "Buyer activity segmentation does not "
    "reconcile to the unique buyer entity count."
)

assert (
    activity_segments[
        "total_award_count"
    ].sum()
    == expected_awards
), (
    "Buyer activity segmentation award "
    "counts do not reconcile."
)

assert np.isclose(
    activity_segments[
        "allocated_award_value"
    ].sum(),
    expected_value,
    rtol=1e-9,
    atol=1,
), (
    "Buyer activity segmentation value "
    "does not reconcile."
)


# ------------------------------------------------------------
# Supplier relationship reconciliation
# ------------------------------------------------------------

supplier_relationship_total = (
    supplier_exposure[
        "supplier_relationship_count"
    ].sum()
)

assert (
    supplier_relationship_total
    <= len(usable_supplier_rel)
), (
    "Supplier relationship count exceeds "
    "usable supplier relationship population."
)


# ------------------------------------------------------------
# Supplier exposure buyer uniqueness
# ------------------------------------------------------------

assert (
    supplier_exposure[
        "buyer_key"
    ].nunique()
    == len(supplier_exposure)
), (
    "Duplicate buyer_key values remain "
    "in supplier_exposure."
)


# ------------------------------------------------------------
# Supplier value reconciliation
# ------------------------------------------------------------

single_value_total = (
    supplier_exposure[
        "single_supplier_value"
    ].sum()
)

expected_single_value = (
    df.loc[
        df["supplier_structure"]
        == "Single supplier",
        "award_value",
    ].sum()
)

assert np.isclose(
    single_value_total,
    expected_single_value,
    rtol=1e-9,
    atol=1,
), (
    "Single-supplier value by buyer "
    "does not reconcile."
)

multiple_value_total = (
    supplier_exposure[
        "multiple_supplier_value"
    ].sum()
)

expected_multiple_value = (
    df.loc[
        df["supplier_structure"]
        == "Multiple suppliers",
        "award_value",
    ].sum()
)

assert np.isclose(
    multiple_value_total,
    expected_multiple_value,
    rtol=1e-9,
    atol=1,
), (
    "Multiple-supplier value by buyer "
    "does not reconcile."
)


# ------------------------------------------------------------
# Buyer method reconciliation
# ------------------------------------------------------------

method_award_total = (
    buyer_method[
        "award_count"
    ].sum()
)

assert (
    method_award_total
    == expected_awards
), (
    "Procurement-method buyer analysis "
    "does not reconcile to total awards."
)


# ------------------------------------------------------------
# Print validation results
# ------------------------------------------------------------

print(
    f"Buyer entity count: "
    f"{len(buyer_overview):,} "
    f"(expected {expected_buyers:,})"
)

print(
    f"Award count reconciled: "
    f"{buyer_award_total:,} "
    f"(expected {expected_awards:,})"
)

print(
    f"Award value reconciled: "
    f"£{buyer_value_total:,.2f}"
)

print(
    f"Activity segmentation buyers: "
    f"{activity_segments['buyer_count'].sum():,}"
)

print(
    f"Activity segmentation awards: "
    f"{activity_segments['total_award_count'].sum():,}"
)

print(
    f"Supplier relationships used: "
    f"{supplier_relationship_total:,}"
)

print(
    f"Single-supplier value reconciled: "
    f"£{single_value_total:,.2f}"
)

print(
    f"Multiple-supplier value reconciled: "
    f"£{multiple_value_total:,.2f}"
)

print(
    "Buyer overview reconciliation passed"
)

print(
    "Award count reconciliation passed"
)

print(
    "Award value reconciliation passed"
)

print(
    "Activity segmentation reconciliation passed"
)

print(
    "Supplier relationship reconciliation passed"
)

print(
    "Supplier structure value reconciliation passed"
)

print(
    "Buyer-key uniqueness validation passed"
)


# ============================================================
# SAVE OUTPUT FILES
# ============================================================

section("Saving analysis outputs")

outputs = {
    "buyer_overview.csv": buyer_overview,
    "top_buyers_by_value.csv": top_buyers_value,
    "top_buyers_by_count.csv": top_buyers_count,
    "supplier_exposure_by_buyer.csv": supplier_exposure,
    "buyer_procurement_method.csv": buyer_method,
    "buyer_direct_limited_exposure.csv": buyer_direct_limited,
    "buyer_long_duration_exposure.csv": buyer_long_duration,
    "buyer_activity_segments.csv": activity_segments,
    "buyer_review_population.csv": review,
    "buyer_data_quality.csv": buyer_quality,
    "buyer_name_quality.csv": buyer_name_quality,
}

for filename, data in outputs.items():

    output_path = (
        OUTPUT_DIR / filename
    )

    data.to_csv(
        output_path,
        index=False
    )

    print(
        f"Created: {filename}"
    )


# ============================================================
# FINAL OUTPUT SUMMARY
# ============================================================

section("OUTPUT SUMMARY")

print(
    f"Output directory: "
    f"{OUTPUT_DIR}"
)

print("\nOutput files created:")

for file in sorted(
    OUTPUT_DIR.glob("*.csv")
):
    print(
        f"  - {file.name}"
    )

print(
    "\nAnalysis 03 completed successfully."
)