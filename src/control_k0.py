"""Scoring of the control K0 (ADR 0038, 0041): the answers without retrieval.

scaffold_control  After C1-C3 are scored and summarised (scores.csv exists), write the K0 item
                  file and sheet for the questions of scores.csv: one code per question
                  (Q001-K0), the answer and no excerpts. The key points are the frozen ones of
                  the C1-C3 set; the answers must be those of the latest generation run.
summarise_control Check every K0 sheet row against its checks under the K0 rules (no
                  groundedness), write scores_control.csv and compare K0 with C1-C3 on the four
                  criteria of config.CONTROL_CRITERIA, overall, per question type and class, and
                  per closed-book verdict (ADR 0040).

K0 is not scored blind: it has no excerpts, so it is recognisable (ADR 0041). It is scored only
after C1-C3, so knowing what the model answers without help cannot colour the C1-C3 scores.
"""

import json
import statistics
from pathlib import Path

import closed_book
import scoring_rules as rules
from atomic_csv import read_csv, write_csv
from config import (
    CATALOGUE_FREEZE_FILE,
    CLOSED_BOOK_FILE,
    CONTROL_ANSWER_STRATEGIES,
    CONTROL_CRITERIA,
    DOCUMENTS_FILE,
    GENERATED_ANSWERS_CONTROL_FILE,
    GENERATION_RUNS_FILE,
    GROUND_TRUTH_FILE,
    KEY_POINTS_FILE,
    PILOT_RUNS_FILE_NAME,
    QUESTIONS_FILE,
    RUBRIC_MAX_SCORE,
    RUBRIC_RULES_VERSION,
    SCORES_CONTROL_FILE,
    SCORES_FILE,
    SCORING_CHECKS_CONTROL_FILE,
    SCORING_ITEMS_CONTROL_FILE,
    SCORING_SHEET_CONTROL_FILE,
    SECTIONS_FILE,
    STRATEGY_IDS,
)
from evaluate_answers import GROUPS, SCORES_HEADER, catalogue
from generate import ANSWERS_HEADER
from run_log import append_scaffold_run, append_step_run, latest_run, require_run, sha256_of

(CODE_SUFFIX,) = CONTROL_ANSWER_STRATEGIES  # "K0"
CONTROL_SHEET_HEADER = ["code", "question_id", *CONTROL_CRITERIA, "notes"]
CONTROL_SCORES_HEADER = ["question_id", "strategy", *CONTROL_CRITERIA, "total_score"]
EXPERIMENT = ",".join(STRATEGY_IDS)
VERDICT_GROUPS = {"miss": "dependent", "hit": "known"}  # closed-book verdict -> group label
SCAFFOLD_KEYS = (
    "control_answers_file", "questions_file", "ground_truth_file", "scores_file",
    "key_points_file", "items_file", "sheet_file", "generation_runs_file",
)  # fmt: skip


def frozen_key_points(key_points_file: Path, runs_file: Path) -> dict[str, list[str]]:
    """The key points the C1-C3 set froze; refused if missing or changed since."""
    record = latest_run(runs_file, "key_points", EXPERIMENT)
    frozen = record and record["outputs_sha256"].get(key_points_file.name)
    if not frozen or not key_points_file.exists() or sha256_of(key_points_file) != frozen:
        raise ValueError(
            f"K0 needs the frozen key points of the C1-C3 set; {key_points_file} is not frozen "
            f"or differs from the freeze in {runs_file}"
        )
    return rules.key_points(read_csv(key_points_file, rules.KEY_POINTS_HEADER))


