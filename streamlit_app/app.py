import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import psycopg2

load_dotenv()

SILVER_SCHEMA = os.getenv("SILVER_SCHEMA", "analytics_silver")
GOLD_SCHEMA = os.getenv("GOLD_SCHEMA", "analytics_gold")

st.set_page_config(
    page_title="MENA Digital Wallet — Risk & Fraud Monitoring",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
    /* Overall styling */
    .main {
        background-color: #fafafa;
    }
    
    /* Brand logo */
    .brand-logo {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0a2540;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    .brand-logo span {
        color: #635bff;
    }
    
    /* Typography */
    h1 {
        font-weight: 600;
        color: #0a2540;
        margin-bottom: 0.5rem;
    }
    
    h2 {
        font-weight: 600;
        color: #0a2540;
        font-size: 1.5rem;
        margin-top: 2.5rem;
        margin-bottom: 1rem;
        border-bottom: 1px solid #e3e8ee;
        padding-bottom: 0.5rem;
    }
    
    h3 {
        font-weight: 500;
        color: #425466;
        font-size: 1.1rem;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 600;
        color: #0a2540;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        font-weight: 500;
        color: #425466;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    [data-testid="metric-container"] {
        background-color: white;
        border: 1px solid #e3e8ee;
        border-radius: 8px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f6f9fc;
    }
    
    /* Dataframes */
    [data-testid="stDataFrame"] {
        border: 1px solid #e3e8ee;
        border-radius: 6px;
    }
    
    /* Reduce excessive padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Captions */
    .caption-text {
        color: #697386;
        font-size: 0.875rem;
        margin-top: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)



def format_currency(value):
    """Format value as currency with thousands separator."""
    if pd.isna(value) or value is None:
        return "$0.00"
    return f"${value:,.2f}"


def format_percentage(value, decimals=2):
    """Format value as percentage."""
    if pd.isna(value) or value is None:
        return "0.00%"
    return f"{value * 100:.{decimals}f}%"


def format_number(value):
    """Format integer with thousands separator."""
    if pd.isna(value) or value is None:
        return "0"
    return f"{int(value):,}"


def safe_get_value(df, column, default=0):
    """Safely extract value from dataframe."""
    if len(df) == 0 or column not in df.columns:
        return default
    val = df[column].iloc[0]
    return val if not pd.isna(val) else default


# ─────────────────────────────────────────────────────────────────────
# Database Connection
# ─────────────────────────────────────────────────────────────────────

def get_connection():
    return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
        dbname=os.getenv("PG_DB", "mena_payments"),
        user=os.getenv("PG_USER", "mena"),
        password=os.getenv("PG_PASSWORD", "mena"),
    )



@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
        dbname=os.getenv("PG_DB", "mena_payments"),
        user=os.getenv("PG_USER", "mena"),
        password=os.getenv("PG_PASSWORD", "mena"),
    )


conn = get_connection()



countries_q = f"""
SELECT DISTINCT country
FROM {GOLD_SCHEMA}.dim_user
ORDER BY 1;
"""

date_bounds_q = f"""
SELECT MIN(attempt_ts)::date AS min_date, MAX(attempt_ts)::date AS max_date
FROM {GOLD_SCHEMA}.fact_payment_attempts;
"""

countries = pd.read_sql(countries_q, conn)["country"].tolist()
bounds = pd.read_sql(date_bounds_q, conn).iloc[0]

#
st.sidebar.markdown(
    '<div class="brand-logo"><span>Falcon</span>Risk</div>',
    unsafe_allow_html=True
)
st.sidebar.markdown("---")

st.sidebar.header("Filters")

country = st.sidebar.selectbox(
    "Customer Country",
    ["ALL"] + countries,
    help="Filter transactions by customer's country of origin"
)
st.sidebar.caption("Select a specific country or view all regions")

date_range = st.sidebar.date_input(
    "Date Range",
    (bounds["min_date"], bounds["max_date"]),
    key="date_filter"
)
st.sidebar.caption("Historical data range for analysis")

band = st.sidebar.multiselect(
    "Risk Categories",
    ["low", "medium", "high"],
    default=["low", "medium", "high"]
)
st.sidebar.caption("Include transactions by risk classification")

