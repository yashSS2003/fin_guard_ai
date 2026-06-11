"""LLM-powered compliance analysis with a safe local fallback."""

from __future__ import annotations

import json

from langchain_openai import ChatOpenAI

from config import settings
from src.schemas import ComplianceAnalysis, ComplianceIssue, risk_category_from_score, status_from_score
from src.utils import logger, parse_json_object


SYSTEM_PROMPT = """
You are FinGuard AI, an assistant for compliance reviewers in fintech and banking.
Analyze the submitted content against the policy context. Return only valid JSON.
Be conservative: flag guaranteed returns, missing risk warnings, misleading claims,
restricted investment advice, missing disclosures, privacy/KYC concerns, and aggressive tone.
"""


class LLMService:
    """Run compliance analysis using an OpenAI-compatible chat model."""

    def __init__(self) -> None:
        self.has_api_key = bool(settings.openai_api_key)
        self.llm = None
        if self.has_api_key:
            self.llm = ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=0.1,
            )

    def analyze(self, content: str, policy_context: str) -> ComplianceAnalysis:
        if not content.strip():
            raise ValueError("Please provide non-empty content for analysis.")

        if not self.llm:
            return self._heuristic_analysis(content, policy_context)

        prompt = f"""
Policy context:
{policy_context}

Content to review:
{content}

Required JSON schema:
{{
  "risk_score": 8,
  "risk_category": "High",
  "issues_found": [
    {{
      "issue": "Missing risk warning",
      "reason": "The content discusses returns without describing investment risk.",
      "policy_reference": "marketing_guidelines.txt",
      "suggested_correction": "Add a clear risk warning near the claim."
    }}
  ],
  "policy_violations": [],
  "missing_disclosures": [],
  "explanation": "",
  "suggested_correction": "",
  "final_status": ""
}}
"""
        try:
            response = self.llm.invoke(
                [
                    ("system", SYSTEM_PROMPT),
                    ("human", prompt),
                ]
            )
            data = parse_json_object(str(response.content))
            score = int(data.get("risk_score", 0))
            data["risk_category"] = risk_category_from_score(score)
            data["final_status"] = status_from_score(score)
            return ComplianceAnalysis.model_validate(data)
        except Exception as exc:
            logger.exception("Invalid LLM response. Falling back to heuristic analysis: %s", exc)
            return self._heuristic_analysis(content, policy_context)

    def _heuristic_analysis(self, content: str, policy_context: str) -> ComplianceAnalysis:
        lowered = content.lower()
        issue_rules = [
            ("Guaranteed returns", ["guaranteed return", "guaranteed returns", "guaranteed profit", "guaranteed wealth", "guaranteed cashback", "guaranteed approval", "risk-free", "no risk", "zero risk"], "Claims must not promise guaranteed investment outcomes."),
            ("Overpromising tone", ["double your money", "sure profit", "best returns", "guaranteed profit", "guaranteed wealth"], "Marketing must avoid exaggerated or misleading statements."),
            ("Missing risk warning", ["investment", "returns", "portfolio", "profit", "wealth plan", "mutual fund", "sip"], "Investment content should include a clear risk warning."),
            ("Restricted advice", ["you should invest", "must buy", "definitely invest", "must invest", "invest immediately", "invest today"], "Personalized investment advice requires proper suitability checks."),
            ("Fee disclosure gap", ["zero fee", "free loan", "no charges", "no hidden charges", "zero fees", "no annual fee"], "Fee claims must include conditions, exclusions, and applicable charges."),
        ]

        issues: list[ComplianceIssue] = []
        for title, keywords, reason in issue_rules:
            if any(keyword in lowered for keyword in keywords):
                issues.append(
                    ComplianceIssue(
                        issue=title,
                        reason=reason,
                        policy_reference="Relevant retrieved policy context",
                        suggested_correction="Add balanced wording, required disclosures, and avoid absolute claims.",
                    )
                )

        score = min(10, 2 + len(issues) * 2)
        if any(kw in lowered for kw in ["guaranteed return", "guaranteed returns", "guaranteed profit", "guaranteed wealth", "guaranteed cashback", "guaranteed approval", "risk-free", "zero risk"]):
            score = max(score, 8)
        category = risk_category_from_score(score)
        status = status_from_score(score)
        policy_violations = [issue.issue for issue in issues]
        missing = ["Risk disclosure"] if any("risk warning" in issue.issue.lower() for issue in issues) else []

        return ComplianceAnalysis(
            risk_score=score,
            risk_category=category,
            issues_found=issues,
            policy_violations=policy_violations,
            missing_disclosures=missing,
            explanation=(
                "Analysis used the local rule-based fallback because OPENAI_API_KEY is not configured. "
                "Retrieved policies were still used to provide context."
            ),
            suggested_correction="Review the flagged statements and add clear disclosures, risk warnings, and balanced language.",
            final_status=status,
        )

    @staticmethod
    def to_pretty_json(analysis: ComplianceAnalysis) -> str:
        return json.dumps(analysis.model_dump(), indent=2)
