"""키가 있으면 live.json이 오래됐을 때 백그라운드에서 다시 모은다."""

from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime

from app.ingest import naver

logger = logging.getLogger(__name__)

CHECK_EVERY_S = 600
_lock = threading.Lock()
_state: dict = {"running": False, "last_error": "", "last_result": None}


def refresh_hours() -> float:
    try:
        return max(0.5, float(os.getenv("LIVE_REFRESH_HOURS", "6")))
    except ValueError:
        return 6.0


def age_hours() -> float | None:
    if not naver.LIVE_PATH.exists():
        return None
    return (time.time() - naver.LIVE_PATH.stat().st_mtime) / 3600


def run_once() -> bool:
    if not _lock.acquire(blocking=False):
        return False
    _state["running"] = True
    try:
        result = naver.refresh()
        _state["last_result"] = result
        _state["last_error"] = ""
        logger.info("live.json 갱신: %s", result)
    except Exception as exc:
        _state["last_error"] = str(exc)
        logger.warning("live.json 갱신 실패: %s", exc)
    finally:
        _state["running"] = False
        _lock.release()
    return True


def start_background() -> None:
    if os.getenv("LIVE_REFRESH", "on").lower() in ("off", "0", "false"):
        return

    def loop() -> None:
        while True:
            if naver.keys():
                age = age_hours()
                if age is None or age >= refresh_hours():
                    run_once()
            time.sleep(CHECK_EVERY_S)

    threading.Thread(target=loop, name="live-refresh", daemon=True).start()


def status() -> dict:
    age = age_hours()
    fetched = None
    if naver.LIVE_PATH.exists():
        fetched = datetime.fromtimestamp(naver.LIVE_PATH.stat().st_mtime).isoformat(timespec="seconds")
    return {
        "live": "on" if naver.keys() else "no_keys",
        "live_running": _state["running"],
        "live_updated_at": fetched or "",
        "live_age_hours": round(age, 2) if age is not None else None,
        "live_last_error": _state["last_error"],
    }
