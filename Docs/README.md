# Docs

PCForge의 모든 문서는 이 폴더 아래 용도별 하위 폴더에 둡니다. 새 문서는 아래 표에서 맞는 폴더를 골라 넣습니다. 폴더 구조는 [인수인계 문서](plan/PCForge_인수인계.md) 4장의 규칙입니다.

| 폴더 | 용도 | 현재 문서 |
|------|------|-----------|
| [plan/](plan/) | 초기 기획·로직·DB·배포 계획 | [기획서 v1.2](plan/PCForge_기획서_v1.2.md), [인수인계](plan/PCForge_인수인계.md) |
| [Architecture/](Architecture/) | 시스템·계층·데이터 흐름 아키텍처 | [pcforge_architecture.md](Architecture/pcforge_architecture.md) |
| [branchs/](branchs/) | 브랜치·커밋 기록 (**템플릿 필수**, **commits/ 하위 폴더 필수**) | [커밋 기록](branchs/commits/), [작성법](branchs/README.md) |
| [find_debug/](find_debug/) | 작업·실행 디버깅 일일 기록 | 없음 |
| [guidance/](guidance/) | 기능·실행 가이드 | [local-setup.md](guidance/local-setup.md), [api-reference.md](guidance/api-reference.md) |
| [trainings/](trainings/) | 학습·연구 정리 | 없음 |
| [repeater/](repeater/) | 서버 연결·인프라 장애와 해결 | 없음 |
| [vaildates/](vaildates/) | 검증·체크리스트 | [skeleton-validation.md](vaildates/skeleton-validation.md) |
| [web_management/](web_management/) | 배포 전·배포 시 웹 관리 기록 | 없음 |

폴더 이름의 `branchs`, `vaildates`는 인수인계 문서에 적힌 그대로 쓰는 것이며 오타가 아닙니다.

## 규칙

- **새 문서:** 반드시 위 폴더 중 맞는 곳에 둡니다. 프로젝트 루트에 문서를 방치하지 않습니다.
- **커밋 기록:** 모든 커밋마다 [branchs/commits/](branchs/commits/)에 기록 파일을 만들어 같은 커밋에 넣습니다. `commits/` 하위 폴더는 필수이며 삭제하지 않습니다. 작성법은 [branchs/README.md](branchs/README.md)를 참고하세요.
- **템플릿 보호:** [COMMIT_TEMPLATE.md](branchs/COMMIT_TEMPLATE.md)는 절대 삭제하지 않습니다.
- **빈 폴더:** 문서가 없는 폴더는 `.gitkeep`으로 유지합니다. 첫 문서를 넣을 때 `.gitkeep`은 지워도 됩니다.
