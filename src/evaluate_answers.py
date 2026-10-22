"""Answer quality evaluation: blind rubric 0-2 on five criteria (ADR 0013, 0032), derived from
checks by fixed rules (ADR 0035, 0036).

--mode scaffold  From generated_answers.csv write four files:
                 scoring_packet.md  what the rater reads: per question the question and the
                                    reference answer, then each answer under a neutral code
                                    (Q001-A, Q001-B, ...) with the excerpts the model saw;
                 scoring_sheet.csv  one row per code, criteria 0-2 (written by the Scoring page
                                    from the checks), notes;
                 scoring_key.csv    which strategy each code stands for; not opened while scoring;
                 scoring_items.jsonl the same answers as data for the scoring page (ADR 0034),
                                    equally blind.
                 The answers of a question appear in an order shuffled with config.SCORING_SEED,
                 and nothing in packet or sheet names the strategy (no strategy keys, no chunk
                 IDs). An existing sheet or key is never overwritten; with both present and the
                 same key, only packet and item file are written again (after a fresh clone).
                 The answers and chunk files must be exactly those of the latest generation run
                 (ADR 0033).
--mode summarise Check the filled sheet against its key (every code exactly once, every
                 criterion an integer 0-2), unblind it into scores.csv with total_score = mean of
                 the criteria, and print mean, median and standard deviation per strategy,
                 overall and per question type and construction class. With a checks file
                 (scoring_checks.csv, ADR 0035) the key points must be the frozen ones and every
                 sheet row must equal the scores its checks derive under the current rules.
--control        Both modes on the control K0 instead (src/control_k0.py, ADR 0041): scaffold
                 only after C1-C3 are summarised (scores.csv exists); summarise compares K0 with
                 C1-C3 on the four criteria of config.CONTROL_CRITERIA.

Both modes use the main catalogue only while it matches its freeze record (ADR 0030). With --set
DIR they work on a pilot set instead, and --limit N (pilot sets only) scores its first N
questions. Answers exist only for the experiment C1-C3, never for the control K1 (ADR 0026), and
every question of the catalogue needs exactly one answer of every strategy.

Output schema of scores.csv (docs/reference/data-formats.md): question_id, strategy,
correctness, completeness, groundedness, no_hallucination, clarity, total_score
"""

import hashlib
import json
import random
import re
import statistics
from pathlib import Path

import scoring_rules as rules
from atomic_csv import read_csv, write_csv
from config import (
    CATALOGUE_FREEZE_FILE,
    CHUNK_FILES,
    DOCUMENTS_FILE,
    GENERATED_ANSWERS_FILE,
    GENERATION_RUNS_FILE,
    GROUND_TRUTH_FILE,
    KEY_POINTS_FILE,
    PILOT_RUNS_FILE_NAME,
    QUESTIONS_FILE,
    RUBRIC_CRITERIA,
    RUBRIC_MAX_SCORE,
    RUBRIC_RULES_VERSION,
    SCORES_FILE,
    SCORING_CHECKS_FILE,
    SCORING_ITEMS_FILE,
    SCORING_KEY_FILE,
    SCORING_METHOD,
    SCORING_PACKET_FILE,
    SCORING_SEED,
    SCORING_SHEET_FILE,
    SECTIONS_FILE,
    STRATEGY_IDS,
)
from embed import load_jsonl
from freeze import is_main_catalogue, require_frozen, require_rules_version
from generate import ANSWERS_HEADER
from prompt import context
from retrieve import (
    GROUND_TRUTH_HEADER,
    QUESTIONS_HEADER,
    QUESTIONS_REQUIRED,
    read_rows,
    split_ids,
)
from run_log import append_scaffold_run, append_step_run, latest_run, require_run, sha256_of

SCORES_HEADER = ["question_id", "strategy", *RUBRIC_CRITERIA, "total_score"]
SHEET_HEADER = ["code", "question_id", *RUBRIC_CRITERIA, "notes"]
KEY_HEADER = ["code", "question_id", "strategy"]
GROUPS = ["type", "difficulty"]  # questions.csv columns the summary is broken down by
LETTERS = "ABCDEFGHIJ"  # code suffixes, one per strategy of a question


