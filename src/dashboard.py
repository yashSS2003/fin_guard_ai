"""Dashboard aggregation helpers."""

from __future__ import annotations

import pandas as pd


def calculate_metrics(df: pd.DataFrame) -> dict[str, float | int]:
    if df.empty:
        return {
            "total_cases": 0,
            "pending_reviews": 0,
            "approved_cases": 0,
            "rejected_cases": 0,
            "average_risk_score": 0.0,
            "high_risk_cases": 0,
        }

    return {
        "total_cases": len(df),
        "pending_reviews": int((df["final_decision"] == "Pending Human Review").sum()),
        "approved_cases": int(df["final_decision"].isin(["Auto Approved", "Approved"]).sum()),
        "rejected_cases": int((df["final_decision"] == "Rejected").sum()),
        "average_risk_score": round(float(df["risk_score"].mean()), 2),
        "high_risk_cases": int((df["risk_category"] == "High").sum()),
    }
