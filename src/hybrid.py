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
"""

import csv
import sys
from pathlib import Path

import second_rater
from atomic_csv import read_csv, write_csv
from config import HYBRID_EXTRA_QUESTIONS, HYBRID_EXTRA_SAMPLE_FILE, HYBRID_SEED, RUBRIC_CRITERIA
from freeze import require_frozen
from retrieve import QUESTIONS_HEADER, QUESTIONS_REQUIRED, read_rows
from run_log import append_step_run, require_run

DRAW_STEP = "hybrid_draw"


def paths(set_dir: Path | None) -> dict[str, Path]:
    """The files of second_rater.paths plus the extra sample."""
    p = second_rater.paths(set_dir)
    extra = HYBRID_EXTRA_SAMPLE_FILE if set_dir is None else set_dir / HYBRID_EXTRA_SAMPLE_FILE.name
    return p | {"extra_file": extra}


def _sample_ids(path: Path) -> set[str]:
    return {r["question_id"] for r in read_csv(path, second_rater.SAMPLE_HEADER)}


def questions_with_values(sheet_file: Path, checks_file: Path) -> set[str]:
    """Question IDs (code prefix) with a filled sheet row or a checks row; plain CSV, no results."""
    found = set()
    if sheet_file.exists():
        with sheet_file.open(encoding="utf-8", newline="") as f:
            found |= {
                row["code"].rsplit("-", 1)[0]
                for row in csv.DictReader(f)
                if any((row.get(c) or "").strip() for c in (*RUBRIC_CRITERIA, "notes"))
            }
    if checks_file.exists():
        with checks_file.open(encoding="utf-8", newline="") as f:
            found |= {row["code"].rsplit("-", 1)[0] for row in csv.DictReader(f) if row.get("code")}
    return found


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


def main(argv: list[str] | None = None) -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Hybrid scoring (ADR 0051).")
    ap.add_argument("--mode", choices=["draw"], required=True)
    ap.add_argument("--set", type=Path, metavar="DIR", help="a pilot set instead of the main run")
    args = ap.parse_args(argv)
    files = paths(args.set)
    rows = run_draw(files, HYBRID_EXTRA_QUESTIONS, pilot=bool(args.set))
    print(f"{len(rows)} questions -> {files['extra_file']}")


if __name__ == "__main__":
    main()
