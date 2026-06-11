"""Orchestrates the LangGraph compliance review workflow."""

from __future__ import annotations

from datetime import datetime, timezone

from src.compliance_graph import get_compliance_graph
from src.langchain_memory import SQLiteChatHistory
from src.memory_store import MemoryStore
from src.schemas import ReviewRecord
from src.utils import generate_case_id, logger


class ComplianceChecker:
    """Run the full LangGraph compliance review workflow."""

    def __init__(self, session_id: str = "default") -> None:
        self.graph   = get_compliance_graph()
        self.memory  = MemoryStore()
        self.chat_memory = SQLiteChatHistory(session_id=session_id)

    def run_review(self, content: str) -> tuple[ReviewRecord, list[str]]:
        """
        Run the LangGraph workflow for a piece of content.
        Returns (ReviewRecord, status_messages).
        status_messages are small informational strings shown in the UI.
        """
        case_id = generate_case_id()
        logger.info("[ComplianceChecker] Starting review | case=%s", case_id)

        # Build initial state
        initial_state = {
            "content":             content,
            "case_id":             case_id,
            "policy_context":      "",
            "retrieved_references": [],
            "analysis":            None,
            "retry_count":         0,
            "retry_reason":        "",
            "is_borderline":       False,
            "correction_count":    0,
            "last_error":          "",
            "final_analysis":      None,
            "status_messages":     [],
        }

        # Run graph
        final_state = self.graph.invoke(initial_state)

        analysis = final_state["final_analysis"]
        status_messages = final_state.get("status_messages", [])

        # Save conversation memory
        self.chat_memory.add_user_message(f"Review request: {content[:200]}")
        self.chat_memory.save_review_summary(
            case_id=case_id,
            risk_score=analysis.risk_score,
            risk_category=analysis.risk_category,
            issues=[i.model_dump() for i in analysis.issues_found],
        )

        # Build and persist record
        record = ReviewRecord(
            case_id=case_id,
            input_content=content,
            retrieved_policies=final_state.get("retrieved_references", []),
            risk_score=analysis.risk_score,
            risk_category=analysis.risk_category,
            issues=[i.model_dump() for i in analysis.issues_found],
            suggested_corrections=analysis.suggested_correction,
            final_decision=analysis.final_status,
            reviewer_comments="",
            timestamp=datetime.now(timezone.utc),
        )
        self.memory.save_review(record)
        logger.info("[ComplianceChecker] Done | case=%s | score=%d | retries=%d | corrections=%d",
                    case_id, analysis.risk_score,
                    final_state.get("retry_count", 0),
                    final_state.get("correction_count", 0))
        return record, status_messages
