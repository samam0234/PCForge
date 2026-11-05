# branchs — 브랜치·커밋 기록

모든 커밋마다 기록 파일을 하나씩 만들어 **같은 커밋, 같은 브랜치**에 함께 넣습니다. 무엇을, 왜 바꿨고 어떻게 확인했는지를 코드와 따로 남기는 용도입니다. 규칙의 원본은 [인수인계 문서](../plan/PCForge_인수인계.md) 6.2입니다.

> [COMMIT_TEMPLATE.md](COMMIT_TEMPLATE.md)는 **절대 삭제하지 않습니다.**
>
> 기록 파일은 반드시 **`Docs/branchs/commits/` 하위 폴더**에 저장합니다. 이 폴더도 필수이며 삭제하지 않습니다.

## 파일 이름

```
Docs/branchs/commits/YYMMDD_HHMM_[id]_[이름]_[브랜치].md
```

| 부분 | 설명 | 예시 |
|------|------|------|
| `YYMMDD_HHMM` | 커밋 시각 | `261105_0729` |
| `[id]` | 3자리 일련번호. 기록이 생길 때마다 하나씩 올림 | `009` |
| `[이름]` | 작성자 | `while` |
| `[브랜치]` | 브랜치 이름. `/`는 `-`로 바꿈 | `feature-docs` |

예: `261105_0729_009_while_feature-docs.md` (`feature/docs` 브랜치의 9번째 기록)

## 작성 방법

