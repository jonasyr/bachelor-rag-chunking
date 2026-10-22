"""Blind scoring in the app (ADR 0032, 0034, 0035).

Reads a set's blind item file (scoring_items.jsonl from evaluate_answers.py --mode scaffold)
and its scoring sheet, and writes the sheet; it never opens the key, so nothing here can show
which strategy an answer comes from. Once scores.csv exists the scores were unblinded and the
sheet is read-only. Key points (ADR 0035) are written per question, then frozen with a run
record; every score save checks that the frozen file is unchanged. Paths are module globals
from config, read at call time, so the page and its tests share them.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from markdown_it import MarkdownIt

import scoring_rules as rules
from atomic_csv import read_csv, write_csv
from config import (
    CONTROL_CRITERIA,
    GENERATION_RUNS_FILE,
    KEY_POINTS_FILE,
    KEY_POINTS_MAX,
    PILOT_DIR,
    PILOT_RUNS_FILE_NAME,
    RUBRIC_CRITERIA,
    RUBRIC_MAX_SCORE,
    SCORES_CONTROL_FILE,
    SCORES_FILE,
    SCORING_CHECKS_CONTROL_FILE,
    SCORING_CHECKS_FILE,
    SCORING_ITEMS_CONTROL_FILE,
    SCORING_ITEMS_FILE,
    SCORING_SHEET_CONTROL_FILE,
    SCORING_SHEET_FILE,
    SECOND_RATER_DIR,
    SECOND_RATER_DIR_NAME,
    SECOND_RATER_ENV,
    SECOND_RATER_PSEUDONYM,
    STRATEGY_IDS,
)
from control_k0 import CONTROL_SHEET_HEADER
from evaluate_answers import SHEET_HEADER
from run_log import append_key_points_run, latest_run, sha256_of

TEXT_MARKDOWN = MarkdownIt("commonmark", {"html": False}).enable("table")  # model text: no raw HTML


@dataclass(frozen=True)
class ScoringSet:
    name: str
    items_file: Path
    sheet_file: Path
    scores_file: Path
    key_points_file: Path
    checks_file: Path
    runs_file: Path
    control: bool = False  # the control K0 (ADR 0041): K0 rules, four criteria
    freeze_items_file: Path | None = None  # K0: the C1-C3 item file its key points were frozen on
    rater: bool = False  # the second rater's set (ADR 0046): frozen key points, no K0 set


def criteria(s: ScoringSet) -> list[str]:
    return list(CONTROL_CRITERIA) if s.control else list(RUBRIC_CRITERIA)


def _sheet_header(s: ScoringSet) -> list[str]:
    return CONTROL_SHEET_HEADER if s.control else SHEET_HEADER


def _control_set(base: ScoringSet) -> ScoringSet | None:
    """The K0 set next to a C1-C3 set (same folder), if its item file exists."""
    folder = base.items_file.parent
    items = folder / SCORING_ITEMS_CONTROL_FILE.name
    if not items.exists():
        return None
    return ScoringSet(
        f"{base.name}: control K0",
        items,
        folder / SCORING_SHEET_CONTROL_FILE.name,
        folder / SCORES_CONTROL_FILE.name,
        base.key_points_file,
        folder / SCORING_CHECKS_CONTROL_FILE.name,
        base.runs_file,
        control=True,
        freeze_items_file=base.items_file,
    )


def rater_mode() -> str | None:
    """The rater named by the environment (config.SECOND_RATER_ENV), if any."""
    return os.environ.get(SECOND_RATER_ENV)


def _rater_set(name: str, folder: Path) -> ScoringSet:
    return ScoringSet(
        name,
        folder / SCORING_ITEMS_FILE.name,
        folder / SCORING_SHEET_FILE.name,
        folder / SCORES_FILE.name,
        folder / KEY_POINTS_FILE.name,
        folder / SCORING_CHECKS_FILE.name,
        folder / PILOT_RUNS_FILE_NAME,
        rater=True,
    )


def rater_sets() -> list[ScoringSet]:
    """The second rater's sets: the main one and one per pilot folder `second_rater/`."""
    sets = []
    if (SECOND_RATER_DIR / SCORING_ITEMS_FILE.name).exists():
        sets.append(_rater_set("Second rater", SECOND_RATER_DIR))
    for items in sorted(PILOT_DIR.rglob(SCORING_ITEMS_FILE.name)):
        if items.parent.name == SECOND_RATER_DIR_NAME:
            rel = items.parent.parent.relative_to(PILOT_DIR).as_posix()
            name = "Pilot: second rater" if rel == "." else f"Pilot: {rel}: second rater"
            sets.append(_rater_set(name, items.parent))
    return sets


