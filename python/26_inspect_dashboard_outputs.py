
from pathlib import Path
import pandas as pd


# ============================================================
# DASHBOARD OUTPUT INSPECTION
# ============================================================

DASHBOARD_DIR = Path("data/processed/analysis/dashboard")

print("=" * 80)
print("DASHBOARD CSV OUTPUT INSPECTION")
print("=" * 80)

if not DASHBOARD_DIR.exists():
    raise FileNotFoundError(
        f"Dashboard directory not found: {DASHBOARD_DIR.resolve()}"
    )

csv_files = sorted(DASHBOARD_DIR.glob("*.csv"))

if not csv_files:
    raise FileNotFoundError(
        f"No CSV files found in: {DASHBOARD_DIR.resolve()}"
    )

print(f"\nDashboard directory:")
print(DASHBOARD_DIR.resolve())

print(f"\nCSV files found: {len(csv_files)}")

# ============================================================
# INSPECT EACH FILE
# ============================================================

for number, file_path in enumerate(csv_files, start=1):

    print("\n" + "=" * 80)
    print(f"[{number}/{len(csv_files)}] {file_path.name}")
    print("=" * 80)

    try:
        df = pd.read_csv(file_path)

        print(f"\nRows:    {len(df):,}")
        print(f"Columns: {len(df.columns):,}")

        print("\nColumn names:")
        for i, column in enumerate(df.columns, start=1):
            print(f"  {i:>2}. {column}")

        print("\nData types:")
        print(df.dtypes.to_string())

        print("\nFirst 5 rows:")

        if df.empty:
            print("  [EMPTY FILE]")
        else:
            print(
                df.head(5).to_string(
                    index=False,
                    max_cols=30,
                    max_colwidth=40
                )
            )

    except Exception as error:
        print(f"\nERROR reading {file_path.name}:")
        print(error)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("INSPECTION COMPLETE")
print("=" * 80)

print(f"\nFiles inspected: {len(csv_files)}")
print(f"Directory: {DASHBOARD_DIR.resolve()}")

print("\nNext step:")
print("Review the output above before building the dashboard.")
