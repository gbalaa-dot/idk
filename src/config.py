from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass
class AppConfig:
    mode: str
    endpoint_url: str
    poll_interval_seconds: int
    database_path: str
    target_threshold: float
    timezone: str
    headers: dict[str, str]
    ws_subscribe_message: dict[str, Any] | None


def load_config(path: str = "config.yaml") -> AppConfig:
    load_dotenv()
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")

    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    return AppConfig(
        mode=str(raw.get("mode", "websocket")).lower(),
        endpoint_url=str(raw.get("endpoint_url", "")).strip(),
        poll_interval_seconds=int(raw.get("poll_interval_seconds", 5)),
        database_path=str(raw.get("database_path", "data/crash_results.sqlite")),
        target_threshold=float(raw.get("target_threshold", 2.0)),
        timezone=str(raw.get("timezone", "UTC")),
        headers=raw.get("headers", {}) or {},
        ws_subscribe_message=raw.get("ws_subscribe_message"),
    )
