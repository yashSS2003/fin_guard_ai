# FinGuard AI: Compliance Review & Risk Assessment System

FinGuard AI is a beginner-to-intermediate AI/ML portfolio project for reviewing financial content against a small compliance policy knowledge base. It demonstrates LLM analysis, local RAG with FAISS, SQLite memory, human-in-the-loop review, and Streamlit dashboarding.

## Features

- Paste text or upload `.txt` and `.pdf` documents
- Retrieve relevant policy chunks from `data/policies`
- Generate structured compliance analysis with risk score, issues, explanations, and corrections
- Route high-risk cases to a human review queue
- Store every case and reviewer decision in SQLite
- Search review history and export records to CSV
- View dashboard metrics and risk distribution charts

## Tech Stack

- Python 3.11+
- Streamlit
- LangChain
- OpenAI-compatible chat and embedding models
- FAISS
- SQLite
- Pandas
- Pydantic
- python-dotenv

## Setup

```bash
cd fin_guard_ai
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Add your API key to `.env`:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
DATABASE_PATH=data/compliance.db
```

Run the app:

```bash
streamlit run app.py
```

If `OPENAI_API_KEY` is not configured, the app still runs with a local rule-based analysis fallback and keyword-based embeddings. This is useful for demos, but real LLM output requires an API key.

## Project Structure

```text
fin_guard_ai/
  app.py
  config.py
  requirements.txt
  README.md
  data/
    policies/
    sample_inputs/
  pages/
  src/
```

## Interview Talking Points

- RAG makes the LLM answer with policy context instead of relying only on model memory.
- Pydantic validates structured model outputs and protects downstream UI/database code.
- SQLite memory turns the app from a one-off analyzer into a review system with audit history.
- High-risk cases are routed to human reviewers, which reflects realistic compliance workflows.
