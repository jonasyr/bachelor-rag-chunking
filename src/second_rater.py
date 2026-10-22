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
--mode export  Write R2's set to data/evaluation/second_rater/ (pilot: DIR/second_rater/): the items
               of the drawn questions (lines copied unchanged, same codes and order),
               their frozen key points, an empty scoring sheet and a run log that makes the app
               accept the set as scaffolded and frozen. Never the key and never own checks. Needs
               the draw (checked against its run record), the item file and frozen key points; the
               main run is refused once scores.csv exists or the R2 folder holds values (pilot sets:
               scores.csv only warns). Run record `second_rater_export`.
--mode close   Close R2's rating: every code needs checks and a sheet row, the key points must be
               the frozen ones and every score must follow from its checks under the current rules
               (evaluate_answers.check_derived); the item file must be the exported one. Appends
               the record `second_rater_close` (rater R2, rules version, checksums of items and
               key points as inputs, of checks and sheet as outputs) to the R2 run log, which makes
               the set read-only in the app. A closed rating cannot be closed again.

--questions N (pilot sets only) sets the number of questions; the main catalogue always draws
config.SECOND_RATER_QUESTIONS.
"""

import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

import scoring_store
from atomic_csv import read_csv, write_csv
from config import (
    CATALOGUE_FREEZE_FILE,
    DOCUMENTS_FILE,
    GENERATION_RUNS_FILE,
    GROUND_TRUTH_FILE,
    KEY_POINTS_FILE,
    PILOT_RUNS_FILE_NAME,
    QUESTIONS_FILE,
    RUBRIC_CRITERIA,
    RUBRIC_RULES_VERSION,
    SCORES_FILE,
    SCORING_CHECKS_FILE,
    SCORING_ITEMS_FILE,
    SCORING_SHEET_FILE,
    SECOND_RATER_DIR,
    SECOND_RATER_DIR_NAME,
    SECOND_RATER_MAX_DRAWS,
    SECOND_RATER_PSEUDONYM,
    SECOND_RATER_QUESTIONS,
    SECOND_RATER_SAMPLE_FILE,
    SECOND_RATER_SEED,
    SECTIONS_FILE,
    STRATEGY_IDS,
)
from evaluate_answers import SHEET_HEADER, check_derived
from freeze import require_frozen
from retrieve import QUESTIONS_HEADER, QUESTIONS_REQUIRED, read_rows
from run_log import (
    append_key_points_run,
    append_scaffold_run,
    append_step_run,
    latest_run,
    require_run,
    sha256_of,
)

SAMPLE_HEADER = ["question_id", "type", "difficulty"]
DRAW_STEP = "second_rater_draw"
EXPORT_STEP = "second_rater_export"
CLOSE_STEP = "second_rater_close"
STRATEGY = ",".join(STRATEGY_IDS)


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


def run_export(p: dict, pilot: bool) -> Path:
    """Write R2's set from the drawn questions; return its folder. Main run: every guard aborts;
    pilot set: a present scores.csv only warns."""
    for key in ("sample_file", "items_file"):
        if not p[key].exists():
            raise RuntimeError(f"{p[key]} not found; run the draw and the scaffold first")
    require_run(p["runs_file"], DRAW_STEP, STRATEGY, [], [p["sample_file"]])
    mine = scoring_store.ScoringSet(
        "own",
        p["items_file"],
        p["sheet_file"],
        p["scores_file"],
        p["key_points_file"],
        p["checks_file"],
        p["runs_file"],
    )
    try:
        scoring_store.require_frozen_key_points(mine)
    except PermissionError as error:
        raise RuntimeError(f"{error}; freeze the key points in the app first") from None
    if p["scores_file"].exists():
        message = f"{p['scores_file']} exists: the scores were unblinded already (ADR 0046)"
        if not pilot:
            raise RuntimeError(message)
        print(f"warning: {message}", file=sys.stderr)
    out = p["dir"]
    sheet_file, checks_file = out / SCORING_SHEET_FILE.name, out / SCORING_CHECKS_FILE.name
    present = own_values(sheet_file, checks_file)
    if (out / SCORES_FILE.name).exists():
        present.append(SCORES_FILE.name)
    if latest_run(out / PILOT_RUNS_FILE_NAME, CLOSE_STEP, STRATEGY) is not None:
        present.append("close record")
    if present:
        raise FileExistsError(f"{out} already holds values ({', '.join(present)}); not overwritten")
    sampled = {r["question_id"] for r in read_csv(p["sample_file"], SAMPLE_HEADER)}
    lines = [
        line
        for line in p["items_file"].read_text(encoding="utf-8").splitlines(keepends=True)
        if line.strip() and json.loads(line)["question_id"] in sampled
    ]
    items = [json.loads(line) for line in lines]
    for qid in sorted(sampled):
        n = sum(i["question_id"] == qid for i in items)
        if n != len(STRATEGY_IDS):
            raise RuntimeError(
                f"{qid} has {n} items in {p['items_file']}, expected {len(STRATEGY_IDS)}"
            )
    points = [
        r
        for r in read_csv(p["key_points_file"], scoring_store.KEY_POINTS_HEADER)
        if r["question_id"] in sampled
    ]
    out.mkdir(parents=True, exist_ok=True)
    items_out, points_out = out / SCORING_ITEMS_FILE.name, out / KEY_POINTS_FILE.name
    items_out.write_text("".join(lines), encoding="utf-8")
    write_csv(points_out, scoring_store.KEY_POINTS_HEADER, points)
    write_csv(
        sheet_file,
        SHEET_HEADER,
        [
            {"code": i["code"], "question_id": i["question_id"]}
            | dict.fromkeys([*RUBRIC_CRITERIA, "notes"], "")
            for i in items
        ],
    )
    runs_out = out / PILOT_RUNS_FILE_NAME
    runs_out.unlink(missing_ok=True)  # no values yet: a repeated export starts the log afresh
    items_sha = sha256_of(items_out)
    append_scaffold_run(STRATEGY, len(items), {items_out.name: items_sha}, runs_out)
    append_key_points_run(
        STRATEGY, {points_out.name: sha256_of(points_out), items_out.name: items_sha}, runs_out
    )
    append_step_run(
        EXPORT_STEP,
        STRATEGY,
        [p["sample_file"], p["items_file"], p["key_points_file"]],
        [items_out, points_out],
        p["runs_file"],
    )
    return out


def run_close(p: dict) -> dict:
    """Check R2's finished rating and log the close record; return it."""
    out = p["dir"]
    items, points = out / SCORING_ITEMS_FILE.name, out / KEY_POINTS_FILE.name
    sheet, checks = out / SCORING_SHEET_FILE.name, out / SCORING_CHECKS_FILE.name
    runs = out / PILOT_RUNS_FILE_NAME
    for f in (items, points, sheet, runs):
        if not f.exists():
            raise RuntimeError(f"{f} not found; export R2's set first")
    if latest_run(runs, CLOSE_STEP, STRATEGY) is not None:
        raise RuntimeError(f"the second rating in {out} is closed already")
    require_run(runs, "scaffold", STRATEGY, [], [items])  # the exported item file, unchanged
    check_derived(sheet, checks, points, runs)  # every code has checks; scores follow from them
    return append_step_run(
        CLOSE_STEP,
        STRATEGY,
        [items, points],
        [checks, sheet],
        runs,
        extra={"rater": SECOND_RATER_PSEUDONYM, "rules_version": RUBRIC_RULES_VERSION},
    )


