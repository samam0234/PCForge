"""호환성 지식 검색. Chroma에 넣어 둔 메모를 용도와 부품 이름에 맞춰 가져온다."""

from app.rag.store import retrieve


def retrieve_compatibility_notes(query: str, k: int = 3) -> tuple[list[dict[str, str]], str | None]:
    return retrieve(query, k)
