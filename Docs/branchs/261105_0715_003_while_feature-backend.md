# 커밋 기록

- 일시: 2026-11-05 07:15
- 작성자: while
- 브랜치: feature/backend
- 커밋 메시지: `feat(backend): Axum 뼈대와 DB 스키마 추가`

## 변경 내용

- /health, /api/recommend(FastAPI 전달), 로그인·세션 조회는 501 스텁
- AI 서버 오류 응답 처리(4xx 전달, 그 외 502)
- PostgreSQL 초기 스키마 마이그레이션(5개 테이블)

## 검증

- 프론트 타입 체크·빌드, 백엔드 빌드, 임시 서버 기동 후 추천 요청 End-to-End 확인 (2026-11-05)

## 남은 작업

- 로드맵 Phase 1: Ollama·RAG 연결
