from pathlib import Path
import pandas as pd
import re
import sys

# ================================================================
# CONTRACTS FINDER 2025
# NORMALIZED DATA EXTRACTION
# ================================================================

# Make Windows terminal UTF-8 safe
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


# ================================================================
# 1. PROJECT PATHS
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ================================================================
# 2. SETTINGS
# ================================================================

RAW_FILE_PATTERN = "Contracts Finder OCDS 2025-*.csv"

OUTPUT_RELEASES = PROCESSED_DIR / "releases_2025.csv"
OUTPUT_AWARDS = PROCESSED_DIR / "awards_2025.csv"
OUTPUT_SUPPLIERS = PROCESSED_DIR / "award_suppliers_2025.csv"
OUTPUT_SUPPLIER_MASTER = PROCESSED_DIR / "suppliers_2025.csv"


# ================================================================
# 3. RAW FILE DISCOVERY
# ================================================================

raw_files = sorted(RAW_DIR.glob(RAW_FILE_PATTERN))

print("=" * 75)
print("CONTRACTS FINDER 2025 NORMALIZED DATA EXTRACTION")
print("=" * 75)

print(f"\nRaw CSV files found: {len(raw_files)}")

if not raw_files:
    raise RuntimeError(
        f"No files found in {RAW_DIR} matching {RAW_FILE_PATTERN}"
    )


# ================================================================
# 4. COLUMN PATTERNS
# ================================================================

# OCDS flattened CSV structure:
#
# releases/0/ocid
# releases/0/id
# releases/0/date
# releases/0/tender/title
# releases/0/awards/0/id
# releases/0/awards/1/id
# releases/0/awards/0/suppliers/0/id
# releases/0/awards/0/suppliers/1/id
#
# We dynamically discover all indexes.

AWARD_PATTERN = re.compile(
    r"^releases/0/awards/(\d+)/"
)

SUPPLIER_PATTERN = re.compile(
    r"^releases/0/awards/(\d+)/suppliers/(\d+)/"
)


# ================================================================
# 5. HELPER FUNCTIONS
# ================================================================

def safe_read_header(file_path):
    """
    Read only the CSV header.

    This prevents the large daily files from being loaded
    into memory simply to discover their schema.
    """

    try:
        return pd.read_csv(
            file_path,
            nrows=0,
            encoding="utf-8-sig"
        ).columns.tolist()

    except UnicodeDecodeError:

        return pd.read_csv(
            file_path,
            nrows=0,
            encoding="latin1"
        ).columns.tolist()


def safe_read_csv(file_path, usecols):
    """
    Read only the requested columns.

    Missing columns are ignored because different OCDS
    releases may have different fields.
    """

    try:
        return pd.read_csv(
            file_path,
            usecols=usecols,
            encoding="utf-8-sig",
            low_memory=False
        )

    except UnicodeDecodeError:

        return pd.read_csv(
            file_path,
            usecols=usecols,
            encoding="latin1",
            low_memory=False
        )


def clean_value(value):
    """
    Convert empty strings and NaN values to None.
    """

    if pd.isna(value):
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


def get_value(row, column):
    """
    Safely retrieve a value from a pandas row.
    """

    if column not in row.index:
        return None

    return clean_value(row[column])


def first_existing(row, columns):
    """
    Return the first non-empty value among candidate columns.
    """

    for column in columns:

        if column in row.index:

            value = clean_value(row[column])

            if value is not None:
                return value

    return None


def normalize_supplier_name(name):
    """
    Basic supplier-name normalization.

    This is deliberately conservative.

    We are NOT trying to decide whether two companies
    are legally the same entity.
    """

    if name is None:
        return None

    value = str(name).upper().strip()

    value = re.sub(r"\s+", " ", value)

    return value


# ================================================================
# 6. DISCOVER YEAR-WIDE SCHEMA
# ================================================================