alert_window_mins = st.sidebar.selectbox(
    "Monitoring Window",
    [15, 60, 240],
    index=1,
    key="alert_window_mins"
)
st.sidebar.caption("Real-time alert lookback period (minutes)")


# Build WHERE clause and params
where = "WHERE 1=1"
params = []

if country != "ALL":
    where += " AND u.country = %s"
    params.append(country)

# Normalize date input
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

where += " AND f.attempt_ts::date BETWEEN %s AND %s"
params.extend([start_date, end_date])




kpi_query = f"""
SELECT
  COUNT(*) AS total_txns,
  SUM(f.amount) AS total_volume,
  AVG(CASE WHEN f.status='approved' THEN 1 ELSE 0 END) AS approval_rate
FROM {GOLD_SCHEMA}.fact_payment_attempts f
JOIN {GOLD_SCHEMA}.dim_user u ON u.user_id = f.user_id
{where};
"""

fraud_query = f"""
SELECT
  COUNT(DISTINCT CASE WHEN s.risk_band='high' THEN f.attempt_id END)::float
  / NULLIF(COUNT(DISTINCT f.attempt_id), 0) AS fraud_rate
FROM {GOLD_SCHEMA}.fact_payment_attempts f
JOIN {GOLD_SCHEMA}.dim_user u ON u.user_id = f.user_id
LEFT JOIN {GOLD_SCHEMA}.risk_scores s ON s.attempt_id = f.attempt_id
{where};
"""

risk_dist_query = f"""
SELECT
  s.risk_band,
  COUNT(*) AS cnt
FROM {GOLD_SCHEMA}.risk_scores s
JOIN {GOLD_SCHEMA}.fact_payment_attempts f
  ON f.attempt_id = s.attempt_id
JOIN {GOLD_SCHEMA}.dim_user u
  ON u.user_id = f.user_id
{where}
  AND s.risk_band = ANY(%s)
GROUP BY s.risk_band
ORDER BY s.risk_band;
"""

daily_q = f"""
SELECT
  f.attempt_ts::date AS day,
  COUNT(*) AS txns,
  SUM(f.amount) AS gmv,
  AVG(CASE WHEN f.status='approved' THEN 1 ELSE 0 END) AS approval_rate
FROM {GOLD_SCHEMA}.fact_payment_attempts f
JOIN {GOLD_SCHEMA}.dim_user u ON u.user_id = f.user_id
{where}
GROUP BY 1
ORDER BY 1;
"""

high_risk_query = f"""
SELECT
  s.attempt_id,
  s.user_id,
  s.risk_score,
  s.risk_band,
  e.triggered_rules
FROM {GOLD_SCHEMA}.risk_scores s
LEFT JOIN {GOLD_SCHEMA}.risk_explanations e ON e.attempt_id = s.attempt_id
JOIN {GOLD_SCHEMA}.fact_payment_attempts f ON f.attempt_id = s.attempt_id
JOIN {GOLD_SCHEMA}.dim_user u ON u.user_id = f.user_id
{where}
  AND s.risk_band = 'high'
ORDER BY s.risk_score DESC
LIMIT 50;
"""

top_users_q = f"""
SELECT
  s.user_id,
  s.risk_band,
  COUNT(*) AS flagged
FROM {GOLD_SCHEMA}.risk_scores s
JOIN {GOLD_SCHEMA}.fact_payment_attempts f
  ON f.attempt_id = s.attempt_id
JOIN {GOLD_SCHEMA}.dim_user u
  ON u.user_id = f.user_id
{where}
  AND s.risk_band = ANY(%s)
GROUP BY 1,2
ORDER BY flagged DESC
LIMIT 10;
"""

risk_trend_q = f"""
SELECT
  f.attempt_ts::date AS day,
  s.risk_band,
  COUNT(*) AS flagged
FROM {GOLD_SCHEMA}.risk_scores s
JOIN {GOLD_SCHEMA}.fact_payment_attempts f
  ON f.attempt_id = s.attempt_id
JOIN {GOLD_SCHEMA}.dim_user u
  ON u.user_id = f.user_id
{where}
GROUP BY 1,2
ORDER BY 1,2;
"""

