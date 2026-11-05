"""PCForge LangGraph.

카탈로그 JSON에서 후보를 고르고, Chroma 메모와 규칙으로 호환을 본 뒤
Ollama가 그 목록만 가지고 설명을 쓴다.
"""

from operator import add
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from app.catalog import gather
from app.llm import ollama
from app.rag.retriever import retrieve_compatibility_notes
from app.schemas import Product, Recommendation, Requirements

BUILD_MEMBER = ["CPU", "메인보드", "메모리", "GPU", "SSD", "파워", "케이스", "쿨러", "모니터", "키보드", "마우스"]
BUILD_GUEST = ["CPU", "메인보드", "메모리", "GPU", "SSD", "파워"]
SHARES = {
    "CPU": 0.20,
    "메인보드": 0.12,
    "메모리": 0.10,
    "GPU": 0.32,
    "SSD": 0.08,
    "파워": 0.07,
    "케이스": 0.06,
    "쿨러": 0.05,
    "모니터": 0.14,
    "키보드": 0.04,
    "마우스": 0.03,
}
SIZE = {"Mini-ITX": 0, "M-ATX": 1, "ATX": 2}
REC_LIMIT = {"guest": 6, "member": 12}
RAG_K = {"guest": 2, "member": 4}


class AgentState(TypedDict, total=False):
    requirements: Requirements
    raw_results: list[Product]
    products: list[Product]
    rag_notes: list[dict[str, str]]
    warnings: list[str]
    recommendations: list[Recommendation]
    explanation: str
    steps: Annotated[list[str], add]


def requirements_analyzer(state: AgentState) -> AgentState:
    req = state["requirements"]
    tier = "회원" if req.access_tier == "member" else "비로그인"
    note = f", 메모 {len(req.notes)}자" if req.notes else ""
    picked = f", 후보 {len(req.selected_ids)}개" if req.selected_ids else ""
    return {"steps": [f"RequirementsAnalyzer: {tier} / {req.purpose} / {req.budget_krw}원{picked}{note}"]}


def search_planner(state: AgentState) -> AgentState:
    req = state["requirements"]
    if req.selected_ids:
        return {"steps": ["SearchPlanner: 담아 둔 목록을 추천 후보로 씁니다"]}
    return {"steps": [f"SearchPlanner: {req.condition} 조건으로 카탈로그를 거릅니다"]}


def site_searcher(state: AgentState) -> AgentState:
    results = gather(state["requirements"])
    return {"raw_results": results, "steps": [f"SiteSearcher: 카탈로그 {len(results)}건"]}


def result_normalizer(state: AgentState) -> AgentState:
    unique: dict[str, Product] = {}
    for product in state["raw_results"]:
        key = product.id or f"{product.site}:{product.product_name}"
        unique[key] = product
    products = list(unique.values())
    return {"products": products, "steps": [f"ResultNormalizer: {len(products)}건으로 정리"]}


def compatibility_checker(state: AgentState) -> AgentState:
    req = state["requirements"]
    names = " ".join(product.product_name for product in state["products"][:8])
    query = " ".join(part for part in (req.purpose, req.notes, req.part_name, req.socket, names) if part)
    k = RAG_K.get(req.access_tier, RAG_K["guest"])
    notes, problem = retrieve_compatibility_notes(query or req.purpose, k)
    warnings = []
    if problem:
        warnings.append(problem)
    elif notes:
        warnings.append("참고한 메모: " + ", ".join(note["title"] for note in notes))
    return {
        "rag_notes": notes,
        "warnings": warnings,
        "steps": [f"CompatibilityChecker: 근거 메모 {len(notes)}건"],
    }


def _perf(product: Product) -> int:
    try:
        return int(float(product.specs.get("perf", "0")))
    except ValueError:
        return 0


def _score(product: Product, req: Requirements, selected: set[str]) -> float:
    price_fit = max(0.0, 1 - product.price / req.budget_krw)
    purpose_fit = 1.0 if req.purpose in product.specs.get("purposes", "").split(",") else 0.35
    selected_fit = 1.0 if product.id in selected else 0.0
    priority = 0.0
    if "소음" in req.priorities and product.specs.get("noise") == "낮음":
        priority += 0.6
    if "전력" in req.priorities and product.specs.get("power") == "낮음":
        priority += 0.6
    if "성능" in req.priorities:
        priority += _perf(product) / 100
    price_weight = 0.35 if "가격" in req.priorities or req.purpose == "사무" else 0.08
    return purpose_fit * 0.35 + selected_fit + (_perf(product) / 100) * 0.5 + priority * 0.3 + price_fit * price_weight


