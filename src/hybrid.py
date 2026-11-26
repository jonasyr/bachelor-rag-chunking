"""Hybrid scoring (ADR 0051): which questions Jonas scores himself.

Jonas scores the questions of the R2 sample (second_rater_sample.csv, ADR 0046) and
config.HYBRID_EXTRA_QUESTIONS more; the LLM cross-check scores every answer.

--mode draw  Draw the extra questions from the questions outside the R2 sample, stratified by
             question type and construction class like the R2 draw (second_rater.draw, seed
             config.HYBRID_SEED). Writes hybrid_extra_sample.csv (question_id, type, difficulty,
             sorted by question_id) and a run record `hybrid_draw` (seed, count, checksums of
             questions.csv and the R2 sample as inputs, of the extra sample as output).
             The catalogue must be frozen, the R2 sample must be the one its draw recorded, an
             existing extra sample is never overwritten, and no question outside the R2 sample may
             hold own values yet (values on the R2 sample are expected). The draw reads
             questions.csv and the R2 sample only; of the result files it merely checks which
             questions already hold own values. With --set DIR (pilot set) that guard only warns.
--mode summarise  The values of the thesis: Jonas' values for his questions (both samples), the
             LLM's for the rest, unblinded with the key into scores.csv (HYBRID_SCORES_HEADER: a
             `rater` column, "human" or "llm"), and the LLM's values of every answer into
             llm_rater/scores.csv (SCORES_HEADER) for the sensitivity analysis and the K0
             comparison. Refuses unless both draws and the LLM run (scope "all") built exactly
             these files, Jonas' sheet and checks hold values only on his questions and on all of
             them, and every sheet row equals what its checks derive. Run record
             `hybrid_summarise`: Jonas' files under inputs_sha256/outputs_sha256, the LLM's under
             llm_inputs_sha256/llm_outputs_sha256 (same file names as Jonas' files).
"""

import csv
import sys
from collections import Counter
from pathlib import Path

import control_k0
import llm_rater
import second_rater
from atomic_csv import read_csv, write_csv
from config import (
    HYBRID_EXTRA_QUESTIONS,
    HYBRID_EXTRA_SAMPLE_FILE,
    HYBRID_SEED,
    LLM_RATER_SCORES_FILE,
    QUESTIONS_FILE,
    RUBRIC_CRITERIA,
    SCORES_CONTROL_FILE,
    SCORES_FILE,
    SCORING_CHECKS_CONTROL_FILE,
    SCORING_CHECKS_FILE,
    SCORING_KEY_FILE,
    SCORING_SHEET_CONTROL_FILE,
    SCORING_SHEET_FILE,
)
from evaluate_answers import (
    HYBRID_SCORES_HEADER,
    KEY_HEADER,
    SCORES_HEADER,
    SHEET_HEADER,
    check_derived,
    unblind_rows,
)
from freeze import require_frozen
from retrieve import QUESTIONS_HEADER, QUESTIONS_REQUIRED, read_rows
from run_log import append_step_run, require_run, sha256_of

DRAW_STEP = "hybrid_draw"
SUMMARISE_STEP = "hybrid_summarise"
RATER_HUMAN = "human"  # the `rater` of a row of scores.csv (no names, ADR 0051)
RATER_LLM = "llm"
STRATEGY = second_rater.STRATEGY


