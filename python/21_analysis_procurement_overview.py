from pathlib import Path
import pandas as pd


# ============================================================
# GOVERNMENT PROCUREMENT INTELLIGENCE
# ANALYSIS 01 — PROCUREMENT OVERVIEW
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "analysis"
    / "procurement_analytical_dataset.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "analysis"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

print("=" * 70)
print("GOVERNMENT PROCUREMENT INTELLIGENCE")
print("ANALYSIS 01 — PROCUREMENT OVERVIEW")
print("=" * 70)


# ============================================================
# 1. LOAD DATA
# ============================================================

print("\nLoading analytical dataset...")

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Analytical dataset not found:\n{INPUT_FILE}\n\n"
        "Run python/20_build_analytical_dataset.py first."
    )

df = pd.read_csv(INPUT_FILE)

print(f"Records loaded: {len(df):,}")
print(f"Columns loaded: {len(df.columns):,}")


# ============================================================
# 2. BASIC DATASET PROFILE
# ============================================================

print("\n" + "=" * 70)
print("1. DATASET PROFILE")
print("=" * 70)

print(f"\nAward records:              {len(df):,}")

print(
    f"Unique buyers:              "
    f"{df['buyer_name'].nunique(dropna=True):,}"
)

print(
    f"Unique supplier records:    "
    f"{df['supplier_names'].nunique(dropna=True):,}"
)

print(
    f"Unique procurement methods: "
    f"{df['procurement_method_group'].nunique(dropna=True):,}"
)


# ============================================================
# 3. AWARD VALUE KPIs
# ============================================================

print("\n" + "=" * 70)
print("2. AWARD VALUE KPIs")
print("=" * 70)

valid_value = df["award_value"].dropna()

total_award_value = valid_value.sum()
mean_award_value = valid_value.mean()
median_award_value = valid_value.median()
max_award_value = valid_value.max()

print(
    f"\nTotal allocated award value: "
    f"£{total_award_value:,.2f}"
)

print(
    f"Average award value:         "
    f"£{mean_award_value:,.2f}"
)

print(
    f"Median award value:          "
    f"£{median_award_value:,.2f}"
)

print(
    f"Largest individual award:    "
    f"£{max_award_value:,.2f}"
)

print(
    f"Records with award value:    "
    f"{valid_value.shape[0]:,}"
)

print(
    f"Records missing award value: "
    f"{df['award_value'].isna().sum():,}"
)


# ============================================================
# 4. VALUE DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("3. AWARD VALUE DISTRIBUTION")
print("=" * 70)

value_distribution = (
    df["award_value_band"]
    .value_counts()
    .rename_axis("award_value_band")
    .reset_index(name="award_count")
)

value_distribution["percentage"] = (
    value_distribution["award_count"]
    / len(df)
    * 100
)

print(
    value_distribution
    .to_string(index=False)
)


# ============================================================
# 5. PROCUREMENT METHOD ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("4. PROCUREMENT METHOD")
print("=" * 70)

method_summary = (
    df.groupby(
        "procurement_method_group",
        dropna=False
    )
    .agg(
        award_count=("award_id", "count"),
        allocated_award_value=("award_value", "sum"),
        median_award_value=("award_value", "median")
    )
    .reset_index()
)

method_summary["award_share_pct"] = (
    method_summary["award_count"]
    / method_summary["award_count"].sum()
    * 100
)

method_summary["value_share_pct"] = (
    method_summary["allocated_award_value"]
    / method_summary["allocated_award_value"].sum()
    * 100
)

method_summary = method_summary.sort_values(
    "allocated_award_value",
    ascending=False
)

print(
    method_summary
    .to_string(index=False)
)


# ============================================================
# 6. CONTRACT DURATION
# ============================================================

print("\n" + "=" * 70)
print("5. CONTRACT DURATION")
print("=" * 70)

duration_valid = df[
    df["contract_duration_years"].notna()
].copy()

print(
    f"\nRecords with contract duration: "
    f"{len(duration_valid):,}"
)

print(
    f"Average duration:              "
    f"{duration_valid['contract_duration_years'].mean():.2f} years"
)

print(
    f"Median duration:               "
    f"{duration_valid['contract_duration_years'].median():.2f} years"
)

print(
    f"Longest contract:              "
    f"{duration_valid['contract_duration_years'].max():.2f} years"
)

duration_summary = (
    df["contract_duration_band"]
    .value_counts()
    .rename_axis("contract_duration_band")
    .reset_index(name="award_count")
)

duration_summary["percentage"] = (
    duration_summary["award_count"]
    / len(df)
    * 100
)

print(
    "\nContract duration distribution:"
)

print(
    duration_summary
    .to_string(index=False)
)


# ============================================================
# 7. SUPPLIER STRUCTURE
# ============================================================

print("\n" + "=" * 70)
print("6. SUPPLIER STRUCTURE")
print("=" * 70)

