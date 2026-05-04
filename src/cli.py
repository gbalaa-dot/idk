from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.backtest import evaluate_models
from src.collector import run_collector
from src.config import AppConfig
from src.database import CrashDatabase
from src.graphs import generate_graphs
from src.stats import compute_stats

console = Console()


def cmd_collect(config: AppConfig, db: CrashDatabase) -> None:
    run_collector(config, db)


def cmd_stats(config: AppConfig, db: CrashDatabase) -> None:
    df = db.to_dataframe()
    if df.empty:
        console.print("[yellow][STATS] No data in database.[/yellow]")
        return
    stats = compute_stats(df, threshold=config.target_threshold)
    table = Table(title="Crash Stats", show_lines=True)
    table.add_column("Metric")
    table.add_column("Value")
    for k, v in stats.items():
        if k == "autocorr_lags_1_50":
            continue
        table.add_row(k, str(v))
    console.print(table)


def cmd_graph(config: AppConfig, db: CrashDatabase) -> None:
    df = db.to_dataframe()
    if df.empty:
        console.print("[yellow][INFO] No data in database.[/yellow]")
        return
    bt = evaluate_models(df, threshold=config.target_threshold)
    generate_graphs(df, bt)
    console.print("[green][INFO] Saved graphs to ./graphs[/green]")


def cmd_backtest(config: AppConfig, db: CrashDatabase) -> None:
    df = db.to_dataframe()
    if df.empty:
        console.print("[yellow][INFO] No data in database.[/yellow]")
        return
    bt = evaluate_models(df, threshold=config.target_threshold)
    console.print(Panel.fit("Backtest Results", style="cyan"))
    console.print_json(json.dumps(bt))


def cmd_export_csv(db: CrashDatabase, out_path: str = "data/rounds_export.csv") -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    db.export_csv(out_path)
    console.print(f"[green][INFO] Exported CSV to {out_path}[/green]")


def cmd_import_csv(db: CrashDatabase, path: str) -> None:
    inserted = db.import_csv(path)
    console.print(f"[green][INFO] Imported {inserted} rows[/green]")
