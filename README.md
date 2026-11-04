# PCForge

용도와 예산, 선호 조건을 입력하면 AI 에이전트가 쇼핑몰과 중고 거래 사이트에서 PC 부품·완제품을 찾아 비교·추천해 주는 사이트입니다.

> **현재 상태: 뼈대 단계.** 7단계 LangGraph 흐름과 계층 간 호출은 동작하지만, 추천 결과는 목업 데이터입니다. LLM, RAG, 실제 검색, 로그인, 기록 저장은 아직 구현되지 않았습니다.

## 구성

| 폴더 | 기술 | 포트 |
|------|------|------|
| [frontend/](frontend/) | SvelteKit (TypeScript) | 5173 |
| [backend/](backend/) | Axum (Rust) | 3000 |
| [ai-server/](ai-server/) | FastAPI, LangGraph, Streamlit | 8000 |
| [docker-compose.yml](docker-compose.yml) | PostgreSQL | 5432 |

## 실행

명령은 프로젝트 루트 기준이며, 터미널을 나눠서 실행합니다. Git Bash 기준입니다.

```bash
# 1. 환경 변수 준비 (값을 수정해서 사용, POSTGRES_PASSWORD와 DATABASE_URL의 비밀번호를 맞춥니다)
cp .env.example .env
cp backend/.env.example backend/.env
cp ai-server/.env.example ai-server/.env
cp frontend/.env.example frontend/.env

# 2. DB 실행 및 스키마 적용
docker compose up -d
cargo install sqlx-cli --no-default-features --features postgres   # 최초 1회
(cd backend && sqlx migrate run)

# 3. AI 서버
cd ai-server
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m uvicorn app.main:app --port 8000

# 4. 백엔드
cd backend && cargo run

# 5. 프론트엔드
cd frontend && npm install && npm run dev
```

AI 로직만 확인하려면 `ai-server`에서 Streamlit을 실행합니다.

```bash
.venv/Scripts/python -m streamlit run streamlit_app.py
```

## 문서

작업 규칙은 [AGENTS.md](AGENTS.md)에서 시작합니다. 기획과 인수인계 문서는 [Docs/plan/](Docs/plan/)에 있습니다.