def scoring_sets() -> list[ScoringSet]:
    """The main run and every pilot folder that holds an item file, each followed by its K0 set
    (ADR 0041) when that exists, then the second rater's sets. In R2 mode (`rater_mode`) only
    the second rater's sets, so nothing else is reachable."""
    if rater_mode() == SECOND_RATER_PSEUDONYM:
        return rater_sets()
    sets = []
    if SCORING_ITEMS_FILE.exists():
        sets.append(
            ScoringSet(
                "Main catalogue",
                SCORING_ITEMS_FILE,
                SCORING_SHEET_FILE,
                SCORES_FILE,
                KEY_POINTS_FILE,
                SCORING_CHECKS_FILE,
                GENERATION_RUNS_FILE,
            )
        )
    for items in sorted(PILOT_DIR.rglob(SCORING_ITEMS_FILE.name)):
        folder = items.parent
        if folder.name == SECOND_RATER_DIR_NAME:
            continue  # listed below as a second rater set
        rel = folder.relative_to(PILOT_DIR).as_posix()
        name = "Pilot" if rel == "." else f"Pilot: {rel}"
        sets.append(
            ScoringSet(
                name,
                items,
                folder / SCORING_SHEET_FILE.name,
                folder / SCORES_FILE.name,
                folder / KEY_POINTS_FILE.name,
                folder / SCORING_CHECKS_FILE.name,
                folder / PILOT_RUNS_FILE_NAME,
            )
        )
    with_control = []
    for s in sets:
        with_control.append(s)
        control = _control_set(s)
        if control is not None:
            with_control.append(control)
    return with_control + rater_sets()


def _sheet(s: ScoringSet) -> list[dict]:
    if not s.sheet_file.exists():
        raise FileNotFoundError(
            f"{s.sheet_file} not found; run src/evaluate_answers.py --mode scaffold first"
        )
    return read_csv(s.sheet_file, _sheet_header(s))


def load_items(s: ScoringSet) -> list[dict]:
    """The items in packet order; refused unless they match the sheet code for code."""
    lines = s.items_file.read_text(encoding="utf-8").splitlines()
    items = [json.loads(line) for line in lines if line.strip()]
    if [i["code"] for i in items] != [r["code"] for r in _sheet(s)]:
        raise ValueError(
            f"{s.items_file} does not match {s.sheet_file}; run src/evaluate_answers.py --mode "
            "scaffold again with the same --set and --limit (it rewrites the item file and keeps "
            "the sheet)"
        )
    return items


def _value(row: dict, criterion: str, path: Path) -> int | None:
    text = row[criterion].strip()
    if not text:
        return None
    if not text.isdigit() or int(text) > RUBRIC_MAX_SCORE:
        raise ValueError(f"{path}: {row['code']} {criterion} is {text!r}, not 0-{RUBRIC_MAX_SCORE}")
    return int(text)


def load_scores(s: ScoringSet) -> dict[str, dict]:
    """Per code the criterion values (None while empty) and the notes."""
    return {
        r["code"]: {
            "values": {c: _value(r, c, s.sheet_file) for c in criteria(s)},
            "notes": r["notes"],
        }
        for r in _sheet(s)
    }


KEY_POINTS_HEADER = rules.KEY_POINTS_HEADER
STRATEGY = ",".join(STRATEGY_IDS)


