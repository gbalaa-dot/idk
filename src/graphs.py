from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def generate_graphs(df: pd.DataFrame, backtest_results: dict | None = None) -> None:
    out = Path("graphs")
    out.mkdir(parents=True, exist_ok=True)

    sdf = df.sort_values("timestamp_utc").copy()
    sdf["timestamp_utc"] = pd.to_datetime(sdf["timestamp_utc"], utc=True, errors="coerce")
    s = sdf["crash_multiplier"].astype(float)

    plt.figure(); plt.plot(sdf["timestamp_utc"], s); plt.title("Multiplier Over Time"); plt.tight_layout(); plt.savefig(out / "multiplier_over_time.png"); plt.close()
    plt.figure(); plt.hist(s, bins=50); plt.title("Histogram"); plt.tight_layout(); plt.savefig(out / "histogram.png"); plt.close()
    plt.figure(); plt.hist(s[s > 0], bins=50, log=True); plt.title("Log Histogram"); plt.tight_layout(); plt.savefig(out / "log_histogram.png"); plt.close()

    ts = sdf.set_index("timestamp_utc")["crash_multiplier"]
    for window, name in [("1h", "rolling_average_1h.png"), ("10h", "rolling_average_10h.png"), ("100h", "rolling_average_100h.png")]:
        plt.figure(); ts.rolling(window).mean().plot(); plt.title(f"Rolling Average {window}"); plt.tight_layout(); plt.savefig(out / name); plt.close()

    autocorr = [s.autocorr(lag=i) for i in range(1, 51)]
    plt.figure(); plt.bar(range(1, 51), autocorr); plt.title("Autocorrelation (1-50)"); plt.tight_layout(); plt.savefig(out / "autocorrelation.png"); plt.close()

    plt.figure()
    if backtest_results and "walk_forward" in backtest_results and backtest_results["walk_forward"]:
        acc = backtest_results["walk_forward"].get("accuracy", 0)
        plt.plot([acc], marker="o")
    else:
        plt.plot([0], marker="o")
    plt.title("Prediction Accuracy Over Time (summary)")
    plt.tight_layout(); plt.savefig(out / "prediction_accuracy_over_time.png"); plt.close()
