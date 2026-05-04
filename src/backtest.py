from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

from src.models import FEATURE_COLUMNS, create_features, get_models


def evaluate_models(df: pd.DataFrame, threshold: float = 2.0) -> dict[str, Any]:
    feats = create_features(df, threshold=threshold).dropna().reset_index(drop=True)
    X = feats[FEATURE_COLUMNS]
    y = feats["target_next"].astype(int)
    split = int(len(feats) * 0.7)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    majority = int(y_train.mean() >= 0.5)
    base_preds = np.full(len(y_test), majority)
    results: dict[str, Any] = {
        "baseline_majority": _metrics(y_test, base_preds, probs=None)
    }

    # Rolling-window heuristic
    rolling_preds = (X_test["mean_last_10"] >= threshold).astype(int).values
    results["rolling_window"] = _metrics(y_test, rolling_preds, probs=rolling_preds)

    for bundle in get_models():
        m = bundle.model
        if m is None:
            continue
        m.fit(X_train, y_train)
        preds = m.predict(X_test)
        probs = m.predict_proba(X_test)[:, 1] if hasattr(m, "predict_proba") else preds
        results[bundle.name] = _metrics(y_test, preds, probs=probs)

    results["walk_forward"] = walk_forward_validation(feats, threshold=threshold)
    results["conclusion"] = summarize_results(results)
    return results


def walk_forward_validation(feats: pd.DataFrame, threshold: float = 2.0, step: int = 100) -> dict[str, Any]:
    X = feats[FEATURE_COLUMNS]
    y = feats["target_next"].astype(int)
    start = max(200, int(len(feats) * 0.3))
    preds, actual = [], []
    for i in range(start, len(feats), step):
        X_train, y_train = X.iloc[:i], y.iloc[:i]
        X_test, y_test = X.iloc[i : i + step], y.iloc[i : i + step]
        if len(X_test) == 0:
            break
        m = __import__("sklearn.linear_model", fromlist=["LogisticRegression"]).LogisticRegression(max_iter=2000)
        m.fit(X_train, y_train)
        p = m.predict(X_test)
        preds.extend(p.tolist())
        actual.extend(y_test.tolist())
    return _metrics(np.array(actual), np.array(preds), probs=np.array(preds)) if actual else {}


def _metrics(y_true: Any, y_pred: Any, probs: Any = None) -> dict[str, Any]:
    out = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    try:
        out["roc_auc"] = float(roc_auc_score(y_true, probs))
    except Exception:
        out["roc_auc"] = float("nan")
    return out


def summarize_results(results: dict[str, Any]) -> dict[str, Any]:
    baseline = results["baseline_majority"]["accuracy"]
    best_name, best_acc = None, -1.0
    for name, vals in results.items():
        if isinstance(vals, dict) and "accuracy" in vals and name != "baseline_majority":
            if vals["accuracy"] > best_acc:
                best_acc = vals["accuracy"]
                best_name = name
    p_value = float(binomtest(int(best_acc * 1000), 1000, p=0.5, alternative="greater").pvalue) if best_acc >= 0 else 1.0
    return {
        "best_model": best_name,
        "best_accuracy": best_acc,
        "beats_50_percent": bool(best_acc > 0.5),
        "beats_majority_baseline": bool(best_acc > baseline),
        "statistically_meaningful": bool(p_value < 0.05),
        "p_value_vs_50pct": p_value,
        "warning": "Possible overfitting/random noise if walk-forward is unstable or gains are small.",
    }
