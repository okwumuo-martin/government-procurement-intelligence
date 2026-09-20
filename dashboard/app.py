from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="UK Government Procurement Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# DESIGN SYSTEM
# ============================================================

NAVY = "#0F172A"
BLUE = "#2563EB"
SKY = "#60A5FA"
TEAL = "#0F766E"
AMBER = "#D97706"
SLATE = "#64748B"
SLATE_DARK = "#334155"
BORDER = "#E2E8F0"
PAGE_BG = "#F8FAFC"
WHITE = "#FFFFFF"

PLOTLY_SEQUENCE = [BLUE, SKY, TEAL, AMBER, SLATE]


# ============================================================
# CUSTOM STYLING
# ============================================================

st.markdown(
    f"""
    <style>
        .stApp {{
            background: {PAGE_BG};
        }}

        .block-container {{
            max-width: 1500px;
            padding-top: 1.4rem;
            padding-bottom: 3rem;
        }}

        section[data-testid="stSidebar"] {{
            background: {NAVY};
        }}

        section[data-testid="stSidebar"] * {{
            color: #E2E8F0;
        }}

        section[data-testid="stSidebar"] label {{
            color: #CBD5E1 !important;
        }}

        h1 {{
            color: {NAVY};
            font-weight: 750;
            letter-spacing: -0.035em;
        }}

        h2 {{
            color: {NAVY};
            font-weight: 700;
            letter-spacing: -0.025em;
        }}

        h3 {{
            color: {NAVY};
            font-weight: 650;
        }}

        div[data-testid="metric-container"] {{
            background: {WHITE};
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 16px 18px;
            min-height: 112px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        }}

        div[data-testid="metric-container"] label {{
            color: {SLATE} !important;
            font-size: 0.82rem;
            font-weight: 600;
        }}

        div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
            color: {NAVY};
            font-size: 1.55rem;
            font-weight: 750;
        }}

        div[data-testid="stDataFrame"] {{
            border: 1px solid {BORDER};
            border-radius: 10px;
            overflow: hidden;
            background: {WHITE};
        }}

        .dashboard-hero {{
            background: linear-gradient(135deg, #FFFFFF 0%, #EFF6FF 100%);
            border: 1px solid #DBEAFE;
            border-radius: 14px;
            padding: 21px 25px;
            margin-bottom: 14px;
        }}

        .hero-title {{
            color: {NAVY};
            font-size: 1.4rem;
            font-weight: 750;
            margin-bottom: 5px;
        }}

        .hero-text {{
            color: {SLATE_DARK};
            line-height: 1.55;
            margin: 0;
        }}

        .section-note {{
            color: {SLATE};
            font-size: 0.88rem;
            line-height: 1.5;
            margin-top: -4px;
            margin-bottom: 12px;
        }}

        .insight-card {{
            background: {WHITE};
            border-left: 4px solid {BLUE};
            border-radius: 9px;
            padding: 15px 18px;
            margin: 10px 0 16px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        }}

        .insight-title {{
            color: {NAVY};
            font-weight: 700;
            margin-bottom: 5px;
        }}

        .insight-text {{
            color: {SLATE_DARK};
            line-height: 1.55;
        }}

        .filter-badge {{
            display: inline-block;
            background: #EFF6FF;
            color: #1D4ED8;
            border: 1px solid #BFDBFE;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 0.78rem;
            font-weight: 650;
            margin-bottom: 8px;
        }}

        .footer {{
            text-align: center;
            color: {SLATE};
            padding: 22px 0 4px;
            font-size: 0.82rem;
        }}

        .stDownloadButton > button {{
            border-radius: 8px;
            font-weight: 650;
            border: 1px solid #CBD5E1;
            background: #FFFFFF;
            color: {NAVY};
        }}

        hr {{
            border-color: {BORDER};
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DATA = PROJECT_ROOT / "data" / "processed" / "analysis" / "dashboard"


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_csv(filename: str) -> pd.DataFrame:
    path = DASHBOARD_DATA / filename
    if not path.exists():
        raise FileNotFoundError(f"Required dashboard data file not found: {path}")
    return pd.read_csv(path)


@st.cache_data
def load_all_data() -> dict:
    return {
        "kpis": load_csv("dashboard_kpis.csv"),
        "procurement_method": load_csv("dashboard_procurement_method.csv"),
        "value_distribution": load_csv("dashboard_value_distribution.csv"),
        "duration_distribution": load_csv("dashboard_duration_distribution.csv"),
        "supplier_concentration": load_csv("dashboard_supplier_concentration.csv"),
        "supplier_structure": load_csv("dashboard_supplier_structure.csv"),
        "supplier_summary": load_csv("dashboard_supplier_summary.csv"),
        "supplier_value_distribution": load_csv("dashboard_supplier_value_distribution.csv"),
        "buyer_overview": load_csv("dashboard_buyer_overview.csv"),
        "buyer_activity_bands": load_csv("dashboard_buyer_activity_bands.csv"),
        "buyer_segments": load_csv("dashboard_buyer_segments.csv"),
        "buyer_outliers": load_csv("dashboard_buyer_outliers.csv"),
        "buyer_procurement_method": load_csv("dashboard_buyer_procurement_method.csv"),
        "buyer_direct_limited": load_csv("dashboard_buyer_direct_limited.csv"),
        "buyer_long_duration": load_csv("dashboard_buyer_long_duration.csv"),
        "top_buyers_count": load_csv("dashboard_top_buyers_by_count.csv"),
        "top_buyers_value": load_csv("dashboard_top_buyers_by_value.csv"),
        "review_population": load_csv("dashboard_review_population.csv"),
        "buyer_data_quality": load_csv("dashboard_buyer_data_quality.csv"),
        "metric_dictionary": load_csv("dashboard_metric_dictionary.csv"),
    }


try:
    data = load_all_data()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.info(
        "Make sure the consolidated dashboard CSV files exist under "
        "data/processed/analysis/dashboard/."
    )
    st.stop()


# ============================================================
# FORMATTING HELPERS
# ============================================================

def get_kpi(metric_name: str):
    row = data["kpis"].loc[data["kpis"]["metric"] == metric_name]
    return None if row.empty else row.iloc[0]["value"]


def missing(value) -> bool:
    return value is None or pd.isna(value)


def format_number(value) -> str:
    return "N/A" if missing(value) else f"{float(value):,.0f}"


def format_percent(value, decimals: int = 1) -> str:
    return "N/A" if missing(value) else f"{float(value):.{decimals}f}%"


def format_currency(value, decimals: int = 2) -> str:
    """Compact GBP: £B, £M, £K, then £."""
    if missing(value):
        return "N/A"

    value = float(value)
    sign = "-" if value < 0 else ""
    value = abs(value)

    if value >= 1_000_000_000:
        return f"{sign}£{value / 1_000_000_000:.{decimals}f}B"
    if value >= 1_000_000:
        return f"{sign}£{value / 1_000_000:.{decimals}f}M"
    if value >= 1_000:
        return f"{sign}£{value / 1_000:.{decimals}f}K"
    return f"{sign}£{value:,.{decimals}f}"


def format_billions(value, decimals: int = 2) -> str:
    return "N/A" if missing(value) else f"£{float(value) / 1e9:.{decimals}f}B"


def rename_columns(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    return df.rename(
        columns={k: v for k, v in mapping.items() if k in df.columns}
    )


def currency_display(
    df: pd.DataFrame,
    source: str,
    target: str,
) -> pd.DataFrame:
    """Replace a numeric GBP column with a presentation-friendly text column."""
    out = df.copy()
    if source in out.columns:
        out[target] = out[source].apply(format_currency)
        out.drop(columns=[source], inplace=True)
    return out


def billion_display(
    df: pd.DataFrame,
    source: str,
    target: str,
) -> pd.DataFrame:
    """Replace a numeric GBP column with an explicit £B presentation column."""
    out = df.copy()
    if source in out.columns:
        out[target] = out[source].apply(format_billions)
        out.drop(columns=[source], inplace=True)
    return out


def add_download(
    df: pd.DataFrame,
    label: str,
    filename: str,
    key: str,
) -> None:
    st.download_button(
        label=label,
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


# ============================================================
# CHART / UI HELPERS
# ============================================================

def polish_chart(fig, height: int = 420, legend: bool = False):
    fig.update_layout(
        height=height,
        margin=dict(l=18, r=18, t=64, b=44),
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        font=dict(family="Arial, sans-serif", color=NAVY, size=12),
        title=dict(
            font=dict(size=17, color=NAVY),
            x=0,
            xanchor="left",
        ),
        showlegend=legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        xaxis=dict(
            showgrid=False,
            linecolor=BORDER,
            tickfont=dict(color=SLATE_DARK),
        ),
        yaxis=dict(
            gridcolor=BORDER,
            zeroline=False,
            tickfont=dict(color=SLATE_DARK),
        ),
        hoverlabel=dict(bgcolor=WHITE, font_color=NAVY),
    )
    return fig


def insight(title: str, text: str):
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">{title}</div>
            <div class="insight-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def footer():
    st.markdown(
        """
        <div class="footer">
            UK Government Procurement Analytics
            &nbsp;•&nbsp; Contracts Finder 2025
            &nbsp;•&nbsp; Analytical portfolio project
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown("## 📊 Procurement Analytics")
st.sidebar.caption("UK Government Contracts Finder • 2025")

st.sidebar.divider()

page = st.sidebar.radio(
    "Navigate",
    [
        "Overview",
        "Buyer Analytics",
        "Supplier Analytics",
        "Procurement Structure",
        "Review Screening",
        "Methodology & Data Quality",
    ],
)

st.sidebar.divider()
st.sidebar.markdown("**Dataset status**")
st.sidebar.success("Validated dashboard data")
st.sidebar.caption(f"{format_number(get_kpi('total_awards'))} analytical award records")
st.sidebar.caption("Source: UK Government Contracts Finder / OCDS")
st.sidebar.caption("Allocated values ≠ actual supplier payments")


# ============================================================
# HEADER
# ============================================================

st.title("UK Government Procurement Analytics")

st.markdown(
    """
    <div class="dashboard-hero">
        <div class="hero-title">Supplier, Contract & Spend Analytics</div>
        <p class="hero-text">
            An analytical examination of UK Government Contracts Finder awards
            released during 2025, focusing on procurement value, buyer activity,
            supplier concentration and contract structure.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "UK Government Contracts Finder • Open Contracting Data Standard (OCDS) • "
    "2025 analytical release dataset"
)

st.divider()


# ============================================================
# OVERVIEW
# ============================================================

if page == "Overview":

    st.header("Executive Overview")
    st.markdown(
        '<div class="section-note">Summary of the scale, structure and '
        'distribution of procurement awards in the validated 2025 analytical '
        'dataset.</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Procurement awards", format_number(get_kpi("total_awards")))
        st.caption("Analytical award records")

    with c2:
        st.metric(
            "Allocated award value",
            format_billions(get_kpi("allocated_award_value")),
        )
        st.caption("Not actual supplier payments")

    with c3:
        st.metric(
            "Median award value",
            format_currency(get_kpi("median_award_value")),
        )
        st.caption("Median award size")

    with c4:
        st.metric(
            "Buyer entities",
            format_number(get_kpi("unique_buyer_entities")),
        )
        st.caption("Entity-level buyer analysis")

    st.markdown("#### Additional indicators")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Maximum award", format_billions(get_kpi("maximum_award_value")))
        st.caption("Largest analytical award")

    with c2:
        st.metric(
            "Priority review records",
            format_number(get_kpi("priority_review_records")),
        )
        st.caption("PRI screening population")

    with c3:
        st.metric(
            "High review records",
            format_number(get_kpi("high_review_records")),
        )
        st.caption("PRI screening population")

    with c4:
        st.metric(
            "Missing supplier information",
            format_number(get_kpi("missing_supplier_information")),
        )
        st.caption("Records without usable supplier information")

    insight(
        "Executive insight",
        f"The dataset contains <strong>{format_number(get_kpi('total_awards'))}"
        f"</strong> analytical awards representing approximately "
        f"<strong>{format_billions(get_kpi('allocated_award_value'))}</strong> "
        "in allocated award value. Award volume is broad, while financial "
        "value is concentrated in a smaller number of high-value awards.",
    )

    st.divider()

    st.subheader("Procurement Method")
    st.caption(
        "The two charts show procurement methods from financial-value and "
        "award-count perspectives."
    )

    method = data["procurement_method"].copy()

    c1, c2 = st.columns(2)

    with c1:
        tmp = method.sort_values("value_share_percent", ascending=False)
        fig = px.bar(
            tmp,
            x="procurement_method_group",
            y="value_share_percent",
            text="value_share_percent",
            title="Allocated value share",
            labels={
                "procurement_method_group": "Procurement method",
                "value_share_percent": "Value share (%)",
            },
            color_discrete_sequence=[BLUE],
        )
        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
            cliponaxis=False,
        )
        st.plotly_chart(
            polish_chart(fig),
            use_container_width=True,
        )

    with c2:
        tmp = method.sort_values("award_share_percent", ascending=False)
        fig = px.bar(
            tmp,
            x="procurement_method_group",
            y="award_share_percent",
            text="award_share_percent",
            title="Award-count share",
            labels={
                "procurement_method_group": "Procurement method",
                "award_share_percent": "Award share (%)",
            },
            color_discrete_sequence=[SKY],
        )
        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
            cliponaxis=False,
        )
        st.plotly_chart(
            polish_chart(fig),
            use_container_width=True,
        )

    st.info(
        "Procurement method patterns differ between award count and allocated "
        "value. Open procurement represents a much larger share of allocated "
        "value than of award count."
    )

    st.subheader("Award Value Distribution")

    value_dist = data["value_distribution"].copy()
    value_order = [
        "<100K",
        "100K-<1M",
        "1M-<10M",
        "10M-<100M",
        "100M-<1B",
        "1B+",
        "Unknown",
    ]
    value_dist["sort_order"] = value_dist["award_value_band"].map(
        {v: i for i, v in enumerate(value_order)}
    )
    value_dist = value_dist.sort_values("sort_order")

    fig = px.bar(
        value_dist,
        x="award_value_band",
        y="value_share_percent",
        text="value_share_percent",
        title="Allocated value share by award size",
        labels={
            "award_value_band": "Award value band",
            "value_share_percent": "Value share (%)",
        },
        color_discrete_sequence=[BLUE],
    )
    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
        cliponaxis=False,
    )
    st.plotly_chart(
        polish_chart(fig, height=410),
        use_container_width=True,
    )

    st.caption(
        "Award values are allocated award values in the analytical dataset, "
        "not actual supplier payments."
    )

    st.subheader("Contract Duration")

    duration = data["duration_distribution"].copy()
    duration_order = [
        "<1 year",
        "1-<3 years",
        "3-<5 years",
        "5-<10 years",
        "10-<20 years",
        "20+ years",
    ]
    duration["sort_order"] = duration["duration_band"].map(
        {v: i for i, v in enumerate(duration_order)}
    )
    duration = duration.sort_values("sort_order")

    fig = px.bar(
        duration,
        x="duration_band",
        y="value_share_percent",
        text="value_share_percent",
        title="Allocated value share by contract duration",
        labels={
            "duration_band": "Contract duration",
            "value_share_percent": "Value share (%)",
        },
        color_discrete_sequence=[TEAL],
    )
    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
        cliponaxis=False,
    )
    st.plotly_chart(
        polish_chart(fig, height=410),
        use_container_width=True,
    )

    st.caption(
        "Longer contract duration is an analytical characteristic and does "
        "not, by itself, indicate a problematic contract."
    )


# ============================================================
# BUYER ANALYTICS
# ============================================================

elif page == "Buyer Analytics":

    st.header("Buyer Analytics")
    st.markdown(
        '<div class="section-note">Buyer analysis uses constructed buyer '
        'entity keys rather than relying solely on reported names, reducing '
        'fragmentation where one organization appears under multiple names.'
        '</div>',
        unsafe_allow_html=True,
    )

    buyers_all = data["buyer_overview"].copy()

    search = st.text_input(
        "Search buyer",
        placeholder="Type a buyer name to filter the analysis...",
    )

    buyers = buyers_all.copy()

    if search.strip():
        buyers = buyers[
            buyers["buyer_name"].str.contains(
                search.strip(),
                case=False,
                na=False,
                regex=False,
            )
        ]
        st.markdown(
            f'<div class="filter-badge">Filtered to buyers matching '
            f'“{search.strip()}”</div>',
            unsafe_allow_html=True,
        )

    if buyers.empty:
        st.warning("No buyer entities matched that search.")
    else:
        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Buyer entities", format_number(len(buyers)))
            st.caption("Matching entities" if search else "All buyer entities")

        with c2:
            st.metric("Awards", format_number(buyers["award_count"].sum()))
            st.caption("Matching awards" if search else "All analytical awards")

        with c3:
            st.metric(
                "Allocated value",
                format_currency(buyers["allocated_award_value"].sum()),
            )
            st.caption(
                "Matching allocated value" if search else "All allocated value"
            )

        st.divider()

        st.subheader("Largest Buyers by Allocated Award Value")

        top = (
            buyers.sort_values("allocated_award_value", ascending=False)
            .head(15)
            .copy()
        )
        display = top[["buyer_name", "award_count", "allocated_award_value"]].copy()
        display = billion_display(display, "allocated_award_value", "Allocated value (£B)")
        display = rename_columns(
            display,
            {"buyer_name": "Buyer", "award_count": "Awards"},
        )

        st.dataframe(display, use_container_width=True, hide_index=True, height=430)
        add_download(top, "Download buyer results", "buyer_value_results.csv", "buyer-value")

        st.subheader("Buyer Activity Bands")

        activity = data["buyer_activity_bands"].copy()
        fig = px.bar(
            activity,
            x="activity_band",
            y="buyer_count",
            text="buyer_count",
            title="Buyer entities by activity level",
            labels={
                "activity_band": "Awards per buyer",
                "buyer_count": "Buyer entities",
            },
            color_discrete_sequence=[BLUE],
        )
        fig.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside",
            cliponaxis=False,
        )
        st.plotly_chart(
            polish_chart(fig, height=410),
            use_container_width=True,
        )

        st.subheader("Buyer Activity vs Allocated Value")

        fig = px.scatter(
            buyers,
            x="award_count",
            y="allocated_award_value",
            hover_name="buyer_name",
            log_x=True,
            log_y=True,
            title="Buyer activity and allocated award value",
            labels={
                "award_count": "Number of awards",
                "allocated_award_value": "Allocated award value (£)",
            },
            color_discrete_sequence=[BLUE],
        )
        fig = polish_chart(fig, height=500)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Logarithmic axes are used because buyer activity and allocated "
            "value span several orders of magnitude."
        )

        st.subheader("Buyer Activity / Value Segmentation")

        segments = data["buyer_segments"].copy()
        segment_order = [
            "High activity/High value",
            "High activity/Lower value",
            "Lower activity/High value",
            "Lower activity/Lower value",
        ]
        segments["sort_order"] = segments["buyer_segment"].map(
            {v: i for i, v in enumerate(segment_order)}
        )
        segments = segments.sort_values("sort_order")

        fig = px.bar(
            segments,
            x="buyer_segment",
            y="allocated_value",
            text="value_share",
            title="Allocated value by buyer segment",
            labels={
                "buyer_segment": "Buyer segment",
                "allocated_value": "Allocated value (£)",
                "value_share": "Value share (%)",
            },
            color_discrete_sequence=[TEAL],
        )
        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
            cliponaxis=False,
        )
        st.plotly_chart(
            polish_chart(fig, height=450),
            use_container_width=True,
        )

        insight(
            "Buyer segmentation insight",
            "A relatively small population of high-value buyer entities "
            "accounts for a substantial share of the financial value in the "
            "dataset. Activity volume and financial scale therefore provide "
            "different views of buyer importance.",
        )

        st.subheader("Most Active Buyers")

        active = (
            buyers.sort_values(
                ["award_count", "allocated_award_value"],
                ascending=[False, False],
            )
            .head(15)
            .copy()
        )
        active_display = active[
            ["buyer_name", "award_count", "allocated_award_value"]
        ].copy()
        active_display = currency_display(
            active_display,
            "allocated_award_value",
            "Allocated value",
        )
        active_display = rename_columns(
            active_display,
            {"buyer_name": "Buyer", "award_count": "Awards"},
        )

        st.dataframe(
            active_display,
            use_container_width=True,
            hide_index=True,
            height=430,
        )
        add_download(
            active,
            "Download active buyer results",
            "most_active_buyers.csv",
            "buyer-active",
        )


# ============================================================
# SUPPLIER ANALYTICS
# ============================================================

elif page == "Supplier Analytics":

    st.header("Supplier Analytics")
    st.markdown(
        '<div class="section-note">Supplier analytics examines allocated '
        'award value among supplier entities with usable supplier relationships. '
        'Multi-supplier awards are equally allocated for this analysis.'
        '</div>',
        unsafe_allow_html=True,
    )

    suppliers_all = data["supplier_summary"].copy()

    search = st.text_input(
        "Search supplier",
        placeholder="Type a supplier name to filter the analysis...",
    )

    suppliers = suppliers_all.copy()

    if search.strip():
        suppliers = suppliers[
            suppliers["canonical_supplier_name"].str.contains(
                search.strip(),
                case=False,
                na=False,
                regex=False,
            )
        ]
        st.markdown(
            f'<div class="filter-badge">Filtered to suppliers matching '
            f'“{search.strip()}”</div>',
            unsafe_allow_html=True,
        )

    if suppliers.empty:
        st.warning("No suppliers matched that search.")
    else:
        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Usable supplier entities", format_number(len(suppliers)))
            st.caption("Matching entities" if search else "All usable suppliers")

        with c2:
            st.metric(
                "Award relationships",
                format_number(suppliers["award_count"].sum()),
            )
            st.caption(
                "Matching relationships"
                if search
                else "Supplier-award relationships"
            )

        with c3:
            st.metric(
                "Allocated supplier value",
                format_currency(suppliers["allocated_award_value"].sum()),
            )
            st.caption(
                "Matching allocated value"
                if search
                else "Allocated across usable suppliers"
            )

        st.divider()

        st.subheader("Supplier Concentration")

        concentration = data["supplier_concentration"].copy()
        concentration["top_percent"] = (
            concentration["supplier_percentile"]
            .str.extract(r"(\d+(?:\.\d+)?)")[0]
            .astype(float)
        )
        concentration = concentration.sort_values("top_percent")

        fig = px.line(
            concentration,
            x="top_percent",
            y="value_share_percent",
            markers=True,
            text="value_share_percent",
            title="Cumulative share of allocated supplier value",
            labels={
                "top_percent": "Top share of supplier entities (%)",
                "value_share_percent": "Cumulative value share (%)",
            },
            color_discrete_sequence=[BLUE],
        )
        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="top center",
            cliponaxis=False,
        )
        fig.update_xaxes(
            tickvals=concentration["top_percent"],
            ticktext=concentration["supplier_percentile"],
        )
        st.plotly_chart(
            polish_chart(fig, height=450),
            use_container_width=True,
        )

        top1 = concentration.loc[
            concentration["supplier_percentile"] == "Top 1%",
            "value_share_percent",
        ]
        if not top1.empty:
            insight(
                "Supplier concentration insight",
                f"The top 1% of usable supplier entities account for "
                f"<strong>{top1.iloc[0]:.1f}%</strong> of allocated supplier "
                "value. This measure is based on usable supplier relationships "
                "and equal allocation of multi-supplier awards.",
            )

        st.warning(
            "Supplier concentration uses usable supplier relationships only. "
            "Equal allocation across multi-supplier awards is an analytical "
            "assumption and does not represent actual supplier payments."
        )

        st.subheader("Largest Suppliers by Allocated Value")

        top = (
            suppliers.sort_values("allocated_award_value", ascending=False)
            .head(20)
            .copy()
        )
        display = top[
            [
                "canonical_supplier_name",
                "award_count",
                "buyer_count",
                "allocated_award_value",
                "supplier_rank",
            ]
        ].copy()
        display = currency_display(
            display,
            "allocated_award_value",
            "Allocated value",
        )
        display = rename_columns(
            display,
            {
                "canonical_supplier_name": "Supplier",
                "award_count": "Awards",
                "buyer_count": "Buyers",
                "supplier_rank": "Rank",
            },
        )

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            height=500,
        )
        add_download(
            top,
            "Download supplier results",
            "supplier_value_results.csv",
            "supplier-results",
        )

        st.subheader("Supplier Value Distribution")

        supplier_dist = data["supplier_value_distribution"].copy()
        supplier_order = [
            "<100K",
            "100K<1M",
            "1M<10M",
            "10M<100M",
            "100M<1B",
            "1B+",
        ]
        supplier_dist["sort_order"] = supplier_dist["value_band"].map(
            {v: i for i, v in enumerate(supplier_order)}
        )
        supplier_dist = supplier_dist.sort_values("sort_order")

        fig = px.bar(
            supplier_dist,
            x="value_band",
            y="supplier_count",
            text="supplier_count",
            title="Supplier entities by allocated value band",
            labels={
                "value_band": "Allocated value band",
                "supplier_count": "Supplier entities",
            },
            color_discrete_sequence=[TEAL],
        )
        fig.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside",
            cliponaxis=False,
        )
        st.plotly_chart(
            polish_chart(fig, height=420),
            use_container_width=True,
        )


# ============================================================
# PROCUREMENT STRUCTURE
# ============================================================

elif page == "Procurement Structure":

    st.header("Procurement Structure")
    st.markdown(
        '<div class="section-note">This section examines supplier structure, '
        'direct/limited procurement and long-duration contracts as analytical '
        'characteristics of the 2025 award dataset.</div>',
        unsafe_allow_html=True,
    )

    structure = data["supplier_structure"].copy()
    single = structure.loc[
        structure["supplier_structure"] == "Single supplier"
    ].iloc[0]
    multiple = structure.loc[
        structure["supplier_structure"] == "Multiple suppliers"
    ].iloc[0]

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Single-supplier awards", format_number(single["award_count"]))
        st.caption("Award count")

    with c2:
        st.metric(
            "Multiple-supplier awards",
            format_number(multiple["award_count"]),
        )
        st.caption("Award count")

    with c3:
        st.metric(
            "Multi-supplier value share",
            format_percent(multiple["value_share_percent"]),
        )
        st.caption("Share of allocated award value")

    st.subheader("Single vs Multiple Supplier Awards")

    c1, c2 = st.columns(2)

    with c1:
        fig = px.pie(
            structure,
            names="supplier_structure",
            values="award_count",
            title="Award count",
            hole=0.48,
            color_discrete_sequence=[BLUE, SKY],
        )
        st.plotly_chart(
            polish_chart(fig, height=400),
            use_container_width=True,
        )

    with c2:
        fig = px.pie(
            structure,
            names="supplier_structure",
            values="allocated_value",
            title="Allocated award value",
            hole=0.48,
            color_discrete_sequence=[TEAL, AMBER],
        )
        st.plotly_chart(
            polish_chart(fig, height=400),
            use_container_width=True,
        )

    st.caption(
        "Multi-supplier awards use equal allocation for supplier-value analysis."
    )

    st.subheader("Direct and Limited Procurement")

    direct = data["buyer_direct_limited"].sort_values(
        "direct_limited_value",
        ascending=False,
    ).head(20).copy()

    direct_display = direct[
        [
            "buyer_name",
            "award_count",
            "direct_limited_awards",
            "direct_limited_value",
            "direct_limited_award_share_percent",
            "direct_limited_value_share_percent",
        ]
    ].copy()
    direct_display = currency_display(
        direct_display,
        "direct_limited_value",
        "Direct/limited value",
    )
    direct_display = rename_columns(
        direct_display,
        {
            "buyer_name": "Buyer",
            "award_count": "Total awards",
            "direct_limited_awards": "Direct/limited awards",
            "direct_limited_award_share_percent": "Award share (%)",
            "direct_limited_value_share_percent": "Value share (%)",
        },
    )

    st.dataframe(
        direct_display,
        use_container_width=True,
        hide_index=True,
        height=500,
    )
    add_download(
        direct,
        "Download direct/limited table",
        "direct_limited_buyers.csv",
        "direct-limited",
    )
    st.caption(
        "Direct or limited procurement records are presented as an analytical "
        "review population, not as evidence of wrongdoing."
    )

    st.subheader("Long-Duration Contracts")

    long_duration = data["buyer_long_duration"].sort_values(
        "long_duration_value",
        ascending=False,
    ).head(20).copy()

    long_display = long_duration[
        [
            "buyer_name",
            "award_count",
            "long_duration_awards",
            "long_duration_value",
            "maximum_duration_years",
        ]
    ].copy()
    long_display = billion_display(
        long_display,
        "long_duration_value",
        "Long-duration value (£B)",
    )
    long_display = rename_columns(
        long_display,
        {
            "buyer_name": "Buyer",
            "award_count": "Total awards",
            "long_duration_awards": "Long-duration awards",
            "maximum_duration_years": "Max duration (years)",
        },
    )

    st.dataframe(
        long_display,
        use_container_width=True,
        hide_index=True,
        height=500,
        column_config={
            "Max duration (years)": st.column_config.NumberColumn(format="%.2f"),
        },
    )
    add_download(
        long_duration,
        "Download long-duration table",
        "long_duration_contracts.csv",
        "long-duration",
    )

    st.info(
        "Long contract duration is an analytical characteristic, not evidence "
        "that a contract is problematic. Longer contracts can be appropriate "
        "for services, infrastructure and other long-term arrangements."
    )


# ============================================================
# REVIEW SCREENING
# ============================================================

elif page == "Review Screening":

    st.header("Procurement Review Screening")
    st.caption(
        "Analytical screening population — not an official government risk assessment"
    )

    st.markdown(
        """
This section presents the project's **Procurement Review Indicator (PRI)**
screening population. The PRI is a user-defined analytical screening
indicator. It is **not** an official government risk score, fraud probability
or finding of wrongdoing.
"""
    )

    st.info(
        "A high PRI score does not establish fraud, corruption, misconduct or "
        "contractual failure. Records should be treated as candidates for "
        "further analytical review."
    )

    review = data["review_population"].copy()

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Priority review",
            format_number(get_kpi("priority_review_records")),
        )

    with c2:
        st.metric(
            "High review",
            format_number(get_kpi("high_review_records")),
        )

    with c3:
        st.metric(
            "High / Priority pool",
            format_number(get_kpi("high_priority_review_records")),
        )

    st.divider()

    categories = [
        c
        for c in ["Priority review", "High review"]
        if c in review["pri_category"].dropna().unique()
    ]

    selected = st.multiselect(
        "Review category",
        options=categories,
        default=categories,
    )

    filtered = review[review["pri_category"].isin(selected)].copy()

    st.markdown(
        f'<div class="filter-badge">{format_number(len(filtered))} '
        "review records selected</div>",
        unsafe_allow_html=True,
    )

    display_cols = [
        "buyer_name",
        "award_value",
        "award_date",
        "procurement_method",
        "procurement_category",
        "contract_duration_years",
        "usable_supplier_count",
        "supplier_names",
        "pri_score",
        "pri_category",
        "review_rationale",
    ]
    display_cols = [c for c in display_cols if c in filtered.columns]

    table = filtered[display_cols].sort_values(
        ["pri_score", "award_value"],
        ascending=[False, False],
    ).copy()

    table = currency_display(table, "award_value", "Award value")
    table = rename_columns(
        table,
        {
            "buyer_name": "Buyer",
            "award_date": "Award date",
            "procurement_method": "Procurement method",
            "procurement_category": "Procurement category",
            "contract_duration_years": "Contract duration (years)",
            "usable_supplier_count": "Usable suppliers",
            "supplier_names": "Supplier(s)",
            "pri_score": "PRI score",
            "pri_category": "PRI category",
            "review_rationale": "Review rationale",
        },
    )

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        height=560,
        column_config={
            "Contract duration (years)": st.column_config.NumberColumn(
                format="%.2f"
            ),
            "PRI score": st.column_config.NumberColumn(format="%d"),
        },
    )

    st.caption(
        "The review population supports analytical prioritisation only; it "
        "does not establish misconduct."
    )

    add_download(
        filtered,
        "Download selected review population",
        "procurement_review_population.csv",
        "review-population",
    )


# ============================================================
# METHODOLOGY & DATA QUALITY
# ============================================================

elif page == "Methodology & Data Quality":

    st.header("Methodology & Data Quality")

    st.subheader("Data Source")
    st.markdown(
        "The project uses UK Government **Contracts Finder** procurement data "
        "published using the **Open Contracting Data Standard (OCDS)**."
    )

    st.subheader("Analytical Period")
    st.markdown(
        "The analytical dataset is based on **2025 release dates**. Historical "
        "award dates can therefore appear within 2025 release data where they "
        "are part of the relevant release lifecycle."
    )

    st.subheader("Award Versions")
    st.markdown(
        "Awards are handled at the `award_id + release_id` version grain, "
        "with the latest relevant award version used for downstream award-level analysis."
    )

    st.subheader("Supplier Allocation")
    st.markdown(
        "Where an award has multiple usable suppliers, its award value is "
        "allocated equally across those supplier relationships for supplier "
        "concentration analysis. This prevents the full award value from being "
        "counted once for every supplier."
    )

    st.subheader("Buyer Entities")
    st.markdown(
        "Buyer analysis uses constructed buyer entity keys so organizations "
        "with multiple reported names can be analyzed at the entity level."
    )

    st.subheader("Review Screening")
    st.markdown(
        "The Procurement Review Indicator (PRI) combines selected characteristics "
        "such as award value, contract duration, procurement method and supplier "
        "structure. It is a project-defined screening measure rather than an "
        "official government risk assessment."
    )

    st.divider()

    st.subheader("Buyer Data Quality")

    quality = rename_columns(
        data["buyer_data_quality"].copy(),
        {"metric": "Metric", "count": "Count"},
    )

    st.dataframe(
        quality,
        use_container_width=True,
        hide_index=True,
        height=330,
    )

    st.divider()

    st.subheader("Key Analytical Caveats")
    st.markdown(
        """
- **Allocated award value is not actual government expenditure or supplier payments.**
- Supplier concentration is calculated only where supplier information is usable.
- Multi-supplier awards use equal allocation for analytical purposes.
- Supplier identity variation is treated as a data-quality/entity-resolution issue.
- Long contract duration does not inherently indicate a problem.
- Direct or limited procurement records are review populations, not evidence of wrongdoing.
- The PRI is a user-defined screening indicator and should not be interpreted as an official risk score.
"""
    )

    st.divider()

    st.subheader("Metric Dictionary")

    dictionary = rename_columns(
        data["metric_dictionary"].copy(),
        {
            "metric": "Metric",
            "category": "Category",
            "definition": "Definition",
            "unit": "Unit",
            "important_caveat": "Important caveat",
        },
    )

    st.dataframe(
        dictionary,
        use_container_width=True,
        hide_index=True,
        height=430,
    )

    st.divider()

    st.subheader("Project Objective")
    st.markdown(
        """
The project demonstrates an end-to-end analytics workflow using a large
public procurement dataset:

**Data acquisition → data quality investigation → normalization →
SQL analysis → analytical feature engineering → supplier/buyer analysis →
dashboard development.**
"""
    )

    st.subheader("Analytical Skills Demonstrated")

    skills = [
        "Python data engineering",
        "SQL analytical querying",
        "Data quality investigation",
        "Entity resolution",
        "Supplier concentration analysis",
        "Buyer segmentation",
        "Procurement analysis",
        "Feature engineering",
        "Interactive dashboard development",
        "Analytical communication",
    ]

    cols = st.columns(2)
    for i, skill in enumerate(skills):
        with cols[i % 2]:
            st.markdown(f"✓ {skill}")

    st.divider()

    st.subheader("Project Resources")
    st.markdown(
        """
- **Source data:** UK Government Contracts Finder
- **Code:** GitHub repository
- **Case study:** Portfolio project page
- **Dashboard:** Interactive Streamlit application
"""
    )


# ============================================================
# FOOTER
# ============================================================

footer()
