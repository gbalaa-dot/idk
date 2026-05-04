from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

import requests
import websocket
from rich.console import Console
from rich.live import Live
from rich.table import Table

from src.config import AppConfig
from src.database import CrashDatabase
from src.parser import parse_round

logger = logging.getLogger(__name__)
console = Console()


def _status_table(count: int, latest: float | None, average: float | None, started_at: float) -> Table:
    t = Table(title="Live Collection Status")
    t.add_column("Rounds")
    t.add_column("Latest")
    t.add_column("Average")
    t.add_column("Runtime")
    runtime = int(time.time() - started_at)
    t.add_row(str(count), f"{latest:.2f}x" if latest is not None else "-", f"{average:.2f}x" if average is not None else "-", f"{runtime}s")
    return t


def _handle_payload(data: Any, db: CrashDatabase, source: str) -> tuple[int, float | None]:
    inserted = 0
    latest = None
    candidates = data if isinstance(data, list) else [data]
    for item in candidates:
        if not isinstance(item, dict):
            continue
        parsed = parse_round(item)
        if not parsed:
            continue
        ok = db.insert_round(source=source, **parsed)
        if ok:
            latest = float(parsed["crash_multiplier"])
            console.print(f"[INFO] Collected round: {latest:.2f}x")
        inserted += int(ok)
    return inserted, latest


def collect_polling(config: AppConfig, db: CrashDatabase, duration_seconds: int | None = None) -> None:
    count = 0
    total = 0.0
    latest = None
    started = time.time()
    with Live(_status_table(count, latest, None, started), refresh_per_second=2, console=console) as live:
        while True:
            if duration_seconds and time.time() - started >= duration_seconds:
                return
            try:
                resp = requests.get(config.endpoint_url, headers=config.headers, timeout=20)
                resp.raise_for_status()
                c, l = _handle_payload(resp.json(), db, source="polling")
                count += c
                if l is not None:
                    latest = l
                    total += l
            except Exception as exc:
                console.print(f"[ERROR] Failed to parse response: {exc}")
            avg = (total / count) if count else None
            live.update(_status_table(count, latest, avg, started))
            time.sleep(max(config.poll_interval_seconds, 1))


def collect_websocket(config: AppConfig, db: CrashDatabase, duration_seconds: int | None = None) -> None:
    state = {"count": 0, "sum": 0.0, "latest": None, "started": time.time(), "stop": False}

    def on_message(ws: websocket.WebSocketApp, message: str) -> None:
        try:
            payload = json.loads(message)
            c, l = _handle_payload(payload, db, source="websocket")
            state["count"] += c
            if l is not None:
                state["latest"] = l
                state["sum"] += l
        except Exception as exc:
            console.print(f"[ERROR] Failed to parse response: {exc}")

    def on_open(ws: websocket.WebSocketApp) -> None:
        if config.ws_subscribe_message:
            ws.send(json.dumps(config.ws_subscribe_message))

    with Live(_status_table(0, None, None, state["started"]), refresh_per_second=2, console=console) as live:
        while True:
            if duration_seconds and time.time() - state["started"] >= duration_seconds:
                return
            try:
                ws = websocket.WebSocketApp(config.endpoint_url, header=[f"{k}: {v}" for k, v in config.headers.items()], on_open=on_open, on_message=on_message)
                ws.run_forever(ping_interval=30, ping_timeout=10)
            except Exception as exc:
                logger.error("Websocket error: %s", exc)
            avg = (state["sum"] / state["count"]) if state["count"] else None
            live.update(_status_table(state["count"], state["latest"], avg, state["started"]))
            time.sleep(2)


def run_collector(config: AppConfig, db: CrashDatabase, duration_seconds: int | None = None) -> None:
    if not config.endpoint_url:
        raise ValueError("endpoint_url is empty in config.yaml")
    if config.mode == "polling":
        collect_polling(config, db, duration_seconds=duration_seconds)
    else:
        collect_websocket(config, db, duration_seconds=duration_seconds)
