from __future__ import annotations

import argparse


from src.cli import cmd_backtest, cmd_collect, cmd_export_csv, cmd_graph, cmd_import_csv, cmd_stats
from src.config import load_config
from src.dashboard import create_app
from src.database import CrashDatabase


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Passive Bloxflip crash analysis tool")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("collect")
    sub.add_parser("stats")
    sub.add_parser("graph")
    sub.add_parser("backtest")
    sub.add_parser("export-csv")
    imp = sub.add_parser("import-csv")
    imp.add_argument("path")
    run_all = sub.add_parser("run_all")
    run_all.add_argument("--minutes", type=int, default=10)
    sub.add_parser("dashboard")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    cfg = load_config()
    db = CrashDatabase(cfg.database_path)
    try:
        if args.command == "collect":
            cmd_collect(cfg, db)
        elif args.command == "stats":
            cmd_stats(cfg, db)
        elif args.command == "graph":
            cmd_graph(cfg, db)
        elif args.command == "backtest":
            cmd_backtest(cfg, db)
        elif args.command == "export-csv":
            cmd_export_csv(db)
        elif args.command == "import-csv":
            cmd_import_csv(db, args.path)
        elif args.command == "run_all":
            cmd_collect(cfg, db) if args.minutes <= 0 else __import__("src.collector", fromlist=["run_collector"]).run_collector(cfg, db, duration_seconds=args.minutes * 60)
            cmd_stats(cfg, db)
            cmd_graph(cfg, db)
            cmd_backtest(cfg, db)
        elif args.command == "dashboard":
            db.close()
            import uvicorn
            uvicorn.run(create_app(cfg.database_path, cfg.target_threshold), host="127.0.0.1", port=8000)
            return
    finally:
        db.close()


if __name__ == "__main__":
    main()
