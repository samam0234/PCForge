# ai-server (FastAPI + LangGraph)

PCForge의 AI 서버입니다. LangGraph 에이전트, RAG, 로컬 LLM, 검색 도구를 맡고, **인증과 기록 저장은 맡지 않습니다.** 전체 구조는 [루트 README](../README.md)를 참고하세요.

> **현재 모든 노드는 규칙 기반 임시 구현이고, 검색 결과는 목업입니다.** LLM(Ollama)과 RAG는 아직 연결되지 않았습니다.

## 실행

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt     # Linux/macOS: .venv/bin/python
cp .env.example .env

.venv/Scripts/python -m uvicorn app.main:app --port 8000    # API 서버
.venv/Scripts/python -m streamlit run streamlit_app.py      # 단독 MVP 화면
```

- API 문서(Swagger UI): <http://localhost:8000/docs>
- 포트는 `--port`로 정합니다. `.env`의 `AI_SERVER_PORT`는 코드에서 읽지 않습니다.
- `OLLAMA_*`, `EMBEDDING_MODEL`도 아직 읽지 않으며 Phase 1에서 연결합니다.

## 엔드포인트

| 경로 | 설명 |
|------|------|
| `GET /health` | `{"status":"ok"}` |
| `POST /agent/run` | 요구사항을 받아 에이전트를 실행하고 추천 결과를 반환 |

요청·응답 예시는 [API 레퍼런스](../Docs/guidance/api-reference.md)에 있습니다.

## 구조

```
app/
├── main.py              FastAPI 앱, /health, /agent/run
├── schemas.py           Requirements, Product, Recommendation, AgentResult
├── agents/graph.py      LangGraph 그래프와 7개 노드
├── tools/site_search.py 사이트 검색 도구 (목업)
└── rag/retriever.py     호환성 지식 검색 (자리만 있음, 빈 결과)
streamlit_app.py         에이전트 단독 검증 화면
```

## 에이전트

```
RequirementsAnalyzer → SearchPlanner → SiteSearcher → ResultNormalizer
  → CompatibilityChecker → RankerAndRecommender → Explainer
```

- 각 노드는 `AgentState`의 일부만 반환하고, `steps`는 노드마다 누적됩니다.
- 노드별 현재 동작과 교체 계획은 [아키텍처 문서](../Docs/Architecture/pcforge_architecture.md)에 있습니다.
- `graph.stream()`으로 노드별 진행을 받을 수 있고, Streamlit 화면이 이를 사용합니다.

### 목업 검색 도구

`tools/site_search.py`의 상품명에는 `[목업]`이 붙고 `is_mock: true`입니다. 실제 사이트를 연동할 때는 각 사이트의 이용약관과 robots 기준을 지키고, 요청량을 제한하며, 캐시를 사용합니다.

## 다음 작업 (Phase 1)

1. Ollama 연동 후 `RequirementsAnalyzer`, `Explainer`를 LLM으로 교체
2. Chroma + 로컬 임베딩으로 `rag/retriever.py` 구현
3. `CompatibilityChecker`를 룰 + RAG 검증으로 교체

## 의존성

버전은 [requirements.txt](requirements.txt)에 고정되어 있습니다.