def paths(set_dir: Path | None) -> dict[str, Path]:
    """The files of second_rater.paths plus the extra sample, the key and the LLM's files."""
    p = second_rater.paths(set_dir)
    if set_dir is None:
        extra, key = HYBRID_EXTRA_SAMPLE_FILE, SCORING_KEY_FILE
    else:
        extra, key = set_dir / HYBRID_EXTRA_SAMPLE_FILE.name, set_dir / SCORING_KEY_FILE.name
    llm_dir = llm_rater.paths(set_dir)["out_dir"]
    llm_scores = LLM_RATER_SCORES_FILE if set_dir is None else llm_dir / SCORES_FILE.name
    scores_control = SCORES_CONTROL_FILE if set_dir is None else set_dir / SCORES_CONTROL_FILE.name
    return p | {
        "control_items_file": llm_rater.paths(set_dir)["control_items_file"],
        "llm_control_sheet_file": llm_dir / SCORING_SHEET_CONTROL_FILE.name,
        "llm_control_checks_file": llm_dir / SCORING_CHECKS_CONTROL_FILE.name,
        "scores_control_file": scores_control,
        "extra_file": extra,
        "key_file": key,
        "llm_dir": llm_dir,
        "llm_sheet_file": llm_dir / SCORING_SHEET_FILE.name,
        "llm_checks_file": llm_dir / SCORING_CHECKS_FILE.name,
        "llm_scores_file": llm_scores,
    }


def _sample_ids(path: Path) -> set[str]:
    return {r["question_id"] for r in read_csv(path, second_rater.SAMPLE_HEADER)}


def codes_with_values(sheet_file: Path, checks_file: Path) -> set[str]:
    """Codes with a filled sheet row or a checks row; plain CSV, no results."""
    found = set()
    if sheet_file.exists():
        with sheet_file.open(encoding="utf-8", newline="") as f:
            found |= {
                row["code"]
                for row in csv.DictReader(f)
                if any((row.get(c) or "").strip() for c in (*RUBRIC_CRITERIA, "notes"))
            }
    if checks_file.exists():
        with checks_file.open(encoding="utf-8", newline="") as f:
            found |= {row["code"] for row in csv.DictReader(f) if row.get("code")}
    return found


def questions_with_values(sheet_file: Path, checks_file: Path) -> set[str]:
    """Question IDs (code prefix) of codes_with_values."""
    return {code.rsplit("-", 1)[0] for code in codes_with_values(sheet_file, checks_file)}


def human_questions(p: dict[str, Path]) -> set[str]:
    """The questions Jonas scores: the R2 sample and the extra sample."""
    return _sample_ids(p["sample_file"]) | _sample_ids(p["extra_file"])


def run_draw(p: dict[str, Path], n: int, pilot: bool) -> list[dict]:
    """Guard, draw, write the extra sample and log the run. Main catalogue: every guard aborts;
    pilot set: own values outside the R2 sample only warn."""
    require_frozen(
        p["questions_file"],
        p["ground_truth_file"],
        p["sections_file"],
        p["documents_file"],
        p["freeze_file"],
    )
    require_run(
        p["runs_file"],
        second_rater.DRAW_STEP,
        second_rater.STRATEGY,
        [p["questions_file"]],
        [p["sample_file"]],
    )
    if p["extra_file"].exists():
        raise FileExistsError(f"{p['extra_file']} exists; a draw is never overwritten (ADR 0051)")
    first = _sample_ids(p["sample_file"])
    scored = sorted(questions_with_values(p["sheet_file"], p["checks_file"]) - first)
    if scored:
        message = (
            f"own values exist for {', '.join(scored)} outside the R2 sample; the extra draw must "
            "come before any own scoring of those questions (ADR 0051)"
        )
        if not pilot:
            raise RuntimeError(message)
        print(f"warning: {message}", file=sys.stderr)
    questions = read_rows(
        p["questions_file"], "question catalogue", QUESTIONS_HEADER, QUESTIONS_REQUIRED
    )
    rows = second_rater.draw(
        [q for q in questions if q["question_id"] not in first], n, HYBRID_SEED
    )
    write_csv(p["extra_file"], second_rater.SAMPLE_HEADER, rows)
    append_step_run(
        DRAW_STEP,
        second_rater.STRATEGY,
        [p["questions_file"], p["sample_file"]],
        [p["extra_file"]],
        p["runs_file"],
        extra={"seed": HYBRID_SEED, "questions": n},
    )
    return rows


def _own_inputs(p: dict[str, Path]) -> list[Path]:
    keys = ("sheet_file", "checks_file", "key_file", "key_points_file", "sample_file", "extra_file")
    return [p[k] for k in keys]


