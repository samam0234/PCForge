"""재고 중인 PC 매물을 허용된 목록 문서에서 모아 data/catalog/live.json에 쓴다.

중고나라 검색 문서와 당근 판매 페이지, 다나와 카테고리 목록만 사용한다.
번개장터 앱 셸에는 매물이 없고 api.bunjang.co.kr 은 robots 가 전체 수집을 막아서 넣지 않는다.
검색 경로가 막힌 곳(/kr/buy-sell/s/, /list/ajax/, /bridge/)은 요청하지 않는다.

실행: ai-server 에서 python scripts/collect_stock.py
"""

from __future__ import annotations

import gzip
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree

import httpx

ROOT = Path(__file__).resolve().parents[2]
LIVE_PATH = ROOT / "data" / "catalog" / "live.json"
HEADERS = {
    "User-Agent": "PCForgeCatalog/1.0 (local study; in-stock catalog)",
    "Accept-Language": "ko-KR,ko;q=0.9",
}
JN_LIST = "https://web.joongna.com/search"
JN_CATEGORIES = {
    158: "노트북",
    159: "데스크탑",
    160: "모니터",
    161: "CPU",
    162: "SSD",
    163: "GPU",
    165: "파워",
    166: "키보드",
}
JN_HIGH = (8, 159, 161, 163)
DANAWA_SEEDS = (
    "112747",
    "11236855",
    "112751",
    "112752",
    "112753",
    "11255541",
    "11255542",
    "112760",
    "112763",
    "112775",
    "112777",
    "11216929",
    "112782",
    "112787",
    "11253591",
    "113990",
)
BRANDS = (
    ("AMD", ("amd", "라이젠", "ryzen", "라데온", "radeon")),
    ("인텔", ("인텔", "intel", "코어i", "코어 i")),
    ("NVIDIA", ("nvidia", "지포스", "rtx", "gtx")),
    ("삼성", ("삼성", "samsung")),
    ("SK하이닉스", ("하이닉스", "hynix")),
    ("LG", ("lg", "그램")),
    ("ASUS", ("asus", "에이수스")),
    ("MSI", ("msi",)),
    ("GIGABYTE", ("gigabyte", "기가바이트")),
    ("ASRock", ("asrock", "애즈락")),
    ("애플", ("애플", "맥북", "macbook")),
    ("레노버", ("레노버", "lenovo")),
    ("Dell", ("dell", "델")),
    ("HP", ("hp",)),
    ("Corsair", ("corsair", "커세어")),
    ("G.SKILL", ("g.skill", "지스킬")),
    ("Kingston", ("kingston", "킹스톤")),
    ("Crucial", ("crucial", "크루셜")),
    ("WD", ("western digital", "웨스턴", "wd ")),
    ("Seagate", ("seagate", "씨게이트")),
    ("Seasonic", ("seasonic", "시소닉")),
    ("마이크로닉스", ("마이크로닉스", "micronics")),
    ("한성", ("한성",)),
    ("ABKO", ("abko", "앱코")),
    ("Logitech", ("logitech", "로지텍")),
    ("Razer", ("razer", "레이저")),
    ("Keychron", ("keychron", "키크론")),
    ("Leopold", ("leopold", "레오폴드")),
)
DANAWA_CATEGORY = (
    ("메인보드", ("메인보드", "mainboard")),
    ("CPU", ("cpu", "라이젠", "ryzen", "인텔")),
    ("메모리", ("램", "ram", "ddr4", "ddr5", "메모리")),
    ("GPU", ("그래픽", "vga", "rtx", "gtx", "라데온", "지포스", "gpu")),
    ("SSD", ("ssd", "nvme")),
    ("HDD", ("hdd", "하드")),
    ("파워", ("파워", "psu")),
    ("쿨러", ("쿨러", "수냉")),
    ("케이스", ("케이스",)),
    ("모니터", ("모니터",)),
    ("키보드", ("키보드",)),
    ("마우스", ("마우스",)),
    ("노트북", ("노트북", "맥북", "그램")),
    ("데스크탑", ("본체", "데스크탑", "데스크톱", "조립")),
)
KEEP_URL = (
    "컴퓨터", "노트북", "그램", "맥북", "그래픽", "vga", "메인보드", "ssd", "nvme",
    "ddr4", "ddr5", "rtx", "gtx", "라이젠", "ryzen", "게이밍", "본체", "모니터",
    "파워", "마우스", "조립", "데스크탑", "데스크톱", "cpu", "gpu", "램", "메모리",
    "쿨러", "수냉", "키보드",
)
SKIP_URL = (
    "피아노", "바이크", "자전거", "코스프레", "유모차", "아이폰", "갤럭시", "에어팟",
    "버즈", "아이패드", "휴대폰", "폰케이스",
)
SOCKETS = ("AM5", "AM4", "LGA1851", "LGA1700", "LGA1200", "sTR5", "sTRX4")


