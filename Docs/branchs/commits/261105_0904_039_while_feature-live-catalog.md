# 커밋 기록

## 기본 정보

- 일시: 2026-11-05 09:04
- 작성자: while
- 브랜치: feature/live-catalog
- 커밋 메시지: `docs(guidance): 실시간 상품 수집 방법을 추가`

## 변경 내용

- `Docs/guidance/local-setup.md`에 네이버 쇼핑 검색 키, 수집 명령, 갱신 주기를 적는다.
- 단종·판매완료 매물은 연하게 보이고 추천에서 빠지며, `live.json`은 커밋하지 않는다고 적는다.
- `.gitignore`에 Chroma 데이터와 `data/catalog/live.json`을 넣는다.

## 변경 이유

수집은 키가 있어야 돌고, 모은 파일은 기기마다 달라서 저장소에 넣지 않는다. 실행 방법을 로컬 가이드에 남겨야 다음에 같은 방식으로 켤 수 있다.

## 검증

- 가이드의 환경 변수 이름이 `ai-server/.env.example`과 같은지 확인했다.
- `live.json`을 만든 뒤 `git status`에 나오지 않는 것은 샘플 파일을 지우기 전에 gitignore가 적용된 상태로 확인하지 못했다. 경로는 gitignore에 있다.

## 남은 작업

- 네이버 키를 넣은 뒤 한 번 수집해 실제 판매 페이지 링크를 확인한다.
