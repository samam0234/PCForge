# PCForge AGENTS.md (SSOT)

모든 에이전트의 공통 진입점입니다. 작업을 시작하기 전에 아래 문서를 읽습니다.

- 상세 규칙과 인수인계: [Docs/plan/PCForge_인수인계.md](Docs/plan/PCForge_인수인계.md)
- 기획서: [Docs/plan/PCForge_기획서_v1.2.md](Docs/plan/PCForge_기획서_v1.2.md)
- 아키텍처: [Docs/Architecture/pcforge_architecture.md](Docs/Architecture/pcforge_architecture.md)
- 실행 방법과 문제 해결: [Docs/guidance/local-setup.md](Docs/guidance/local-setup.md)
- API 형식: [Docs/guidance/api-reference.md](Docs/guidance/api-reference.md)
- 카탈로그와 수집 한계: [Docs/guidance/catalog.md](Docs/guidance/catalog.md)
- 검증 기록: [Docs/vaildates/catalog-llm-validation.md](Docs/vaildates/catalog-llm-validation.md)

규칙의 원본은 인수인계 문서입니다. 에이전트별 파일(`.Claude/CLAUDE.md` 등)은 이 파일을 가리키기만 하며, 규칙을 중복해서 쓰지 않습니다.

## 핵심 규칙 찾아보기

| 주제 | 인수인계 문서 위치 |
|------|-------------------|
| 계층별 역할 분담 | 3장 |
| 폴더 구조와 Docs 용도 | 4장 |
| 커밋 메시지 형식 `type(scope): 한국어 요약` | 6.1 |
| 커밋 기록 문서화 (`Docs/branchs/commits/`, 하위 폴더 필수) | 6.2 |
| 브랜치 전략 (`feature/*`, `--no-ff`) | 6.3 |
| push·병합·삭제·덮어쓰기 사전 확인 | 6.4 |
