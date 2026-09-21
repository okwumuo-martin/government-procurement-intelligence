# Government Procurement Intelligence - Portfolio Case Study

## From messy procurement records to a deployed decision-support product

**Project:** Government Procurement Intelligence: Supplier, Contract & Spend Analytics
**Tools:** Python, pandas, SQL, SQLite, Plotly, Streamlit, Git/GitHub
**Data:** UK Contracts Finder / Open Contracting Data Standard (OCDS)
**Scope:** 2025 Contracts Finder publication activity

---

## 1. Business problem

Public procurement data can contain thousands of records, but raw contracting records do not automatically answer operational questions.

The project asks:

> **How is public procurement award value distributed across buyers, suppliers and procurement structures, and where do the data indicate areas that merit further review?**

The objective was not to label organisations or suppliers as problematic. Instead, the project demonstrates how an analyst can convert complex public data into defensible metrics and a transparent review population.

---

## 2. Why the data required engineering

The source contained:

- repeated release records
- award lifecycle versions
- one-to-many supplier relationships
- inconsistent supplier naming
- missing procurement fields
- unreliable identifiers
- reference text masquerading as supplier information
- different dates representing different procurement stages

The core lesson was:

> **A professional dashboard is only as reliable as the analytical layer underneath it.**

Therefore, data-quality investigation was treated as a major project deliverable.

---

## 3. Analytical pipeline

```text
Raw Contracts Finder files
        ↓
Schema inspection
        ↓
Field profiling
        ↓
Cleaning / 2025 filtering
        ↓
Lifecycle duplicate investigation
        ↓
Award-version modelling
        ↓
Supplier relationship modelling
        ↓
Validation and reconciliation
        ↓
SQLite + SQL analysis
        ↓
Python analytics
        ↓
Curated dashboard datasets
        ↓
Streamlit dashboard
        ↓
Cloud deployment
```

---

## 4. Data-quality and modelling decisions

### Award grain

Awards were modelled at:

`award_id + release_id`

This prevents different release versions from being incorrectly counted as independent awards.

### Supplier relationships

Supplier relationships were separated from awards because an award may have multiple suppliers.

Final relationship layer:

**57,311 supplier relationship observations**

### Supplier value allocation

For supplier concentration analysis, multi-supplier award value was allocated equally across usable suppliers.

Example:

```text
£100M award
3 usable suppliers

A = £33.33M
B = £33.33M
C = £33.33M
```

This prevents the same £100M from being counted as £300M in supplier totals.

It is an analytical allocation, not a claim about actual supplier payments.

### Entity quality

Supplier IDs were not assumed to be perfect identifiers. Cases involving multiple names, missing/unreliable IDs and reference-text records were flagged rather than silently merged.

---

## 5. Scale of the final analytical layer

| Metric | Result |
|---|---:|
| Award records | **45,011** |
| Allocated award value | **£449.8B** |
| Buyer entities | **5,980** |
| Usable supplier entities | **36,746** |
| Supplier relationships | **57,311** |
| Median award value | **£94.3K** |
| Mean award value | **£10.0M** |

The large mean/median gap demonstrates the strong right-skew of procurement award values.

---

## 6. Supplier concentration

Among usable supplier relationships:

| Supplier group | Allocated value share |
|---|---:|
| Top 1% | **70.97%** |
| Top 5% | **86.79%** |
| Top 10% | **93.25%** |
| Top 25% | **98.24%** |
| Top 50% | **99.66%** |

This is a concentration measure based on published award values and the project's allocation method. It is not a measure of actual payments.

---

## 7. Buyer segmentation

Buyer analysis combined:

- procurement activity
- allocated award value

This produced four useful segments:

1. High activity / High value
2. High activity / Lower value
3. Lower activity / High value
4. Lower activity / Lower value

Key results:

- **230 high-value buyers** account for **93.25%** of allocated value.
- **24 buyers with 200+ awards** account for **35.24%** of value.
- **3,190 one-award buyers** account for **15.38%** of value.

This separates organisational activity from financial concentration.

---

## 8. Procurement-method analysis

By award count:

| Method | Share |
|---|---:|
| Selective | **49.76%** |
| Open | **18.73%** |
| Unknown | **16.72%** |
| Direct | **10.89%** |
| Limited | **3.90%** |

