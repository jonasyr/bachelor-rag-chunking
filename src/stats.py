"""Statistics for the comparison of the chunking strategies (D44).

Pure functions. Inputs map a strategy to its per-question values, all lists in the same question
order (paired by question). A constant or otherwise untestable metric is reported with
``testable = False`` and without a p-value; nothing here returns NaN.
"""

from __future__ import annotations

import math
from itertools import combinations

import numpy as np
from scipy import stats as sps

from config import ANALYSIS_DIFF_DECIMALS


def _finite(x: float) -> float | None:
    x = float(x)
    return x if math.isfinite(x) else None


def _check_lengths(values: dict[str, list[float]]) -> int:
    lengths = {len(v) for v in values.values()}
    if len(lengths) > 1:
        raise ValueError(f"lists differ in length: {sorted(lengths)}")
    return lengths.pop() if lengths else 0


def friedman(values: dict[str, list[float]]) -> dict:
    """Friedman test over k >= 3 strategies; Kendall's W = chi2 / (n (k - 1)).

    scipy's statistic is tie-corrected, so W is too.
    """
    n = _check_lengths(values)
    k = len(values)
    untestable = {"statistic": None, "kendalls_w": None, "n": n, "testable": False}
    if n < 2 or k < 3:
        return untestable
    columns = [np.asarray(v, dtype=float) for v in values.values()]
    stacked = np.vstack(columns)
    # all strategies equal in every question: every block fully tied, chi2 undefined
    if np.all(stacked.max(axis=0) == stacked.min(axis=0)):
        return untestable
    res = sps.friedmanchisquare(*columns)
    statistic, p = _finite(res.statistic), _finite(res.pvalue)
    if statistic is None or p is None:
        return untestable
    return {
        "statistic": statistic,
        "p": p,
        "kendalls_w": statistic / (n * (k - 1)),
        "n": n,
        "testable": True,
    }


def wilcoxon_pair(a: list[float], b: list[float]) -> dict:
    """Two-sided Wilcoxon signed-rank test, zero differences dropped (``zero_method="wilcox"``).

    Normal approximation with tie correction and without continuity correction (exact p-values
    are not defined with ties); effect size r = |z| / sqrt(n_nonzero), unsigned, so the
    direction is ``median_diff`` (median of a - b). Differences are rounded to
    ``config.ANALYSIS_DIFF_DECIMALS`` places so that equal differences of fractional metrics
    (1 - 2/3 and 1/3) form one tie group despite float error.
    """
    if len(a) != len(b):
        raise ValueError(f"lists differ in length: {len(a)} vs {len(b)}")
    diff = np.round(np.asarray(a, dtype=float) - np.asarray(b, dtype=float), ANALYSIS_DIFF_DECIMALS)
    n_nonzero = int(np.count_nonzero(diff))
    if n_nonzero == 0:
        return {"statistic": None, "r": None, "n_nonzero": 0, "testable": False}
    res = sps.wilcoxon(diff, zero_method="wilcox", method="approx", correction=False)
    p, z = _finite(res.pvalue), _finite(res.zstatistic)
    if p is None or z is None:
        return {"statistic": None, "r": None, "n_nonzero": n_nonzero, "testable": False}
    return {
        "statistic": float(res.statistic),
        "p": p,
        "r": abs(z) / math.sqrt(n_nonzero),
        "median_diff": float(np.median(diff)),
        "n_nonzero": n_nonzero,
        "testable": True,
    }


def holm(pvalues: dict[str, float]) -> dict[str, float]:
    """Holm step-down adjustment: monotone, capped at 1, in the order of the input."""
    m = len(pvalues)
    adjusted: dict[str, float] = {}
    running = 0.0
    for rank, (key, p) in enumerate(sorted(pvalues.items(), key=lambda kv: kv[1])):
        running = max(running, min(1.0, (m - rank) * p))
        adjusted[key] = running
    return {key: adjusted[key] for key in pvalues}


def _pair_names(values: dict[str, list[float]]) -> list[tuple[str, str]]:
    return list(combinations(sorted(values), 2))


def confirmatory(metrics: dict[str, dict[str, list[float]]], alpha: float) -> dict:
    """Friedman per metric, Holm over the omnibus p; gated pairwise Wilcoxon, Holm over all pairs.

    Result per metric: the Friedman dict plus ``p_adj`` and ``significant``; ``pairs``
    ("C1-C2" -> Wilcoxon dict plus ``p_adj``) only for metrics with ``p_adj < alpha``.
    """
    result = {metric: friedman(values) for metric, values in metrics.items()}
    omnibus = {metric: r["p"] for metric, r in result.items() if r["testable"]}
    for metric, p_adj in holm(omnibus).items():
        result[metric]["p_adj"] = p_adj
    for r in result.values():
        r["significant"] = bool(r.get("p_adj", 1.0) < alpha)

    pair_p: dict[str, float] = {}
    for metric, r in result.items():
        if not r["significant"]:
            continue
        r["pairs"] = {}
        for x, y in _pair_names(metrics[metric]):
            pair = wilcoxon_pair(metrics[metric][x], metrics[metric][y])
            r["pairs"][f"{x}-{y}"] = pair
            if pair["testable"]:
                pair_p[f"{metric}|{x}-{y}"] = pair["p"]
    for key, p_adj in holm(pair_p).items():
        metric, name = key.split("|")
        result[metric]["pairs"][name]["p_adj"] = p_adj
    for r in result.values():
        for pair in r.get("pairs", {}).values():
            pair["significant"] = bool(pair.get("p_adj", 1.0) < alpha)
    return result


def effect_sizes(values: dict[str, list[float]]) -> dict:
    """Descriptive metrics: Kendall's W and pairwise r, without p-values."""
    omnibus = friedman(values)
    pairs = {}
    for x, y in _pair_names(values):
        pair = wilcoxon_pair(values[x], values[y])
        pairs[f"{x}-{y}"] = {"r": pair["r"], "n_nonzero": pair["n_nonzero"]}
    return {"kendalls_w": omnibus["kendalls_w"], "n": omnibus["n"], "pairs": pairs}


def spearman(x: list[float], y: list[float]) -> dict:
    """Spearman rank correlation; a constant input is reported as untestable."""
    if len(x) != len(y):
        raise ValueError(f"lists differ in length: {len(x)} vs {len(y)}")
    n = len(x)
    untestable = {"rho": None, "n": n, "testable": False}
    if n < 3 or len(set(x)) < 2 or len(set(y)) < 2:
        return untestable
    res = sps.spearmanr(x, y)
    rho, p = _finite(res.statistic), _finite(res.pvalue)
    if rho is None or p is None:
        return untestable
    return {"rho": rho, "p": p, "n": n, "testable": True}
