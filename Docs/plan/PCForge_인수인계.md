# PCForge 에이전트 인수인계 및 규칙

**프로젝트명**: PCForge  
**버전**: 1.2  
**작성일**: 2026-11-05  
**기술 스택**: SvelteKit (TypeScript) + Axum (Rust) + FastAPI + PostgreSQL  
**유형**: 미니 프로젝트 (Vibe Coding 대상 · 사심 + 실용)  
**AI 핵심**: LangChain / LangGraph + RAG + 로컬 LLM (Ollama / LM Studio) + Streamlit MVP  
**SSOT**: 루트 `AGENTS.md` (본 문서는 인수인계 및 상세 규칙 원본, AGENTS.md는 이를 가리킴)

---

## 1. 프로젝트 개요

**PCForge**는 사용자가 원하는 PC 용도(게이밍, 영상편집, 개발, AI 학습, 사무 등), 예산, 선호 조건(신품/중고, 브랜드, 성능 수준, 소음/전력/크기 등)을 입력하면 AI 에이전트가 공식 쇼핑몰과 중고 거래 사이트에서 적합한 부품·완제품·조립 PC를 검색·비교·추천해 주는 맞춤형 에이전트 사이트입니다.

**핵심 가치**: “내 예산과 용도에 딱 맞는 PC 구성·장비를 여러 쇼핑몰에서 한 번에 찾아주고, 비교·추천까지 해주는 경험”

### 선정 배경
- 사용자 본인에게 당장 필요한 실용적인 도구 (사심 프로젝트)
- 공식 쇼핑몰(쿠팡, 11번가, 컴퓨존, 다나와, 오버시스템, 샵다나와 등)과 중고 사이트(번개장터, 중고나라, 당근마켓 등)를 아우르는 통합 검색·추천 에이전트
- LangChain / LangGraph 기반 에이전트 워크플로우 + RAG로 환각 최소화 실습
- SvelteKit + Axum + FastAPI 3계층 + PostgreSQL 실습
- 로컬 LLM (Ollama / LM Studio)으로 비용 없이 빠른 반복
- Streamlit으로 AI 서버 MVP 우선 검증

### 목표
1. 사용자 요구사항 입력 → AI 에이전트 다중 사이트 검색·비교 → 맞춤 추천 End-to-End
2. SvelteKit / Axum / FastAPI 역할 분리
3. LangGraph 멀티스텝 에이전트 구현
4. RAG로 PC 호환성·부품 지식 주입, 환각 방지
5. Streamlit MVP 후 본 서비스 연동
6. 로컬 LLM 중심 운영

### MVP 범위
- 요구사항 입력 폼 (용도, 예산, 신품/중고, 필수 스펙, 우선순위)
- AI 에이전트 기반 맞춤 추천 목록 (부품/완제품, 구성 제안 포함)
- 간단한 로그인/회원가입 및 개인 검색·추천 기록 저장
- 추천 결과 상세 비교 (가격, 스펙, 판매처, 중고 상태, 근거)
- Streamlit MVP: 에이전트 워크플로우 및 추천 결과 시각화
- 기본 제품 캐시 및 검색 히스토리 (PostgreSQL)
- PC 호환성 기본 체크
- 용도별 프리셋 및 기본 빌드 템플릿

### 제외 범위 (향후 확장)
- 실시간 대량 크롤링 인프라 및 법적 리스크 대응 고도화
- 자동 구매/결제 연동
- 실시간 가격 알림 / 푸시
- 이미지 기반 부품 인식 또는 중고 상태 판별
- 고급 중고 신뢰도 분석
- 모바일 앱, 다중 언어, 커뮤니티 빌드 공유

---

## 2. 기술 스택 및 역할

| 레이어 | 기술 | 역할 | 기본 포트 |
|--------|------|------|-----------|
| Frontend | SvelteKit (TypeScript) | UI, 폼, 결과 카드, 인증, 기록 대시보드, 프리셋 | 5173 |
| Backend (Main) | Axum (Rust) | API 게이트웨이, 인증, PostgreSQL, FastAPI 프록시, 캐시, 에러 핸들링 | 3000 |
| AI Server | FastAPI | LangGraph 에이전트, RAG, 로컬 LLM, Streamlit MVP | 8000 |
| Database | PostgreSQL | 사용자, 검색/추천 기록, 제품 캐시, 호환성 룰 | 5432 |
| AI / Agent | LangChain, LangGraph, RAG, Ollama / LM Studio | 멀티스텝 검색·비교·추천, 환각 억제 | - |
| MVP 시각화 | Streamlit | AI 서버 로직 단독 테스트 | - |
| 기타 | JWT/세션, SQLx, httpx, Playwright(선택), Chroma/FAISS/pgvector | 인증, DB, 통신, 검색 보조, 벡터 스토어 | - |