class Catalog:
    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.seen: set[str] = set()
        self.lock = threading.Lock()
        self.by_shop = {"중고나라": 0, "당근마켓": 0, "다나와": 0}

    def add(self, row: dict | None) -> bool:
        if not row:
            return False
        with self.lock:
            if row["id"] in self.seen:
                return False
            self.seen.add(row["id"])
            self.rows.append(row)
            self.by_shop[row["shop"]] = self.by_shop.get(row["shop"], 0) + 1
            return True

    def __len__(self) -> int:
        return len(self.rows)


class Fetcher:
    def __init__(self) -> None:
        self.client = httpx.Client(headers=HEADERS, timeout=25, follow_redirects=True)
        self.lock = threading.Lock()
        self.next_at = 0.0

    def get(self, url: str, params: dict | None = None) -> str | None:
        for attempt in range(4):
            with self.lock:
                wait = self.next_at - time.monotonic()
                self.next_at = max(self.next_at, time.monotonic()) + 0.12
            if wait > 0:
                time.sleep(wait)
            try:
                response = self.client.get(url, params=params)
            except httpx.HTTPError:
                time.sleep(0.8 * (attempt + 1))
                continue
            if response.status_code in (429, 503):
                time.sleep(1.6 * (attempt + 1))
                continue
            if response.status_code != 200:
                return None
            return response.text
        return None

    def close(self) -> None:
        self.client.close()


def classify(title: str, default: str) -> str:
    blob = title.lower()
    for category, words in DANAWA_CATEGORY:
        if any(word in blob for word in words):
            return category
    return default


def purposes_for(title: str) -> list[str]:
    blob = title.lower()
    found: list[str] = []
    if any(word in blob for word in ("게임", "게이밍", "rtx", "gtx", "지포스", "라데온")):
        found.append("게이밍")
    if any(word in blob for word in ("영상", "편집", "모니터")):
        found.append("영상편집")
    if any(word in blob for word in ("개발", "노트북", "맥북")):
        found.append("개발")
    if any(word in blob for word in ("5090", "4090", "a6000", "학습")):
        found.append("AI 학습")
    if any(word in blob for word in ("사무", "오피스", "키보드", "마우스")):
        found.append("사무")
    return found or ["게이밍", "사무"]


def brand_of(title: str) -> str:
    blob = title.lower()
    for name, words in BRANDS:
        if any(word in blob for word in words):
            return name
    return ""


def socket_of(title: str) -> str:
    compact = title.upper().replace(" ", "")
    for socket in SOCKETS:
        if socket.upper().replace(" ", "") in compact:
            return socket
    return ""


def form_of(title: str, category: str) -> str:
    blob = title.lower()
    if category == "노트북" or any(word in blob for word in ("노트북", "맥북", "그램")):
        return "노트북"
    if "mini-itx" in blob or "미니itx" in compact_form(blob):
        return "Mini-ITX"
    if "m-atx" in blob or "matx" in compact_form(blob) or "마이크로atx" in compact_form(blob):
        return "M-ATX"
    if "atx" in compact_form(blob):
        return "ATX"
    return "데스크탑"


