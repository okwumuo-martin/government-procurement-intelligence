# Government Procurement Intelligence: Supplier, Contract & Spend Analytics

> End-to-end procurement analytics platform built with Python, SQL and Streamlit using UK Contracts Finder / Open Contracting Data Standard (OCDS) data.

## 🚀 Live dashboard

**[Open the live dashboard](https://okwumuomartinukgovernmentprocurementanalytics.streamlit.app/)**

**[GitHub repository](https://github.com/okwumuo-martin/government-procurement-intelligence)**

## Executive summary

This project transforms UK public-procurement records into a validated analytical layer and an interactive decision-support dashboard.

The final analytical layer contains:

- **45,011 award records**
- **£449.8B allocated award value**
- **5,980 buyer entities**
- **36,746 usable supplier entities**
- **57,311 supplier relationship observations**

The analysis covers supplier concentration, buyer segmentation, procurement methods, contract duration, supplier structure, data quality and a transparent review-screening framework.

> **Important:** allocated award value is not actual supplier payments or government expenditure. For supplier-level analysis, multi-supplier award value is allocated equally across usable supplier relationships to avoid double-counting.

## Business question

> **How is public procurement award value distributed across buyers, suppliers and procurement structures, and where do the data indicate areas that merit further review?**

The project examines:

1. buyer and supplier concentration
2. procurement-method mix
3. contract-duration patterns
4. single- versus multi-supplier structures
5. high-value awards
6. combinations of observable characteristics suitable for further review
7. buyer and supplier data-quality issues

## Key findings

### Supplier concentration

Among usable supplier relationships:

| Supplier group | Allocated supplier value share |
|---|---:|
| Top 1% | **70.97%** |
| Top 5% | **86.79%** |
| Top 10% | **93.25%** |
| Top 25% | **98.24%** |
| Top 50% | **99.66%** |

This is a descriptive concentration result, not evidence of misconduct or improper procurement.

### Buyer concentration and activity

- **5,980** buyer entities
- **230 high-value buyers** account for **93.25%** of allocated award value
- **24 buyers with 200+ awards** account for **35.24%** of value
- **3,190 one-award buyers** account for **15.38%** of value

Buyer segmentation separates procurement activity from financial scale.

### Procurement methods

By award count:

| Method | Share |
|---|---:|
| Selective | 49.76% |
| Open | 18.73% |
| Unknown | 16.72% |
| Direct | 10.89% |
| Limited | 3.90% |

By allocated value:

| Method | Share |
|---|---:|
| Open | 72.04% |
| Selective | 24.12% |
| Unknown | 1.84% |
| Limited | 1.24% |
| Direct | 0.75% |

The difference shows why procurement analysis should examine both count and value.

### Contract duration

Across records with usable contract dates:

- mean: **1.90 years**
- median: approximately **1 year**
- **62.3%** last at least one year
- **30.5%** last at least three years
- **7.6%** last at least five years
- **0.48%** last at least ten years

Long duration is treated as a contextual feature, not evidence of a problem.

### Review screening

The project created a transparent Procurement Review Indicator (PRI) using observable characteristics such as:

- very high award value
- long contract duration
- direct or limited procurement method
- single usable supplier relationship

Final screening population:

- **4 Priority review records**
- **51 High review records**
- **55 High/Priority records**

The PRI is a portfolio-project screening framework, not an official government risk score, fraud detector or finding of wrongdoing.

## Data-quality engineering

A major part of the project was making the data analytically trustworthy.

The workflow investigated:

- repeated release records
- award lifecycle/versioning
- analytical grain
- duplicate award versions
- multi-supplier relationships
- supplier-name variation
- unreliable/missing supplier identifiers
- supplier reference-text records
- missing procurement fields
- buyer identity variation
- referential integrity

Awards were modelled at:

`award_id + release_id`

Supplier relationships were modelled separately so that one award can legitimately have multiple suppliers.

## Analytical workflow

```text
Contracts Finder / OCDS
        ↓
Raw daily CSV files
        ↓
Schema + field profiling
        ↓
Cleaning and lifecycle investigation
        ↓
Normalized analytical layer
        ↓
Validation and reconciliation
        ↓
SQLite + SQL analysis
        ↓
Python analytical datasets
        ↓
Curated dashboard datasets
        ↓
Streamlit + Plotly dashboard
        ↓
Streamlit Community Cloud
```

## Dashboard

The deployed application contains:

- **Executive Overview** :- KPIs, value distribution, procurement method and duration
- **Buyer Analytics** :- buyer activity, value concentration and segmentation
- **Supplier Analytics** :- supplier concentration, value distribution and structure
- **Procurement Structure** :- method and supplier structure
- **Review Screening** :- transparent review population and rationale
- **Methodology & Data Quality** :- definitions, assumptions and limitations

## Technical stack

**Python 3.11 · pandas 2.2.3 · SQL · SQLite · Plotly 7.1.0 · Streamlit 1.64.0 · Git/GitHub**

### Reproducible dashboard dependencies

```text
streamlit==1.64.0
pandas==2.2.3
plotly==7.1.0
```

## Repository structure

```text
government-procurement-intelligence/
├── dashboard/
│   ├── app.py
│   └── requirements.txt
├── data/
│   ├── raw/
│   └── processed/
│       └── analysis/
│           └── dashboard/
├── docs/
│   ├── data_quality_report.txt
│   ├── lifecycle_duplicate_investigation.txt
│   └── case_study.md
├── python/
│   ├── 01_inspect_raw_data.py
│   ├── ...
│   ├── 25_consolidate_dashboard_metrics.py
│   └── 26_inspect_dashboard_outputs.py
├── sql/
│   ├── 03_procurement_analysis.sql
│   ├── 04_supplier_analysis.sql
│   ├── 05_risk_analysis.sql
│   └── 06_supplier_pri_diagnostic.sql
├── .streamlit/
│   └── config.toml
├── requirements.txt
└── README.md
```

## Data source

The project uses UK Contracts Finder data published using the Open Contracting Data Standard.

- https://www.data.gov.uk/collections/government-and-parliament/contracts-finder
- https://www.gov.uk/government/publications/open-standards-for-government/open-contracting-data-standard-profile
- https://www.gov.uk/government/publications/open-contracting

## Limitations

1. Award value is not payment data.
2. Equal allocation across multi-supplier awards is an analytical assumption.
3. Supplier identity is imperfect and some relationships require review.
4. Procurement fields contain missing values.
5. PRI scores are screening indicators, not findings of wrongdoing.
6. Long contracts are not inherently problematic.
7. Award date and release/publication date represent different lifecycle concepts.

## Why this is a strong analytics project

The project demonstrates the complete analytical workflow:

**business question → data engineering → data-quality investigation → analytical modelling → SQL/Python analysis → KPI design → interactive BI → deployment**

It demonstrates skills relevant to Data Analyst, BI Analyst, Operations Analyst, Business Analyst, Supply Chain/Logistics Analyst and Junior Data Scientist roles.

## Author

**Martin Ifeanyi Okwumuo**

Data Analyst | Operations & Logistics Analytics | Business Intelligence | Data Science

- Portfolio: https://okwumuo-martin.github.io
- GitHub: https://github.com/okwumuo-martin
- LinkedIn: https://www.linkedin.com/in/martin-okwumuo-137a3716a/