By allocated value:

| Method | Share |
|---|---:|
| Open | **72.04%** |
| Selective | **24.12%** |
| Unknown | **1.84%** |
| Limited | **1.24%** |
| Direct | **0.75%** |

The difference demonstrates why counts and financial magnitude need to be analysed separately.

---

## 9. Contract duration

Across records with usable contract dates:

- mean duration: **1.90 years**
- median: approximately **1 year**
- 62.3% last at least one year
- 30.5% last at least three years
- 7.6% last at least five years
- 0.48% last at least ten years

The maximum observed duration was approximately 76 years.

Duration was deliberately not treated as a standalone indicator of wrongdoing.

---

## 10. Procurement Review Indicator

A transparent rule-based Procurement Review Indicator was developed using observable characteristics:

- high award value
- long contract duration
- direct procurement
- limited procurement
- single usable supplier relationship

Final population:

- **4 Priority review records**
- **51 High review records**
- **55 High/Priority records**

The PRI is a portfolio-project screening framework.

It is **not** an official government risk score, fraud detector, corruption probability or conclusion that a procurement was improper.

---

## 11. Dashboard product

The final Streamlit dashboard converts the analytical layer into six user-facing areas.

### Executive Overview

Provides headline KPIs and high-level distributions.

### Buyer Analytics

Allows users to explore buyer activity, value, segmentation and selected screening characteristics.

### Supplier Analytics

Provides supplier concentration, supplier-value distribution and supplier structure.

### Procurement Structure

Compares procurement methods and supplier structures.

### Review Screening

Presents the review population with score components and rationale.

### Methodology & Data Quality

Makes assumptions and limitations visible to users.

---

## 12. Deployment architecture

The application uses curated dashboard CSVs rather than recomputing the entire analytical pipeline on every page load.

```text
Python / SQL
     ↓
Validated analytical layer
     ↓
Dashboard consolidation
     ↓
Curated CSV datasets
     ↓
Streamlit + Plotly
     ↓
Streamlit Community Cloud
```

This keeps the deployed application lightweight and separates data preparation from presentation.

---

## 13. Reproducibility

Pinned dashboard dependencies:

```text
streamlit==1.64.0
pandas==2.2.3
plotly==7.1.0
```

The Streamlit entrypoint is:

`dashboard/app.py`

The dependency file is:

`dashboard/requirements.txt`

The application is deployed from the GitHub `main` branch.

---

## 14. Professional skills demonstrated

### Data engineering
- multi-file ingestion
- schema profiling
- lifecycle investigation
- duplicate resolution
- analytical-grain design
- entity-quality analysis
- validation/reconciliation

### Analytics
- descriptive statistics
- concentration analysis
- segmentation
- outlier analysis
- procurement-method analysis
- contract-duration analysis
- transparent screening logic

### SQL
- relational modelling
- aggregation
- buyer/supplier analysis
- diagnostic queries
- review-population analysis

### Python
- pandas
- reusable analytical scripts
- validation
- feature creation
- dataset consolidation

### BI and deployment
- KPI design
- interactive filters
- Plotly
- Streamlit
- Git/GitHub
- cloud deployment

---

## 15. Limitations

The project deliberately documents its limitations:

1. Award value is not payment data.
2. Supplier allocation is an analytical assumption.
3. Entity resolution is imperfect.
4. Some procurement fields are missing.
5. Screening indicators do not establish wrongdoing.
6. Long duration alone is not evidence of a problem.
7. Release date and award date represent different lifecycle concepts.

---

## 16. Future improvements

Potential next steps include:

- automated ingestion of new releases
- stronger supplier entity resolution
- CPV/category analysis
- buyer-supplier network analysis
- geographic analysis
- year-over-year trends
- contract amendment monitoring
- implementation/payment analysis where available
- automated anomaly detection
- scheduled dashboard refresh

---

## 17. Project links

**Live dashboard:**
https://okwumuomartinukgovernmentprocurementanalytics.streamlit.app/

**GitHub:**
https://github.com/okwumuo-martin/government-procurement-intelligence

**Portfolio:**
https://okwumuo-martin.github.io

**LinkedIn:**
https://www.linkedin.com/in/martin-okwumuo-137a3716a/
