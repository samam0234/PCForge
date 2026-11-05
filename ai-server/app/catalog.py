"""카탈로그 JSON을 메모리에 두고, 파일이 바뀌면 다음 조회에서 다시 읽는다."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.schemas import Product, Requirements

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "data" / "catalog" / "products.json"
LIVE_PATH = ROOT / "data" / "catalog" / "live.json"
MEMBER_ONLY = ("model", "material", "color", "noise")
CLOSED = {"discontinued", "sold", "stopped", "upcoming", "unverified"}
SHORTLIST_CAP = {"guest": 30, "member": 120}
NOT_A_LISTING = re.compile(r"구매합니다|구입합니다|삽니다|구합니다|매입|부품용|고장")
FLOOR_RATIO = 0.3

_cache: dict | None = None
_mtime: tuple[float, float] | None = None


def _mtimes() -> tuple[float, float]:
    live = LIVE_PATH.stat().st_mtime if LIVE_PATH.exists() else 0.0
    return CATALOG_PATH.stat().st_mtime, live


def load_catalog() -> dict:
    global _cache, _mtime
    mtime = _mtimes()
    if _cache is None or _mtime != mtime:
        data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        if mtime[1]:
            try:
                live = json.loads(LIVE_PATH.read_text(encoding="utf-8"))
                data["products"] = [*live.get("products", []), *data["products"]]
            except (OSError, ValueError):
                pass
        _cache = data
        _mtime = mtime
    return _cache


def to_product(item: dict) -> Product:
    specs = {key: str(value) for key, value in item.get("specs", {}).items()}
    specs.update(
        {
            "noise": item.get("noise", ""),
            "power": item.get("power", ""),
            "grade": item.get("grade", ""),
            "material": item.get("material", ""),
            "form_factor": item.get("form_factor", ""),
            "socket": item.get("socket", ""),
            "color": item.get("color", ""),
            "purposes": ",".join(item.get("purposes", [])),
        }
    )
    return Product(
        id=item["id"],
        product_name=item["name"],
        category=item["category"],
        price=int(item["price"]),
        site=item["shop"],
        specs=specs,
        is_used=item.get("condition") == "used",
        is_mock=False,
        url=item.get("url"),
        model=item.get("model", ""),
        brand=item.get("brand", ""),
        material=item.get("material", ""),
        grade=item.get("grade", ""),
        color=item.get("color", ""),
        summary=item.get("summary", ""),
    )


def _blob(item: dict) -> str:
    return " ".join(
        [
            item.get("name", ""),
            item.get("brand", ""),
            item.get("model", ""),
            item.get("material", ""),
            item.get("summary", ""),
        ]
    ).lower()


def _contains(item: dict, needle: str) -> bool:
    return needle.lower() in _blob(item)


def offerable(item: dict) -> bool:
    """판매 페이지 링크가 있는 현재 매물과 기준 시세만 추천에 넣는다."""
    availability = item.get("availability") or "reference"
    if availability in CLOSED:
        return False
    if item.get("source") in {"naver", "market"}:
        return availability == "selling" and bool(item.get("url"))
    return True


def matches(item: dict, req: Requirements) -> bool:
    member = req.access_tier == "member"
    if req.part_name and not _contains(item, req.part_name.strip()):
        return False
    if req.purpose and req.purpose not in item.get("purposes", []):
        return False
    if req.condition == "new" and item.get("condition") != "new":
        return False
    if req.condition == "used" and item.get("condition") != "used":
        return False
    if item.get("price", 0) > req.budget_krw:
        return False
    checks = {
        "category": req.category,
        "brand": req.brand,
        "shop": req.shop,
        "form_factor": req.form_factor,
        "socket": req.socket,
        "grade": req.grade,
        "power": req.power,
    }
    if member:
        checks.update(
            {
                "model": req.model,
                "material": req.material,
                "color": req.color,
                "noise": req.noise,
            }
        )
    for field, expected in checks.items():
        if expected and item.get(field) != expected:
            return False
    return True


def gather(req: Requirements) -> list[Product]:
    products = load_catalog()["products"]
    cap = SHORTLIST_CAP.get(req.access_tier, SHORTLIST_CAP["guest"])
    selected = [item_id for item_id in req.selected_ids if item_id][:cap]
    if selected:
        by_id = {item["id"]: item for item in products}
        return [to_product(by_id[item_id]) for item_id in selected if item_id in by_id and offerable(by_id[item_id])]
    return [to_product(item) for item in products if offerable(item) and matches(item, req)]


def compact(item: dict) -> dict:
    """에이전트와 화면에 넘기는 짧은 매물 정보. 회원 전용 칸(소재·색·소음)은 넣지 않는다."""
    price_kind = {"market": "판매글 가격", "naver": "네이버 쇼핑 가격"}.get(item.get("source"), "기준 시세")
    url = item.get("url") or ""
    row = {
        "id": item["id"],
        "name": item.get("name", "")[:100],
        "category": item.get("category", ""),
        "brand": item.get("brand", ""),
        "price": int(item.get("price", 0)),
        "price_kind": price_kind,
        "shop": item.get("shop", ""),
        "condition": "중고" if item.get("condition") == "used" else "신품",
        "grade": item.get("grade", ""),
        "url": url if url.startswith(("https://", "http://")) else None,
    }
    for key in ("socket", "form_factor"):
        if item.get(key):
            row[key] = item[key]
    row.update({key: str(value) for key, value in (item.get("specs") or {}).items()})
    return row


def _price_floors(products: list[dict]) -> dict[str, float]:
    """분류별 기준 시세 최저가의 일부. 이보다 싼 판매글은 그 부품 자체가 아니라고 본다."""
    lowest: dict[str, int] = {}
    for item in products:
        if item.get("source") in {"naver", "market"}:
            continue
        category = item.get("category", "")
        price = item.get("price", 0)
        if price > 0 and (category not in lowest or price < lowest[category]):
            lowest[category] = price
    return {category: price * FLOOR_RATIO for category, price in lowest.items()}


def _is_real_listing(item: dict, floors: dict[str, float]) -> bool:
    """중고 판매글에서 '삽니다' 글과 부속품처럼 값이 맞지 않는 글을 뺀다."""
    if item.get("source") != "market":
        return True
    if NOT_A_LISTING.search(item.get("name", "")):
        return False
    return item.get("price", 0) >= floors.get(item.get("category", ""), 0)


def _perf_of(item: dict) -> float:
    try:
        return float((item.get("specs") or {}).get("perf", 0))
    except (TypeError, ValueError):
        return 0.0


def search_items(
    *,
    query: str = "",
    category: str = "",
    brand: str = "",
    socket: str = "",
    purpose: str = "",
    condition: str = "",
    price_min: int = 0,
    price_max: int = 0,
    sort: str = "perf",
    limit: int = 8,
) -> tuple[int, list[dict]]:
    """판매 중인 매물을 찾아 같은 모델은 가장 싼 한 줄만 남긴다. (조건에 맞은 수, 목록)을 돌려준다."""
    tokens = [token.lower() for token in query.split()]
    products = load_catalog()["products"]
    floors = _price_floors(products)
    found: list[dict] = []
    for item in products:
        if not offerable(item) or not _is_real_listing(item, floors):
            continue
        price = item.get("price", 0)
        if (price_max and price > price_max) or price < price_min:
            continue
        if category and item.get("category") != category:
            continue
        if brand and item.get("brand", "").lower() != brand.lower():
            continue
        if socket and item.get("socket", "").lower() != socket.lower():
            continue
        if purpose and purpose not in item.get("purposes", []):
            continue
        if condition and item.get("condition") != condition:
            continue
        if tokens:
            blob = _blob(item)
            squeezed = blob.replace(" ", "")
            if not all(token in blob or token in squeezed for token in tokens):
                continue
        found.append(item)

    cheapest: dict[tuple[str, str], dict] = {}
    for item in found:
        key = (item.get("model") or item.get("name", ""), item.get("condition", ""))
        if key not in cheapest or item.get("price", 0) < cheapest[key].get("price", 0):
            cheapest[key] = item
    rows = list(cheapest.values())
    if sort == "price":
        rows.sort(key=lambda item: item.get("price", 0))
    else:
        rows.sort(key=lambda item: (-_perf_of(item), item.get("price", 0)))
    return len(found), rows[:limit]


def items_by_ids(ids: list[str]) -> dict[str, dict]:
    wanted = set(ids)
    return {item["id"]: item for item in load_catalog()["products"] if item["id"] in wanted}