def compact_form(blob: str) -> str:
    return blob.replace(" ", "").replace("-", "")


def specs_of(title: str) -> dict[str, str]:
    specs: dict[str, str] = {}
    memory = re.search(r"DDR\s*([45])", title, re.I)
    if memory:
        specs["memory"] = f"DDR{memory.group(1)}"
    return specs


def listing(
    *,
    item_id: str,
    name: str,
    category: str,
    shop: str,
    price: int,
    url: str,
    image: str,
    condition: str,
    fetched_at: str,
) -> dict | None:
    name = re.sub(r"\s+", " ", name).strip()
    if len(name) < 2 or price <= 0 or price > 500_000_000 or not url.startswith("http"):
        return None
    return {
        "id": item_id,
        "name": name[:180],
        "category": category,
        "brand": brand_of(name),
        "model": "",
        "material": "",
        "form_factor": form_of(name, category),
        "socket": socket_of(name),
        "condition": condition,
        "grade": "중고" if condition == "used" else "새상품",
        "color": "",
        "shop": shop,
        "price": price,
        "noise": "",
        "power": "",
        "purposes": purposes_for(name),
        "summary": f"{shop}에서 판매 중인 매물입니다. 가격과 재고는 판매 페이지에서 확인합니다.",
        "specs": specs_of(name),
        "url": url,
        "image": image if image.startswith("http") else None,
        "source": "market",
        "availability": "selling",
        "fetched_at": fetched_at,
    }


def parse_array(text: str, key: str) -> list:
    plain = text.replace('\\"', '"')
    token = f'"{key}":['
    start = plain.find(token)
    if start < 0:
        return []
    try:
        data, _ = json.JSONDecoder().raw_decode(plain[start + len(token) - 1 :])
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def loose_items(plain: str) -> list[dict]:
    """JSON이 제목 안의 따옴표로 깨져도 seq, 가격, 제목, 상태를 뽑는다."""
    pattern = re.compile(
        r'"seq":(\d+),"productPositionNo":\d+,"platformType":\d+,"price":(\d+),'
        r'"parcelFee":\d+,"url":"((?:\\.|[^"\\])*)","title":"((?:\\.|[^"\\])*)","state":(\d+)'
    )
    rows = []
    for seq, price, url, title, state in pattern.findall(plain):
        rows.append(
            {
                "seq": int(seq),
                "price": int(price),
                "url": url.replace("\\u0026", "&").replace("\\/", "/"),
                "title": title.replace("\\u0026", "&").replace("\\n", " "),
                "state": int(state),
            }
        )
    return rows


def joongna_row(item: dict, default: str, fetched_at: str) -> dict | None:
    if item.get("state") not in (0, "0"):
        return None
    try:
        price = int(item.get("price") or 0)
        seq = int(item.get("seq") or 0)
    except (TypeError, ValueError):
        return None
    title = str(item.get("title") or "")
    image = str(item.get("url") or "")
    return listing(
        item_id=f"jn-{seq}",
        name=title,
        category=classify(title, default),
        shop="중고나라",
        price=price,
        url=f"https://web.joongna.com/product/{seq}",
        image=image,
        condition="used",
        fetched_at=fetched_at,
    )


