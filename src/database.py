from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


SCHEMA = """
CREATE TABLE IF NOT EXISTS rounds (
    id INTEGER PRIMARY KEY,
    round_id TEXT UNIQUE,
    timestamp_utc TEXT,
    crash_multiplier REAL,
    source TEXT,
    raw_json TEXT,
    created_at TEXT
);
"""


class CrashDatabase:
    def __init__(self, path: str) -> None:
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute(SCHEMA)
        self.conn.commit()

    def insert_round(
        self,
        round_id: str,
        timestamp_utc: str,
        crash_multiplier: float,
        source: str,
        raw_json: dict,
    ) -> bool:
        created_at = datetime.now(timezone.utc).isoformat()
        payload = (
            round_id,
            timestamp_utc,
            float(crash_multiplier),
            source,
            json.dumps(raw_json, ensure_ascii=False),
            created_at,
        )
        try:
            self.conn.execute(
                """
                INSERT INTO rounds (round_id, timestamp_utc, crash_multiplier, source, raw_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def to_dataframe(self) -> pd.DataFrame:
        df = pd.read_sql_query(
            "SELECT * FROM rounds ORDER BY timestamp_utc ASC, id ASC",
            self.conn,
        )
        if not df.empty:
            df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
        return df

    def export_csv(self, out_path: str) -> None:
        self.to_dataframe().to_csv(out_path, index=False)

    def import_csv(self, csv_path: str) -> int:
        df = pd.read_csv(csv_path)
        required = {"round_id", "timestamp_utc", "crash_multiplier", "source", "raw_json"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")
        count = 0
        for _, row in df.iterrows():
            raw_json = row["raw_json"]
            if isinstance(raw_json, str):
                try:
                    raw_json = json.loads(raw_json)
                except json.JSONDecodeError:
                    raw_json = {"raw": raw_json}
            inserted = self.insert_round(
                round_id=str(row["round_id"]),
                timestamp_utc=str(row["timestamp_utc"]),
                crash_multiplier=float(row["crash_multiplier"]),
                source=str(row.get("source", "csv")),
                raw_json=raw_json,
            )
            count += int(inserted)
        return count

    def close(self) -> None:
        self.conn.close()
