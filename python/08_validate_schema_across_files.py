from pathlib import Path
import pandas as pd
import re
import sys

# ============================================================
# CONTRACTS FINDER 2025
# YEAR-WIDE SCHEMA VALIDATION
# ============================================================

# Windows UTF-8 safety
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

print("=" * 70)
print("CONTRACTS FINDER 2025 YEAR-WIDE SCHEMA VALIDATION")
print("=" * 70)

# ------------------------------------------------------------
# 1. FIND RAW FILES
# ------------------------------------------------------------

files = sorted(RAW_DIR.glob("Contracts Finder OCDS 2025-*.csv"))

print(f"\nRaw CSV files found: {len(files)}")

if not files:
    raise RuntimeError("No Contracts Finder 2025 CSV files found.")

# ------------------------------------------------------------
# 2. SCHEMA PATTERNS
# ------------------------------------------------------------

award_pattern = re.compile(
    r"^releases/0/awards/(\d+)/"
)

supplier_pattern = re.compile(
    r"^releases/0/awards/(\d+)/suppliers/(\d+)/"
)

# Track everything found across the entire year
award_indexes_by_file = {}
supplier_indexes_by_file = {}

all_award_indexes = set()
all_supplier_positions = set()

# ------------------------------------------------------------
# 3. SCAN EVERY FILE HEADER
# ------------------------------------------------------------

print("\nScanning headers across all files...")
print("-" * 70)

for i, file_path in enumerate(files, start=1):

    try:
        header = pd.read_csv(
            file_path,
            nrows=0,
            encoding="utf-8-sig"
        ).columns.tolist()

    except UnicodeDecodeError:
        header = pd.read_csv(
            file_path,
            nrows=0,
            encoding="latin1"
        ).columns.tolist()

    award_indexes = set()
    supplier_positions = set()

    for column in header:

        award_match = award_pattern.match(column)

        if award_match:
            award_index = int(award_match.group(1))
            award_indexes.add(award_index)
            all_award_indexes.add(award_index)

        supplier_match = supplier_pattern.match(column)

        if supplier_match:
            award_index = int(supplier_match.group(1))
            supplier_index = int(supplier_match.group(2))

            supplier_positions.add(
                (award_index, supplier_index)
            )

            all_supplier_positions.add(
                (award_index, supplier_index)
            )

    award_indexes_by_file[file_path.name] = sorted(award_indexes)
    supplier_indexes_by_file[file_path.name] = sorted(
        supplier_positions
    )

    print(
        f"Scanned {i:>3}/{len(files)}: "
        f"{file_path.name} | "
        f"Awards: {sorted(award_indexes) if award_indexes else 'None'} | "
        f"Suppliers: {sorted(supplier_positions) if supplier_positions else 'None'}"
    )

# ------------------------------------------------------------
# 4. YEAR-WIDE RESULTS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("YEAR-WIDE SCHEMA RESULTS")
print("=" * 70)

print(
    "\nAward indexes found across the entire dataset:"
)
print(
    sorted(all_award_indexes)
    if all_award_indexes
    else "None"
)

print(
    "\nMaximum award index:"
)

if all_award_indexes:
    print(max(all_award_indexes))

    print(
        f"Therefore maximum awards represented in a release: "
        f"{max(all_award_indexes) + 1}"
    )
else:
    print("None")

print(
    "\nSupplier positions found across the entire dataset:"
)

if all_supplier_positions:
    for award_index, supplier_index in sorted(
        all_supplier_positions
    ):
        print(
            f"  Award {award_index} -> "
            f"Supplier {supplier_index}"
        )

    max_supplier_index = max(
        supplier_index
        for _, supplier_index in all_supplier_positions
    )

    print(
        f"\nMaximum supplier index: {max_supplier_index}"
    )

    print(
        f"Maximum suppliers represented within one award: "
        f"{max_supplier_index + 1}"
    )

else:
    print("None")

# ------------------------------------------------------------
# 5. FILES WITH MULTIPLE AWARDS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FILES CONTAINING MULTIPLE AWARD POSITIONS")
print("=" * 70)

multiple_award_files = {
    filename: indexes
    for filename, indexes
    in award_indexes_by_file.items()
    if len(indexes) > 1
}

print(
    f"\nFiles with more than one award position: "
    f"{len(multiple_award_files)}"
)

for filename, indexes in list(
    multiple_award_files.items()
)[:20]:

    print(
        f"  {filename}: awards {indexes}"
    )

if len(multiple_award_files) > 20:
    print(
        f"  ... and "
        f"{len(multiple_award_files) - 20} more"
    )

# ------------------------------------------------------------
# 6. FILES CONTAINING MULTIPLE SUPPLIERS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FILES CONTAINING MULTIPLE SUPPLIER POSITIONS")
print("=" * 70)

multiple_supplier_files = {
    filename: positions
    for filename, positions
    in supplier_indexes_by_file.items()
    if len(positions) > 1
}

print(
    f"\nFiles with more than one supplier position: "
    f"{len(multiple_supplier_files)}"
)

for filename, positions in list(
    multiple_supplier_files.items()
)[:20]:

    print(
        f"  {filename}: suppliers {positions}"
    )

if len(multiple_supplier_files) > 20:
    print(
        f"  ... and "
        f"{len(multiple_supplier_files) - 20} more"
    )

# ------------------------------------------------------------
# 7. DISTRIBUTION OF SCHEMA COMPLEXITY
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("SCHEMA COMPLEXITY DISTRIBUTION")
print("=" * 70)

award_position_counts = {}

for indexes in award_indexes_by_file.values():

    count = len(indexes)

    award_position_counts[count] = (
        award_position_counts.get(count, 0) + 1
    )

print("\nNumber of award positions per file:")

for count in sorted(award_position_counts):

    print(
        f"  {count} award position(s): "
        f"{award_position_counts[count]} files"
    )

supplier_position_counts = {}

for positions in supplier_indexes_by_file.values():

    count = len(positions)

    supplier_position_counts[count] = (
        supplier_position_counts.get(count, 0) + 1
    )

print("\nNumber of supplier positions per file:")

for count in sorted(supplier_position_counts):

    print(
        f"  {count} supplier position(s): "
        f"{supplier_position_counts[count]} files"
    )

# ------------------------------------------------------------
# 8. FINAL DATA MODEL RECOMMENDATION
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("DATA MODEL IMPLICATION")
print("=" * 70)

print(
    """
The raw Contracts Finder data is nested OCDS data.

The recommended relational model is:

    PROCUREMENT
         |
         | 1-to-many
         v
    RELEASE
         |
         | 1-to-many
         v
       AWARD
         |
         | many-to-many
         v
      SUPPLIER

The database should therefore NOT assume:

    one procurement = one release
    one release = one award
    one award = one supplier

Instead, the relational structure should preserve
the possibility of multiple lifecycle records.
"""
)

print("=" * 70)
print("YEAR-WIDE SCHEMA VALIDATION COMPLETE")
print("=" * 70)