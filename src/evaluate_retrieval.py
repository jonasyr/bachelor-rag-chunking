"""Retrieval evaluation (ADR 0012, 0026).

Computes Hit@k, reciprocal rank, Precision@k, Recall@k and the context tokens of the top-k
chunks per question, strategy and relevance rule (main rule and sensitivity rule,
docs/reference/evaluation.md), writes them to retrieval_scores.csv and prints the means per
strategy, overall and per question type and construction class. k is always TOP_K (ADR 0014).
Reads retrieved_results.csv (or retrieved_results_control.csv for K1), questions.csv,
ground_truth.csv, sections.jsonl and the chunk files. The main catalogue is evaluated only
while it matches its freeze record (ADR 0030), and the results must carry the relevance flags
that the ground truth yields, so a stale retrieval run cannot slip into the evaluation.

Output schema: question_id, strategy, rule, hit, reciprocal_rank, precision, recall,
context_tokens
"""

import csv
import statistics
from pathlib import Path

from config import (
    CATALOGUE_FREEZE_FILE,
    CHUNK_FILES,
    CONTROL_CHUNK_FILES,
    CONTROL_RETRIEVAL_SCORES_FILE,
    CONTROL_RETRIEVED_FILE,
    CONTROL_STRATEGIES,
    DOCUMENTS_FILE,
    EMBEDDING_RUNS_FILE,
    GROUND_TRUTH_FILE,
    PILOT_RUNS_FILE_NAME,
    QUESTIONS_FILE,
    RELEVANCE_MIN_OVERLAP,
    RETRIEVAL_SCORES_FILE,
    RETRIEVED_RESULTS_FILE,
    SECTIONS_FILE,
    SENSITIVITY_MIN_OVERLAP,
    STRATEGY_IDS,
    TOP_K,
)
from embed import load_jsonl
from freeze import require_frozen
from relevance import is_relevant
from retrieve import (
    GROUND_TRUTH_HEADER,
    HEADER,
    QUESTIONS_HEADER,
    QUESTIONS_REQUIRED,
    read_rows,
    relevant_sections,
)
from run_log import append_step_run

SCORES_HEADER = [
    "question_id",
    "strategy",
    "rule",
    "hit",
    "reciprocal_rank",
    "precision",
    "recall",
    "context_tokens",
]
RULES = {"main": RELEVANCE_MIN_OVERLAP, "sensitivity": SENSITIVITY_MIN_OVERLAP}
METRICS = ["hit", "reciprocal_rank", "precision", "recall", "context_tokens"]
GROUPS = ["type", "difficulty"]  # questions.csv columns the summary is broken down by
ALL_STRATEGIES = {**STRATEGY_IDS, **CONTROL_STRATEGIES}  # key -> strategy field of its chunks


def question_scores(ranked: list[dict], wanted: list[dict], k: int, min_overlap: int) -> dict:
    """Metrics of one ranked chunk list against the annotated sections of its question."""
    top = ranked[:k]
    flags = [is_relevant(c, wanted, min_overlap) for c in top]
    covered = [s for s in wanted if any(is_relevant(c, [s], min_overlap) for c in top)]
    return {
        "hit": int(any(flags)),
        "reciprocal_rank": next((1 / rank for rank, f in enumerate(flags, start=1) if f), 0.0),
        "precision": sum(flags) / k,
        "recall": len(covered) / len(wanted),
        "context_tokens": sum(c["end_token"] - c["start_token"] for c in top),
    }


def ranked_results(
    path: Path, qids: list[str], strategies: list[str], chunks: dict[str, dict]
) -> dict[tuple[str, str], list[dict]]:
    """Result rows per (question, strategy) in rank order; raise unless complete and known."""
    rows = read_rows(path, "retrieval results", HEADER, HEADER, unique_ids=False)
    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        if row["question_id"] not in qids:
            raise ValueError(f"{path}: unknown question {row['question_id']}")
        if row["strategy"] not in strategies:
            raise ValueError(f"{path}: unknown strategy {row['strategy']}")
        chunk = chunks.get(row["chunk_id"])
        if chunk is None or chunk.get("strategy") != ALL_STRATEGIES[row["strategy"]]:
            raise ValueError(f"{path}: unknown chunk {row['chunk_id']} of {row['strategy']}")
        grouped.setdefault((row["question_id"], row["strategy"]), []).append(row)
    missing = [f"{q}/{s}" for q in qids for s in strategies if (q, s) not in grouped]
    if missing:
        raise ValueError(f"{path}: results missing for {missing}; run src/retrieve.py")
    for (qid, key), group in grouped.items():
        group.sort(key=lambda r: int(r["rank"]))
        if [int(r["rank"]) for r in group] != list(range(1, TOP_K + 1)):
            raise ValueError(f"{path}: {qid}/{key} must have ranks 1-{TOP_K}")
    return grouped


