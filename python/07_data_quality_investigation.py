from pathlib import Path
import pandas as pd
import sys


# ============================================================
# WINDOWS UTF-8 CONSOLE FIX
# ============================================================

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "docs"

REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# INPUT FILES
# ============================================================

PROCUREMENT_FILE = (
    PROCESSED_DIR / "procurement_releases_2025.csv"
)

AWARDS_FILE = (
    PROCESSED_DIR / "awards_2025.csv"
)

SUPPLIERS_FILE = (
    PROCESSED_DIR / "award_suppliers_2025.csv"
)


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("CONTRACTS FINDER 2025 DATA QUALITY INVESTIGATION")
print("=" * 70)


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading processed datasets...")

procurement = pd.read_csv(
    PROCUREMENT_FILE,
    low_memory=False
)

awards = pd.read_csv(
    AWARDS_FILE,
    low_memory=False
)

suppliers = pd.read_csv(
    SUPPLIERS_FILE,
    low_memory=False
)

print(
    f"Procurement releases: {len(procurement):,}"
)

print(
    f"Awards:               {len(awards):,}"
)

print(
    f"Supplier relationships:{len(suppliers):,}"
)


# ============================================================
# 1. DATASET STRUCTURE
# ============================================================

print("\n" + "=" * 70)
print("1. DATASET STRUCTURE")
print("=" * 70)

print("\nProcurement columns:")
print(list(procurement.columns))

print("\nAward columns:")
print(list(awards.columns))

print("\nSupplier columns:")
print(list(suppliers.columns))


# ============================================================
# 2. DATE COVERAGE
# ============================================================

print("\n" + "=" * 70)
print("2. DATE COVERAGE")
print("=" * 70)


# Convert release date to timezone-aware datetime
procurement["release_date"] = pd.to_datetime(
    procurement["release_date"],
    errors="coerce",
    utc=True
)


# Convert tender publication date if available
if "tender_publication_date" in procurement.columns:

    procurement["tender_publication_date"] = pd.to_datetime(
        procurement["tender_publication_date"],
        errors="coerce",
        utc=True
    )


# Convert award dates if available
if "award_date" in awards.columns:

    awards["award_date"] = pd.to_datetime(
        awards["award_date"],
        errors="coerce",
        utc=True
    )


if "award_date_published" in awards.columns:

    awards["award_date_published"] = pd.to_datetime(
        awards["award_date_published"],
        errors="coerce",
        utc=True
    )


print("\nRelease date range:")

print(
    f"Minimum: {procurement['release_date'].min()}"
)

print(
    f"Maximum: {procurement['release_date'].max()}"
)


# Create release year
procurement["release_year"] = (
    procurement["release_date"].dt.year
)


print("\nRelease records by year:")

print(
    procurement["release_year"]
    .value_counts(dropna=False)
    .sort_index()
)


# ============================================================
# 3. RECORDS OUTSIDE 2025
# ============================================================

print("\n" + "=" * 70)
print("3. RECORDS OUTSIDE 2025")
print("=" * 70)


outside_2025 = procurement[
    procurement["release_date"].notna()
    & (procurement["release_year"] != 2025)
].copy()


inside_2025 = procurement[
    procurement["release_date"].notna()
    & (procurement["release_year"] == 2025)
].copy()


print(
    f"\nRecords with release date in 2025: "
    f"{len(inside_2025):,}"
)

print(
    f"Records outside 2025:             "
    f"{len(outside_2025):,}"
)


if len(procurement) > 0:

    percentage_outside = (
        len(outside_2025)
        / len(procurement)
        * 100
    )

    print(
        f"Percentage outside 2025:          "
        f"{percentage_outside:.2f}%"
    )


# ------------------------------------------------------------
# Additional outside-2025 investigation
# ------------------------------------------------------------

if len(outside_2025) > 0:

    print("\nOutside-2025 records by year:")

    print(
        outside_2025["release_year"]
        .value_counts()
        .sort_index()
    )


    print("\nOutside-2025 records by release tag:")

    print(
        outside_2025["release_tag"]
        .value_counts(dropna=False)
    )


    print("\nSample outside-2025 records:")

    columns_to_show = [
        "ocid",
        "release_id",
        "release_date",
        "release_tag",
        "buyer_name",
        "tender_title"
    ]

    columns_to_show = [
        column
        for column in columns_to_show
        if column in outside_2025.columns
    ]


    print(
        outside_2025[
            columns_to_show
        ]
        .sort_values("release_date")
        .head(20)
        .to_string(index=False)
    )