country_risk_q = f"""
SELECT
  u.country,
  COUNT(*) FILTER (WHERE s.risk_band='high')::float
  / COUNT(*) AS high_risk_ratio
FROM {GOLD_SCHEMA}.fact_payment_attempts f
JOIN {GOLD_SCHEMA}.dim_user u ON u.user_id = f.user_id
LEFT JOIN {GOLD_SCHEMA}.risk_scores s ON s.attempt_id = f.attempt_id
{where}
GROUP BY 1
ORDER BY high_risk_ratio DESC;
"""

live_high_risk_count_q = f"""
SELECT
  COUNT(*) AS high_risk_last_window
FROM {GOLD_SCHEMA}.fact_payment_attempts f
JOIN {GOLD_SCHEMA}.risk_scores s
  ON s.attempt_id = f.attempt_id
JOIN {GOLD_SCHEMA}.dim_user u
  ON u.user_id = f.user_id
{where}
  AND s.risk_band = 'high'
  AND f.attempt_ts >= NOW() - (%s || ' minutes')::interval;
"""

live_top_users_q = f"""
SELECT
  s.user_id,
  COUNT(*) AS high_risk_cnt
FROM {GOLD_SCHEMA}.fact_payment_attempts f
JOIN {GOLD_SCHEMA}.risk_scores s
  ON s.attempt_id = f.attempt_id
JOIN {GOLD_SCHEMA}.dim_user u
  ON u.user_id = f.user_id
{where}
  AND s.risk_band = 'high'
  AND f.attempt_ts >= NOW() - (%s || ' minutes')::interval
GROUP BY 1
ORDER BY 2 DESC
LIMIT 5;
"""

live_top_merchants_q = f"""
SELECT
  f.merchant_id,
  COUNT(*) AS high_risk_cnt
FROM {GOLD_SCHEMA}.fact_payment_attempts f
JOIN {GOLD_SCHEMA}.risk_scores s
  ON s.attempt_id = f.attempt_id
JOIN {GOLD_SCHEMA}.dim_user u
  ON u.user_id = f.user_id
{where}
  AND s.risk_band = 'high'
  AND f.attempt_ts >= NOW() - (%s || ' minutes')::interval
GROUP BY 1
ORDER BY 2 DESC
LIMIT 5;
"""




kpi_query = f"""
SELECT
  COUNT(*) AS total_txns,
  SUM(f.amount) AS total_volume,
  AVG(CASE WHEN f.status='approved' THEN 1 ELSE 0 END) AS approval_rate
FROM {GOLD_SCHEMA}.fact_payment_attempts f
JOIN {GOLD_SCHEMA}.dim_user u ON u.user_id = f.user_id
{where};
"""

fraud_query = f"""
SELECT
  COUNT(DISTINCT CASE WHEN s.risk_band='high' THEN f.attempt_id END)::float
  / NULLIF(COUNT(DISTINCT f.attempt_id), 0) AS fraud_rate
FROM {GOLD_SCHEMA}.fact_payment_attempts f
JOIN {GOLD_SCHEMA}.dim_user u ON u.user_id = f.user_id
LEFT JOIN {GOLD_SCHEMA}.risk_scores s ON s.attempt_id = f.attempt_id
{where};
"""

risk_dist_query = f"""
SELECT
  s.risk_band,
  COUNT(*) AS cnt
FROM {GOLD_SCHEMA}.risk_scores s
JOIN {GOLD_SCHEMA}.fact_payment_attempts f
  ON f.attempt_id = s.attempt_id
JOIN {GOLD_SCHEMA}.dim_user u
  ON u.user_id = f.user_id
{where}
  AND s.risk_band = ANY(%s)
GROUP BY s.risk_band
ORDER BY s.risk_band;
"""

daily_q = f"""
SELECT
  f.attempt_ts::date AS day,
  COUNT(*) AS txns,
  SUM(f.amount) AS gmv,
  AVG(CASE WHEN f.status='approved' THEN 1 ELSE 0 END) AS approval_rate
FROM {GOLD_SCHEMA}.fact_payment_attempts f
JOIN {GOLD_SCHEMA}.dim_user u ON u.user_id = f.user_id
{where}
GROUP BY 1
ORDER BY 1;
"""