def evaluate(
    results_file: Path = RETRIEVED_RESULTS_FILE,
    questions_file: Path = QUESTIONS_FILE,
    ground_truth_file: Path = GROUND_TRUTH_FILE,
    sections_file: Path = SECTIONS_FILE,
    documents_file: Path = DOCUMENTS_FILE,
    chunk_files: dict[str, Path] = CHUNK_FILES,
    strategies: dict[str, str] = STRATEGY_IDS,
    out_file: Path = RETRIEVAL_SCORES_FILE,
    freeze_file: Path = CATALOGUE_FREEZE_FILE,
    runs_file: Path = EMBEDDING_RUNS_FILE,
) -> list[dict]:
    """Write one score row per question, strategy and rule; return the rows."""
    require_frozen(questions_file, ground_truth_file, sections_file, documents_file, freeze_file)
    if strategies not in (STRATEGY_IDS, CONTROL_STRATEGIES):
        raise ValueError("strategies must be the experiment set or the control set (D26)")
    if sorted(chunk_files) != sorted(strategies):
        raise ValueError(f"chunk_files must cover exactly the strategies {sorted(strategies)}")
    questions = read_rows(
        questions_file, "question catalogue", QUESTIONS_HEADER, QUESTIONS_REQUIRED
    )
    ground_truth = read_rows(
        ground_truth_file, "ground truth", GROUND_TRUTH_HEADER, GROUND_TRUTH_HEADER
    )
    relevant = relevant_sections(
        questions, ground_truth, load_jsonl(sections_file, "run src/preprocess.py first")
    )
    chunks = {
        c["chunk_id"]: c
        for key in strategies
        for c in load_jsonl(chunk_files[key], "run src/chunking.py first")
    }
    qids = sorted(q["question_id"] for q in questions)
    keys = list(strategies)
    grouped = ranked_results(results_file, qids, keys, chunks)

    rows: list[dict] = []
    for qid in qids:
        for key in keys:
            ranked = [chunks[r["chunk_id"]] for r in grouped[qid, key]]
            for result, c in zip(grouped[qid, key], ranked, strict=True):
                if result["is_relevant"] != str(int(is_relevant(c, relevant[qid], RULES["main"]))):
                    raise ValueError(
                        f"{results_file}: is_relevant of {qid}/{key} rank {result['rank']} "
                        "disagrees with the ground truth; run src/retrieve.py again"
                    )
            for rule, min_overlap in RULES.items():
                scores = question_scores(ranked, relevant[qid], TOP_K, min_overlap)
                rows.append({"question_id": qid, "strategy": key, "rule": rule, **scores})

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(SCORES_HEADER)
        for row in rows:
            writer.writerow(
                [row["question_id"], row["strategy"], row["rule"], row["hit"]]
                + [f"{row[m]:.6f}" for m in ("reciprocal_rank", "precision", "recall")]
                + [row["context_tokens"]]
            )
    inputs = [results_file, questions_file, ground_truth_file, sections_file, *chunk_files.values()]
    append_step_run("evaluate_retrieval", ",".join(keys), inputs, [out_file], runs_file)
    with out_file.open(encoding="utf-8", newline="") as f:  # the rows as written
        return list(csv.DictReader(f))


def set_paths(set_dir: Path, control: bool = False) -> dict[str, Path]:
    """The files of a pilot set (data/pilot/...): results, catalogue, scores and run log in the set;
    sections, documents and chunks are the shared processed corpus."""
    return {
        "results_file": set_dir
        / (CONTROL_RETRIEVED_FILE if control else RETRIEVED_RESULTS_FILE).name,
        "questions_file": set_dir / QUESTIONS_FILE.name,
        "ground_truth_file": set_dir / GROUND_TRUTH_FILE.name,
        "out_file": set_dir
        / (CONTROL_RETRIEVAL_SCORES_FILE if control else RETRIEVAL_SCORES_FILE).name,
        "runs_file": set_dir / PILOT_RUNS_FILE_NAME,
    }


def summarise(rows: list[dict], questions_file: Path = QUESTIONS_FILE) -> dict[tuple, dict]:
    """Mean of every metric per (group, value, strategy, rule); group "all" spans all questions,
    the other groups are the question type and construction class."""
    with questions_file.open(encoding="utf-8", newline="") as f:
        questions = {q["question_id"]: q for q in csv.DictReader(f)}
    buckets: dict[tuple, list[dict]] = {}
    for row in rows:
        labels = [("all", "all")] + [(g, questions[row["question_id"]][g]) for g in GROUPS]
        for group, value in labels:
            buckets.setdefault((group, value, row["strategy"], row["rule"]), []).append(row)
    return {
        key: {"n": len(group)} | {m: statistics.mean(float(r[m]) for r in group) for m in METRICS}
        for key, group in buckets.items()
    }


def print_summary(summary: dict[tuple, dict], k: int = TOP_K) -> None:
    for rule in RULES:
        print(f"\nrule: {rule}")
        print(
            f"{'group':28} {'strategy':8} {'n':>3} {f'Hit@{k}':>6} {'MRR':>6} "
            f"{f'P@{k}':>6} {f'R@{k}':>6} {f'ctx@{k}':>7}"
        )
        for (group, value, strategy, r), means in summary.items():
            if r != rule:
                continue
            label = "all" if group == "all" else f"{group}={value}"
            print(
                f"{label:28} {strategy:8} {means['n']:3} "
                + " ".join(
                    f"{means[m]:6.3f}" for m in ("hit", "reciprocal_rank", "precision", "recall")
                )
                + f" {means['context_tokens']:7.0f}"
            )


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Retrieval metrics per strategy (ADR 0012).")
    p.add_argument("--control", action="store_true", help="the size-matched control K1")
    p.add_argument(
        "--set", type=Path, metavar="DIR", help="a pilot set (e.g. data/pilot/e2e) instead"
    )
    args = p.parse_args()
    paths = set_paths(args.set, args.control) if args.set else {}
    if args.control:
        rows = evaluate(
            **{
                "results_file": CONTROL_RETRIEVED_FILE,
                "out_file": CONTROL_RETRIEVAL_SCORES_FILE,
                **paths,
                "chunk_files": CONTROL_CHUNK_FILES,
                "strategies": CONTROL_STRATEGIES,
            }
        )
    else:
        rows = evaluate(**paths)
    print_summary(summarise(rows, paths.get("questions_file", QUESTIONS_FILE)))
