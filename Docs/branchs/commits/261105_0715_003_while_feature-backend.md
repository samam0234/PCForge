# 커밋 기록

## 기본 정보

- 일시: 2026-11-05 07:15
- 작성자: while
- 브랜치: feature/backend
- 커밋 메시지: `feat(backend): Axum 뼈대와 DB 스키마 추가`

## 변경 내용

- /health, /api/recommend(FastAPI 전달), 로그인·세션 조회는 501 스텁
- AI 서버 오류 응답 처리(4xx 전달, 그 외 502)
- PostgreSQL 초기 스키마 마이그레이션(5개 테이블)

## 변경 이유

기획서 Phase 2: Axum은 게이트웨이와 오케스트레이션만 맡고 AI 로직은 FastAPI에 둔다. DB 스키마는 기획서 5.3 데이터 모델을 따랐다.

## 검증

- `cargo build` 성공
- 임시 PostgreSQL에 마이그레이션을 적용해 5개 테이블 생성 확인
- 추천 요청 End-to-End 200, 입력 오류 422, AI 서버 종료 시 502, 미구현 라우트 501, 허용 출처 preflight 응답 헤더, DB 종료 시 `/health`가 `database: down` — 모두 직접 실행해 확인 (2026-11-05)

## 남은 작업

- 로드맵 Phase 1: Ollama·RAG 연결