def main(argv: list[str] | None = None) -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Second rating by R2 (ADR 0046).")
    ap.add_argument("--mode", choices=["draw", "export", "close"], required=True)
    ap.add_argument("--set", type=Path, metavar="DIR", help="a pilot set instead of the main run")
    ap.add_argument("--questions", type=int, metavar="N", help="draw, pilot sets only: sample size")
    args = ap.parse_args(argv)
    if args.questions is not None and args.mode != "draw":
        ap.error("--questions is for --mode draw only")
    if args.questions is not None and not args.set:
        ap.error(
            "--questions needs --set: the main run always draws "
            f"{SECOND_RATER_QUESTIONS} questions"
        )
    if args.mode == "draw" and args.set and args.questions is None:
        ap.error("--mode draw with --set needs --questions N for the sample size")
    files = paths(args.set)
    if args.mode == "close":
        print(f"R2 rating closed -> {run_close(files)['outputs_sha256']}")
        return
    if args.mode == "export":
        print(f"R2 set -> {run_export(files, pilot=bool(args.set))}")
        return
    sample = run_draw(files, args.questions or SECOND_RATER_QUESTIONS, pilot=bool(args.set))
    print(f"{len(sample)} questions -> {files['sample_file']}")


if __name__ == "__main__":
    main()
