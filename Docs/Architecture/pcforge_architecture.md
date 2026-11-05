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
                     │ PostgreSQL  │          │ Ollama       │
                     │             │          │ + Chroma     │
                     └─────────────┘          └──────────────┘
```

PostgreSQL 호스트 포트는 루트 `.env`의 `POSTGRES_PORT`이고 기본은 `5432`입니다. 카탈로그 JSON은 DB에 두지 않고 `data/catalog/`에서 읽습니다.

| 계층 | 맡는 일 | 맡지 않는 일 |
|------|---------|--------------|
| SvelteKit | 목록, 필터, 담기, 추천 화면, 로그인, 기록 | DB 접근, AI 서버 직접 호출 |
| Axum | 인증, 등급 결정, 카탈로그 조회, 추천 요청 정리, 기록 저장 | 에이전트·LLM 로직 |
| FastAPI | LangGraph, 카탈로그 검색, RAG, Ollama, 실시간 수집 | 사용자 인증, 기록 저장 |

## 추천 요청 흐름

1. SvelteKit이 `POST /api/recommend`로 Axum에 보냅니다. 로그인한 경우 토큰을 붙입니다.
2. Axum이 용도·예산·등급·메모·담아 둔 id를 정리합니다. 판매가 끝난 id는 여기서 뺍니다.
3. Axum이 `POST /agent/run`으로 FastAPI를 호출합니다.
4. FastAPI가 그래프를 실행합니다. 회원 메모는 `NoteReader`가 우선순위로 읽고, 설명은 Ollama가 작성합니다. 모델이 없으면 단어 추출과 짧은 요약으로 넘어갑니다.
5. 회원 요청이면 Axum이 세션과 추천을 저장하고 `session_id`를 붙여 응답합니다.

요청·응답 형식은 [API 레퍼런스](../guidance/api-reference.md), 목록 파일과 수집 한계는 [카탈로그 가이드](../guidance/catalog.md)에 있습니다.

## 코드 위치

| 영역 | 위치 | 설명 |
|------|------|------|
| 첫 화면 | `frontend/src/routes/+page.svelte` | 목록과 추천 |
| 로그인 | `frontend/src/routes/login/` | 가입·로그인 |
| 기록 | `frontend/src/routes/history/` | 내 추천 |
| 안내 글 | `frontend/src/routes/journal/` | 사용 설명 |
| 상담 | `frontend/src/routes/assistant/` | 질문과 도구 진행 표시 |
| 목록 화면 | `frontend/src/components/CatalogDesk.svelte` | 필터, 예산, 재고, 담기 |
| 프론트 API | `frontend/src/lib/api.ts` | Axum 호출 |
| 백엔드 라우트 | `backend/src/routes/` | health, catalog, recommend, sessions, auth, chat |
| 상담 전달 | `backend/src/routes/assistant.rs` | 대화 검증과 NDJSON 전달 |
| 카탈로그 조회 | `backend/src/catalog.rs` | 기준 시세와 실시간 파일을 합쳐 거름 |
| 에이전트 | `ai-server/app/agents/graph.py` | 추천 8개 노드 |
| 상담 에이전트 | `ai-server/app/agents/assistant.py` | 도구를 호출하는 대화 |
| 카탈로그 검색 | `ai-server/app/catalog.py` | 추천 후보 |
| 로컬 모델 | `ai-server/app/llm/ollama.py` | 채팅·임베딩. 실패하면 호출부가 대체 |
| RAG | `ai-server/app/rag/` | Chroma. 문서가 없으면 빈 메모 |
| 실시간 수집 | `ai-server/app/ingest/` | 네이버 Open API와 주기 |
| 수집 스크립트 | `ai-server/scripts/` | 기준 시세, 실시간 매물, 재고 재확인 |

## LangGraph 노드

```
RequirementsAnalyzer → NoteReader → SearchPlanner → SiteSearcher
  → ResultNormalizer → CompatibilityChecker → RankerAndRecommender → Explainer
```

| 노드 | 현재 동작 |
|------|-----------|
| RequirementsAnalyzer | 등급, 용도, 예산, 담아 둔 수, 메모 길이를 단계 로그에 남김 |
| NoteReader | 회원 메모를 Ollama로 읽어 가격·성능·소음·전력을 보탬. 실패하면 메모 속 단어 |
| SearchPlanner | 담아 둔 id가 있으면 그 목록을, 없으면 조건으로 카탈로그를 거름 |
| SiteSearcher | `gather()`로 판매 가능한 카탈로그 행을 가져옴 |
| ResultNormalizer | id 또는 사이트+상품명으로 중복 제거 |
| CompatibilityChecker | Chroma에서 호환 메모를 찾아 경고에 제목을 붙임 |
| RankerAndRecommender | 예산 안에서 점수화하고 구성 순서로 추천 |
| Explainer | Ollama로 설명. 연결이 없으면 짧은 요약 |

## 데이터

### PostgreSQL

| 테이블 | 내용 |
|--------|------|
| `users` | 이메일, 이름, `password_hash`, 선호도 |
| `auth_tokens` | 토큰 해시, 만료 14일 |
| `search_sessions` | 회원 추천 요청. 설명은 `requirements_json._explanation` |
| `recommendations` | 세션별 추천 상품 |
| `product_cache` | 스키마만 있고 현재 수집 경로에서는 쓰지 않음 |
| `compatibility_rules` | 스키마만 있음. 호환 메모는 Chroma와 규칙 함수가 담당 |

스키마는 `backend/migrations/0001_init.sql`과 `0002_auth.sql`입니다.

### 카탈로그 파일

기준 시세는 `products.json`, 판매 페이지가 있는 매물은 `live.json`입니다. `live.json`은 생성 파일이라 커밋하지 않습니다.

## 구현 현황

| 항목 | 상태 |
|------|------|
| 목록, 예산 전체, 재고 상태 필터 | 동작. 화면에서 확인 |
| 로그인, 추천 기록 | 동작 |
| 카탈로그 기반 추천과 호환 경고 | 동작 |
| 회원 메모의 우선순위 해석 | Ollama로 확인. 화면 추천 버튼 경로는 별도 기록 |
| 실시간 매물 | 중고나라·당근·다나와 허용 페이지. 네이버는 키가 있을 때만 |
| 목업 검색 도구 | `site_search.py`에 남아 있으나 그래프의 검색 노드는 카탈로그를 사용 |
| 상담 | `/assistant`. 도구 4개, 대화는 서버에 저장하지 않음 |

확인 범위는 [카탈로그·메모 해석 검증](../vaildates/catalog-llm-validation.md)과 [상담 검증](../vaildates/assistant-validation.md)에 있습니다.
