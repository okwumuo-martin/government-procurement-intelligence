from pathlib import Path
import pandas as pd
import re

# ============================================================
# 06_validate_2025_dataset.py
# Government Procurement Intelligence
# Contracts Finder / OCDS 2025
#
# Purpose:
#   Extract and validate procurement releases, awards,
#   and suppliers from the daily Contracts Finder CSV files.
#
# Important:
#   The Contracts Finder CSV uses the structure:
#   releases/0/...
# ============================================================


# ------------------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# 2. OUTPUT FILES
# ------------------------------------------------------------

PROCUREMENT_OUTPUT = (
    PROCESSED_DIR / "procurement_releases_2025.csv"
)

AWARDS_OUTPUT = (
    PROCESSED_DIR / "awards_2025.csv"
)

SUPPLIERS_OUTPUT = (
    PROCESSED_DIR / "award_suppliers_2025.csv"
)


# ------------------------------------------------------------
# 3. DISCOVER RAW FILES
# ------------------------------------------------------------

raw_files = sorted(
    RAW_DIR.glob("Contracts Finder OCDS 2025-*.csv")
)

print("=" * 70)
print("CONTRACTS FINDER 2025 DATA VALIDATION")
print("=" * 70)

print(f"\nRaw CSV files found: {len(raw_files)}")

if not raw_files:
    raise RuntimeError(
        "No Contracts Finder 2025 CSV files were found."
    )


# ------------------------------------------------------------
# 4. HELPER FUNCTIONS
# ------------------------------------------------------------

def clean_text(value):
    """Convert values to clean strings while preserving missing data."""

    if pd.isna(value):
        return pd.NA

    value = str(value).strip()

    if value == "":
        return pd.NA

    return value


def get_value(row, column):
    """Safely retrieve a column value from a row."""

    if column in row.index:
        return clean_text(row[column])

    return pd.NA


def get_number(row, column):
    """Safely retrieve a numeric value."""

    if column not in row.index:
        return pd.NA

    value = row[column]

    if pd.isna(value):
        return pd.NA

    try:
        return float(value)
    except (ValueError, TypeError):
        return pd.NA


# ------------------------------------------------------------
# 5. FIND AWARD AND SUPPLIER POSITIONS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("DISCOVERING AWARD AND SUPPLIER STRUCTURE")
print("=" * 70)

# Inspect one header only.
header = pd.read_csv(
    raw_files[0],
    nrows=0
)

columns = list(header.columns)


award_indexes = sorted(
    {
        int(match.group(1))
        for column in columns
        for match in [
            re.search(
                r"^releases/0/awards/(\d+)/",
                column
            )
        ]
        if match
    }
)

supplier_indexes = sorted(
    {
        int(match.group(1))
        for column in columns
        for match in [
            re.search(
                r"^releases/0/awards/0/suppliers/(\d+)/",
                column
            )
        ]
        if match
    }
)


print(f"Maximum award indexes found: {award_indexes}")
print(
    f"Maximum supplier indexes for award 0: "
    f"{supplier_indexes}"
)

if award_indexes:
    print(
        f"Maximum awards in a release: "
        f"{max(award_indexes) + 1}"
    )
else:
    print("No award columns detected.")

if supplier_indexes:
    print(
        f"Maximum suppliers in award 0: "
        f"{max(supplier_indexes) + 1}"
    )
else:
    print("No supplier columns detected.")


# ------------------------------------------------------------
# 6. COLUMN DEFINITIONS
# ------------------------------------------------------------

