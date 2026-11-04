# 커밋 기록

## 기본 정보

- 일시: 2026-11-05 07:29
- 작성자: while
- 브랜치: feature/ai-server
- 커밋 메시지: `docs(ai-server): AI 서버 README 추가`

## 변경 내용

- 실행, 엔드포인트, 구조, 에이전트 흐름, 목업 검색 주의, 다음 작업 정리
- .env의 포트·Ollama 변수가 아직 코드에서 쓰이지 않음을 명시

## 변경 이유

AI 서버를 처음 보는 사람이 실행 방법, 구조, 아직 연결되지 않은 부분을 알 수 있어야 한다.

## 검증

- `.env`의 `AI_SERVER_PORT`, `OLLAMA_*`, `EMBEDDING_MODEL`을 코드가 읽지 않음을 소스 검색으로 확인 (가상환경 제외)
- 엔드포인트와 구조는 코드와 대조
- README의 실행 명령은 적은 그대로 실행하지 않음 (uvicorn은 다른 포트로, Streamlit은 `AppTest`로 확인)

## 남은 작업

- 로드맵 Phase 1: Ollama·RAG 연결
