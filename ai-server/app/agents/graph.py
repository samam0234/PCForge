"""PCForge LangGraph 에이전트 뼈대.

노드 7개의 흐름은 실제로 실행되지만, LLM·RAG·실제 검색은 아직 연결되지 않았다.
각 노드는 규칙 기반 임시 구현이며 Phase 1에서 교체한다.
"""

from operator import add
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from app.rag.retriever import retrieve_compatibility_notes
from app.schemas import Product, Recommendation, Requirements
from app.tools.site_search import search_site

NEW_SITES = ["쿠팡", "11번가", "컴퓨존", "다나와", "오버시스템", "샵다나와"]
USED_SITES = ["번개장터", "중고나라", "당근마켓"]


class AgentState(TypedDict, total=False):
    requirements: Requirements
    search_plan: list[dict[str, str]]
    raw_results: list[Product]
    products: list[Product]
    warnings: list[str]
    recommendations: list[Recommendation]
    explanation: str
    steps: Annotated[list[str], add]


def requirements_analyzer(state: AgentState) -> AgentState:
    # TODO: LLM으로 자유 입력(notes)을 구조화
    return {"steps": ["RequirementsAnalyzer: 요구사항 확인"]}


def search_planner(state: AgentState) -> AgentState:
    req = state["requirements"]
    sites = {
        "new": NEW_SITES,
        "used": USED_SITES,
        "mixed": NEW_SITES + USED_SITES,
    }[req.condition]
    plan = [{"site": site, "query": req.purpose} for site in sites]
    return {"search_plan": plan, "steps": [f"SearchPlanner: {len(plan)}개 사이트 검색 계획"]}


def site_searcher(state: AgentState) -> AgentState:
    results = [p for item in state["search_plan"] for p in search_site(item["site"], item["query"])]
    return {"raw_results": results, "steps": [f"SiteSearcher: {len(results)}건 수집 (목업)"]}


def result_normalizer(state: AgentState) -> AgentState:
    unique = {(p.site, p.product_name): p for p in state["raw_results"]}
    products = list(unique.values())
    return {"products": products, "steps": [f"ResultNormalizer: {len(products)}건으로 정리"]}


def compatibility_checker(state: AgentState) -> AgentState:
    # TODO: 룰 + RAG 기반 실제 호환성 검증
    notes = retrieve_compatibility_notes(state["requirements"].purpose)
    warnings = notes or ["호환성 검증이 아직 구현되지 않았습니다. 구매 전 직접 확인하세요."]
    return {"warnings": warnings, "steps": ["CompatibilityChecker: 검증 미구현 (임시 경고)"]}


def ranker_and_recommender(state: AgentState) -> AgentState:
    budget = state["requirements"].budget_krw
    recommendations = [
        Recommendation(
            **p.model_dump(),
            score=round(1 - p.price / budget, 3),
            reason="예산 대비 가격 기준 임시 점수입니다.",
        )
        for p in state["products"]
        if p.price <= budget
    ]
    recommendations.sort(key=lambda r: r.score, reverse=True)
    return {
        "recommendations": recommendations,
        "steps": [f"RankerAndRecommender: {len(recommendations)}건 추천"],
    }


def explainer(state: AgentState) -> AgentState:
    # TODO: LLM으로 트레이드오프와 신품/중고 믹스 설명 생성
    explanation = (
        f"'{state['requirements'].purpose}' 용도로 목업 데이터에서 "
        f"{len(state['recommendations'])}건을 골랐습니다. 실제 상품 정보가 아닙니다."
    )
    return {"explanation": explanation, "steps": ["Explainer: 설명 생성"]}


NODES = [
    ("requirements_analyzer", requirements_analyzer),
    ("search_planner", search_planner),
    ("site_searcher", site_searcher),
    ("result_normalizer", result_normalizer),
    ("compatibility_checker", compatibility_checker),
    ("ranker_and_recommender", ranker_and_recommender),
    ("explainer", explainer),
]


def build_graph():
    builder = StateGraph(AgentState)
    for name, node in NODES:
        builder.add_node(name, node)
    previous = START
    for name, _ in NODES:
        builder.add_edge(previous, name)
        previous = name
    builder.add_edge(previous, END)
    return builder.compile()


graph = build_graph()
