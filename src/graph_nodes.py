"""LangGraph node functions for the compliance review workflow."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import settings
from src.graph_state import ComplianceState
from src.rag_engine import RAGEngine
from src.schemas import (
    ComplianceAnalysis,
    ComplianceIssue,
    risk_category_from_score,
    status_from_score,
)
from src.utils import logger, parse_json_object

# ── Shared instances (lazy init) ──────────────────────────────────────────────
_rag_engine: RAGEngine | None = None
_llm: ChatOpenAI | None = None


def _get_rag() -> RAGEngine:
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine


def _get_llm() -> ChatOpenAI | None:
    global _llm
    if _llm is None and settings.openai_api_key:
        _llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.1,
        )
    return _llm


SYSTEM_PROMPT = """
You are FinGuard AI, a compliance review assistant for fintech and banking.
Analyze the submitted content against the policy context provided.
Return ONLY valid JSON — no preamble, no markdown fences.
Be conservative: flag guaranteed returns, missing risk warnings, misleading claims,
restricted investment advice, missing disclosures, privacy/KYC issues, and aggressive tone.
"""

ANALYSIS_SCHEMA = """{
  "risk_score": 8,
  "risk_category": "High",
  "issues_found": [
    {
      "issue": "Missing risk warning",
      "reason": "The content discusses returns without describing investment risk.",
      "policy_reference": "marketing_guidelines.txt",
      "suggested_correction": "Add a clear risk warning near the claim."
    }
  ],
  "policy_violations": ["Missing risk warning"],
  "missing_disclosures": ["Risk disclosure"],
  "explanation": "Explanation here.",
  "suggested_correction": "Overall correction guidance.",
  "final_status": "Pending Human Review"
}"""


# ── Node 1: Retrieve policies ─────────────────────────────────────────────────
def node_retrieve_policies(state: ComplianceState) -> ComplianceState:
    """RAG node — retrieve relevant policy chunks for the content."""
    logger.info("[Graph] node_retrieve_policies | case=%s", state["case_id"])
    rag = _get_rag()
    policy_context, references = rag.retrieve_text(state["content"])
    return {
        **state,
        "policy_context": policy_context,
        "retrieved_references": references,
        "status_messages": state.get("status_messages", []) + ["📚 Policy context retrieved"],
    }


# ── Node 2: Analyse compliance ────────────────────────────────────────────────
def node_analyse_compliance(state: ComplianceState) -> ComplianceState:
    """LLM node — run compliance analysis using policy context."""
    logger.info(
        "[Graph] node_analyse_compliance | case=%s | retry=%d | correction=%d",
        state["case_id"], state.get("retry_count", 0), state.get("correction_count", 0),
    )

    llm = _get_llm()
    content = state["content"]
    policy_context = state["policy_context"]
    msgs = state.get("status_messages", [])

    if state.get("retry_count", 0) > 0:
        msgs = msgs + [f"🔄 Re-analysing (borderline score, attempt {state['retry_count'] + 1}/3)…"]
    if state.get("correction_count", 0) > 0:
        msgs = msgs + [f"🔁 Self-correcting output (attempt {state['correction_count'] + 1}/3)…"]

    if not llm:
        analysis = _heuristic_analysis(content, policy_context)
        return {**state, "analysis": analysis, "status_messages": msgs + ["⚙️ Heuristic fallback used"]}

    prompt = f"""Policy context:
{policy_context}

Content to review:
{content}

