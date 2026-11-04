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
4. Axum이 결과를 PostgreSQL에 저장한 뒤 응답합니다. (저장은 Phase 2 예정, 현재는 응답만 전달)

요청·응답 형식은 [API 레퍼런스](../guidance/api-reference.md)를 참고하세요.

## 코드 위치

| 영역 | 위치 | 설명 |
|------|------|------|
| 프론트 화면 | `frontend/src/routes/+page.svelte` | 폼·결과 화면 조립 |
| 프론트 컴포넌트 | `frontend/src/components/` | 입력 폼, 추천 카드 |
| 프론트 API 호출 | `frontend/src/lib/api.ts` | Axum 호출과 응답 타입 |
| 프론트 환경 변수 | `frontend/src/env.ts` | `PUBLIC_API_BASE_URL` |
| 백엔드 라우트 | `backend/src/routes/` | health, recommend, sessions, auth |
| 백엔드 AI 호출 | `backend/src/services/ai_client.rs` | FastAPI 호출, 오류 변환 |
| 백엔드 오류 | `backend/src/error.rs` | 상태 코드 매핑 |
| 백엔드 DB | `backend/src/db/`, `backend/migrations/` | 연결 풀, 스키마 |
| 에이전트 그래프 | `ai-server/app/agents/graph.py` | 7개 노드와 흐름 |
| 검색 도구 | `ai-server/app/tools/site_search.py` | 목업 상품 |
| RAG | `ai-server/app/rag/retriever.py` | 자리만 있음 (빈 결과) |
| 스키마 | `ai-server/app/schemas.py` | 요청·응답 모델 |

## LangGraph 노드

`ai-server/app/agents/graph.py`에서 아래 순서로 실행됩니다. 상태에 `steps`를 누적해 단계 로그를 응답에 담습니다.

```
RequirementsAnalyzer → SearchPlanner → SiteSearcher → ResultNormalizer
  → CompatibilityChecker → RankerAndRecommender → Explainer
```

| 노드 | 현재 동작 | 교체 예정 |
|------|-----------|-----------|
| RequirementsAnalyzer | 입력 확인 | LLM으로 자유 입력(`notes`) 구조화 |
| SearchPlanner | `condition`에 따라 신품·중고 사이트 목록 선택 | 사이트별 키워드 확장 |
| SiteSearcher | 목업 상품 반환 | 공개 검색, 사이트 API, Playwright |
| ResultNormalizer | 사이트+상품명 중복 제거 | 스펙 추출, 가격 정리 |
| CompatibilityChecker | 미구현 경고 | 룰 + RAG 호환성 검증 |
| RankerAndRecommender | 예산 이하만 남기고 `1 - 가격/예산`으로 정렬 | 용도·우선순위 반영 점수 |
| Explainer | 고정 문장 | LLM 설명, 신품·중고 믹스 제안 |

## 데이터 모델

`backend/migrations/0001_init.sql` 기준입니다.

| 테이블 | 주요 컬럼 | 비고 |
|--------|-----------|------|
| `users` | id, email(unique), name, preferences_json | 비밀번호 컬럼 없음 (인증 방식 미정) |
| `search_sessions` | id, user_id → users, requirements_json, status | 사용자 삭제 시 함께 삭제 |
| `recommendations` | id, session_id → search_sessions, product_name, price, site, url, reason, specs_json, is_used, score | 세션 삭제 시 함께 삭제 |
| `product_cache` | id, site, external_id, title, price, specs | (site, external_id) 유일 |
| `compatibility_rules` | id, category, rule_json, description | 룰 기반 호환성 데이터 |

`id`는 UUID(`gen_random_uuid()`)이고, `RagDocuments` 테이블은 기획서에서 선택 항목이라 만들지 않았습니다.

## 구현 현황

| 항목 | 상태 |
|------|------|
| 계층 간 추천 요청 전달 | 동작 |
| LangGraph 7개 노드 흐름 | 동작 (규칙 기반 임시 구현) |
| 사이트 검색 | 목업 |
| 로컬 LLM, RAG, 호환성 검증 | 미구현 |
| 로그인, 세션 조회 (`/api/auth/login`, `/api/sessions`) | 미구현 (501 응답) |
| DB 스키마 | 작성·적용 확인 |
| 추천 기록 저장 | 미구현 |

검증 내용은 [뼈대 검증 기록](../vaildates/skeleton-validation.md)에 있습니다.

## 미정 사항

- 로컬 LLM 모델: 인수인계 문서는 `qwen3:8b`·`gemma4`, 기획서는 `Qwen2.5` 계열로 서로 다릅니다. Phase 1 시작 전에 정해야 합니다.
- 인증 방식: JWT와 세션 중 선택, 비밀번호 저장 컬럼 추가 여부.
- 벡터 스토어: 개발은 Chroma, 이후 FAISS 또는 pgvector.
