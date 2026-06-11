"""Utility helpers for text extraction, IDs, and JSON parsing."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from io import BytesIO
from typing import Any


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("finguard")


def generate_case_id() -> str:
    """Create a readable unique case identifier."""

    return f"FG-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def extract_text_from_upload(uploaded_file: Any) -> str:
    """Extract text from Streamlit-uploaded txt or pdf files."""

    if uploaded_file is None:
        return ""

    name = uploaded_file.name.lower()
    content = uploaded_file.read()

    if name.endswith(".txt"):
        return content.decode("utf-8", errors="ignore").strip()

    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ImportError("PDF uploads require pypdf. Install requirements.txt and try again.") from exc
        reader = PdfReader(BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()

    raise ValueError("Unsupported file type. Please upload a .txt or .pdf file.")


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object, including responses wrapped in markdown fences."""

    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("LLM response did not contain a JSON object.")
    return json.loads(cleaned[start : end + 1])