high_risk_query = f"""
SELECT
  s.attempt_id,
  s.user_id,
  s.risk_score,
  s.risk_band,
  e.triggered_rules
FROM {GOLD_SCHEMA}.risk_scores s
LEFT JOIN {GOLD_SCHEMA}.risk_explanations e ON e.attempt_id = s.attempt_id
JOIN {GOLD_SCHEMA}.fact_payment_attempts f ON f.attempt_id = s.attempt_id
JOIN {GOLD_SCHEMA}.dim_user u ON u.user_id = f.user_id
{where}
  AND s.risk_band = 'high'
ORDER BY s.risk_score DESC
LIMIT 50;
"""

top_users_q = f"""
SELECT
  s.user_id,
  s.risk_band,
  COUNT(*) AS flagged
FROM {GOLD_SCHEMA}.risk_scores s
JOIN {GOLD_SCHEMA}.fact_payment_attempts f
  ON f.attempt_id = s.attempt_id
JOIN {GOLD_SCHEMA}.dim_user u
  ON u.user_id = f.user_id
{where}
  AND s.risk_band = ANY(%s)
GROUP BY 1,2
ORDER BY flagged DESC
LIMIT 10;
"""

risk_trend_q = f"""
SELECT
  f.attempt_ts::date AS day,
  s.risk_band,
  COUNT(*) AS flagged
FROM {GOLD_SCHEMA}.risk_scores s
JOIN {GOLD_SCHEMA}.fact_payment_attempts f
  ON f.attempt_id = s.attempt_id
JOIN {GOLD_SCHEMA}.dim_user u
  ON u.user_id = f.user_id
{where}
GROUP BY 1,2
ORDER BY 1,2;
"""

country_risk_q = f"""
SELECT
  u.country,
  COUNT(*) FILTER (WHERE s.risk_band='high')::float
  / COUNT(*) AS high_risk_ratio
FROM {GOLD_SCHEMA}.fact_payment_attempts f
JOIN {GOLD_SCHEMA}.dim_user u ON u.user_id = f.user_id
LEFT JOIN {GOLD_SCHEMA}.risk_scores s ON s.attempt_id = f.attempt_id
{where}
GROUP BY 1
ORDER BY high_risk_ratio DESC;
"""

live_high_risk_count_q = f"""
SELECT
  COUNT(*) AS high_risk_last_window
FROM {GOLD_SCHEMA}.fact_payment_attempts f
JOIN {GOLD_SCHEMA}.risk_scores s
  ON s.attempt_id = f.attempt_id
JOIN {GOLD_SCHEMA}.dim_user u
  ON u.user_id = f.user_id
{where}
  AND s.risk_band = 'high'
  AND f.attempt_ts >= NOW() - (%s || ' minutes')::interval;
"""

live_top_users_q = f"""
SELECT
  s.user_id,
  COUNT(*) AS high_risk_cnt
FROM {GOLD_SCHEMA}.fact_payment_attempts f
JOIN {GOLD_SCHEMA}.risk_scores s
  ON s.attempt_id = f.attempt_id
JOIN {GOLD_SCHEMA}.dim_user u
  ON u.user_id = f.user_id
{where}
  AND s.risk_band = 'high'
  AND f.attempt_ts >= NOW() - (%s || ' minutes')::interval
GROUP BY 1
ORDER BY 2 DESC
LIMIT 5;
"""

live_top_merchants_q = f"""
SELECT
  f.merchant_id,
  COUNT(*) AS high_risk_cnt
FROM {GOLD_SCHEMA}.fact_payment_attempts f
JOIN {GOLD_SCHEMA}.risk_scores s
  ON s.attempt_id = f.attempt_id
JOIN {GOLD_SCHEMA}.dim_user u
  ON u.user_id = f.user_id
{where}
  AND s.risk_band = 'high'
  AND f.attempt_ts >= NOW() - (%s || ' minutes')::interval
GROUP BY 1
ORDER BY 2 DESC
LIMIT 5;
"""




