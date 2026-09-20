from pathlib import Path
import pandas as pd


# ============================================================
# CONTRACTS FINDER 2025
# DUPLICATE CONFLICT INVESTIGATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CONFLICT_DIR = PROCESSED_DIR / "duplicate_conflicts"

AWARDS_FILE = PROCESSED_DIR / "awards_2025.csv"
RELATIONSHIPS_FILE = PROCESSED_DIR / "award_suppliers_2025.csv"


print("=" * 70)
print("CONTRACTS FINDER 2025")
print("DUPLICATE CONFLICT INVESTIGATION")
print("=" * 70)


# ============================================================
# 1. LOAD DATA
# ============================================================

print("\nLoading datasets...")

awards = pd.read_csv(
    AWARDS_FILE,
    low_memory=False
)

relationships = pd.read_csv(
    RELATIONSHIPS_FILE,
    low_memory=False
)

print(f"Awards:              {len(awards):,}")
print(f"Award-supplier rows: {len(relationships):,}")


# ============================================================
# 2. HELPER
# ============================================================

def show_value_changes(group, columns):
    """
    Show columns whose values differ within a duplicate group.
    """

    changes = {}

    for column in columns:

        values = (
            group[column]
            .fillna("<NA>")
            .astype(str)
            .str.strip()
            .unique()
        )

        if len(values) > 1:
            changes[column] = list(values)

    return changes


# ============================================================
# 3. AWARD CONFLICTS
# ============================================================

print("\n" + "=" * 70)
print("SECTION 1: AWARD CONFLICTS")
print("=" * 70)

award_key = "award_id"

award_counts = (
    awards.groupby(award_key)
    .size()
)

repeated_awards = award_counts[
    award_counts > 1
].index

award_conflicts_found = []

for award_id in repeated_awards:

    group = awards[
        awards["award_id"] == award_id
    ].copy()

    # Ignore source_file because it is expected to differ
    comparison_columns = [
        col
        for col in group.columns
        if col != "source_file"
        and col != "award_id"
    ]

    changes = show_value_changes(
        group,
        comparison_columns
    )

    if changes:

        award_conflicts_found.append(
            {
                "award_id": award_id,
                "records": len(group),
                "changed_fields": changes
            }
        )


print(
    f"\nAward conflict groups found: "
    f"{len(award_conflicts_found)}"
)


for number, conflict in enumerate(
    award_conflicts_found,
    start=1
):

    award_id = conflict["award_id"]

    group = awards[
        awards["award_id"] == award_id
    ].copy()

    print("\n" + "-" * 70)
    print(f"AWARD CONFLICT {number}")
    print("-" * 70)

    print(f"Award ID: {award_id}")

    print("\nFields that changed:")

    for field, values in conflict["changed_fields"].items():

        print(f"\n  {field}:")

        for value in values:
            print(f"    - {value}")

    print("\nFull records:")

    display_columns = [
        "ocid",
        "release_id",
        "release_date",
        "award_id",
        "award_status",
        "award_date",
        "award_value",
        "award_currency",
        "contract_start",
        "contract_end",
        "source_file"
    ]

    display_columns = [
        col
        for col in display_columns
        if col in group.columns
    ]

    print(
        group[display_columns]
        .to_string(index=False)
    )


# ============================================================
# 4. AWARD CONFLICT SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("AWARD CONFLICT INTERPRETATION")
print("=" * 70)

print(
    """
These conflicts require special handling.

A repeated award_id does NOT automatically mean that one
record should be deleted.

If award_value, contract_end, or another business field
changes between release dates, this may represent a legitimate
award lifecycle update.

We will preserve these records until the analytical model
defines how award versions should be represented.
"""
)


# ============================================================
# 5. SUPPLIER RELATIONSHIP CONFLICTS
# ============================================================

print("\n" + "=" * 70)
print("SECTION 2: AWARD-SUPPLIER CONFLICTS")
print("=" * 70)

relationship_key = [
    "award_id",
    "supplier_id"
]

relationship_counts = (
    relationships
    .groupby(
        relationship_key,
        dropna=False
    )
    .size()
)

repeated_relationships = relationship_counts[
    relationship_counts > 1
].index


supplier_conflicts_found = []


for key in repeated_relationships:

    award_id = key[0]
    supplier_id = key[1]

    group = relationships[
        (relationships["award_id"] == award_id)
        &
        (
            relationships["supplier_id"]
            == supplier_id
        )
    ].copy()

    comparison_columns = [
        col
        for col in group.columns
        if col not in [
            "source_file",
            "award_id",
            "supplier_id"
        ]
    ]

    changes = show_value_changes(
        group,
        comparison_columns
    )

    if changes:

        supplier_conflicts_found.append(
            {
                "award_id": award_id,
                "supplier_id": supplier_id,
                "records": len(group),
                "changed_fields": changes
            }
        )


print(
    f"\nSupplier relationship conflict groups found: "
    f"{len(supplier_conflicts_found)}"
)


