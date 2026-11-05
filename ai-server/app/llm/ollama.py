"""로컬 Ollama 채팅·임베딩. 모델이 없으면 호출부가 요약으로 넘어간다."""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Iterator

import httpx

logger = logging.getLogger(__name__)

_tags: list[dict] = []
_tags_at = 0.0
CHAT_FALLBACKS = ("qwen3:8b", "gemma4:12b", "gemma4:e4b")


def base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


def _installed_tags() -> list[dict]:
    global _tags, _tags_at
    now = time.time()
    if _tags and now - _tags_at < 30:
        return _tags
    try:
        response = httpx.get(f"{base_url()}/api/tags", timeout=3)
        response.raise_for_status()
        _tags = [item for item in response.json().get("models", []) if item.get("name")]
    except Exception as exc:
        logger.warning("Ollama 모델 목록을 읽지 못했습니다: %s", exc)
        _tags = []
    _tags_at = now
    return _tags


def installed_models() -> list[str]:
    return [item["name"] for item in _installed_tags()]


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


def resolve_tool_model() -> str | None:
    """도구 호출을 지원하는 로컬 모델을 고른다. 클라우드 모델로는 대화를 보내지 않는다."""
    usable = [
        item["name"]
        for item in _installed_tags()
        if "cloud" not in item["name"]
        and "ocr" not in item["name"]
        and ("capabilities" not in item or "tools" in item["capabilities"])
    ]
    for candidate in (os.getenv("OLLAMA_MODEL", "qwen3:8b"), *CHAT_FALLBACKS):
        if candidate in usable:
            return candidate
    return usable[0] if usable else None


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


def chat_stream(
    model: str,
    messages: list[dict],
    tools: list[dict] | None,
    num_predict: int,
    timeout: float,
) -> Iterator[dict]:
    """Ollama 응답 조각을 차례로 돌려준다. 조각마다 message와 done_reason이 들어 있다."""
    payload: dict = {
        "model": model,
        "stream": True,
        "think": False,
        "messages": messages,
        "options": {"temperature": 0.3, "num_predict": num_predict, "num_ctx": 8192},
    }
    if tools:
        payload["tools"] = tools
    with httpx.Client(timeout=httpx.Timeout(timeout, connect=5)) as client:
        for _ in range(2):
            with client.stream("POST", f"{base_url()}/api/chat", json=payload) as response:
                if response.status_code == 400 and "think" in payload:
                    if "think" in response.read().decode("utf-8", "replace"):
                        payload.pop("think")
                        continue
                    raise RuntimeError("Ollama가 요청을 거절했습니다")
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    if chunk.get("error"):
                        raise RuntimeError(str(chunk["error"]))
                    yield chunk
                return


def status() -> dict[str, str]:
    model = resolve_chat_model()
    if not model:
        return {"ollama": "down", "ollama_model": ""}
    return {"ollama": "up", "ollama_model": model}
