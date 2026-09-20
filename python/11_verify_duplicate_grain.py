from pathlib import Path
import pandas as pd
import hashlib


# ============================================================
# CONTRACTS FINDER 2025
# DUPLICATE GRAIN VERIFICATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

RELEASES_FILE = PROCESSED_DIR / "releases_2025.csv"
AWARDS_FILE = PROCESSED_DIR / "awards_2025.csv"
RELATIONSHIPS_FILE = PROCESSED_DIR / "award_suppliers_2025.csv"


print("=" * 70)
print("CONTRACTS FINDER 2025")
print("DUPLICATE GRAIN VERIFICATION")
print("=" * 70)


# ============================================================
# 1. LOAD DATA
# ============================================================

print("\nLoading normalized datasets...")

releases = pd.read_csv(RELEASES_FILE, low_memory=False)
awards = pd.read_csv(AWARDS_FILE, low_memory=False)
relationships = pd.read_csv(RELATIONSHIPS_FILE, low_memory=False)

print(f"Releases:              {len(releases):,}")
print(f"Awards:                {len(awards):,}")
print(f"Award-supplier rows:   {len(relationships):,}")


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def normalize_value(value):
    """
    Convert values into a stable representation for comparison.
    Treat NaN and blank values consistently.
    """
    if pd.isna(value):
        return "<NA>"

    if isinstance(value, str):
        return value.strip()

    return str(value)