kpis = pd.read_sql(kpi_query, conn, params=params)
fraud = pd.read_sql(fraud_query, conn, params=params)
risk_dist = pd.read_sql(risk_dist_query, conn, params=params + [band])
daily = pd.read_sql(daily_q, conn, params=params)
high_risk = pd.read_sql(high_risk_query, conn, params=params)
top_users = pd.read_sql(top_users_q, conn, params=params + [band])
risk_trend = pd.read_sql(risk_trend_q, conn, params=params)
country_risk = pd.read_sql(country_risk_q, conn, params=params)
live_high_risk = pd.read_sql(
    live_high_risk_count_q, conn, params=params + [alert_window_mins]
)
live_top_users = pd.read_sql(
    live_top_users_q, conn, params=params + [alert_window_mins]
)
live_top_merchants = pd.read_sql(
    live_top_merchants_q, conn, params=params + [alert_window_mins]
)




st.title("MENA Digital Wallet — Risk & Fraud Monitoring")
st.markdown(
    '<p style="font-size: 1.1rem; color: #697386; margin-bottom: 2rem;">'
    'Executive overview of transaction volume, approvals, and fraud exposure with drill-down for investigation.'
    '</p>',
    unsafe_allow_html=True
)


st.markdown("## Overview")

col1, col2, col3, col4 = st.columns(4)

total_txns = safe_get_value(kpis, "total_txns", 0)
total_volume = safe_get_value(kpis, "total_volume", 0.0)
approval_rate = safe_get_value(kpis, "approval_rate", 0.0)
fraud_rate = safe_get_value(fraud, "fraud_rate", 0.0)

with col1:
    st.metric("Total Transactions", format_number(total_txns))
    st.markdown('<p class="caption-text">All payment attempts in selected period</p>', unsafe_allow_html=True)

with col2:
    st.metric("Total Payment Volume", format_currency(total_volume))
    st.markdown('<p class="caption-text">Aggregate transaction value</p>', unsafe_allow_html=True)

with col3:
    st.metric("Approval Rate", format_percentage(approval_rate))
    st.markdown('<p class="caption-text">Successfully approved transactions</p>', unsafe_allow_html=True)

