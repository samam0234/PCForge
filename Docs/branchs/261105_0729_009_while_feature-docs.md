# 커밋 기록

- 일시: 2026-11-05 07:29
- 작성자: while
- 브랜치: feature/docs
- 커밋 메시지: `docs(guidance): 로컬 환경·API 가이드와 검증 기록 추가`

## 변경 내용

- Docs/guidance/local-setup.md: 준비물, 실행 순서, 초기화, 문제 해결 표
- Docs/guidance/api-reference.md: 실제 실행 결과 기반 요청·응답 예시
- Docs/vaildates/skeleton-validation.md: 확인한 것, 발견한 문제, 확인하지 못한 것

## 검증

- 문서 속 명령과 수치는 임시 환경(PostgreSQL 컨테이너, 로컬 서버)에서 직접 실행해 확인함 (Docs/vaildates/skeleton-validation.md 참고)

## 남은 작업

- 로드맵 Phase 1: Ollama·RAG 연결