1. [COMMIT_TEMPLATE.md](COMMIT_TEMPLATE.md)를 복사해 위 규칙대로 이름을 붙이고 `commits/` 폴더에 둡니다.
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
| [001](commits/261105_0715_001_while_feature-repo-setup.md) | `feature/repo-setup` | `chore(repo): 루트 설정 파일과 에이전트 폴더 추가` |
| [002](commits/261105_0715_002_while_feature-docs.md) | `feature/docs` | `docs(plan): 기획서와 인수인계 문서 이동 및 Docs 구조 추가` |
| [003](commits/261105_0715_003_while_feature-backend.md) | `feature/backend` | `feat(backend): Axum 뼈대와 DB 스키마 추가` |
| [004](commits/261105_0715_004_while_feature-ai-server.md) | `feature/ai-server` | `feat(ai-server): FastAPI와 LangGraph 에이전트 뼈대 추가` |
| [005](commits/261105_0715_005_while_feature-frontend.md) | `feature/frontend` | `feat(frontend): SvelteKit 요구사항 폼과 추천 결과 화면 추가` |
| [006](commits/261105_0718_006_while_feature-docs.md) | `feature/docs` | `docs(branchs): 총 병합 기록 추가` (병합 기록) |
| [007](commits/261105_0729_007_while_feature-repo-setup.md) | `feature/repo-setup` | `docs(repo): 루트 README 고도화와 문서 링크 추가` |
| [008](commits/261105_0729_008_while_feature-docs.md) | `feature/docs` | `docs(architecture): 아키텍처 문서에 코드 위치·노드 현황·데이터 모델 추가` |
| [009](commits/261105_0729_009_while_feature-docs.md) | `feature/docs` | `docs(guidance): 로컬 환경·API 가이드와 검증 기록 추가` |
| [010](commits/261105_0729_010_while_feature-backend.md) | `feature/backend` | `fix(backend): 예시 DATABASE_URL 호스트를 127.0.0.1로 변경` |
| [011](commits/261105_0729_011_while_feature-backend.md) | `feature/backend` | `docs(backend): 백엔드 README 추가` |
| [012](commits/261105_0729_012_while_feature-ai-server.md) | `feature/ai-server` | `docs(ai-server): AI 서버 README 추가` |
| [013](commits/261105_0729_013_while_feature-frontend.md) | `feature/frontend` | `docs(frontend): sv 기본 README를 프로젝트 README로 교체` |
| [014](commits/261105_0733_014_while_feature-docs.md) | `feature/docs` | `docs(branchs): Docs 목차와 커밋 기록 작성법 안내 추가` |
| [015](commits/261105_0733_015_while_feature-repo-setup.md) | `feature/repo-setup` | `docs(repo): 루트 README에 Docs 목차와 커밋 기록 작성법 링크 추가` |
| [016](commits/261105_0735_016_while_feature-docs.md) | `feature/docs` | `docs(branchs): 총 병합 기록 추가` (병합 기록) |
| [017](commits/261105_0739_017_while_feature-repo-setup.md) | `feature/repo-setup` | `docs(branchs): 커밋 기록 001·007을 템플릿 항목에 맞게 보완` |
| [018](commits/261105_0739_018_while_feature-repo-setup.md) | `feature/repo-setup` | `docs(repo): README 동작 표기를 검증 범위에 맞게 수정` |
| [019](commits/261105_0741_019_while_feature-docs.md) | `feature/docs` | `docs(branchs): 커밋 기록 002·006·008·009를 템플릿 항목에 맞게 보완` |
| [020](commits/261105_0739_020_while_feature-backend.md) | `feature/backend` | `docs(branchs): 커밋 기록 003·010·011을 템플릿 항목에 맞게 보완` |
| [021](commits/261105_0739_021_while_feature-ai-server.md) | `feature/ai-server` | `docs(branchs): 커밋 기록 004·012를 템플릿 항목에 맞게 보완` |
| [022](commits/261105_0739_022_while_feature-frontend.md) | `feature/frontend` | `docs(branchs): 커밋 기록 005·013을 템플릿 항목에 맞게 보완` |
| [023](commits/261105_0739_023_while_feature-frontend.md) | `feature/frontend` | `docs(frontend): README 상태 표기를 검증 범위에 맞게 수정` |
| [024](commits/261105_0741_024_while_feature-docs.md) | `feature/docs` | `docs(branchs): 총 병합 기록 추가` (병합 기록) |
| [025](commits/261105_0746_025_while_feature-repo-setup.md) | `feature/repo-setup` | `docs(branchs): 커밋 기록을 branchs/commits/ 하위 폴더로 이동` |
| [026](commits/261105_0745_026_while_feature-docs.md) | `feature/docs` | `docs(plan): 갱신된 인수인계 문서 반영 (commits 하위 폴더, 모델 목록)` |
| [027](commits/261105_0746_027_while_feature-docs.md) | `feature/docs` | `docs(branchs): 커밋 기록을 branchs/commits/ 하위 폴더로 이동` |
| [028](commits/261105_0746_028_while_feature-backend.md) | `feature/backend` | `docs(branchs): 커밋 기록을 branchs/commits/ 하위 폴더로 이동` |
| [029](commits/261105_0746_029_while_feature-ai-server.md) | `feature/ai-server` | `docs(branchs): 커밋 기록을 branchs/commits/ 하위 폴더로 이동` |
| [030](commits/261105_0746_030_while_feature-ai-server.md) | `feature/ai-server` | `chore(ai-server): 예시 OLLAMA_MODEL을 인수인계 문서의 추천 모델로 변경` |
| [031](commits/261105_0746_031_while_feature-frontend.md) | `feature/frontend` | `docs(branchs): 커밋 기록을 branchs/commits/ 하위 폴더로 이동` |
| [032](commits/261105_0747_032_while_feature-docs.md) | `feature/docs` | `docs(branchs): 총 병합 기록 추가` (병합 기록) |
| [033](commits/261105_0748_033_while_feature-repo-setup.md) | `feature/repo-setup` | `docs(branchs): 누락된 커밋 기록을 branchs/commits/ 하위 폴더로 이동` |
| [034](commits/261105_0748_034_while_feature-backend.md) | `feature/backend` | `docs(branchs): 누락된 커밋 기록을 branchs/commits/ 하위 폴더로 이동` |
| [035](commits/261105_0900_035_while_feature-live-catalog.md) | `feature/live-catalog` | `feat(data): 부품 기준 카탈로그와 호환 메모를 추가` |
| [036](commits/261105_0901_036_while_feature-live-catalog.md) | `feature/live-catalog` | `feat(ai-server): 판매 링크 수집과 로컬 추천을 연결` |
| [037](commits/261105_0902_037_while_feature-live-catalog.md) | `feature/live-catalog` | `feat(backend): 로그인과 판매 상태 카탈로그 API를 추가` |
| [038](commits/261105_0903_038_while_feature-live-catalog.md) | `feature/live-catalog` | `feat(frontend): 판매 페이지 증거와 단종 표시를 추가` |

새 기록을 만들 때 이 표에도 한 줄을 추가합니다.
