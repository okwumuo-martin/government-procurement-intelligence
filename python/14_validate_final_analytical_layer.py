"""
14_validate_final_analytical_layer.py

Contracts Finder 2025
Final Analytical Layer Quality Gate

Purpose
-------
Validates the five analytical datasets produced by
13_resolve_duplicate_conflicts.py before SQLite creation.

This script does NOT modify any data.
"""

from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

FINAL_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "final"
)

DQ_DIR = FINAL_DIR / "data_quality"

REPORT_FILE = (
    DQ_DIR
    / "final_analytical_layer_validation.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("CONTRACTS FINDER 2025")
print("FINAL ANALYTICAL LAYER QUALITY GATE")
print("=" * 70)

print("\nLoading final analytical datasets...")

procurements = pd.read_csv(
    FINAL_DIR / "procurements_2025.csv"
)

releases = pd.read_csv(
    FINAL_DIR / "releases_2025.csv"
)

awards = pd.read_csv(
    FINAL_DIR / "award_versions_2025.csv"
)

relationships = pd.read_csv(
    FINAL_DIR / "award_suppliers_2025.csv"
)

suppliers = pd.read_csv(
    FINAL_DIR / "suppliers_2025.csv"
)

print(
    f"Procurements:       {len(procurements):,}"
)

print(
    f"Releases:           {len(releases):,}"
)

print(
    f"Award versions:     {len(awards):,}"
)

print(
    f"Relationships:      {len(relationships):,}"
)

print(
    f"Suppliers:          {len(suppliers):,}"
)


results = []


def record(
    category,
    test,
    status,
    value,
    expected,
    notes=""
):
    results.append(
        {
            "category": category,
            "test": test,
            "status": status,
            "value": value,
            "expected": expected,
            "notes": notes
        }
    )


# ============================================================
# SECTION 1 — PRIMARY KEY CHECKS
# ============================================================

print("\n" + "=" * 70)
print("1. PRIMARY KEY VALIDATION")
print("=" * 70)


# -----------------------------
# Procurement
# -----------------------------

null_ocid = procurements["ocid"].isna().sum()

duplicate_ocid = (
    procurements["ocid"]
    .duplicated()
    .sum()
)

print(
    f"\nProcurement OCID nulls:       {null_ocid}"
)

print(
    f"Procurement OCID duplicates:  {duplicate_ocid}"
)

record(
    "Primary keys",
    "procurements.ocid.null",
    "PASS" if null_ocid == 0 else "FAIL",
    null_ocid,
    0
)

record(
    "Primary keys",
    "procurements.ocid.duplicate",
    "PASS" if duplicate_ocid == 0 else "FAIL",
    duplicate_ocid,
    0
)


# -----------------------------
# Releases
# -----------------------------

null_release_id = releases["release_id"].isna().sum()

duplicate_release_id = (
    releases["release_id"]
    .duplicated()
    .sum()
)

print(
    f"\nRelease ID nulls:             {null_release_id}"
)

print(
    f"Release ID duplicates:        {duplicate_release_id}"
)

record(
    "Primary keys",
    "releases.release_id.null",
    "PASS" if null_release_id == 0 else "FAIL",
    null_release_id,
    0
)

record(
    "Primary keys",
    "releases.release_id.duplicate",
    "PASS" if duplicate_release_id == 0 else "FAIL",
    duplicate_release_id,
    0
)


# -----------------------------
# Award versions
# -----------------------------

award_key = [
    "award_id",
    "release_id"
]

null_award_id = awards["award_id"].isna().sum()

null_award_release = awards["release_id"].isna().sum()

duplicate_award_versions = (
    awards
    .duplicated(subset=award_key)
    .sum()
)

print(
    f"\nAward ID nulls:               {null_award_id}"
)

print(
    f"Award release ID nulls:       {null_award_release}"
)

print(
    f"Duplicate award versions:     {duplicate_award_versions}"
)

record(
    "Primary keys",
    "awards.award_id.null",
    "PASS" if null_award_id == 0 else "FAIL",
    null_award_id,
    0
)

record(
    "Primary keys",
    "awards.release_id.null",
    "PASS" if null_award_release == 0 else "FAIL",
    null_award_release,
    0
)

record(
    "Primary keys",
    "awards.award_id_release_id.duplicate",
    "PASS" if duplicate_award_versions == 0 else "FAIL",
    duplicate_award_versions,
    0
)


# -----------------------------
# Supplier master
# -----------------------------

null_supplier_key = suppliers["supplier_key"].isna().sum()

duplicate_supplier_key = (
    suppliers["supplier_key"]
    .duplicated()
    .sum()
)

print(
    f"\nSupplier key nulls:           {null_supplier_key}"
)

print(
    f"Supplier key duplicates:      {duplicate_supplier_key}"
)

record(
    "Primary keys",
    "suppliers.supplier_key.null",
    "PASS" if null_supplier_key == 0 else "FAIL",
    null_supplier_key,
    0
)

record(
    "Primary keys",
    "suppliers.supplier_key.duplicate",
    "PASS" if duplicate_supplier_key == 0 else "FAIL",
    duplicate_supplier_key,
    0
)


# ============================================================
# SECTION 2 — RELATIONSHIP GRAIN
# ============================================================

print("\n" + "=" * 70)
print("2. RELATIONSHIP GRAIN VALIDATION")
print("=" * 70)


relationship_key = [
    "award_id",
    "release_id",
    "supplier_index"
]

relationship_duplicates = (
    relationships
    .duplicated(subset=relationship_key)
    .sum()
)

print(
    f"\nDuplicate relationship observations: "
    f"{relationship_duplicates}"
)

record(
    "Relationship grain",
    "award_release_supplier_index_duplicate",
    "PASS" if relationship_duplicates == 0 else "FAIL",
    relationship_duplicates,
    0
)


# ============================================================
# SECTION 3 — AWARD VERSION LOGIC
# ============================================================

print("\n" + "=" * 70)
print("3. AWARD VERSION LOGIC")
print("=" * 70)


version_number_nulls = (
    awards["award_version_number"]
    .isna()
    .sum()
)

version_count_nulls = (
    awards["award_version_count"]
    .isna()
    .sum()
)

latest_flag_nulls = (
    awards["is_latest_award_version"]
    .isna()
    .sum()
)


invalid_version_numbers = (
    awards["award_version_number"]
    <= 0
).sum()


print(
    f"\nVersion number nulls:         {version_number_nulls}"
)

print(
    f"Version count nulls:          {version_count_nulls}"
)

print(
    f"Latest flag nulls:            {latest_flag_nulls}"
)

print(
    f"Invalid version numbers:      {invalid_version_numbers}"
)


record(
    "Award lifecycle",
    "award_version_number.null",
    "PASS" if version_number_nulls == 0 else "FAIL",
    version_number_nulls,
    0
)

record(
    "Award lifecycle",
    "award_version_count.null",
    "PASS" if version_count_nulls == 0 else "FAIL",
    version_count_nulls,
    0
)

record(
    "Award lifecycle",
    "is_latest_award_version.null",
    "PASS" if latest_flag_nulls == 0 else "FAIL",
    latest_flag_nulls,
    0
)

record(
    "Award lifecycle",
    "award_version_number.invalid",
    "PASS" if invalid_version_numbers == 0 else "FAIL",
    invalid_version_numbers,
    0
)


# Verify exactly one latest version per award
latest_counts = (
    awards
    .groupby("award_id")[
        "is_latest_award_version"
    ]
    .sum()
)

awards_without_one_latest = (
    latest_counts != 1
).sum()

print(
    f"Awards without exactly one latest version: "
    f"{awards_without_one_latest}"
)

record(
    "Award lifecycle",
    "exactly_one_latest_version_per_award",
    "PASS"
    if awards_without_one_latest == 0
    else "FAIL",
    awards_without_one_latest,
    0
)


# ============================================================
# SECTION 4 — REFERENTIAL INTEGRITY
# ============================================================

print("\n" + "=" * 70)
print("4. REFERENTIAL INTEGRITY")
print("=" * 70)


procurement_ocids = set(
    procurements["ocid"].dropna()
)

release_ocids = set(
    releases["ocid"].dropna()
)

award_ocids = set(
    awards["ocid"].dropna()
)

release_missing_procurement = (
    release_ocids - procurement_ocids
)

award_missing_procurement = (
    award_ocids - procurement_ocids
)


award_ids = set(
    awards["award_id"].dropna()
)

relationship_awards = set(
    relationships["award_id"].dropna()
)

relationship_missing_awards = (
    relationship_awards - award_ids
)


supplier_keys = set(
    suppliers["supplier_key"].dropna()
)

relationship_supplier_keys = set(
    relationships["supplier_key"].dropna()
)

relationship_missing_suppliers = (
    relationship_supplier_keys - supplier_keys
)


print(
    "\nRelease OCIDs missing procurement:",
    len(release_missing_procurement)
)

print(
    "Award OCIDs missing procurement:",
    len(award_missing_procurement)
)

print(
    "Relationship awards missing awards:",
    len(relationship_missing_awards)
)

print(
    "Relationship suppliers missing supplier master:",
    len(relationship_missing_suppliers)
)


record(
    "Referential integrity",
    "release_to_procurement",
    "PASS"
    if len(release_missing_procurement) == 0
    else "FAIL",
    len(release_missing_procurement),
    0
)

record(
    "Referential integrity",
    "award_to_procurement",
    "PASS"
    if len(award_missing_procurement) == 0
    else "FAIL",
    len(award_missing_procurement),
    0
)

record(
    "Referential integrity",
    "relationship_to_award",
    "PASS"
    if len(relationship_missing_awards) == 0
    else "FAIL",
    len(relationship_missing_awards),
    0
)

record(
    "Referential integrity",
    "relationship_to_supplier",
    "PASS"
    if len(relationship_missing_suppliers) == 0
    else "FAIL",
    len(relationship_missing_suppliers),
    0
)


# ============================================================
# SECTION 5 — SUPPLIER IDENTITY QUALITY
# ============================================================

print("\n" + "=" * 70)
print("5. SUPPLIER IDENTITY QUALITY")
print("=" * 70)


identity_counts = (
    relationships[
        "supplier_identity_flag"
    ]
    .value_counts(dropna=False)
)

for identity_flag, count in identity_counts.items():

    print(
        f"{identity_flag}: {count:,}"
    )


review_count = int(
    (
        relationships[
            "supplier_identity_flag"
        ]
        == "id_multiple_names_review"
    ).sum()
)

unreliable_count = int(
    (
        relationships[
            "supplier_identity_flag"
        ]
        == "unreliable_id_name_based"
    ).sum()
)


record(
    "Supplier identity",
    "relationships_flagged_multiple_names",
    "INFO",
    review_count,
    "review"
)

record(
    "Supplier identity",
    "relationships_unreliable_ids",
    "INFO",
    unreliable_count,
    "review"
)


# ============================================================
# SECTION 6 — MISSING VALUES
# ============================================================

print("\n" + "=" * 70)
print("6. KEY FIELD COMPLETENESS")
print("=" * 70)


def check_missing(
    df,
    dataset_name,
    columns
):

    for column in columns:

        if column not in df.columns:
            continue

        missing = int(
            df[column].isna().sum()
        )

        total = len(df)

        percentage = (
            missing / total * 100
            if total > 0
            else 0
        )

        print(
            f"{dataset_name}.{column}: "
            f"{missing:,} missing "
            f"({percentage:.2f}%)"
        )

        record(
            "Completeness",
            f"{dataset_name}.{column}.missing",
            "INFO",
            missing,
            "source-dependent",
            f"{percentage:.2f}% missing"
        )


check_missing(
    procurements,
    "procurements",
    [
        "ocid",
        "tender_title",
        "buyer_name",
        "procurement_method",
        "procurement_category",
        "tender_value"
    ]
)


check_missing(
    releases,
    "releases",
    [
        "release_id",
        "ocid",
        "release_date"
    ]
)


check_missing(
    awards,
    "awards",
    [
        "award_id",
        "release_id",
        "award_date",
        "award_value",
        "contract_start",
        "contract_end"
    ]
)


check_missing(
    relationships,
    "relationships",
    [
        "award_id",
        "supplier_id",
        "supplier_name",
        "supplier_key"
    ]
)


check_missing(
    suppliers,
    "suppliers",
    [
        "supplier_key",
        "canonical_supplier_name"
    ]
)


# ============================================================
# SECTION 7 — NUMERIC SANITY CHECKS
# ============================================================

print("\n" + "=" * 70)
print("7. NUMERIC SANITY CHECKS")
print("=" * 70)


if "tender_value" in procurements.columns:

    procurements["tender_value"] = pd.to_numeric(
        procurements["tender_value"],
        errors="coerce"
    )

    negative_tender_values = (
        procurements["tender_value"] < 0
    ).sum()

    print(
        f"\nNegative tender values: "
        f"{negative_tender_values}"
    )

    record(
        "Numeric validity",
        "negative_tender_values",
        "PASS"
        if negative_tender_values == 0
        else "REVIEW",
        int(negative_tender_values),
        0
    )


if "award_value" in awards.columns:

    awards["award_value"] = pd.to_numeric(
        awards["award_value"],
        errors="coerce"
    )

    negative_award_values = (
        awards["award_value"] < 0
    ).sum()

    print(
        f"Negative award values: "
        f"{negative_award_values}"
    )

    record(
        "Numeric validity",
        "negative_award_values",
        "PASS"
        if negative_award_values == 0
        else "REVIEW",
        int(negative_award_values),
        0
    )


# ============================================================
# SECTION 8 — DATE SANITY
# ============================================================

print("\n" + "=" * 70)
print("8. DATE SANITY")
print("=" * 70)


for column in [
    "release_date",
    "award_date",
    "contract_start",
    "contract_end"
]:

    if column in awards.columns:

        awards[column] = pd.to_datetime(
            awards[column],
            errors="coerce",
            utc=True
        )


if "contract_start" in awards.columns and \
   "contract_end" in awards.columns:

    invalid_contract_dates = (
        (
            awards["contract_end"].notna()
        )
        &
        (
            awards["contract_start"].notna()
        )
        &
        (
            awards["contract_end"]
            <
            awards["contract_start"]
        )
    ).sum()

    print(
        f"\nContract end before contract start: "
        f"{invalid_contract_dates}"
    )

    record(
        "Date validity",
        "contract_end_before_start",
        "PASS"
        if invalid_contract_dates == 0
        else "REVIEW",
        int(invalid_contract_dates),
        0
    )


# ============================================================
# SECTION 9 — DATASET STRUCTURE
# ============================================================

print("\n" + "=" * 70)
print("9. DATASET STRUCTURE")
print("=" * 70)


datasets = {
    "procurements": procurements,
    "releases": releases,
    "award_versions": awards,
    "award_suppliers": relationships,
    "suppliers": suppliers
}


for name, df in datasets.items():

    print(
        f"{name}: "
        f"{df.shape[0]:,} rows × "
        f"{df.shape[1]:,} columns"
    )

    record(
        "Structure",
        f"{name}.row_count",
        "INFO",
        len(df),
        "documented"
    )

    record(
        "Structure",
        f"{name}.column_count",
        "INFO",
        len(df.columns),
        "documented"
    )


# ============================================================
# SECTION 10 — OVERALL RESULT
# ============================================================

print("\n" + "=" * 70)
print("QUALITY GATE RESULT")
print("=" * 70)


results_df = pd.DataFrame(results)

results_df.to_csv(
    REPORT_FILE,
    index=False
)


failures = results_df[
    results_df["status"] == "FAIL"
]

reviews = results_df[
    results_df["status"] == "REVIEW"
]


print(
    f"\nTests recorded: {len(results_df):,}"
)

print(
    f"Failures:       {len(failures):,}"
)

print(
    f"Review items:   {len(reviews):,}"
)


if len(failures) == 0:

    print(
        "\nQUALITY GATE: PASSED"
    )

    print(
        "\nNo structural or referential-integrity "
        "failures were detected."
    )

    print(
        "\nThe analytical layer is ready for "
        "SQLite schema creation."
    )

else:

    print(
        "\nQUALITY GATE: FAILED"
    )

    print(
        "\nThe following tests require attention:"
    )

    print(
        failures[
            [
                "category",
                "test",
                "value",
                "expected",
                "notes"
            ]
        ].to_string(index=False)
    )


print(
    f"\nValidation report saved to:"
)

print(
    f"  {REPORT_FILE}"
)

print("=" * 70)