Required JSON schema:
{ANALYSIS_SCHEMA}"""

    try:
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        raw = str(response.content)
        data = parse_json_object(raw)
        score = int(data.get("risk_score", 0))
        data["risk_category"] = risk_category_from_score(score)
        data["final_status"]  = status_from_score(score)
        analysis = ComplianceAnalysis.model_validate(data)
        return {
            **state,
            "analysis": analysis,
            "last_error": "",
            "status_messages": msgs + ["🤖 LLM analysis complete"],
        }
    except Exception as exc:
        logger.warning("[Graph] LLM parse error: %s", exc)
        return {
            **state,
            "analysis": None,
            "last_error": str(exc),
            "status_messages": msgs,
        }


# ── Node 3: Score routing / borderline check ──────────────────────────────────
def node_score_routing(state: ComplianceState) -> ComplianceState:
    """Evaluate score; mark borderline cases for re-analysis."""
    analysis = state.get("analysis")
    if analysis is None:
        return {**state, "is_borderline": False}

    score = analysis.risk_score
    is_borderline = (5 <= score <= 7) and state.get("retry_count", 0) < 2
    reason = f"Score {score} is in borderline range (5–7), re-analysing for accuracy." if is_borderline else ""

    msgs = state.get("status_messages", [])
    if is_borderline:
        msgs = msgs + [f"⚠️ Borderline score ({score}/10) — triggering re-analysis…"]

    return {**state, "is_borderline": is_borderline, "retry_reason": reason, "status_messages": msgs}


# ── Node 4: Self-correction ───────────────────────────────────────────────────
def node_self_correct(state: ComplianceState) -> ComplianceState:
    """Triggered when LLM output was malformed — increment correction counter."""
    correction_count = state.get("correction_count", 0) + 1
    logger.info("[Graph] node_self_correct | case=%s | attempt=%d", state["case_id"], correction_count)
    return {
        **state,
        "correction_count": correction_count,
        "status_messages": state.get("status_messages", []) + [
            f"🔁 Output malformed, self-correcting (attempt {correction_count}/3)…"
        ],
    }


# ── Node 5: Increment retry counter ──────────────────────────────────────────
def node_increment_retry(state: ComplianceState) -> ComplianceState:
    """Increment retry count before re-analysing a borderline result."""
    retry_count = state.get("retry_count", 0) + 1
    return {**state, "retry_count": retry_count}


# ── Node 6: Finalise result ───────────────────────────────────────────────────
def node_finalise(state: ComplianceState) -> ComplianceState:
    """Accept current analysis as final — or fall back to heuristic."""
    analysis = state.get("analysis")
    if analysis is None:
        logger.warning("[Graph] node_finalise: no analysis, using heuristic fallback")
        analysis = _heuristic_analysis(state["content"], state.get("policy_context", ""))

    msgs = state.get("status_messages", []) + ["✅ Analysis finalised"]
    return {**state, "final_analysis": analysis, "status_messages": msgs}


# ── Conditional edge functions ────────────────────────────────────────────────
def edge_after_analyse(state: ComplianceState) -> str:
    """Route after analysis: self-correct if malformed, else score-route."""
    if state.get("analysis") is None:
        correction_count = state.get("correction_count", 0)
        if correction_count < 2:
            return "self_correct"
        return "finalise"   # give up after 2 corrections
    return "score_routing"


def edge_after_score_routing(state: ComplianceState) -> str:
    """Route after scoring: re-analyse if borderline, else finalise."""
    if state.get("is_borderline"):
        return "increment_retry"
    return "finalise"


# ── Heuristic fallback (unchanged from original) ─────────────────────────────
def _heuristic_analysis(content: str, policy_context: str) -> ComplianceAnalysis:
    lowered = content.lower()
    issue_rules = [
        ("Guaranteed returns",
         ["guaranteed return", "guaranteed returns", "guaranteed profit", "guaranteed wealth",
          "guaranteed cashback", "guaranteed approval", "risk-free", "no risk", "zero risk"],
         "Claims must not promise guaranteed investment outcomes."),
        ("Overpromising tone",
         ["double your money", "sure profit", "best returns", "guaranteed profit", "guaranteed wealth"],
         "Marketing must avoid exaggerated or misleading statements."),
        ("Missing risk warning",
         ["investment", "returns", "portfolio", "profit", "wealth plan", "mutual fund", "sip"],
         "Investment content should include a clear risk warning."),
        ("Restricted advice",
         ["you should invest", "must buy", "definitely invest", "must invest",
          "invest immediately", "invest today"],
         "Personalized investment advice requires proper suitability checks."),
        ("Fee disclosure gap",
         ["zero fee", "free loan", "no charges", "no hidden charges", "zero fees", "no annual fee"],
         "Fee claims must include conditions, exclusions, and applicable charges."),
    ]
    issues: list[ComplianceIssue] = []
    for title, keywords, reason in issue_rules:
        if any(kw in lowered for kw in keywords):
            issues.append(ComplianceIssue(
                issue=title, reason=reason,
                policy_reference="Relevant retrieved policy context",
                suggested_correction="Add balanced wording and required disclosures.",
            ))
    score = min(10, 2 + len(issues) * 2)
    if any(kw in lowered for kw in [
        "guaranteed return", "guaranteed returns", "guaranteed profit",
        "guaranteed cashback", "guaranteed approval", "risk-free", "zero risk",
    ]):
        score = max(score, 8)
    category = risk_category_from_score(score)
    status   = status_from_score(score)
    return ComplianceAnalysis(
        risk_score=score, risk_category=category, issues_found=issues,
        policy_violations=[i.issue for i in issues],
        missing_disclosures=["Risk disclosure"] if any("risk warning" in i.issue.lower() for i in issues) else [],
        explanation="Heuristic fallback — OPENAI_API_KEY not configured.",
        suggested_correction="Add clear disclosures, risk warnings, and balanced language.",
        final_status=status,
    )