def scaffold_control(
    control_answers_file: Path = GENERATED_ANSWERS_CONTROL_FILE,
    questions_file: Path = QUESTIONS_FILE,
    ground_truth_file: Path = GROUND_TRUTH_FILE,
    sections_file: Path = SECTIONS_FILE,
    documents_file: Path = DOCUMENTS_FILE,
    freeze_file: Path = CATALOGUE_FREEZE_FILE,
    scores_file: Path = SCORES_FILE,
    key_points_file: Path = KEY_POINTS_FILE,
    items_file: Path = SCORING_ITEMS_CONTROL_FILE,
    sheet_file: Path = SCORING_SHEET_CONTROL_FILE,
    generation_runs_file: Path = GENERATION_RUNS_FILE,
) -> int:
    """Write the K0 item file and sheet; return the number of codes."""
    questions, truth = catalogue(
        questions_file, ground_truth_file, sections_file, documents_file, freeze_file
    )
    if not scores_file.exists():
        raise ValueError(
            f"{scores_file} is missing: score and summarise C1-C3 first, K0 comes after them "
            "(ADR 0041)"
        )
    if sheet_file.exists():
        raise FileExistsError(f"{sheet_file} exists and may hold K0 scores; move it away first")
    qids = sorted({r["question_id"] for r in read_csv(scores_file, SCORES_HEADER)})
    points = frozen_key_points(key_points_file, generation_runs_file)
    missing = [q for q in qids if q not in points]
    if missing:
        raise ValueError(f"no frozen key points for {missing}")
    answers = read_csv(control_answers_file, ANSWERS_HEADER)
    if not answers:
        raise ValueError(f"{control_answers_file} has no answers; run src/generate.py first")
    foreign = sorted({a["strategy"] for a in answers} - {CODE_SUFFIX})
    if foreign:
        raise ValueError(f"{control_answers_file}: strategy {foreign} is not the control K0")
    ids = [a["question_id"] for a in answers]
    if sorted(ids) != sorted(questions):
        raise ValueError(f"{control_answers_file}: needs exactly one answer per catalogue question")
    require_run(
        generation_runs_file,
        "generate",
        EXPERIMENT,
        [questions_file, ground_truth_file],
        [control_answers_file],
    )
    by_id = {a["question_id"]: a for a in answers}
    items = [
        {
            "code": f"{qid}-{CODE_SUFFIX}",
            "question_id": qid,
            "question": questions[qid]["question"],
            "reference_answer": truth[qid]["expected_answer"],
            "answer": by_id[qid]["answer"],
            "excerpts": [],
        }
        for qid in qids
    ]
    text = "".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items)
    items_file.parent.mkdir(parents=True, exist_ok=True)
    items_file.write_text(text, encoding="utf-8")
    write_csv(
        sheet_file,
        CONTROL_SHEET_HEADER,
        [
            {"code": i["code"], "question_id": i["question_id"]}
            | dict.fromkeys([*CONTROL_CRITERIA, "notes"], "")
            for i in items
        ],
    )
    append_scaffold_run(
        CODE_SUFFIX, len(items), {items_file.name: sha256_of(items_file)}, generation_runs_file
    )
    return len(items)


def _value(row: dict, criterion: str, path: Path) -> int:
    text = row[criterion].strip()
    if not text.isdigit() or int(text) > RUBRIC_MAX_SCORE:
        raise ValueError(f"{path}: {row['code']} {criterion} = {text!r}, not 0-{RUBRIC_MAX_SCORE}")
    return int(text)


def _stats(values: list[dict]) -> dict:
    total = [v["total"] for v in values]
    return {
        "n": len(values),
        "total_score": statistics.mean(total),
        "median": statistics.median(total),
        "sd": statistics.stdev(total) if len(total) > 1 else 0.0,
    } | {c: statistics.mean(v[c] for v in values) for c in CONTROL_CRITERIA}