for number, conflict in enumerate(
    supplier_conflicts_found,
    start=1
):

    award_id = conflict["award_id"]
    supplier_id = conflict["supplier_id"]

    group = relationships[
        (relationships["award_id"] == award_id)
        &
        (
            relationships["supplier_id"]
            == supplier_id
        )
    ].copy()

    print("\n" + "-" * 70)
    print(
        f"SUPPLIER RELATIONSHIP CONFLICT {number}"
    )
    print("-" * 70)

    print(f"Award ID:    {award_id}")
    print(f"Supplier ID: {supplier_id}")

    print("\nFields that changed:")

    for field, values in conflict["changed_fields"].items():

        print(f"\n  {field}:")

        for value in values:
            print(f"    - {value}")

    print("\nFull records:")

    display_columns = [
        "ocid",
        "release_id",
        "award_id",
        "supplier_index",
        "supplier_id",
        "supplier_name",
        "supplier_name_normalized",
        "source_file"
    ]

    display_columns = [
        col
        for col in display_columns
        if col in group.columns
    ]

    print(
        group[display_columns]
        .to_string(index=False)
    )


# ============================================================
# 6. SUPPLIER ID QUALITY CHECK
# ============================================================

print("\n" + "=" * 70)
print("SECTION 3: SUPPLIER ID QUALITY")
print("=" * 70)


supplier_id_summary = (
    relationships
    .groupby("supplier_id", dropna=False)
    .agg(
        relationship_count=("award_id", "size"),
        distinct_supplier_names=(
            "supplier_name",
            "nunique"
        )
    )
    .reset_index()
)


problem_supplier_ids = supplier_id_summary[
    supplier_id_summary[
        "distinct_supplier_names"
    ] > 1
].copy()


print(
    f"\nSupplier IDs associated with "
    f"multiple supplier names: "
    f"{len(problem_supplier_ids):,}"
)


print(
    "\nTop examples:"
)

print(
    problem_supplier_ids
    .sort_values(
        "distinct_supplier_names",
        ascending=False
    )
    .head(20)
    .to_string(index=False)
)


# ============================================================
# 7. PLACEHOLDER / SUSPICIOUS SUPPLIER IDS
# ============================================================

print("\n" + "=" * 70)
print("SECTION 4: SUSPICIOUS SUPPLIER IDs")
print("=" * 70)


supplier_ids = (
    relationships["supplier_id"]
    .dropna()
    .astype(str)
    .str.strip()
)


suspicious_ids = supplier_ids[
    supplier_ids.str.endswith("-0")
    |
    supplier_ids.str.contains(
        r"^GB-COH-0$",
        regex=True
    )
].unique()


print(
    f"\nPotential placeholder IDs found: "
    f"{len(suspicious_ids):,}"
)

for supplier_id in suspicious_ids[:50]:

    names = (
        relationships.loc[
            relationships["supplier_id"]
            == supplier_id,
            "supplier_name"
        ]
        .dropna()
        .astype(str)
        .unique()
    )

    print(
        f"\n{supplier_id}"
    )

    for name in names[:20]:
        print(f"  - {name}")


# ============================================================
# 8. SAVE STRUCTURED REPORTS
# ============================================================

print("\n" + "=" * 70)
print("SAVING INVESTIGATION REPORTS")
print("=" * 70)


# Award conflict summary
award_summary_rows = []

for conflict in award_conflicts_found:

    award_summary_rows.append(
        {
            "award_id": conflict["award_id"],
            "records": conflict["records"],
            "changed_fields": "; ".join(
                conflict["changed_fields"].keys()
            )
        }
    )


pd.DataFrame(
    award_summary_rows
).to_csv(
    CONFLICT_DIR /
    "award_conflict_investigation.csv",
    index=False
)


# Supplier conflict summary
supplier_summary_rows = []

for conflict in supplier_conflicts_found:

    supplier_summary_rows.append(
        {
            "award_id": conflict["award_id"],
            "supplier_id": conflict["supplier_id"],
            "records": conflict["records"],
            "changed_fields": "; ".join(
                conflict["changed_fields"].keys()
            )
        }
    )


pd.DataFrame(
    supplier_summary_rows
).to_csv(
    CONFLICT_DIR /
    "supplier_conflict_investigation.csv",
    index=False
)


# Supplier ID quality report
problem_supplier_ids.to_csv(
    CONFLICT_DIR /
    "supplier_id_multiple_names.csv",
    index=False
)


print(
    "\nSaved:"
)

print(
    "  duplicate_conflicts/"
    "award_conflict_investigation.csv"
)

print(
    "  duplicate_conflicts/"
    "supplier_conflict_investigation.csv"
)

print(
    "  duplicate_conflicts/"
    "supplier_id_multiple_names.csv"
)


# ============================================================
# 9. FINAL STATUS
# ============================================================

print("\n" + "=" * 70)
print("INVESTIGATION COMPLETE")
print("=" * 70)

print(
    """
No records have been deleted or overwritten.

The purpose of this investigation is to determine whether
conflicting records represent:

1. legitimate procurement/award lifecycle updates,
2. supplier-name variations,
3. invalid or placeholder supplier identifiers,
4. genuine data-quality conflicts.

Do NOT finalize the SQLite database until these findings
have been reviewed.
"""
)