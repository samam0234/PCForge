"""국내 유통 모델 기준의 부품 카탈로그와 호환성 문서를 만든다.

가격은 2026-11-01 스냅샷의 기준 시세다. 쇼핑몰 결제 가격을 긁어 온 값이 아니다.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "data" / "catalog" / "products.json"
KNOWLEDGE_PATH = ROOT / "data" / "knowledge" / "compatibility.json"

NEW_SHOPS = [
    ("쿠팡", "coupang", 1.03, "새상품"),
    ("11번가", "11st", 1.00, "새상품"),
    ("컴퓨존", "compuzone", 0.96, "새상품"),
    ("다나와", "danawa", 0.985, "새상품"),
    ("오버시스템", "oversystem", 0.95, "새상품"),
    ("샵다나와", "shopdanawa", 0.975, "미개봉"),
]
USED_SHOPS = [
    ("번개장터", "bunjang", 0.82, "S급"),
    ("중고나라", "joongna", 0.73, "A급"),
    ("당근마켓", "daangn", 0.63, "B급"),
]


def slug(*parts: str) -> str:
    raw = "-".join(parts)
    ascii_part = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    ascii_part = re.sub(r"-+", "-", ascii_part).strip("-")[:48] or "item"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:6]
    return f"{ascii_part}-{digest}"


def won(value: float) -> int:
    return max(10_000, int(round(value / 1000.0) * 1000))


def part(
    category: str,
    brand: str,
    model: str,
    price: int,
    material: str,
    form_factor: str,
    socket: str,
    color: str,
    noise: str,
    power: str,
    purposes: list[str],
    specs: dict[str, str | int],
    channels: str = "both",
    name: str = "",
) -> dict:
    title = name or f"{brand} {model}"
    summary = f"{material} · {form_factor}. {purposes[0]} 용으로 보는 모델입니다."
    return {
        "category": category,
        "brand": brand,
        "model": model,
        "name": title,
        "price": price,
        "material": material,
        "form_factor": form_factor,
        "socket": socket,
        "color": color,
        "noise": noise,
        "power": power,
        "purposes": purposes,
        "channels": channels,
        "summary": summary,
        "specs": {key: str(value) for key, value in specs.items()},
    }


def cpus() -> list[dict]:
    rows = [
        ("AMD", "Ryzen 5 5600", 145_000, "AM4", "DDR4", 65, 6, 42, ["게이밍", "사무", "개발"], "used"),
        ("AMD", "Ryzen 5 7500F", 178_000, "AM5", "DDR5", 65, 6, 58, ["게이밍", "개발", "사무", "스트리밍"], "both"),
        ("AMD", "Ryzen 5 7600", 238_000, "AM5", "DDR5", 65, 6, 62, ["게이밍", "개발", "스트리밍"], "both"),
        ("AMD", "Ryzen 5 9600X", 318_000, "AM5", "DDR5", 65, 6, 70, ["게이밍", "개발", "스트리밍"], "both"),
        ("AMD", "Ryzen 7 7700", 328_000, "AM5", "DDR5", 65, 8, 74, ["게이밍", "개발", "영상편집"], "both"),
        ("AMD", "Ryzen 7 7800X3D", 548_000, "AM5", "DDR5", 120, 8, 90, ["게이밍", "스트리밍"], "both"),
        ("AMD", "Ryzen 7 9700X", 468_000, "AM5", "DDR5", 65, 8, 82, ["게이밍", "개발", "영상편집"], "both"),
        ("AMD", "Ryzen 7 9800X3D", 748_000, "AM5", "DDR5", 120, 8, 98, ["게이밍", "스트리밍"], "both"),
        ("AMD", "Ryzen 9 7900X", 498_000, "AM5", "DDR5", 170, 12, 84, ["영상편집", "개발", "3D 작업"], "both"),
        ("AMD", "Ryzen 9 9900X", 688_000, "AM5", "DDR5", 120, 12, 92, ["영상편집", "개발", "3D 작업", "AI 학습"], "both"),
        ("AMD", "Ryzen 9 9950X", 968_000, "AM5", "DDR5", 170, 16, 100, ["영상편집", "3D 작업", "AI 학습", "개발"], "both"),
        ("Intel", "Core i5-12400F", 162_000, "LGA1700", "DDR4/DDR5", 117, 6, 48, ["사무", "개발", "게이밍"], "both"),
        ("Intel", "Core i5-14400F", 248_000, "LGA1700", "DDR4/DDR5", 148, 10, 60, ["게이밍", "개발", "사무"], "both"),
        ("Intel", "Core i5-14600KF", 362_000, "LGA1700", "DDR4/DDR5", 125, 14, 76, ["게이밍", "영상편집", "스트리밍"], "both"),
        ("Intel", "Core i7-14700K", 528_000, "LGA1700", "DDR4/DDR5", 253, 20, 88, ["영상편집", "게이밍", "3D 작업", "개발"], "both"),
        ("Intel", "Core i9-14900K", 742_000, "LGA1700", "DDR4/DDR5", 253, 24, 96, ["영상편집", "3D 작업", "AI 학습"], "both"),
        ("Intel", "Core Ultra 5 245K", 428_000, "LGA1851", "DDR5", 125, 14, 78, ["게이밍", "개발", "스트리밍"], "both"),
        ("Intel", "Core Ultra 7 265K", 572_000, "LGA1851", "DDR5", 250, 20, 90, ["영상편집", "개발", "3D 작업"], "both"),
        ("Intel", "Core Ultra 9 285K", 848_000, "LGA1851", "DDR5", 250, 24, 99, ["영상편집", "3D 작업", "AI 학습"], "both"),
    ]
    items = []
    for brand, model, price, socket, memory, tdp, cores, perf, purposes, channels in rows:
        power = "높음" if tdp >= 200 else "보통" if tdp >= 120 else "낮음"
        noise = "보통" if tdp >= 160 else "낮음"
        items.append(
            part(
                "CPU",
                brand,
                model,
                price,
                "구리 히트스프레더",
                "데스크탑",
                socket,
                "실버",
                noise,
                power,
                purposes,
                {"memory": memory, "tdp_w": tdp, "cores": cores, "perf": perf},
                channels,
            )
        )
    return items


def gpus() -> list[dict]:
    chips = [
        ("RTX 3060", "12GB", 268_000, 170, 40, ["게이밍"], "used"),
        ("RTX 3070", "8GB", 348_000, 220, 52, ["게이밍", "영상편집"], "used"),
        ("RTX 3080", "10GB", 468_000, 320, 64, ["게이밍", "영상편집", "3D 작업"], "used"),
        ("RTX 4060", "8GB", 392_000, 115, 58, ["게이밍", "스트리밍", "사무"], "both"),
        ("RTX 4060 Ti", "8GB", 528_000, 160, 66, ["게이밍", "스트리밍", "영상편집"], "both"),
        ("RTX 4070 SUPER", "12GB", 842_000, 220, 78, ["게이밍", "영상편집", "3D 작업", "AI 학습"], "both"),
        ("RTX 4070 Ti SUPER", "16GB", 1_148_000, 285, 86, ["게이밍", "영상편집", "3D 작업", "AI 학습"], "both"),
        ("RTX 4080 SUPER", "16GB", 1_548_000, 320, 92, ["게이밍", "영상편집", "3D 작업", "AI 학습"], "both"),
        ("RTX 4090", "24GB", 2_860_000, 450, 100, ["AI 학습", "3D 작업", "영상편집", "게이밍"], "both"),
        ("RTX 5060", "8GB", 458_000, 145, 64, ["게이밍", "스트리밍"], "both"),
        ("RTX 5070", "12GB", 918_000, 250, 84, ["게이밍", "영상편집", "3D 작업", "AI 학습"], "both"),
        ("RTX 5070 Ti", "16GB", 1_268_000, 300, 90, ["게이밍", "영상편집", "3D 작업", "AI 학습"], "both"),
        ("RTX 5080", "16GB", 1_828_000, 360, 96, ["게이밍", "3D 작업", "AI 학습", "영상편집"], "both"),
        ("RX 7600", "8GB", 328_000, 165, 54, ["게이밍", "사무"], "both"),
        ("RX 7700 XT", "12GB", 512_000, 245, 70, ["게이밍", "영상편집"], "both"),
        ("RX 7800 XT", "16GB", 678_000, 263, 76, ["게이밍", "영상편집", "3D 작업"], "both"),
        ("RX 7900 XTX", "24GB", 1_248_000, 355, 88, ["게이밍", "3D 작업", "영상편집"], "both"),
        ("Arc B580", "12GB", 386_000, 190, 60, ["게이밍", "개발", "스트리밍"], "both"),
    ]
    partners = [
        ("ASUS", "듀얼", 0.97, "블랙", "플라스틱 슈라우드"),
        ("MSI", "벤투스", 1.00, "블랙", "메탈 백플레이트"),
        ("GIGABYTE", "윈드포스", 1.04, "그레이", "알루미늄 슈라우드"),
    ]
    items = []
    for model, vram, price, tdp, perf, purposes, channels in chips:
        slot = "3슬롯" if tdp >= 280 else "2슬롯"
        noise = "높음" if tdp >= 320 else "보통" if tdp >= 180 else "낮음"
        power = "높음" if tdp >= 250 else "보통" if tdp >= 140 else "낮음"
        for brand, line, factor, color, material in partners:
            items.append(
                part(
                    "GPU",
                    brand,
                    model,
                    int(price * factor),
                    material,
                    slot,
                    "없음",
                    color,
                    noise,
                    power,
                    purposes,
                    {"vram": vram, "tdp_w": tdp, "perf": perf, "line": line},
                    channels,
                    name=f"{brand} {line} {model} {vram}",
                )
            )
    return items


def boards() -> list[dict]:
    rows = [
        ("ASUS", "TUF B650M-PLUS", 178_000, "M-ATX", "AM5", "DDR5", "B650", "블랙"),
        ("MSI", "PRO B650-S", 198_000, "ATX", "AM5", "DDR5", "B650", "블랙"),
        ("GIGABYTE", "B650 AORUS ELITE", 248_000, "ATX", "AM5", "DDR5", "B650", "블랙"),
        ("ASRock", "B850M Pro RS", 214_000, "M-ATX", "AM5", "DDR5", "B850", "블랙"),
        ("MSI", "MAG X870 TOMAHAWK", 418_000, "ATX", "AM5", "DDR5", "X870", "블랙"),
        ("ASUS", "ROG STRIX X670E-E", 618_000, "ATX", "AM5", "DDR5", "X670E", "블랙"),
        ("ASUS", "ROG STRIX B650E-I", 378_000, "Mini-ITX", "AM5", "DDR5", "B650E", "블랙"),
        ("ASUS", "PRIME B760M-A", 158_000, "M-ATX", "LGA1700", "DDR5", "B760", "화이트"),
        ("MSI", "PRO B760-P DDR4", 149_000, "ATX", "LGA1700", "DDR4", "B760", "블랙"),
        ("GIGABYTE", "Z790 AORUS ELITE", 378_000, "ATX", "LGA1700", "DDR5", "Z790", "블랙"),
        ("ASUS", "TUF B860M-PLUS", 228_000, "M-ATX", "LGA1851", "DDR5", "B860", "블랙"),
        ("MSI", "MAG Z890 TOMAHAWK", 478_000, "ATX", "LGA1851", "DDR5", "Z890", "블랙"),
        ("ASRock", "B550M PRO4", 112_000, "M-ATX", "AM4", "DDR4", "B550", "블랙"),
        ("MAXSUN", "B650M WIFI", 128_000, "M-ATX", "AM5", "DDR5", "B650", "블랙"),
    ]
    items = []
    for brand, model, price, form, socket, memory, chipset, color in rows:
        purposes = ["게이밍", "개발", "영상편집", "사무"]
        if socket == "AM4":
            purposes = ["게이밍", "사무"]
        chipset_perf = {
            "B550": 42,
            "B650": 58,
            "B650E": 64,
            "B850": 60,
            "B760": 52,
            "Z790": 74,
            "B860": 62,
            "Z890": 78,
            "X670E": 82,
            "X870": 80,
        }.get(chipset, 50)
        items.append(
            part(
                "메인보드",
                brand,
                model,
                price,
                "유리섬유 PCB",
                form,
                socket,
                color,
                "낮음",
                "낮음",
                purposes,
                {"memory": memory, "chipset": chipset, "perf": chipset_perf},
            )
        )
    return items


def memory() -> list[dict]:
    rows = [
        ("삼성", "DDR5-5600 32GB", 138_000, "DDR5", "32GB", 56, "블랙", "알루미늄 방열판"),
        ("SK하이닉스", "DDR5-6000 32GB", 156_000, "DDR5", "32GB", 62, "블랙", "알루미늄 방열판"),
        ("G.SKILL", "DDR5-6000 CL30 32GB", 182_000, "DDR5", "32GB", 70, "블랙", "알루미늄 방열판"),
        ("Corsair", "DDR5-6000 32GB 화이트", 176_000, "DDR5", "32GB", 66, "화이트", "알루미늄 방열판"),
        ("Kingston", "DDR5-6400 32GB", 188_000, "DDR5", "32GB", 68, "블랙", "알루미늄 방열판"),
        ("TeamGroup", "DDR5-6000 32GB", 146_000, "DDR5", "32GB", 60, "블랙", "알루미늄 방열판"),
        ("Corsair", "DDR5-6400 64GB", 318_000, "DDR5", "64GB", 80, "블랙", "알루미늄 방열판"),
        ("Kingston", "DDR5-5600 16GB", 72_000, "DDR5", "16GB", 40, "그린", "PCB"),
        ("삼성", "DDR4-3200 32GB", 88_000, "DDR4", "32GB", 48, "그린", "PCB"),
        ("G.SKILL", "DDR4-3600 16GB", 54_000, "DDR4", "16GB", 36, "블랙", "알루미늄 방열판"),
    ]
    return [
        part(
            "메모리",
            brand,
            model,
            price,
            material,
            "DIMM",
            "없음",
            color,
            "낮음",
            "낮음",
            ["게이밍", "개발", "영상편집", "사무", "AI 학습"],
            {"memory": memory, "capacity": capacity, "perf": perf},
        )
        for brand, model, price, memory, capacity, perf, color, material in rows
    ]


def ssds() -> list[dict]:
    rows = [
        ("삼성", "990 PRO 1TB", 162_000, "1TB", 74, "M.2 2280"),
        ("삼성", "990 PRO 2TB", 278_000, "2TB", 86, "M.2 2280"),
        ("SK하이닉스", "Platinum P41 1TB", 142_000, "1TB", 72, "M.2 2280"),
        ("SK하이닉스", "P51 2TB", 298_000, "2TB", 90, "M.2 2280"),
        ("WD", "SN850X 2TB", 252_000, "2TB", 82, "M.2 2280"),
        ("WD", "SN7100 1TB", 112_000, "1TB", 64, "M.2 2280"),
        ("Crucial", "T500 2TB", 232_000, "2TB", 78, "M.2 2280"),
        ("Solidigm", "P44 Pro 1TB", 128_000, "1TB", 68, "M.2 2280"),
        ("삼성", "870 EVO 1TB", 118_000, "1TB", 40, "2.5인치"),
        ("Micron", "3500 4TB", 468_000, "4TB", 94, "M.2 2280"),
    ]
    return [
        part(
            "SSD",
            brand,
            model,
            price,
            "알루미늄 히트싱크" if form.startswith("M.2") else "금속 하우징",
            form,
            "없음",
            "블랙",
            "낮음",
            "낮음",
            ["게이밍", "개발", "영상편집", "사무", "AI 학습"],
            {"capacity": capacity, "perf": perf},
        )
        for brand, model, price, capacity, perf, form in rows
    ]


def hdds() -> list[dict]:
    rows = [
        ("Seagate", "Barracuda 2TB", 86_000, "2TB", 30),
        ("WD", "Blue 4TB", 132_000, "4TB", 34),
        ("Toshiba", "DT02 4TB", 124_000, "4TB", 32),
        ("Seagate", "IronWolf 8TB", 278_000, "8TB", 40),
    ]
    return [
        part(
            "HDD",
            brand,
            model,
            price,
            "알루미늄 플래터",
            "3.5인치",
            "없음",
            "실버",
            "보통",
            "낮음",
            ["영상편집", "사무", "개발"],
            {"capacity": capacity, "perf": perf},
        )
        for brand, model, price, capacity, perf in rows
    ]


def psus() -> list[dict]:
    rows = [
        ("마이크로닉스", "Classic II 650W", 74_000, 650, 40),
        ("darkFlash", "650W 브론즈", 62_000, 650, 34),
        ("슈퍼플라워", "SF-750 골드", 122_000, 750, 58),
        ("Seasonic", "Focus GX-750", 152_000, 750, 70),
        ("Corsair", "RM750x", 164_000, 750, 72),
        ("Seasonic", "Focus GX-850", 182_000, 850, 78),
        ("Corsair", "RM850x", 194_000, 850, 80),
        ("슈퍼플라워", "1000W 플래티넘", 214_000, 1000, 88),
    ]
    return [
        part(
            "파워",
            brand,
            model,
            price,
            "스틸 하우징",
            "ATX",
            "없음",
            "블랙",
            "낮음" if watt >= 750 else "보통",
            "낮음",
            ["게이밍", "영상편집", "개발", "사무", "AI 학습", "3D 작업"],
            {"watt": watt, "perf": perf},
        )
        for brand, model, price, watt, perf in rows
    ]


def cases() -> list[dict]:
    rows = [
        ("Fractal", "North", 186_000, "ATX", "우드", "우드", "보통", ["게이밍", "개발", "사무"]),
        ("Fractal", "Meshify 2", 168_000, "ATX", "메시", "블랙", "낮음", ["게이밍", "영상편집"]),
        ("Lian Li", "Lancool 207", 142_000, "ATX", "스틸", "블랙", "보통", ["게이밍", "개발"]),
        ("Lian Li", "O11 Vision", 236_000, "ATX", "강화유리", "화이트", "보통", ["게이밍", "스트리밍"]),
        ("NZXT", "H5 Flow", 154_000, "ATX", "스틸", "화이트", "낮음", ["게이밍", "개발"]),
        ("NZXT", "H9 Elite", 286_000, "ATX", "강화유리", "블랙", "보통", ["스트리밍", "게이밍"]),
        ("Corsair", "4000D", 128_000, "ATX", "스틸", "블랙", "보통", ["게이밍", "사무"]),
        ("darkFlash", "DLX21", 74_000, "ATX", "메시", "블랙", "낮음", ["게이밍", "사무"]),
        ("ABKO", "NCORE 100", 46_000, "M-ATX", "플라스틱", "블랙", "보통", ["사무"]),
        ("마이크로닉스", "GX2", 54_000, "M-ATX", "스틸", "실버", "보통", ["사무", "개발"]),
        ("Cooler Master", "NR200P", 124_000, "Mini-ITX", "알루미늄", "블랙", "보통", ["게이밍", "개발"]),
        ("ASUS", "Prime AP201", 112_000, "M-ATX", "메시", "화이트", "낮음", ["개발", "스트리밍"]),
    ]
    return [
        part(
            "케이스",
            brand,
            model,
            price,
            material,
            form,
            "없음",
            color,
            noise,
            "낮음",
            purposes,
            {"perf": 40},
        )
        for brand, model, price, form, material, color, noise, purposes in rows
    ]


def coolers() -> list[dict]:
    rows = [
        ("Thermalright", "Peerless Assassin 120", 39_000, "공랭", "알루미늄 핀", "보통", 55),
        ("Deepcool", "AK400", 36_000, "공랭", "알루미늄 핀", "보통", 48),
        ("Noctua", "NH-D15", 148_000, "공랭", "구리 베이스", "낮음", 80),
        ("ID-COOLING", "SE-214", 22_000, "공랭", "알루미늄 핀", "보통", 36),
        ("Thermalright", "Frozen Notte 360", 112_000, "수랭 360", "알루미늄 라디에이터", "낮음", 74),
        ("ARCTIC", "Liquid Freezer III 360", 142_000, "수랭 360", "알루미늄 라디에이터", "낮음", 86),
        ("NZXT", "Kraken 240", 178_000, "수랭 240", "알루미늄 라디에이터", "낮음", 70),
        ("Deepcool", "LS720", 128_000, "수랭 360", "구리 베이스", "낮음", 78),
    ]
    return [
        part(
            "쿨러",
            brand,
            model,
            price,
            material,
            form,
            "없음",
            "블랙",
            noise,
            "낮음",
            ["게이밍", "영상편집", "개발", "3D 작업"],
            {"perf": perf},
        )
        for brand, model, price, form, material, noise, perf in rows
    ]


def monitors() -> list[dict]:
    rows = [
        ("LG", "27GP850", 378_000, "27인치", "IPS 패널", "블랙", ["게이밍", "스트리밍"], 78),
        ("삼성", "오디세이 G5 27", 318_000, "27인치", "VA 패널", "블랙", ["게이밍"], 70),
        ("ASUS", "TUF VG27AQ", 292_000, "27인치", "IPS 패널", "블랙", ["게이밍", "개발"], 72),
        ("Dell", "U2724D", 518_000, "27인치", "IPS 패널", "실버", ["개발", "영상편집", "사무"], 80),
        ("LG", "32UP55", 448_000, "32인치", "IPS 패널", "화이트", ["영상편집", "사무", "3D 작업"], 76),
        ("삼성", "S24R350", 148_000, "24인치", "IPS 패널", "블랙", ["사무"], 36),
        ("BenQ", "MOBIUZ EX2710", 336_000, "27인치", "IPS 패널", "블랙", ["게이밍", "스트리밍"], 74),
        ("ASUS", "ProArt PA278QV", 468_000, "27인치", "IPS 패널", "블랙", ["영상편집", "3D 작업", "개발"], 84),
    ]
    return [
        part(
            "모니터",
            brand,
            model,
            price,
            material,
            form,
            "없음",
            color,
            "낮음",
            "낮음",
            purposes,
            {"perf": perf},
        )
        for brand, model, price, form, material, color, purposes, perf in rows
    ]


def keyboards() -> list[dict]:
    rows = [
        ("Keychron", "K8", 118_000, "알루미늄", "PBT 키캡", "그레이", 70),
        ("ABKO", "KN10", 36_000, "텐키리스", "ABS 키캡", "블랙", 30),
        ("Logitech", "MX Keys", 142_000, "무선", "ABS 키캡", "그레이", 60),
        ("한성", "GK898B", 88_000, "풀배열", "PBT 키캡", "블랙", 64),
        ("Corsair", "K70", 178_000, "풀배열", "알루미늄 상판", "블랙", 74),
        ("Leopold", "FC900R", 164_000, "풀배열", "PBT 키캡", "화이트", 80),
    ]
    return [
        part(
            "키보드",
            brand,
            model,
            price,
            material,
            form,
            "없음",
            color,
            "낮음",
            "낮음",
            ["게이밍", "개발", "사무", "영상편집"],
            {"perf": perf},
        )
        for brand, model, price, form, material, color, perf in rows
    ]


def mice() -> list[dict]:
    rows = [
        ("Logitech", "G PRO X SUPERLIGHT", 152_000, "블랙", 86),
        ("Razer", "DeathAdder V3", 72_000, "블랙", 64),
        ("ZOWIE", "EC2-CW", 148_000, "블랙", 78),
        ("Logitech", "MX Master 3S", 132_000, "그레이", 70),
        ("ATK", "X1", 52_000, "화이트", 58),
        ("Pulsar", "X2", 118_000, "블랙", 74),
    ]
    return [
        part(
            "마우스",
            brand,
            model,
            price,
            "무광 플라스틱",
            "무선" if "MX" in model or "SUPERLIGHT" in model or "CW" in model else "유선",
            "없음",
            color,
            "낮음",
            "낮음",
            ["게이밍", "개발", "사무"],
            {"perf": perf},
        )
        for brand, model, price, color, perf in rows
    ]


def fans() -> list[dict]:
    rows = [
        ("ARCTIC", "P12 5팩", 42_000, "강화 플라스틱", 70),
        ("Noctua", "NF-A12x25", 36_000, "강화 플라스틱", 90),
        ("Lian Li", "UNI SL120", 92_000, "알루미늄 프레임", 74),
        ("Thermalright", "TL-C12", 16_000, "강화 플라스틱", 40),
    ]
    return [
        part(
            "케이스팬",
            brand,
            model,
            price,
            material,
            "120mm",
            "없음",
            "블랙",
            "낮음",
            "낮음",
            ["게이밍", "영상편집", "개발"],
            {"perf": perf},
        )
        for brand, model, price, material, perf in rows
    ]


def bases() -> list[dict]:
    return [
        *cpus(),
        *gpus(),
        *boards(),
        *memory(),
        *ssds(),
        *hdds(),
        *psus(),
        *cases(),
        *coolers(),
        *monitors(),
        *keyboards(),
        *mice(),
        *fans(),
    ]


def expand(items: list[dict]) -> list[dict]:
    listings = []
    for item in items:
        shops = []
        if item["channels"] in ("both", "new"):
            shops.extend((shop, code, factor, grade, "new") for shop, code, factor, grade in NEW_SHOPS)
        if item["channels"] in ("both", "used"):
            shops.extend((shop, code, factor, grade, "used") for shop, code, factor, grade in USED_SHOPS)
        for shop, code, factor, grade, condition in shops:
            payload = {
                "id": slug(item["brand"], item["name"], code, condition, grade),
                "name": item["name"],
                "category": item["category"],
                "brand": item["brand"],
                "model": item["model"],
                "material": item["material"],
                "form_factor": item["form_factor"],
                "socket": item["socket"],
                "condition": condition,
                "grade": grade,
                "color": item["color"],
                "shop": shop,
                "price": won(item["price"] * factor),
                "noise": item["noise"],
                "power": item["power"],
                "purposes": item["purposes"],
                "summary": item["summary"],
                "specs": item["specs"],
            }
            listings.append(payload)
    ids = [row["id"] for row in listings]
    if len(ids) != len(set(ids)):
        raise RuntimeError("카탈로그 id가 중복됩니다")
    return listings


def knowledge() -> list[dict]:
    return [
        {
            "id": "am5-ddr5",
            "title": "AM5는 DDR5만 맞는다",
            "tags": "AM5 DDR5 메모리",
            "text": "라이젠 7000·9000 시리즈의 AM5 소켓 메인보드는 DDR5만 꽂힌다. DDR4 메모리는 핀과 키가 달라 장착되지 않는다. 7500F, 7800X3D, 9800X3D를 고르면 메모리도 DDR5로 맞춰야 한다.",
        },
        {
            "id": "am4-ddr4",
            "title": "AM4는 DDR4 보드와 메모리",
            "tags": "AM4 DDR4",
            "text": "라이젠 5000의 AM4 플랫폼은 DDR4 메인보드와 DDR4 메모리를 쓴다. B550 보드에 DDR5를 섞으면 부팅되지 않는다.",
        },
        {
            "id": "lga1851-ddr5",
            "title": "코어 울트라의 LGA1851",
            "tags": "LGA1851 DDR5 울트라",
            "text": "코어 울트라 200S의 LGA1851 보드는 DDR5 전용이다. 13·14세대 LGA1700 쿨러 브라켓이 맞는 제품도 있지만, 소켓 자체가 다르므로 보드와 CPU는 한 세대로 맞춘다.",
        },
        {
            "id": "lga1700-memory",
            "title": "LGA1700 보드는 DDR4와 DDR5가 갈린다",
            "tags": "LGA1700 DDR4 DDR5",
            "text": "12·13·14세대 CPU는 같은 LGA1700이어도 메인보드가 DDR4 전용인지 DDR5 전용인지 먼저 본다. 메모리 세대는 CPU가 아니라 보드가 결정한다. 모델명에 DDR4가 적힌 보드는 DDR5와 섞지 않는다.",
        },
        {
            "id": "dual-channel",
            "title": "메모리는 두 장으로",
            "tags": "메모리 듀얼채널",
            "text": "게임과 영상 작업 모두 메모리 두 장 구성이 한 장보다 여유가 있다. 32GB를 권할 때는 16GB 두 장, 이미 두 장으로 나온 킷을 고르는 편이 낫다.",
        },
        {
            "id": "psu-headroom",
            "title": "파워는 GPU TDP보다 넓게",
            "tags": "파워 전력 GPU",
            "text": "그래픽카드 TDP에 CPU와 드라이브 여유를 더한다. 대략 그래픽 TDP의 1.6배에 200W를 더한 용량보다 파워 정격이 낮으면 순간 부하에서 꺼질 수 있다. 4070 SUPER급은 750W, 4080·5080·4090급은 850W에서 1000W를 본다.",
        },
        {
            "id": "case-board",
            "title": "케이스보다 보드가 크면 들어가지 않는다",
            "tags": "케이스 ATX M-ATX Mini-ITX",
            "text": "Mini-ITX 케이스에는 Mini-ITX 보드만, M-ATX 케이스에는 M-ATX와 Mini-ITX가 들어간다. ATX 보드는 ATX 케이스가 필요하다. 보드가 케이스 지원 규격보다 크면 조립이 불가능하다.",
        },
        {
            "id": "x3d-heat",
            "title": "X3D 프로세서는 캐시 온도를 본다",
            "tags": "7800X3D 9800X3D 쿨러",
            "text": "7800X3D와 9800X3D는 게임 성능이 좋지만 적층 캐시 때문에 쿨러를 얇은 번들로 끝내기 어렵다. 타워형 공랭이나 240mm 이상 수랭을 같이 보는 편이 안전하다.",
        },
        {
            "id": "used-grade",
            "title": "중고 등급은 가격만큼 상태를 본다",
            "tags": "중고 S급 A급 B급 미개봉",
            "text": "이 카탈로그에서 미개봉과 새상품은 신품 채널이다. S급은 사용감이 적은 중고, A급은 생활 사용감, B급은 가격이 낮은 대신 외관과 동작 확인이 더 필요한 매물로 구분한다. 등급은 판매 문구의 참고치이지 보증이 아니다.",
        },
        {
            "id": "vram-ai",
            "title": "로컬 AI는 VRAM이 먼저다",
            "tags": "AI 학습 VRAM",
            "text": "로컬에서 모델을 올릴 때는 코어 수보다 그래픽카드 VRAM이 먼저 병목이 된다. 7B급을 여유 있게 보려면 12GB 이상, 더 큰 양자화 모델을 보려면 16GB 이상을 후보에 둔다. 게임만 한다면 같은 예산에서 코어 클럭 쪽을 봐도 된다.",
        },
        {
            "id": "noise-mesh",
            "title": "소음은 케이스 소재와 팬에서 갈린다",
            "tags": "소음 메시 강화유리",
            "text": "메시 전면은 같은 팬 속도에서 강화유리 밀폐형보다 온도가 낮아 팬을 천천히 돌릴 수 있다. 강화유리는 보여 주기에 유리하고, 플라스틱 보급형 케이스는 진동이 남기 쉽다. 소음을 우선하면 메시 또는 흡음이 있는 스틸 케이스와 낮은 소음 쿨러를 같이 고른다.",
        },
        {
            "id": "material-note",
            "title": "소재는 온도보다 만지는 느낌과 무게에 남는다",
            "tags": "소재 알루미늄 스틸 강화유리 PBT",
            "text": "알루미늄 슈라우드와 메탈 백플레이트는 플라스틱보다 무겁고 발열이 케이스 안으로 퍼지는 방식이 다르다. 키보드의 PBT 키캡은 ABS보다 반들거림이 적다. 케이스의 우드와 강화유리는 온도와 별개로 공간의 인상을 바꾼다. 소재 필터는 성능 점수가 아니라 이런 차이를 고르라고 있다.",
        },
        {
            "id": "shop-mix",
            "title": "쇼핑몰을 나누면 가격이 갈리고 배송도 갈린다",
            "tags": "쿠팡 컴퓨존 다나와 중고",
            "text": "같은 모델도 쿠팡, 11번가, 컴퓨존, 다나와, 오버시스템, 샵다나와의 기준 시세가 조금씩 다르다. 중고는 번개장터, 중고나라, 당근마켓으로 따로 둔다. 한 쇼핑몰로 묶으면 배송과 반품이 단순하고, 나누면 부품별 최저가에 가까워지는 대신 일정과 보증이 흩어진다.",
        },
        {
            "id": "price-kind",
            "title": "이 파일의 가격은 기준 시세다",
            "tags": "기준 시세 카탈로그",
            "text": "카탈로그 가격은 2026-11-01에 정리한 국내 유통 모델의 기준 시세다. 쿠폰, 카드 할인, 중고 흥정은 반영하지 않았다. 파일을 고치면 다음 조회부터 그 금액으로 걸러진다. 결제 버튼의 실시간 가격으로 읽지 않는다.",
        },
        {
            "id": "ssd-boot",
            "title": "부팅 드라이브는 SSD로",
            "tags": "SSD HDD",
            "text": "운영체제와 게임은 SSD에 두고, HDD는 영상 원본이나 백업처럼 용량이 큰 자료에 쓴다. 1TB는 게임 몇 개면 금방 차서, 게이밍과 영상편집은 2TB를 후보에 둔다.",
        },
        {
            "id": "aio-case",
            "title": "수랭 라디에이터가 들어갈 자리",
            "tags": "수랭 케이스 쿨러",
            "text": "360 수랭은 상단이나 전면에 360mm 자리가 있는 ATX 케이스를 전제로 한다. Mini-ITX 케이스에는 타워형 공랭 높이와 라디에이터 길이가 먼저 걸린다. 케이스 폼팩터를 Mini-ITX로 좁혔으면 360 수랭을 같이 담지 않는 편이 안전하다.",
        },
        {
            "id": "office-idle",
            "title": "사무용은 전력과 소음을 내린다",
            "tags": "사무 전력 소음",
            "text": "문서와 브라우저가 중심이면 고전력 그래픽카드보다 65W급 CPU, 낮은 소음 전원, 24인치 모니터가 예산에 맞다. 남는 예산은 메모리 32GB와 SSD 용량에 두는 편이 체감이 크다.",
        },
        {
            "id": "edit-balance",
            "title": "영상편집은 CPU와 메모리와 저장이 같이 간다",
            "tags": "영상편집",
            "text": "타임라인 작업은 코어가 많은 CPU, 32GB 이상 메모리, 2TB급 SSD가 함께 있어야 한다. 그래픽카드는 프리뷰와 일부 인코딩에 쓰이므로 12GB 이상 VRAM을 후보에 두되, CPU를 너무 낮은 등급으로 내리면 미리보기가 먼저 막힌다.",
        },
        {
            "id": "color-build",
            "title": "색을 맞추면 부품이 한 세트로 보인다",
            "tags": "색상 블랙 화이트",
            "text": "블랙과 화이트를 섞으면 조립 사진에서 부품이 따로 논다. 색 필터는 호환을 보장하지 않고, 케이스와 보드와 메모리의 보이는 면을 맞출 때 쓴다.",
        },
        {
            "id": "f-suffix",
            "title": "F 모델은 내장 그래픽이 없다",
            "tags": "7500F 12400F 14400F",
            "text": "7500F, 12400F, 14400F, 14600KF처럼 모델명에 F가 있으면 내장 그래픽이 없다. 화면을 내려면 그래픽카드가 필요하다. 사무용으로 CPU만 담고 그래픽카드를 빼면 모니터에 신호가 가지 않는다.",
        },
    ]


def keep_urls(listings: list[dict]) -> None:
    if not CATALOG_PATH.exists():
        return
    try:
        current = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    urls = {item["id"]: item["url"] for item in current.get("products", []) if item.get("url")}
    for item in listings:
        if item["id"] in urls:
            item["url"] = urls[item["id"]]


def main() -> None:
    listings = expand(bases())
    keep_urls(listings)
    catalog = {
        "snapshot": "2026-11-01",
        "price_kind": "catalog_reference",
        "currency": "KRW",
        "note": "2026-11-01 국내 유통 모델의 쇼핑몰별 기준 시세입니다. 결제 화면의 실시간 가격이 아니며, 이 파일을 고치면 다음 조회에 반영됩니다.",
        "products": listings,
    }
    docs = knowledge()
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    KNOWLEDGE_PATH.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"products {len(listings)} -> {CATALOG_PATH}")
    print(f"knowledge {len(docs)} -> {KNOWLEDGE_PATH}")


if __name__ == "__main__":
    main()
