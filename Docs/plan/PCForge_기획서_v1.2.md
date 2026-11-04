# PCForge 기획서 v1.2

**AI 기반 컴퓨터 장비 맞춤 추천 에이전트 플랫폼**

| 항목 | 내용 |
|------|------|
| 프로젝트명 | PCForge |
| 버전 | 1.2 |
| 작성일 | 2026-11-05 |
| 기술 스택 | SvelteKit (TypeScript) + Axum (Rust) + FastAPI |
| 데이터베이스 | PostgreSQL |
| 유형 | 미니 프로젝트 (Vibe Coding 대상 · 사심 + 실용) |
| AI 핵심 | LangChain / LangGraph + RAG + 로컬 LLM (Ollama / LM Studio) + Streamlit MVP |

---

## 1. 프로젝트 개요

**PCForge**는 사용자가 원하는 PC 용도(게이밍, 영상편집, 개발, AI 학습, 사무 등), 예산, 선호 조건(신품/중고, 브랜드, 성능 수준, 소음/전력/크기 등)을 입력하면 AI 에이전트가 공식 쇼핑몰과 중고 거래 사이트에서 적합한 부품·완제품·조립 PC를 검색·비교·추천해 주는 맞춤형 에이전트 사이트입니다.

핵심 가치는 **“내 예산과 용도에 딱 맞는 PC 구성·장비를 여러 쇼핑몰에서 한 번에 찾아주고, 비교·추천까지 해주는 경험”**입니다.

### 선정 배경
- 사용자 본인에게 당장 필요한 실용적인 도구 (사심 프로젝트)
- 공식 쇼핑몰(11번가, 쿠팡, 컴퓨존, 오버시스템, 다나와, 샵다나와 등)과 중고 사이트(번개장터, 중고나라, 당근마켓 등)를 아우르는 통합 검색·추천 에이전트
- LangChain / LangGraph 기반 에이전트 워크플로우 + RAG로 환각 최소화 및 분석 강화 실습에 적합
- SvelteKit + Axum + FastAPI 3계층 아키텍처 + PostgreSQL 실습
- 로컬 LLM (Ollama / LM Studio) 활용으로 외부 API 비용 없이 빠르게 반복 가능
- Streamlit으로 AI 서버 MVP를 먼저 검증한 후 본 서비스 연동

### 대상 사이트 (초기)
**공식 쇼핑몰**
- 쿠팡, 11번가, 컴퓨존, 다나와(가격비교), 오버시스템, 샵다나와, 기타 공식몰

**중고 거래**
- 번개장터, 중고나라, 당근마켓, 중고나라 카페, 당근 비즈니스 등

---

## 2. 목표 및 범위

### 목표
1. 사용자 요구사항(용도·예산·조건) 입력 → AI 에이전트가 다중 사이트 검색·비교 → 맞춤 추천 목록 제공까지 End-to-End 구현
2. SvelteKit(프론트 + 최소 서버) / Axum(메인 오케스트레이터) / FastAPI(AI 서버) 역할 분리
3. LangGraph 기반 멀티스텝 에이전트(검색 계획 → 사이트별 조회 → 비교·필터 → 추천 생성) 구현
4. RAG로 PC 호환성·부품 지식·사이트 특성 등을 주입하여 환각 방지
5. Streamlit으로 AI 로직 빠른 검증 후 본 서비스 연동
6. 로컬 LLM (Ollama / LM Studio) 중심 운영

### 범위 (MVP)
- 사용자 요구사항 입력 폼 (용도, 예산, 신품/중고 선호, 필수 스펙, 우선순위 등)
- AI 에이전트 기반 맞춤 추천 목록 생성 (부품 또는 완제품 단위, 구성 제안 포함)
- 간단한 로그인/회원가입 및 개인 검색·추천 기록 저장
- 추천 결과 상세 비교 (가격, 스펙, 판매처, 중고 상태, 추천 근거)
- Streamlit MVP: 에이전트 워크플로우 및 추천 결과 시각화
- 기본 제품 캐시 및 검색 히스토리 (PostgreSQL)
- PC 호환성 기본 체크 (CPU-메인보드-RAM, GPU 전력/케이스 등 주요 조합)
- 용도별 프리셋 및 기본 빌드 템플릿

### 제외 범위 (향후 확장)
- 실시간 대량 크롤링 인프라 및 법적 리스크 대응 고도화
- 자동 구매/결제 연동
- 실시간 가격 알림 / 푸시
- 이미지 기반 부품 인식 또는 중고 상태 판별
- 고급 중고 신뢰도 분석 (판매자 평점 연동)
- 모바일 앱
- 다중 언어 지원
- 커뮤니티 빌드 공유 기능

---

## 3. 기술 스택

