# ai-server (FastAPI + LangGraph)

PCForge의 AI 서버입니다. LangGraph 에이전트, 카탈로그 검색, RAG, 로컬 LLM을 맡고, **인증과 기록 저장은 맡지 않습니다.** 전체 구조는 [루트 README](../README.md)를 참고하세요.

추천 후보는 `data/catalog/`의 기준 시세와 실시간 매물입니다. Ollama가 없으면 설명은 짧은 요약이고, 회원 메모는 단어로 우선순위를 고릅니다.

## 실행

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt     # Linux/macOS: .venv/bin/python
cp .env.example .env

.venv/Scripts/python -m uvicorn app.main:app --port 8000    # API 서버
.venv/Scripts/python -m streamlit run streamlit_app.py      # 단독 MVP 화면
```

- API 문서(Swagger UI): <http://localhost:8000/docs>
- 포트는 `--port`로 정합니다.
- `OLLAMA_BASE_URL`의 기본은 `http://localhost:11434`입니다.
- 네이버 키가 없으면 `POST /catalog/refresh`는 `503`이고, 기존 `live.json`은 유지됩니다.

## 엔드포인트

| 경로 | 설명 |
|------|------|
| `GET /health` | 서버, Chroma, Ollama, 실시간 수집 상태 |
| `POST /agent/run` | 그래프를 실행하고 추천을 반환 |
| `POST /catalog/refresh` | 네이버 키가 있을 때 백그라운드 갱신 |

요청·응답 예시는 [API 레퍼런스](../Docs/guidance/api-reference.md)에 있습니다.

## 구조

```
app/
├── main.py              FastAPI 앱
├── schemas.py           Requirements, Product, Recommendation, AgentResult
├── agents/graph.py      LangGraph 그래프와 8개 노드
├── catalog.py           추천에 넣는 카탈로그 검색
├── llm/ollama.py        채팅·임베딩
├── ingest/              네이버 Open API와 갱신 주기
├── tools/site_search.py 남아 있는 목업 도구. 그래프 검색은 catalog.py를 사용
└── rag/                 Chroma 인덱스와 조회
scripts/                 기준 시세, 실시간 수집, 재고 재확인. _probe는 조사 전용
streamlit_app.py         에이전트 단독 화면
```

## 에이전트

```
RequirementsAnalyzer → NoteReader → SearchPlanner → SiteSearcher → ResultNormalizer
  → CompatibilityChecker → RankerAndRecommender → Explainer
```

- 각 노드는 `AgentState`의 일부만 반환하고, `steps`는 노드마다 누적됩니다.
- 노드별 동작은 [아키텍처 문서](../Docs/Architecture/pcforge_architecture.md)에 있습니다.
- 수집 범위와 재고 값은 [카탈로그 가이드](../Docs/guidance/catalog.md)에 있습니다.

## 의존성

버전은 [requirements.txt](requirements.txt)에 고정되어 있습니다.