PROCUREMENT_COLUMNS = {
    "ocid": "releases/0/ocid",
    "release_id": "releases/0/id",
    "release_date": "releases/0/date",
    "release_tag": "releases/0/tag/0",
    "initiation_type": "releases/0/initiationType",

    "tender_id": "releases/0/tender/id",
    "tender_title": "releases/0/tender/title",
    "tender_description": "releases/0/tender/description",
    "tender_publication_date":
        "releases/0/tender/datePublished",
    "tender_status": "releases/0/tender/status",

    "cpv_scheme":
        "releases/0/tender/classification/scheme",
    "cpv_code":
        "releases/0/tender/classification/id",
    "cpv_description":
        "releases/0/tender/classification/description",

    "tender_value":
        "releases/0/tender/value/amount",
    "tender_currency":
        "releases/0/tender/value/currency",

    "procurement_method":
        "releases/0/tender/procurementMethod",
    "procurement_method_details":
        "releases/0/tender/procurementMethodDetails",

    "tender_period_end":
        "releases/0/tender/tenderPeriod/endDate",

    "contract_start":
        "releases/0/tender/contractPeriod/startDate",
    "contract_end":
        "releases/0/tender/contractPeriod/endDate",

    "sme_suitability":
        "releases/0/tender/suitability/sme",
    "vcse_suitability":
        "releases/0/tender/suitability/vcse",

    "procurement_category":
        "releases/0/tender/mainProcurementCategory",

    "buyer_id":
        "releases/0/buyer/id",
    "buyer_name":
        "releases/0/buyer/name",
}


# ------------------------------------------------------------
# 7. PROCESS EACH DAILY FILE
# ------------------------------------------------------------

procurement_records = []
award_records = []
supplier_records = []


for file_number, file_path in enumerate(
    raw_files,
    start=1
):

    print(
        f"\rProcessing "
        f"{file_number}/{len(raw_files)}: "
        f"{file_path.name}",
        end=""
    )

    # Read only the columns we actually need.
    file_header = pd.read_csv(
        file_path,
        nrows=0
    )

    available_columns = set(
        file_header.columns
    )

    required_columns = set(
        PROCUREMENT_COLUMNS.values()
    )

    # Add all award columns.
    for award_index in award_indexes:

        award_prefix = (
            f"releases/0/awards/{award_index}/"
        )

        for column in file_header.columns:

            if column.startswith(award_prefix):
                required_columns.add(column)

    # Read the selected columns only.
    use_columns = [
        column
        for column in file_header.columns
        if column in required_columns
    ]

    df = pd.read_csv(
        file_path,
        usecols=use_columns,
        low_memory=False
    )

    # --------------------------------------------------------
    # Process each release
    # --------------------------------------------------------

    for _, row in df.iterrows():

        ocid = get_value(
            row,
            PROCUREMENT_COLUMNS["ocid"]
        )

        release_id = get_value(
            row,
            PROCUREMENT_COLUMNS["release_id"]
        )

        # Ignore rows without an OCID.
        if pd.isna(ocid):
            continue

        procurement_record = {}

        for output_name, source_column in (
            PROCUREMENT_COLUMNS.items()
        ):

            if output_name in [
                "tender_value"
            ]:

                procurement_record[
                    output_name
                ] = get_number(
                    row,
                    source_column
                )

            else:

                procurement_record[
                    output_name
                ] = get_value(
                    row,
                    source_column
                )

        procurement_records.append(
            procurement_record
        )


        # ----------------------------------------------------
        # Process awards
        # ----------------------------------------------------

        for award_index in award_indexes:

            prefix = (
                f"releases/0/awards/"
                f"{award_index}/"
            )

            award_id = get_value(
                row,
                prefix + "id"
            )

            if pd.isna(award_id):
                continue

            award_record = {
                "ocid": ocid,
                "release_id": release_id,
                "award_id": award_id,

                "award_status": get_value(
                    row,
                    prefix + "status"
                ),

                "award_date": get_value(
                    row,
                    prefix + "date"
                ),

                "award_date_published": get_value(
                    row,
                    prefix + "datePublished"
                ),

                "award_value": get_number(
                    row,
                    prefix + "value/amount"
                ),

                "award_currency": get_value(
                    row,
                    prefix + "value/currency"
                ),

                "contract_start": get_value(
                    row,
                    prefix + "contractPeriod/startDate"
                ),

                "contract_end": get_value(
                    row,
                    prefix + "contractPeriod/endDate"
                ),

                "award_description": get_value(
                    row,
                    prefix + "description"
                ),
            }

            award_records.append(
                award_record
            )


            # ------------------------------------------------
            # Process suppliers
            # ------------------------------------------------

            for supplier_index in supplier_indexes:

                supplier_prefix = (
                    f"{prefix}"
                    f"suppliers/"
                    f"{supplier_index}/"
                )

                supplier_id = get_value(
                    row,
                    supplier_prefix + "id"
                )

                supplier_name = get_value(
                    row,
                    supplier_prefix + "name"
                )

                if (
                    pd.isna(supplier_id)
                    and pd.isna(supplier_name)
                ):
                    continue

                supplier_records.append(
                    {
                        "ocid": ocid,
                        "release_id": release_id,
                        "award_id": award_id,
                        "supplier_id": supplier_id,
                        "supplier_name": supplier_name,
                    }
                )


