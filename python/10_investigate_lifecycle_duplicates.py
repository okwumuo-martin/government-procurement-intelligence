"""
10_investigate_lifecycle_duplicates.py

Investigate Contracts Finder 2025:
- procurement lifecycle
- repeated release IDs
- multiple releases per OCID
- release tag sequences
- award lifecycle
- potential duplicate vs legitimate repeated records

This script does NOT delete records.
It produces evidence for the final database design.
"""

from pathlib import Path
import pandas as pd
import sys

# ============================================================
# WINDOWS UTF-8 SAFETY
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DOCS_DIR = PROJECT_ROOT / "docs"

DOCS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("CONTRACTS FINDER 2025")
print("LIFECYCLE AND DUPLICATE RELEASE INVESTIGATION")
print("=" * 70)

releases_file = PROCESSED_DIR / "releases_2025.csv"
awards_file = PROCESSED_DIR / "awards_2025.csv"
supplier_file = PROCESSED_DIR / "award_suppliers_2025.csv"

print("\nLoading normalized datasets...")

releases = pd.read_csv(
    releases_file,
    low_memory=False
)

awards = pd.read_csv(
    awards_file,
    low_memory=False
)

suppliers = pd.read_csv(
    supplier_file,
    low_memory=False
)

print(f"Procurement releases: {len(releases):,}")
print(f"Awards:               {len(awards):,}")
print(f"Supplier relationships:{len(suppliers):,}")


# ============================================================
# DATE CONVERSION
# ============================================================

releases["release_date"] = pd.to_datetime(
    releases["release_date"],
    errors="coerce",
    utc=True
)

if "award_date" in awards.columns:
    awards["award_date"] = pd.to_datetime(
        awards["award_date"],
        errors="coerce",
        utc=True
    )


# ============================================================
# REPORT STORAGE
# ============================================================

report = []

def add(text=""):
    print(text)
    report.append(str(text))


# ============================================================
# 1. BASIC STRUCTURE
# ============================================================

add("\n" + "=" * 70)
add("1. DATASET STRUCTURE")
add("=" * 70)

add(f"Release rows:             {len(releases):,}")
add(f"Unique OCIDs:             {releases['ocid'].nunique(dropna=True):,}")
add(f"Unique release IDs:       {releases['release_id'].nunique(dropna=True):,}")

if "award_id" in awards.columns:
    add(f"Award rows:               {len(awards):,}")
    add(f"Unique award IDs:         {awards['award_id'].nunique(dropna=True):,}")

if "supplier_id" in suppliers.columns:
    add(
        f"Unique supplier IDs:     "
        f"{suppliers['supplier_id'].nunique(dropna=True):,}"
    )

if "supplier_name" in suppliers.columns:
    add(
        f"Unique supplier names:   "
        f"{suppliers['supplier_name'].nunique(dropna=True):,}"
    )


# ============================================================
# 2. RELEASE TAG DISTRIBUTION
# ============================================================

add("\n" + "=" * 70)
add("2. RELEASE TAG DISTRIBUTION")
add("=" * 70)

tag_counts = (
    releases["release_tag"]
    .value_counts(dropna=False)
)

for tag, count in tag_counts.items():
    pct = count / len(releases) * 100
    add(f"{str(tag):25} {count:8,} ({pct:6.2f}%)")


# ============================================================
# 3. RELEASES PER OCID
# ============================================================

add("\n" + "=" * 70)
add("3. RELEASES PER PROCUREMENT (OCID)")
add("=" * 70)

releases_per_ocid = (
    releases.groupby("ocid")
    .size()
    .sort_values(ascending=False)
)

add(f"OCIDs with one release:      {(releases_per_ocid == 1).sum():,}")
add(f"OCIDs with multiple releases:{(releases_per_ocid > 1).sum():,}")
add(f"Maximum releases for one OCID: {releases_per_ocid.max():,}")

add("\nDistribution:")

distribution = releases_per_ocid.value_counts().sort_index()

