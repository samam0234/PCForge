# frontend (SvelteKit)

PCForge의 사용자 인터페이스입니다. 폼, 결과 카드, 화면 상태만 맡고, **DB나 AI 서버를 직접 호출하지 않으며** Axum 백엔드만 호출합니다. 전체 구조는 [루트 README](../README.md)를 참고하세요.

## 현재 상태

| 기능 | 상태 |
|------|------|
| 목록, 예산, 재고, 담기 | 동작. 예산 전체와 판매완료 표시는 화면에서 확인 |
| 추천 결과, 경고, 설명 | 동작. 메모를 넣은 추천 버튼은 다시 눌러 보지 않음 |
| 로그인, 기록, 안내 글 | 동작 |
| 스타일 | 목록·글 화면에 적용 |

## 실행

```bash
cp .env.example .env     # 선택: 기본값이 http://localhost:3000
npm install
npm run dev              # http://localhost:5173
```

백엔드(`:3000`)와 AI 서버(`:8000`)가 떠 있어야 추천 요청이 동작합니다. 꺼져 있으면 화면에 오류 메시지가 표시됩니다.

## 스크립트

| 명령 | 설명 |
|------|------|
| `npm run dev` | 개발 서버 |
| `npm run check` | 타입·Svelte 검사 |
| `npm run build` | 프로덕션 빌드 |
| `npm run preview` | 빌드 결과 미리보기 |

## 환경 변수

SvelteKit 3 방식으로 [src/env.ts](src/env.ts)에 정의하고, 코드에서는 `$app/env/public`으로 읽습니다. (`$env/dynamic/public`은 쓸 수 없음)

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `PUBLIC_API_BASE_URL` | Axum 백엔드 주소 | `http://localhost:3000` |

## 구조

```
src/
├── env.ts
├── lib/api.ts                   Axum 호출과 응답 타입
├── lib/session.svelte.ts        로그인 상태
├── lib/journal.ts               안내 글
├── components/
│   ├── CatalogDesk.svelte       목록, 필터, 담기
│   ├── RequirementForm.svelte   추천 조건
│   └── RecommendationCard.svelte 추천 카드
└── routes/
    ├── +page.svelte             목록과 추천
    ├── login/                   가입·로그인
    ├── history/                 내 기록
    └── journal/                 안내 글
```

- Svelte 5 룬 모드(`$state`, `$props`)를 사용합니다.
- `#lib/*`는 `src/lib/*`의 임포트 별칭입니다. 타입스크립트에서는 확장자를 붙여 `#lib/api.ts`로 임포트합니다.

## 배포

`adapter-auto`가 설정되어 있지만 배포 환경은 아직 정하지 않았습니다. 빌드 시 "지원되는 프로덕션 환경을 찾지 못했다"는 안내가 나오는 것은 이 때문입니다. 배포 대상이 정해지면 해당 어댑터로 교체합니다.
