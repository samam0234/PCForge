"""판매 페이지를 다시 읽어 단종, 판매중단, 판매완료를 구분한다.

중고나라와 당근은 상품 페이지의 schema.org availability 를 보고,
다나와는 상품 페이지의 단종·판매중단 문구와 최저가를 본다.
당근은 한 장씩 쉬고, 403 이 이어지면 그 사이트는 멈춘다.
검색이 막힌 경로와 번개장터 API 는 요청하지 않는다.

실행: ai-server 에서 python scripts/recheck_stock.py
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
LIVE_PATH = ROOT / "data" / "catalog" / "live.json"
REFERENCE_PATH = ROOT / "data" / "catalog" / "products.json"
STOCK = importlib.util.spec_from_file_location("collect_stock", Path(__file__).with_name("collect_stock.py"))
stock = importlib.util.module_from_spec(STOCK)
assert STOCK.loader is not None
STOCK.loader.exec_module(stock)

SCHEMA = re.compile(r'"availability"\s*:\s*"https://schema\.org/([A-Za-z]+)"')
SCHEMA_MAP = {
    "InStock": "selling",
    "LimitedAvailability": "selling",
    "OutOfStock": "sold",
    "SoldOut": "sold",
    "Discontinued": "discontinued",
    "PreOrder": "upcoming",
    "PreSale": "upcoming",
}
DANAWA_CLOSED = (
    (re.compile(r">\s*단종\s*<|단종상품|이 상품은 단종"), "discontinued"),
    (re.compile(r">\s*판매중단\s*<|>\s*판매중지\s*<|판매가 중단"), "stopped"),
)
SUMMARIES = {
    "selling": "{shop} 판매 페이지에서 판매중으로 확인한 매물입니다.",
    "sold": "{shop} 판매 페이지에서 판매완료로 확인한 매물입니다.",
    "discontinued": "{shop} 판매 페이지에서 단종으로 확인한 매물입니다.",
    "stopped": "{shop} 판매 페이지에서 판매중단으로 확인한 매물입니다.",
    "upcoming": "{shop} 판매 페이지에서 판매예정으로 확인한 매물입니다.",
}


class Gate:
    def __init__(self, gap: float) -> None:
        self.gap = gap
        self.lock = threading.Lock()
        self.next_at = 0.0

    def wait(self) -> None:
        with self.lock:
            delay = self.next_at - time.monotonic()
            self.next_at = max(self.next_at, time.monotonic()) + self.gap
        if delay > 0:
            time.sleep(delay)


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def host_of(url: str) -> str:
    if "daangn.com" in url:
        return "daangn"
    if "danawa.com" in url:
        return "danawa"
    if "joongna.com" in url:
        return "joongna"
    return "other"


def fetch_text(client: httpx.Client, gate: Gate, url: str, limit: int) -> tuple[int, str]:
    gate.wait()
    try:
        with client.stream("GET", url) as response:
            status = response.status_code
            if status != 200:
                return status, ""
            parts: list[str] = []
            size = 0
            for chunk in response.iter_text():
                parts.append(chunk)
                size += len(chunk)
                if size >= limit:
                    break
            return status, "".join(parts)
    except httpx.HTTPError:
        return 0, ""


def judge(url: str, status: int, text: str) -> str | None:
    if status in (404, 410):
        return "sold"
    if status != 200 or not text:
        return None
    if host_of(url) in {"joongna", "daangn"}:
        match = SCHEMA.search(text)
        if match and match.group(1) in SCHEMA_MAP:
            return SCHEMA_MAP[match.group(1)]
        if "판매완료" in text:
            return "sold"
        return None
    if host_of(url) == "danawa":
        for pattern, label in DANAWA_CLOSED:
            if pattern.search(text):
                return label
        if "최저가" in text:
            return "selling"
    return None


def apply(row: dict, label: str | None, checked_at: str) -> bool:
    row["stock_checked"] = checked_at
    if not label or label == row.get("availability"):
        return False
    row["availability"] = label
    shop = str(row.get("shop") or "판매처")
    row["summary"] = SUMMARIES.get(label, row.get("summary", "")).format(shop=shop)
    return True


def write_live(payload: dict) -> None:
    tmp = LIVE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(LIVE_PATH)


def check_rows(rows: list[dict], client: httpx.Client, gate: Gate, checked_at: str, workers: int) -> dict[str, int]:
    counts = {"checked": 0, "changed": 0, "blocked": 0}
    blocked: set[str] = set()
    fails: dict[str, int] = {}
    lock = threading.Lock()

    def one(row: dict) -> None:
        url = str(row.get("url") or "")
        site = host_of(url)
        if not url.startswith("http") or site in blocked:
            return
        limit = 220_000 if site == "danawa" else 140_000
        status, text = fetch_text(client, gate, url, limit)
        with lock:
            if status == 403:
                fails[site] = fails.get(site, 0) + 1
                if fails[site] >= 4:
                    blocked.add(site)
                    counts["blocked"] += 1
                return
            fails[site] = 0
            counts["checked"] += 1
            if apply(row, judge(url, status, text), checked_at):
                counts["changed"] += 1
            if counts["checked"] % 100 == 0:
                print(f"RECHECK progress {counts}", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, rows))
    return counts


def daangn_any(text: str, url: str, checked_at: str) -> dict | None:
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', text)
    product = None
    for block in blocks:
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("@type") == "Product":
            product = data
            break
    if not product:
        return None
    offers = product.get("offers") or {}
    availability = str(offers.get("availability") or "")
    if "InStock" in availability:
        label = "selling"
    elif "Discontinued" in availability:
        label = "discontinued"
    elif any(token in availability for token in ("OutOfStock", "SoldOut")):
        label = "sold"
    else:
        return None
    try:
        price = int(float(offers.get("price") or 0))
    except (TypeError, ValueError):
        return None
    name = str(product.get("name") or "")
    if not stock.daangn_keep(name) and not stock.daangn_keep(url):
        return None
    code = url.rstrip("/").split("/")[-1].split("-")[-1] or url
    image = product.get("image")
    row = stock.listing(
        item_id=f"dg-{code}",
        name=name,
        category=stock.classify(name, "PC부품"),
        shop="당근마켓",
        price=price,
        url=url,
        image=image if isinstance(image, str) else "",
        condition="used",
        fetched_at=checked_at,
    )
    if not row:
        return None
    row["availability"] = label
    row["summary"] = SUMMARIES[label].format(shop="당근마켓")
    row["stock_checked"] = checked_at
    return row


def add_daangn(payload: dict, client: httpx.Client, checked_at: str, cap: int) -> int:
    fetcher = stock.Fetcher()
    try:
        locs = stock.daangn_locs(fetcher)
    finally:
        fetcher.close()
    known = {str(row.get("url")) for row in payload["products"]}
    fresh = [url for url in locs if url not in known]
    gate = Gate(0.55)
    added = 0
    blocked = 0
    for url in fresh:
        if added >= cap or blocked >= 3:
            break
        status, text = fetch_text(client, gate, url, 180_000)
        if status == 403:
            blocked += 1
            continue
        blocked = 0
        row = daangn_any(text, url, checked_at)
        if row and row["id"] not in {item.get("id") for item in payload["products"]}:
            payload["products"].append(row)
            added += 1
            print(f"RECHECK daangn-new {row['availability']} {added}", flush=True)
    return added


def recheck_reference(client: httpx.Client, gate: Gate, checked_at: str) -> int:
    if not REFERENCE_PATH.exists():
        return 0
    payload = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    rows = [row for row in payload.get("products") or [] if isinstance(row, dict)]
    urls = []
    seen: set[str] = set()
    for row in rows:
        url = str(row.get("url") or "")
        if "prod.danawa.com/info/" in url and url not in seen:
            seen.add(url)
            urls.append(url)
    found: dict[str, str] = {}

    def one(url: str) -> None:
        status, text = fetch_text(client, gate, url, 220_000)
        label = judge(url, status, text)
        if label in {"discontinued", "stopped"}:
            found[url] = label

    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(one, urls[:400]))
    changed = 0
    for row in rows:
        label = found.get(str(row.get("url") or ""))
        if not label or row.get("availability") == label:
            continue
        row["availability"] = label
        row["stock_checked"] = checked_at
        changed += 1
    if changed:
        REFERENCE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"RECHECK reference closed {changed} urls {len(urls[:400])}", flush=True)
    return changed


def collect_more_daangn() -> None:
    """사이트맵에만 있는 당근 판매 페이지를 천천히 읽어 판매완료도 남긴다."""
    checked_at = now()
    payload = json.loads(LIVE_PATH.read_text(encoding="utf-8"))
    known = {str(row.get("url")) for row in payload["products"]}
    ids = {str(row.get("id")) for row in payload["products"]}
    fetcher = stock.Fetcher()
    try:
        locs = [url for url in stock.daangn_locs(fetcher) if url not in known]
    finally:
        fetcher.close()
    print(f"RECHECK daangn fresh {len(locs)}", flush=True)
    client = httpx.Client(headers=stock.HEADERS, timeout=20, follow_redirects=True)
    gate = Gate(0.7)
    added = 0
    blocked = 0
    try:
        for url in locs[:220]:
            if added >= 70 or blocked >= 2:
                break
            status, text = fetch_text(client, gate, url, 180_000)
            if status == 403:
                blocked += 1
                continue
            blocked = 0
            row = daangn_any(text, url, checked_at)
            if not row or row["id"] in ids:
                continue
            payload["products"].append(row)
            ids.add(row["id"])
            added += 1
            print(f"RECHECK daangn-new {row['availability']} {added}", flush=True)
            if added % 10 == 0:
                write_live(payload)
    finally:
        client.close()
        if added:
            write_live(payload)
    print(f"RECHECK daangn-more added {added} total {len(payload['products'])}", flush=True)


def main() -> None:
    if "--daangn-more" in sys.argv:
        collect_more_daangn()
        return
    checked_at = now()
    payload = json.loads(LIVE_PATH.read_text(encoding="utf-8"))
    rows = [row for row in payload.get("products") or [] if isinstance(row, dict)]
    pending = [row for row in rows if row.get("url") and not row.get("stock_checked")]
    danawa = [row for row in pending if host_of(str(row["url"])) == "danawa"]
    daangn = [row for row in pending if host_of(str(row["url"])) == "daangn"]
    joongna = [row for row in pending if host_of(str(row["url"])) == "joongna"]
    joongna.sort(key=lambda row: int(row.get("price") or 0), reverse=True)
    joongna = joongna[:1200]
    print(
        f"RECHECK plan danawa {len(danawa)} daangn {len(daangn)} joongna {len(joongna)}",
        flush=True,
    )
    client = httpx.Client(headers=stock.HEADERS, timeout=20, follow_redirects=True)
    try:
        fast = Gate(0.16)
        counts = check_rows(danawa + joongna, client, fast, checked_at, 4)
        print(f"RECHECK fast {counts}", flush=True)
        write_live(payload)
        slow = Gate(0.55)
        daangn_counts = check_rows(daangn, client, slow, checked_at, 1)
        print(f"RECHECK daangn {daangn_counts}", flush=True)
        added = add_daangn(payload, client, checked_at, 80)
        payload["note"] = "판매 페이지를 다시 읽어 판매중, 단종, 판매중단, 판매완료를 구분한 매물입니다."
        write_live(payload)
        print(f"RECHECK live added {added} total {len(payload['products'])}", flush=True)
        recheck_reference(client, fast, checked_at)
    finally:
        client.close()
    labels: dict[str, int] = {}
    for row in payload["products"]:
        label = str(row.get("availability") or "")
        labels[label] = labels.get(label, 0) + 1
    print(f"RECHECK availability {labels}", flush=True)


if __name__ == "__main__":
    main()