def row_signature(row, columns):
    """
    Create a stable hash from all substantive columns.
    """
    values = [
        normalize_value(row[col])
        for col in columns
    ]

    text = "||".join(values)

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def investigate_duplicates(df, key_columns, dataset_name):
    """
    Investigate repeated business keys.

    source_file is excluded from comparison because the same
    record can legitimately appear in multiple daily source files.
    """

    print("\n" + "=" * 70)
    print(f"{dataset_name.upper()} DUPLICATE INVESTIGATION")
    print("=" * 70)

    missing_keys = df[key_columns].isna().any(axis=1)

    if missing_keys.any():
        print(
            f"\nRows with missing key values: "
            f"{missing_keys.sum():,}"
        )

    valid = df.loc[~missing_keys].copy()

    duplicate_mask = valid.duplicated(
        subset=key_columns,
        keep=False
    )

    duplicates = valid.loc[duplicate_mask].copy()

    if duplicates.empty:
        print("\nNo repeated business keys found.")
        return {
            "duplicate_rows": 0,
            "duplicate_groups": 0,
            "exact_groups": 0,
            "conflicting_groups": 0,
            "deduplicated": valid.copy(),
            "conflicts": pd.DataFrame()
        }

    print(
        f"\nRows involved in repeated keys: "
        f"{len(duplicates):,}"
    )

    duplicate_groups = (
        duplicates.groupby(key_columns, dropna=False)
        .ngroups
    )

    print(
        f"Repeated business-key groups: "
        f"{duplicate_groups:,}"
    )

    # --------------------------------------------------------
    # Columns used to determine whether duplicate records
    # actually contain different information.
    #
    # source_file is deliberately excluded because the same
    # record can occur in multiple daily extracts.
    # --------------------------------------------------------

    comparison_columns = [
        col
        for col in valid.columns
        if col not in ["source_file"]
        and col not in key_columns
    ]

    # --------------------------------------------------------
    # Calculate a signature for each row.
    # --------------------------------------------------------

    duplicates["_row_signature"] = duplicates.apply(
        lambda row: row_signature(
            row,
            comparison_columns
        ),
        axis=1
    )

    # --------------------------------------------------------
    # Count distinct substantive records within each key.
    # --------------------------------------------------------

    group_signature_counts = (
        duplicates
        .groupby(key_columns)["_row_signature"]
        .nunique()
        .reset_index(name="distinct_signatures")
    )

    exact_groups = group_signature_counts[
        group_signature_counts["distinct_signatures"] == 1
    ]

    conflicting_groups = group_signature_counts[
        group_signature_counts["distinct_signatures"] > 1
    ]

    print(
        f"Exact-identical duplicate groups: "
        f"{len(exact_groups):,}"
    )

    print(
        f"Conflicting duplicate groups: "
        f"{len(conflicting_groups):,}"
    )

    # --------------------------------------------------------
    # Rows belonging to conflicting groups
    # --------------------------------------------------------

    conflicts = duplicates.merge(
        conflicting_groups[key_columns],
        on=key_columns,
        how="inner"
    )

    # Remove helper column before saving.
    duplicates.drop(
        columns=["_row_signature"],
        inplace=True
    )

    conflicts.drop(
        columns=["_row_signature"],
        inplace=True,
        errors="ignore"
    )

    # --------------------------------------------------------
    # Print examples of conflicts.
    # --------------------------------------------------------

    if not conflicts.empty:

        print("\nWARNING: CONFLICTING DUPLICATES FOUND")

        print("\nExample conflicting groups:")

        example_keys = (
            conflicting_groups[key_columns]
            .head(5)
        )

        for _, key_row in example_keys.iterrows():

            mask = pd.Series(
                True,
                index=conflicts.index
            )

            for key in key_columns:
                mask &= (
                    conflicts[key]
                    == key_row[key]
                )

            example = conflicts.loc[mask]

            print("\nKey:")
            for key in key_columns:
                print(
                    f"  {key}: "
                    f"{key_row[key]}"
                )

            print("\nRecords:")

            print(
                example.to_string(index=False)
            )

    # --------------------------------------------------------
    # Create analytical deduplicated table.
    #
    # IMPORTANT:
    # We only remove repeated business keys here.
    # Conflicting duplicates are NOT silently resolved.
    #
    # If conflicts exist, they remain in the table for now.
    # --------------------------------------------------------

    if conflicting_groups.empty:

        analytical = valid.drop_duplicates(
            subset=key_columns,
            keep="first"
        ).copy()

    else:

        conflict_index = set()

        for _, key_row in conflicting_groups.iterrows():

            mask = pd.Series(
                True,
                index=valid.index
            )

            for key in key_columns:
                mask &= (
                    valid[key]
                    == key_row[key]
                )

            conflict_index.update(
                valid.index[mask].tolist()
            )

        non_conflicting = valid.loc[
            ~valid.index.isin(conflict_index)
        ]

        analytical = pd.concat(
            [
                non_conflicting.drop_duplicates(
                    subset=key_columns,
                    keep="first"
                ),
                valid.loc[
                    valid.index.isin(conflict_index)
                ]
            ],
            ignore_index=True
        )

    return {
        "duplicate_rows": len(duplicates),
        "duplicate_groups": duplicate_groups,
        "exact_groups": len(exact_groups),
        "conflicting_groups": len(conflicting_groups),
        "deduplicated": analytical,
        "conflicts": conflicts
    }


# ============================================================
# 3. RELEASE GRAIN
# ============================================================

release_result = investigate_duplicates(
    releases,
    ["release_id"],
    "Release"
)


# ============================================================
# 4. AWARD GRAIN
# ============================================================

award_result = investigate_duplicates(
    awards,
    ["award_id"],
    "Award"
)


# ============================================================
# 5. AWARD-SUPPLIER RELATIONSHIP GRAIN
# ============================================================

# Prefer award_id + supplier_id where supplier_id exists.

if "supplier_id" in relationships.columns:

    relationship_result = investigate_duplicates(
        relationships,
        ["award_id", "supplier_id"],
        "Award-Supplier Relationship"
    )

else:

    print(
        "\nWARNING: supplier_id column not found."
    )

    relationship_result = investigate_duplicates(
        relationships,
        ["award_id", "supplier_name"],
        "Award-Supplier Relationship"
    )


# ============================================================
# 6. SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("DUPLICATE VERIFICATION SUMMARY")
print("=" * 70)

print("\nRELEASES")
print(
    f"Repeated groups:       "
    f"{release_result['duplicate_groups']:,}"
)
print(
    f"Exact-identical:       "
    f"{release_result['exact_groups']:,}"
)
print(
    f"Conflicting:           "
    f"{release_result['conflicting_groups']:,}"
)