def catalogue(
    questions_file: Path,
    ground_truth_file: Path,
    sections_file: Path,
    documents_file: Path,
    freeze_file: Path,
) -> tuple[dict[str, dict], dict[str, dict]]:
    """Questions and ground truth by ID; the main catalogue only while it is frozen and under the
    rules version of its freeze."""
    require_frozen(questions_file, ground_truth_file, sections_file, documents_file, freeze_file)
    if is_main_catalogue(questions_file, ground_truth_file):
        require_rules_version(freeze_file)
    questions = read_rows(
        questions_file, "question catalogue", QUESTIONS_HEADER, QUESTIONS_REQUIRED
    )
    truth = read_rows(ground_truth_file, "ground truth", GROUND_TRUTH_HEADER, GROUND_TRUTH_HEADER)
    return (
        {q["question_id"]: q for q in questions},
        {t["question_id"]: t for t in truth},
    )


def scored_questions(
    questions: dict[str, dict],
    limit: int | None,
    questions_file: Path,
    ground_truth_file: Path,
) -> list[str]:
    """The question IDs to score: all, or for a pilot set the first `limit` in ID order."""
    qids = sorted(questions)
    if limit is None:
        return qids
    if limit < 1:
        raise ValueError(f"limit must be a positive number of questions, got {limit}")
    if is_main_catalogue(questions_file, ground_truth_file):
        raise ValueError("a limit is for pilot sets only; every experiment answer is scored (D32)")
    return qids[:limit]


def check_grid(path: Path, rows: list[dict], qids: list[str]) -> None:
    """Every question of the catalogue has exactly one row per experiment strategy, nothing
    else, so no strategy is compared on fewer questions than the others."""
    pairs = [(r["question_id"], r["strategy"]) for r in rows]
    foreign = sorted({s for _, s in pairs} - set(STRATEGY_IDS))
    if foreign:
        raise ValueError(f"{path}: strategy {foreign} is not in the experiment C1-C3 (no K1)")
    duplicates = sorted({p for p in pairs if pairs.count(p) > 1})
    if duplicates:
        raise ValueError(f"{path}: duplicate rows {duplicates}")
    foreign_questions = sorted({q for q, _ in pairs} - set(qids))
    if foreign_questions:
        raise ValueError(f"{path}: questions {foreign_questions} are not in the catalogue")
    missing = [f"{q}/{s}" for q in qids for s in STRATEGY_IDS if (q, s) not in pairs]
    if missing:
        raise ValueError(f"{path}: rows missing for {missing}")


def fenced(text: str) -> str:
    """Text in a code fence longer than any backtick run inside, so it cannot end the fence."""
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}text\n{text}\n{fence}"


