"""
Liara Agentic Copilot — vector_store.py
Qdrant local vector store with fastembed for embedding.
Gracefully falls back when DB is empty or unavailable.

Retrieval is hybrid (ADR-001): dense vector search catches semantic
similarity, BM25 keyword search catches exact technical terms (env var
names, CLI flags, package names) that embeddings tend to blur. Results
from both are merged with Reciprocal Rank Fusion.
"""
import os
import re
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


# ─── BM25 Sparse Index (in-memory, built lazily from Qdrant payloads) ───────
# Completes ADR-001's "Hybrid Search (Dense + Sparse BM25)" decision: dense
# vectors alone tend to blur exact technical tokens (env var names like
# LIARA_URL, CLI flags, package names), which BM25 catches by exact match.

_TOKEN_RE = re.compile(r"[\w؀-ۿ]+")
RRF_K = 60  # standard Reciprocal Rank Fusion smoothing constant

_bm25_state = {"index": None, "ids": [], "payloads": [], "point_count": -1}


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _build_bm25_index(client):
    """(Re)builds the in-memory BM25 corpus from all Qdrant payloads.
    Cheap no-op if the collection hasn't grown since the last build."""
    global _bm25_state
    try:
        info = client.get_collection(COLLECTION_NAME)
        point_count = info.points_count or 0
    except Exception:
        return None

    if _bm25_state["index"] is not None and _bm25_state["point_count"] == point_count:
        return _bm25_state["index"]

    try:
        from rank_bm25 import BM25Okapi
    except Exception as e:
        print(f"[vector_store] rank_bm25 not available, BM25 leg disabled: {e}")
        return None

    ids, payloads, corpus = [], [], []
    try:
        offset = None
        while True:
            points, offset = client.scroll(
                collection_name=COLLECTION_NAME,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for p in points:
                text = (p.payload or {}).get("text", "")
                if not text:
                    continue
                ids.append(p.id)
                payloads.append(p.payload)
                corpus.append(_tokenize(text))
            if offset is None:
                break
    except Exception as e:
        print(f"[vector_store] BM25 corpus scroll failed: {e}")
        return None

    if not corpus:
        return None

    _bm25_state = {
        "index": BM25Okapi(corpus),
        "ids": ids,
        "payloads": payloads,
        "point_count": point_count,
    }
    return _bm25_state["index"]


def _bm25_search(client, query: str, limit: int) -> list[tuple[str, dict]]:
    """Returns up to `limit` (point_id, payload) pairs ranked by BM25 score."""
    index = _build_bm25_index(client)
    tokens = _tokenize(query)
    if index is None or not tokens:
        return []
    try:
        scores = index.get_scores(tokens)
    except Exception as e:
        print(f"[vector_store] BM25 scoring error: {e}")
        return []

    ranked_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    results = []
    for i in ranked_idx[:limit]:
        if scores[i] <= 0:
            continue
        results.append((_bm25_state["ids"][i], _bm25_state["payloads"][i]))
    return results


# ─── Search ──────────────────────────────────────────────────────────────────

def _format_hit(payload: dict) -> str:
    text = payload.get("text", "")
    url = payload.get("url", "")
    section = payload.get("section", "")
    part = f"- {text}"
    if section:
        part = f"- **{section}**: {text}"
    if url:
        part += f" ([منبع]({url}))"
    return part


def search_docs(query: str, top_k: int = 3) -> str:
    """
    Hybrid search in Liara docs: dense vectors (semantic) + BM25 (keyword),
    merged with Reciprocal Rank Fusion. Falls back to dense-only if the
    BM25 leg is unavailable, and to "" if nothing is retrievable.
    """
    if not RAG_ENABLED:
        return ""

    client = _get_client()
    if not client:
        return ""

    model = _get_embed_model()
    if not model:
        return ""

    dense_hits = []
    try:
        embeddings = list(model.embed([query]))
        if embeddings:
            vector = embeddings[0].tolist()
            dense_hits = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=vector,
                limit=top_k * 2,
            )
    except Exception as e:
        print(f"[vector_store] dense search error: {e}")

    bm25_hits = []
    try:
        bm25_hits = _bm25_search(client, query, top_k * 2)
    except Exception as e:
        print(f"[vector_store] BM25 search error: {e}")

    if not dense_hits and not bm25_hits:
        return ""

    # Reciprocal Rank Fusion — combine both rankings without needing
    # comparable score scales (cosine similarity vs. BM25 score).
    fused: dict = {}
    for rank, h in enumerate(dense_hits):
        entry = fused.setdefault(h.id, {"payload": h.payload, "score": 0.0})
        entry["score"] += 1.0 / (RRF_K + rank + 1)
    for rank, (point_id, payload) in enumerate(bm25_hits):
        entry = fused.setdefault(point_id, {"payload": payload, "score": 0.0})
        entry["score"] += 1.0 / (RRF_K + rank + 1)

    if not fused:
        return ""

    top = sorted(fused.values(), key=lambda e: e["score"], reverse=True)[:top_k]
    return "\n\n".join(_format_hit(entry["payload"] or {}) for entry in top)


def has_docs() -> bool:
    """True if the collection already has indexed points."""
    if not RAG_ENABLED:
        return False
    client = _get_client()
    if not client:
        return False
    try:
        info = client.get_collection(COLLECTION_NAME)
        return (info.points_count or 0) > 0
    except Exception:
        return False


# ─── Init on import (lazy — just prepare path) ──────────────────────────────
# Actual client creation happens on first search call