print("\n" + "=" * 75)
print("STEP 1: DISCOVERING YEAR-WIDE AWARD AND SUPPLIER STRUCTURE")
print("=" * 75)

all_award_indexes = set()
all_supplier_positions = set()

file_schema = {}

for i, file_path in enumerate(raw_files, start=1):

    header = safe_read_header(file_path)

    award_indexes = set()
    supplier_positions = set()

    for column in header:

        award_match = AWARD_PATTERN.match(column)

        if award_match:

            award_index = int(award_match.group(1))

            award_indexes.add(award_index)
            all_award_indexes.add(award_index)

        supplier_match = SUPPLIER_PATTERN.match(column)

        if supplier_match:

            award_index = int(supplier_match.group(1))
            supplier_index = int(supplier_match.group(2))

            supplier_positions.add(
                (award_index, supplier_index)
            )

            all_supplier_positions.add(
                (award_index, supplier_index)
            )

    file_schema[file_path] = {
        "header": header,
        "award_indexes": sorted(award_indexes),
        "supplier_positions": sorted(supplier_positions)
    }

    print(
        f"Scanned {i:>3}/{len(raw_files)}: "
        f"{file_path.name} | "
        f"Awards: {len(award_indexes)} | "
        f"Supplier positions: {len(supplier_positions)}"
    )


print("\nYear-wide award indexes:")
print(sorted(all_award_indexes))

if all_award_indexes:

    print(
        f"Maximum award index: "
        f"{max(all_award_indexes)}"
    )

    print(
        f"Maximum awards represented in one release: "
        f"{max(all_award_indexes) + 1}"
    )

else:

    print("No award positions detected.")


if all_supplier_positions:

    max_supplier_index = max(
        supplier_index
        for _, supplier_index in all_supplier_positions
    )

    print(
        f"\nMaximum supplier index: "
        f"{max_supplier_index}"
    )

    print(
        f"Maximum suppliers represented within one award: "
        f"{max_supplier_index + 1}"
    )

else:

    print("\nNo supplier positions detected.")


# ================================================================
# 7. RELEASE-LEVEL FIELDS
# ================================================================

RELEASE_FIELDS = {
    "ocid": "releases/0/ocid",
    "release_id": "releases/0/id",
    "release_date": "releases/0/date",
    "release_tag": "releases/0/tag/0",
    "initiation_type": "releases/0/initiationType",

    "tender_id": "releases/0/tender/id",
    "tender_title": "releases/0/tender/title",
    "tender_description": "releases/0/tender/description",
    "tender_status": "releases/0/tender/status",
    "tender_value": "releases/0/tender/value/amount",
    "tender_currency": "releases/0/tender/value/currency",

    "procurement_method": "releases/0/tender/procurementMethod",
    "procurement_method_details": (
        "releases/0/tender/procurementMethodDetails"
    ),
    "procurement_category": (
        "releases/0/tender/mainProcurementCategory"
    ),

    "tender_period_start": (
        "releases/0/tender/tenderPeriod/startDate"
    ),
    "tender_period_end": (
        "releases/0/tender/tenderPeriod/endDate"
    ),

    "buyer_id": "releases/0/buyer/id",
    "buyer_name": "releases/0/buyer/name",

    "cpv_scheme": (
        "releases/0/tender/classification/scheme"
    ),
    "cpv_code": (
        "releases/0/tender/classification/id"
    ),
    "cpv_description": (
        "releases/0/tender/classification/description"
    ),

    "vcse_suitability": (
        "releases/0/tender/hasElectronicAuction"
    ),

    "sme_suitability": (
        "releases/0/tender/smeFriendly"
    ),
}


# ================================================================
# 8. DETERMINE REQUIRED RELEASE COLUMNS
# ================================================================

required_release_columns = set(
    RELEASE_FIELDS.values()
)


# ================================================================
# 9. EXTRACTION CONTAINERS
# ================================================================

release_records = []
award_records = []
supplier_records = []


# ================================================================
# 10. PROCESS EACH RAW FILE
# ================================================================