with col4:
    st.metric("High-Risk Transaction Ratio", format_percentage(fraud_rate))
    st.markdown('<p class="caption-text">Transactions flagged as high risk</p>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# Real-Time Monitoring
# ─────────────────────────────────────────────────────────────────────

st.markdown("## Real-Time Monitoring")

high_risk_last_window = safe_get_value(live_high_risk, "high_risk_last_window", 0)

col_alert, col_users, col_merchants = st.columns([1, 1.5, 1.5])

with col_alert:
    st.metric(
        f"High-Risk Transactions (Last {alert_window_mins} Minutes)",
        format_number(high_risk_last_window)
    )
    st.markdown('<p class="caption-text">Real-time flagged activity</p>', unsafe_allow_html=True)

with col_users:
    st.markdown("### Customers with Highest Risk Activity")
    if len(live_top_users) == 0:
        st.info("No high-risk customer activity in this window")
    else:
        display_users = live_top_users.rename(columns={
            "user_id": "Customer ID",
            "high_risk_cnt": "High-Risk Transactions"
        })
        st.dataframe(display_users, use_container_width=True, hide_index=True)

with col_merchants:
    st.markdown("### Merchants with Highest Risk Exposure")
    if len(live_top_merchants) == 0:
        st.info("No high-risk merchant activity in this window")
    else:
        display_merchants = live_top_merchants.rename(columns={
            "merchant_id": "Merchant ID",
            "high_risk_cnt": "High-Risk Transactions"
        })
        st.dataframe(display_merchants, use_container_width=True, hide_index=True)




st.markdown("## Risk Classification Distribution")

if len(risk_dist) == 0:
    st.info("No risk scores found for the selected filters")
else:
    # Order by risk level for better visualization
    risk_order = {"low": 0, "medium": 1, "high": 2}
    risk_dist_sorted = risk_dist.copy()
    risk_dist_sorted["order"] = risk_dist_sorted["risk_band"].map(risk_order)
    risk_dist_sorted = risk_dist_sorted.sort_values("order")
    
    # Rename for display
    risk_dist_display = risk_dist_sorted.rename(columns={
        "risk_band": "Risk Category",
        "cnt": "Transaction Count"
    })
    
    st.bar_chart(risk_dist_display.set_index("Risk Category")["Transaction Count"])
    st.caption("Distribution of transactions across risk categories (Low, Medium, High)")



st.markdown("## Daily Trends")

if len(daily) == 0:
    st.info("No transaction data available for the selected date range")
else:
    daily_display = daily.set_index("day")
    
    col_trend1, col_trend2 = st.columns(2)
    
    with col_trend1:
        st.markdown("### Transactions & Payment Volume")
        # Rename columns for display
        trend_vol = daily_display[["txns", "gmv"]].rename(columns={
            "txns": "Transactions",
            "gmv": "Payment Volume ($)"
        })
        st.line_chart(trend_vol)
    
    with col_trend2:
        st.markdown("### Approval Rate")
        trend_approval = daily_display[["approval_rate"]].rename(columns={
            "approval_rate": "Approval Rate"
        })
        st.line_chart(trend_approval)

# Risk trend by category
if len(risk_trend) > 0:
    st.markdown("### Risk Activity by Category")
    pivot = risk_trend.pivot(index="day", columns="risk_band", values="flagged").fillna(0)
    pivot.columns = [col.capitalize() for col in pivot.columns]
    st.line_chart(pivot)
    st.caption("Daily breakdown of flagged transactions by risk category")


# ─────────────────────────────────────────────────────────────────────
# Investigation
# ─────────────────────────────────────────────────────────────────────

st.markdown("## Investigation")

st.markdown("### High-Risk Transactions (Explainable)")

if len(high_risk) == 0:
    st.info("No high-risk transactions found for the selected filters")
else:
    high_risk_display = high_risk.rename(columns={
        "attempt_id": "Transaction ID",
        "user_id": "Customer ID",
        "risk_score": "Risk Score",
        "risk_band": "Risk Category",
        "triggered_rules": "Triggered Signals"
    })
    st.dataframe(high_risk_display, use_container_width=True, hide_index=True)

# Drill-down section
st.markdown("### Transaction Details Drill-Down")

ids = high_risk["attempt_id"].tolist() if len(high_risk) > 0 else []
selected = st.selectbox(
    "Select a Transaction ID to investigate",
    ["— Select —"] + ids,
    help="View detailed information and triggered risk signals"
)

if selected and selected != "— Select —":
    tx_q = f"""
    SELECT *
    FROM {GOLD_SCHEMA}.fact_payment_attempts
    WHERE attempt_id = %s;
    """
    rules_q = f"""
    SELECT rule_name, txn_count_10min
    FROM {GOLD_SCHEMA}.risk_signals
    WHERE attempt_id = %s;
    """

    tx = pd.read_sql(tx_q, conn, params=[selected])
    rules = pd.read_sql(rules_q, conn, params=[selected])

    c1, c2 = st.columns([1.5, 1])
    
    with c1:
        st.markdown("#### Transaction Details")
        if len(tx) > 0:
            # Rename columns for better readability
            tx_display = tx.rename(columns={
                "attempt_id": "Transaction ID",
                "user_id": "Customer ID",
                "merchant_id": "Merchant ID",
                "amount": "Amount",
                "status": "Status",
                "attempt_ts": "Timestamp"
            })
            st.dataframe(tx_display, use_container_width=True, hide_index=True)
        else:
            st.warning("Transaction details not found")
    
    with c2:
        st.markdown("#### Triggered Signals")
        if len(rules) > 0:
            rules_display = rules.rename(columns={
                "rule_name": "Signal Name",
                "txn_count_10min": "Activity Count (10min)"
            })
            st.dataframe(rules_display, use_container_width=True, hide_index=True)
        else:
            st.info("No signals triggered for this transaction")


# ─────────────────────────────────────────────────────────────────────
# Additional Analytics
# ─────────────────────────────────────────────────────────────────────

st.markdown("## Risk Analytics by Region")

if len(country_risk) > 0:
    country_risk_display = country_risk.rename(columns={
        "country": "Country",
        "high_risk_ratio": "High-Risk Ratio"
    })
    st.bar_chart(country_risk_display.set_index("Country"))
    st.caption("Percentage of high-risk transactions by customer country")
else:
    st.info("No regional risk data available for selected filters")
