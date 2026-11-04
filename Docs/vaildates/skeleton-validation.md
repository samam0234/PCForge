# 뼈대 검증 기록

- 검증일: 2026-11-05
- 대상: 뼈대 단계 (`main` 기준)
- 환경: Windows 11, Node 24, Rust 1.98, Python 3.10, Docker 28

## 성공 기준 체크리스트

기획서 7장의 기준입니다. 뼈대 단계에서는 목업과 규칙 기반 구현이라 대부분 미충족입니다.

- [ ] 요구사항 입력 시 합리적인 맞춤 추천 목록이 생성됨 (호환성 경고 포함) — 목업 결과, 호환성 검증 미구현
- [ ] Streamlit에서 에이전트 중간 과정과 최종 결과가 보임 — 자동 테스트로 예외 없음만 확인, 실제 화면은 미확인
- [ ] 로그인 후 개인 검색·추천 기록 조회 가능 — 미구현
- [ ] 전체 스택(SvelteKit → Axum → FastAPI → PostgreSQL + 로컬 LLM) 동작 — LLM 미연동, DB는 연결만 확인(저장 없음)
- [x] LangGraph 멀티스텝 워크플로우가 실제로 실행됨 — 7개 노드 모두 실행 (규칙 기반)
- [ ] Vibe Coding으로 빠르게 반복 가능한 구조 — 판단 보류
- [ ] 기본 신품/중고 믹스 추천 및 설명 가능 — 믹스 로직과 설명 미구현

## 확인한 것

| 항목 | 방법 | 결과 |
|------|------|------|
| 프론트 타입 체크 | `npm run check` | 오류 0, 경고 0 |
| 프론트 빌드 | `npm run build` | 성공 (adapter-auto는 배포 환경 미감지 안내만 출력) |
| 백엔드 빌드 | `cargo build` | 성공 |
| 마이그레이션 | `sqlx migrate run` (임시 PostgreSQL 17) | 5개 테이블 생성 |
| `docker compose` | 루트 `.env` 없이 실행 | 변수 누락 오류로 실패 (의도한 동작) |
| `docker compose` | 루트 `.env` 작성 후 `up --wait` | 컨테이너 healthy |
| 추천 End-to-End | 백엔드 → AI 서버 `POST /api/recommend` | 200, 7단계 실행, 예산 초과 상품 제외 |
| 입력 오류 | 빈 용도, 음수 예산 | 422 |
| AI 서버 다운 | AI 서버 종료 후 추천 요청 | 502 |
| 미구현 API | `/api/sessions`, `/api/auth/login` | 501 |
| CORS | 허용 출처로 preflight | `access-control-allow-origin` 반환 |
| DB 다운 | 컨테이너 종료 후 `/health` | `database: down`, 서버는 유지 |
| Streamlit | `AppTest`로 실행 후 버튼 클릭 | 예외 0 |
| 프론트 페이지 | dev 서버 응답 확인 | 200, 제목·버튼 문구 포함 |

## 발견한 문제

| 문제 | 원인 | 조치 |
|------|------|------|
| `DATABASE_URL`을 `localhost`로 쓰면 `/health`가 `database: down` | Windows에서 `localhost` 연결 실패 (`127.0.0.1`은 정상). 정확한 원인은 미확인 | 예시 파일과 문서를 `127.0.0.1`로 수정 |
| SvelteKit 3에서 `$env/dynamic/public`이 없음 | 환경 변수 방식이 `src/env.ts` + `$app/env/public`으로 바뀜 | `src/env.ts` 추가, 임포트 수정 |

`sqlx-cli`는 `localhost`로도 연결됐지만, 백엔드는 실패했습니다. 두 도구의 동작 차이는 따로 조사하지 않았습니다.

## 확인하지 못한 것

- 브라우저에서 폼을 직접 눌러 추천 카드가 그려지는지 (페이지 응답과 CORS만 확인)
- Streamlit 실제 화면 (자동 테스트만 수행)
- 로컬 LLM, RAG, 실제 사이트 검색 (미구현)
- Linux, macOS 환경에서의 실행 (Windows에서만 확인)
- `npm audit` low 등급 4건 (강제 수정이 호환성을 깨뜨릴 수 있어 적용하지 않음)
