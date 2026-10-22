"""Second rating by a second rater, pseudonym R2 (ADR 0046).

--mode draw    Draw the questions R2 scores, after the catalogue freeze and before any own scoring.
               Writes second_rater_sample.csv (question_id, type, difficulty, sorted by
               question_id) and a run record `second_rater_draw` (seed, count, checksums of
               questions.csv and the sample). The sample is stratified: the number per question type
               and per construction class is proportional to the catalogue (largest remainder, ties
               decided by the seed), and a seeded draw is repeated until both marginals hit their
               targets exactly. The draw reads questions.csv only; of the result files it merely
               checks whether the sheet or the checks already hold own values.
               The main catalogue must be frozen and free of own values, and an existing sample is
               never overwritten. With --set DIR (pilot set) the guard on own values only warns.
--mode export  Not yet implemented.
--mode close   Not yet implemented.

--questions N (pilot sets only) sets the number of questions; the main catalogue always draws
config.SECOND_RATER_QUESTIONS.
"""

import csv
import random
import sys
from collections import Counter
from pathlib import Path

from atomic_csv import write_csv
from config import (
    CATALOGUE_FREEZE_FILE,
    DOCUMENTS_FILE,
    GENERATION_RUNS_FILE,
    GROUND_TRUTH_FILE,
    KEY_POINTS_FILE,
    PILOT_RUNS_FILE_NAME,
    QUESTIONS_FILE,
    RUBRIC_CRITERIA,
    SCORES_FILE,
    SCORING_CHECKS_FILE,
    SCORING_ITEMS_FILE,
    SCORING_SHEET_FILE,
    SECOND_RATER_DIR,
    SECOND_RATER_DIR_NAME,
    SECOND_RATER_MAX_DRAWS,
    SECOND_RATER_QUESTIONS,
    SECOND_RATER_SAMPLE_FILE,
    SECOND_RATER_SEED,
    SECTIONS_FILE,
    STRATEGY_IDS,
)
from freeze import require_frozen
from retrieve import QUESTIONS_HEADER, QUESTIONS_REQUIRED, read_rows
from run_log import append_step_run

SAMPLE_HEADER = ["question_id", "type", "difficulty"]
DRAW_STEP = "second_rater_draw"


