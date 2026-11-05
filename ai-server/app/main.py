import logging
import threading
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

load_dotenv()

from app.agents.graph import graph
from app.ingest import naver, scheduler
from app.llm import ollama
from app.rag import store
from app.schemas import AgentResult, Requirements

logger = logging.getLogger(__name__)


def _warm_index() -> None:
    try:
        embedder = store.ensure_index()
        logger.info("Chroma 인덱스를 준비했습니다 (%s)", embedder)
    except Exception:
        logger.exception("Chroma 인덱스를 준비하지 못했습니다")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    threading.Thread(target=_warm_index, daemon=True).start()
    scheduler.start_background()
    yield


app = FastAPI(title="PCForge AI Server", version="0.3.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    body = {"status": "ok", "chroma": store.status()}
    body.update(ollama.status())
    body.update(scheduler.status())
    return body


@app.post("/catalog/refresh", status_code=202)
def refresh_catalog() -> dict:
    if not naver.keys():
        raise HTTPException(status_code=503, detail="NAVER_CLIENT_ID / NAVER_CLIENT_SECRET을 ai-server/.env에 넣어 주세요")
    started = not scheduler.status()["live_running"]
    if started:
        threading.Thread(target=scheduler.run_once, daemon=True).start()
    return {"started": started, **scheduler.status()}


@app.post("/agent/run", response_model=AgentResult)
def run_agent(requirements: Requirements) -> dict:
    state = graph.invoke({"requirements": requirements, "steps": []})
    return {
        "recommendations": state["recommendations"],
        "warnings": state["warnings"],
        "explanation": state["explanation"],
        "steps": state["steps"],
    }
