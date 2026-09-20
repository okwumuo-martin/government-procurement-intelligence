from pathlib import Path
import sqlite3
import pandas as pd
import sys


# ============================================================
# CONTRACTS FINDER 2025
# SQL ANALYSIS RUNNER
# ============================================================

print("=" * 70)
print("CONTRACTS FINDER 2025")
print("PROCUREMENT PERFORMANCE SQL ANALYSIS")
print("=" * 70)


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "database"
    / "procurement_2025.db"
)

if len(sys.argv) > 1:
    sql_filename = sys.argv[1]
else:
    sql_filename = "03_procurement_analysis.sql"

SQL_PATH = PROJECT_ROOT / "sql" / sql_filename

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "sql_results"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. CHECK REQUIRED FILES
# ============================================================

print("\nChecking required files...")

if not DATABASE_PATH.exists():
    raise FileNotFoundError(
        f"SQLite database not found:\n{DATABASE_PATH}"
    )

if not SQL_PATH.exists():
    raise FileNotFoundError(
        f"SQL analysis file not found:\n{SQL_PATH}"
    )

print(f"  [OK] Database: {DATABASE_PATH.name}")
print(f"  [OK] SQL file: {SQL_PATH.name}")


# ============================================================
# 3. CONNECT TO SQLITE
# ============================================================

print("\nConnecting to SQLite database...")

conn = sqlite3.connect(DATABASE_PATH)

print("  [OK] Connection established")


# ============================================================
# 4. READ SQL FILE
# ============================================================

print("\nReading SQL analysis file...")

sql_text = SQL_PATH.read_text(
    encoding="utf-8"
)

print(
    f"  [OK] SQL file loaded "
    f"({len(sql_text):,} characters)"
)


# ============================================================
# 5. SPLIT SQL INTO INDIVIDUAL QUERIES
# ============================================================

# Remove comment-only lines while preserving SQL.
lines = []

for line in sql_text.splitlines():

    stripped = line.strip()

    if stripped.startswith("--"):
        continue

    lines.append(line)


clean_sql = "\n".join(lines)


# Split statements at semicolons.
queries = [
    query.strip()
    for query in clean_sql.split(";")
    if query.strip()
]


print(
    f"  [OK] SQL statements detected: "
    f"{len(queries)}"
)


# ============================================================
# 6. RUN EACH QUERY
# ============================================================

print("\n" + "=" * 70)
print("RUNNING SQL ANALYSIS")
print("=" * 70)


results = []


for number, query in enumerate(queries, start=1):

    print("\n" + "=" * 70)
    print(f"QUERY {number}")
    print("=" * 70)

    try:

        dataframe = pd.read_sql_query(
            query,
            conn
        )

        row_count = len(dataframe)

        print(
            f"Rows returned: {row_count:,}"
        )

        # ----------------------------------------------------
        # Save every query result to CSV
        # ----------------------------------------------------

        sql_stem = Path(sql_filename).stem

        result_filename = (
            f"{sql_stem}_query_{number:02d}.csv"
        )

        result_path = OUTPUT_DIR / result_filename

        dataframe.to_csv(
            result_path,
            index=False
        )

        print(
            f"Full result saved to:"
            f"\n  {result_path}"
        )

        # ----------------------------------------------------
        # Display manageable preview
        # ----------------------------------------------------

        if row_count == 0:

            print("\nNo rows returned.")

        elif row_count <= 20:

            print("\nQuery result:")

            with pd.option_context(
                "display.max_columns", None,
                "display.width", 180,
                "display.max_colwidth", 50
            ):
                print(
                    dataframe.to_string(
                        index=False
                    )
                )

        else:

            print(
                "\nPreview "
                "(first 10 rows):"
            )

            with pd.option_context(
                "display.max_columns", None,
                "display.width", 180,
                "display.max_colwidth", 50
            ):
                print(
                    dataframe.head(10).to_string(
                        index=False
                    )
                )

            print(
                f"\n... {row_count - 10:,} "
                f"additional rows saved to CSV."
            )

        results.append({
            "query_number": number,
            "status": "SUCCESS",
            "rows_returned": row_count,
            "result_file": result_filename
        })

    except Exception as error:

        print(
            f"[ERROR] Query {number} failed:"
        )

        print(error)

        results.append({
            "query_number": number,
            "status": "FAILED",
            "rows_returned": 0,
            "result_file": ""
        })


# ============================================================
# 7. SAVE QUERY EXECUTION LOG
# ============================================================

execution_log = pd.DataFrame(results)

sql_stem = Path(sql_filename).stem

log_filename = (
    f"{sql_stem}_execution_log.csv"
)

log_path = OUTPUT_DIR / log_filename

execution_log.to_csv(
    log_path,
    index=False
)

print("\nExecution log saved to:")
print(f"  {log_path}")


# ============================================================
# 8. CLOSE DATABASE CONNECTION
# ============================================================

conn.close()


# ============================================================
# 9. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("SQL ANALYSIS COMPLETE")
print("=" * 70)

successful = (
    execution_log["status"] == "SUCCESS"
).sum()

failed = (
    execution_log["status"] == "FAILED"
).sum()

print(
    f"\nQueries executed: {len(execution_log)}"
)

print(
    f"Successful:       {successful}"
)

print(
    f"Failed:           {failed}"
)

print(
    f"\nAll query results saved to:\n"
    f"  {OUTPUT_DIR}"
)

print("=" * 70)