# 커밋 기록

## 기본 정보

- 일시: 2026-11-05 07:29
- 작성자: while
- 브랜치: feature/docs
- 커밋 메시지: `docs(guidance): 로컬 환경·API 가이드와 검증 기록 추가`

## 변경 내용

- Docs/guidance/local-setup.md: 준비물, 실행 순서, 초기화, 문제 해결 표
- Docs/guidance/api-reference.md: 실제 실행 결과 기반 요청·응답 예시
- Docs/vaildates/skeleton-validation.md: 확인한 것, 발견한 문제, 확인하지 못한 것

## 변경 이유

실행 방법, API 형식, 검증 결과를 한곳에서 찾을 수 있게 하기 위해서다.

## 검증

- API 예시는 FastAPI `TestClient`로 받은 실제 응답을 사용
- 문제 해결 표 중 localhost 연결 실패, compose 변수 누락, 422, 502, 501은 직접 재현함
- 포트 충돌, CORS 오류, 빈 목록 항목은 동작 원리에 근거한 안내이며 재현하지 않음

## 남은 작업

- 로드맵 Phase 1: Ollama·RAG 연결
