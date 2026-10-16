"""Answer quality evaluation: manual rubric 0-2 on five criteria (ADR 0013).

--mode scaffold  Write scores.csv with one unscored row per generated answer; an existing
                 scores.csv is never overwritten, so manual scores cannot be lost.
--mode summarise Check the filled scores.csv (every criterion an integer 0-2), fill in
                 total_score = mean of the criteria, print mean, median and standard deviation
                 per strategy, overall and per question type and construction class.

Answers exist only for the experiment C1-C3, never for the control K1 (ADR 0026), and every
question needs an answer of every strategy, so the strategies are compared on the same questions.

Output schema (docs/reference/data-formats.md): question_id, strategy, correctness, completeness,
groundedness, no_hallucination, clarity, total_score
"""

import statistics
from pathlib import Path

from atomic_csv import read_csv, write_csv
from config import (
    GENERATED_ANSWERS_FILE,
    QUESTIONS_FILE,
    RUBRIC_CRITERIA,
    RUBRIC_MAX_SCORE,
    SCORES_FILE,
    STRATEGY_IDS,
)
from retrieve import QUESTIONS_HEADER

ANSWERS_HEADER = [
    "question_id",
    "strategy",
    "answer",
    "sources",
    "prompt_tokens",
    "completion_tokens",
]
SCORES_HEADER = ["question_id", "strategy", *RUBRIC_CRITERIA, "total_score"]
GROUPS = ["type", "difficulty"]  # questions.csv columns the summary is broken down by


def check_grid(path: Path, rows: list[dict]) -> None:
    """Every question has exactly one row per experiment strategy, nothing else."""
    pairs = [(r["question_id"], r["strategy"]) for r in rows]
    foreign = sorted({s for _, s in pairs} - set(STRATEGY_IDS))
    if foreign:
        raise ValueError(f"{path}: strategy {foreign} is not in the experiment C1-C3 (no K1)")
    duplicates = sorted({p for p in pairs if pairs.count(p) > 1})
    if duplicates:
        raise ValueError(f"{path}: duplicate rows {duplicates}")
    qids = sorted({q for q, _ in pairs})
    missing = [f"{q}/{s}" for q in qids for s in STRATEGY_IDS if (q, s) not in pairs]
    if missing:
        raise ValueError(f"{path}: rows missing for {missing}")


def scaffold(answers_file: Path = GENERATED_ANSWERS_FILE, scores_file: Path = SCORES_FILE) -> int:
    """Write the unscored rows in (question_id, strategy) order; return their number."""
    if scores_file.exists():
        raise FileExistsError(
            f"{scores_file} exists and may hold manual scores; move it away to start afresh"
        )
    answers = read_csv(answers_file, ANSWERS_HEADER)
    if not answers:
        raise ValueError(f"{answers_file} has no answers; run src/generate.py first")
    check_grid(answers_file, answers)
    order = list(STRATEGY_IDS)
    rows = [
        {"question_id": a["question_id"], "strategy": a["strategy"]}
        | dict.fromkeys([*RUBRIC_CRITERIA, "total_score"], "")
        for a in sorted(answers, key=lambda a: (a["question_id"], order.index(a["strategy"])))
    ]
    write_csv(scores_file, SCORES_HEADER, rows)
    return len(rows)


def criterion_value(row: dict, criterion: str, path: Path) -> int:
    where = f"{path}: {row['question_id']}/{row['strategy']} {criterion}"
    text = row[criterion].strip()
    if not text:
        raise ValueError(f"{where} is unscored")
    if not text.isdigit() or int(text) > RUBRIC_MAX_SCORE:
        raise ValueError(f"{where} = {text!r}, must be an integer 0-{RUBRIC_MAX_SCORE}")
    return int(text)


def summarise(
    scores_file: Path = SCORES_FILE, questions_file: Path = QUESTIONS_FILE
) -> dict[tuple, dict]:
    """Fill total_score and return the statistics per (group, value, strategy); group "all"
    spans all questions, the other groups are the question type and construction class."""
    rows = read_csv(scores_file, SCORES_HEADER)
    if not rows:
        raise ValueError(f"{scores_file} has no rows; run --mode scaffold first")
    check_grid(scores_file, rows)
    questions = {q["question_id"]: q for q in read_csv(questions_file, QUESTIONS_HEADER)}
    unknown = sorted({r["question_id"] for r in rows} - set(questions))
    if unknown:
        raise ValueError(f"{scores_file}: questions {unknown} are not in {questions_file}")
    totals = []
    for row in rows:
        values = [criterion_value(row, c, scores_file) for c in RUBRIC_CRITERIA]
        total = f"{sum(values) / len(values):.1f}"  # steps of 1/5: one decimal is exact
        if row["total_score"].strip() and float(row["total_score"]) != float(total):
            raise ValueError(
                f"{scores_file}: {row['question_id']}/{row['strategy']} total_score "
                f"{row['total_score']} is not the mean of the criteria ({total})"
            )
        totals.append(total)
    for row, total in zip(rows, totals, strict=True):
        row["total_score"] = total
    write_csv(scores_file, SCORES_HEADER, rows)

    buckets: dict[tuple, list[dict]] = {}
    for row in rows:
        labels = [("all", "all")] + [(g, questions[row["question_id"]][g]) for g in GROUPS]
        for group, value in labels:
            buckets.setdefault((group, value, row["strategy"]), []).append(row)
    summary = {}
    for key, group in buckets.items():
        total = [float(r["total_score"]) for r in group]
        summary[key] = {
            "n": len(group),
            "total_score": statistics.mean(total),
            "median": statistics.median(total),
            "sd": statistics.stdev(total) if len(total) > 1 else 0.0,
        } | {c: statistics.mean(int(r[c]) for r in group) for c in RUBRIC_CRITERIA}
    return summary


def print_summary(summary: dict[tuple, dict]) -> None:
    short = "".join(f" {c[:6]:>6}" for c in RUBRIC_CRITERIA)
    print(f"{'group':28} {'strategy':8} {'n':>3} {'mean':>5} {'median':>6} {'sd':>5}{short}")
    for (group, value, strategy), s in summary.items():
        label = "all" if group == "all" else f"{group}={value}"
        print(
            f"{label:28} {strategy:8} {s['n']:3} {s['total_score']:5.2f} {s['median']:6.2f} "
            f"{s['sd']:5.2f}" + "".join(f" {s[c]:6.2f}" for c in RUBRIC_CRITERIA)
        )


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Manual rubric scores (ADR 0013).")
    p.add_argument("--mode", choices=["scaffold", "summarise"], required=True)
    args = p.parse_args()
    if args.mode == "scaffold":
        print(f"{scaffold()} unscored rows -> {SCORES_FILE}")
    else:
        print_summary(summarise())
