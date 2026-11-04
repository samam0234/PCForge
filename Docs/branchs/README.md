# branchs — 브랜치·커밋 기록

모든 커밋마다 기록 파일을 하나씩 만들어 **같은 커밋, 같은 브랜치**에 함께 넣습니다. 무엇을, 왜 바꿨고 어떻게 확인했는지를 코드와 따로 남기는 용도입니다. 규칙의 원본은 [인수인계 문서](../plan/PCForge_인수인계.md) 6.2입니다.

> [COMMIT_TEMPLATE.md](COMMIT_TEMPLATE.md)는 **절대 삭제하지 않습니다.**

## 파일 이름

```
YYMMDD_HHMM_[id]_[이름]_[브랜치].md
```

| 부분 | 설명 | 예시 |
|------|------|------|
| `YYMMDD_HHMM` | 커밋 시각 | `261105_0729` |
| `[id]` | 3자리 일련번호. 기록이 생길 때마다 하나씩 올림 | `009` |
| `[이름]` | 작성자 | `while` |
| `[브랜치]` | 브랜치 이름. `/`는 `-`로 바꿈 | `feature-docs` |

예: `261105_0729_009_while_feature-docs.md` (`feature/docs` 브랜치의 9번째 기록)

## 작성 방법

1. [COMMIT_TEMPLATE.md](COMMIT_TEMPLATE.md)를 복사해 위 규칙대로 이름을 붙입니다.
2. 아래 항목을 채웁니다.
3. 코드와 **같은 커밋에** 포함해서 커밋합니다.

| 항목 | 내용 |
|------|------|
| 기본 정보 | 일시, 작성자, 브랜치, 커밋 메시지 |
| 변경 내용 | 무엇을 바꿨는지 |
| 변경 이유 | 왜 바꿨는지 |
| 검증 | 어떻게 확인했는지. 확인하지 못한 것은 못했다고 적음 |
| 남은 작업 | 이어서 해야 할 일 |

커밋 메시지는 `type(scope): 한국어 요약` 형식입니다. type과 scope는 영어, 요약은 한국어로 씁니다.

## 병합 기록

병합 기록은 브랜치마다 쓰지 않고, **모든 커밋이 끝난 뒤 총 병합 때 한 번에** 작성합니다. 병합은 사용자 지시가 있을 때만 하며 `--no-ff`로 `develop` → `main` 순서입니다.

## 기록 목록

| id | 브랜치 | 커밋 메시지 |
|----|--------|-------------|
| [001](261105_0715_001_while_feature-repo-setup.md) | `feature/repo-setup` | `chore(repo): 루트 설정 파일과 에이전트 폴더 추가` |
| [002](261105_0715_002_while_feature-docs.md) | `feature/docs` | `docs(plan): 기획서와 인수인계 문서 이동 및 Docs 구조 추가` |
| [003](261105_0715_003_while_feature-backend.md) | `feature/backend` | `feat(backend): Axum 뼈대와 DB 스키마 추가` |
| [004](261105_0715_004_while_feature-ai-server.md) | `feature/ai-server` | `feat(ai-server): FastAPI와 LangGraph 에이전트 뼈대 추가` |
| [005](261105_0715_005_while_feature-frontend.md) | `feature/frontend` | `feat(frontend): SvelteKit 요구사항 폼과 추천 결과 화면 추가` |
| [006](261105_0718_006_while_feature-docs.md) | `feature/docs` | `docs(branchs): 총 병합 기록 추가` (병합 기록) |
| [007](261105_0729_007_while_feature-repo-setup.md) | `feature/repo-setup` | `docs(repo): 루트 README 고도화와 문서 링크 추가` |
| [008](261105_0729_008_while_feature-docs.md) | `feature/docs` | `docs(architecture): 아키텍처 문서에 코드 위치·노드 현황·데이터 모델 추가` |
| [009](261105_0729_009_while_feature-docs.md) | `feature/docs` | `docs(guidance): 로컬 환경·API 가이드와 검증 기록 추가` |
| [010](261105_0729_010_while_feature-backend.md) | `feature/backend` | `fix(backend): 예시 DATABASE_URL 호스트를 127.0.0.1로 변경` |
| [011](261105_0729_011_while_feature-backend.md) | `feature/backend` | `docs(backend): 백엔드 README 추가` |
| [012](261105_0729_012_while_feature-ai-server.md) | `feature/ai-server` | `docs(ai-server): AI 서버 README 추가` |
| [013](261105_0729_013_while_feature-frontend.md) | `feature/frontend` | `docs(frontend): sv 기본 README를 프로젝트 README로 교체` |
| [014](261105_0733_014_while_feature-docs.md) | `feature/docs` | `docs(branchs): Docs 목차와 커밋 기록 작성법 안내 추가` |
| [015](261105_0733_015_while_feature-repo-setup.md) | `feature/repo-setup` | `docs(repo): 루트 README에 Docs 목차와 커밋 기록 작성법 링크 추가` |
| [016](261105_0735_016_while_feature-docs.md) | `feature/docs` | `docs(branchs): 총 병합 기록 추가` (병합 기록) |
| [hil](261105_0739_017_while_feature-repo-setup.md) | `feature/repo-setup` | `docs(branchs): 커밋 기록 001·007을 템플릿 항목에 맞게 보완` |
| [hil](261105_0739_018_while_feature-repo-setup.md) | `feature/repo-setup` | `docs(repo): README 동작 표기를 검증 범위에 맞게 수정` |
| [hil](261105_0741_019_while_feature-docs.md) | `feature/docs` | `docs(branchs): 커밋 기록 002·006·008·009를 템플릿 항목에 맞게 보완` |
| [hil](261105_0739_020_while_feature-backend.md) | `feature/backend` | `docs(branchs): 커밋 기록 003·010·011을 템플릿 항목에 맞게 보완` |
| [hil](261105_0739_021_while_feature-ai-server.md) | `feature/ai-server` | `docs(branchs): 커밋 기록 004·012를 템플릿 항목에 맞게 보완` |
| [hil](261105_0739_022_while_feature-frontend.md) | `feature/frontend` | `docs(branchs): 커밋 기록 005·013을 템플릿 항목에 맞게 보완` |
| [hil](261105_0739_023_while_feature-frontend.md) | `feature/frontend` | `docs(frontend): README 상태 표기를 검증 범위에 맞게 수정` |
| [hil](261105_0741_024_while_feature-docs.md) | `feature/docs` | `docs(branchs): 총 병합 기록 추가` (병합 기록) |

새 기록을 만들 때 이 표에도 한 줄을 추가합니다.
