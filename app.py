"""FinGuard AI - Home page with navigation cards."""

from __future__ import annotations
import streamlit as st
from config import settings
from src.memory_store import MemoryStore

st.set_page_config(page_title="FinGuard AI", page_icon="🛡️", layout="wide")

MemoryStore()

st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
section[data-testid="stSidebar"] { display: none; }
.stApp { background: #0f1117; }
.hero-wrap {
    background: linear-gradient(135deg, #1a1f2e 0%, #0f1117 60%, #1a1f2e 100%);
    border: 1px solid #2a2f3e;
    border-radius: 16px;
    padding: 48px 40px 36px 40px;
    margin-bottom: 12px;
    position: relative;
    overflow: hidden;
}
.hero-wrap::before {
    content: "";
    position: absolute;
    top: -60px; right: -60px;
    width: 260px; height: 260px;
    background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-badge {
    display: inline-block;
    background: rgba(99,102,241,0.15);
    color: #818cf8;
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
    margin-bottom: 16px;
}
.hero-title {
    font-size: 42px;
    font-weight: 800;
    color: #f1f5f9;
    margin: 0 0 10px 0;
    line-height: 1.1;
    letter-spacing: -0.02em;
}
.hero-title span { color: #818cf8; }
.hero-sub {
    font-size: 16px;
    color: #94a3b8;
    margin: 0;
    max-width: 560px;
    line-height: 1.6;
}
.sys-info {
    position: absolute;
    top: 20px; right: 28px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 11px;
    color: #64748b;
    line-height: 1.7;
    text-align: right;
}
.sys-info b { color: #94a3b8; font-weight: 600; }
.nav-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    margin-top: 8px;
}
.nav-card {
    background: #1a1f2e;
    border: 1px solid #2a2f3e;
    border-radius: 14px;
    padding: 28px 28px 24px 28px;
    cursor: pointer;
    transition: all 0.2s ease;
    text-decoration: none;
    display: block;
    position: relative;
    overflow: hidden;
}
.nav-card::after {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.03) 0%, transparent 60%);
    border-radius: 14px;
}
.nav-card:hover {
    border-color: #4f46e5;
    background: #1e2338;
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(79,70,229,0.18);
}
.card-icon { font-size: 28px; margin-bottom: 14px; display: block; }
.card-title { font-size: 18px; font-weight: 700; color: #f1f5f9; margin: 0 0 6px 0; }
.card-desc { font-size: 13px; color: #64748b; margin: 0 0 16px 0; line-height: 1.5; }
.card-arrow { font-size: 12px; color: #4f46e5; font-weight: 600; letter-spacing: 0.03em; }
.card-blue  { border-top: 3px solid #6366f1; }
.card-amber { border-top: 3px solid #f59e0b; }
.card-teal  { border-top: 3px solid #14b8a6; }
.card-green { border-top: 3px solid #22c55e; }
.stAlert { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

sys_info = f"""
<b>LLM</b> {settings.openai_model}<br>
<b>Embeddings</b> {settings.embedding_model[:22]}…<br>
<b>Review threshold</b> Risk ≥ 7
"""

st.markdown(f"""
<div class="hero-wrap">
  <div class="sys-info">{sys_info}</div>
  <div class="hero-badge">🛡️ COMPLIANCE PLATFORM</div>
  <h1 class="hero-title">FinGuard <span>AI</span></h1>
  <p class="hero-sub">
    Analyze financial communications, retrieve relevant policy guidance,
    score compliance risk, and route high-risk cases for human approval.
  </p>
</div>
""", unsafe_allow_html=True)

if not settings.openai_api_key:
    st.warning("⚠️  OPENAI_API_KEY is not configured. Running with local rule-based fallback and keyword embeddings.")

st.markdown("""
<div class="nav-grid">

  <a class="nav-card card-blue" href="/Submit_Review" target="_self">
    <span class="card-icon">📋</span>
    <div class="card-title">Submit Review</div>
    <div class="card-desc">Paste or upload financial content. Powered by LangGraph — retrieves policy context, analyses risk, auto-retries borderline scores.</div>
    <div class="card-arrow">Start analysis →</div>
  </a>

  <a class="nav-card card-amber" href="/Human_Review" target="_self">
    <span class="card-icon">🔍</span>
    <div class="card-title">Human Review</div>
    <div class="card-desc">Review high-risk cases (score ≥ 7) flagged for manual approval. Approve, reject, or request changes with reviewer comments.</div>
    <div class="card-arrow">Open queue →</div>
  </a>

  <a class="nav-card card-teal" href="/Review_History" target="_self">
    <span class="card-icon">📁</span>
    <div class="card-title">Review History</div>
    <div class="card-desc">Search and filter all past compliance reviews. View detailed case records and export results as CSV.</div>
    <div class="card-arrow">Browse records →</div>
  </a>

  <a class="nav-card card-green" href="/Dashboard" target="_self">
    <span class="card-icon">📊</span>
    <div class="card-title">Dashboard</div>
    <div class="card-desc">Track compliance metrics — risk distribution, decision outcomes, and risk score trends across all reviewed content.</div>
    <div class="card-arrow">View analytics →</div>
  </a>

</div>
""", unsafe_allow_html=True)