def summarise_control(
    questions_file: Path = QUESTIONS_FILE,
    ground_truth_file: Path = GROUND_TRUTH_FILE,
    sections_file: Path = SECTIONS_FILE,
    documents_file: Path = DOCUMENTS_FILE,
    freeze_file: Path = CATALOGUE_FREEZE_FILE,
    scores_file: Path = SCORES_FILE,
    key_points_file: Path = KEY_POINTS_FILE,
    items_file: Path = SCORING_ITEMS_CONTROL_FILE,
    sheet_file: Path = SCORING_SHEET_CONTROL_FILE,
    checks_file: Path = SCORING_CHECKS_CONTROL_FILE,
    control_scores_file: Path = SCORES_CONTROL_FILE,
    generation_runs_file: Path = GENERATION_RUNS_FILE,
    closed_book_file: Path | None = CLOSED_BOOK_FILE,
) -> dict[tuple, dict]:
    """Write scores_control.csv; return statistics per (group, value, strategy) for K0 and
    C1-C3 on the four shared criteria."""
    questions, truth = catalogue(
        questions_file, ground_truth_file, sections_file, documents_file, freeze_file
    )
    points = frozen_key_points(key_points_file, generation_runs_file)
    sheet = read_csv(sheet_file, CONTROL_SHEET_HEADER)
    if not sheet:
        raise ValueError(f"{sheet_file} is empty; run --mode scaffold --control first")
    stored = {r["code"]: r for r in read_csv(checks_file, rules.checks_header(True))}
    rows = []
    for row in sheet:
        code = row["code"]
        if code not in stored:
            raise ValueError(f"{checks_file}: no checks for {code}; score it on the Scoring page")
        version, checks = rules.from_row(stored[code], control=True)
        if version != RUBRIC_RULES_VERSION:
            raise ValueError(f"{checks_file}: {code} was scored under rules {version}")
        rules.validate(checks, len(points.get(row["question_id"], [])), control=True)
        for criterion, value in rules.derive_control(checks).items():
            if _value(row, criterion, sheet_file) != value:
                raise ValueError(
                    f"{sheet_file}: {code} {criterion} is {row[criterion]!r}, its checks give "
                    f"{value}"
                )
        values = [int(row[c]) for c in CONTROL_CRITERIA]
        rows.append(
            {"question_id": row["question_id"], "strategy": CODE_SUFFIX}
            | dict(zip(CONTROL_CRITERIA, values, strict=True))
            | {"total_score": f"{sum(values) / len(values):.2f}"}  # steps of 1/4: exact
        )
    write_csv(control_scores_file, CONTROL_SCORES_HEADER, rows)
    append_step_run(
        "summarise_control",
        CODE_SUFFIX,
        [sheet_file, checks_file, key_points_file, scores_file],
        [control_scores_file],
        generation_runs_file,
    )

    k0_ids = {r["question_id"] for r in rows}
    entries = [
        {"question_id": r["question_id"], "strategy": r["strategy"]}
        | {c: int(r[c]) for c in CONTROL_CRITERIA}
        for r in [*read_csv(scores_file, SCORES_HEADER), *rows]
        if r["question_id"] in k0_ids
    ]
    for e in entries:
        e["total"] = sum(e[c] for c in CONTROL_CRITERIA) / len(CONTROL_CRITERIA)
    verdicts: dict[str, str] = {}
    if closed_book_file is not None and closed_book_file.exists():
        screen_rows = closed_book.read_screen(closed_book_file)
        listed = [{"question_id": q, "question": questions[q]["question"]} for q in questions]
        verdicts = {
            q: VERDICT_GROUPS.get(state, "not judged")
            for q, state in closed_book.states(screen_rows, listed, truth).items()
        }
    buckets: dict[tuple, list[dict]] = {}
    order = [CODE_SUFFIX, *STRATEGY_IDS]
    for e in sorted(entries, key=lambda e: (e["question_id"], order.index(e["strategy"]))):
        labels = [("all", "all")] + [(g, questions[e["question_id"]][g]) for g in GROUPS]
        if verdicts:
            labels.append(("closed_book", verdicts[e["question_id"]]))
        for group, value in labels:
            buckets.setdefault((group, value, e["strategy"]), []).append(e)
    return {key: _stats(values) for key, values in buckets.items()}


def print_control_summary(summary: dict[tuple, dict]) -> None:
    short = "".join(f" {c[:6]:>6}" for c in CONTROL_CRITERIA)
    print(f"{'group':28} {'strategy':8} {'n':>3} {'mean':>5} {'median':>6} {'sd':>5}{short}")
    for (group, value, strategy), s in summary.items():
        label = "all" if group == "all" else f"{group}={value}"
        print(
            f"{label:28} {strategy:8} {s['n']:3} {s['total_score']:5.2f} {s['median']:6.2f} "
            f"{s['sd']:5.2f}" + "".join(f" {s[c]:6.2f}" for c in CONTROL_CRITERIA)
        )


def control_paths(set_dir: Path) -> dict[str, Path]:
    """The K0 files of a pilot set; the closed-book verdicts exist for the main catalogue only."""
    return {
        "control_answers_file": set_dir / GENERATED_ANSWERS_CONTROL_FILE.name,
        "questions_file": set_dir / QUESTIONS_FILE.name,
        "ground_truth_file": set_dir / GROUND_TRUTH_FILE.name,
        "scores_file": set_dir / SCORES_FILE.name,
        "key_points_file": set_dir / KEY_POINTS_FILE.name,
        "items_file": set_dir / SCORING_ITEMS_CONTROL_FILE.name,
        "sheet_file": set_dir / SCORING_SHEET_CONTROL_FILE.name,
        "checks_file": set_dir / SCORING_CHECKS_CONTROL_FILE.name,
        "control_scores_file": set_dir / SCORES_CONTROL_FILE.name,
        "generation_runs_file": set_dir / PILOT_RUNS_FILE_NAME,
    }