# ============================================================
# 4. RELEASE TAGS
# ============================================================

print("\n" + "=" * 70)
print("4. RELEASE TAGS")
print("=" * 70)


if "release_tag" in procurement.columns:

    print("\nRelease tag distribution:")

    print(
        procurement["release_tag"]
        .value_counts(dropna=False)
    )

else:

    print(
        "\nrelease_tag column not found."
    )


# ============================================================
# 5. DUPLICATE RELEASE IDs
# ============================================================

print("\n" + "=" * 70)
print("5. DUPLICATE RELEASE IDs")
print("=" * 70)


release_counts = (
    procurement["release_id"]
    .value_counts()
)


duplicate_release_ids = release_counts[
    release_counts > 1
]


print(
    f"\nUnique release IDs: "
    f"{procurement['release_id'].nunique():,}"
)


print(
    f"Release IDs appearing more than once: "
    f"{len(duplicate_release_ids):,}"
)


# ------------------------------------------------------------
# Duplicate release diagnostic
# ------------------------------------------------------------

if len(duplicate_release_ids) > 0:

    print("\nTop repeated release IDs:")

    print(
        duplicate_release_ids
        .head(20)
    )


    duplicate_release_rows = procurement[
        procurement["release_id"].isin(
            duplicate_release_ids.index
        )
    ].copy()


    duplicate_release_summary = (
        duplicate_release_rows
        .groupby("release_id")
        .agg(
            row_count=("release_id", "size"),
            unique_ocids=("ocid", "nunique"),
            unique_dates=("release_date", "nunique"),
            unique_tags=("release_tag", "nunique"),
            unique_buyers=("buyer_name", "nunique"),
            unique_titles=("tender_title", "nunique")
        )
    )


    print(
        "\nDuplicate release-ID diagnostic:"
    )

    print(
        duplicate_release_summary
        .head(20)
        .to_string()
    )


    identical_release_records = (
        duplicate_release_summary[
            (duplicate_release_summary["unique_ocids"] == 1)
            & (
                duplicate_release_summary["unique_dates"]
                == 1
            )
            & (
                duplicate_release_summary["unique_tags"]
                == 1
            )
            & (
                duplicate_release_summary["unique_buyers"]
                == 1
            )
            & (
                duplicate_release_summary["unique_titles"]
                == 1
            )
        ]
    )


    print(
        "\nRepeated release IDs with identical "
        "key fields: "
        f"{len(identical_release_records):,}"
    )


    print(
        "\nSample repeated release records:"
    )


    columns_to_show = [
        "release_id",
        "ocid",
        "release_date",
        "release_tag",
        "buyer_name",
        "tender_title"
    ]


    columns_to_show = [
        column
        for column in columns_to_show
        if column in duplicate_release_rows.columns
    ]


    print(
        duplicate_release_rows[
            columns_to_show
        ]
        .sort_values("release_id")
        .head(30)
        .to_string(index=False)
    )


# ============================================================
# 6. MULTIPLE RELEASES PER OCID
# ============================================================

print("\n" + "=" * 70)
print("6. MULTIPLE RELEASES PER OCID")
print("=" * 70)


ocid_counts = (
    procurement["ocid"]
    .value_counts()
)


multiple_release_ocids = ocid_counts[
    ocid_counts > 1
]


print(
    f"\nUnique OCIDs: "
    f"{procurement['ocid'].nunique():,}"
)


print(
    f"OCIDs with multiple releases: "
    f"{len(multiple_release_ocids):,}"
)


if len(multiple_release_ocids) > 0:

    print(
        "\nTop OCIDs by number of releases:"
    )

    print(
        multiple_release_ocids
        .head(20)
    )


    sample_ocids = (
        multiple_release_ocids
        .head(5)
        .index
    )


    print(
        "\nSample lifecycle records:"
    )


    lifecycle_sample = procurement[
        procurement["ocid"].isin(sample_ocids)
    ].copy()


    columns_to_show = [
        "ocid",
        "release_id",
        "release_date",
        "release_tag",
        "tender_status",
        "buyer_name",
        "tender_title"
    ]


    columns_to_show = [
        column
        for column in columns_to_show
        if column in lifecycle_sample.columns
    ]


    print(
        lifecycle_sample[
            columns_to_show
        ]
        .sort_values(
            ["ocid", "release_date"]
        )
        .to_string(index=False)
    )


# ============================================================
# 7. SUPPLIER NAME STANDARDIZATION
# ============================================================

