"""
Dashboard page — metrics, trends, SLA stats, engineer performance.
Only accessible to engineers and admins.
"""

import sys
from pathlib import Path

# Add project root to sys.path so "frontend" package is importable
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pandas as pd
import plotly.express as px
import streamlit as st

from frontend.components.auth import get_role, get_user, logout, require_login
from frontend import api_client

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Dashboard | Helpdesk AI", page_icon="📊", layout="wide")

# ── Auth gate ─────────────────────────────────────────────────────────────────
token = require_login()
user  = get_user()
role  = get_role()

# ── Role guard: employees don't see this page ─────────────────────────────────
if role not in ("engineer", "admin"):
    st.error("⛔ Access denied. This page is for engineers and admins only.")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### 👤 {user.get('full_name', 'User')}")
    st.markdown(f"**Role:** {role.title()}")
    st.divider()
    if st.button("🚪 Sign Out", use_container_width=True):
        logout()

# ── Page header ───────────────────────────────────────────────────────────────
st.title("📊 Dashboard")
st.caption("Real-time ITSM metrics")

# ── Load all dashboard data ───────────────────────────────────────────────────
with st.spinner("Loading dashboard data..."):
    try:
        summary    = api_client.get_dashboard_summary(token)
        trends     = api_client.get_dashboard_trends(token)
        sla_stats  = api_client.get_sla_stats(token)
        engineers  = api_client.get_engineer_stats(token)
        load_error = None
    except ValueError as e:
        load_error = str(e)

if load_error:
    st.error(f"Failed to load dashboard: {load_error}")
    st.stop()

# ── Section 1: KPI metric cards ───────────────────────────────────────────────
st.subheader("Ticket Summary")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("🟡 Open",        summary.get("open", 0))
col2.metric("🔵 In Progress", summary.get("in_progress", 0))
col3.metric("🟢 Resolved",    summary.get("resolved", 0))
col4.metric("⚫ Closed",      summary.get("closed", 0))
col5.metric("🔁 Reopened",    summary.get("reopened", 0))

avg_hours = summary.get("avg_resolution_hours")
if avg_hours is not None:
    st.info(f"⏱ Average resolution time: **{float(avg_hours):.1f} hours**")
else:
    st.info("⏱ Average resolution time: No resolved tickets yet.")

st.divider()

# ── Section 2: Monthly trend line chart ───────────────────────────────────────
st.subheader("Monthly Ticket Trends (Last 6 Months)")

if trends:
    df_trends = pd.DataFrame(trends)
    df_trends["month"] = pd.to_datetime(df_trends["month"]).dt.strftime("%b %Y")

    fig = px.line(
        df_trends,
        x="month",
        y=["created", "resolved"],
        markers=True,
        labels={"value": "Tickets", "month": "Month", "variable": "Type"},
        color_discrete_map={"created": "#636EFA", "resolved": "#00CC96"},
    )
    fig.update_layout(
        legend_title_text="",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No trend data available yet.")

st.divider()

# ── Section 3: SLA breach rate by department ──────────────────────────────────
st.subheader("SLA Breach Rate by Department")

if sla_stats:
    df_sla = pd.DataFrame(sla_stats)
    df_sla["breach_pct"] = (df_sla["breach_rate"].astype(float) * 100).round(1)

    fig2 = px.bar(
        df_sla,
        x="department",
        y="breach_pct",
        text="breach_pct",
        labels={"department": "Department", "breach_pct": "Breach Rate (%)"},
        color="breach_pct",
        color_continuous_scale=["#00CC96", "#FFA15A", "#EF553B"],
    )
    fig2.update_traces(texttemplate="%{text}%", textposition="outside")
    fig2.update_layout(
        coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No SLA data available yet.")

st.divider()

# ── Section 4: Engineer performance table ─────────────────────────────────────
st.subheader("Engineer Performance")

if engineers:
    df_eng = pd.DataFrame(engineers)
    # Make column names readable: "resolved_count" → "Resolved Count"
    df_eng.columns = [c.replace("_", " ").title() for c in df_eng.columns]
    st.dataframe(df_eng, use_container_width=True, hide_index=True)
else:
    st.info("No engineer data available yet.")
