from typing import Literal

from pydantic import BaseModel, Field


class Requirements(BaseModel):
    purpose: str = Field(min_length=1, description="용도 (게이밍, 영상편집, 개발, AI 학습, 사무 등)")
    budget_krw: int = Field(gt=0, description="예산 (원)")
    condition: Literal["new", "used", "mixed"] = "mixed"
    required_specs: list[str] = []
    priorities: list[str] = []
    notes: str = ""


class Product(BaseModel):
    product_name: str
    category: str
    price: int
    site: str
    url: str | None = None
    specs: dict[str, str] = {}
    is_used: bool = False
    is_mock: bool = True


class Recommendation(Product):
    score: float
    reason: str


class AgentResult(BaseModel):
    recommendations: list[Recommendation]
    warnings: list[str]
    explanation: str
    steps: list[str]
