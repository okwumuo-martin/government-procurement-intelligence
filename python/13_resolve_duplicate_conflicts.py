"""
13_resolve_duplicate_conflicts.py

Contracts Finder 2025
Final conflict-resolution and analytical-layer preparation.

Purpose
-------
Creates clean analytical datasets from the normalized Contracts Finder
2025 datasets while preserving source observations and lifecycle history.

Important design principles
----------------------------
1. Never modify the normalized/source datasets.
2. Preserve award lifecycle history.
3. Deduplicate only exact duplicate observations.
4. Do not assume supplier_id is always a reliable unique identifier.
5. Preserve original supplier names.
6. Flag ambiguous supplier identities rather than silently merging them.
7. Keep an auditable resolution log.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import re


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR = INPUT_DIR / "final"
DQ_DIR = OUTPUT_DIR / "data_quality"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DQ_DIR.mkdir(parents=True, exist_ok=True)


RELEASES_FILE = INPUT_DIR / "releases_2025.csv"
AWARDS_FILE = INPUT_DIR / "awards_2025.csv"
RELATIONSHIPS_FILE = INPUT_DIR / "award_suppliers_2025.csv"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_text(value):
    """
    Basic text cleaning while preserving the meaning of the value.
    """
    if pd.isna(value):
        return None

    value = str(value)

    # Replace tabs/newlines with spaces
    value = re.sub(r"[\r\n\t]+", " ", value)

    # Collapse repeated whitespace
    value = re.sub(r"\s+", " ", value)

    value = value.strip()

    return value if value else None


def normalize_supplier_name(value):
    """
    Standardized supplier name for comparison.

    This is NOT treated as the legal supplier identity.
    """
    value = clean_text(value)

    if value is None:
        return None

    value = value.upper()

    return value


def remove_company_suffix_variation(value):
    """
    Produces a comparison-oriented supplier name.

    This is deliberately conservative.

    It does NOT attempt fuzzy matching.
    """
    if value is None:
        return None

    value = value.upper()

    # Normalize punctuation
    value = re.sub(r"[.,]", " ", value)

    # Normalize common company suffixes
    replacements = {
        r"\bLIMITED\b": "LTD",
        r"\bPLC\b": "PLC",
        r"\bINCORPORATED\b": "INC",
        r"\bCORPORATION\b": "CORP",
    }

    for pattern, replacement in replacements.items():
        value = re.sub(pattern, replacement, value)

    value = re.sub(r"\s+", " ", value).strip()

    return value


def is_unreliable_supplier_id(value):
    """
    Supplier identifiers known to be unsuitable as a unique identity key.
    """
    if pd.isna(value):
        return True

    value = str(value).strip().upper()

    if value == "":
        return True

    unreliable_ids = {
        "GB-COH-0",
        "GB-COH-NA",
        "NA",
        "N/A",
        "NONE",
        "NULL",
    }

    return value in unreliable_ids


def supplier_identity_key(row):
    """
    Create a deterministic analytical supplier key.

    Reliable supplier IDs:
        SUP_ID:<supplier_id>

    Unreliable/missing IDs:
        NAME:<normalized supplier name>

    The original supplier_id is retained separately.

    IMPORTANT:
    Name-based keys are used only when the supplier identifier is
    clearly unusable. We do not fuzzy-match names.
    """

    supplier_id = row.get("supplier_id")
    supplier_name = row.get("supplier_name")

    if not is_unreliable_supplier_id(supplier_id):

        supplier_id = str(supplier_id).strip().upper()

        return f"SUP_ID:{supplier_id}"

    normalized_name = normalize_supplier_name(supplier_name)

    if normalized_name:

        comparison_name = remove_company_suffix_variation(
            normalized_name
        )

        return f"NAME:{comparison_name}"

    # Last-resort deterministic key
    award_id = str(row.get("award_id", "UNKNOWN"))
    supplier_index = str(row.get("supplier_index", "UNKNOWN"))

    return f"UNKNOWN:{award_id}:{supplier_index}"


def make_hash_key(df, columns):
    """
    Creates a deterministic string key from selected columns.
    """
    return (
        df[columns]
        .fillna("<NULL>")
        .astype(str)
        .agg("|".join, axis=1)
    )


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("CONTRACTS FINDER 2025")
print("FINAL CONFLICT RESOLUTION")
print("=" * 70)


# ============================================================
# 1. LOAD DATA
# ============================================================

print("\nLoading normalized datasets...")

releases = pd.read_csv(RELEASES_FILE)
awards = pd.read_csv(AWARDS_FILE)
relationships = pd.read_csv(RELATIONSHIPS_FILE)

print(f"Releases:             {len(releases):,}")
print(f"Awards:               {len(awards):,}")
print(f"Award-supplier rows:  {len(relationships):,}")


# ============================================================
# 2. BASIC TEXT CLEANING
# ============================================================

print("\nCleaning textual fields...")

for df in [releases, awards, relationships]:

    for column in df.columns:

        if df[column].dtype == "object":

            df[column] = df[column].apply(clean_text)


# Recreate normalized supplier name after cleaning
if "supplier_name" in relationships.columns:

    relationships["supplier_name_normalized"] = (
        relationships["supplier_name"]
        .apply(normalize_supplier_name)
    )


# ============================================================
# 3. RELEASE RESOLUTION
# ============================================================

print("\n" + "=" * 70)
print("STEP 1: RELEASE RESOLUTION")
print("=" * 70)

release_key = "release_id"

release_duplicate_count = (
    releases.duplicated(subset=[release_key], keep=False).sum()
)

release_duplicate_groups = (
    releases.loc[
        releases.duplicated(subset=[release_key], keep=False),
        release_key
    ].nunique()
)

print(
    f"Repeated release rows:   "
    f"{release_duplicate_count:,}"
)

print(
    f"Repeated release groups:  "
    f"{release_duplicate_groups:,}"
)


# We already established through script 11 that all repeated release IDs
# are exact-identical apart from source_file.
#
# Therefore retain one canonical observation.

releases = (
    releases
    .sort_values(
        ["release_id", "source_file"],
        na_position="last"
    )
    .drop_duplicates(
        subset=["release_id"],
        keep="first"
    )
    .reset_index(drop=True)
)

print(
    f"Canonical releases:       "
    f"{len(releases):,}"
)


# ============================================================
# 4. AWARD VERSION RESOLUTION
# ============================================================

print("\n" + "=" * 70)
print("STEP 2: AWARD VERSION RESOLUTION")
print("=" * 70)

print(
    "\nAward lifecycle grain:"
)

print(
    "    award_id + release_id"
)

print(
    "\nThis preserves legitimate award updates while removing "
    "only exact duplicate observations."
)


award_version_keys = [
    "award_id",
    "release_id"
]

award_version_duplicates = awards.duplicated(
    subset=award_version_keys,
    keep=False
).sum()

print(
    f"\nRepeated award-version rows: "
    f"{award_version_duplicates:,}"
)


# Remove exact duplicate observations at award-version grain.
#
# source_file is deliberately excluded from the duplicate test because
# it represents lineage, not a business attribute.

award_compare_columns = [
    column
    for column in awards.columns
    if column != "source_file"
]

awards["_award_version_hash"] = (
    awards[award_compare_columns]
    .fillna("<NULL>")
    .astype(str)
    .agg("|".join, axis=1)
)

before_awards = len(awards)

awards = (
    awards
    .drop_duplicates(
        subset=["award_id", "release_id", "_award_version_hash"],
        keep="first"
    )
    .reset_index(drop=True)
)

removed_award_duplicates = before_awards - len(awards)

awards = awards.drop(
    columns=["_award_version_hash"]
)

print(
    f"Exact duplicate award-version rows removed: "
    f"{removed_award_duplicates:,}"
)

print(
    f"Final award-version rows: "
    f"{len(awards):,}"
)


# ============================================================
# 5. CREATE AWARD VERSION METADATA
# ============================================================

print("\nCreating award lifecycle metadata...")

awards["release_date"] = pd.to_datetime(
    awards["release_date"],
    errors="coerce",
    utc=True
)

awards["award_date"] = pd.to_datetime(
    awards["award_date"],
    errors="coerce",
    utc=True
)

awards["contract_start"] = pd.to_datetime(
    awards["contract_start"],
    errors="coerce",
    utc=True
)

awards["contract_end"] = pd.to_datetime(
    awards["contract_end"],
    errors="coerce",
    utc=True
)


# Sort so the latest release is last
awards = awards.sort_values(
    ["award_id", "release_date", "release_id"]
).reset_index(drop=True)


# Version number within award lifecycle
awards["award_version_number"] = (
    awards
    .groupby("award_id")
    .cumcount() + 1
)


# Number of observed versions
awards["award_version_count"] = (
    awards
    .groupby("award_id")["award_id"]
    .transform("count")
)


awards["is_latest_award_version"] = (
    awards["award_version_number"]
    ==
    awards["award_version_count"]
)


# ============================================================
# 6. SUPPLIER RELATIONSHIP CLEANING
# ============================================================

print("\n" + "=" * 70)
print("STEP 3: SUPPLIER RELATIONSHIP RESOLUTION")
print("=" * 70)


# Clean supplier index
if "supplier_index" in relationships.columns:

    relationships["supplier_index"] = pd.to_numeric(
        relationships["supplier_index"],
        errors="coerce"
    )


# Create source-observation key.
#
# This deliberately uses supplier_index because supplier_id is known
# to be unreliable in some records.

relationships["relationship_observation_key"] = (
    relationships["award_id"].astype(str)
    + "|"
    + relationships["release_id"].astype(str)
    + "|"
    + relationships["supplier_index"].astype(str)
)


# ============================================================
# 7. REMOVE EXACT DUPLICATE RELATIONSHIP OBSERVATIONS
# ============================================================

relationship_compare_columns = [
    column
    for column in relationships.columns
    if column not in [
        "source_file",
        "relationship_observation_key"
    ]
]

relationships["_relationship_hash"] = (
    relationships[relationship_compare_columns]
    .fillna("<NULL>")
    .astype(str)
    .agg("|".join, axis=1)
)


before_relationships = len(relationships)

relationships = (
    relationships
    .drop_duplicates(
        subset=[
            "relationship_observation_key",
            "_relationship_hash"
        ],
        keep="first"
    )
    .reset_index(drop=True)
)

removed_relationship_duplicates = (
    before_relationships - len(relationships)
)

relationships = relationships.drop(
    columns=["_relationship_hash"]
)


print(
    f"Exact duplicate relationship rows removed: "
    f"{removed_relationship_duplicates:,}"
)

print(
    f"Relationship observations retained: "
    f"{len(relationships):,}"
)


# ============================================================
# 8. IDENTIFY SUPPLIER ID QUALITY
# ============================================================

print("\nAssessing supplier identifier quality...")


relationships["supplier_id_quality"] = np.where(
    relationships["supplier_id"].apply(
        is_unreliable_supplier_id
    ),
    "unreliable",
    "usable"
)


# ============================================================
# 9. CREATE ANALYTICAL SUPPLIER KEY
# ============================================================

print("Creating analytical supplier keys...")


relationships["supplier_key"] = relationships.apply(
    supplier_identity_key,
    axis=1
)


# ============================================================
# 10. SUPPLIER ID / NAME CONSISTENCY CHECK
# ============================================================

print("Checking supplier identity consistency...")


supplier_id_name_counts = (
    relationships
    .groupby("supplier_id", dropna=False)
    .agg(
        relationship_count=(
            "supplier_id",
            "size"
        ),
        distinct_supplier_names=(
            "supplier_name_normalized",
            "nunique"
        )
    )
    .reset_index()
)


supplier_id_name_counts = (
    supplier_id_name_counts
    .sort_values(
        ["distinct_supplier_names", "relationship_count"],
        ascending=[False, False]
    )
)


supplier_id_name_counts.to_csv(
    DQ_DIR / "supplier_id_name_quality_2025.csv",
    index=False
)


# ============================================================
# 11. FLAG SUPPLIER IDENTITY
# ============================================================

print("Assigning supplier identity flags...")


# Count names associated with each supplier ID
relationships["supplier_id_name_count"] = (
    relationships
    .groupby("supplier_id")[
        "supplier_name_normalized"
    ]
    .transform("nunique")
)


def classify_supplier_identity(row):

    supplier_id = row["supplier_id"]

    # No reliable supplier ID
    if is_unreliable_supplier_id(supplier_id):

        return "unreliable_id_name_based"

    # One consistent name
    if row["supplier_id_name_count"] <= 1:

        return "confirmed_id"

    # Multiple names under same ID.
    #
    # We do not automatically call this a conflict because many
    # differences are legal-name/trading-name variations.
    #
    # Keep the supplier ID but flag it for review.

    return "id_multiple_names_review"


relationships["supplier_identity_flag"] = (
    relationships.apply(
        classify_supplier_identity,
        axis=1
    )
)


# ============================================================
# 12. SUPPLIER MASTER
# ============================================================

print("\n" + "=" * 70)
print("STEP 4: BUILDING SUPPLIER MASTER")
print("=" * 70)


# For reliable IDs:
#   supplier_key = SUP_ID:<supplier_id>
#
# For unreliable IDs:
#   supplier_key = NAME:<comparison name>
#
# We retain the most frequently reported supplier name as the
# canonical display name.

supplier_master = (
    relationships
    .groupby("supplier_key", dropna=False)
    .agg(
        supplier_id=(
            "supplier_id",
            lambda x: next(
                (
                    str(v)
                    for v in x
                    if not is_unreliable_supplier_id(v)
                ),
                None
            )
        ),
        canonical_supplier_name=(
            "supplier_name",
            lambda x: (
                x.dropna()
                .value_counts()
                .index[0]
                if len(x.dropna()) > 0
                else None
            )
        ),
        reported_name_count=(
            "supplier_name_normalized",
            "nunique"
        ),
        relationship_count=(
            "supplier_key",
            "size"
        )
    )
    .reset_index()
)


supplier_master["supplier_id_quality"] = np.where(
    supplier_master["supplier_id"].isna(),
    "unreliable_or_missing",
    "usable"
)


supplier_master["identity_review_flag"] = np.where(
    supplier_master["reported_name_count"] > 1,
    "review_name_variation",
    "no_name_conflict"
)


supplier_master = supplier_master.sort_values(
    ["relationship_count", "canonical_supplier_name"],
    ascending=[False, True]
).reset_index(drop=True)


print(
    f"Supplier master rows: "
    f"{len(supplier_master):,}"
)


# ============================================================
# 13. ADD SUPPLIER MASTER FIELDS TO RELATIONSHIPS
# ============================================================

relationships = relationships.merge(
    supplier_master[
        [
            "supplier_key",
            "canonical_supplier_name",
            "identity_review_flag"
        ]
    ],
    on="supplier_key",
    how="left"
)


# ============================================================
# 14. CREATE PROCUREMENT MASTER
# ============================================================

print("\n" + "=" * 70)
print("STEP 5: BUILDING PROCUREMENT MASTER")
print("=" * 70)


# Use releases as the source of procurement-level observations.
#
# One procurement = one OCID.
#
# We take the latest release observation for each OCID where
# possible, while retaining release history separately.

if "release_date" in releases.columns:

    releases["release_date"] = pd.to_datetime(
        releases["release_date"],
        errors="coerce",
        utc=True
    )


# Determine latest release for each OCID
releases_sorted = releases.sort_values(
    ["ocid", "release_date", "release_id"]
)


latest_release = (
    releases_sorted
    .drop_duplicates(
        subset=["ocid"],
        keep="last"
    )
    .copy()
)


# Fields available at procurement level.
#
# Only use fields that actually exist in the dataset.

preferred_procurement_fields = [
    "ocid",
    "tender_title",
    "tender_status",
    "buyer_name",
    "buyer_id",
    "procurement_method",
    "procurement_category",
    "cpv_code",
    "tender_value",
    "tender_currency"
]


available_procurement_fields = [
    column
    for column in preferred_procurement_fields
    if column in latest_release.columns
]


procurements = latest_release[
    available_procurement_fields
].copy()


# If some expected procurement fields are absent, that is okay.
print(
    f"Procurement master rows: "
    f"{len(procurements):,}"
)


# ============================================================
# 15. RESOLUTION LOG
# ============================================================

print("\nCreating resolution log...")


resolution_log = pd.DataFrame(
    [
        {
            "issue_type": "release_duplicates",
            "rule": (
                "Repeated release_id values were confirmed "
                "exact-identical and reduced to one observation."
            ),
            "action": "deduplicated",
            "rows_removed": release_duplicate_count - release_duplicate_groups
        },
        {
            "issue_type": "award_versions",
            "rule": (
                "Award history preserved at award_id + release_id grain."
            ),
            "action": "preserved",
            "rows_removed": removed_award_duplicates
        },
        {
            "issue_type": "supplier_relationship_duplicates",
            "rule": (
                "Exact duplicate source observations removed using "
                "award_id + release_id + supplier_index."
            ),
            "action": "deduplicated_exact_only",
            "rows_removed": removed_relationship_duplicates
        },
        {
            "issue_type": "unreliable_supplier_ids",
            "rule": (
                "Known placeholder IDs such as GB-COH-0 and GB-COH-NA "
                "are not used as supplier identity keys."
            ),
            "action": "name_based_identity",
            "rows_removed": 0
        },
        {
            "issue_type": "supplier_name_variations",
            "rule": (
                "Original names preserved; reliable supplier IDs remain "
                "the primary analytical identity."
            ),
            "action": "preserved_and_flagged",
            "rows_removed": 0
        },
        {
            "issue_type": "award_lifecycle_updates",
            "rule": (
                "Changed award values or contract dates across release "
                "dates are retained as lifecycle versions."
            ),
            "action": "preserved",
            "rows_removed": 0
        }
    ]
)


# ============================================================
# 16. DATA QUALITY SUMMARY
# ============================================================

print("Creating data quality summary...")


quality_summary = pd.DataFrame(
    [
        {
            "metric": "normalized_releases",
            "value": len(pd.read_csv(RELEASES_FILE))
        },
        {
            "metric": "final_releases",
            "value": len(releases)
        },
        {
            "metric": "normalized_awards",
            "value": len(pd.read_csv(AWARDS_FILE))
        },
        {
            "metric": "final_award_versions",
            "value": len(awards)
        },
        {
            "metric": "normalized_relationships",
            "value": len(pd.read_csv(RELATIONSHIPS_FILE))
        },
        {
            "metric": "final_relationships",
            "value": len(relationships)
        },
        {
            "metric": "procurements",
            "value": len(procurements)
        },
        {
            "metric": "suppliers",
            "value": len(supplier_master)
        },
        {
            "metric": "supplier_relationships_flagged_for_review",
            "value": int(
                (
                    relationships["supplier_identity_flag"]
                    == "id_multiple_names_review"
                ).sum()
            )
        },
        {
            "metric": "unreliable_supplier_relationships",
            "value": int(
                (
                    relationships["supplier_identity_flag"]
                    == "unreliable_id_name_based"
                ).sum()
            )
        }
    ]
)


# ============================================================
# 17. SAVE FINAL DATASETS
# ============================================================

print("\n" + "=" * 70)
print("STEP 6: SAVING FINAL ANALYTICAL DATASETS")
print("=" * 70)


releases.to_csv(
    OUTPUT_DIR / "releases_2025.csv",
    index=False
)

awards.to_csv(
    OUTPUT_DIR / "award_versions_2025.csv",
    index=False
)

relationships.to_csv(
    OUTPUT_DIR / "award_suppliers_2025.csv",
    index=False
)

supplier_master.to_csv(
    OUTPUT_DIR / "suppliers_2025.csv",
    index=False
)

procurements.to_csv(
    OUTPUT_DIR / "procurements_2025.csv",
    index=False
)


resolution_log.to_csv(
    DQ_DIR / "resolution_log_2025.csv",
    index=False
)

quality_summary.to_csv(
    DQ_DIR / "data_quality_summary_2025.csv",
    index=False
)


# ============================================================
# 18. FINAL VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("FINAL VALIDATION")
print("=" * 70)


print(
    f"\nFinal procurements:       {len(procurements):,}"
)

print(
    f"Final releases:           {len(releases):,}"
)

print(
    f"Final award versions:     {len(awards):,}"
)

print(
    f"Final supplier relations: {len(relationships):,}"
)

print(
    f"Final suppliers:          {len(supplier_master):,}"
)


# Referential integrity checks

procurement_ocids = set(
    procurements["ocid"].dropna()
)

release_ocids = set(
    releases["ocid"].dropna()
)

award_ocids = set(
    awards["ocid"].dropna()
)

print("\nReferential integrity:")

print(
    "  Release OCIDs missing from procurement master:",
    len(release_ocids - procurement_ocids)
)

print(
    "  Award OCIDs missing from procurement master:",
    len(award_ocids - procurement_ocids)
)


award_ids = set(
    awards["award_id"].dropna()
)

relationship_award_ids = set(
    relationships["award_id"].dropna()
)

print(
    "  Relationship awards missing from award table:",
    len(relationship_award_ids - award_ids)
)


supplier_keys = set(
    supplier_master["supplier_key"].dropna()
)

relationship_supplier_keys = set(
    relationships["supplier_key"].dropna()
)

print(
    "  Relationship supplier keys missing from supplier master:",
    len(relationship_supplier_keys - supplier_keys)
)


# ============================================================
# 19. FINAL MESSAGE
# ============================================================

print("\n" + "=" * 70)
print("CONFLICT RESOLUTION COMPLETE")
print("=" * 70)

print(
    "\nThe normalized source datasets were not modified."
)

print(
    "\nFinal analytical files:"
)

print(
    f"  {OUTPUT_DIR / 'procurements_2025.csv'}"
)

print(
    f"  {OUTPUT_DIR / 'releases_2025.csv'}"
)

print(
    f"  {OUTPUT_DIR / 'award_versions_2025.csv'}"
)

print(
    f"  {OUTPUT_DIR / 'award_suppliers_2025.csv'}"
)

print(
    f"  {OUTPUT_DIR / 'suppliers_2025.csv'}"
)

print(
    "\nData-quality documentation:"
)

print(
    f"  {DQ_DIR / 'resolution_log_2025.csv'}"
)

print(
    f"  {DQ_DIR / 'data_quality_summary_2025.csv'}"
)

print(
    "\nIMPORTANT:"
)

print(
    "Do not create the SQLite database yet."
)

print(
    "First validate the final analytical datasets."
)

print("=" * 70)