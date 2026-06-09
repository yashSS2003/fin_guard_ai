"""Application configuration for FinGuard AI."""

from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR   = Path(__file__).resolve().parent
DATA_DIR   = BASE_DIR / "data"
POLICY_DIR = DATA_DIR / "policies"
FAISS_DIR  = DATA_DIR / "faiss_index"

load_dotenv(BASE_DIR / ".env")


def _get_secret(key: str, default: str = "") -> str:
    """Read from env first, then fall back to Streamlit secrets if available."""
    val = os.getenv(key, "")
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


class Settings:
    """Centralized environment-backed settings."""

    openai_api_key:  str  = ""
    openai_model:    str  = ""
    embedding_model: str  = ""
    database_path:   Path = Path("data/compliance.db")
    retrieval_k:     int  = 3

    def __init__(self) -> None:
        self.openai_api_key  = _get_secret("OPENAI_API_KEY",   "")
        self.openai_model    = _get_secret("OPENAI_MODEL",     "gpt-4o-mini")
        self.embedding_model = _get_secret("EMBEDDING_MODEL",  "text-embedding-3-small")
        db_path_str          = _get_secret("DATABASE_PATH",    "data/compliance.db")
        self.database_path   = Path(db_path_str)

    def resolved_database_path(self) -> Path:
        if self.database_path.is_absolute():
            return self.database_path
        return BASE_DIR / self.database_path


settings = Settings()