def scaffold(
    answers_file: Path = GENERATED_ANSWERS_FILE,
    questions_file: Path = QUESTIONS_FILE,
    ground_truth_file: Path = GROUND_TRUTH_FILE,
    sections_file: Path = SECTIONS_FILE,
    documents_file: Path = DOCUMENTS_FILE,
    freeze_file: Path = CATALOGUE_FREEZE_FILE,
    chunk_files: dict[str, Path] = CHUNK_FILES,
    sheet_file: Path = SCORING_SHEET_FILE,
    packet_file: Path = SCORING_PACKET_FILE,
    key_file: Path = SCORING_KEY_FILE,
    items_file: Path = SCORING_ITEMS_FILE,
    seed: int = SCORING_SEED,
    generation_runs_file: Path = GENERATION_RUNS_FILE,
    limit: int | None = None,
) -> int:
    """Write packet, sheet and key for blind scoring; return the number of answers.

    `limit` (pilot sets only) scores the first questions in ID order; all answers are still
    checked."""
    questions, truth = catalogue(
        questions_file, ground_truth_file, sections_file, documents_file, freeze_file
    )
    scored = scored_questions(questions, limit, questions_file, ground_truth_file)
    # Sheet and key both present: only packet and item file are written again, and only if the
    # key is the one this call computes (restores the ignored files after a fresh clone).
    restoring = sheet_file.exists() and key_file.exists()
    for path in (sheet_file, key_file):
        if path.exists() and not restoring:
            raise FileExistsError(
                f"{path} exists and may hold manual scores or their key; move it away to "
                "start afresh"
            )
    answers = read_csv(answers_file, ANSWERS_HEADER)
    if not answers:
        raise ValueError(f"{answers_file} has no answers; run src/generate.py first")
    qids = sorted(questions)
    check_grid(answers_file, answers, qids)
    if sorted(chunk_files) != sorted(STRATEGY_IDS):
        raise ValueError(f"chunk_files must cover exactly the strategies {sorted(STRATEGY_IDS)}")
    # the packet must show the excerpts the model saw: the chunk files and answers of the run
    inputs = [questions_file, ground_truth_file, *(chunk_files[k] for k in STRATEGY_IDS)]
    require_run(generation_runs_file, "generate", ",".join(STRATEGY_IDS), inputs, [answers_file])
    chunks = {
        key: {c["chunk_id"]: c for c in load_jsonl(path, "run src/chunking.py first")}
        for key, path in chunk_files.items()
    }
    by_pair = {(a["question_id"], a["strategy"]): a for a in answers}
    for (qid, key), answer in by_pair.items():
        unknown = [cid for cid in split_ids(answer["sources"]) if cid not in chunks[key]]
        if unknown:
            raise ValueError(f"{answers_file}: {qid}/{key} cites unknown chunk {unknown}")

    rng = random.Random(seed)
    key_rows, sheet_rows = [], []
    items: list[dict] = []
    packet = [
        "# Scoring packet",
        "",
        "A reading copy. Score in the app (page Scoring): freeze the key points, then answer the "
        "checks per code; the five scores follow from the rules "
        "(docs/reference/evaluation.md#regelbasierte-bewertung, ADR 0035, 0036). Do not open "
        "scoring_key.csv before every code is scored.",
    ]
    for qid in scored:
        order = list(STRATEGY_IDS)
        rng.shuffle(order)
        packet += [
            "",
            f"## {qid}",
            "",
            f"**Question:** {questions[qid]['question']}",
            "",
            f"**Reference answer:** {truth[qid]['expected_answer']}",
        ]
        for letter, key in zip(LETTERS, order, strict=False):
            code = f"{qid}-{letter}"
            answer = by_pair[qid, key]
            key_rows.append({"code": code, "question_id": qid, "strategy": key})
            sheet_rows.append(
                {"code": code, "question_id": qid} | dict.fromkeys([*RUBRIC_CRITERIA, "notes"], "")
            )
            items.append(
                {
                    "code": code,
                    "question_id": qid,
                    "question": questions[qid]["question"],
                    "reference_answer": truth[qid]["expected_answer"],
                    "answer": answer["answer"],
                    "excerpts": [chunks[key][cid]["text"] for cid in split_ids(answer["sources"])],
                }
            )
            packet += [
                "",
                f"### {code}",
                "",
                "**Answer:**",
                "",
                fenced(answer["answer"]),
                "",
                "**Excerpts the model saw:**",
                "",
                fenced(context(split_ids(answer["sources"]), chunks[key])),
            ]
    items_text = "".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items)
    items_sha = hashlib.sha256(items_text.encode("utf-8")).hexdigest()
    strategy = ",".join(STRATEGY_IDS)
    if restoring:
        refuse = "; move sheet and key away to start afresh"
        try:
            same_key = read_csv(key_file, KEY_HEADER) == key_rows
        except ValueError:
            same_key = False
        if not same_key:
            raise FileExistsError(
                f"{sheet_file} and {key_file} exist and may hold manual scores or their key, and "
                f"the key differs from this call's (other --set or --limit){refuse}"
            )
        # the scores belong to exactly the items they were given on: same answers, excerpts,
        # questions and reference answers as the logged scaffold
        record = latest_run(generation_runs_file, "scaffold", strategy)
        if record is None:
            raise FileExistsError(
                f"{generation_runs_file} has no scaffold record for the existing sheet{refuse}"
            )
        if record.get("outputs_sha256", {}).get(items_file.name) != items_sha:
            raise FileExistsError(
                f"the items differ from those {sheet_file} was scored on (answers, excerpts or "
                f"reference answers changed){refuse}"
            )
    else:
        write_csv(key_file, KEY_HEADER, key_rows)
        write_csv(sheet_file, SHEET_HEADER, sheet_rows)
    packet_file.parent.mkdir(parents=True, exist_ok=True)
    packet_file.write_text("\n".join(packet) + "\n", encoding="utf-8")
    items_file.parent.mkdir(parents=True, exist_ok=True)
    items_file.write_text(items_text, encoding="utf-8")
    if not restoring:
        append_scaffold_run(
            strategy, len(key_rows), {items_file.name: items_sha}, generation_runs_file
        )
    return len(key_rows)