def questions(items: list[dict]) -> list[dict]:
    """Question and reference answer per question, in packet order; never an answer."""
    seen: dict[str, dict] = {}
    for item in items:
        seen.setdefault(
            item["question_id"],
            {k: item[k] for k in ("question_id", "question", "reference_answer")},
        )
    return list(seen.values())


def load_key_points(s: ScoringSet) -> dict[str, list[str]]:
    """Key points per question; a malformed file (numbering, count, empty text) is refused."""
    try:
        return rules.key_points(read_csv(s.key_points_file, KEY_POINTS_HEADER))
    except ValueError as error:
        raise ValueError(f"{s.key_points_file}: {error}") from error


def _freeze(s: ScoringSet) -> dict | None:
    """The latest key-point freeze made on the current scaffold (same item file), or None."""
    record = latest_run(s.runs_file, "key_points", STRATEGY)
    items = s.freeze_items_file or s.items_file  # K0: frozen on its C1-C3 set
    if record is None or not items.exists():
        return None
    if record["outputs_sha256"].get(items.name) != sha256_of(items):
        return None  # frozen for an earlier scaffold of this set
    return record


def is_frozen(s: ScoringSet) -> bool:
    return _freeze(s) is not None


def save_key_points(s: ScoringSet, items: list[dict], question_id: str, points: list[str]) -> None:
    """Replace one question's key points (point 1 = core point); refused after the freeze."""
    if s.control:
        raise PermissionError(f"{s.name} uses the frozen key points of its C1-C3 set")
    if is_frozen(s):
        raise PermissionError(f"the key points of {s.name} are frozen")
    known = {q["question_id"] for q in questions(items)}
    if question_id not in known:
        raise ValueError(f"unknown question {question_id}")
    if not 1 <= len(points) <= KEY_POINTS_MAX:
        raise ValueError(f"a question has 1 to {KEY_POINTS_MAX} key points, got {len(points)}")
    for text in points:
        if not text.strip():
            raise ValueError("a key point is empty")
        if "\n" in text or "\r" in text:
            raise ValueError("a key point is one line")
    # points of questions no longer in the scaffold (fewer questions after a new scaffold) go
    current = {q: t for q, t in load_key_points(s).items() if q in known}
    current[question_id] = [t.strip() for t in points]
    rows = [
        {"question_id": qid, "point": str(n), "text": text}
        for qid in sorted(current)
        for n, text in enumerate(current[qid], start=1)
    ]
    write_csv(s.key_points_file, KEY_POINTS_HEADER, rows)


def freeze_key_points(s: ScoringSet, items: list[dict]) -> None:
    """Record the checksums of the key points and of the scaffold they belong to (the item
    file) once every question has some (ADR 0035)."""
    if s.control:
        raise PermissionError(f"{s.name} uses the frozen key points of its C1-C3 set")
    if is_frozen(s):
        raise PermissionError(f"the key points of {s.name} are frozen already")
    points = load_key_points(s)
    missing = [q["question_id"] for q in questions(items) if q["question_id"] not in points]
    if missing:
        raise ValueError(f"no key points yet for {', '.join(missing)}")
    known = {q["question_id"] for q in questions(items)}
    stray = sorted(set(points) - known)
    if stray:
        raise ValueError(
            f"key points for questions outside {s.name}: {', '.join(stray)}; save the key points "
            "of any question once to drop them"
        )
    if s.checks_file.exists():
        raise ValueError(
            f"{s.checks_file} holds checks of an earlier scaffold; move it aside before freezing"
        )
    items_sha = sha256_of(s.items_file)
    scaffold = latest_run(s.runs_file, "scaffold", STRATEGY)
    if scaffold is None or scaffold["outputs_sha256"].get(s.items_file.name) != items_sha:
        raise ValueError(
            f"{s.items_file} differs from the latest scaffold record in {s.runs_file}; run "
            "src/evaluate_answers.py --mode scaffold again"
        )
    outputs = {s.key_points_file.name: sha256_of(s.key_points_file), s.items_file.name: items_sha}
    append_key_points_run(STRATEGY, outputs, s.runs_file)


