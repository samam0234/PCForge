"""당근 판매 페이지를 몇 건만 읽어 보는 조사 스크립트다. 카탈로그를 쓰지 않는다."""

import json
import sys
from pathlib import Path

import httpx

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from collect_stock import Fetcher, daangn_locs
from recheck_stock import daangn_any, fetch_text, Gate

LIVE = Path(__file__).resolve().parents[3] / "data" / "catalog" / "live.json"
rows = json.loads(LIVE.read_text(encoding="utf-8"))["products"]
known = {row.get("url") for row in rows}
fetcher = Fetcher()
try:
    locs = daangn_locs(fetcher)
finally:
    fetcher.close()
fresh = [url for url in locs if url not in known]
print("locs", len(locs), "fresh", len(fresh))
client = httpx.Client(headers={"User-Agent": "PCForgeCatalog/1.0 (local study; in-stock catalog)", "Accept-Language": "ko"}, timeout=20, follow_redirects=True)
gate = Gate(0.7)
lines = []
blocked = 0
for url in fresh[:18]:
    status, text = fetch_text(client, gate, url, 160_000)
    if status == 403:
        blocked += 1
        lines.append(f"403 {url[-40:]}")
        if blocked >= 2:
            break
        continue
    blocked = 0
    row = daangn_any(text, url, "now")
    label = row["availability"] if row else "-"
    lines.append(f"{status} {label} {len(text)} {url[-48:]}")
client.close()
Path(__file__).with_name("_probe_status.txt").write_text("\n".join(lines), encoding="utf-8")
print("lines", len(lines))