print("\n" + "=" * 75)
print("STEP 2: EXTRACTING NORMALIZED RECORDS")
print("=" * 75)

total_rows_processed = 0
total_release_records = 0
total_award_records = 0
total_supplier_records = 0


for file_number, file_path in enumerate(
    raw_files,
    start=1
):

    schema = file_schema[file_path]

    header = schema["header"]

    award_indexes = schema["award_indexes"]

    supplier_positions = schema["supplier_positions"]

    # ------------------------------------------------------------
    # Determine columns actually available in this file
    # ------------------------------------------------------------

    columns_to_read = set()

    # Release-level columns
    for column in required_release_columns:

        if column in header:

            columns_to_read.add(column)

    # Award-level columns
    for award_index in award_indexes:

        prefix = (
            f"releases/0/awards/{award_index}/"
        )

        for column in header:

            if column.startswith(prefix):

                columns_to_read.add(column)

    # Supplier-level columns
    for award_index, supplier_index in supplier_positions:

        prefix = (
            f"releases/0/awards/"
            f"{award_index}/suppliers/"
            f"{supplier_index}/"
        )

        for column in header:

            if column.startswith(prefix):

                columns_to_read.add(column)

    columns_to_read = [
        column
        for column in header
        if column in columns_to_read
    ]

    if not columns_to_read:

        print(
            f"WARNING: No usable columns found in "
            f"{file_path.name}"
        )

        continue

    # ------------------------------------------------------------
    # Read narrow subset
    # ------------------------------------------------------------

    df = safe_read_csv(
        file_path,
        columns_to_read
    )

    total_rows_processed += len(df)

    print(
        f"Processing {file_number:>3}/{len(raw_files)}: "
        f"{file_path.name} | "
        f"Rows: {len(df):,} | "
        f"Awards: {len(award_indexes)} | "
        f"Supplier positions: {len(supplier_positions)}"
    )

    # ------------------------------------------------------------
    # Process each release
    # ------------------------------------------------------------

    for _, row in df.iterrows():

        # ========================================================
        # RELEASE
        # ========================================================

        release_record = {}

        for field_name, column_name in RELEASE_FIELDS.items():

            release_record[field_name] = get_value(
                row,
                column_name
            )

        # Source file provides useful lineage
        release_record["source_file"] = file_path.name

        # --------------------------------------------------------
        # Only retain records with an OCID
        # --------------------------------------------------------

        if release_record["ocid"] is None:

            continue

        release_records.append(
            release_record
        )

        total_release_records += 1

        # ========================================================
        # AWARDS
        # ========================================================

        for award_index in award_indexes:

            award_prefix = (
                f"releases/0/awards/{award_index}/"
            )

            award_id = get_value(
                row,
                award_prefix + "id"
            )

            # If there is no award ID, don't create
            # a meaningless award record.
            if award_id is None:

                continue

            award_record = {

                "ocid": release_record["ocid"],

                "release_id": release_record["release_id"],

                "release_date": release_record["release_date"],

                "award_index": award_index,

                "award_id": award_id,

                "award_status": get_value(
                    row,
                    award_prefix + "status"
                ),

                "award_date": get_value(
                    row,
                    award_prefix + "date"
                ),

                "award_value": get_value(
                    row,
                    award_prefix + "value/amount"
                ),

                "award_currency": get_value(
                    row,
                    award_prefix + "value/currency"
                ),

                "award_title": get_value(
                    row,
                    award_prefix + "title"
                ),

                "award_description": get_value(
                    row,
                    award_prefix + "description"
                ),

                "contract_start": get_value(
                    row,
                    award_prefix +
                    "contractPeriod/startDate"
                ),

                "contract_end": get_value(
                    row,
                    award_prefix +
                    "contractPeriod/endDate"
                ),

                "source_file": file_path.name
            }

            award_records.append(
                award_record
            )

            total_award_records += 1

            # ====================================================
            # SUPPLIERS FOR THIS AWARD
            # ====================================================

            supplier_indexes = sorted(
                supplier_index
                for award_idx, supplier_index
                in supplier_positions
                if award_idx == award_index
            )

            for supplier_index in supplier_indexes:

                supplier_prefix = (
                    f"releases/0/awards/"
                    f"{award_index}/suppliers/"
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

                # Only create a relationship when there
                # is actually a supplier.
                if (
                    supplier_id is None
                    and supplier_name is None
                ):

                    continue

                supplier_record = {

                    "ocid": release_record["ocid"],

                    "release_id": release_record["release_id"],

                    "award_id": award_id,

                    "award_index": award_index,

                    "supplier_index": supplier_index,

                    "supplier_id": supplier_id,

                    "supplier_name": supplier_name,

                    "supplier_name_normalized":
                        normalize_supplier_name(
                            supplier_name
                        ),

                    "source_file": file_path.name
                }

                supplier_records.append(
                    supplier_record
                )

                total_supplier_records += 1


# ================================================================
# 11. CONVERT TO DATAFRAMES
# ================================================================

print("\n" + "=" * 75)
print("STEP 3: ASSEMBLING DATASETS")
print("=" * 75)

releases = pd.DataFrame(
    release_records
)

awards = pd.DataFrame(
    award_records
)

award_suppliers = pd.DataFrame(
    supplier_records
)


print(
    f"\nRaw release records extracted: "
    f"{len(releases):,}"
)

print(
    f"Raw award records extracted: "
    f"{len(awards):,}"
)

print(
    f"Raw supplier relationships extracted: "
    f"{len(award_suppliers):,}"
)


# ================================================================
# 12. DATE CONVERSION
# ================================================================

print("\nConverting date fields...")

if not releases.empty:

    releases["release_date"] = pd.to_datetime(
        releases["release_date"],
        errors="coerce",
        utc=True
    )

    releases["tender_period_start"] = pd.to_datetime(
        releases["tender_period_start"],
        errors="coerce",
        utc=True
    )

    releases["tender_period_end"] = pd.to_datetime(
        releases["tender_period_end"],
        errors="coerce",
        utc=True
    )


if not awards.empty:

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


# ================================================================
# 13. NUMERIC CONVERSION
# ================================================================

if not releases.empty:

    releases["tender_value"] = pd.to_numeric(
        releases["tender_value"],
        errors="coerce"
    )


if not awards.empty:

    awards["award_value"] = pd.to_numeric(
        awards["award_value"],
        errors="coerce"
    )


# ================================================================
# 14. EXACT DUPLICATE REMOVAL
# ================================================================

print("\nRemoving exact duplicate records...")

release_duplicates = releases.duplicated().sum()

award_duplicates = awards.duplicated().sum()

supplier_duplicates = award_suppliers.duplicated().sum()


releases = releases.drop_duplicates().reset_index(
    drop=True
)

awards = awards.drop_duplicates().reset_index(
    drop=True
)

award_suppliers = award_suppliers.drop_duplicates().reset_index(
    drop=True
)


print(
    f"Release exact duplicates removed: "
    f"{release_duplicates:,}"
)

print(
    f"Award exact duplicates removed: "
    f"{award_duplicates:,}"
)

print(
    f"Supplier exact duplicates removed: "
    f"{supplier_duplicates:,}"
)


# ================================================================
# 15. CREATE SUPPLIER MASTER
# ================================================================

print("\nCreating supplier master dataset...")

if not award_suppliers.empty:

    supplier_master = (
        award_suppliers[
            [
                "supplier_id",
                "supplier_name",
                "supplier_name_normalized"
            ]
        ]
        .drop_duplicates()
        .sort_values(
            by=[
                "supplier_name_normalized",
                "supplier_name"
            ],
            na_position="last"
        )
        .reset_index(drop=True)
    )

else:

    supplier_master = pd.DataFrame(
        columns=[
            "supplier_id",
            "supplier_name",
            "supplier_name_normalized"
        ]
    )


# ================================================================
# 16. FILTER RELEASE DATE TO 2025
# ================================================================

print("\nApplying 2025 analytical date filter...")

# Important:
#
# We keep the raw extraction in memory first and then identify
# records whose release date falls inside calendar year 2025.
#
# The original raw CSV files remain untouched.

if not releases.empty:

    releases_2025 = releases[
        (
            releases["release_date"].dt.year == 2025
        )
    ].copy()

else:

    releases_2025 = releases.copy()


valid_release_ids = set(
    releases_2025["release_id"]
    .dropna()
)


valid_ocids = set(
    releases_2025["ocid"]
    .dropna()
)


if not awards.empty:

    awards_2025 = awards[
        awards["release_id"].isin(
            valid_release_ids
        )
    ].copy()

else:

    awards_2025 = awards.copy()


if not award_suppliers.empty:

    award_suppliers_2025 = award_suppliers[
        award_suppliers["release_id"].isin(
            valid_release_ids
        )
    ].copy()

else:

    award_suppliers_2025 = award_suppliers.copy()


print(
    f"Release records in 2025: "
    f"{len(releases_2025):,}"
)

print(
    f"Award records linked to 2025 releases: "
    f"{len(awards_2025):,}"
)

print(
    f"Supplier relationships linked to 2025 releases: "
    f"{len(award_suppliers_2025):,}"
)


# ================================================================
# 17. SAVE DATASETS
# ================================================================

print("\n" + "=" * 75)
print("STEP 4: SAVING NORMALIZED DATASETS")
print("=" * 75)


# Save using UTF-8 with BOM so Excel/Windows handles
# supplier names and other Unicode text correctly.

releases_2025.to_csv(
    OUTPUT_RELEASES,
    index=False,
    encoding="utf-8-sig"
)

awards_2025.to_csv(
    OUTPUT_AWARDS,
    index=False,
    encoding="utf-8-sig"
)

award_suppliers_2025.to_csv(
    OUTPUT_SUPPLIERS,
    index=False,
    encoding="utf-8-sig"
)

supplier_master.to_csv(
    OUTPUT_SUPPLIER_MASTER,
    index=False,
    encoding="utf-8-sig"
)


print(
    f"\nSaved:\n"
    f"  {OUTPUT_RELEASES}\n"
    f"  {OUTPUT_AWARDS}\n"
    f"  {OUTPUT_SUPPLIERS}\n"
    f"  {OUTPUT_SUPPLIER_MASTER}"
)


# ================================================================
# 18. FINAL VALIDATION
# ================================================================

print("\n" + "=" * 75)
print("STEP 5: FINAL EXTRACTION VALIDATION")
print("=" * 75)


print("\nDataset sizes:")

print(
    f"  Releases: "
    f"{len(releases_2025):,} rows × "
    f"{len(releases_2025.columns)} columns"
)

print(
    f"  Awards: "
    f"{len(awards_2025):,} rows × "
    f"{len(awards_2025.columns)} columns"
)

print(
    f"  Award-suppliers: "
    f"{len(award_suppliers_2025):,} rows × "
    f"{len(award_suppliers_2025.columns)} columns"
)

print(
    f"  Supplier master: "
    f"{len(supplier_master):,} rows × "
    f"{len(supplier_master.columns)} columns"
)


# ---------------------------------------------------------------
# Unique identifiers
# ---------------------------------------------------------------

if not releases_2025.empty:

    print("\nRelease identifiers:")

    print(
        f"  Unique OCIDs: "
        f"{releases_2025['ocid'].nunique():,}"
    )

    print(
        f"  Unique release IDs: "
        f"{releases_2025['release_id'].nunique():,}"
    )


if not awards_2025.empty:

    print("\nAward identifiers:")

    print(
        f"  Unique award IDs: "
        f"{awards_2025['award_id'].nunique():,}"
    )


if not award_suppliers_2025.empty:

    print("\nSupplier identifiers:")

    print(
        f"  Unique supplier IDs: "
        f"{award_suppliers_2025['supplier_id'].nunique():,}"
    )

    print(
        f"  Unique supplier names: "
        f"{award_suppliers_2025['supplier_name'].nunique():,}"
    )

    print(
        f"  Unique normalized supplier names: "
        f"{award_suppliers_2025['supplier_name_normalized'].nunique():,}"
    )


# ---------------------------------------------------------------
# Referential integrity
# ---------------------------------------------------------------

print("\nReferential integrity checks:")

release_ids = set(
    releases_2025["release_id"].dropna()
)

award_release_ids = set(
    awards_2025["release_id"].dropna()
)

supplier_release_ids = set(
    award_suppliers_2025["release_id"].dropna()
)


orphan_awards = (
    award_release_ids
    - release_ids
)

orphan_supplier_releases = (
    supplier_release_ids
    - release_ids
)


print(
    f"  Award records without matching release: "
    f"{len(orphan_awards):,}"
)

print(
    f"  Supplier records without matching release: "
    f"{len(orphan_supplier_releases):,}"
)


# ---------------------------------------------------------------
# Award -> supplier integrity
# ---------------------------------------------------------------

award_ids = set(
    awards_2025["award_id"].dropna()
)

supplier_award_ids = set(
    award_suppliers_2025["award_id"].dropna()
)


orphan_supplier_awards = (
    supplier_award_ids
    - award_ids
)


print(
    f"  Supplier relationships without matching award: "
    f"{len(orphan_supplier_awards):,}"
)


# ---------------------------------------------------------------
# Multiple awards per release
# ---------------------------------------------------------------

if not awards_2025.empty:

    awards_per_release = (
        awards_2025
        .groupby("release_id")
        .size()
    )

    print("\nAward cardinality:")

    print(
        f"  Releases with awards: "
        f"{awards_per_release.shape[0]:,}"
    )

    print(
        f"  Maximum awards in one release: "
        f"{awards_per_release.max():,}"
    )


# ---------------------------------------------------------------
# Multiple suppliers per award
# ---------------------------------------------------------------

if not award_suppliers_2025.empty:

    suppliers_per_award = (
        award_suppliers_2025
        .groupby("award_id")
        .size()
    )

    print("\nSupplier cardinality:")

    print(
        f"  Awards with suppliers: "
        f"{suppliers_per_award.shape[0]:,}"
    )

    print(
        f"  Maximum suppliers linked to one award: "
        f"{suppliers_per_award.max():,}"
    )


# ================================================================
# 19. BASIC BUSINESS DATA CHECK
# ================================================================

print("\n" + "=" * 75)
print("BASIC BUSINESS DATA CHECK")
print("=" * 75)


if not releases_2025.empty:

    print("\nProcurement categories:")

    print(
        releases_2025[
            "procurement_category"
        ]
        .value_counts(dropna=False)
        .head(10)
    )


if not awards_2025.empty:

    print("\nAward status:")

    print(
        awards_2025[
            "award_status"
        ]
        .value_counts(dropna=False)
        .head(10)
    )


if not award_suppliers_2025.empty:

    print("\nTop 10 suppliers by award relationships:")

    print(
        award_suppliers_2025[
            "supplier_name_normalized"
        ]
        .value_counts()
        .head(10)
    )


# ================================================================
# 20. COMPLETION
# ================================================================

print("\n" + "=" * 75)
print("NORMALIZED EXTRACTION COMPLETE")
print("=" * 75)

print(
    "\nThe raw data has been transformed into separate "
    "release, award, supplier-relationship and supplier-master "
    "datasets."
)

print(
    "\nNext step: inspect the extraction results and "
    "validate duplicate/lifecycle relationships before "
    "building the SQLite database."
)

print("=" * 75)