def _require_exists(path: Path, command: str) -> None:
    if not path.exists():
        raise RuntimeError(f"{path} not found; run {command} first (ADR 0051)")


def run_summarise(p: dict[str, Path]) -> dict[str, int]:
    """Guard, merge Jonas' values on his questions with the LLM's on the rest, unblind, write
    scores.csv (with `rater`) and llm_rater/scores.csv and log the run; return the answers per
    rater. Nothing is written unless every guard passes."""
    require_frozen(
        p["questions_file"],
        p["ground_truth_file"],
        p["sections_file"],
        p["documents_file"],
        p["freeze_file"],
    )
    _require_exists(p["sample_file"], "src/second_rater.py --mode draw")
    _require_exists(p["extra_file"], "src/hybrid.py --mode draw")
    require_run(p["runs_file"], second_rater.DRAW_STEP, STRATEGY, [], [p["sample_file"]])
    require_run(p["runs_file"], DRAW_STEP, STRATEGY, [p["sample_file"]], [p["extra_file"]])
    for path in (p["llm_sheet_file"], p["llm_checks_file"]):
        _require_exists(path, "src/llm_rater.py")
    record = require_run(
        p["runs_file"],
        llm_rater.STEP,
        llm_rater.STRATEGY,
        [p["items_file"], p["key_points_file"]],
        [p["llm_checks_file"], p["llm_sheet_file"]],
    )
    if record.get("scope") != "all":
        raise RuntimeError(
            f"the latest {llm_rater.STEP} run has scope {record.get('scope')!r}; the LLM must "
            'rate every answer, ADR 0051 (LLM_RATER_SCOPE = "all")'
        )

    human = human_questions(p)
    sheet = read_csv(p["sheet_file"], SHEET_HEADER)
    outside = sorted(
        c
        for c in codes_with_values(p["sheet_file"], p["checks_file"])
        if c.rsplit("-", 1)[0] not in human
    )
    if outside:
        raise RuntimeError(
            f"own values or checks outside the hybrid questions: {', '.join(outside)}; the LLM "
            "scores those questions (ADR 0051)"
        )
    human_codes = {r["code"] for r in sheet if r["question_id"] in human}
    check_derived(
        p["sheet_file"], p["checks_file"], p["key_points_file"], p["runs_file"], codes=human_codes
    )
    check_derived(p["llm_sheet_file"], p["llm_checks_file"], p["key_points_file"], p["runs_file"])
    llm_sheet = read_csv(p["llm_sheet_file"], SHEET_HEADER)
    llm_by_code = {r["code"]: r for r in llm_sheet}
    if sorted(llm_by_code) != sorted(r["code"] for r in sheet):
        raise ValueError(f"{p['llm_sheet_file']}: the codes differ from {p['sheet_file']}")

    questions = read_rows(
        p["questions_file"], "question catalogue", QUESTIONS_HEADER, QUESTIONS_REQUIRED
    )
    qids = sorted(q["question_id"] for q in questions)
    key = read_csv(p["key_file"], KEY_HEADER)
    merged = [r if r["code"] in human_codes else llm_by_code[r["code"]] for r in sheet]
    mixed = [
        r | {"rater": RATER_HUMAN if r["question_id"] in human else RATER_LLM}
        for r in unblind_rows(merged, key, qids, p["sheet_file"], p["key_file"])
    ]
    llm_only = unblind_rows(llm_sheet, key, qids, p["llm_sheet_file"], p["key_file"])

    write_csv(p["scores_file"], HYBRID_SCORES_HEADER, mixed)
    write_csv(p["llm_scores_file"], SCORES_HEADER, llm_only)
    counts = Counter(r["rater"] for r in mixed)
    answers = {RATER_HUMAN: counts[RATER_HUMAN], RATER_LLM: counts[RATER_LLM]}
    llm_inputs = (p["llm_sheet_file"], p["llm_checks_file"])
    append_step_run(
        SUMMARISE_STEP,
        STRATEGY,
        _own_inputs(p),
        [p["scores_file"]],
        p["runs_file"],
        extra={
            "llm_inputs_sha256": {f.name: sha256_of(f) for f in llm_inputs},
            "llm_outputs_sha256": {p["llm_scores_file"].name: sha256_of(p["llm_scores_file"])},
            "answers": answers,
        },
    )
    return answers


