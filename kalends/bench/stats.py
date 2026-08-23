"""Small statistics helpers (stdlib only). Nothing clever: means, spread,
t-based confidence intervals, paired differences with Cohen's d_z."""
from __future__ import annotations

import math
import statistics


def t_critical(df: int, level: float = 0.95) -> float:
    """Two-sided t critical value, small lookup + normal tail. Good to ~1%."""
    table_95 = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45,
                7: 2.36, 8: 2.31, 9: 2.26, 10: 2.23, 12: 2.18, 15: 2.13,
                20: 2.09, 25: 2.06, 30: 2.04, 40: 2.02, 60: 2.00, 100: 1.98}
    if level != 0.95:
        raise ValueError("only 95% implemented")
    if df <= 0:
        return float("nan")
    keys = sorted(table_95)
    for k in keys:
        if df <= k:
            return table_95[k]
    return 1.96


def summarize(xs: list[float]) -> dict:
    """mean / sd / median / 95% CI half-width / n for one metric across seeds."""
    n = len(xs)
    if n == 0:
        return {"n": 0}
    mean = statistics.fmean(xs)
    sd = statistics.stdev(xs) if n > 1 else 0.0
    half = t_critical(n - 1) * sd / math.sqrt(n) if n > 1 else 0.0
    return {"mean": round(mean, 4), "sd": round(sd, 4),
            "median": round(statistics.median(xs), 4),
            "ci95": [round(mean - half, 4), round(mean + half, 4)], "n": n}


def paired(xs: list[float], ys: list[float]) -> dict:
    """Paired comparison x - y over the same seeds: mean difference, 95% CI,
    Cohen's d_z (mean diff / sd of diffs). Positive = x better."""
    assert len(xs) == len(ys) and xs
    diffs = [a - b for a, b in zip(xs, ys)]
    n = len(diffs)
    mean = statistics.fmean(diffs)
    sd = statistics.stdev(diffs) if n > 1 else 0.0
    half = t_critical(n - 1) * sd / math.sqrt(n) if n > 1 else 0.0
    d_z = mean / sd if sd > 0 else float("inf") if mean != 0 else 0.0
    return {"mean_diff": round(mean, 4),
            "ci95": [round(mean - half, 4), round(mean + half, 4)],
            "cohen_dz": round(d_z, 3) if d_z != float("inf") else "inf",
            "n": n}
