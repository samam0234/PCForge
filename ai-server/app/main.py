from dotenv import load_dotenv
from fastapi import FastAPI

from app.agents.graph import graph
from app.schemas import AgentResult, Requirements

load_dotenv()

app = FastAPI(title="PCForge AI Server", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/agent/run", response_model=AgentResult)
def run_agent(requirements: Requirements) -> dict:
    state = graph.invoke({"requirements": requirements, "steps": []})
    return {
        "recommendations": state["recommendations"],
        "warnings": state["warnings"],
        "explanation": state["explanation"],
        "steps": state["steps"],
    }
