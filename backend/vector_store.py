"""
Liara Agentic Copilot — vector_store.py
Qdrant local vector store with fastembed for embedding.
Gracefully falls back when DB is empty or unavailable.
"""
import os
import tempfile
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ─── Config ──────────────────────────────────────────────────────────────────

_default_path = (
    "/app/qdrant_data"
    if os.name != "nt"
    else os.path.join(tempfile.gettempdir(), "qdrant_liara")
)
STORAGE_PATH = os.getenv("QDRANT_STORAGE_PATH", _default_path)
COLLECTION_NAME = "liara_docs"
VECTOR_SIZE = 384  # BAAI/bge-small-en-v1.5 default dim
RAG_ENABLED = os.getenv("RAG_ENABLED", "0") == "1"

os.makedirs(STORAGE_PATH, exist_ok=True)

# ─── Lazy Singletons ────────────────────────────────────────────────────────

_client = None
_qdrant_ok = False
_embed_model = None


def _get_client():
    global _client, _qdrant_ok
    if _client is not None:
        return _client
    try:
        from qdrant_client import QdrantClient
        _client = QdrantClient(path=STORAGE_PATH)
        _qdrant_ok = True
        _init_collection()
    except Exception as e:
        print(f"[vector_store] Qdrant init failed: {e}")
        _client = None
        _qdrant_ok = False
    return _client


def _init_collection():
    """Create collection if it doesn't exist."""
    global _client
    if not _client:
        return
    try:
        from qdrant_client.http.models import Distance, VectorParams
        cols = [c.name for c in _client.get_collections().collections]
        if COLLECTION_NAME not in cols:
            _client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            print(f"[vector_store] Collection '{COLLECTION_NAME}' created")
    except Exception as e:
        print(f"[vector_store] init_collection error: {e}")


def _get_embed_model():
    global _embed_model
    if _embed_model is not None:
        return _embed_model
    try:
        from fastembed import TextEmbedding
        model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        _embed_model = TextEmbedding(model_name=model_name)
    except Exception as e:
        print(f"[vector_store] Embedding model load failed: {e}")
        _embed_model = None
    return _embed_model


# ─── Search ──────────────────────────────────────────────────────────────────

def search_docs(query: str, top_k: int = 3) -> str:
    """
    Vector search in Liara docs.
    Returns formatted results or empty string for fallback.
    """
    if not RAG_ENABLED:
        return ""

    client = _get_client()
    if not client:
        return ""

    model = _get_embed_model()
    if not model:
        return ""

    try:
        embeddings = list(model.embed([query]))
        if not embeddings:
            return ""
        vector = embeddings[0].tolist()

        hits = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=top_k,
        )
        if not hits:
            return ""

        parts = []
        for h in hits:
            text = h.payload.get("text", "")
            url = h.payload.get("url", "")
            section = h.payload.get("section", "")

            part = f"- {text}"
            if section:
                part = f"- **{section}**: {text}"
            if url:
                part += f" ([منبع]({url}))"
            parts.append(part)

        return "\n\n".join(parts)

    except Exception as e:
        print(f"[vector_store] search error: {e}")
        return ""


# ─── Init on import (lazy — just prepare path) ──────────────────────────────
# Actual client creation happens on first search call
