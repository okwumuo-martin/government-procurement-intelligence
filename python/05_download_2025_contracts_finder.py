import requests
from pathlib import Path
from datetime import date, timedelta
import time

# ============================================================
# Government Procurement Intelligence
# Step 4B: Download Contracts Finder OCDS data for 2025
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = (
    "https://www.contractsfinder.service.gov.uk/"
    "harvester/Notices/Data/CSV"
)

START_DATE = date(2025, 1, 1)
END_DATE = date(2025, 12, 31)

print("=" * 70)
print("GOVERNMENT PROCUREMENT INTELLIGENCE")
print("CONTRACTS FINDER 2025 DATA DOWNLOADER")
print("=" * 70)

print(f"\nStart date: {START_DATE}")
print(f"End date:   {END_DATE}")

# ------------------------------------------------------------
# Download counters
# ------------------------------------------------------------

downloaded = 0
skipped = 0
empty_files = 0
failed = 0

current_date = START_DATE

# ------------------------------------------------------------
# Process each calendar day
# ------------------------------------------------------------

while current_date <= END_DATE:

    year = current_date.year
    month = current_date.month
    day = current_date.day

    date_string = current_date.strftime("%Y-%m-%d")

    filename = (
        f"Contracts Finder OCDS {date_string}.csv"
    )

    output_file = RAW_DIR / filename

    url = (
        f"{BASE_URL}/"
        f"{year}/{month:02d}/{day:02d}"
    )

    print("\n" + "-" * 70)
    print(f"Date: {date_string}")
    print(f"URL:  {url}")

    # --------------------------------------------------------
    # Skip existing files
    # --------------------------------------------------------

    if output_file.exists():

        print("Status: already downloaded — skipping")

        skipped += 1

        current_date += timedelta(days=1)

        continue

    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

    try:

        response = requests.get(
            url,
            timeout=60
        )

        # ----------------------------------------------------
        # Handle HTTP response
        # ----------------------------------------------------

        if response.status_code == 200:

            content = response.content

            # Check for an empty response
            if len(content) == 0:

                print("Status: empty response")

                empty_files += 1

            else:

                output_file.write_bytes(content)

                size_mb = len(content) / (
                    1024 * 1024
                )

                print(
                    f"Status: downloaded "
                    f"({size_mb:.2f} MB)"
                )

                downloaded += 1

        elif response.status_code == 404:

            print(
                "Status: no file available "
                "(HTTP 404)"
            )

            empty_files += 1

        else:

            print(
                f"Status: HTTP {response.status_code}"
            )

            failed += 1

    except requests.RequestException as error:

        print(
            f"Status: download failed — {error}"
        )

        failed += 1

    # --------------------------------------------------------
    # Small pause to avoid hammering the service
    # --------------------------------------------------------

    time.sleep(0.2)

    current_date += timedelta(days=1)

# ------------------------------------------------------------
# Final summary
# ------------------------------------------------------------

print("\n")
print("=" * 70)
print("DOWNLOAD COMPLETE")
print("=" * 70)

print(f"\nDownloaded:      {downloaded:,}")
print(f"Already existed: {skipped:,}")
print(f"No/empty file:   {empty_files:,}")
print(f"Failed:          {failed:,}")

print("\nRaw data directory:")
print(RAW_DIR)

print("\n" + "=" * 70)