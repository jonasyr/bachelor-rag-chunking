"""Difficulty probe (pilot, not part of the ground truth).

Runs retrieval for the pilot questions in data/pilot/ and prints Hit@5, MRR, Precision@5 and
Recall@5 per strategy, to check whether retrieval on the corpus is hard enough to separate the
chunking strategies (no ceiling effect). Recall@5 = share of a question's relevant sections that
any top-5 chunk overlaps.
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

PILOT = ROOT / "data" / "pilot"


def main() -> None:
    out = PILOT / "retrieved_results.csv"
    retrieve(
        questions_file=PILOT / "questions.csv",
        ground_truth_file=PILOT / "ground_truth.csv",
        query_file=PILOT / "query_embeddings.npz",
        out_file=out,
        runs_file=PILOT / "runs.jsonl",
    )
    sections = {s["section_id"]: s for s in load_jsonl(SECTIONS_FILE, "")}
    with (PILOT / "ground_truth.csv").open(encoding="utf-8", newline="") as f:
        gold = {r["question_id"]: split_ids(r["relevant_section_ids"]) for r in csv.DictReader(f)}
    chunks = {c["chunk_id"]: c for k in STRATEGY_IDS for c in load_jsonl(CHUNK_FILES[k], "")}
    with out.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    print(
        f"{'strategy':8} {'Hit@5':>6} {'MRR':>6} {'P@5':>6} {'R@5':>6}"
        f"   (n={len(gold)} pilot questions)"
    )
    for key in STRATEGY_IDS:
        hit = mrr = prec = rec = 0.0
        for qid, wanted in gold.items():
            ranked = sorted(
                (r for r in rows if r["question_id"] == qid and r["strategy"] == key),
                key=lambda r: int(r["rank"]),
            )
            flags = [r["is_relevant"] == "1" for r in ranked]
            hit += any(flags)
            mrr += next((1 / (i + 1) for i, f in enumerate(flags) if f), 0.0)
            prec += sum(flags) / TOP_K
            covered = {
                sid
                for sid in wanted
                for r in ranked
                if overlap_tokens(chunks[r["chunk_id"]], sections[sid]) >= RELEVANCE_MIN_OVERLAP
            }
            rec += len(covered) / len(wanted)
        n = len(gold)
        print(f"{key:8} {hit / n:6.2f} {mrr / n:6.2f} {prec / n:6.2f} {rec / n:6.2f}")
    runs = [json.loads(line) for line in (PILOT / "runs.jsonl").read_text().splitlines()]
    last = runs[-1]
    print(
        f"cost: {last['input_tokens']} question tokens USD {last['cost_usd']:.6f}, "
        f"vintage check {last['canary_input_tokens']} tokens USD {last['canary_cost_usd']:.6f}, "
        f"canary cosine {last['canary_min_cosine']}"
    )


if __name__ == "__main__":
    main()