for n_releases, count in distribution.items():
    add(
        f"  {n_releases:>3} release(s): "
        f"{count:>8,} OCIDs"
    )


# ============================================================
# 4. MULTI-RELEASE OCIDs
# ============================================================

add("\n" + "=" * 70)
add("4. EXAMPLES OF MULTI-RELEASE PROCUREMENTS")
add("=" * 70)

multi_ocids = releases_per_ocid[
    releases_per_ocid > 1
].head(20)

if len(multi_ocids) == 0:
    add("No multi-release OCIDs found.")
else:

    for ocid in multi_ocids.index:

        subset = releases[
            releases["ocid"] == ocid
        ].sort_values("release_date")

        add(f"\nOCID: {ocid}")
        add(f"Number of releases: {len(subset)}")

        columns = [
            "release_id",
            "release_date",
            "release_tag",
            "tender_title",
            "buyer_name"
        ]

        columns = [
            col for col in columns
            if col in subset.columns
        ]

        for _, row in subset[columns].iterrows():

            add(
                "  "
                f"{row.get('release_date')} | "
                f"{row.get('release_tag')} | "
                f"{row.get('release_id')}"
            )


# ============================================================
# 5. RELEASE TAG SEQUENCES
# ============================================================

add("\n" + "=" * 70)
add("5. RELEASE TAG SEQUENCES")
add("=" * 70)

sequence_counts = {}

for ocid, group in releases.groupby("ocid"):

    ordered = (
        group
        .sort_values("release_date")
        ["release_tag"]
        .dropna()
        .astype(str)
        .tolist()
    )

    if not ordered:
        continue

    sequence = " -> ".join(ordered)

    sequence_counts[sequence] = (
        sequence_counts.get(sequence, 0) + 1
    )

add("\nMost common lifecycle sequences:")

for sequence, count in sorted(
    sequence_counts.items(),
    key=lambda x: x[1],
    reverse=True
)[:20]:

    add(
        f"{count:8,}  {sequence}"
    )


# ============================================================
# 6. REPEATED RELEASE IDs
# ============================================================

add("\n" + "=" * 70)
add("6. REPEATED RELEASE IDs")
add("=" * 70)

release_id_counts = (
    releases["release_id"]
    .value_counts()
)

repeated_release_ids = release_id_counts[
    release_id_counts > 1
]

add(
    f"Unique release IDs:       "
    f"{releases['release_id'].nunique():,}"
)

add(
    f"Repeated release IDs:     "
    f"{len(repeated_release_ids):,}"
)

add(
    f"Rows involved in repeats: "
    f"{repeated_release_ids.sum():,}"
)


# ============================================================
# 7. INVESTIGATE REPEATED RELEASE IDS
# ============================================================

add("\n" + "=" * 70)
add("7. REPEATED RELEASE ID INVESTIGATION")
add("=" * 70)

if len(repeated_release_ids) == 0:

    add("No repeated release IDs found.")

else:

    add("\nFirst 20 repeated release IDs:")

    for release_id in repeated_release_ids.head(20).index:

        subset = releases[
            releases["release_id"] == release_id
        ]

        add(f"\nRelease ID: {release_id}")

        compare_columns = [
            "release_id",
            "ocid",
            "release_date",
            "release_tag",
            "tender_id",
            "tender_title",
            "buyer_id",
            "buyer_name",
            "tender_status",
            "tender_value",
            "procurement_method",
            "procurement_category",
            "source_file"
        ]

        compare_columns = [
            col for col in compare_columns
            if col in subset.columns
        ]

        add(
            subset[compare_columns]
            .to_string(index=False)
        )


# ============================================================
# 8. ARE REPEATED RELEASE IDS EXACT DUPLICATES?
# ============================================================

add("\n" + "=" * 70)
add("8. DUPLICATE CLASSIFICATION")
add("=" * 70)

key_columns = [
    col for col in [
        "ocid",
        "release_id",
        "release_date",
        "release_tag",
        "tender_id",
        "tender_title",
        "buyer_id",
        "buyer_name",
        "tender_status",
        "tender_value",
        "tender_currency",
        "procurement_method",
        "procurement_category"
    ]
    if col in releases.columns
]