**로컬 LLM 추천 (Ollama / LM Studio)**  
한국어 + Tool Calling 우수: Qwen2.5 (7B/14B/32B), Llama 3.1/3.2 Instruct  
경량: Llama 3.2 3B, Gemma 2 9B, Phi-3.5

**RAG**: Chroma(개발) / FAISS 또는 pgvector, 로컬 임베딩 (nomic-embed, bge-m3), PC 호환성 가이드·칩셋·벤치마크 요약 문서

환경 변수는 각 레이어 `.env` / `.env.example`로 관리. API 키·DB 연결 문자열 절대 커밋 금지.

---

## 3. 시스템 아키텍처

상세: `Docs/Architecture/pcforge_architecture.md`

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  SvelteKit  │────▶│      Axum        │────▶│    FastAPI      │
│  (Frontend) │◀────│ (Main Backend)   │◀────│  (AI Server)    │
└─────────────┘     └──────────────────┘     └─────────────────┘
                            │                         │
                            ▼                         ▼
                     ┌─────────────┐          ┌──────────────┐
                     │ PostgreSQL  │          │ Local LLM    │
                     │             │          │ (Ollama/LM)  │
                     └─────────────┘          │ + RAG Store  │
                                              └──────────────┘
```

### 역할 분담 (필수·예외 없음)
| 컴포넌트 | 책임 |
|----------|------|
| **SvelteKit** | 사용자 인터페이스, 폼, 결과 카드/비교, 인증 UI, 기록 조회, 프리셋. UI/상태만. |
| **Axum** | API 게이트웨이, 인증/세션, DB 저장/조회, AI 서버 호출 오케스트레이션, 캐싱, 에러 처리. 오케스트레이션만. |
| **FastAPI** | LangGraph 에이전트 실행, RAG 조회, 로컬 LLM 추론, 도구 호출, Streamlit 통합. AI 관련 작업만. |
| **PostgreSQL** | Users, SearchSessions, Recommendations, ProductCache, CompatibilityRules. |

### LangGraph 에이전트 노드
1. RequirementsAnalyzer: 사용자 입력 파싱·구조화
2. NoteReader: 회원 메모를 가격·성능·소음·전력으로 읽기
3. SearchPlanner: 사이트별 검색 전략 수립
4. SiteSearcher: 카탈로그에서 판매 가능한 후보를 가져오기
5. ResultNormalizer: 결과 정규화·중복 제거·스펙 추출
6. CompatibilityChecker: RAG + 룰 기반 호환성 검증
7. RankerAndRecommender: 점수화 후 최종 추천 + 근거
8. Explainer: 친화적 설명 및 트레이드오프

---

## 4. 폴더 구조 (권장)

```
pcforge/
├── frontend/                     # SvelteKit
│   ├── src/
│   │   ├── routes/
│   │   ├── lib/
│   │   └── components/
│   ├── package.json
│   └── .env.example
│
├── backend/                      # Axum (Rust)
│   ├── src/
│   │   ├── main.rs
│   │   ├── routes/
│   │   ├── services/
│   │   └── db/
│   ├── Cargo.toml
│   └── .env.example
│
├── ai-server/                    # FastAPI + Streamlit
│   ├── app/
│   │   ├── main.py
│   │   ├── agents/               # LangGraph
│   │   ├── tools/
│   │   └── rag/
│   ├── streamlit_app.py
│   ├── requirements.txt
│   └── .env.example
│
├── Docs/                         # 문서 저장 폴더 (아래 구조 필수)
│   ├── plan/
│   ├── Architecture/
│   ├── branchs/
│   ├── find_debug/
│   ├── guidance/
│   ├── trainings/
│   ├── repeater/
│   ├── vaildates/
│   └── web_management/
│
├── docker-compose.yml            # (선택)
├── .env.example
├── AGENTS.md                     # SSOT
├── .gitattributes
├── LICENSE
├── SECURITY.md
└── README.md
```

### Docs 폴더 용도 (필수·예외 없음)
| 폴더 | 용도 |
|------|------|
| [plan/](./Docs/plan/) | 초기 기획·로직·DB·배포 계획 |
| [Architecture/](./Docs/Architecture/) | 시스템·계층·데이터 흐름 아키텍처 |
| [branchs/](./Docs/branchs/) | 브랜치·커밋 기록 (**템플릿 필수**, **commits/ 하위 폴더 필수**) |
| [find_debug/](./Docs/find_debug/) | 작업/실행 디버깅 일일 기록 |
| [guidance/](./Docs/guidance/) | 기능·실행 가이드 |
| [trainings/](./Docs/trainings/) | 학습·연구 정리 |
| [repeater/](./Docs/repeater/) | 서버 연결·인프라 장애와 해결 |
| [vaildates/](./Docs/vaildates/) | 검증·체크리스트 |
| [web_management/](./Docs/web_management/) | 배포 전/배포 시 웹 관리 기록 |

- `Docs/branchs/COMMIT_TEMPLATE.md` 또는 `_template.md`는 절대 삭제하지 않는다.
- 새 문서는 반드시 위 폴더 중 적절한 곳에 배치한다.

---

## 5. 데이터 모델 및 API 요약

### PostgreSQL 주요 테이블
- Users: id, email, name, created_at, preferences_json
- SearchSessions: id, user_id, requirements_json, created_at, status
- Recommendations: id, session_id, product_name, price, site, url, reason, specs_json, is_used, score, created_at
- ProductCache: id, site, external_id, title, price, specs, updated_at
- CompatibilityRules: 룰 기반 호환성 데이터

### 주요 API (예시)
- Axum: GET `/api/catalog`, POST `/api/recommend`, GET `/api/sessions`, POST `/api/auth/register`, POST `/api/auth/login`, POST `/api/auth/logout`, GET `/api/auth/me`
- FastAPI: POST `/agent/run`, GET `/health`, POST `/catalog/refresh`, Streamlit 별도
- 필드와 등급 차이는 `Docs/guidance/api-reference.md`

---

## 6. 공통 규칙 (필수·예외 없음)

### 6.1 커밋 메시지 형식
- **형식**: `type(scope): 한국어 요약`
- type/scope는 **영어**, 제목 요약과 본문은 **한국어**
- 예시:
  - ✅ `feat(frontend): 요구사항 입력 폼 컴포넌트 추가`
  - ✅ `fix(ai-server): LangGraph 호환성 체크 노드 오류 수정`
  - ✅ `docs(rules): 커밋 기록 템플릿 업데이트`
  - ✅ `chore(backend): Axum 의존성 정리`
- ❌ 금지 예시:
  - `added recommend form`
  - `feat: 추천 폼 추가` (scope 누락)
  - `fix(backend): fixed the bug` (영어 본문)

### 6.2 커밋 기록 문서화 (필수·예외 없음)
모든 커밋 시 아래 규칙으로 기록 파일을 생성·커밋한다.
- **경로**: `Docs/branchs/commits/YYMMDD_HHMM_[id]_[이름]_[브랜치].md`  
  (반드시 `branchs/commits/` 하위 폴더에 저장)
- **예시**: `Docs/branchs/commits/261105_0740_001_WHILE496_feature-recommend.md`
- 템플릿: `Docs/branchs/COMMIT_TEMPLATE.md`
- 기록 파일도 같은 브랜치에 반드시 커밋한다.
- `Docs/branchs/commits/` 폴더는 필수이며 삭제하지 않는다.

### 6.3 브랜치 전략
- 작업은 **`feature/*`** 에서만 한다.
- `develop` / `main` 은 병합 전용.
- 병합은 `--no-ff` 로 이력을 보존한다.
- **병합 시점**: 브랜치 하나가 끝날 때마다 병합하지 않는다. 요청받은 작업을 전부 커밋한 뒤 한 번에 총 병합하고, **사용자 명시적 지시 없이는 병합하지 않는다**.
- 병합 기록 문서도 총 병합 때 한 번에 작성한다.

### 6.4 되돌리기 어려운 작업 (사전 확인 필수)
- push, 병합, 삭제, 덮어쓰기는 **명시적 지시가 있을 때만** 한다.
- 한 번 승인한 것을 다른 상황에 확장 적용하지 않는다.

### 6.5 SSOT 구조
- 루트 `AGENTS.md`에 공유 규칙을 두고, `.Claude/CLAUDE.md`, `.Grok/GROK.md` 등 에이전트별 파일은 **이를 가리키기만** 한다.
- 규칙을 여러 곳에 중복 작성하지 않는다.

### 6.6 에이전트 인수인계 대상 (필수)
아래 폴더/파일을 프로젝트 루트에 준비한다.
- `.Agents/` (공통)
- `.Claude/CLAUDE.md`
- `.Codex/`
- `.Grok/GROK.md`
- `.Gemini/`
- `.Antigravity/`
- `.Cursor/`
- `.Manus/`
- `.Kimi/`
- `.Ollama/`
- `.Opencode/`
- `.Qwen/`
- `.Windsurf/`

모든 에이전트는 작업 시작 전 `AGENTS.md` 및 본 문서를 확인한다.

### 6.7 기타 필수 파일
- `.gitattributes`
- `LICENSE`
- `SECURITY.md`
- `README.md`

---

## 7. 개발 로드맵 (Vibe Coding)

### Phase 1: AI MVP (1~3일)
- FastAPI + LangGraph 기본 에이전트 스켈레톤
- Ollama 연동 및 간단한 도구 호출 (초기 목업 검색)
- Streamlit으로 요구사항 → 추천 결과 데모 완성
- 기본 RAG (PC 스펙 지식 문서 + 호환성 룰)

### Phase 2: 메인 백엔드 (1~2일)
- Axum 프로젝트 구성
- PostgreSQL 연동 (SQLx)
- FastAPI 프록시 및 기본 인증
- 검색 세션 / 추천 기록 저장

### Phase 3: 프론트엔드 (1~2일)
- SvelteKit UI + 로그인
- 요구사항 입력 폼 및 추천 결과 카드 / 비교 뷰
- 개인 기록 대시보드
- 전체 End-to-End 연동

### Phase 4: 고도화 및 폴리싱
- 사이트별 검색 도구 개선 (목업 → 실제 또는 Playwright)
- RAG 데이터 보강
- 에이전트 프롬프트 및 그래프 튜닝
- UI/UX 개선, 프리셋, 에러 처리

1–4단계는 처음 잡을 때의 순서입니다. 지금 어디까지 됐는지는 8장과 9장을 봅니다.

---

## 8. 성공 기준

- [x] 요구사항 입력 시 카탈로그 기준 추천과 호환 경고가 생성됨
- [ ] Streamlit에서 에이전트 중간 과정과 최종 결과가 보임 (화면 재확인은 없음)
- [x] 로그인 후 개인 검색·추천 기록 조회 가능
- [x] 전체 스택 (SvelteKit → Axum → FastAPI → PostgreSQL + 로컬 LLM) 동작. Ollama가 없으면 설명만 짧은 요약으로 대체
- [x] LangGraph 멀티스텝 워크플로우가 실제로 실행됨
- [x] Vibe Coding으로 빠르게 반복 가능한 구조
- [x] 기본 신품/중고 믹스 추천 및 설명 가능

확인 범위와 아직 보지 않은 항목은 `Docs/vaildates/catalog-llm-validation.md`에 있습니다.

---

## 9. 다음 단계

1. `main` 병합과 그 이후 배포는 사용자 지시 후에만 진행
2. 네이버 Open API 키가 없으면 신품 실시간 검색은 건너뛰고, 기존 `live.json`은 유지
3. 번개장터·11번가·쿠팡처럼 수집이 허용되지 않은 호스트는 계속 제외
4. 허용된 다나와 목록 첫 페이지에 단종 상품이 없으면 단종 행은 생기지 않음
5. 재확인하지 않은 중고나라 주소가 남아 있음. 다시 읽을 때는 간격을 두고 허용된 페이지만 요청

**PCForge**로 나에게 필요한 컴퓨터 장비 추천 에이전트를 빠르게 만들어 보세요!

---

## 참고
- 원본 기획서: `Docs/plan/PCForge_기획서_v1.2.md`
- 아키텍처: `Docs/Architecture/pcforge_architecture.md`
- 코딩 수칙 및 에이전트 인수인계 필수 가이드: `코딩수칙_및_에이전트인수인계_필수가이드.md`
- SSOT: 루트 `AGENTS.md`
- 크롤링 시 각 사이트 이용약관·로봇 배제 기준 준수, 초기 MVP는 목업/공개 검색 권장
