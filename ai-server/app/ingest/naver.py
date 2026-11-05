"""네이버 쇼핑 검색 API로 카탈로그 모델의 실제 판매 목록을 모아 live.json에 쓴다.

실행: python -m app.ingest.naver
키: NAVER_CLIENT_ID, NAVER_CLIENT_SECRET (https://developers.naver.com 에서 '검색' API 등록)
"""

from __future__ import annotations

import html
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from scripts.build_catalog import bases

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
LIVE_PATH = ROOT / "data" / "catalog" / "live.json"
ENDPOINT = "https://openapi.naver.com/v1/search/shop.json"
PER_QUERY = 40
KEEP_PER_QUERY = 18
SPACING_S = 0.15
VARIANTS = {"ti", "super", "xt", "xtx", "x", "f", "k", "kf", "x3d", "s"}
USED_TYPES = {4, 5, 6}
DISCONTINUED_TYPES = {7, 8, 9}
UPCOMING_TYPES = {10, 11, 12}
CLOSED = {"discontinued", "sold", "upcoming", "unverified"}
BRAND_ALIASES = {
    "삼성": ("삼성", "samsung"),
    "SK하이닉스": ("하이닉스", "hynix"),
    "마이크로닉스": ("마이크로닉스", "micronics"),
    "슈퍼플라워": ("슈퍼플라워", "super flower", "superflower"),
    "한성": ("한성", "hansung"),
    "ABKO": ("앱코", "abko"),
    "darkFlash": ("darkflash", "다크플래쉬"),
    "Fractal": ("fractal", "프랙탈"),
    "Lian Li": ("lian li", "리안리"),
    "Cooler Master": ("cooler master", "쿨러마스터"),
    "Thermalright": ("thermalright", "써멀라이트"),
    "Deepcool": ("deepcool", "딥쿨"),
    "ID-COOLING": ("id-cooling", "아이디쿨링"),
    "ARCTIC": ("arctic", "아틱"),
    "Noctua": ("noctua", "녹투아"),
    "Leopold": ("leopold", "레오폴드"),
    "Keychron": ("keychron", "키크론"),
    "Logitech": ("logitech", "로지텍"),
    "Razer": ("razer", "레이저"),
    "ZOWIE": ("zowie", "조위"),
    "Pulsar": ("pulsar", "펄사"),
    "TeamGroup": ("teamgroup", "팀그룹"),
    "G.SKILL": ("g.skill", "gskill", "지스킬"),
    "Corsair": ("corsair", "커세어"),
    "Kingston": ("kingston", "킹스톤"),
    "Crucial": ("crucial", "마이크론 크루셜", "크루셜"),
    "Micron": ("micron", "마이크론"),
    "Solidigm": ("solidigm", "솔리다임"),
    "Seagate": ("seagate", "씨게이트"),
    "Toshiba": ("toshiba", "도시바"),
    "WD": ("wd", "western digital", "웨스턴디지털"),
    "Seasonic": ("seasonic", "시소닉"),
    "MAXSUN": ("maxsun", "맥선"),
    "BenQ": ("benq", "벤큐"),
    "Dell": ("dell", "델"),
    "LG": ("lg",),
    "ASUS": ("asus", "에이수스"),
    "MSI": ("msi",),
    "GIGABYTE": ("gigabyte", "기가바이트"),
    "ASRock": ("asrock", "애즈락"),
    "NZXT": ("nzxt",),
    "ATK": ("atk",),
}


class MissingKeys(RuntimeError):
    pass


def keys() -> tuple[str, str] | None:
    client_id = os.getenv("NAVER_CLIENT_ID", "").strip()
    secret = os.getenv("NAVER_CLIENT_SECRET", "").strip()
    if not client_id or not secret:
        return None
    return client_id, secret


def tokens(text: str) -> list[str]:
    text = html.unescape(re.sub(r"<[^>]+>", "", text)).lower()
    text = re.sub(r"(?<=\d)(?=[a-z])|(?<=[a-z])(?=\d)", " ", text)
    return re.findall(r"[a-z0-9가-힣]+", text)


