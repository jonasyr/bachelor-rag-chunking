"""Difficulty probe (pilot, not part of the ground truth).

Runs retrieval for a pilot question set and prints Hit@5, MRR, Precision@5 and Recall@5 per
strategy, overall and per question kind, plus the rank of the first relevant chunk per question.
It checks whether retrieval on the corpus is hard enough to separate the chunking strategies (no
ceiling effect). Recall@5 = share of a question's relevant sections that any top-5 chunk overlaps.
The kind of a question is its `notes` field without the leading "pilot".

Usage: uv run python scripts/difficulty_probe.py [SET_DIR]
(SET_DIR defaults to data/pilot; the hard set is data/pilot/hard)
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from config import (  # noqa: E402
    CHUNK_FILES,
    RELEVANCE_MIN_OVERLAP,
    SECTIONS_FILE,
    STRATEGY_IDS,
    TOP_K,
)
from embed import load_jsonl  # noqa: E402
from relevance import overlap_tokens  # noqa: E402
from retrieve import retrieve, split_ids  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def scores(flags: list[bool], wanted: list[str], covered: set[str]) -> tuple[float, ...]:
    """Hit@k, reciprocal rank, Precision@k and Recall@k of one ranked list."""
    return (
        float(any(flags)),
        next((1 / (i + 1) for i, f in enumerate(flags) if f), 0.0),
        sum(flags) / TOP_K,
        len(covered) / len(wanted),
    )


def main(pilot: Path) -> None:
    out = pilot / "retrieved_results.csv"
    retrieve(
        questions_file=pilot / "questions.csv",
        ground_truth_file=pilot / "ground_truth.csv",
        query_file=pilot / "query_embeddings.npz",
        out_file=out,
        runs_file=pilot / "runs.jsonl",
    )
    sections = {s["section_id"]: s for s in load_jsonl(SECTIONS_FILE, "")}
    gold = {
        r["question_id"]: split_ids(r["relevant_section_ids"])
        for r in read_csv(pilot / "ground_truth.csv")
    }
    kind = {
        r["question_id"]: r["notes"].removeprefix("pilot").strip() or "all"
        for r in read_csv(pilot / "questions.csv")
    }
    chunks = {c["chunk_id"]: c for k in STRATEGY_IDS for c in load_jsonl(CHUNK_FILES[k], "")}
    rows = read_csv(out)

    per_q: dict[tuple[str, str], tuple[float, ...]] = {}
    first: dict[tuple[str, str], str] = {}
    for key in STRATEGY_IDS:
        for qid, wanted in gold.items():
            ranked = sorted(
                (r for r in rows if r["question_id"] == qid and r["strategy"] == key),
                key=lambda r: int(r["rank"]),
            )
            flags = [r["is_relevant"] == "1" for r in ranked]
            covered = {
                sid
                for sid in wanted
                for r in ranked
                if overlap_tokens(chunks[r["chunk_id"]], sections[sid]) >= RELEVANCE_MIN_OVERLAP
            }
            per_q[key, qid] = scores(flags, wanted, covered)
            first[key, qid] = str(flags.index(True) + 1) if any(flags) else "-"

    groups = {"all": list(gold)} | {
        k: [q for q in gold if kind[q] == k] for k in dict.fromkeys(kind.values()) if k != "all"
    }
    for name, qids in groups.items():
        print(f"\n{name} (n={len(qids)})")
        print(f"{'strategy':8} {'Hit@5':>6} {'MRR':>6} {'P@5':>6} {'R@5':>6}")
        for key in STRATEGY_IDS:
            means = [sum(per_q[key, q][i] for q in qids) / len(qids) for i in range(4)]
            print(f"{key:8} " + " ".join(f"{m:6.2f}" for m in means))

    print("\nrank of the first relevant chunk (- = none in top 5), R@5 if below 1")
    print(f"{'question':8} {'kind':14} " + " ".join(f"{k:>9}" for k in STRATEGY_IDS))
    for qid in gold:
        cells = [
            first[key, qid] + (f" R{per_q[key, qid][3]:.2f}" if per_q[key, qid][3] < 1 else "")
            for key in STRATEGY_IDS
        ]
        print(f"{qid:8} {kind[qid]:14} " + " ".join(f"{c:>9}" for c in cells))

    last = [json.loads(line) for line in (pilot / "runs.jsonl").read_text().splitlines()][-1]
    print(
        f"\ncost: {last['input_tokens']} question tokens USD {last['cost_usd']:.6f}, "
        f"vintage check {last['canary_input_tokens']} tokens USD {last['canary_cost_usd']:.6f}, "
        f"canary cosine {last['canary_min_cosine']}"
    )


if __name__ == "__main__":
    main(ROOT / (sys.argv[1] if len(sys.argv) > 1 else "data/pilot"))
