# API 레퍼런스

프론트엔드는 Axum(`:3000`)만 호출합니다. FastAPI(`:8000`)는 Axum이 호출하는 내부용입니다.

## Axum (`http://localhost:3000`)

### `GET /health`

서버와 DB 상태를 반환합니다. DB가 꺼져 있어도 `200`으로 응답하고 `database`만 `down`이 됩니다.

```json
{ "status": "ok", "database": "up" }
```

### `POST /api/recommend`

요구사항을 AI 서버(`POST /agent/run`)로 그대로 전달하고, 응답을 돌려줍니다. 입력 검증은 현재 FastAPI 스키마가 맡습니다. 인증과 기록 저장은 Phase 2에서 추가됩니다.

**요청**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `purpose` | string (1자 이상) | ✅ | 용도: 게이밍, 영상편집, 개발, AI 학습, 사무 등 |
| `budget_krw` | integer (> 0) | ✅ | 예산 (원) |
| `condition` | `"new"` · `"used"` · `"mixed"` | | 기본 `"mixed"` |
| `required_specs` | string[] | | 필수 스펙 (현재 미사용) |
| `priorities` | string[] | | 우선순위 (현재 미사용) |
| `notes` | string | | 자유 입력 (현재 미사용) |

```bash
curl -X POST localhost:3000/api/recommend \
  -H 'content-type: application/json' \
  -d '{"purpose":"게이밍","budget_krw":250000,"condition":"used"}'
```

**응답 `200`** (실제 실행 결과, 목업 데이터)

```json
{
  "recommendations": [
    {
      "product_name": "[목업] 중고 RTX 3060",
      "category": "GPU",
      "price": 200000,
      "site": "중고나라",
      "url": null,
      "specs": { "tdp_w": "170" },
      "is_used": true,
      "is_mock": true,
      "score": 0.2,
      "reason": "예산 대비 가격 기준 임시 점수입니다."
    }
  ],
  "warnings": ["호환성 검증이 아직 구현되지 않았습니다. 구매 전 직접 확인하세요."],
  "explanation": "'게이밍' 용도로 목업 데이터에서 1건을 골랐습니다. 실제 상품 정보가 아닙니다.",
  "steps": [
    "RequirementsAnalyzer: 요구사항 확인",
    "SearchPlanner: 3개 사이트 검색 계획",
    "SiteSearcher: 2건 수집 (목업)",
    "ResultNormalizer: 2건으로 정리",
    "CompatibilityChecker: 검증 미구현 (임시 경고)",
    "RankerAndRecommender: 1건 추천",
    "Explainer: 설명 생성"
  ]
}
```

| 응답 필드 | 설명 |
|-----------|------|
| `recommendations[].score` | 임시 점수. `1 - 가격/예산`이며 높을수록 예산 대비 저렴함 |
| `recommendations[].is_mock` | `true`면 목업 상품 |
| `warnings` | 호환성·주의 경고 |
| `steps` | 에이전트가 실행한 단계 로그 |

**오류**

| 상태 | 의미 |
|------|------|
| `422` | 입력 검증 실패. 본문은 FastAPI의 `detail` 배열을 그대로 전달 |
| `502` | AI 서버에 연결하지 못했거나 서버 오류 `{"error":"AI 서버를 사용할 수 없습니다"}` |

### `GET /api/sessions` · `POST /api/auth/login`

Phase 2 예정이며 현재는 `501`과 `{"error":"아직 구현되지 않았습니다"}`를 반환합니다.

## FastAPI (`http://localhost:8000`)

| 경로 | 설명 |
|------|------|
| `GET /health` | `{"status":"ok"}` |
| `POST /agent/run` | 요청·응답은 위 `/api/recommend`와 동일 |
| `GET /docs` | FastAPI가 자동 생성하는 Swagger UI |

## CORS

Axum은 `FRONTEND_ORIGIN`(기본 `http://localhost:5173`) 한 곳만 허용하고, `GET`·`POST`와 `Content-Type`·`Authorization` 헤더를 허용합니다.
