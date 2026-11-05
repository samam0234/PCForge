# API 레퍼런스

프론트엔드는 Axum(`:3000`)만 호출합니다. FastAPI(`:8000`)는 Axum이 호출하는 내부용입니다. 인증이 필요한 요청은 `Authorization: Bearer <token>`을 붙입니다. 토큰이 없거나 만료되면 비로그인으로 처리하는 목록 조회와, 거절하는 기록 조회를 구분합니다.

오류 본문은 `{"error":"메시지"}`입니다. AI 서버가 4xx로 거절하면 Axum은 그 상태 코드와 본문을 그대로 전달합니다.

## 비로그인과 회원

| 항목 | 비로그인 | 회원 |
|------|----------|------|
| 목록 필터 | 모델, 재질, 색, 소음 제외 11개 | 15개 전부 |
| 한 페이지 | 48 | 96 |
| 담아 두기 | 30 | 120 |
| 추천 건수 | 6 | 12 |
| 호환 메모 검색 | 2건 | 4건 |
| 메모·우선순위 | 요청에서 제거 | 메모 400자, 우선순위는 가격·성능·소음·전력 |
| 추천 기록 | 저장하지 않음 | 저장 후 `session_id`를 돌려줌 |

등급은 토큰으로만 정합니다. 본문의 `access_tier`를 회원이 직접 올려도, Axum이 토큰 기준으로 다시 넣습니다.

## Axum (`http://localhost:3000`)

### `GET /health`

서버와 DB 상태를 반환합니다. DB가 꺼져 있어도 `200`이고 `database`만 `down`입니다.

```json
{ "status": "ok", "database": "up" }
```

### `GET /api/catalog`

`data/catalog/products.json`(기준 시세)과 `data/catalog/live.json`(실시간, 없으면 생략)을 합쳐 거릅니다. 판매가 끝난 상품은 뒤로 보내고, 판매중을 앞에 둡니다.

**쿼리**

| 이름 | 설명 |
|------|------|
| `part_name` | 이름·모델·요약에 포함된 문자열 |
| `purpose` | 용도 |
| `price_min`, `price_max` | 원. 비우면 그 방향 제한 없음 |
| `condition` | `new`, `used`. 비우면 둘 다 |
| `category`, `brand`, `model`, `material`, `form_factor`, `socket`, `shop`, `color`, `noise`, `power`, `grade` | 같은 값만 |
| `source` | `reference`, `naver`, `market` |
| `availability` | `selling`, `sold`, `discontinued`, `stopped`, `upcoming`, `unverified` |
| `offset` | 페이지 시작. 기본 0 |

비로그인이 `model`, `material`, `color`, `noise`를 보내도 무시합니다. 응답의 `locked_filters`가 잠긴 이름입니다.

```bash
curl "localhost:3000/api/catalog?purpose=게이밍&price_max=2000000&availability=selling"
```

**응답 `200`**

| 필드 | 설명 |
|------|------|
| `tier` | `guest` 또는 `member` |
| `total` | 걸러진 전체 건수 |
| `offset`, `limit` | 이번 페이지 |
| `shortlist_limit`, `recommend_limit` | 담기와 추천 상한 |
| `live_count`, `live_fetched_at` | 실시간 파일 건수와 수집 시각 |
| `facets` | 화면 필터에 쓰는 값 묶음 |
| `items` | 상품. `availability`가 닫힌 값이면 화면에서 흐리게 두고 담기에서 뺍니다 |

### `POST /api/recommend`

요청을 정리한 뒤 `POST /agent/run`으로 넘깁니다. 회원 추천만 `search_sessions`와 `recommendations`에 저장합니다.

**요청**

| 필드 | 필수 | 설명 |
|------|------|------|
| `purpose` | ✅ | 1자 이상, 40자까지 |
| `budget_krw` | ✅ | 1원 이상. 5억 원을 넘으면 5억으로 자름 |
| `condition` | | `new`, `used`, `mixed`. 그 외는 `mixed` |
| `priorities` | | 회원만. `가격`, `성능`, `소음`, `전력` |
| `notes` | | 회원만. 400자. 언어 모델이 우선순위를 읽는 메모 |
| `selected_ids` | | 담아 둔 상품 id. 상한을 넘기면 앞부분만, 없거나 판매가 끝난 id는 제거 |
| `part_name`, `category`, `brand`, `shop`, `form_factor`, `socket`, `power`, `grade` | | 카탈로그 필터 |
| `model`, `material`, `color`, `noise` | | 회원만 필터로 적용 |

```bash
curl -X POST localhost:3000/api/recommend \
  -H 'content-type: application/json' \
  -H 'authorization: Bearer TOKEN' \
  -d '{"purpose":"게이밍","budget_krw":2000000,"notes":"소음이 적고 화이트 위주로","priorities":["성능"]}'
```

**응답 `200`**

| 필드 | 설명 |
|------|------|
| `recommendations` | 상품, `score`, `reason`, `url` |
| `warnings` | 호환 메모와 제외 안내. 판매가 끝난 후보를 빼면 맨 앞에 그 건수를 알림 |
| `explanation` | 로컬 모델이 쓴 설명. 모델이 없으면 짧은 요약 |
| `steps` | 노드 로그. 회원 메모가 있으면 `NoteReader`가 들어감 |
| `tier` | `guest` 또는 `member` |
| `session_id` | 회원일 때만 |

**오류**

| 상태 | 의미 |
|------|------|
| `400` | 본문이 객체가 아니거나, 용도가 비었거나, 예산이 1원 미만 |
| `502` | AI 서버에 연결하지 못했거나 서버 오류 |

### `POST /api/auth/register`

`email`, `password`(8자 이상), `name`(1–40자). 성공 시 `token`과 `user`(`id`, `email`, `name`). 토큰은 14일. 이메일이 있으면 `409`.

### `POST /api/auth/login`

`email`, `password`. 실패는 `401`이고 이메일과 비밀번호 오류를 구분하지 않습니다.

### `GET /api/auth/me`

토큰의 사용자. 없으면 `401`.

### `POST /api/auth/logout`

토큰을 지웁니다. 없으면 `401`. 성공은 `{"ok":true}`.

### `GET /api/sessions`

로그인한 사용자의 최근 20개 추천입니다. 각 항목은 `id`, `created_at`, `status`, `purpose`, `budget_krw`, `explanation`, `recommendations`입니다.

## FastAPI (`http://localhost:8000`)

| 경로 | 설명 |
|------|------|
| `GET /health` | `status`, `chroma`, Ollama 모델, `live`, `live_updated_at`, `live_running`, `live_last_error` |
| `POST /agent/run` | 그래프 실행. 등급과 메모 정리는 Axum이 끝낸 뒤의 본문을 기대함 |
| `POST /catalog/refresh` | 네이버 쇼핑 검색을 백그라운드에서 다시 돌림. 키가 없으면 `503`, 이미 돌면 `started: false`. 성공은 `202` |
| `POST /agent/chat` | 상담 이벤트를 NDJSON으로 보냄. Axum `POST /api/chat`이 전달 |
| `GET /docs` | Swagger UI |

상담 요청 필드와 이벤트는 [상담 가이드](assistant.md)에 있습니다.

## CORS

Axum은 `FRONTEND_ORIGIN`(기본 `http://localhost:5173`) 한 곳만 허용하고, `GET`·`POST`와 `Content-Type`·`Authorization` 헤더를 허용합니다.