print("\n")


# ------------------------------------------------------------
# 8. CREATE DATAFRAMES
# ------------------------------------------------------------

print("=" * 70)
print("ASSEMBLING DATASETS")
print("=" * 70)

procurement_df = pd.DataFrame(
    procurement_records
)

awards_df = pd.DataFrame(
    award_records
)

suppliers_df = pd.DataFrame(
    supplier_records
)


# ------------------------------------------------------------
# 9. REMOVE EXACT DUPLICATES
# ------------------------------------------------------------

procurement_before = len(
    procurement_df
)

award_before = len(
    awards_df
)

supplier_before = len(
    suppliers_df
)


procurement_df = procurement_df.drop_duplicates()

awards_df = awards_df.drop_duplicates()

suppliers_df = suppliers_df.drop_duplicates()


print(
    f"\nProcurement exact duplicates removed: "
    f"{procurement_before - len(procurement_df)}"
)

print(
    f"Award exact duplicates removed: "
    f"{award_before - len(awards_df)}"
)

print(
    f"Supplier exact duplicates removed: "
    f"{supplier_before - len(suppliers_df)}"
)


# ------------------------------------------------------------
# 10. CONVERT DATA TYPES
# ------------------------------------------------------------

date_columns = [
    "release_date",
    "tender_publication_date",
    "tender_period_end",
    "contract_start",
    "contract_end",
]

for column in date_columns:

    if column in procurement_df.columns:

        procurement_df[column] = pd.to_datetime(
            procurement_df[column],
            errors="coerce",
            utc=True
        )


award_date_columns = [
    "award_date",
    "award_date_published",
    "contract_start",
    "contract_end",
]

for column in award_date_columns:

    if column in awards_df.columns:

        awards_df[column] = pd.to_datetime(
            awards_df[column],
            errors="coerce",
            utc=True
        )


# ------------------------------------------------------------
# 11. VALIDATION
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("DATA VALIDATION")
print("=" * 70)


print(
    f"\nProcurement releases: "
    f"{len(procurement_df):,}"
)

print(
    f"Unique OCIDs: "
    f"{procurement_df['ocid'].nunique():,}"
)

print(
    f"Unique release IDs: "
    f"{procurement_df['release_id'].nunique():,}"
)

print(
    f"Awards: "
    f"{len(awards_df):,}"
)

print(
    f"Unique awards: "
    f"{awards_df['award_id'].nunique():,}"
)

print(
    f"Supplier relationships: "
    f"{len(suppliers_df):,}"
)

print(
    f"Unique suppliers: "
    f"{suppliers_df['supplier_name'].nunique():,}"
)


# ------------------------------------------------------------
# 12. DATE COVERAGE
# ------------------------------------------------------------

if not procurement_df.empty:

    min_date = procurement_df[
        "release_date"
    ].min()

    max_date = procurement_df[
        "release_date"
    ].max()

    print(
        f"\nRelease date range: "
        f"{min_date} to {max_date}"
    )