| 레이어 | 기술 | 역할 |
|--------|------|------|
| Frontend | SvelteKit (TypeScript) | UI, 요구사항 입력, 추천 결과 표시, 로그인/회원가입, 개인 기록 대시보드, 동적 서버 기능 |
| Backend (Main) | Axum (Rust) | API 게이트웨이, 인증, 비즈니스 로직, PostgreSQL 연동, FastAPI 프록시, 에러 핸들링, 캐시 |
| AI Server | FastAPI | LangGraph 에이전트, LangChain 도구, RAG 파이프라인, 로컬 LLM 연동, Streamlit MVP |
| Database | PostgreSQL | 사용자, 검색/추천 기록, 제품 캐시, 선호도, 호환성 룰, RAG 메타데이터 저장 |
| AI / Agent | LangChain, LangGraph, RAG, Ollama / LM Studio | 멀티스텝 검색·비교·추천 에이전트, 환각 억제, 로컬 추론 |
| MVP 시각화 | Streamlit | AI 서버 로직 단독 테스트 및 결과 화면 |
| 기타 | JWT 또는 세션, SQLx / Diesel, httpx, Playwright(선택), Chroma/FAISS/pgvector(선택) | 인증, DB, 서비스 간 통신, 브라우저 기반 검색 보조, 벡터 스토어 |

### AI 관련 기술 상세 및 추천 모델

**로컬 LLM 추천 (Ollama / LM Studio)**
- 한국어 + Tool Calling 우수: Qwen2.5 (7B/14B/32B), Llama 3.1/3.2 Instruct
- 경량/빠른 반복: Llama 3.2 3B, Gemma 2 9B, Phi-3.5
- 한국어 특화 시도: EEVE-Korean 계열 또는 가능한 오픈 한국어 모델
- Tool use / Agent 용도로 function calling 지원 모델 우선

**RAG 구성**
- 벡터 스토어: Chroma (개발), FAISS 또는 pgvector (프로덕션 연동 가능)
- 임베딩: 로컬 임베딩 모델 (nomic-embed, bge-m3, 또는 Ollama 임베딩)
- 문서 소스: PC 부품 호환성 가이드, 주요 칩셋/소켓 정보, 용도별 권장 사양, 사이트별 검색 팁, 중고 거래 주의사항, 주요 CPU/GPU 벤치마크 요약

**LangGraph 에이전트 노드 예시**
1. RequirementsAnalyzer: 사용자 입력 파싱 및 구조화 (용도, 예산, 하드 스펙, 우선순위)
2. SearchPlanner: 사이트별 검색 쿼리 및 전략 수립 (신품/중고 비중, 키워드 확장)
3. SiteSearcher: 도구 호출로 각 사이트 검색 (웹 검색 / 목업 / Playwright)
4. ResultNormalizer: 결과 정규화, 중복 제거, 스펙 추출, 가격 정리
5. CompatibilityChecker: RAG + 룰 기반 호환성 검증 및 경고 생성
6. RankerAndRecommender: 점수화 후 최종 추천 목록 + 근거 생성
7. Explainer: 사용자 친화적 설명, 트레이드오프, 신품/중고 믹스 제안

---

## 4. 시스템 아키텍처 및 오케스트레이션

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

### 역할 분담
- **SvelteKit**: 사용자 인터페이스, 폼, 결과 카드, 인증 UI, 기록 조회, 프리셋 선택
- **Axum**: 요청 검증, 사용자 세션, DB 저장/조회, AI 서버 호출 오케스트레이션, 캐싱, 에러 처리
- **FastAPI**: LangGraph 에이전트 실행, RAG 조회, 로컬 LLM 추론, 도구 호출 (사이트 검색 등), Streamlit 통합

---

## 5. 주요 기능 상세

### 5.1 추천 플로우 (상세)
1. 사용자가 용도·예산·조건 입력 (예: "게이밍, 150만원, 중고 GPU 가능, RTX 4060 이상, 소음 낮은 것 선호")
2. SvelteKit → Axum으로 전송
3. Axum이 유효성 검사 후 FastAPI AI 서버 호출
4. FastAPI LangGraph 에이전트:
   - 요구사항 분석 및 검색 계획 수립
   - 사이트별 검색 도구 호출 (또는 쿼리 생성)
   - 결과 수집·정규화·필터링
   - RAG로 호환성·적정성 검증
   - 최종 추천 목록 + 근거 생성
5. Axum이 결과를 PostgreSQL에 저장
6. SvelteKit에 결과 반환 및 카드 형태로 시각화 (비교 테이블 포함)