def criterion_value(row: dict, criterion: str, path: Path) -> int:
    where = f"{path}: {row['code']} {criterion}"
    text = row[criterion].strip()
    if not text:
        raise ValueError(f"{where} is unscored")
    if not text.isdigit() or int(text) > RUBRIC_MAX_SCORE:
        raise ValueError(f"{where} = {text!r}, must be an integer 0-{RUBRIC_MAX_SCORE}")
    return int(text)


def unblind(sheet_file: Path, key_file: Path, qids: list[str]) -> list[dict]:
    """The sheet's scores with their strategies, in (question_id, strategy) order."""
    sheet = read_csv(sheet_file, SHEET_HEADER)
    key = read_csv(key_file, KEY_HEADER)
    if not sheet or not key:
        raise ValueError("sheet or key is empty; run --mode scaffold first")
    check_grid(key_file, key, qids)
    codes = [r["code"] for r in sheet]
    if sorted(codes) != sorted(r["code"] for r in key):
        raise ValueError(f"{sheet_file}: the codes do not match the key {key_file}")
    by_code = {r["code"]: r for r in key}
    for row in sheet:
        if row["question_id"] != by_code[row["code"]]["question_id"]:
            raise ValueError(f"{sheet_file}: {row['code']} has another question in the key")
    rows = []
    for row in sheet:
        values = [criterion_value(row, c, sheet_file) for c in RUBRIC_CRITERIA]
        rows.append(
            {"question_id": row["question_id"], "strategy": by_code[row["code"]]["strategy"]}
            | dict(zip(RUBRIC_CRITERIA, values, strict=True))
            | {"total_score": f"{sum(values) / len(values):.1f}"}  # steps of 1/5: exact
        )
    order = list(STRATEGY_IDS)
    return sorted(rows, key=lambda r: (r["question_id"], order.index(r["strategy"])))


