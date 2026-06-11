"""Submit Review page — powered by LangGraph."""

from __future__ import annotations
import json
import uuid
import streamlit as st
from src.compliance_checker import ComplianceChecker
from src.utils import extract_text_from_upload

st.set_page_config(page_title="Submit Review · FinGuard AI", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
section[data-testid="stSidebar"] { display: none; }
.stApp { background: #0f1117; }
.page-header {
    background: linear-gradient(135deg, #1a1f2e 0%, #0f1117 100%);
    border: 1px solid #2a2f3e;
    border-left: 4px solid #6366f1;
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 24px;
}
.page-header h2 { color: #f1f5f9; font-size: 24px; margin: 0 0 4px 0; }
.page-header p  { color: #64748b; font-size: 14px; margin: 0; }
.back-link a { color: #6366f1 !important; font-size: 13px; text-decoration: none; }
.score-high   { color: #ef4444; font-size: 36px; font-weight: 800; }
.score-medium { color: #f59e0b; font-size: 36px; font-weight: 800; }
.score-low    { color: #22c55e; font-size: 36px; font-weight: 800; }
.badge { display: inline-block; border-radius: 6px; padding: 3px 12px; font-size: 12px; font-weight: 700; letter-spacing: 0.04em; }
.badge-high    { background: rgba(239,68,68,0.15);  color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }
.badge-medium  { background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }
.badge-low     { background: rgba(34,197,94,0.15);  color: #22c55e; border: 1px solid rgba(34,197,94,0.3); }
.badge-pending { background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }
.badge-approved{ background: rgba(34,197,94,0.15);  color: #22c55e; border: 1px solid rgba(34,197,94,0.3); }
.section-label { color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 6px; }
.graph-step { font-size: 11px; color: #64748b; line-height: 1.8; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="back-link"><a href="/" target="_self">← Back to Home</a></p>', unsafe_allow_html=True)
st.markdown("""
<div class="page-header">
  <h2>📋 Submit Compliance Review</h2>
  <p>Paste financial content or upload a file. Powered by LangGraph — retrieves policy context, analyses risk, auto-retries borderline scores.</p>
</div>
""", unsafe_allow_html=True)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "latest_review" not in st.session_state:
    st.session_state.latest_review = None
if "status_messages" not in st.session_state:
    st.session_state.status_messages = []

col_input, col_upload = st.columns([3, 1])
with col_input:
    text_input = st.text_area("Paste content for review", height=200,
        placeholder="Paste email, marketing copy, loan terms, product description…")
with col_upload:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Or upload a file", type=["txt", "pdf"], label_visibility="collapsed")
    st.markdown("<div style='color:#64748b;font-size:12px;margin-top:6px'>Supported: .txt · .pdf</div>", unsafe_allow_html=True)

st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
run_btn = st.button("🔍  Run Compliance Review", type="primary")

if run_btn:
    try:
        uploaded_text = extract_text_from_upload(uploaded_file) if uploaded_file else ""
        content = (uploaded_text or text_input).strip()
        if not content:
            st.error("Please paste content or upload a non-empty file.")
        else:
            with st.spinner("Running LangGraph compliance workflow…"):
                checker = ComplianceChecker(session_id=st.session_state.session_id)
                record, status_msgs = checker.run_review(content)
            st.session_state.latest_review = record.model_dump()
            st.session_state.status_messages = status_msgs
    except Exception as exc:
        st.error(f"Could not complete review: {exc}")

record = st.session_state.latest_review
if record:
    msgs = st.session_state.get("status_messages", [])
    if msgs:
        steps_html = " &nbsp;·&nbsp; ".join(msgs)
        st.markdown(f"<div class='graph-step'>{steps_html}</div>", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#2a2f3e;margin:16px 0'>", unsafe_allow_html=True)

    score    = record["risk_score"]
    cat      = record["risk_category"]
    decision = record["final_decision"]

    score_cls = "score-high" if cat == "High" else ("score-medium" if cat == "Medium" else "score-low")
    badge_cat = f"badge-{cat.lower()}"
    badge_dec = "badge-pending" if "Pending" in decision else "badge-approved"

    st.success(f"✅  Review complete — Case ID: **{record['case_id']}**")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='section-label'>Risk Score</div><div class='{score_cls}'>{score}<span style='font-size:18px;color:#64748b'>/10</span></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='section-label'>Risk Category</div><div style='margin-top:6px'><span class='badge {badge_cat}'>{cat}</span></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='section-label'>Decision</div><div style='margin-top:6px'><span class='badge {badge_dec}'>{decision}</span></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    st.markdown("<div class='section-label'>Detected Issues</div>", unsafe_allow_html=True)
    if record["issues"]:
        st.dataframe(record["issues"], use_container_width=True)
    else:
        st.markdown("<p style='color:#22c55e;font-size:13px'>✓ No issues detected.</p>", unsafe_allow_html=True)

    st.markdown("<div class='section-label' style='margin-top:14px'>Suggested Correction</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#cbd5e1;font-size:14px;line-height:1.6'>{record['suggested_corrections']}</p>", unsafe_allow_html=True)

    with st.expander("📎 Retrieved Policy References"):
        for ref in record["retrieved_policies"]:
            st.caption(ref)

    st.download_button(
        "⬇️  Export Result JSON",
        data=json.dumps(record, default=str, indent=2),
        file_name=f"{record['case_id']}.json",
        mime="application/json",
    )
