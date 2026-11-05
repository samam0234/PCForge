"""로컬 Ollama 채팅·임베딩. 모델이 없으면 호출부가 요약으로 넘어간다."""

from __future__ import annotations

import logging
import os
import time

import httpx

logger = logging.getLogger(__name__)

_models: list[str] = []
_models_at = 0.0
CHAT_FALLBACKS = ("qwen3:8b", "gemma4:12b", "gemma4:e4b")


def base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


def installed_models() -> list[str]:
    global _models, _models_at
    now = time.time()
    if _models and now - _models_at < 30:
        return _models
    try:
        response = httpx.get(f"{base_url()}/api/tags", timeout=3)
        response.raise_for_status()
        _models = [item.get("name", "") for item in response.json().get("models", []) if item.get("name")]
    except Exception as exc:
        logger.warning("Ollama 모델 목록을 읽지 못했습니다: %s", exc)
        _models = []
    _models_at = now
    return _models


def resolve_chat_model() -> str | None:
    installed = installed_models()
    if not installed:
        return None
    wanted = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    if wanted in installed:
        return wanted
    wanted_family = wanted.split(":", 1)[0]
    for name in installed:
        if name.split(":", 1)[0] == wanted_family:
            return name
    for candidate in CHAT_FALLBACKS:
        if candidate in installed:
            return candidate
    for name in installed:
        if "cloud" in name or "ocr" in name:
            continue
        return name
    return None


def embed(model: str, texts: list[str]) -> list[list[float]]:
    response = httpx.post(
        f"{base_url()}/api/embed",
        json={"model": model, "input": texts},
        timeout=120,
    )
    response.raise_for_status()
    vectors = response.json().get("embeddings")
    if not vectors or len(vectors) != len(texts):
        raise RuntimeError("임베딩 응답이 비어 있습니다")
    return vectors


def chat(model: str, system: str, user: str, num_predict: int, timeout: float) -> str:
    payload: dict = {
        "model": model,
        "stream": False,
        "think": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "options": {"temperature": 0.4, "num_predict": num_predict},
    }
    with httpx.Client(timeout=timeout) as client:
        response = client.post(f"{base_url()}/api/chat", json=payload)
        if response.status_code == 400 and "think" in response.text:
            payload.pop("think", None)
            response = client.post(f"{base_url()}/api/chat", json=payload)
        response.raise_for_status()
        message = response.json().get("message") or {}
    return (message.get("content") or "").strip()


def status() -> dict[str, str]:
    model = resolve_chat_model()
    if not model:
        return {"ollama": "down", "ollama_model": ""}
    return {"ollama": "up", "ollama_model": model}