def require_summarise(p: dict[str, Path]) -> dict:
    """The latest hybrid_summarise record; raise unless every file it hashed, Jonas' and the
    LLM's (kept apart because their names are the same), is as it is now."""
    record = require_run(
        p["runs_file"], SUMMARISE_STEP, STRATEGY, _own_inputs(p), [p["scores_file"]]
    )
    llm_files = [
        ("llm_inputs_sha256", p["llm_sheet_file"]),
        ("llm_inputs_sha256", p["llm_checks_file"]),
        ("llm_outputs_sha256", p["llm_scores_file"]),
    ]
    for field, path in llm_files:
        if not path.exists() or record.get(field, {}).get(path.name) != sha256_of(path):
            raise RuntimeError(
                f"{path} differs from the latest {SUMMARISE_STEP} run of "
                f"{record.get('date', '?')}; run src/hybrid.py --mode summarise again"
            )
    return record


def run_summarise_control(p: dict[str, Path]) -> dict[tuple, dict]:
    """Score K0 from the LLM's checks (scores_control.csv) and return the K0 and C1-C3 statistics
    with the LLM's values on both sides (ADR 0051). Refuses unless hybrid summarise and the LLM's
    control run happened and none of their files changed since."""
    require_summarise(p)  # the LLM's folder and the summarise record, files unchanged
    for path in (p["llm_control_sheet_file"], p["llm_control_checks_file"]):
        _require_exists(path, "src/llm_rater.py --control")
    require_run(
        p["runs_file"],
        llm_rater.CONTROL_STEP,
        control_k0.CODE_SUFFIX,
        [p["control_items_file"], p["key_points_file"]],
        [p["llm_control_checks_file"], p["llm_control_sheet_file"]],
    )
    # summarise_control's record names `scores.csv` once: the LLM's file, not the mixed one
    return control_k0.summarise_control(
        questions_file=p["questions_file"],
        ground_truth_file=p["ground_truth_file"],
        sections_file=p["sections_file"],
        documents_file=p["documents_file"],
        freeze_file=p["freeze_file"],
        scores_file=p["llm_scores_file"],
        key_points_file=p["key_points_file"],
        items_file=p["control_items_file"],
        sheet_file=p["llm_control_sheet_file"],
        checks_file=p["llm_control_checks_file"],
        control_scores_file=p["scores_control_file"],
        generation_runs_file=p["runs_file"],
        # closed-book verdicts exist for the main catalogue only (as control_paths)
        **({} if p["questions_file"] == QUESTIONS_FILE else {"closed_book_file": None}),
    )


def main(argv: list[str] | None = None) -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Hybrid scoring (ADR 0051).")
    ap.add_argument("--mode", choices=["draw", "summarise", "summarise-control"], required=True)
    ap.add_argument("--set", type=Path, metavar="DIR", help="a pilot set instead of the main run")
    args = ap.parse_args(argv)
    files = paths(args.set)
    if args.mode == "summarise-control":
        control_k0.print_control_summary(run_summarise_control(files))
        print(f"K0 from the LLM -> {files['scores_control_file']}")
        return
    if args.mode == "summarise":
        answers = run_summarise(files)
        print(
            f"{answers[RATER_HUMAN]} human + {answers[RATER_LLM]} llm answers -> "
            f"{files['scores_file']}; LLM only -> {files['llm_scores_file']}"
        )
        return
    rows = run_draw(files, HYBRID_EXTRA_QUESTIONS, pilot=bool(args.set))
    print(f"{len(rows)} questions -> {files['extra_file']}")


if __name__ == "__main__":
    main()
