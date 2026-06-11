"""LangGraph state definition for the compliance review workflow."""

from __future__ import annotations
from typing import TypedDict, Optional
from src.schemas import ComplianceAnalysis


class ComplianceState(TypedDict):
    """Shared state passed between all LangGraph nodes."""

    # Input
    content: str
    case_id: str

    # RAG node output
    policy_context: str
    retrieved_references: list[str]

    # Analysis node output
    analysis: Optional[ComplianceAnalysis]

    # Re-analysis tracking
    retry_count: int
    retry_reason: str
    is_borderline: bool

    # Self-correction tracking
    correction_count: int
    last_error: str

    # Final output
    final_analysis: Optional[ComplianceAnalysis]
    status_messages: list[str]  # shown as small text in UI