print("\nAWARDS")
print(
    f"Repeated groups:       "
    f"{award_result['duplicate_groups']:,}"
)
print(
    f"Exact-identical:       "
    f"{award_result['exact_groups']:,}"
)
print(
    f"Conflicting:           "
    f"{award_result['conflicting_groups']:,}"
)

print("\nAWARD-SUPPLIER RELATIONSHIPS")
print(
    f"Repeated groups:       "
    f"{relationship_result['duplicate_groups']:,}"
)
print(
    f"Exact-identical:       "
    f"{relationship_result['exact_groups']:,}"
)
print(
    f"Conflicting:           "
    f"{relationship_result['conflicting_groups']:,}"
)


# ============================================================
# 7. SAVE CONFLICT REPORTS
# ============================================================

conflict_dir = PROCESSED_DIR / "duplicate_conflicts"
conflict_dir.mkdir(exist_ok=True)

release_conflicts = release_result["conflicts"]
award_conflicts = award_result["conflicts"]
relationship_conflicts = relationship_result["conflicts"]

release_conflicts.to_csv(
    conflict_dir / "release_conflicts_2025.csv",
    index=False
)

award_conflicts.to_csv(
    conflict_dir / "award_conflicts_2025.csv",
    index=False
)

relationship_conflicts.to_csv(
    conflict_dir / "award_supplier_conflicts_2025.csv",
    index=False
)


# ============================================================
# 8. SAVE PRELIMINARY ANALYTICAL TABLES
# ============================================================

print("\nSaving preliminary analytical datasets...")

release_result["deduplicated"].to_csv(
    PROCESSED_DIR / "analytical_releases_2025.csv",
    index=False
)

award_result["deduplicated"].to_csv(
    PROCESSED_DIR / "analytical_awards_2025.csv",
    index=False
)

relationship_result["deduplicated"].to_csv(
    PROCESSED_DIR / "analytical_award_suppliers_2025.csv",
    index=False
)


# ============================================================
# 9. BUILD SUPPLIER MASTER
# ============================================================

print("\nBuilding supplier master from the")
print("filtered analytical 2025 relationship table...")

analytical_relationships = (
    relationship_result["deduplicated"]
)

if "supplier_id" in analytical_relationships.columns:

    suppliers = (
        analytical_relationships[
            [
                "supplier_id",
                "supplier_name"
            ]
        ]
        .dropna(subset=["supplier_id"])
        .drop_duplicates()
        .sort_values(
            ["supplier_name", "supplier_id"],
            na_position="last"
        )
    )

else:

    suppliers = (
        analytical_relationships[
            ["supplier_name"]
        ]
        .dropna()
        .drop_duplicates()
        .sort_values("supplier_name")
    )


suppliers.to_csv(
    PROCESSED_DIR / "analytical_suppliers_2025.csv",
    index=False
)


print(
    f"Analytical suppliers: "
    f"{len(suppliers):,}"
)


# ============================================================
# 10. FINAL STATUS
# ============================================================

print("\n" + "=" * 70)
print("DUPLICATE GRAIN VERIFICATION COMPLETE")
print("=" * 70)

if (
    release_result["conflicting_groups"] == 0
    and award_result["conflicting_groups"] == 0
    and relationship_result["conflicting_groups"] == 0
):

    print(
        "\nSTATUS: SAFE TO PROCEED TO ANALYTICAL DATABASE DESIGN."
    )

else:

    print(
        "\nSTATUS: CONFLICTS REQUIRE INVESTIGATION "
        "BEFORE FINAL DATABASE DEDUPLICATION."
    )

print("\nOutput files:")

print(
    "  analytical_releases_2025.csv"
)

print(
    "  analytical_awards_2025.csv"
)

print(
    "  analytical_award_suppliers_2025.csv"
)

print(
    "  analytical_suppliers_2025.csv"
)

print(
    "  duplicate_conflicts/"
)

print("\nNo raw source files were modified.")