def clean_title(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", text))).strip()


def seeds() -> list[dict]:
    """모델마다 검색어 하나. 그래픽카드는 칩 이름으로 한 번만 찾는다."""
    picked: dict[tuple[str, str], dict] = {}
    for item in bases():
        key = (item["category"], item["model"])
        if key in picked:
            picked[key].setdefault("partners", []).append(item)
            continue
        picked[key] = {**item, "partners": [item]}
    return list(picked.values())


def query_for(seed: dict) -> str:
    category = seed["category"]
    if category == "GPU":
        return f"{seed['model']} {seed['specs'].get('vram', '')} 그래픽카드".strip()
    if category == "CPU":
        return f"{seed['brand']} {seed['model']} CPU"
    return f"{seed['brand']} {seed['model']}"


def _key_tokens(seed: dict) -> list[str]:
    model = seed["model"]
    if seed["category"] == "CPU":
        return tokens(model.split()[-1].split("-")[-1])
    if seed["category"] == "GPU":
        return tokens(re.sub(r"^(RTX|RX|Arc)\s+", "", model))
    return tokens(model)


def _seq_match(title: list[str], key: list[str]) -> bool:
    for start in range(len(title) - len(key) + 1):
        if title[start : start + len(key)] != key:
            continue
        after = title[start + len(key)] if start + len(key) < len(title) else ""
        if after in VARIANTS:
            continue
        return True
    return False


def _brand_ok(seed: dict, title: str, brand: str) -> bool:
    aliases = BRAND_ALIASES.get(seed["brand"], (seed["brand"].lower(),))
    haystack = f"{title} {brand}".lower()
    return any(alias in haystack for alias in aliases)


def accept(seed: dict, raw: dict) -> bool:
    title = clean_title(raw.get("title", ""))
    title_tokens = tokens(title)
    key = _key_tokens(seed)
    if seed["category"] in ("CPU", "GPU"):
        if not _seq_match(title_tokens, key):
            return False
    elif not set(key).issubset(set(title_tokens)):
        return False
    if seed["category"] not in ("GPU",) and not _brand_ok(seed, title, f"{raw.get('brand', '')} {raw.get('maker', '')}"):
        return False
    vram = seed["specs"].get("vram", "")
    if vram:
        sizes = set(re.findall(r"(\d+)\s*gb", title.lower()))
        if sizes and vram.lower().replace("gb", "") not in sizes:
            return False
    try:
        price = int(raw.get("lprice") or 0)
        product_type = int(raw.get("productType") or 1)
    except ValueError:
        return False
    if product_type in DISCONTINUED_TYPES or product_type in UPCOMING_TYPES:
        return True
    if price <= 0:
        return False
    low = 0.25 if product_type in USED_TYPES else 0.45
    return seed["price"] * low <= price <= seed["price"] * 2.6


def _partner(seed: dict, brand: str) -> dict:
    lowered = brand.lower()
    for partner in seed.get("partners", []):
        if partner["brand"].lower() in lowered:
            return partner
    return seed


def availability_for(product_type: int, link: str) -> str:
    if product_type in DISCONTINUED_TYPES:
        return "discontinued"
    if product_type in UPCOMING_TYPES:
        return "upcoming"
    if not link.startswith("http"):
        return "unverified"
    return "selling"


def normalize(seed: dict, raw: dict, fetched_at: str) -> dict | None:
    try:
        product_type = int(raw.get("productType") or 1)
    except ValueError:
        return None
    used = product_type in USED_TYPES
    brand = (raw.get("brand") or raw.get("maker") or seed["brand"]).strip() or seed["brand"]
    if seed["category"] != "GPU":
        brand = seed["brand"]
    base = _partner(seed, brand)
    unknown_partner = seed["category"] == "GPU" and base is seed
    mall = (raw.get("mallName") or "").strip()
    shop = "네이버 가격비교" if mall in ("", "네이버") else mall
    title = clean_title(raw.get("title", ""))
    link = (raw.get("link") or "").strip()
    availability = availability_for(product_type, link)
    note = {
        "selling": "판매 페이지 링크가 있는 현재 매물입니다.",
        "discontinued": "단종 상품이라 추천에서 제외합니다.",
        "upcoming": "아직 판매 전이라 추천에서 제외합니다.",
        "unverified": "판매 페이지 링크가 없어 추천에서 제외합니다.",
    }[availability]
    return {
        "id": f"nv-{raw.get('productId')}",
        "name": title,
        "category": seed["category"],
        "brand": brand,
        "model": seed["model"],
        "material": "판매처 확인" if unknown_partner else base["material"],
        "form_factor": seed["form_factor"],
        "socket": seed["socket"],
        "condition": "used" if used else "new",
        "grade": "중고" if used else "새상품",
        "color": "판매처 확인" if unknown_partner else base["color"],
        "shop": shop,
        "price": int(raw["lprice"]),
        "noise": seed["noise"],
        "power": seed["power"],
        "purposes": seed["purposes"],
        "summary": f"{seed['model']} {note}",
        "specs": base["specs"],
        "url": link or None,
        "availability": availability,
        "image": raw.get("image") or None,
        "source": "naver",
        "fetched_at": fetched_at,
    }


def search(client: httpx.Client, query: str) -> list[dict]:
    for attempt in range(3):
        response = client.get(ENDPOINT, params={"query": query, "display": PER_QUERY, "sort": "sim"})
        if response.status_code == 429:
            time.sleep(1.5 * (attempt + 1))
            continue
        if response.status_code in (401, 403):
            raise MissingKeys(f"네이버 API 인증 실패 ({response.status_code}): {response.text[:120]}")
        response.raise_for_status()
        return response.json().get("items", [])
    return []


def load_previous() -> list[dict]:
    if not LIVE_PATH.exists():
        return []
    try:
        payload = json.loads(LIVE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return list(payload.get("products", []))


def merge_previous(listings: dict[str, dict], seen: set[str], previous: list[dict], complete: bool) -> list[dict]:
    """이번 검색에 없는 이전 판매 매물은 판매완료로 남긴다. 일부만 돌렸으면 상태를 바꾸지 않는다."""
    merged = dict(listings)
    for old in previous:
        item_id = old.get("id")
        if not item_id or item_id in merged:
            continue
        if complete and old.get("availability", "selling") == "selling" and item_id not in seen:
            retired = dict(old)
            retired["availability"] = "sold"
            retired["summary"] = f"{old.get('model', '')} 이전 수집에 있던 매물이 이번 검색에서 빠졌습니다. 판매가 끝난 것으로 보고 추천에서 제외합니다.".strip()
            merged[item_id] = retired
        else:
            merged[item_id] = old
    return list(merged.values())


def collect(limit: int | None = None) -> dict:
    creds = keys()
    if not creds:
        raise MissingKeys("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET이 없습니다")
    client_id, secret = creds
    fetched_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    listings: dict[str, dict] = {}
    seen: set[str] = set()
    queries = 0
    errors: list[str] = []
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": secret}
    with httpx.Client(headers=headers, timeout=15) as client:
        for seed in seeds()[:limit]:
            query = query_for(seed)
            try:
                raws = search(client, query)
            except MissingKeys:
                raise
            except Exception as exc:
                errors.append(f"{query}: {exc.__class__.__name__}")
                continue
            finally:
                queries += 1
                time.sleep(SPACING_S)
            kept_open = 0
            kept_closed = 0
            for raw in raws:
                product_id = str(raw.get("productId") or "")
                if product_id:
                    seen.add(f"nv-{product_id}")
                if not accept(seed, raw):
                    continue
                row = normalize(seed, raw, fetched_at)
                if not row or row["id"] in listings:
                    continue
                closed = row["availability"] in CLOSED
                if closed and kept_closed >= 6:
                    continue
                if not closed and kept_open >= KEEP_PER_QUERY:
                    continue
                listings[row["id"]] = row
                if closed:
                    kept_closed += 1
                else:
                    kept_open += 1
    complete = limit is None and not errors
    products = merge_previous(listings, seen, load_previous(), complete)
    return {
        "source": "naver_shopping_search",
        "fetched_at": fetched_at,
        "queries": queries,
        "errors": errors[:20],
        "products": products,
    }


def write(payload: dict) -> None:
    LIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = LIVE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, LIVE_PATH)


def refresh(limit: int | None = None) -> dict:
    payload = collect(limit)
    if not payload["products"]:
        raise RuntimeError("가져온 상품이 없어 이전 live.json을 유지합니다")
    write(payload)
    return {"fetched_at": payload["fetched_at"], "products": len(payload["products"]), "queries": payload["queries"]}


if __name__ == "__main__":
    import argparse

    from dotenv import load_dotenv

    load_dotenv()
    parser = argparse.ArgumentParser(description="네이버 쇼핑 검색으로 live.json 갱신")
    parser.add_argument("--limit", type=int, default=None, help="앞에서부터 이 개수의 모델만 검색")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(refresh(args.limit), ensure_ascii=False))