def crawl_joongna(
    fetcher: Fetcher,
    catalog: Catalog,
    fetched_at: str,
    target: int,
    categories: dict[int, str] | None = None,
    high: tuple[int, ...] | None = None,
    max_page: int = 180,
) -> None:
    categories = JN_CATEGORIES if categories is None else categories
    high = JN_HIGH if high is None else high
    next_page = {cat: 1 for cat in categories}
    high_page = {cat: 1 for cat in high}
    stalled: set[int] = set()
    high_stalled: set[int] = set()
    fails: dict[tuple[int, int], int] = {}

    def pull(cat: int, page: int, floor: int | None) -> tuple[int, int, int | None, int]:
        params: dict[str, int | str] = {"category": cat, "page": page}
        if floor:
            params["minPrice"] = floor
        text = fetcher.get(JN_LIST, params)
        if not text:
            return cat, page, floor, -1
        plain = text.replace('\\"', '"')
        if '"items":' not in plain and '"seq":' not in plain:
            return cat, page, floor, -1
        default = categories.get(cat, "PC부품")
        items = parse_array(text, "items")
        if not items:
            items = loose_items(plain)
        if not items:
            return cat, page, floor, (-2 if '"seq":' in plain else 0)
        added = 0
        for item in items:
            if isinstance(item, dict) and catalog.add(joongna_row(item, default, fetched_at)):
                added += 1
        return cat, page, floor, (added if added else -3)

    while len(catalog) < target and (len(stalled) < len(categories) or len(high_stalled) < len(high_page)):
        jobs: list[tuple[int, int, int | None]] = []
        for cat, page in next_page.items():
            if cat not in stalled and page <= max_page:
                jobs.append((cat, page, None))
        for cat, page in high_page.items():
            if cat not in high_stalled and page <= 30:
                jobs.append((cat, page, 10_000_000))
        if not jobs:
            break
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda job: pull(*job), jobs))
        for cat, page, floor, added in results:
            bucket = high_stalled if floor else stalled
            cursor = high_page if floor else next_page
            key = (cat, floor or 0)
            if added == -2:
                fails[key] = fails.get(key, 0) + 1
                if fails[key] >= 4:
                    bucket.add(cat)
                else:
                    cursor[cat] = page + 1
                continue
            if added == -3:
                fails[key] = 0
                cursor[cat] = page + 1
                continue
            if added < 0:
                fails[key] = fails.get(key, 0) + 1
                if fails[key] >= 3:
                    bucket.add(cat)
                continue
            if added == 0:
                bucket.add(cat)
                continue
            fails[key] = 0
            cursor[cat] = page + 1
        print(
            f"STOCK joongna {catalog.by_shop['중고나라']} total {len(catalog)} page {max(next_page.values(), default=0)}",
            flush=True,
        )
        if len(stalled) == len(categories) and len(high_stalled) == len(high_page):
            break


def daangn_keep(url: str) -> bool:
    text = unquote(url).lower()
    if any(word in text for word in SKIP_URL):
        return False
    if "키보드" in text and not any(word in text for word in ("기계식", "게이밍", "컴퓨터", "키크론", "한성", "레오폴드", "앱코", "무접점")):
        return False
    if "케이스" in text and not any(word in text for word in ("컴퓨터", "pc", "atx", "타워", "파워", "조립", "게이밍")):
        return False
    return any(word in text for word in KEEP_URL)


def daangn_row(text: str, url: str, fetched_at: str) -> dict | None:
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
    if "InStock" not in availability:
        return None
    try:
        price = int(float(offers.get("price") or 0))
    except (TypeError, ValueError):
        return None
    name = str(product.get("name") or "")
    if not daangn_keep(name) and not daangn_keep(url):
        return None
    code = url.rstrip("/").split("/")[-1].split("-")[-1] or url
    image = product.get("image")
    image_url = image if isinstance(image, str) else ""
    return listing(
        item_id=f"dg-{code}",
        name=name,
        category=classify(name, "PC부품"),
        shop="당근마켓",
        price=price,
        url=url,
        image=image_url,
        condition="used",
        fetched_at=fetched_at,
    )


def daangn_locs(fetcher: Fetcher) -> list[str]:
    text = fetcher.get("https://www.daangn.com/kr/buy-sell/sitemap-detail.xml.gz")
    if not text:
        return []
    if "<loc>" not in text[:800]:
        try:
            text = gzip.decompress(text.encode("latin1")).decode("utf-8", "replace")
        except OSError:
            return []
    try:
        locs = [unquote(node.text or "") for node in ElementTree.fromstring(text).iter() if node.tag.endswith("loc") and node.text]
    except ElementTree.ParseError:
        locs = [unquote(url) for url in re.findall(r"<loc>([^<]+)</loc>", text)]
    return [url for url in locs if "/kr/buy-sell/" in url and "/kr/buy-sell/s/" not in url and daangn_keep(url)]


