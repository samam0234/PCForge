# PCForge 아키텍처

## 계층 구조

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  SvelteKit  │────▶│      Axum        │────▶│    FastAPI      │
│  :5173      │◀────│  :3000           │◀────│  :8000          │
└─────────────┘     └──────────────────┘     └─────────────────┘
                            │                         │
                            ▼                         ▼
                     ┌─────────────┐          ┌──────────────┐
                     │ PostgreSQL  │          │ Local LLM    │
                     │ :5432       │          │ + RAG Store  │
                     └─────────────┘          └──────────────┘
```

| 계층 | 맡는 일 | 맡지 않는 일 |
|------|---------|--------------|
| SvelteKit | UI와 화면 상태 | DB 접근, AI 서버 직접 호출 |
| Axum | 인증, DB, AI 서버 호출, 캐시, 에러 처리 | 에이전트·LLM 로직 |
| FastAPI | LangGraph, RAG, 로컬 LLM, 검색 도구 | 사용자 인증, 기록 저장 |

## 추천 요청 흐름

1. SvelteKit이 요구사항을 `POST /api/recommend`로 Axum에 보냅니다.
2. Axum이 `POST /agent/run`으로 FastAPI를 호출합니다.
3. FastAPI가 LangGraph 그래프를 실행해 추천 결과를 돌려줍니다.
4. Axum이 결과를 PostgreSQL에 저장한 뒤 응답합니다. (저장은 Phase 2 예정)

## LangGraph 노드

`ai-server/app/agents/graph.py`에서 아래 순서로 실행됩니다.

```
RequirementsAnalyzer → SearchPlanner → SiteSearcher → ResultNormalizer
  → CompatibilityChecker → RankerAndRecommender → Explainer
```

## 구현 현황

| 항목 | 상태 |
|------|------|
| 계층 간 추천 요청 전달 | 동작 |
| LangGraph 7개 노드 흐름 | 동작 (규칙 기반 임시 구현) |
| 사이트 검색 | 목업 |
| 로컬 LLM, RAG, 호환성 검증 | 미구현 |
| 로그인, 세션 조회 (`/api/auth/login`, `/api/sessions`) | 미구현 (501 응답) |
| DB 스키마 | `backend/migrations/0001_init.sql` |
| 추천 기록 저장 | 미구현 |