supplier_structure = (
    df.groupby("supplier_structure")
    .agg(
        award_count=("award_id", "count"),
        allocated_award_value=("award_value", "sum")
    )
    .reset_index()
)

supplier_structure["award_share_pct"] = (
    supplier_structure["award_count"]
    / supplier_structure["award_count"].sum()
    * 100
)

supplier_structure["value_share_pct"] = (
    supplier_structure["allocated_award_value"]
    / supplier_structure["allocated_award_value"].sum()
    * 100
)

print(
    supplier_structure
    .to_string(index=False)
)


# ============================================================
# 8. TOP BUYERS
# ============================================================

print("\n" + "=" * 70)
print("7. TOP BUYERS BY ALLOCATED AWARD VALUE")
print("=" * 70)

top_buyers = (
    df.groupby("buyer_name", dropna=False)
    .agg(
        award_count=("award_id", "count"),
        allocated_award_value=("award_value", "sum"),
        median_award_value=("award_value", "median")
    )
    .reset_index()
    .sort_values(
        "allocated_award_value",
        ascending=False
    )
    .head(15)
)

print(
    top_buyers
    .to_string(index=False)
)


# ============================================================
# 9. TOP BUYERS BY AWARD COUNT
# ============================================================

print("\n" + "=" * 70)
print("8. TOP BUYERS BY NUMBER OF AWARDS")
print("=" * 70)

top_buyers_count = (
    df.groupby("buyer_name", dropna=False)
    .agg(
        award_count=("award_id", "count"),
        allocated_award_value=("award_value", "sum")
    )
    .reset_index()
    .sort_values(
        "award_count",
        ascending=False
    )
    .head(15)
)

print(
    top_buyers_count
    .to_string(index=False)
)


# ============================================================
# 10. DATA QUALITY OVERVIEW
# ============================================================

print("\n" + "=" * 70)
print("9. KEY DATA QUALITY INDICATORS")
print("=" * 70)

quality_metrics = {
    "Missing award value": int(
        df["award_value"].isna().sum()
    ),
    "Missing procurement method": int(
        df["procurement_method"].isna().sum()
    ),
    "Missing procurement category": int(
        df["procurement_category"].isna().sum()
    ),
    "Missing tender value": int(
        df["tender_value"].isna().sum()
    ),
    "No usable supplier": int(
        (df["supplier_structure"] == "No usable supplier").sum()
    ),
    "Supplier identity review": int(
    (
        df["supplier_identity_review_flag"]
        == "review_name_variation"
    ).sum()
)
}

for metric, value in quality_metrics.items():
    print(
        f"{metric:<35} {value:>8,}"
    )


# ============================================================
# 11. EXECUTIVE KPI TABLE
# ============================================================

print("\n" + "=" * 70)
print("10. EXECUTIVE KPI SUMMARY")
print("=" * 70)

kpis = pd.DataFrame(
    [
        {
            "metric": "Award records",
            "value": len(df)
        },
        {
            "metric": "Unique buyers",
            "value": df["buyer_name"].nunique(dropna=True)
        },
        {
            "metric": "Unique supplier records",
            "value": df["supplier_names"].nunique(dropna=True)
        },
        {
            "metric": "Total allocated award value",
            "value": total_award_value
        },
        {
            "metric": "Average award value",
            "value": mean_award_value
        },
        {
            "metric": "Median award value",
            "value": median_award_value
        },
        {
            "metric": "Largest award",
            "value": max_award_value
        },
        {
            "metric": "Average contract duration (years)",
            "value": duration_valid[
                "contract_duration_years"
            ].mean()
        },
        {
            "metric": "Median contract duration (years)",
            "value": duration_valid[
                "contract_duration_years"
            ].median()
        }
    ]
)

print(
    kpis.to_string(index=False)
)


# ============================================================
# 12. SAVE OUTPUTS
# ============================================================

print("\n" + "=" * 70)
print("SAVING ANALYSIS OUTPUTS")
print("=" * 70)

outputs = {
    "procurement_overview_kpis.csv": kpis,
    "procurement_method_summary.csv": method_summary,
    "procurement_value_distribution.csv": value_distribution,
    "procurement_duration_summary.csv": duration_summary,
    "procurement_supplier_structure.csv": supplier_structure,
    "top_buyers_by_value.csv": top_buyers,
    "top_buyers_by_count.csv": top_buyers_count
}

for filename, data in outputs.items():

    output_path = OUTPUT_DIR / filename

    data.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Saved: {filename}")


# ============================================================
# 13. FINAL CHECK
# ============================================================

print("\n" + "=" * 70)
print("ANALYSIS 01 COMPLETE")
print("=" * 70)

print(
    "\nExecutive procurement overview successfully generated."
)

print(
    "\nNext analysis:"
)

print(
    "  Analysis 02 — Supplier Concentration & Supplier Analytics"
)

print("=" * 70)