"""카탈로그 모델마다 다나와에서 판매 중인 상품을 찾아 원본 링크를 붙인다.

검색은 search.danawa.com (Crawl-delay 10초), 상품 페이지는 prod.danawa.com/info 만 본다.
bridge 경로는 robots.txt가 막으므로 요청하지 않고, 페이지에 적힌 판매처 상품번호로 쇼핑몰 주소를 만든다.
실행: python -m scripts.attach_origin_links
"""

from __future__ import annotations

import html
import json
import re
import time
from pathlib import Path

import httpx

from app.ingest.naver import _key_tokens, _seq_match, tokens

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "data" / "catalog" / "products.json"
CACHE_PATH = ROOT / "data" / "catalog" / "link-cache.json"
SEARCH_GAP_S = 10
HEADERS = {
    "User-Agent": "PCForgeCatalog/1.0 (local study; product-link lookup)",
    "Accept-Language": "ko-KR,ko;q=0.9",
}
SHOP_ALIASES = {
    "11번가": ("11번가", "11st"),
    "쿠팡": ("쿠팡", "coupang"),
    "컴퓨존": ("컴퓨존", "compuzone"),
    "샵다나와": ("샵다나와", "shopdanawa"),
    "오버시스템": ("오버시스템", "oversystem"),
    "다나와": ("다나와",),
    "번개장터": ("번개장터", "bunjang"),
    "중고나라": ("중고나라", "joongna"),
    "당근마켓": ("당근", "daangn", "karrot"),
}


def clean_name(name: str) -> str:
    name = re.sub(r"<[^>]+>", "", html.unescape(name))
    name = name.replace("\\u003c", "<").replace("\\u003e", ">").replace("\\u0026", "&")
    name = re.sub(r"<[^>]+>", "", name)
    return re.sub(r"\s+", " ", name).strip()


def model_ok(title: str, category: str, model: str) -> bool:
    title_tokens = tokens(clean_name(title))
    key = _key_tokens({"category": category, "model": model})
    if category in ("CPU", "GPU"):
        return _seq_match(title_tokens, key)
    return set(key).issubset(set(title_tokens))


def search_hits(text: str) -> list[tuple[str, str]]:
    patterns = (
        r'productSeq\\":\\"(\d+)\\".{0,700}?productName\\":\\"(.*?)\\"',
        r'"productSeq":"(\d+)".{0,700}?"productName":"(.*?)"',
    )
    hits: list[tuple[str, str]] = []
    seen: set[str] = set()
    for pattern in patterns:
        for seq, name in re.findall(pattern, text):
            if seq not in seen:
                seen.add(seq)
                hits.append((seq, name))
    return hits


def html_offers(text: str) -> list[dict]:
    start = text.find("list__mall-price")
    section = text[start:] if start >= 0 else text
    offers: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for block in re.findall(r'<li class="list-item">(.*?)</li>', section, flags=re.S):
        image = re.search(r"alt='([^']+)'", block)
        label = re.search(r'class="text__logo"[^>]*aria-label="([^"]+)"', block)
        logo = (image.group(1) if image else label.group(1) if label else "").strip()
        code = re.search(r"link_pcode=([^&\"']+)", block)
        bridge = re.search(r'href="(https://prod\.danawa\.com/bridge/[^"]+)"', block)
        if not logo or not code:
            continue
        url = original_url(logo, code.group(1), bridge.group(1) if bridge else "")
        if not url or (logo, url) in seen:
            continue
        seen.add((logo, url))
        offers.append({"shop": logo, "url": url, "code": code.group(1)})
    return offers


def extract_rows(text: str) -> list[dict]:
    rows: list[dict] = []
    start = 0
    needle = "shopTableRows"
    while True:
        index = text.find(needle, start)
        if index < 0:
            break
        bracket = text.find("[", index)
        if bracket < 0 or bracket - index > 30:
            start = index + len(needle)
            continue
        depth = 0
        end = None
        for cursor in range(bracket, min(len(text), bracket + 400_000)):
            char = text[cursor]
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    end = cursor + 1
                    break
        if end is None:
            break
        blob = text[bracket:end].replace("\\u0026", "&")
        parsed = None
        for candidate in (blob, blob.replace('\\"', '"')):
            try:
                parsed = json.loads(candidate)
                break
            except json.JSONDecodeError:
                continue
        if isinstance(parsed, list):
            rows.extend(item for item in parsed if isinstance(item, dict))
        start = end
    return rows


