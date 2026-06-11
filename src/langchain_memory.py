"""Persistent LangChain conversation memory backed by SQLite."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    messages_from_dict,
    messages_to_dict,
)

from config import settings


class SQLiteChatHistory(BaseChatMessageHistory):
    """LangChain-compatible chat history stored in SQLite."""

    def __init__(self, session_id: str, db_path: Path | None = None) -> None:
        self.session_id = session_id
        self.db_path = db_path or settings.resolved_database_path().parent / "chat_memory.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id  TEXT NOT NULL,
                    message     TEXT NOT NULL,
                    created_at  TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON chat_history(session_id)")

    @property
    def messages(self) -> list[BaseMessage]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT message FROM chat_history WHERE session_id = ? ORDER BY id",
                (self.session_id,),
            ).fetchall()
        dicts = [json.loads(row[0]) for row in rows]
        return messages_from_dict(dicts)

    def add_message(self, message: BaseMessage) -> None:
        serialized = json.dumps(messages_to_dict([message])[0])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO chat_history (session_id, message, created_at) VALUES (?, ?, ?)",
                (self.session_id, serialized, datetime.now(timezone.utc).isoformat()),
            )

    def add_user_message(self, message: str) -> None:
        self.add_message(HumanMessage(content=message))

    def add_ai_message(self, message: str) -> None:
        self.add_message(AIMessage(content=message))

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM chat_history WHERE session_id = ?", (self.session_id,))

    def get_recent(self, n: int = 10) -> list[BaseMessage]:
        """Return the n most recent messages."""
        return self.messages[-n:]

    def to_context_string(self, n: int = 6) -> str:
        """Format recent messages as a compact string for prompt injection."""
        msgs = self.get_recent(n)
        lines = []
        for m in msgs:
            role = "User" if isinstance(m, HumanMessage) else "Assistant"
            lines.append(f"{role}: {m.content[:300]}")
        return "\n".join(lines)

    def save_review_summary(self, case_id: str, risk_score: int,
                             risk_category: str, issues: list[dict]) -> None:
        """Persist a compact review summary as an AI message for session memory."""
        issue_titles = [i.get("issue", "") for i in issues[:3]]
        summary = (
            f"Review {case_id}: score={risk_score}/10, category={risk_category}. "
            f"Issues: {', '.join(issue_titles) if issue_titles else 'none'}."
        )
        self.add_ai_message(summary)

    @staticmethod
    def get_all_sessions(db_path: Path | None = None) -> list[str]:
        """List all distinct session IDs in the database."""
        db = db_path or settings.resolved_database_path().parent / "chat_memory.db"
        if not db.exists():
            return []
        with sqlite3.connect(db) as conn:
            rows = conn.execute(
                "SELECT DISTINCT session_id FROM chat_history ORDER BY session_id"
            ).fetchall()
        return [r[0] for r in rows]
