# 커밋 기록

- 일시: 2026-11-05 07:29
- 작성자: while
- 브랜치: feature/repo-setup
- 커밋 메시지: `docs(repo): 루트 README 고도화와 문서 링크 추가`

## 변경 내용

- 현재 상태 표, 아키텍처와 요청 흐름(mermaid), 환경 변수 표, 실행·확인 절차, API 요약, 로드맵, 개발 규칙, 주의사항 추가
- AGENTS.md에 실행 가이드, API, 검증 기록 링크 추가
- DATABASE_URL 호스트를 127.0.0.1로 적도록 안내 (localhost는 Windows에서 DB 연결 실패 확인)

## 검증

- 문서 속 명령과 수치는 임시 환경(PostgreSQL 컨테이너, 로컬 서버)에서 직접 실행해 확인함 (Docs/vaildates/skeleton-validation.md 참고)

## 남은 작업

- 로드맵 Phase 1: Ollama·RAG 연결
