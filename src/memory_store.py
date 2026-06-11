"""SQLite persistence for review memory and reviewer decisions."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from config import settings
from src.schemas import ReviewRecord


class MemoryStore:
    """Small SQLite-backed memory store for all review cases."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.resolved_database_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reviews (
                    case_id TEXT PRIMARY KEY,
                    input_content TEXT NOT NULL,
                    retrieved_policies TEXT NOT NULL,
                    risk_score INTEGER NOT NULL,
                    risk_category TEXT NOT NULL,
                    issues TEXT NOT NULL,
                    suggested_corrections TEXT NOT NULL,
                    final_decision TEXT NOT NULL,
                    reviewer_comments TEXT DEFAULT '',
                    timestamp TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def save_review(self, record: ReviewRecord) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO reviews (
                    case_id, input_content, retrieved_policies, risk_score,
                    risk_category, issues, suggested_corrections, final_decision,
                    reviewer_comments, timestamp, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.case_id,
                    record.input_content,
                    json.dumps(record.retrieved_policies),
                    record.risk_score,
                    record.risk_category,
                    json.dumps(record.issues),
                    record.suggested_corrections,
                    record.final_decision,
                    record.reviewer_comments,
                    record.timestamp.isoformat(),
                    now,
                ),
            )

    def update_decision(self, case_id: str, decision: str, comments: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE reviews
                SET final_decision = ?, reviewer_comments = ?, updated_at = ?
                WHERE case_id = ?
                """,
                (decision, comments, datetime.now(timezone.utc).isoformat(), case_id),
            )

    def get_case(self, case_id: str) -> dict[str, Any] | None:
        rows = self.search_reviews(case_id)
        if rows.empty:
            return None
        return rows.iloc[0].to_dict()

    def search_reviews(self, query: str = "") -> pd.DataFrame:
        with self.connect() as conn:
            if query:
                like_query = f"%{query}%"
                df = pd.read_sql_query(
                    """
                    SELECT * FROM reviews
                    WHERE case_id LIKE ? OR input_content LIKE ? OR risk_category LIKE ?
                    ORDER BY timestamp DESC
                    """,
                    conn,
                    params=(like_query, like_query, like_query),
                )
            else:
                df = pd.read_sql_query("SELECT * FROM reviews ORDER BY timestamp DESC", conn)
        return df

    def pending_reviews(self) -> pd.DataFrame:
        with self.connect() as conn:
            return pd.read_sql_query(
                """
                SELECT * FROM reviews
                WHERE final_decision = 'Pending Human Review'
                ORDER BY risk_score DESC, timestamp ASC
                """,
                conn,
            )
