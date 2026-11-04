# 커밋 기록

## 기본 정보

- 일시: 2026-11-05 07:46
- 작성자: while
- 브랜치: feature/repo-setup
- 커밋 메시지: `docs(branchs): 커밋 기록을 branchs/commits/ 하위 폴더로 이동`

## 변경 내용

- 이 브랜치의 기록 001, 007, 017, 018을 `Docs/branchs/commits/`로 이동
- README.md, AGENTS.md의 커밋 기록 경로를 `Docs/branchs/commits/`로 수정

## 변경 이유

인수인계 6.2는 커밋 기록을 반드시 `Docs/branchs/commits/` 하위 폴더에 저장하도록 정한다. 기존 기록은 `Docs/branchs/` 바로 아래에 있었다. 인수인계 문서가 갱신된 뒤 다시 읽지 않아 놓쳤다.

## 검증

- `git mv`로 이동해 이력 유지\n- README.md, AGENTS.md의 수정 위치를 `grep`으로 확인

## 남은 작업

- 없음
