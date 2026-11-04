# 병합 기록 (총 병합)

- 일시: 2026-11-05 07:18
- 작성자: while
- 지시: 사용자 명시적 요청. 모든 브랜치 커밋을 마친 뒤 develop 병합, main 병합, 두 브랜치 푸시

## develop 병합 (--no-ff)

| 브랜치 | 범위 |
|--------|------|
| feature/repo-setup | 루트 설정 파일, 에이전트 폴더 |
| feature/docs | Docs 구조, 기획·인수인계 문서 이동, 병합 기록 |
| feature/backend | Axum 뼈대, DB 스키마 |
| feature/ai-server | FastAPI, LangGraph 뼈대, Streamlit |
| feature/frontend | SvelteKit 폼과 결과 화면 |

## main 병합

- develop을 --no-ff로 main에 병합

## 브랜치 운영

- 브랜치는 위 5개로 고정하고 작업 영역별로 재사용한다. 영역별 신규 브랜치를 늘리지 않는다.
- 병합은 모든 커밋이 끝난 뒤 한 번에 한다.