duplicate_groups = []

for release_id, group in releases[
    releases["release_id"].isin(
        repeated_release_ids.index
    )
].groupby("release_id"):

    distinct_versions = group[key_columns].drop_duplicates()

    duplicate_groups.append({
        "release_id": release_id,
        "rows": len(group),
        "distinct_key_versions": len(distinct_versions)
    })

duplicate_analysis = pd.DataFrame(
    duplicate_groups
)

if len(duplicate_analysis):

    exact_repeat_ids = (
        duplicate_analysis[
            duplicate_analysis["distinct_key_versions"] == 1
        ]
    )

    changed_repeat_ids = (
        duplicate_analysis[
            duplicate_analysis["distinct_key_versions"] > 1
        ]
    )

    add(
        f"Repeated IDs with identical key fields: "
        f"{len(exact_repeat_ids):,}"
    )

    add(
        f"Repeated IDs with changed key fields:   "
        f"{len(changed_repeat_ids):,}"
    )

    add(
        f"Total repeated IDs investigated:         "
        f"{len(duplicate_analysis):,}"
    )


# ============================================================
# 9. SAME OCID + SAME TAG
# ============================================================

add("\n" + "=" * 70)
add("9. SAME OCID + SAME RELEASE TAG")
add("=" * 70)

ocid_tag_counts = (
    releases
    .groupby(["ocid", "release_tag"], dropna=False)
    .size()
)

repeated_ocid_tag = (
    ocid_tag_counts[
        ocid_tag_counts > 1
    ]
)

add(
    f"OCID/tag combinations occurring more than once: "
    f"{len(repeated_ocid_tag):,}"
)

if len(repeated_ocid_tag):

    add("\nTop repeated OCID/tag combinations:")

    for (ocid, tag), count in repeated_ocid_tag.head(20).items():

        add(
            f"  {count:>3} | "
            f"{tag} | "
            f"{ocid}"
        )


# ============================================================
# 10. AWARD LIFECYCLE
# ============================================================

add("\n" + "=" * 70)
add("10. AWARD LIFECYCLE")
add("=" * 70)

if "award_status" in awards.columns:

    award_status_counts = (
        awards["award_status"]
        .value_counts(dropna=False)
    )

    add("Award statuses:")

    for status, count in award_status_counts.items():

        pct = count / len(awards) * 100

        add(
            f"  {str(status):25} "
            f"{count:>8,} ({pct:6.2f}%)"
        )


# ============================================================
# 11. AWARDS PER OCID
# ============================================================

add("\n" + "=" * 70)
add("11. AWARDS PER PROCUREMENT")
add("=" * 70)

if "ocid" in awards.columns:

    awards_per_ocid = (
        awards
        .groupby("ocid")
        .size()
        .sort_values(ascending=False)
    )

    add(
        f"OCIDs with awards: "
        f"{len(awards_per_ocid):,}"
    )

    add(
        f"Maximum awards for one OCID: "
        f"{awards_per_ocid.max():,}"
    )

    add(
        f"OCIDs with multiple awards: "
        f"{(awards_per_ocid > 1).sum():,}"
    )


# ============================================================
# 12. AWARD ID DUPLICATES
# ============================================================

add("\n" + "=" * 70)
add("12. REPEATED AWARD IDs")
add("=" * 70)

if "award_id" in awards.columns:

    award_id_counts = (
        awards["award_id"]
        .value_counts()
    )

    repeated_awards = award_id_counts[
        award_id_counts > 1
    ]

    add(
        f"Unique award IDs: "
        f"{awards['award_id'].nunique():,}"
    )

    add(
        f"Repeated award IDs: "
        f"{len(repeated_awards):,}"
    )

    if len(repeated_awards):

        add("\nExamples:")

        for award_id in repeated_awards.head(20).index:

            subset = awards[
                awards["award_id"] == award_id
            ]

            columns = [
                "award_id",
                "ocid",
                "release_id",
                "award_date",
                "award_status",
                "award_value",
                "source_file"
            ]

            columns = [
                col for col in columns
                if col in subset.columns
            ]

            add(f"\nAward ID: {award_id}")

            add(
                subset[columns]
                .to_string(index=False)
            )


