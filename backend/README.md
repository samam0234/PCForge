# backend (Axum)

PCForge의 메인 백엔드입니다. API 게이트웨이, 인증, DB, AI 서버 호출 오케스트레이션을 맡고, **에이전트·LLM 로직은 갖지 않습니다.** 전체 구조는 [루트 README](../README.md)를 참고하세요.

## 현재 상태

| 엔드포인트 | 상태 |
|------------|------|
| `GET /health` | 서버·DB 상태 |
| `GET /api/catalog` | 기준 시세와 실시간 매물 |
| `POST /api/recommend` | 조건 정리 후 AI 서버로 전달. 회원만 기록 |
| `GET /api/sessions` | 로그인 사용자의 최근 기록 |
| `POST /api/auth/register` · `login` · `logout`, `GET /api/auth/me` | 가입과 로그인 |

요청·응답 형식은 [API 레퍼런스](../Docs/guidance/api-reference.md)에 있습니다.

## 실행

```bash
cp .env.example .env     # DATABASE_URL 비밀번호를 루트 .env의 POSTGRES_PASSWORD와 맞춤
sqlx migrate run         # DB가 떠 있어야 함 (루트에서 docker compose up -d)
cargo run
```

`sqlx-cli`는 `cargo install sqlx-cli --no-default-features --features postgres,rustls`로 설치합니다. 마이그레이션은 서버가 자동으로 적용하지 않습니다.

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 연결 문자열 (**필수**, 없으면 시작 시 종료) | - |
| `BACKEND_PORT` | 수신 포트 | `3000` |
| `AI_SERVER_URL` | FastAPI 주소 | `http://localhost:8000` |
| `FRONTEND_ORIGIN` | CORS 허용 출처 (한 곳) | `http://localhost:5173` |
| `RUST_LOG` | 로그 레벨 | `info,tower_http=debug` |

> `DATABASE_URL`의 호스트는 `localhost`가 아니라 **`127.0.0.1`** 로 적습니다. Windows에서 `localhost`로 두면 DB에 연결하지 못하고 `/health`가 `database: down`을 반환했습니다.

## 구조

```
src/
├── main.rs              설정 읽기, 상태 구성, CORS, 서버 시작
├── error.rs             AppError → HTTP 상태 코드
├── db/mod.rs            지연 연결 풀 (DB가 꺼져 있어도 서버는 뜸)
├── routes/              health, catalog, recommend, sessions, auth
├── catalog.rs           카탈로그 파일 조회와 판매 가능 id
└── services/ai_client.rs  FastAPI 호출
migrations/              0001_init.sql, 0002_auth.sql
```

## 동작 규칙

- **오류 매핑:** 추천 조건이 비었으면 `400`이고 본문은 `{"error":"..."}`입니다. AI 서버가 4xx면 상태 코드와 본문을 그대로 전달하고, 연결 실패나 5xx면 `502`입니다.
- **DB 연결:** 풀은 첫 쿼리 때 연결합니다. 획득 제한 시간은 2초입니다.
- **등급:** 회원 여부는 토큰으로만 정합니다. 비로그인 메모와 회원 전용 필터는 AI 서버로 보내기 전에 제거합니다.

## 개발

```bash
cargo check     # 빠른 컴파일 확인
cargo build
```

테스트 코드는 아직 없습니다.
