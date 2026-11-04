# 커밋 기록

- 일시: 2026-11-05 07:29
- 작성자: while
- 브랜치: feature/docs
- 커밋 메시지: `docs(architecture): 아키텍처 문서에 코드 위치·노드 현황·데이터 모델 추가`

## 변경 내용

- 코드 위치 표, 노드별 현재 동작과 교체 계획, 테이블 관계와 제약 정리
- 미정 사항(LLM 모델, 인증 방식, 벡터 스토어) 명시

## 검증

- 문서 속 명령과 수치는 임시 환경(PostgreSQL 컨테이너, 로컬 서버)에서 직접 실행해 확인함 (Docs/vaildates/skeleton-validation.md 참고)

## 남은 작업

- 로드맵 Phase 1: Ollama·RAG 연결
