# 커밋 기록

- 일시: 2026-11-05 07:29
- 작성자: while
- 브랜치: feature/backend
- 커밋 메시지: `fix(backend): 예시 DATABASE_URL 호스트를 127.0.0.1로 변경`

## 변경 내용

- localhost로 두면 Windows에서 백엔드가 DB에 연결하지 못하고 /health가 database: down 반환
- 127.0.0.1로 바꾸면 정상 연결됨을 확인

## 검증

- 문서 속 명령과 수치는 임시 환경(PostgreSQL 컨테이너, 로컬 서버)에서 직접 실행해 확인함 (Docs/vaildates/skeleton-validation.md 참고)

## 남은 작업

- 로드맵 Phase 1: Ollama·RAG 연결
