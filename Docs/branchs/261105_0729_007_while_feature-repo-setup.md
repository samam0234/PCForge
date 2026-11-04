# 커밋 기록

## 기본 정보

- 일시: 2026-11-05 07:29
- 작성자: while
- 브랜치: feature/repo-setup
- 커밋 메시지: `docs(repo): 루트 README 고도화와 문서 링크 추가`

## 변경 내용

- 현재 상태 표, 아키텍처와 요청 흐름(mermaid), 환경 변수 표, 실행·확인 절차, API 요약, 로드맵, 개발 규칙, 주의사항 추가
- AGENTS.md에 실행 가이드, API, 검증 기록 링크 추가
- DATABASE_URL 호스트를 127.0.0.1로 적도록 안내 (localhost는 Windows에서 DB 연결 실패 확인)

## 변경 이유

사용자 요청: 문서 업데이트와 README 고도화, 특히 루트 README를 더 고도화한다.

## 검증

- `docker compose up`(변수 누락 시 실패, 값이 있으면 healthy), `sqlx migrate run`, 백엔드 `/health`는 임시 환경에서 실행해 확인
- README에 적은 `cargo run`, `npm run dev`, `uvicorn ... --port 8000`, `curl localhost:8000/health` 등은 적은 그대로 실행하지 않았다. 임시 포트와 빌드된 실행 파일로 대신 확인함
- 이 시점의 README는 브라우저 동작을 확인하지 않았는데도 ✅ 동작으로 표기했고, 018번 커밋에서 바로잡음

## 남은 작업

- 로드맵 Phase 1: Ollama·RAG 연결