def require_frozen_key_points(s: ScoringSet) -> None:
    record = _freeze(s)
    if record is None:
        raise PermissionError(f"the key points of {s.name} are not frozen yet")
    frozen = record["outputs_sha256"].get(s.key_points_file.name)
    if not s.key_points_file.exists() or sha256_of(s.key_points_file) != frozen:
        raise PermissionError(
            f"{s.key_points_file} differs from the frozen key points; restore it from git"
        )


def is_read_only(s: ScoringSet) -> bool:
    return s.scores_file.exists()


def save_score(s: ScoringSet, code: str, checks: dict, notes: str) -> dict[str, int]:
    """Validate the checks, derive the five scores (ADR 0035) and write checks file and sheet
    atomically with only this code's rows changed; returns the derived values."""
    if is_read_only(s):
        raise PermissionError(f"{s.scores_file} exists: the scores were unblinded, read-only")
    require_frozen_key_points(s)
    rows = _sheet(s)
    row = next((r for r in rows if r["code"] == code), None)
    if row is None:
        raise ValueError(f"unknown code {code} in {s.sheet_file}")
    n_points = len(load_key_points(s).get(row["question_id"], []))
    rules.validate(checks, n_points, control=s.control)
    values = rules.derive_control(checks) if s.control else rules.derive(checks)
    order = [r["code"] for r in rows]
    stored: dict[str, dict] = {}
    header = rules.checks_header(s.control)
    for r in read_csv(s.checks_file, header):
        if r["code"] in stored:
            raise ValueError(f"{s.checks_file}: {r['code']} appears more than once")
        if r["code"] not in order:
            raise ValueError(f"{s.checks_file}: {r['code']} is not in {s.sheet_file}")
        stored[r["code"]] = r
    stored[code] = rules.to_row(code, checks, control=s.control)
    write_csv(
        s.checks_file,
        header,
        sorted(stored.values(), key=lambda r: order.index(r["code"])),
    )
    row.update({c: str(v) for c, v in values.items()} | {"notes": notes})
    write_csv(s.sheet_file, _sheet_header(s), rows)
    return values


def load_checks(s: ScoringSet) -> dict[str, dict]:
    """The stored checks of every scored code."""
    header = rules.checks_header(s.control)
    return {
        r["code"]: rules.from_row(r, control=s.control)[1] for r in read_csv(s.checks_file, header)
    }


def is_scored(entry: dict) -> bool:
    return all(v is not None for v in entry["values"].values())


def progress(items: list[dict], scores: dict[str, dict]) -> tuple[int, int]:
    return sum(is_scored(scores[i["code"]]) for i in items), len(items)


def by_question(items: list[dict], scores: dict[str, dict]) -> list[tuple[str, int, int]]:
    """(question_id, scored, answers) in the order the questions first appear."""
    counts: dict[str, list[int]] = {}
    for item in items:
        done_total = counts.setdefault(item["question_id"], [0, 0])
        done_total[0] += is_scored(scores[item["code"]])
        done_total[1] += 1
    return [(qid, done, total) for qid, (done, total) in counts.items()]


def first_unscored(codes: list[str], scores: dict[str, dict]) -> str:
    return next((c for c in codes if not is_scored(scores[c])), codes[0])


def next_code(codes: list[str], current: str, scores: dict[str, dict]) -> str:
    """The next unscored code after `current` (wrapping); with everything scored the
    following code, or `current` itself at the end."""
    start = codes.index(current)
    for code in codes[start + 1 :] + codes[:start]:
        if not is_scored(scores[code]):
            return code
    return codes[min(start + 1, len(codes) - 1)]


def text_html(text: str) -> str:
    """Model or corpus text as HTML for a formatted page; raw HTML stays visible as text."""
    return TEXT_MARKDOWN.render(text)