def targets(counts: dict[str, int], n: int, rng: random.Random) -> dict[str, int]:
    """Split n over the keys of `counts` proportionally (largest remainder); ties by `rng`."""
    total = sum(counts.values())
    shares = {k: n * c // total for k, c in counts.items()}
    order = list(counts)
    rng.shuffle(order)  # the tie-break; sorted() is stable
    by_remainder = sorted(order, key=lambda k: -((n * counts[k]) % total))
    for k in by_remainder[: n - sum(shares.values())]:
        shares[k] += 1
    return shares


def draw(questions: list[dict], n: int, seed: int) -> list[dict]:
    """n questions whose `type` and `difficulty` counts both equal their targets, by seeded
    rejection sampling; sorted by question_id. Raise if no draw meets both within the limit."""
    pool = sorted(questions, key=lambda q: q["question_id"])
    if n > len(pool):
        raise ValueError(f"cannot draw {n} questions from only {len(pool)}")
    rng = random.Random(seed)
    want = {
        field: targets(Counter(q[field] for q in pool), n, rng) for field in ("type", "difficulty")
    }
    for _ in range(SECOND_RATER_MAX_DRAWS):
        chosen = rng.sample(pool, n)
        if all(
            Counter(q[field] for q in chosen)
            == Counter({k: v for k, v in want[field].items() if v})
            for field in want
        ):
            return [{k: q[k] for k in SAMPLE_HEADER} for q in sorted(chosen, key=_qid)]
    raise ValueError(
        f"no draw meets both strata (type {want['type']}, difficulty {want['difficulty']}) in "
        f"{SECOND_RATER_MAX_DRAWS} attempts; the catalogue cannot satisfy both marginals"
    )


def _qid(question: dict) -> str:
    return question["question_id"]


def paths(set_dir: Path | None) -> dict[str, Path]:
    """The files of the main catalogue or, with `set_dir`, of a pilot set."""
    if set_dir is None:
        return {
            "questions_file": QUESTIONS_FILE,
            "ground_truth_file": GROUND_TRUTH_FILE,
            "sections_file": SECTIONS_FILE,
            "documents_file": DOCUMENTS_FILE,
            "freeze_file": CATALOGUE_FREEZE_FILE,
            "items_file": SCORING_ITEMS_FILE,
            "sheet_file": SCORING_SHEET_FILE,
            "checks_file": SCORING_CHECKS_FILE,
            "key_points_file": KEY_POINTS_FILE,
            "scores_file": SCORES_FILE,
            "sample_file": SECOND_RATER_SAMPLE_FILE,
            "dir": SECOND_RATER_DIR,
            "runs_file": GENERATION_RUNS_FILE,
        }
    return {
        "questions_file": set_dir / QUESTIONS_FILE.name,
        "ground_truth_file": set_dir / GROUND_TRUTH_FILE.name,
        "sections_file": SECTIONS_FILE,
        "documents_file": DOCUMENTS_FILE,
        "freeze_file": CATALOGUE_FREEZE_FILE,
        "items_file": set_dir / SCORING_ITEMS_FILE.name,
        "sheet_file": set_dir / SCORING_SHEET_FILE.name,
        "checks_file": set_dir / SCORING_CHECKS_FILE.name,
        "key_points_file": set_dir / KEY_POINTS_FILE.name,
        "scores_file": set_dir / SCORES_FILE.name,
        "sample_file": set_dir / SECOND_RATER_SAMPLE_FILE.name,
        "dir": set_dir / SECOND_RATER_DIR_NAME,
        "runs_file": set_dir / PILOT_RUNS_FILE_NAME,
    }


def own_values(sheet_file: Path, checks_file: Path) -> list[str]:
    """Which of the own scoring files already hold a value (read as plain CSV, no result data)."""
    found = []
    if sheet_file.exists():
        with sheet_file.open(encoding="utf-8", newline="") as f:
            filled = [
                row
                for row in csv.DictReader(f)
                if any((row.get(c) or "").strip() for c in (*RUBRIC_CRITERIA, "notes"))
            ]
        if filled:
            found.append(sheet_file.name)
    if checks_file.exists():
        with checks_file.open(encoding="utf-8", newline="") as f:
            if sum(1 for record in csv.reader(f) if record) > 1:
                found.append(checks_file.name)
    return found


def run_draw(p: dict, n: int, pilot: bool) -> list[dict]:
    """Guard, draw, write the sample and log the run. Main catalogue: every guard aborts; pilot
    set: own values only warn."""
    require_frozen(
        p["questions_file"],
        p["ground_truth_file"],
        p["sections_file"],
        p["documents_file"],
        p["freeze_file"],
    )
    if p["sample_file"].exists():
        raise FileExistsError(f"{p['sample_file']} exists; a draw is never overwritten (ADR 0046)")
    present = own_values(p["sheet_file"], p["checks_file"])
    if present:
        message = (
            f"{', '.join(present)} already hold own values; the draw must come before any own "
            "scoring (ADR 0046)"
        )
        if not pilot:
            raise RuntimeError(message)
        print(f"warning: {message}", file=sys.stderr)
    questions = read_rows(
        p["questions_file"], "question catalogue", QUESTIONS_HEADER, QUESTIONS_REQUIRED
    )
    rows = draw(questions, n, SECOND_RATER_SEED)
    write_csv(p["sample_file"], SAMPLE_HEADER, rows)
    append_step_run(
        DRAW_STEP,
        ",".join(STRATEGY_IDS),
        [p["questions_file"]],
        [p["sample_file"]],
        p["runs_file"],
        extra={"seed": SECOND_RATER_SEED, "questions": n},
    )
    return rows


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Second rating by R2 (ADR 0046).")
    ap.add_argument("--mode", choices=["draw", "export", "close"], required=True)
    ap.add_argument("--set", type=Path, metavar="DIR", help="a pilot set instead of the main run")
    ap.add_argument("--questions", type=int, metavar="N", help="pilot sets only: sample size")
    args = ap.parse_args()
    if args.questions is not None and not args.set:
        ap.error(
            "--questions needs --set: the main run always draws "
            f"{SECOND_RATER_QUESTIONS} questions"
        )
    if args.mode != "draw":
        raise NotImplementedError(f"--mode {args.mode} is not implemented yet")
    if args.set and args.questions is None:
        ap.error("--set needs --questions N for the sample size")
    files = paths(args.set)
    sample = run_draw(files, args.questions or SECOND_RATER_QUESTIONS, pilot=bool(args.set))
    print(f"{len(sample)} questions -> {files['sample_file']}")
