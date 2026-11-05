# 커밋 기록

## 기본 정보

- 일시: 2026-11-05 07:29
- 작성자: while
- 브랜치: feature/backend
- 커밋 메시지: `fix(backend): 예시 DATABASE_URL 호스트를 127.0.0.1로 변경`

## 변경 내용

- localhost로 두면 Windows에서 백엔드가 DB에 연결하지 못하고 /health가 database: down 반환
- 127.0.0.1로 바꾸면 정상 연결됨을 확인

## 변경 이유

README 절차를 따라 해 보다가 `DATABASE_URL`을 `localhost`로 두면 백엔드가 DB에 연결하지 못하고 `/health`가 `database: down`을 반환하는 것을 발견했다.

## 검증

- `localhost`는 3회 모두 `database: down`, `127.0.0.1`은 3회 모두 `up` (임시 PostgreSQL, 2026-11-05)
- `AI_SERVER_URL`은 `localhost`, `127.0.0.1` 모두 추천 요청 200
- 원인은 확인하지 못함 (`sqlx-cli`는 `localhost`로도 연결됨)

## 남은 작업

- 로드맵 Phase 1: Ollama·RAG 연결