def crawl_daangn(fetcher: Fetcher, catalog: Catalog, fetched_at: str, limit: int) -> None:
    locs = daangn_locs(fetcher)
    print(f"STOCK daangn candidates {len(locs)}", flush=True)
    locs = locs[:limit]

    def pull(url: str) -> None:
        if catalog.by_shop["당근마켓"] >= 8000:
            return
        text = fetcher.get(url)
        if text:
            catalog.add(daangn_row(text, url, fetched_at))

    with ThreadPoolExecutor(max_workers=3) as pool:
        for index, _url in enumerate(pool.map(pull, locs), start=1):
            if index % 200 == 0:
                print(f"STOCK daangn {catalog.by_shop['당근마켓']} scanned {index}", flush=True)
    print(f"STOCK daangn {catalog.by_shop['당근마켓']} total {len(catalog)}", flush=True)


def danawa_category(names: list[str], title: str) -> str:
    return classify(" ".join([*names, title]), "PC부품")


PC_NAV = ("CPU", "메인보드", "RAM", "그래픽", "SSD", "HDD", "케이스", "파워", "쿨러", "모니터", "키보드", "마우스", "노트북", "PC", "중고")


def danawa_nav(text: str) -> list[str]:
    found = re.findall(r'href="/list/\?cate=(\d+)"><span class="text-px13">([^<]+)</span>', text)
    codes: list[str] = []
    for code, name in found:
        if any(word.lower() in name.lower() for word in PC_NAV) and code not in codes:
            codes.append(code)
    return codes


def crawl_danawa(fetcher: Fetcher, catalog: Catalog, fetched_at: str, page_cap: int) -> None:
    home = fetcher.get("https://prod.danawa.com/list/", {"cate": DANAWA_SEEDS[0]})
    queue = list(dict.fromkeys([*DANAWA_SEEDS, *(danawa_nav(home or ""))]))
    seen_pages: set[str] = set()
    while queue and len(seen_pages) < page_cap:
        code = queue.pop(0)
        if code in seen_pages:
            continue
        seen_pages.add(code)
        text = home if code == DANAWA_SEEDS[0] and home else fetcher.get("https://prod.danawa.com/list/", {"cate": code})
        home = None
        if not text:
            continue
        for code_next in danawa_nav(text):
            if code_next not in seen_pages and code_next not in queue:
                queue.append(code_next)
        added = 0
        for product in parse_array(text, "products"):
            if not isinstance(product, dict) or product.get("status") != 1:
                continue
            price_info = product.get("price") or {}
            try:
                price = int(price_info.get("min") or 0)
            except (TypeError, ValueError):
                continue
            names = [str(name) for name in (product.get("category") or {}).get("names") or []]
            title = str(product.get("productName") or "")
            url = str(product.get("productUrl") or "")
            if "prod.danawa.com/info/" not in url:
                continue
            image = ""
            picture = product.get("image") or {}
            if isinstance(picture, dict):
                image = str(picture.get("url") or "")
            used = any("중고" in name for name in names) or "중고" in title
            row = listing(
                item_id=f"dn-{product.get('id')}",
                name=title,
                category=danawa_category(names, title),
                shop="다나와",
                price=price,
                url=url.split("&")[0],
                image=image,
                condition="used" if used else "new",
                fetched_at=fetched_at,
            )
            if catalog.add(row):
                added += 1
        print(
            f"STOCK danawa {catalog.by_shop['다나와']} pages {len(seen_pages)} added {added} total {len(catalog)}",
            flush=True,
        )