def original_url(logo: str, code: str, bridge: str) -> str:
    code = str(code or "").strip()
    if "11번가" in logo or "11st" in logo.lower():
        return f"https://www.11st.co.kr/products/{code}"
    if "G마켓" in logo or "gmarket" in logo.lower():
        return f"https://item.gmarket.co.kr/Item?goodscode={code}"
    if "옥션" in logo:
        return f"https://itempage3.auction.co.kr/DetailView.aspx?itemno={code}"
    if "쿠팡" in logo or "coupang" in logo.lower():
        return f"https://www.coupang.com/vp/products/{code}"
    if "컴퓨존" in logo:
        return f"https://www.compuzone.co.kr/product/product_detail.htm?ProductNo={code}"
    if "SSG" in logo or "신세계" in logo:
        return f"https://www.ssg.com/item/itemView.ssg?itemId={code}"
    if "롯데" in logo or "lotteon" in logo.lower():
        return f"https://www.lotteon.com/p/product/{code}"
    if bridge.startswith("http"):
        return bridge
    return ""


def load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    tmp.replace(CACHE_PATH)


def lookup(client: httpx.Client, category: str, brand: str, model: str) -> dict:
    query = f"{brand} {model}".strip()
    response = client.get("https://search.danawa.com/", params={"query": query})
    response.raise_for_status()
    chosen = ""
    for seq, name in search_hits(response.text):
        if model_ok(name, category, model):
            chosen = seq
            break
    info = f"https://prod.danawa.com/info/?pcode={chosen}" if chosen else ""
    offers: list[dict] = []
    if chosen:
        page = client.get("https://prod.danawa.com/info/", params={"pcode": chosen})
        page.raise_for_status()
        if "shopTableRows" not in page.text:
            time.sleep(1)
            page = client.get("https://prod.danawa.com/info/", params={"pcode": chosen, "cate": "0"})
        seen: set[tuple[str, str]] = set()
        parsed = extract_rows(page.text)
        if not parsed:
            parsed = [
                {"logo": offer["shop"], "linkProductCode": offer.get("code", ""), "url": offer["url"]}
                for offer in html_offers(page.text)
            ]
        for row in parsed:
            logo = str(row.get("logo") or row.get("logoLabel") or "").strip()
            code = str(row.get("linkProductCode") or "").strip()
            bridge = html.unescape(str(row.get("url") or "")).replace("\\u0026", "&")
            url = bridge if bridge.startswith("http") and "loadingBridge" not in bridge else original_url(logo, code, bridge)
            if not logo or not url or (logo, url) in seen:
                continue
            seen.add((logo, url))
            offers.append({"shop": logo, "url": url})
    return {"pcode": chosen, "info": info, "offers": offers}


def shop_url(shop: str, found: dict) -> str:
    aliases = SHOP_ALIASES.get(shop, (shop,))
    for offer in found.get("offers", []):
        name = offer["shop"].lower()
        if any(alias.lower() in name for alias in aliases):
            return offer["url"]
    return found.get("info") or ""


def apply(products: list[dict], cache: dict) -> int:
    linked = 0
    for item in products:
        key = f"{item.get('category')}|{item.get('model')}"
        found = cache.get(key)
        if not found:
            continue
        url = shop_url(item.get("shop", ""), found)
        if url:
            item["url"] = url
            linked += 1
        elif "url" in item and not item["url"]:
            item.pop("url", None)
    return linked


def write_catalog(catalog: dict) -> None:
    tmp = CATALOG_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATALOG_PATH)


def main() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    products = catalog["products"]
    models: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in products:
        key = (item.get("category", ""), item.get("brand", ""), item.get("model", ""))
        if key[2] and key not in seen:
            seen.add(key)
            models.append(key)
    cache = load_cache()
    print(f"models {len(models)} cached {len(cache)}", flush=True)
    with httpx.Client(headers=HEADERS, timeout=20, follow_redirects=True) as client:
        searched = 0
        for index, (category, brand, model) in enumerate(models, start=1):
            key = f"{category}|{model}"
            if key in cache and "error" not in cache[key]:
                continue
            if searched:
                time.sleep(SEARCH_GAP_S)
            searched += 1
            try:
                cache[key] = lookup(client, category, brand, model)
            except Exception as exc:
                cache[key] = {"pcode": "", "info": "", "offers": [], "error": exc.__class__.__name__}
            save_cache(cache)
            found = cache[key]
            print(
                f"{index}/{len(models)} {model} pcode={found.get('pcode') or '-'} offers={len(found.get('offers', []))}",
                flush=True,
            )
            if index % 10 == 0:
                apply(products, cache)
                write_catalog(catalog)
    linked = apply(products, cache)
    catalog["note"] = (
        "기준 시세에 다나와 검색으로 찾은 판매처 원본 링크를 붙였습니다. "
        "판매처가 검색 결과에 없으면 링크를 만들지 않습니다."
    )
    write_catalog(catalog)
    print(f"linked {linked} / {len(products)}", flush=True)


if __name__ == "__main__":
    main()
