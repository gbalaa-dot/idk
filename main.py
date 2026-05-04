from __future__ import annotations

import argparse
import json
import logging

from src.backtest import evaluate_models
from src.collector import run_collector
from src.config import load_config
from src.database import CrashDatabase
from src.graphs import generate_graphs
from src.stats import compute_stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Passive Bloxflip crash analysis tool")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("collect")
    sub.add_parser("stats")
    sub.add_parser("graph")
    sub.add_parser("backtest")
    sub.add_parser("export-csv")
    imp = sub.add_parser("import-csv")
    imp.add_argument("path")

    args = parser.parse_args()
    cfg = load_config()
    db = CrashDatabase(cfg.database_path)

    try:
        if args.command == "collect":
            run_collector(cfg, db)
        elif args.command == "stats":
            df = db.to_dataframe()
            if df.empty:
                print("No data in database.")
                return
            print(json.dumps(compute_stats(df, threshold=cfg.target_threshold), indent=2))
        elif args.command == "graph":
            df = db.to_dataframe()
            if df.empty:
                print("No data in database.")
                return
            bt = evaluate_models(df, threshold=cfg.target_threshold)
            generate_graphs(df, bt)
            print("Saved graphs to ./graphs")
        elif args.command == "backtest":
            df = db.to_dataframe()
            if df.empty:
                print("No data in database.")
                return
            bt = evaluate_models(df, threshold=cfg.target_threshold)
            print(json.dumps(bt, indent=2))
            c = bt["conclusion"]
            print("\nBacktest interpretation:")
            print(f"- Beats 50%: {c['beats_50_percent']}")
            print(f"- Beats majority baseline: {c['beats_majority_baseline']}")
            print(f"- Statistically meaningful: {c['statistically_meaningful']}")
            print(f"- Warning: {c['warning']}")
        elif args.command == "export-csv":
            out = "data/rounds_export.csv"
            db.export_csv(out)
            print(f"Exported to {out}")
        elif args.command == "import-csv":
            inserted = db.import_csv(args.path)
            print(f"Imported {inserted} new rows")
    finally:
        db.close()


if __name__ == "__main__":
    main()