print("\n" + "=" * 70)
print("7. SUPPLIER NAME STANDARDIZATION")
print("=" * 70)


supplier_names = (
    suppliers["supplier_name"]
    .dropna()
    .astype(str)
    .str.strip()
)


print(
    f"\nUnique raw supplier names: "
    f"{supplier_names.nunique():,}"
)


# Basic normalization
supplier_normalized = (
    supplier_names
    .str.upper()
    .str.replace(
        r"\s+",
        " ",
        regex=True
    )
    .str.strip()
)


print(
    f"Unique names after basic normalization: "
    f"{supplier_normalized.nunique():,}"
)


normalization_reduction = (
    supplier_names.nunique()
    - supplier_normalized.nunique()
)


print(
    f"Potential duplicate names revealed "
    f"by normalization: "
    f"{normalization_reduction:,}"
)


# ------------------------------------------------------------
# Identify groups where multiple raw names
# map to the same normalized name
# ------------------------------------------------------------

supplier_check = pd.DataFrame(
    {
        "raw_name": supplier_names,
        "normalized_name": supplier_normalized
    }
)


name_groups = (
    supplier_check
    .groupby("normalized_name")["raw_name"]
    .nunique()
    .sort_values(ascending=False)
)


ambiguous_names = name_groups[
    name_groups > 1
]


print(
    "\nNormalized supplier groups with "
    "multiple raw names: "
    f"{len(ambiguous_names):,}"
)


if len(ambiguous_names) > 0:

    print("\nExamples:")


    examples = (
        supplier_check[
            supplier_check["normalized_name"].isin(
                ambiguous_names.head(15).index
            )
        ]
        .drop_duplicates()
    )


    print(
        examples
        .sort_values("normalized_name")
        .to_string(index=False)
    )


# ============================================================
# 8. TOP SUPPLIERS
# ============================================================

print("\n" + "=" * 70)
print("8. TOP SUPPLIERS")
print("=" * 70)


print(
    suppliers["supplier_name"]
    .value_counts()
    .head(20)
)


# ============================================================
# 9. TENDER VALUE QUALITY
# ============================================================

print("\n" + "=" * 70)
print("9. TENDER VALUE QUALITY")
print("=" * 70)


tender_values = pd.to_numeric(
    procurement["tender_value"],
    errors="coerce"
)


print(
    f"\nTender value records: "
    f"{tender_values.notna().sum():,}"
)


print(
    f"Zero tender values: "
    f"{(tender_values == 0).sum():,}"
)


print(
    f"Negative tender values: "
    f"{(tender_values < 0).sum():,}"
)


print(
    f"Very large tender values (> £100M): "
    f"{(tender_values > 100_000_000).sum():,}"
)


print("\nLargest tender values:")


print(
    tender_values
    .sort_values(ascending=False)
    .head(20)
    .to_string(index=False)
)


# ============================================================
# 10. AWARD VALUE QUALITY
# ============================================================

print("\n" + "=" * 70)
print("10. AWARD VALUE QUALITY")
print("=" * 70)


award_values = pd.to_numeric(
    awards["award_value"],
    errors="coerce"
)


print(
    f"\nAward value records: "
    f"{award_values.notna().sum():,}"
)


print(
    f"Zero award values: "
    f"{(award_values == 0).sum():,}"
)


print(
    f"Negative award values: "
    f"{(award_values < 0).sum():,}"
)


print(
    f"Very large award values (> £100M): "
    f"{(award_values > 100_000_000).sum():,}"
)


print("\nLargest award values:")


print(
    award_values
    .sort_values(ascending=False)
    .head(20)
    .to_string(index=False)
)


# ============================================================
# 11. MISSINGNESS SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("11. MISSINGNESS SUMMARY")
print("=" * 70)


missing_summary = (
    procurement
    .isna()
    .mean()
    .mul(100)
    .sort_values(ascending=False)
)


print(
    missing_summary
    .head(20)
    .round(2)
    .to_string()
)


# ============================================================
# 12. SAVE QUALITY REPORT
# ============================================================

print("\n" + "=" * 70)
print("12. SAVING QUALITY REPORT")
print("=" * 70)


report_file = (
    REPORT_DIR / "data_quality_report.txt"
)


