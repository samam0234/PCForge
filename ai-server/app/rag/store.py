"""호환성 문서를 Chroma에 넣고 비슷한 메모를 찾는다.

임베딩은 Ollama의 bge-m3를 쓰고, 그 호출이 실패하면 해시 벡터로라도 컬렉션을 유지한다.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
import threading
from pathlib import Path

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb
from chromadb.config import Settings

from app.llm import ollama

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE_PATH = ROOT / "data" / "knowledge" / "compatibility.json"
CHROMA_DIR = ROOT / "ai-server" / "data" / "chroma"
COLLECTION = "pcforge_knowledge"
_lock = threading.Lock()
_client = None
_ready: tuple[float, str] | None = None


def _client_or_new():
    global _client
    if _client is None:
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def hash_embed(text: str, dim: int = 384) -> list[float]:
    vector = [0.0] * dim
    tokens = re.findall(r"\w+", text.lower(), flags=re.UNICODE) or ["empty"]
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def embed_texts(texts: list[str]) -> tuple[list[list[float]], str]:
    model = os.getenv("EMBEDDING_MODEL", "bge-m3")
    try:
        vectors = ollama.embed(model, texts)
        width = len(vectors[0])
        if width > 0 and all(len(vector) == width for vector in vectors):
            return vectors, f"ollama:{model}"
    except Exception as exc:
        logger.warning("Ollama 임베딩을 쓰지 못해 해시 벡터로 넘깁니다: %s", exc)
    return [hash_embed(text) for text in texts], "hash"


def _documents() -> list[dict]:
    return json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))


def ensure_index() -> str:
    """인덱스를 준비한다. 문서 파일이 그대로면 다시 임베딩하지 않는다."""
    global _ready
    with _lock:
        mtime = KNOWLEDGE_PATH.stat().st_mtime
        if _ready and _ready[0] == mtime:
            return _ready[1]
        docs = _documents()
        texts = [f"{doc['title']}\n{doc['text']}" for doc in docs]
        vectors, embedder = embed_texts(texts)
        digest = hashlib.sha256(
            (json.dumps(docs, ensure_ascii=False) + "|" + embedder).encode("utf-8")
        ).hexdigest()
        marker = CHROMA_DIR / "source.sha256"
        client = _client_or_new()
        if marker.exists() and marker.read_text(encoding="utf-8") == digest:
            try:
                if client.get_collection(COLLECTION).count() == len(docs):
                    _ready = (mtime, embedder)
                    return embedder
            except Exception:
                logger.info("Chroma 컬렉션을 다시 만듭니다")
        try:
            client.delete_collection(COLLECTION)
        except Exception:
            pass
        collection = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
        collection.add(
            ids=[doc["id"] for doc in docs],
            documents=texts,
            embeddings=vectors,
            metadatas=[{"title": doc["title"], "tags": doc.get("tags", "")} for doc in docs],
        )
        marker.write_text(digest, encoding="utf-8")
        _ready = (mtime, embedder)
        return embedder


def retrieve(query: str, k: int) -> tuple[list[dict[str, str]], str | None]:
    global _ready
    try:
        embedder = ensure_index()
        vectors, query_embedder = embed_texts([query])
        if query_embedder != embedder:
            marker = CHROMA_DIR / "source.sha256"
            if marker.exists():
                marker.unlink()
            _ready = None
            ensure_index()
            vectors, _ = embed_texts([query])
        collection = _client_or_new().get_collection(COLLECTION)
        count = collection.count()
        if count == 0:
            return [], "호환성 메모가 비어 있습니다."
        found = collection.query(query_embeddings=vectors, n_results=min(k, count))
    except Exception as exc:
        logger.warning("Chroma 검색 실패: %s", exc)
        return [], "벡터 검색을 쓰지 못했습니다. 규칙 경고만 확인하세요."

    notes = []
    metadatas = (found.get("metadatas") or [[]])[0]
    documents = (found.get("documents") or [[]])[0]
    for meta, document in zip(metadatas, documents):
        title = (meta or {}).get("title") or "메모"
        body = document or ""
        if "\n" in body:
            body = body.split("\n", 1)[1]
        notes.append({"title": title, "text": body.strip()})
    return notes, None


def status() -> str:
    try:
        count = _client_or_new().get_collection(COLLECTION).count()
    except Exception:
        return "cold"
    return "up" if count else "empty"
