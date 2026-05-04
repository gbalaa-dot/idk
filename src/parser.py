from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def _dig(obj: Any, keys: list[str]) -> Any:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in keys:
                return v
            found = _dig(v, keys)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for i in obj:
            found = _dig(i, keys)
            if found is not None:
                return found
    return None


def parse_round(payload: dict[str, Any]) -> dict[str, Any] | None:
    rid = _dig(payload, ["roundid", "round_id", "id", "gameid", "hash"])
    multiplier = _dig(payload, ["crashmultiplier", "crash_multiplier", "multiplier", "crash", "result"])
    timestamp = _dig(payload, ["timestamp", "time", "createdat", "endedat", "ended_at"])

    if multiplier is None:
        return None

    try:
        multiplier_f = float(multiplier)
    except (TypeError, ValueError):
        return None

    if isinstance(timestamp, (int, float)):
        timestamp_iso = datetime.fromtimestamp(float(timestamp), tz=timezone.utc).isoformat()
    elif isinstance(timestamp, str) and timestamp:
        try:
            timestamp_iso = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
        except ValueError:
            timestamp_iso = datetime.now(timezone.utc).isoformat()
    else:
        timestamp_iso = datetime.now(timezone.utc).isoformat()

    raw_text = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    if rid is None:
        rid = hashlib.sha256(f"{timestamp_iso}|{multiplier_f}|{raw_text}".encode("utf-8")).hexdigest()[:32]

    return {
        "round_id": str(rid),
        "timestamp_utc": timestamp_iso,
        "crash_multiplier": multiplier_f,
        "raw_json": payload,
    }