def check_derived(
    sheet_file: Path, checks_file: Path, key_points_file: Path, runs_file: Path
) -> None:
    """For a rule-based scaffold (ADR 0036), and wherever key points are frozen or a checks file
    exists (ADR 0035): the checks file exists, the key points are the frozen ones, every checks
    row marks as many points as its question has, and every sheet row equals the scores its
    checks derive under the current rules, so neither a hand-entered or hand-edited score,
    changed key points nor an older rule version can be unblinded. Only a scaffold from before
    ADR 0036 without key points or checks keeps its hand-entered scores."""
    record = latest_run(runs_file, "key_points", ",".join(STRATEGY_IDS))
    scaffold = latest_run(runs_file, "scaffold", ",".join(STRATEGY_IDS))
    rule_based = scaffold is not None and scaffold.get("scoring") == SCORING_METHOD
    if not checks_file.exists():
        if record is not None:  # a rule-based run: its scores must come from the checks
            raise ValueError(
                f"the key points are frozen ({runs_file}) but {checks_file} is missing; restore it "
                "from git"
            )
        if rule_based:
            raise ValueError(
                f"the scaffold is rule-based ({runs_file}, ADR 0036): freeze the key points and "
                "score every code with the checks on the Scoring page"
            )
        return
    if record is None:
        raise ValueError(f"{checks_file} exists but the key points are not frozen ({runs_file})")
    items = SCORING_ITEMS_FILE.name
    if scaffold is None or record["outputs_sha256"].get(items) != scaffold["outputs_sha256"].get(
        items
    ):
        raise ValueError(
            f"the key points were frozen for an earlier scaffold ({runs_file}); freeze them again "
            "and score the new answers"
        )
    frozen = record["outputs_sha256"].get(key_points_file.name)
    if not key_points_file.exists() or sha256_of(key_points_file) != frozen:
        raise ValueError(
            f"{key_points_file} differs from the frozen key points; restore it from git"
        )
    try:
        points = rules.key_points(read_csv(key_points_file, rules.KEY_POINTS_HEADER))
    except ValueError as error:
        raise ValueError(f"{key_points_file}: {error}") from error
    counts = {qid: len(texts) for qid, texts in points.items()}
    sheet = read_csv(sheet_file, SHEET_HEADER)
    check_rows = read_csv(checks_file, rules.CHECKS_HEADER)
    order = [r["code"] for r in sheet]
    seen: set[str] = set()
    for code in (r["code"] for r in check_rows):
        if code in seen:
            raise ValueError(f"{checks_file}: {code} appears more than once")
        if code not in order:
            raise ValueError(f"{checks_file}: {code} is not in {sheet_file}")
        seen.add(code)
    if [r["code"] for r in check_rows] != [c for c in order if c in seen]:
        raise ValueError(f"{checks_file}: rows are not in the order of {sheet_file}")
    stored = {r["code"]: r for r in check_rows}
    for row in sheet:
        if row["code"] not in stored:
            raise ValueError(f"{checks_file}: no checks for {row['code']}")
        version, checks = rules.from_row(stored[row["code"]])
        if version != RUBRIC_RULES_VERSION:
            raise ValueError(
                f"{checks_file}: {row['code']} was scored under rules {version}, current rules are "
                f"{RUBRIC_RULES_VERSION}; score it again"
            )
        try:
            rules.validate(checks, counts.get(row["question_id"], 0))
        except ValueError as error:
            raise ValueError(f"{checks_file}: {row['code']}: {error}") from error
        for criterion, value in rules.derive(checks).items():
            if row[criterion].strip() != str(value):
                raise ValueError(
                    f"{sheet_file}: {row['code']} {criterion} is {row[criterion]!r}, its checks "
                    f"give {value}"
                )


def summarise(
    questions_file: Path = QUESTIONS_FILE,
    ground_truth_file: Path = GROUND_TRUTH_FILE,
    sections_file: Path = SECTIONS_FILE,
    documents_file: Path = DOCUMENTS_FILE,
    freeze_file: Path = CATALOGUE_FREEZE_FILE,
    sheet_file: Path = SCORING_SHEET_FILE,
    key_file: Path = SCORING_KEY_FILE,
    checks_file: Path = SCORING_CHECKS_FILE,
    key_points_file: Path = KEY_POINTS_FILE,
    generation_runs_file: Path = GENERATION_RUNS_FILE,
    scores_file: Path = SCORES_FILE,
    limit: int | None = None,
) -> dict[tuple, dict]:
    """Write scores.csv and return the statistics per (group, value, strategy); group "all"
    spans all questions, the other groups are the question type and construction class."""
    questions, _ = catalogue(
        questions_file, ground_truth_file, sections_file, documents_file, freeze_file
    )
    scored = scored_questions(questions, limit, questions_file, ground_truth_file)
    check_derived(sheet_file, checks_file, key_points_file, generation_runs_file)
    rows = unblind(sheet_file, key_file, scored)
    write_csv(scores_file, SCORES_HEADER, rows)
    inputs = [p for p in (sheet_file, key_file, checks_file, key_points_file) if p.exists()]
    append_step_run(
        "summarise", ",".join(STRATEGY_IDS), inputs, [scores_file], generation_runs_file
    )

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
        } | {c: statistics.mean(r[c] for r in group) for c in RUBRIC_CRITERIA}
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


