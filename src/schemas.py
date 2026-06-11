"""Pydantic schemas used across the compliance review workflow."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


RiskCategory = Literal["Low", "Medium", "High"]
ReviewStatus = Literal["Auto Approved", "Pending Human Review", "Approved", "Rejected", "Changes Requested"]


class ComplianceIssue(BaseModel):
    """Single detected compliance issue."""

    issue: str = Field(default="", description="Short issue title")
    reason: str = Field(default="", description="Why this was flagged")
    policy_reference: str = Field(default="", description="Related policy or rule")
    suggested_correction: str = Field(default="", description="Recommended fix")


class ComplianceAnalysis(BaseModel):
    """Structured LLM output for one review."""

    risk_score: int = Field(ge=0, le=10)
    risk_category: RiskCategory
    issues_found: list[ComplianceIssue] = Field(default_factory=list)
    policy_violations: list[str] = Field(default_factory=list)
    missing_disclosures: list[str] = Field(default_factory=list)
    explanation: str = ""
    suggested_correction: str = ""
    final_status: ReviewStatus

    @field_validator("risk_category")
    @classmethod
    def match_score_band(cls, value: RiskCategory, info):
        score = info.data.get("risk_score")
        if score is None:
            return value
        expected = risk_category_from_score(score)
        return expected


class ReviewRecord(BaseModel):
    """Database-ready review record."""

    case_id: str
    input_content: str
    retrieved_policies: list[str]
    risk_score: int
    risk_category: RiskCategory
    issues: list[dict]
    suggested_corrections: str
    final_decision: ReviewStatus
    reviewer_comments: str = ""
    timestamp: datetime


def risk_category_from_score(score: int) -> RiskCategory:
    """Map numeric score to the project risk bands."""

    if score <= 3:
        return "Low"
    if score <= 6:
        return "Medium"
    return "High"


def status_from_score(score: int) -> ReviewStatus:
    """High-risk cases require human review."""

    return "Pending Human Review" if score >= 7 else "Auto Approved"
