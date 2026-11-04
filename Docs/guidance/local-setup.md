# 로컬 환경 가이드

설치부터 실행, 자주 만나는 문제까지 정리한 문서입니다. 요약은 루트 [README](../../README.md)에 있습니다.

## 1. 준비물

| 도구 | 확인한 버전 | 비고 |
|------|-------------|------|
| Node.js / npm | 24.x / 11.x | SvelteKit 3 |
| Rust / cargo | 1.98 | edition 2024 |
| Python | 3.10 | AI 서버 가상환경 |
| Docker | 28.x | PostgreSQL 17 컨테이너 |
| sqlx-cli | 0.9 | 마이그레이션용 (`cargo install`) |
| Ollama | 0.40 | Phase 1에서 연결 예정, 지금은 불필요 |

## 2. 환경 변수

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp ai-server/.env.example ai-server/.env
cp frontend/.env.example frontend/.env
```

- 루트 `.env`는 `docker-compose.yml`이 읽습니다. 값이 비어 있으면 compose가 실행되지 않습니다.
- `backend/.env`의 `DATABASE_URL`은 **필수**입니다. 없으면 백엔드가 시작할 때 종료됩니다.
- `DATABASE_URL`의 비밀번호는 루트 `.env`의 `POSTGRES_PASSWORD`와 같아야 합니다.
- `DATABASE_URL`의 호스트는 `127.0.0.1`을 씁니다. (아래 문제 해결 참고)

## 3. 실행 순서

1. **DB:** `docker compose up -d --wait`
2. **스키마:** `cd backend && sqlx migrate run`
3. **AI 서버:** `cd ai-server && .venv/Scripts/python -m uvicorn app.main:app --port 8000`
4. **백엔드:** `cd backend && cargo run`
5. **프론트엔드:** `cd frontend && npm run dev`

AI 서버와 백엔드는 서로 독립적으로 뜹니다. 추천 요청을 보낼 때 AI 서버가 꺼져 있으면 `502`가 반환됩니다.

## 4. 종료와 초기화

```bash
docker compose down        # 컨테이너 종료 (데이터 유지)
docker compose down -v     # 컨테이너와 DB 데이터까지 삭제
```

`down -v`는 DB 데이터를 지우므로 필요할 때만 사용합니다. 지운 뒤에는 `sqlx migrate run`을 다시 실행해야 합니다.

## 5. 문제 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| `/health`가 `database: down` | `DATABASE_URL`을 `localhost`로 적음 (Windows에서 연결 실패 확인) | 호스트를 `127.0.0.1`로 변경 |
| `/health`가 `database: down` | DB 컨테이너가 꺼져 있거나 비밀번호·포트 불일치 | `docker compose ps`, `.env` 값 확인 |
| 백엔드가 시작 직후 종료 | `DATABASE_URL` 미설정 | `backend/.env` 작성 |
| `docker compose up`이 변수 오류로 실패 | 루트 `.env` 없음 | `cp .env.example .env` 후 값 입력 |
| 5432 포트 충돌 | 다른 PostgreSQL 사용 중 | 루트 `.env`의 `POSTGRES_PORT`와 `DATABASE_URL` 포트를 함께 변경 |
| 추천 요청이 `502` | AI 서버가 꺼져 있음 | AI 서버 실행, `AI_SERVER_URL` 확인 |
| 추천 요청이 `422` | 용도가 비었거나 예산이 0 이하 | 입력값 확인 |
| 브라우저에서 CORS 오류 | 프론트 주소가 `FRONTEND_ORIGIN`과 다름 | `backend/.env`의 `FRONTEND_ORIGIN` 수정 후 재시작 |
| 추천 목록이 비어 있음 | 예산 이하 목업 상품이 없음 (정상) | 예산을 높여 다시 시도 |
