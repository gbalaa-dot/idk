from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests
import websocket

from src.config import AppConfig
from src.database import CrashDatabase
from src.parser import parse_round

logger = logging.getLogger(__name__)


def _handle_payload(data: Any, db: CrashDatabase, source: str) -> int:
    inserted = 0
    candidates = data if isinstance(data, list) else [data]
    for item in candidates:
        if not isinstance(item, dict):
            continue
        parsed = parse_round(item)
        if not parsed:
            continue
        ok = db.insert_round(source=source, **parsed)
        inserted += int(ok)
    return inserted


def collect_polling(config: AppConfig, db: CrashDatabase) -> None:
    logger.info("Starting polling mode")
    while True:
        try:
            resp = requests.get(config.endpoint_url, headers=config.headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            count = _handle_payload(data, db, source="polling")
            logger.info("Polling cycle complete. Inserted: %s", count)
        except Exception as exc:
            logger.error("Polling error: %s", exc)
        time.sleep(max(config.poll_interval_seconds, 1))


def collect_websocket(config: AppConfig, db: CrashDatabase) -> None:
    logger.info("Starting websocket mode")

    def on_message(ws: websocket.WebSocketApp, message: str) -> None:
        try:
            payload = json.loads(message)
            count = _handle_payload(payload, db, source="websocket")
            if count:
                logger.info("Inserted %s rounds from websocket message", count)
        except Exception as exc:
            logger.error("WS message parse error: %s", exc)

    def on_error(ws: websocket.WebSocketApp, error: Any) -> None:
        logger.error("WS error: %s", error)

    def on_open(ws: websocket.WebSocketApp) -> None:
        logger.info("WebSocket connection opened")
        if config.ws_subscribe_message:
            ws.send(json.dumps(config.ws_subscribe_message))

    while True:
        try:
            ws = websocket.WebSocketApp(
                config.endpoint_url,
                header=[f"{k}: {v}" for k, v in config.headers.items()],
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
            )
            ws.run_forever()
        except Exception as exc:
            logger.error("Websocket loop error: %s", exc)
        logger.info("Reconnecting websocket in 5s...")
        time.sleep(5)


def run_collector(config: AppConfig, db: CrashDatabase) -> None:
    if not config.endpoint_url:
        raise ValueError("endpoint_url is empty in config.yaml")
    if config.mode == "polling":
        collect_polling(config, db)
    else:
        collect_websocket(config, db)
