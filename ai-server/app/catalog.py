"""카탈로그 JSON을 메모리에 두고, 파일이 바뀌면 다음 조회에서 다시 읽는다."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas import Product, Requirements

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "data" / "catalog" / "products.json"
LIVE_PATH = ROOT / "data" / "catalog" / "live.json"
MEMBER_ONLY = ("model", "material", "color", "noise")
CLOSED = {"discontinued", "sold", "stopped", "upcoming", "unverified"}
SHORTLIST_CAP = {"guest": 30, "member": 120}

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


def _contains(item: dict, needle: str) -> bool:
    blob = " ".join(
        [
            item.get("name", ""),
            item.get("brand", ""),
            item.get("model", ""),
            item.get("material", ""),
            item.get("summary", ""),
        ]
    ).lower()
    return needle.lower() in blob


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