def _assemble(products: list[Product], req: Requirements) -> list[Product]:
    limit = REC_LIMIT.get(req.access_tier, REC_LIMIT["guest"])
    selected = set(req.selected_ids)
    affordable = [product for product in products if product.price <= req.budget_krw]
    if req.category and not req.selected_ids:
        ranked = sorted(affordable, key=lambda product: _score(product, req, selected), reverse=True)
        return ranked[:limit]

    order = BUILD_MEMBER if req.access_tier == "member" else BUILD_GUEST
    remaining = req.budget_krw
    picked: list[Product] = []
    used: set[str] = set()
    for category in order:
        if len(picked) >= limit:
            break
        choices = [
            product
            for product in affordable
            if product.category == category
            and product.id not in used
            and product.price <= remaining
            and _fits(product, picked)
        ]
        if not choices:
            continue
        ceiling = min(remaining, max(int(req.budget_krw * SHARES.get(category, 0.08)), int(req.budget_krw * 0.04)))
        preferred = [product for product in choices if product.id in selected or product.price <= ceiling]
        best = max(preferred or choices, key=lambda product: _score(product, req, selected))
        picked.append(best)
        used.add(best.id)
        remaining -= best.price

    if len(picked) < limit:
        rest = sorted(
            [product for product in affordable if product.id not in used],
            key=lambda product: _score(product, req, selected),
            reverse=True,
        )
        for product in rest:
            if len(picked) >= limit or product.price > remaining or not _fits(product, picked):
                continue
            picked.append(product)
            used.add(product.id)
            remaining -= product.price
    return picked


def _fits(product: Product, picked: list[Product]) -> bool:
    cpu = _first(picked, "CPU")
    board = _first(picked, "메인보드")
    gpu = _first(picked, "GPU")
    case = _first(picked, "케이스")
    if product.category == "메인보드" and cpu and product.specs.get("socket") != cpu.specs.get("socket"):
        return False
    if product.category == "메모리":
        expected = ""
        if board:
            expected = board.specs.get("memory", "")
        elif cpu and "/" not in cpu.specs.get("memory", ""):
            expected = cpu.specs.get("memory", "")
        if expected and product.specs.get("memory") != expected:
            return False
    if product.category == "케이스" and board:
        board_size = SIZE.get(board.specs.get("form_factor", ""))
        case_size = SIZE.get(product.specs.get("form_factor", ""))
        if board_size is not None and case_size is not None and board_size > case_size:
            return False
    if product.category == "파워" and gpu:
        tdp = _number(gpu, "tdp_w")
        watt = _number(product, "watt")
        if tdp and watt and watt < int(tdp * 1.6 + 200):
            return False
    if product.category == "쿨러" and case and case.specs.get("form_factor") == "Mini-ITX":
        if "360" in product.specs.get("form_factor", ""):
            return False
    return True


def _first(products: list[Product], category: str) -> Product | None:
    return next((product for product in products if product.category == category), None)


def _number(product: Product | None, key: str) -> int:
    if product is None:
        return 0
    try:
        return int(float(product.specs.get(key, "0")))
    except ValueError:
        return 0


def rule_warnings(products: list[Product]) -> list[str]:
    warnings: list[str] = []
    cpu = _first(products, "CPU")
    board = _first(products, "메인보드")
    ram = _first(products, "메모리")
    gpu = _first(products, "GPU")
    psu = _first(products, "파워")
    case = _first(products, "케이스")
    cooler = _first(products, "쿨러")

    if cpu and board and cpu.specs.get("socket") and board.specs.get("socket"):
        if cpu.specs["socket"] != board.specs["socket"]:
            warnings.append(
                f"{cpu.product_name}({cpu.specs['socket']})와 {board.product_name}({board.specs['socket']}) 소켓이 다릅니다."
            )
    if board and ram and board.specs.get("memory") and ram.specs.get("memory"):
        if board.specs["memory"] != ram.specs["memory"]:
            warnings.append(f"{board.product_name}는 {board.specs['memory']}인데 메모리는 {ram.specs['memory']}입니다.")
    if cpu and ram and board is None:
        cpu_memory = cpu.specs.get("memory", "")
        ram_memory = ram.specs.get("memory", "")
        if cpu_memory and "/" not in cpu_memory and ram_memory and cpu_memory != ram_memory:
            warnings.append(f"{cpu.product_name}는 {cpu_memory}인데 고른 메모리는 {ram_memory}입니다.")
    tdp = _number(gpu, "tdp_w")
    watt = _number(psu, "watt")
    if gpu and psu and tdp and watt:
        need = int(tdp * 1.6 + 200)
        if watt < need:
            warnings.append(f"파워 {watt}W는 {gpu.product_name}(TDP {tdp}W)에 여유가 짧습니다. {need}W 이상을 권합니다.")
    if board and case:
        board_size = SIZE.get(board.specs.get("form_factor", ""))
        case_size = SIZE.get(case.specs.get("form_factor", ""))
        if board_size is not None and case_size is not None and board_size > case_size:
            warnings.append(f"{board.product_name}가 {case.product_name}보다 큽니다.")
    if cooler and case and "360" in cooler.specs.get("form_factor", "") and case.specs.get("form_factor") == "Mini-ITX":
        warnings.append("360 수랭은 Mini-ITX 케이스에 들어가기 어렵습니다.")
    if cpu and gpu is None:
        last = cpu.model.split()[-1] if cpu.model.split() else ""
        if last.endswith("F"):
            warnings.append(f"{cpu.product_name}는 내장 그래픽이 없어 그래픽카드가 필요합니다.")
    return warnings


