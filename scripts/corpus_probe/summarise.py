"""Gap rates, preregistered scores and the weighting sensitivity (ADR 0038).

Reads candidates.csv, stats.json, results/ and the classified misses/ and writes summary.json.
Gap rate = fact misses / well-posed probes (open-book correct), with a normal-approximation 95 %
interval. The criteria, weights and rating bands follow data/corpus_probe/preregistration.md;
the bands were fixed before the score table was computed.

Usage: uv run python scripts/corpus_probe/summarise.py
"""

import collections
import math
import statistics

from common import (
    CATEGORIES,
    MISSES_DIR,
    RESULTS_DIR,
    STATS_FILE,
    SUMMARY_FILE,
    candidates,
    read_json,
    read_jsonl,
    write_json,
)

WEIGHTS = {"unknown": 35, "clean": 15, "struct": 15, "quality": 15, "stable": 10, "fit": 10}
SENSITIVITY = {  # alternative weightings; the ranking is reported for each
    "preregistered": WEIGHTS,
    "equal": dict.fromkeys(WEIGHTS, 1),
    "unknown50": {"unknown": 50, "clean": 10, "struct": 10, "quality": 10, "stable": 10, "fit": 10},
    "no_stability_fit": {
        "unknown": 35,
        "clean": 20,
        "struct": 20,
        "quality": 25,
        "stable": 0,
        "fit": 0,
    },
    "quality_heavy": {
        "unknown": 25,
        "clean": 15,
        "struct": 20,
        "quality": 25,
        "stable": 5,
        "fit": 10,
    },
}
SENSITIVITY_MIN_TOKENS = 80_000  # exclusion criterion 5, lower bound
SENSITIVITY_TOP = 5
AI_RATING = {"low": 4, "medium": 3, "medium-high": 2, "high": 1}
FEW_STARS = 100  # fewer GitHub stars lower the fit rating by one


def band(x: float, cuts: list[float]) -> int:
    """Rating 0-4 = number of ascending cuts reached."""
    return sum(x >= c for c in cuts)


def measure(name: str, s: dict) -> dict:
    results = read_jsonl(RESULTS_DIR / f"{name}.jsonl")
    misses = read_json(MISSES_DIR / f"{name}.json")
    counts = collections.Counter(m["category"] for m in misses)
    if set(counts) - set(CATEGORIES):
        raise ValueError(f"misses/{name}.json: unclassified or unknown categories {set(counts)}")
    well_posed = sum(r["open_ok"] for r in results)
    gap = counts["fact"] / well_posed
    se = math.sqrt(gap * (1 - gap) / well_posed)
    total = s["tokens"] or 1
    q = statistics.quantiles(s["page_tokens"], n=4)
    return {
        "docs": s["docs"],
        "tokens": s["tokens"],
        "probes": len(results),
        "well_posed": well_posed,
        "wp_share": well_posed / len(results),
        "misses": len(misses),
        "categories": {c: counts[c] for c in CATEGORIES},
        "gap": gap,
        "ci": [gap - 1.96 * se, gap + 1.96 * se],
        "jsx_per_10k": s["jsx_lines"] / total * 1e4,
        "head_median": statistics.median(s["headings_h2_h4"]),
        "page_iqr": [q[0], q[2]],
        "code_blocks_per_10k": round(s["code_blocks"] / total * 1e4, 1),
        "frontmatter_titles": round(s["frontmatter_titles"], 2),
        "heading_jumps_per_page": round(s["heading_jumps"] / s["docs"], 2),
        "reference_share": round(s["reference_share"], 2),
    }


def ratings(m: dict, c: dict) -> dict:
    clean = (
        band(m["wp_share"], [0.25, 0.35, 0.45, 0.60]) + 4 - band(m["jsx_per_10k"], [5, 10, 15, 20])
    ) / 2
    struct = band(m["head_median"], [3, 5, 6, 8]) - (1 if m["heading_jumps_per_page"] > 0.1 else 0)
    share = m["reference_share"]
    split = 4 if 0.15 <= share <= 0.6 else 2 if 0.05 <= share <= 0.8 else 0
    quality = (
        band(m["code_blocks_per_10k"], [5, 10, 20, 30])
        + (4 if m["frontmatter_titles"] >= 0.9 else 0)
        + split
    ) / 3
    stars = int(c["stars"]) if c["stars"] else 1000
    return {
        "unknown": band(m["gap"], [0.10, 0.20, 0.30, 0.40]),
        "clean": round(clean),
        "struct": max(0, struct),
        "quality": round(quality),
        "stable": 4 - band(int(c["commits30"]), [11, 31, 61, 151]),
        "fit": max(0, AI_RATING[c["ai"]] - (1 if stars < FEW_STARS else 0)),
    }


def main() -> None:
    cands, stats = candidates(), read_json(STATS_FILE)
    rows = []
    for name, c in cands.items():
        m = measure(name, stats[name])
        r = ratings(m, c)
        total = sum(WEIGHTS[k] * r[k] / 4 for k in WEIGHTS)
        rows.append(
            {"name": name, "eligible": c["new"] == "yes", **m, **r, "total": round(total, 1)}
        )
    rows.sort(key=lambda r: (-r["total"], -r["gap"]))
    pool = [r for r in rows if r["eligible"] and r["tokens"] >= SENSITIVITY_MIN_TOKENS]
    sensitivity = {
        k: [r["name"] for r in sorted(pool, key=lambda r: -sum(w[c] * r[c] for c in w))][
            :SENSITIVITY_TOP
        ]
        for k, w in SENSITIVITY.items()
    }
    write_json(SUMMARY_FILE, {"corpora": rows, "sensitivity": sensitivity})
    for r in rows:
        mark = "  " if r["eligible"] else "x "
        print(
            f"{r['name']:13} {mark}total={r['total']:5} gap={r['gap']:.1%} "
            f"[{r['ci'][0]:.1%},{r['ci'][1]:.1%}] wp={r['well_posed']}/{r['probes']} "
            f"tok={r['tokens']}"
        )
    for k, top in sensitivity.items():
        print(f"{k:17}", " > ".join(top))


if __name__ == "__main__":
    main()
