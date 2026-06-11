"""Human-in-the-loop review operations."""

from __future__ import annotations

from src.memory_store import MemoryStore


VALID_DECISIONS = ["Approved", "Rejected", "Changes Requested"]


class HumanReviewService:
    """Manage reviewer queue and decisions."""

    def __init__(self) -> None:
        self.memory = MemoryStore()

    def queue(self):
        return self.memory.pending_reviews()

    def decide(self, case_id: str, decision: str, comments: str = "") -> None:
        if decision not in VALID_DECISIONS:
            raise ValueError(f"Decision must be one of: {', '.join(VALID_DECISIONS)}")
        self.memory.update_decision(case_id, decision, comments)
