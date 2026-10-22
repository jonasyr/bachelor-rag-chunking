"""Statistics for the comparison of the chunking strategies (D44).

Pure functions. Inputs map a strategy to its per-question values, all lists in the same question
order (paired by question). A constant or otherwise untestable metric is reported with
``testable = False`` and without a p-value; nothing here returns NaN. Agreement measures of the
second rating (D46): Gwet's AC1/AC2, Krippendorff's alpha and a cluster bootstrap over questions.
"""

from __future__ import annotations

import math
from collections.abc import Callable
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


def ordinal_weights(q: int) -> list[list[float]]:
    """Gwet's ordinal weights ``w[k][l] = 1 - M(|k - l|) / M(q - 1)``, ``M(d) = d (d + 1) / 2``."""

    def m(d: int) -> float:
        return d * (d + 1) / 2

    top = m(q - 1)
    return [[1.0 - m(abs(k - c)) / top if top else 1.0 for c in range(q)] for k in range(q)]


def gwet_ac(
    pairs: list[tuple[int, int]], q: int, weights: list[list[float]] | None = None
) -> float | None:
    """Gwet's AC1 (``weights=None``, identity) or AC2 (weighted) for two raters, categories 0..q-1.

    ``pa`` is the mean weight of the rating pairs,
    ``pe = sum(w) / (q (q - 1)) * sum(pi_k (1 - pi_k))`` with ``pi_k`` the share of
    all ratings in category k. ``pe == 1`` (one category only) gives 1.0 when ``pa == 1``. No pairs
    give ``None`` (undefined); ratings outside ``range(q)`` raise ``ValueError``.
    """
    if weights is None:
        weights = [[1.0 if k == c else 0.0 for c in range(q)] for k in range(q)]
    if any(not 0 <= v < q for pair in pairs for v in pair):
        raise ValueError(f"rating outside range({q})")
    if not pairs:
        return None
    n = len(pairs)
    pa = sum(weights[a][b] for a, b in pairs) / n
    pi = [sum((a == k) + (b == k) for a, b in pairs) / (2 * n) for k in range(q)]
    total_w = sum(sum(row) for row in weights)
    pe = total_w / (q * (q - 1)) * sum(p * (1 - p) for p in pi) if q > 1 else 1.0
    if math.isclose(pe, 1.0):
        if not math.isclose(pa, 1.0):
            raise ValueError("pe == 1 but pa != 1: invalid weights")
        return 1.0
    return (pa - pe) / (1 - pe)


def krippendorff_alpha(units: list[list[int | None]], metric: str) -> float | None:
    """Krippendorff's alpha from the coincidence matrix; any number of raters, ``None`` = missing.

    Only units with at least two values are pairable. ``metric`` is ``"nominal"`` or ``"ordinal"``
    (``delta^2(c, k) = (sum_{g=c..k} n_g - (n_c + n_k) / 2)^2`` over the sorted category values).
    Returns ``None`` when the expected disagreement is 0 (alpha undefined).
    """
    if metric not in ("nominal", "ordinal"):
        raise ValueError(f"unknown metric: {metric}")
    coincidence: dict[tuple[int, int], float] = {}
    for unit in units:
        values = [v for v in unit if v is not None]
        m = len(values)
        if m < 2:
            continue
        for i, c in enumerate(values):
            for j, k in enumerate(values):
                if i != j:
                    coincidence[(c, k)] = coincidence.get((c, k), 0.0) + 1.0 / (m - 1)
    marginal: dict[int, float] = {}
    for (c, _k), o in coincidence.items():
        marginal[c] = marginal.get(c, 0.0) + o
    n = sum(marginal.values())
    cats = sorted(marginal)

    def delta2(c: int, k: int) -> float:
        if c == k:
            return 0.0
        if metric == "nominal":
            return 1.0
        within = sum(marginal[g] for g in cats if c <= g <= k or k <= g <= c)
        return (within - (marginal[c] + marginal[k]) / 2) ** 2

    if n <= 1:
        return None
    expected = sum(marginal[c] * marginal[k] * delta2(c, k) for c in cats for k in cats)
    if expected == 0:
        return None
    observed = sum(o * delta2(c, k) for (c, k), o in coincidence.items())
    return 1.0 - (n - 1) * observed / expected


def cluster_bootstrap_ci(
    clusters: list[list],
    statistic: Callable[[list], float | None],
    reps: int,
    level: float,
    seed: int,
) -> dict:
    """Percentile bootstrap CI resampling whole clusters (questions) with replacement.

    ``statistic`` receives the resampled list of clusters. Resamples where it returns ``None`` are
    dropped and counted; with none left, ``low`` and ``high`` are ``None``.
    """
    rng = np.random.default_rng(seed)
    n = len(clusters)
    values: list[float] = []
    dropped = 0
    for _ in range(reps):
        idx = rng.integers(0, n, size=n) if n else []
        value = statistic([clusters[i] for i in idx])
        if value is None:
            dropped += 1
        else:
            values.append(value)
    if not values:
        return {"low": None, "high": None, "dropped": dropped}
    tail = (1 - level) / 2 * 100
    low, high = np.percentile(values, [tail, 100 - tail])
    return {"low": float(low), "high": float(high), "dropped": dropped}
