"""Analytics Dashboard page."""

from __future__ import annotations
import streamlit as st
from src.dashboard import calculate_metrics
from src.memory_store import MemoryStore

st.set_page_config(page_title="Dashboard · FinGuard AI", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
section[data-testid="stSidebar"] { display: none; }
.stApp { background: #0f1117; }
.page-header {
    background: linear-gradient(135deg, #1a1f2e 0%, #0f1117 100%);
    border: 1px solid #2a2f3e;
    border-left: 4px solid #22c55e;
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 24px;
}
.page-header h2 { color: #f1f5f9; font-size: 24px; margin: 0 0 4px 0; }
.page-header p  { color: #64748b; font-size: 14px; margin: 0; }
.back-link a { color: #6366f1 !important; font-size: 13px; text-decoration: none; }
.metric-card {
    background: #1a1f2e;
    border: 1px solid #2a2f3e;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
}
.metric-val { font-size: 36px; font-weight: 800; color: #f1f5f9; line-height: 1; margin-bottom: 6px; }
.metric-lbl { font-size: 12px; color: #64748b; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; }
.metric-val-blue   { color: #818cf8; }
.metric-val-amber  { color: #f59e0b; }
.metric-val-green  { color: #22c55e; }
.metric-val-red    { color: #ef4444; }
.metric-val-orange { color: #f97316; }
.section-label { color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin: 20px 0 8px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="back-link"><a href="/" target="_self">← Back to Home</a></p>', unsafe_allow_html=True)
st.markdown("""
<div class="page-header">
  <h2>📊 Compliance Dashboard</h2>
  <p>Aggregated metrics and trend analysis across all reviewed content.</p>
</div>
""", unsafe_allow_html=True)

df      = MemoryStore().search_reviews()
metrics = calculate_metrics(df)

c1, c2, c3, c4, c5, c6 = st.columns(6)
cards = [
    (c1, metrics["total_cases"],        "Total Cases",    "metric-val-blue"),
    (c2, metrics["pending_reviews"],    "Pending Review", "metric-val-amber"),
    (c3, metrics["average_risk_score"], "Avg Risk Score", "metric-val-orange"),
    (c4, metrics["high_risk_cases"],    "High Risk",      "metric-val-red"),
    (c5, metrics["approved_cases"],     "Approved",       "metric-val-green"),
    (c6, metrics["rejected_cases"],     "Rejected",       "metric-val-red"),
]
for col, val, label, cls in cards:
    with col:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-val {cls}">{val}</div>
          <div class="metric-lbl">{label}</div>
        </div>
        """, unsafe_allow_html=True)

if df.empty:
    st.markdown("""
    <div style='background:#1a1f2e;border:1px solid #2a2f3e;border-radius:12px;padding:40px;text-align:center;margin-top:24px'>
      <div style='font-size:32px;margin-bottom:10px'>📈</div>
      <div style='color:#f1f5f9;font-size:16px;font-weight:600'>No data yet</div>
      <div style='color:#64748b;font-size:13px;margin-top:6px'>Submit reviews to populate charts.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<hr style='border-color:#2a2f3e;margin:24px 0'>", unsafe_allow_html=True)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("<div class='section-label'>Risk Distribution</div>", unsafe_allow_html=True)
        risk_counts = df["risk_category"].value_counts().reindex(["Low", "Medium", "High"], fill_value=0)
        st.bar_chart(risk_counts, color="#6366f1")

    with chart_col2:
        st.markdown("<div class='section-label'>Decision Outcomes</div>", unsafe_allow_html=True)
        st.bar_chart(df["final_decision"].value_counts(), color="#14b8a6")

    st.markdown("<div class='section-label'>Risk Score Trend</div>", unsafe_allow_html=True)
    trend = df[["timestamp", "risk_score"]].sort_values("timestamp").set_index("timestamp")
    st.line_chart(trend, color="#f59e0b")
