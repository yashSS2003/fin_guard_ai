"""Local RAG engine using LangChain loaders, embeddings, and FAISS."""

from __future__ import annotations

from pathlib import Path

from langchain_community.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import DATA_DIR, POLICY_DIR, settings
from src.utils import logger


class KeywordEmbeddings(Embeddings):
    """Deterministic local fallback when no API key is configured."""

    terms = [
        "disclosure",
        "risk",
        "return",
        "guarantee",
        "fee",
        "misleading",
        "investment",
        "marketing",
        "advice",
        "complaint",
        "kyc",
        "privacy",
        "loan",
        "credit",
        "approved",
        "restricted",
    ]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        lowered = text.lower()
        return [float(lowered.count(term)) for term in self.terms]


def get_embeddings() -> Embeddings:
    if settings.openai_api_key:
        return OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key)
    logger.warning("OPENAI_API_KEY missing. Using local keyword embeddings fallback.")
    return KeywordEmbeddings()


class RAGEngine:
    """Build and query the policy knowledge base."""

    def __init__(self, policy_dir: Path = POLICY_DIR) -> None:
        self.policy_dir = policy_dir
        self.embeddings = get_embeddings()
        index_name = settings.embedding_model if settings.openai_api_key else "keyword_fallback"
        self.index_dir = DATA_DIR / "faiss_index" / index_name.replace("/", "_")
        self.vector_store = self._load_or_create_index()

    def _load_policy_documents(self) -> list[Document]:
        documents: list[Document] = []
        for path in sorted(self.policy_dir.glob("*.txt")):
            text = path.read_text(encoding="utf-8").strip()
            if text:
                documents.append(Document(page_content=text, metadata={"source": path.name}))
        if not documents:
            raise FileNotFoundError("No policy files found in data/policies.")
        splitter = RecursiveCharacterTextSplitter(chunk_size=650, chunk_overlap=100)
        return splitter.split_documents(documents)

    def _load_or_create_index(self) -> FAISS:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        index_file = self.index_dir / "index.faiss"
        if index_file.exists():
            try:
                return FAISS.load_local(
                    str(self.index_dir),
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
            except Exception as exc:
                logger.warning("Could not load FAISS index, rebuilding: %s", exc)

        chunks = self._load_policy_documents()
        vector_store = FAISS.from_documents(chunks, self.embeddings)
        vector_store.save_local(str(self.index_dir))
        return vector_store

    def retrieve(self, query: str, k: int | None = None) -> list[Document]:
        if not query.strip():
            return []
        return self.vector_store.similarity_search(query, k=k or settings.retrieval_k)

    def retrieve_text(self, query: str) -> tuple[str, list[str]]:
        docs = self.retrieve(query)
        formatted = []
        references = []
        for doc in docs:
            source = doc.metadata.get("source", "policy")
            references.append(f"{source}: {doc.page_content[:180]}...")
            formatted.append(f"Source: {source}\n{doc.page_content}")
        return "\n\n".join(formatted), references
