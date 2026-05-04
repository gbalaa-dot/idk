from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm


def runs_test(binary: pd.Series) -> tuple[float, float]:
    x = binary.dropna().astype(int).tolist()
    if len(x) < 2:
        return float("nan"), float("nan")
    n1 = sum(x)
    n0 = len(x) - n1
    if n1 == 0 or n0 == 0:
        return float("nan"), float("nan")
    runs = 1 + sum(1 for i in range(1, len(x)) if x[i] != x[i - 1])
    mu = (2 * n1 * n0) / (n1 + n0) + 1
    var = (2 * n1 * n0 * (2 * n1 * n0 - n1 - n0)) / (((n1 + n0) ** 2) * (n1 + n0 - 1))
    z = (runs - mu) / np.sqrt(var)
    p = 2 * (1 - norm.cdf(abs(z)))
    return float(z), float(p)


def compute_stats(df: pd.DataFrame, threshold: float = 2.0) -> dict:
    s = df["crash_multiplier"].astype(float)
    ts = df.set_index("timestamp_utc")["crash_multiplier"].astype(float)
    low = s < threshold
    high = s >= threshold
    return {
        "total_rounds": int(len(df)),
        "average": float(s.mean()),
        "median": float(s.median()),
        "min": float(s.min()),
        "max": float(s.max()),
        "below_1_1": int((s < 1.1).sum()),
        "below_1_5": int((s < 1.5).sum()),
        "below_2": int((s < 2.0).sum()),
        "below_5": int((s < 5.0).sum()),
        "below_10": int((s < 10.0).sum()),
        "rolling_avg_1h": float(ts.rolling("1h").mean().iloc[-1]) if not ts.empty else np.nan,
        "rolling_avg_10h": float(ts.rolling("10h").mean().iloc[-1]) if not ts.empty else np.nan,
        "rolling_avg_100h": float(ts.rolling("100h").mean().iloc[-1]) if not ts.empty else np.nan,
        "longest_streak_below_2": _longest_streak(low),
        "longest_streak_ge_2": _longest_streak(high),
        "autocorr_lags_1_50": {lag: float(s.autocorr(lag=lag)) for lag in range(1, 51)},
        "runs_test": runs_test((s >= threshold).astype(int)),
    }


def _longest_streak(mask: pd.Series) -> int:
    best = cur = 0
    for v in mask.tolist():
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best