with open(
    report_file,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "CONTRACTS FINDER 2025 "
        "DATA QUALITY REPORT\n"
    )

    f.write("=" * 60 + "\n\n")


    f.write(
        f"Procurement releases: "
        f"{len(procurement):,}\n"
    )


    f.write(
        f"Unique OCIDs: "
        f"{procurement['ocid'].nunique():,}\n"
    )


    f.write(
        f"Unique release IDs: "
        f"{procurement['release_id'].nunique():,}\n"
    )


    f.write(
        f"Awards: "
        f"{len(awards):,}\n"
    )


    f.write(
        f"Supplier relationships: "
        f"{len(suppliers):,}\n"
    )


    f.write(
        f"Unique supplier names: "
        f"{supplier_names.nunique():,}\n"
    )


    # --------------------------------------------------------
    # Date distribution
    # --------------------------------------------------------

    f.write(
        "\n\nRELEASE DATE DISTRIBUTION\n"
    )

    f.write("-" * 40 + "\n")

    f.write(
        procurement["release_year"]
        .value_counts(dropna=False)
        .sort_index()
        .to_string()
    )


    # --------------------------------------------------------
    # Outside 2025
    # --------------------------------------------------------

    f.write(
        "\n\nOUTSIDE-2025 RECORDS\n"
    )

    f.write("-" * 40 + "\n")

    f.write(
        f"Records outside 2025: "
        f"{len(outside_2025):,}\n"
    )


    # --------------------------------------------------------
    # Release tags
    # --------------------------------------------------------

    f.write(
        "\n\nRELEASE TAGS\n"
    )

    f.write("-" * 40 + "\n")


    if "release_tag" in procurement.columns:

        f.write(
            procurement["release_tag"]
            .value_counts(dropna=False)
            .to_string()
        )


    # --------------------------------------------------------
    # Duplicate release IDs
    # --------------------------------------------------------

    f.write(
        "\n\nDUPLICATE RELEASE IDs\n"
    )

    f.write("-" * 40 + "\n")

    f.write(
        f"Release IDs occurring more than once: "
        f"{len(duplicate_release_ids):,}\n"
    )


    if len(duplicate_release_ids) > 0:

        f.write(
            f"Repeated release IDs with identical "
            f"key fields: "
            f"{len(identical_release_records):,}\n"
        )


    # --------------------------------------------------------
    # Multiple OCID releases
    # --------------------------------------------------------

    f.write(
        "\nMULTIPLE RELEASES PER OCID\n"
    )

    f.write("-" * 40 + "\n")

    f.write(
        f"OCIDs with multiple releases: "
        f"{len(multiple_release_ocids):,}\n"
    )


    # --------------------------------------------------------
    # Supplier standardization
    # --------------------------------------------------------

    f.write(
        "\nSUPPLIER STANDARDIZATION\n"
    )

    f.write("-" * 40 + "\n")

    f.write(
        f"Raw supplier names: "
        f"{supplier_names.nunique():,}\n"
    )

    f.write(
        f"Normalized supplier names: "
        f"{supplier_normalized.nunique():,}\n"
    )

    f.write(
        f"Potential duplicate-name reduction: "
        f"{normalization_reduction:,}\n"
    )

    f.write(
        f"Normalized groups with multiple raw names: "
        f"{len(ambiguous_names):,}\n"
    )


    # --------------------------------------------------------
    # Financial quality
    # --------------------------------------------------------

    f.write(
        "\nFINANCIAL VALUE QUALITY\n"
    )

    f.write("-" * 40 + "\n")

    f.write(
        f"Zero tender values: "
        f"{(tender_values == 0).sum():,}\n"
    )

    f.write(
        f"Negative tender values: "
        f"{(tender_values < 0).sum():,}\n"
    )

    f.write(
        f"Tender values > £100M: "
        f"{(tender_values > 100_000_000).sum():,}\n"
    )

    f.write(
        f"Zero award values: "
        f"{(award_values == 0).sum():,}\n"
    )

    f.write(
        f"Negative award values: "
        f"{(award_values < 0).sum():,}\n"
    )

    f.write(
        f"Award values > £100M: "
        f"{(award_values > 100_000_000).sum():,}\n"
    )


    # --------------------------------------------------------
    # Missingness
    # --------------------------------------------------------

    f.write(
        "\n\nTOP MISSING FIELDS\n"
    )

    f.write("-" * 40 + "\n")

    f.write(
        missing_summary
        .head(20)
        .round(2)
        .to_string()
    )


# ============================================================
# FINISHED
# ============================================================

print(
    f"\nReport saved to:\n"
    f"{report_file}"
)


print("\n" + "=" * 70)
print("DATA QUALITY INVESTIGATION COMPLETE")
print("=" * 70)