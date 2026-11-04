# 커밋 기록

## 기본 정보

- 일시: 2026-11-05 07:15
- 작성자: while
- 브랜치: feature/repo-setup
- 커밋 메시지: `chore(repo): 루트 설정 파일과 에이전트 폴더 추가`

## 변경 내용

- AGENTS.md(SSOT), README, LICENSE, SECURITY.md, .gitattributes, .gitignore
- docker-compose.yml(PostgreSQL), 루트 .env.example
- 에이전트별 폴더 13개(AGENTS.md를 가리키는 안내 파일)

## 변경 이유

인수인계 6.6·6.7이 루트에 필수로 요구하는 파일과 에이전트 폴더를 먼저 갖추기 위해서다. 비밀 정보가 커밋되지 않도록 `.gitignore`와 값 없는 `.env.example`을 두었다.

## 검증

- `git ls-files`에 `.env`, `node_modules`, `.venv`, `target`이 없음을 확인
- `docker compose up`은 루트 `.env`가 없으면 변수 누락 오류로 실패하고, 값을 넣으면 컨테이너가 healthy가 됨을 임시 환경에서 확인 (2026-11-05)
- 에이전트 폴더 13개의 안내 파일은 내용만 확인함 (동작 검증 대상 아님)

## 남은 작업

- 로드맵 Phase 1: Ollama·RAG 연결