def pilot_paths(set_dir: Path) -> dict[str, Path]:
    """The files of a pilot set (data/pilot/...); answers and run log from generate.py --set."""
    return {
        "answers_file": set_dir / GENERATED_ANSWERS_FILE.name,
        "questions_file": set_dir / QUESTIONS_FILE.name,
        "ground_truth_file": set_dir / GROUND_TRUTH_FILE.name,
        "sheet_file": set_dir / SCORING_SHEET_FILE.name,
        "packet_file": set_dir / SCORING_PACKET_FILE.name,
        "key_file": set_dir / SCORING_KEY_FILE.name,
        "items_file": set_dir / SCORING_ITEMS_FILE.name,
        "scores_file": set_dir / SCORES_FILE.name,
        "checks_file": set_dir / SCORING_CHECKS_FILE.name,
        "key_points_file": set_dir / KEY_POINTS_FILE.name,
        "generation_runs_file": set_dir / PILOT_RUNS_FILE_NAME,
    }


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Blind manual rubric scores (ADR 0013, 0032).")
    p.add_argument("--mode", choices=["scaffold", "summarise"], required=True)
    p.add_argument(
        "--set", type=Path, metavar="DIR", help="a pilot set (e.g. data/pilot/hard) instead"
    )
    p.add_argument("--limit", type=int, metavar="N", help="pilot sets only: the first N questions")
    p.add_argument("--control", action="store_true", help="the control K0 (ADR 0041), after C1-C3")
    args = p.parse_args()
    if args.limit is not None and not args.set:
        p.error("--limit needs --set: every experiment answer is scored (ADR 0032)")
    if args.control:
        import control_k0

        if args.limit is not None:
            p.error("--control takes the questions of scores.csv; --limit does not apply")
        cpaths = control_k0.control_paths(args.set) if args.set else {}
        if args.mode == "scaffold":
            keep = control_k0.SCAFFOLD_KEYS
            count = control_k0.scaffold_control(**{k: v for k, v in cpaths.items() if k in keep})
            sheet = cpaths.get("sheet_file", control_k0.SCORING_SHEET_CONTROL_FILE)
            print(f"{count} K0 answers -> {sheet}")
        else:
            summary_args: dict = {k: v for k, v in cpaths.items() if k != "control_answers_file"}
            if args.set:
                summary_args["closed_book_file"] = None  # the verdicts belong to the main catalogue
            control_k0.print_control_summary(control_k0.summarise_control(**summary_args))
            scores = cpaths.get("control_scores_file", control_k0.SCORES_CONTROL_FILE)
            print(f"K0 scores -> {scores}")
        raise SystemExit(0)
    paths = pilot_paths(args.set) if args.set else {}
    if args.mode == "scaffold":
        scaffold_args = {
            k: v
            for k, v in paths.items()
            if k not in ("scores_file", "checks_file", "key_points_file")
        }
        count = scaffold(**scaffold_args, limit=args.limit)
        packet = paths.get("packet_file", SCORING_PACKET_FILE)
        sheet = paths.get("sheet_file", SCORING_SHEET_FILE)
        print(f"{count} blinded answers -> {packet}, {sheet}")
    else:
        keep = [
            "questions_file",
            "ground_truth_file",
            "sheet_file",
            "key_file",
            "checks_file",
            "key_points_file",
            "generation_runs_file",
            "scores_file",
        ]
        print_summary(summarise(**{k: paths[k] for k in keep if k in paths}, limit=args.limit))
        print(f"unblinded scores -> {paths.get('scores_file', SCORES_FILE)}")
