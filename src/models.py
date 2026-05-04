from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression


FEATURE_COLUMNS = [
    "previous_multiplier",
    "mean_last_5",
    "mean_last_10",
    "mean_last_25",
    "mean_last_50",
    "std_last_10",
    "std_last_50",
    "count_below_2_last_10",
    "count_above_5_last_50",
    "streak_below_2",
    "streak_ge_2",
    "since_last_10x",
]


def create_features(df: pd.DataFrame, threshold: float = 2.0) -> pd.DataFrame:
    s = df["crash_multiplier"].astype(float).reset_index(drop=True)
    out = pd.DataFrame(index=df.index)
    out["previous_multiplier"] = s.shift(1)
    out["mean_last_5"] = s.shift(1).rolling(5).mean()
    out["mean_last_10"] = s.shift(1).rolling(10).mean()
    out["mean_last_25"] = s.shift(1).rolling(25).mean()
    out["mean_last_50"] = s.shift(1).rolling(50).mean()
    out["std_last_10"] = s.shift(1).rolling(10).std()
    out["std_last_50"] = s.shift(1).rolling(50).std()
    out["count_below_2_last_10"] = (s.shift(1) < threshold).rolling(10).sum()
    out["count_above_5_last_50"] = (s.shift(1) > 5.0).rolling(50).sum()

    streak_low, streak_high, since_10 = [], [], []
    low = high = 0
    last_10_idx = None
    for i, v in enumerate(s.tolist()):
        streak_low.append(low)
        streak_high.append(high)
        since_10.append(i - last_10_idx if last_10_idx is not None else np.nan)
        if v < threshold:
            low += 1
            high = 0
        else:
            high += 1
            low = 0
        if v >= 10.0:
            last_10_idx = i

    out["streak_below_2"] = streak_low
    out["streak_ge_2"] = streak_high
    out["since_last_10x"] = since_10
    out["target_next"] = (s.shift(-1) >= threshold).astype(float)
    return out


@dataclass
class ModelBundle:
    name: str
    model: BaseEstimator | None


def get_models() -> list[ModelBundle]:
    models = [
        ModelBundle("logistic_regression", LogisticRegression(max_iter=2000)),
        ModelBundle("random_forest", RandomForestClassifier(n_estimators=300, random_state=42)),
    ]
    try:
        from xgboost import XGBClassifier  # type: ignore

        models.append(ModelBundle("xgboost", XGBClassifier(n_estimators=200, random_state=42, eval_metric="logloss")))
    except Exception:
        pass
    return models