def _reason(product: Product, req: Requirements, selected: set[str]) -> str:
    picked = "담아 둔 후보에서 예산 안으로 남긴 부품입니다. " if product.id in selected else ""
    condition = "중고" if product.is_used else "신품"
    return (
        f"{picked}{req.purpose} 용도의 {product.category} 자리입니다. "
        f"기준 시세 {product.price:,}원, {product.site}, {condition} {product.grade}."
    )


def ranker_and_recommender(state: AgentState) -> AgentState:
    req = state["requirements"]
    selected = set(req.selected_ids)
    picked = _assemble(state["products"], req)
    recommendations = [
        Recommendation(
            **product.model_dump(),
            score=round(_score(product, req, selected), 3),
            reason=_reason(product, req, selected),
        )
        for product in picked
    ]
    warnings = list(state.get("warnings") or [])
    warnings.extend(rule_warnings(picked))
    if not recommendations:
        warnings.append("예산 안에 고를 수 있는 부품이 없습니다. 예산을 올리거나 담아 둔 목록을 줄여 보세요.")
    elif req.selected_ids:
        kept = sum(1 for product in picked if product.id in selected)
        warnings.append(f"담아 둔 {len(state['products'])}개 가운데 예산과 구성에 남은 것은 {kept}개입니다.")
    return {
        "recommendations": recommendations,
        "warnings": warnings,
        "steps": [f"RankerAndRecommender: {len(recommendations)}건 추천"],
    }


def _fallback(req: Requirements, recommendations: list[Recommendation]) -> str:
    if not recommendations:
        return f"{req.purpose} 용도로 예산 {req.budget_krw:,}원 안에 고를 부품이 없습니다."
    names = ", ".join(item.product_name for item in recommendations[:6])
    extra = f" 외 {len(recommendations) - 6}개" if len(recommendations) > 6 else ""
    return (
        f"{req.purpose} 용도, 예산 {req.budget_krw:,}원 기준으로 카탈로그 기준 시세에서 "
        f"{len(recommendations)}개를 골랐습니다. {names}{extra}. "
        "금액은 2026-11-01 스냅샷이며 결제 화면의 가격과 다를 수 있습니다."
    )


def _explain(state: AgentState) -> tuple[str, str, str | None]:
    req = state["requirements"]
    recommendations = state["recommendations"]
    fallback = _fallback(req, recommendations)
    model = ollama.resolve_chat_model()
    if not model or not recommendations:
        problem = None if recommendations else None
        if not model:
            problem = "Ollama에 연결하지 못해 짧은 요약만 붙입니다."
        return fallback, "요약", problem

    system = (
        "당신은 PC 부품 잡지의 기자다. 한국어로 쓴다. "
        "주어진 추천, 메모, 경고에 있는 사실만 사용한다. "
        "없는 가격, 재고, 할인, 벤치마크 숫자를 만들지 않는다. "
        "소켓이나 메모리 세대가 다르면 맞다고 쓰지 않는다. "
        "가격은 기준 시세라고 밝힌다."
    )
    lines = [
        (
            f"- {item.product_name} | {item.category} | {item.price}원 | {item.site} | "
            f"{'중고' if item.is_used else '신품'} | 소켓 {item.specs.get('socket', '')} | "
            f"메모리 {item.specs.get('memory', '')} | {item.material}"
        )
        for item in recommendations
    ]
    note_lines = [f"- {note['title']}: {note['text']}" for note in state.get("rag_notes") or []]
    warn_lines = [f"- {warning}" for warning in state.get("warnings") or []]
    length = "두 문단" if req.access_tier != "member" else "세 문단에서 네 문단"
    user = (
        f"용도: {req.purpose}\n예산: {req.budget_krw}원\n조건: {req.condition}\n"
        f"독자 메모: {req.notes or '없음'}\n후보 수: {len(state.get('products') or [])}\n"
        f"고른 부품:\n" + "\n".join(lines) + "\n\n근거 메모:\n" + ("\n".join(note_lines) or "없음")
        + "\n\n이미 확인된 경고:\n" + ("\n".join(warn_lines) or "없음")
        + f"\n\n{length}으로 이 구성의 이유와 구매 전에 볼 점을 써라."
    )
    num_predict = 240 if req.access_tier != "member" else 560
    timeout = 120
    try:
        content = ollama.chat(model, system, user, num_predict, timeout)
    except Exception as exc:
        return fallback, "요약", f"언어 모델 응답이 없어 짧은 요약만 붙입니다. ({exc.__class__.__name__})"
    if not content:
        return fallback, "요약", "언어 모델이 빈 응답을 줘서 짧은 요약만 붙입니다."
    return content, model, None


def explainer(state: AgentState) -> AgentState:
    text, model_name, problem = _explain(state)
    warnings = list(state.get("warnings") or [])
    if problem:
        warnings.append(problem)
    return {"explanation": text, "warnings": warnings, "steps": [f"Explainer: {model_name}"]}


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