# ------------------------------------------------------------
# 13. MISSING DATA
# ------------------------------------------------------------

print("\nMissing-value rates:")

missing_rates = (
    procurement_df.isna()
    .mean()
    .sort_values(ascending=False)
    * 100
)

for column, rate in missing_rates.items():

    print(
        f"  {column:<30} "
        f"{rate:>6.2f}%"
    )


# ------------------------------------------------------------
# 14. PROCUREMENT CATEGORIES
# ------------------------------------------------------------

print("\nProcurement categories:")

if "procurement_category" in procurement_df.columns:

    print(
        procurement_df[
            "procurement_category"
        ]
        .value_counts(dropna=False)
        .to_string()
    )


# ------------------------------------------------------------
# 15. PROCUREMENT METHODS
# ------------------------------------------------------------

print("\nProcurement methods:")

if "procurement_method" in procurement_df.columns:

    print(
        procurement_df[
            "procurement_method"
        ]
        .value_counts(dropna=False)
        .to_string()
    )


# ------------------------------------------------------------
# 16. TOP BUYERS
# ------------------------------------------------------------

print("\nTop 10 buyers:")

print(
    procurement_df[
        "buyer_name"
    ]
    .value_counts()
    .head(10)
    .to_string()
)


# ------------------------------------------------------------
# 17. TOP SUPPLIERS
# ------------------------------------------------------------

print("\nTop 10 suppliers:")

if not suppliers_df.empty:

    print(
        suppliers_df[
            "supplier_name"
        ]
        .value_counts()
        .head(10)
        .to_string()
    )


# ------------------------------------------------------------
# 18. VALUE VALIDATION
# ------------------------------------------------------------

print("\nFinancial summary:")

if "tender_value" in procurement_df.columns:

    tender_values = pd.to_numeric(
        procurement_df["tender_value"],
        errors="coerce"
    )

    print(
        f"Tender value records: "
        f"{tender_values.notna().sum():,}"
    )

    print(
        f"Total tender value: "
        f"£{tender_values.sum():,.2f}"
    )

    print(
        f"Median tender value: "
        f"£{tender_values.median():,.2f}"
    )


if not awards_df.empty:

    award_values = pd.to_numeric(
        awards_df["award_value"],
        errors="coerce"
    )

    print(
        f"Award value records: "
        f"{award_values.notna().sum():,}"
    )

    print(
        f"Total award value: "
        f"£{award_values.sum():,.2f}"
    )

    print(
        f"Median award value: "
        f"£{award_values.median():,.2f}"
    )


# ------------------------------------------------------------
# 19. SAVE DATASETS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("SAVING PROCESSED DATA")
print("=" * 70)


procurement_df.to_csv(
    PROCUREMENT_OUTPUT,
    index=False
)

awards_df.to_csv(
    AWARDS_OUTPUT,
    index=False
)

suppliers_df.to_csv(
    SUPPLIERS_OUTPUT,
    index=False
)


print(
    f"\nSaved:\n"
    f"  {PROCUREMENT_OUTPUT}\n"
    f"  {AWARDS_OUTPUT}\n"
    f"  {SUPPLIERS_OUTPUT}"
)


# ------------------------------------------------------------
# 20. FINAL SUMMARY
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("VALIDATION COMPLETE")
print("=" * 70)

print(
    f"""
Files processed:              {len(raw_files):,}
Procurement releases:         {len(procurement_df):,}
Unique procurements (OCID):   {procurement_df['ocid'].nunique():,}
Unique releases:              {procurement_df['release_id'].nunique():,}
Awards:                       {len(awards_df):,}
Supplier relationships:       {len(suppliers_df):,}
Unique suppliers:             {suppliers_df['supplier_name'].nunique():,}

The 2025 Contracts Finder dataset has been
successfully extracted into relational datasets.
"""
)