"""Review History page."""

from __future__ import annotations
import json
import pandas as pd
import streamlit as st
from src.memory_store import MemoryStore

st.set_page_config(page_title="Review History · FinGuard AI", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
section[data-testid="stSidebar"] { display: none; }
.stApp { background: #0f1117; }
.page-header {
    background: linear-gradient(135deg, #1a1f2e 0%, #0f1117 100%);
    border: 1px solid #2a2f3e;
    border-left: 4px solid #14b8a6;
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 24px;
}
.page-header h2 { color: #f1f5f9; font-size: 24px; margin: 0 0 4px 0; }
.page-header p  { color: #64748b; font-size: 14px; margin: 0; }
.back-link a { color: #6366f1 !important; font-size: 13px; text-decoration: none; }
.section-label { color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 6px; }
.case-detail {
    background: #1a1f2e;
    border: 1px solid #2a2f3e;
    border-radius: 12px;
    padding: 24px 28px;
    margin-top: 16px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="back-link"><a href="/" target="_self">← Back to Home</a></p>', unsafe_allow_html=True)
st.markdown("""
<div class="page-header">
  <h2>📁 Review History</h2>
  <p>Search, filter, and export all past compliance reviews.</p>
</div>
""", unsafe_allow_html=True)

memory = MemoryStore()

scol, fcol = st.columns([2, 1])
with scol:
    query = st.text_input("🔎  Search", placeholder="Search by case ID, content, or risk category…", label_visibility="collapsed")
with fcol:
    risk_filter = st.multiselect("Filter by risk", ["Low", "Medium", "High"],
        default=["Low", "Medium", "High"], label_visibility="collapsed")

df = memory.search_reviews(query)

if df.empty:
    st.markdown("""
    <div style='background:#1a1f2e;border:1px solid #2a2f3e;border-radius:12px;padding:40px;text-align:center;margin-top:16px'>
      <div style='font-size:32px;margin-bottom:10px'>📭</div>
      <div style='color:#f1f5f9;font-size:16px;font-weight:600'>No records found</div>
      <div style='color:#64748b;font-size:13px;margin-top:6px'>Submit a review to see results here.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    filtered = df[df["risk_category"].isin(risk_filter)]

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total",      len(filtered))
    s2.metric("🔴 High",    len(filtered[filtered["risk_category"] == "High"]))
    s3.metric("🟡 Medium",  len(filtered[filtered["risk_category"] == "Medium"]))
    s4.metric("🟢 Low",     len(filtered[filtered["risk_category"] == "Low"]))

    st.dataframe(
        filtered[["case_id", "risk_score", "risk_category", "final_decision", "timestamp"]],
        use_container_width=True,
    )

    dl_col, _ = st.columns([1, 3])
    with dl_col:
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️  Export CSV", csv, "finguard_review_history.csv", "text/csv")

    if not filtered.empty:
        st.markdown("<hr style='border-color:#2a2f3e;margin:20px 0'>", unsafe_allow_html=True)
        st.markdown("<div class='section-label'>Case Details</div>", unsafe_allow_html=True)
        selected = st.selectbox("Open case", filtered["case_id"].tolist(), label_visibility="collapsed")
        case = filtered[filtered["case_id"] == selected].iloc[0]

        cat = case["risk_category"]
        st.markdown("<div class='case-detail'>", unsafe_allow_html=True)
        st.markdown(f"<div style='color:#f1f5f9;font-size:17px;font-weight:700;margin-bottom:14px'>{selected}</div>", unsafe_allow_html=True)

        d1, d2, d3 = st.columns(3)
        d1.metric("Risk Score", int(case["risk_score"]))
        d2.metric("Category",   cat)
        d3.metric("Decision",   case["final_decision"])

        st.markdown("<div class='section-label' style='margin-top:14px'>Submitted Content</div>", unsafe_allow_html=True)
        st.text_area("", value=case["input_content"], height=130, disabled=True, label_visibility="collapsed")

        st.markdown("<div class='section-label' style='margin-top:10px'>Issues</div>", unsafe_allow_html=True)
        issues_data = json.loads(case["issues"]) if isinstance(case["issues"], str) else case["issues"]
        if issues_data:
            st.dataframe(pd.DataFrame(issues_data), use_container_width=True)
        else:
            st.caption("No issues logged.")

        if case["reviewer_comments"]:
            st.markdown("<div class='section-label' style='margin-top:10px'>Reviewer Comments</div>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:#cbd5e1;font-size:14px'>{case['reviewer_comments']}</p>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
