# 카탈로그와 추천

화면의 목록과 추천은 두 JSON을 합쳐 읽습니다. 백엔드와 AI 서버 모두 파일이 바뀌면 다음 조회에서 다시 읽습니다.

| 파일 | 역할 | 커밋 |
|------|------|------|
| `data/catalog/products.json` | 기준 시세. `source`는 `reference` | 함 |
| `data/catalog/live.json` | 판매 페이지가 있는 실시간 매물 | 하지 않음 |
| `data/catalog/link-cache.json` | 링크 수집 중간 캐시 | 하지 않음 |

기준 시세는 주소가 없어도 추천에 넣을 수 있습니다. `source`가 `naver` 또는 `market`인 행은 `availability`가 `selling`이고 `url`이 있을 때만 담기와 추천에 들어갑니다.

## 판매 상태

| 값 | 화면 | 담기·추천 |
|----|------|-----------|
| `selling` | 판매중 | 포함 |
| `reference` | 기준 시세 | 포함 |
| `sold` | 판매완료, 흐림 | 제외 |
| `discontinued` | 단종, 흐림 | 제외 |
| `stopped` | 판매중단, 흐림 | 제외 |
| `upcoming` | 출시 전, 흐림 | 제외 |
| `unverified` | 확인 못 함, 흐림 | 제외 |

상태 값은 판매 페이지의 공개 표시만 사용합니다. 근거 없이 판매완료로 바꾸지 않습니다. 다나와는 상품 정보 페이지의 단종·판매중단 문구와 최저가를 보고, 중고 페이지는 schema.org 재고 표시를 봅니다. `404`·`410`은 판매완료로 둡니다.

## 수집

허용된 페이지만 가져옵니다. `robots.txt`가 막는 경로, 다나와 `/bridge/`·`/list/ajax/`·`/info/ajax/`, 네이버 쇼핑 HTML 검색, `api.bunjang.co.kr`, 11번가·쿠팡 상품 페이지 직접 요청은 하지 않습니다. 허용된 페이지에 공개된 상품 주소를 저장하는 것은 가능합니다. 없는 상품을 만들어 넣지 않습니다.

AI 서버에서 실행합니다.

```bash
cd ai-server
.venv/Scripts/python scripts/collect_stock.py           # 중고나라·당근·다나와를 다시 모아 live.json에 씀
.venv/Scripts/python scripts/collect_stock.py --resume  # 기존 live.json을 이어 받음
.venv/Scripts/python scripts/collect_stock.py --fill    # 있는 파일에 다나와·중고나라를 더함
.venv/Scripts/python scripts/recheck_stock.py           # 아직 확인하지 않은 판매 페이지의 상태를 다시 읽음
.venv/Scripts/python scripts/recheck_stock.py --daangn-more
.venv/Scripts/python scripts/build_catalog.py           # 기준 시세 재생성. 이미 있는 url은 유지
```

`scripts/_probe/`는 상태를 구경하는 스크립트입니다. 카탈로그를 쓰지 않으며, 그 출력 JSON·텍스트는 커밋하지 않습니다.

네이버 쇼핑은 Open API만 사용합니다. `NAVER_CLIENT_ID`와 `NAVER_CLIENT_SECRET`이 비어 있으면 갱신을 건너뛰고, 그때 `live.json`을 비우지 않습니다. 키가 있을 때의 절차는 [로컬 환경 가이드](local-setup.md)에 있습니다.

당근은 요청을 빠르게 반복하면 막힙니다. 재확인은 간격을 두고 한 줄로 진행하고, 연속으로 거절되면 멈춥니다.

## 추천에서 메모가 하는 일

회원 메모는 `NoteReader`가 읽습니다. Ollama가 `가격`, `성능`, `소음`, `전력`만 JSON으로 고르고, 모델이 없거나 응답을 읽지 못하면 메모 안의 같은 단어로 대체합니다. 이미 고른 우선순위는 유지하고, 메모에서 새로 나온 기준만 뒤에 붙입니다.

메모의 색 이름(화이트, 흰색, 블랙, 핑크)은 색 필터로 넣지 않습니다. 실시간 매물 대부분이 색이 비어 있어, 색을 조건으로 고정하면 후보가 사라집니다. 상품명에 그 단어가 있을 때만 점수를 올립니다.

비로그인 메모와 우선순위는 Axum이 AI 서버로 보내기 전에 제거합니다.
