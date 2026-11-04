# 커밋 기록

## 기본 정보

- 일시: 2026-11-05 07:15
- 작성자: while
- 브랜치: feature/ai-server
- 커밋 메시지: `feat(ai-server): FastAPI와 LangGraph 에이전트 뼈대 추가`

## 변경 내용

- 7개 노드 LangGraph 흐름(규칙 기반 임시 구현, 목업 검색)
- /health, /agent/run, Streamlit MVP
- LLM·RAG·호환성 검증은 아직 미구현

## 변경 이유

기획서 Phase 1: LLM과 RAG를 붙이기 전에 LangGraph 흐름과 입출력 형식을 먼저 확정해 뼈대부터 검증한다.

## 검증

- 7개 노드가 모두 실행되고 `steps`에 7줄이 기록됨, 예산 이하 상품만 남음을 직접 실행해 확인
- Streamlit은 `AppTest`로 실행해 예외 없음만 확인함 (실제 화면은 확인하지 못함)
- `/health`, `/agent/run`은 백엔드를 거쳐 호출해 200 확인

## 남은 작업

- 로드맵 Phase 1: Ollama·RAG 연결
