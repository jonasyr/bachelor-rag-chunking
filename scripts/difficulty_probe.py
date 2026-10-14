"""Difficulty probe (pilot, not part of the ground truth).

Runs retrieval for a pilot question set and prints Hit@5, MRR, Precision@5 and Recall@5 per
strategy, overall and per question kind, plus the rank of the first relevant chunk per question.
It checks whether retrieval on the corpus is hard enough to separate the chunking strategies (no
ceiling effect). Recall@5 = share of a question's relevant sections that any top-5 chunk overlaps.
The kind of a question is its `notes` field without the leading "pilot". Also runs the
size-matched control K1 (ADR 0026) and prints chunk size and context tokens per strategy.

Usage: uv run python scripts/difficulty_probe.py [SET_DIR]
(SET_DIR defaults to config.PILOT_DIR = data/pilot; the hard set is data/pilot/hard)
"""

import csv
import json
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from config import (  # noqa: E402
    CHUNK_FILES,
    CONTROL_CHUNK_FILES,
    CONTROL_RETRIEVED_FILE,
    CONTROL_STRATEGIES,
    GROUND_TRUTH_FILE,
    PILOT_DIR,
    PILOT_RUNS_FILE_NAME,
    QUERY_EMBEDDINGS_FILE,
    QUESTIONS_FILE,
    RELEVANCE_MIN_OVERLAP,
    RETRIEVED_RESULTS_FILE,
    SECTIONS_FILE,
    STRATEGY_IDS,
    TOP_K,
)
from embed import load_jsonl  # noqa: E402
from relevance import overlap_tokens  # noqa: E402
from retrieve import retrieve, retrieve_control, split_ids  # noqa: E402


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


def length(chunk: dict) -> int:
    return chunk["end_token"] - chunk["start_token"]


def pilot_dir(argv: list[str]) -> Path:
    """The pilot set to probe: SET_DIR relative to the repo root, default config.PILOT_DIR."""
    return ROOT / argv[1] if len(argv) > 1 else PILOT_DIR


def set_files(pilot: Path) -> dict[str, Path]:
    """Input and output files of a pilot set, named like the evaluation artefacts in config."""
    return {
        "questions_file": pilot / QUESTIONS_FILE.name,
        "ground_truth_file": pilot / GROUND_TRUTH_FILE.name,
        "query_file": pilot / QUERY_EMBEDDINGS_FILE.name,
        "runs_file": pilot / PILOT_RUNS_FILE_NAME,
        "out_file": pilot / RETRIEVED_RESULTS_FILE.name,
        "control_out_file": pilot / CONTROL_RETRIEVED_FILE.name,
    }


def main(pilot: Path) -> None:
    files = set_files(pilot)
    out, control_out = files.pop("out_file"), files.pop("control_out_file")
    common: dict[str, Any] = dict(files)  # Any: the keys are path parameters of retrieve()
    retrieve(out_file=out, **common)
    retrieve_control(out_file=control_out, **common)
    keys = [*STRATEGY_IDS, *CONTROL_STRATEGIES]
    chunk_files = {**CHUNK_FILES, **CONTROL_CHUNK_FILES}
    sections = {s["section_id"]: s for s in load_jsonl(SECTIONS_FILE, "")}
    gold = {
        r["question_id"]: split_ids(r["relevant_section_ids"])
        for r in read_csv(common["ground_truth_file"])
    }
    kind = {
        r["question_id"]: r["notes"].removeprefix("pilot").strip() or "all"
        for r in read_csv(common["questions_file"])
    }
    chunks = {c["chunk_id"]: c for k in keys for c in load_jsonl(chunk_files[k], "")}
    rows = read_csv(out) + read_csv(control_out)

    per_q: dict[tuple[str, str], tuple[float, ...]] = {}
    first: dict[tuple[str, str], str] = {}
    context: dict[str, list[int]] = {k: [] for k in keys}
    for key in keys:
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
            context[key].append(sum(length(chunks[r["chunk_id"]]) for r in ranked))

    print(
        f"{'strategy':8} {'chunks':>6} {'median':>6} {'mean':>6} {'context@5':>9}   (K1 = control)"
    )
    for key in keys:
        lengths = [length(c) for c in chunks.values() if c["chunk_id"].startswith(f"{key}_")]
        print(
            f"{key:8} {len(lengths):6} {statistics.median(lengths):6.0f} "
            f"{statistics.mean(lengths):6.0f} {statistics.mean(context[key]):9.0f}"
        )

    groups = {"all": list(gold)} | {
        k: [q for q in gold if kind[q] == k] for k in dict.fromkeys(kind.values()) if k != "all"
    }
    for name, qids in groups.items():
        print(f"\n{name} (n={len(qids)})")
        print(f"{'strategy':8} {'Hit@5':>6} {'MRR':>6} {'P@5':>6} {'R@5':>6}")
        for key in keys:
            means = [sum(per_q[key, q][i] for q in qids) / len(qids) for i in range(4)]
            print(f"{key:8} " + " ".join(f"{m:6.2f}" for m in means))

    print("\nrank of the first relevant chunk (- = none in top 5), R@5 if below 1")
    print(f"{'question':8} {'kind':14} " + " ".join(f"{k:>9}" for k in keys))
    for qid in gold:
        cells = [
            first[key, qid] + (f" R{per_q[key, qid][3]:.2f}" if per_q[key, qid][3] < 1 else "")
            for key in keys
        ]
        print(f"{qid:8} {kind[qid]:14} " + " ".join(f"{c:>9}" for c in cells))

    for run in [json.loads(line) for line in common["runs_file"].read_text().splitlines()][-2:]:
        print(
            f"\n{run['strategy']}: {run['input_tokens']} question tokens "
            f"USD {run['cost_usd']:.6f}, vintage check {run['canary_input_tokens']} tokens "
            f"USD {run['canary_cost_usd']:.6f}, canary cosine {run['canary_min_cosine']}"
        )


if __name__ == "__main__":
    main(pilot_dir(sys.argv))
