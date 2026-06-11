"""Human Review Queue page."""

from __future__ import annotations
import json
import streamlit as st
from src.human_review import HumanReviewService, VALID_DECISIONS

st.set_page_config(page_title="Human Review · FinGuard AI", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
section[data-testid="stSidebar"] { display: none; }
.stApp { background: #0f1117; }
.page-header {
    background: linear-gradient(135deg, #1a1f2e 0%, #0f1117 100%);
    border: 1px solid #2a2f3e;
    border-left: 4px solid #f59e0b;
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 24px;
}
.page-header h2 { color: #f1f5f9; font-size: 24px; margin: 0 0 4px 0; }
.page-header p  { color: #64748b; font-size: 14px; margin: 0; }
.back-link a { color: #6366f1 !important; font-size: 13px; text-decoration: none; }
.section-label { color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 6px; }
.badge { display: inline-block; border-radius: 6px; padding: 3px 12px; font-size: 12px; font-weight: 700; letter-spacing: 0.04em; }
.badge-high   { background: rgba(239,68,68,0.15);  color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }
.badge-medium { background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }
.badge-low    { background: rgba(34,197,94,0.15);  color: #22c55e; border: 1px solid rgba(34,197,94,0.3); }
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
  <h2>🔍 Human Review Queue</h2>
  <p>High-risk cases (score ≥ 7) pending manual reviewer decision. Approve, reject, or request changes.</p>
</div>
""", unsafe_allow_html=True)

service = HumanReviewService()
queue   = service.queue()

if queue.empty:
    st.markdown("""
    <div style='background:#1a1f2e;border:1px solid #2a2f3e;border-radius:12px;padding:40px;text-align:center;'>
      <div style='font-size:36px;margin-bottom:12px'>✅</div>
      <div style='color:#f1f5f9;font-size:18px;font-weight:600'>Queue is clear</div>
      <div style='color:#64748b;font-size:14px;margin-top:6px'>No cases are pending human review.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"<div style='color:#94a3b8;font-size:13px;margin-bottom:8px'>⚠️ <b style='color:#f59e0b'>{len(queue)}</b> case(s) pending review</div>", unsafe_allow_html=True)
    st.dataframe(
        queue[["case_id", "risk_score", "risk_category", "final_decision", "timestamp"]],
        use_container_width=True,
    )

    st.markdown("<hr style='border-color:#2a2f3e;margin:20px 0'>", unsafe_allow_html=True)

    case_id = st.selectbox("Select case to review", queue["case_id"].tolist())
    case = queue[queue["case_id"] == case_id].iloc[0]
    cat = case["risk_category"]
    badge_cls = f"badge-{cat.lower()}"

    st.markdown("<div class='case-detail'>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#f1f5f9;font-size:18px;font-weight:700;margin-bottom:16px'>{case_id}</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='section-label'>Risk Score</div><div style='font-size:32px;font-weight:800;color:#ef4444'>{int(case['risk_score'])}<span style='font-size:16px;color:#64748b'>/10</span></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='section-label'>Category</div><div style='margin-top:6px'><span class='badge {badge_cls}'>{cat}</span></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-label'>Submitted Content</div>", unsafe_allow_html=True)
    st.text_area("", value=case["input_content"], height=160, disabled=True, label_visibility="collapsed")

    st.markdown("<div class='section-label' style='margin-top:12px'>Detected Issues</div>", unsafe_allow_html=True)
    issues_data = json.loads(case["issues"]) if isinstance(case["issues"], str) else case["issues"]
    if issues_data:
        st.dataframe(issues_data, use_container_width=True)
    else:
        st.caption("No issues logged.")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#2a2f3e;margin:20px 0'>", unsafe_allow_html=True)
    st.markdown("<div class='section-label'>Reviewer Decision</div>", unsafe_allow_html=True)
    dcol1, dcol2 = st.columns([1, 2])
    with dcol1:
        decision = st.selectbox("Decision", VALID_DECISIONS, label_visibility="collapsed")
    with dcol2:
        comments = st.text_input("Comments (optional)", placeholder="Add reviewer notes…", label_visibility="collapsed")

    if st.button("💾  Save Decision", type="primary"):
        service.decide(case_id, decision, comments)
        st.success(f"✅ Decision '{decision}' saved for {case_id}. Refresh to update the queue.")