### 5.2 Streamlit MVP 화면
- 요구사항 입력 텍스트/폼 + 프리셋 버튼
- 에이전트 실행 버튼 및 중간 단계 로그 (Plan → Search → Normalize → Check → Rank)
- 최종 추천 결과 카드 (제품명, 가격, 판매처, 추천 이유, 호환성 경고)
- 로컬 LLM 선택 (Ollama 모델 목록)
- RAG 문서 조회 테스트 패널

### 5.3 데이터 모델 (PostgreSQL)
- Users: id, email, name, created_at, preferences_json
- SearchSessions: id, user_id, requirements_json, created_at, status
- Recommendations: id, session_id, product_name, price, site, url, reason, specs_json, is_used, score, created_at
- ProductCache: id, site, external_id, title, price, specs, updated_at (선택)
- CompatibilityRules: 간단한 룰 기반 호환성 데이터 (RAG 소스 겸용)
- RagDocuments: 메타데이터 (선택, 벡터는 별도)

### 5.4 추가 고려 기능 및 데이터
- 용도별 프리셋 (게이밍 / 영상편집 / 개발 / AI 학습 / 사무) + 예산 구간별 예시 구성
- 신품 vs 중고 트레이드오프 설명 및 추천 믹스
- 기본 조립 호환성 체크 및 경고 (소켓, 전력, 크기, 쿨링)
- 추천 이유 설명 가능성 (Explainable AI 스타일)
- 검색 기록 재사용 및 수정, 즐겨찾기 빌드
- 가격 범위별 추천 다양화 (최고 가성비 / 고성능 / 저소음 등)
- RAG용 데이터: 칩셋 호환성 표, 권장 파워 용량, 주요 GPU/CPU 벤치마크 요약, 중고 거래 사기 주의사항
- 향후: 사용자 피드백 기반 선호도 학습, 가격 변동 추적

---

## 6. 개발 로드맵 (Vibe Coding)

### Phase 1: AI MVP (1~3일)
- FastAPI + LangGraph 기본 에이전트 스켈레톤
- Ollama 연동 및 간단한 도구 호출 (초기 목업 검색)
- Streamlit으로 요구사항 → 추천 결과 데모 완성
- 기본 RAG (PC 스펙 지식 문서 몇 개 + 호환성 룰)

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
- 사이트별 검색 도구 개선 (실제 크롤링/API 연동 또는 고품질 목업 + Playwright)
- RAG 데이터 보강 (호환성, 가격대별 권장 구성, 사이트 특성)
- 에이전트 프롬프트 및 그래프 튜닝, 재시도/에러 핸들링
- UI/UX 개선, 프리셋, 에러 처리, 성능 최적화

---

## 7. 성공 기준

- [ ] 요구사항 입력 시 합리적인 맞춤 추천 목록이 생성됨 (호환성 경고 포함)
- [ ] Streamlit에서 에이전트 중간 과정과 최종 결과가 보임
- [ ] 로그인 후 개인 검색·추천 기록 조회 가능
- [ ] 전체 스택 (SvelteKit → Axum → FastAPI → PostgreSQL + 로컬 LLM) 동작
- [ ] LangGraph 멀티스텝 워크플로우가 실제로 실행됨
- [ ] Vibe Coding으로 빠르게 반복 가능한 구조
- [ ] 기본 신품/중고 믹스 추천 및 설명 가능

---

## 8. 다음 단계

1. FastAPI + Streamlit으로 LangGraph 에이전트 프로토타입 먼저 만들기
2. Ollama에 한국어/Tool Calling 성능 좋은 모델 설치 및 도구 호출 테스트
3. Axum 기본 프로젝트 + PostgreSQL 스키마 구성
4. SvelteKit 프론트 스켈레톤 구성
5. 사이트 검색 도구는 초기에는 목업 또는 제한적 웹 검색으로 시작 후 점진 개선
6. RAG 문서 수집 (호환성 가이드 등) 및 임베딩 파이프라인 구축

**PCForge**로 나에게 필요한 컴퓨터 장비 추천 에이전트를 빠르게 만들어 보세요!

---

### 참고: 크롤링 및 사이트 연동 시 유의점
- 각 사이트의 이용약관 및 로봇 배제 기준을 준수할 것
- 초기 MVP는 공개 검색 결과 또는 사용자 제공 링크 기반으로 시작 권장
- 장기적으로는 공식 API(가능한 경우) 또는 파트너십 활용 고려
- 중고 거래는 사기·상태 불일치 리스크가 있으므로 추천 시 주의 문구 포함
- 과도한 요청 방지 (rate limiting, 캐시 활용)

### 추천 추가 모델/도구
- 임베딩: bge-m3, nomic-embed-text
- 경량 리랭커 (선택): 로컬 cross-encoder
- 모니터링: LangSmith (개발 시) 또는 간단한 로그
