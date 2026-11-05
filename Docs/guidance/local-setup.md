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
| Ollama | 0.40 | 설명과 회원 메모 해석. 꺼져 있으면 짧은 요약과 단어 추출로 넘어감 |

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

### 실시간 상품 수집 (네이버 쇼핑 검색 API)

1. [네이버 개발자 센터](https://developers.naver.com/apps/#/register)에서 애플리케이션을 등록하고 사용 API로 **검색**을 고릅니다.
2. 발급받은 값을 `ai-server/.env`의 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`에 넣습니다. 이 값은 커밋하지 않습니다.
3. AI 서버를 다시 띄우면 `data/catalog/live.json`이 없거나 `LIVE_REFRESH_HOURS`(기본 6시간)보다 오래됐을 때 백그라운드에서 다시 모읍니다.

- 바로 모으기: `cd ai-server && .venv/Scripts/python -m app.ingest.naver` (`--limit 5`로 앞의 5개 모델만 시험)
- 서버에 요청: `POST http://localhost:8000/catalog/refresh` (202, 이미 도는 중이면 `started: false`)
- 상태 확인: `GET http://localhost:8000/health`의 `live`, `live_updated_at`, `live_last_error`
- 한 번 갱신에 카탈로그 모델 수(약 126회)만큼 호출하며, 호출 사이에 0.15초를 쉽니다. 일일 한도는 25,000회입니다.
- 백엔드와 AI 서버는 `products.json`(기준 시세)과 `live.json`(실시간)을 합쳐서 읽고, 파일이 바뀌면 다음 조회에 반영합니다. 수집 결과가 0건이면 이전 `live.json`을 유지합니다.
- 판매 중인 매물만 판매 페이지 링크를 증거로 붙입니다. 단종·판매중단·판매완료는 연하게 보이고 담기와 추천에서 빠집니다. 키가 없으면 이 갱신은 건너뛰고, 그때 기존 `live.json`을 지우지 않습니다.
- 중고·다나와 매물과 재고 재확인은 [카탈로그 가이드](catalog.md)의 스크립트를 씁니다. `live.json`과 `link-cache.json`은 커밋하지 않습니다.

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
| 추천 요청이 `400` | 용도가 비었거나 예산이 1원 미만 | 입력값 확인 |
| 브라우저에서 CORS 오류 | 프론트 주소가 `FRONTEND_ORIGIN`과 다름 | `backend/.env`의 `FRONTEND_ORIGIN` 수정 후 재시작 |
| `127.0.0.1:5173`이 열리지 않음 | 개발 서버가 `localhost`로만 수신 | `http://localhost:5173/` 로 연다 |
| 추천 설명이 짧음 | Ollama가 꺼져 있거나 모델이 없음 | Ollama를 켜고 채팅 모델을 설치. 없어도 추천 목록은 나옴 |
| 추천 목록이 비어 있음 | 예산·필터 안에 판매 가능한 상품이 없음 | 예산 또는 필터를 완화 |