def write(catalog: Catalog, fetched_at: str) -> None:
    payload = {
        "source": "market_pages",
        "fetched_at": fetched_at,
        "note": "중고나라 검색 문서, 당근 판매중 페이지, 다나와 목록에서 모은 재고 매물입니다. 번개장터는 허용된 페이지에 매물이 없어 빠졌습니다.",
        "products": catalog.rows,
    }
    LIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = LIVE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(LIVE_PATH)


def self_check(fetcher: Fetcher) -> None:
    first = parse_array(fetcher.get(JN_LIST, {"category": 163, "page": 1}) or "", "items")
    second = parse_array(fetcher.get(JN_LIST, {"category": 163, "page": 2}) or "", "items")
    high = parse_array(fetcher.get(JN_LIST, {"category": 163, "minPrice": 10_000_000}) or "", "items")
    if not first or not second or first[0].get("seq") == second[0].get("seq"):
        raise SystemExit("중고나라 다음 페이지가 같은 매물입니다")
    priced = [item for item in high if isinstance(item, dict) and int(item.get("price") or 0) >= 10_000_000]
    if len(priced) < 5:
        raise SystemExit(f"중고나라 고가 매물 파싱 실패: {len(high)}")
    print(f"STOCK check pages {first[0].get('seq')} {second[0].get('seq')} high {len(priced)}", flush=True)


def load_existing(catalog: Catalog) -> None:
    if not LIVE_PATH.exists():
        return
    payload = json.loads(LIVE_PATH.read_text(encoding="utf-8"))
    for row in payload.get("products") or []:
        if isinstance(row, dict):
            catalog.add(row)


def main() -> None:
    fetched_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    fetcher = Fetcher()
    catalog = Catalog()
    resume = "--resume" in sys.argv
    try:
        if "--fill" in sys.argv:
            load_existing(catalog)
            print(f"STOCK fill-before {len(catalog)} {catalog.by_shop}", flush=True)
            crawl_danawa(fetcher, catalog, fetched_at, 80)
            crawl_joongna(
                fetcher,
                catalog,
                fetched_at,
                len(catalog) + 2500,
                categories={165: "파워"},
                high=(),
                max_page=40,
            )
            write(catalog, fetched_at)
        elif "--shops" in sys.argv:
            load_existing(catalog)
            print(f"STOCK shops-before {len(catalog)} {catalog.by_shop}", flush=True)
            crawl_daangn(fetcher, catalog, fetched_at, 2500)
            if len(catalog) < 52000:
                crawl_joongna(
                    fetcher,
                    catalog,
                    fetched_at,
                    52000,
                    categories={8: "PC부품"},
                    high=(),
                    max_page=40,
                )
            write(catalog, fetched_at)
        elif resume:
            load_existing(catalog)
            print(f"STOCK resume {len(catalog)} {catalog.by_shop}", flush=True)
            crawl_joongna(fetcher, catalog, fetched_at, 54000, max_page=220)
            if catalog.by_shop.get("당근마켓", 0) < 30:
                crawl_daangn(fetcher, catalog, fetched_at, 1200)
            if catalog.by_shop.get("다나와", 0) < 200:
                crawl_danawa(fetcher, catalog, fetched_at, 120)
            write(catalog, fetched_at)
        else:
            self_check(fetcher)
            crawl_joongna(fetcher, catalog, fetched_at, 44000)
            write(catalog, fetched_at)
            crawl_daangn(fetcher, catalog, fetched_at, 5000)
            write(catalog, fetched_at)
            crawl_danawa(fetcher, catalog, fetched_at, 120)
            if len(catalog) < 52000:
                crawl_joongna(
                    fetcher,
                    catalog,
                    fetched_at,
                    52000,
                    categories={8: "PC부품"},
                    high=(),
                    max_page=500,
                )
            write(catalog, fetched_at)
    finally:
        fetcher.close()
    expensive = sum(1 for row in catalog.rows if row["price"] >= 10_000_000)
    print(
        f"STOCK done total {len(catalog)} shops {catalog.by_shop} over10m {expensive}",
        flush=True,
    )


if __name__ == "__main__":
    main()