# ============================================================
# 13. AWARDS LINKED TO RELEASES
# ============================================================

add("\n" + "=" * 70)
add("13. RELEASE-TO-AWARD LINKAGE")
add("=" * 70)

if "release_id" in awards.columns:

    awards_per_release = (
        awards
        .groupby("release_id")
        .size()
    )

    add(
        f"Releases with at least one award: "
        f"{len(awards_per_release):,}"
    )

    add(
        f"Maximum awards linked to one release: "
        f"{awards_per_release.max():,}"
    )

    add(
        f"Releases with multiple awards: "
        f"{(awards_per_release > 1).sum():,}"
    )


# ============================================================
# 14. SUPPLIER RELATIONSHIP MULTIPLICITY
# ============================================================

add("\n" + "=" * 70)
add("14. SUPPLIER RELATIONSHIP MULTIPLICITY")
add("=" * 70)

if "award_id" in suppliers.columns:

    suppliers_per_award = (
        suppliers
        .groupby("award_id")
        .size()
    )

    add(
        f"Awards with suppliers: "
        f"{len(suppliers_per_award):,}"
    )

    add(
        f"Maximum suppliers linked to one award: "
        f"{suppliers_per_award.max():,}"
    )

    add(
        f"Awards with multiple suppliers: "
        f"{(suppliers_per_award > 1).sum():,}"
    )


# ============================================================
# 15. POTENTIAL DUPLICATE AWARD-SUPPLIER RELATIONSHIPS
# ============================================================

add("\n" + "=" * 70)
add("15. POTENTIAL DUPLICATE SUPPLIER RELATIONSHIPS")
add("=" * 70)

relationship_keys = [
    col for col in [
        "award_id",
        "supplier_id",
        "supplier_name"
    ]
    if col in suppliers.columns
]

if relationship_keys:

    relationship_counts = (
        suppliers
        .groupby(relationship_keys, dropna=False)
        .size()
    )

    repeated_relationships = (
        relationship_counts[
            relationship_counts > 1
        ]
    )

    add(
        f"Repeated award-supplier combinations: "
        f"{len(repeated_relationships):,}"
    )

    if len(repeated_relationships):

        add("\nTop examples:")

        for keys, count in repeated_relationships.head(20).items():

            add(
                f"  {count:>3} occurrences | "
                f"{keys}"
            )


# ============================================================
# 16. FINAL INTERPRETATION
# ============================================================

add("\n" + "=" * 70)
add("16. INVESTIGATION INTERPRETATION")
add("=" * 70)

add(
    """
The investigation distinguishes between:

1. Legitimate lifecycle records
   - multiple releases for the same OCID
   - tender, award, amendment and award-update events
   - multiple awards associated with one procurement

2. Potential duplicate records
   - repeated release IDs
   - repeated award IDs
   - repeated award-supplier relationships

No records are deleted by this investigation.

The database should preserve legitimate lifecycle events and only
remove records when duplication is demonstrated by the evidence.

Recommended analytical principle:

    PROCUREMENT
        |
        +-- RELEASE
        |
        +-- AWARD
               |
               +-- AWARD_SUPPLIER
                      |
                      +-- SUPPLIER

Release-level lifecycle information should remain available for
auditability and procurement-process analysis.
"""
)


# ============================================================
# SAVE REPORT
# ============================================================

report_file = DOCS_DIR / "lifecycle_duplicate_investigation.txt"

with open(
    report_file,
    "w",
    encoding="utf-8"
) as f:

    f.write("\n".join(report))

print("\n" + "=" * 70)
print("INVESTIGATION COMPLETE")
print("=" * 70)
print(f"Report saved to: {report_file}")