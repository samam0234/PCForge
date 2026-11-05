# 커밋 기록

## 기본 정보

- 일시: 2026-11-05 07:29
- 작성자: while
- 브랜치: feature/frontend
- 커밋 메시지: `docs(frontend): sv 기본 README를 프로젝트 README로 교체`

## 변경 내용

- 현재 상태, 실행, 스크립트, SvelteKit 3 환경 변수 방식, 구조, 배포 어댑터 미정 안내

## 변경 이유

`sv`가 만든 기본 README는 프로젝트와 무관해서 현재 상태, 실행 방법, SvelteKit 3 환경 변수 방식을 담은 문서로 교체했다.

## 검증

- 환경 변수 방식(`src/env.ts`, `$app/env/public`)은 코드와 대조했고 `npm run check`·`build` 통과
- 상태 표의 ✅ 항목은 브라우저에서 확인하지 않았는데도 표기했고, 023번 커밋에서 바로잡음
- `npm run dev`는 적은 그대로 실행하지 않음 (다른 포트로 `vite dev`를 띄워 확인)

## 남은 작업

- 로드맵 Phase 1: Ollama·RAG 연결
