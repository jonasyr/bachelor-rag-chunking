"""Blind scoring in the app (ADR 0032, 0034, 0035).

Reads a set's blind item file (scoring_items.jsonl from evaluate_answers.py --mode scaffold)
and its scoring sheet, and writes the sheet; it never opens the key, so nothing here can show
which strategy an answer comes from. Once scores.csv exists the scores were unblinded and the
sheet is read-only. Key points (ADR 0035) are written per question, then frozen with a run
record; every score save checks that the frozen file is unchanged. Paths are module globals
from config, read at call time, so the page and its tests share them.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from markdown_it import MarkdownIt

import scoring_rules as rules
from atomic_csv import read_csv, write_csv
from config import (
    GENERATION_RUNS_FILE,
    KEY_POINTS_FILE,
    KEY_POINTS_MAX,
    PILOT_DIR,
    PILOT_RUNS_FILE_NAME,
    RUBRIC_CRITERIA,
    RUBRIC_MAX_SCORE,
    SCORES_FILE,
    SCORING_CHECKS_FILE,
    SCORING_ITEMS_FILE,
    SCORING_SHEET_FILE,
    STRATEGY_IDS,
)
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


def scoring_sets() -> list[ScoringSet]:
    """The main run and every pilot folder that holds an item file."""
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
    return sets


def _sheet(s: ScoringSet) -> list[dict]:
    if not s.sheet_file.exists():
        raise FileNotFoundError(
            f"{s.sheet_file} not found; run src/evaluate_answers.py --mode scaffold first"
        )
    return read_csv(s.sheet_file, SHEET_HEADER)


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
            "values": {c: _value(r, c, s.sheet_file) for c in RUBRIC_CRITERIA},
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
    points: dict[str, list[str]] = {}
    for row in read_csv(s.key_points_file, KEY_POINTS_HEADER):
        points.setdefault(row["question_id"], []).append(row["text"])
    return points


def is_frozen(s: ScoringSet) -> bool:
    return latest_run(s.runs_file, "key_points", STRATEGY) is not None


def save_key_points(s: ScoringSet, items: list[dict], question_id: str, points: list[str]) -> None:
    """Replace one question's key points (point 1 = core point); refused after the freeze."""
    if is_frozen(s):
        raise PermissionError(f"the key points of {s.name} are frozen")
    if question_id not in {q["question_id"] for q in questions(items)}:
        raise ValueError(f"unknown question {question_id}")
    if not 1 <= len(points) <= KEY_POINTS_MAX:
        raise ValueError(f"a question has 1 to {KEY_POINTS_MAX} key points, got {len(points)}")
    for text in points:
        if not text.strip():
            raise ValueError("a key point is empty")
        if "\n" in text or "\r" in text:
            raise ValueError("a key point is one line")
    current = load_key_points(s) | {question_id: [t.strip() for t in points]}
    rows = [
        {"question_id": qid, "point": str(n), "text": text}
        for qid in sorted(current)
        for n, text in enumerate(current[qid], start=1)
    ]
    write_csv(s.key_points_file, KEY_POINTS_HEADER, rows)


def freeze_key_points(s: ScoringSet, items: list[dict]) -> None:
    """Record the checksum of the key points once every question has some (ADR 0035)."""
    if is_frozen(s):
        raise PermissionError(f"the key points of {s.name} are frozen already")
    points = load_key_points(s)
    missing = [q["question_id"] for q in questions(items) if q["question_id"] not in points]
    if missing:
        raise ValueError(f"no key points yet for {', '.join(missing)}")
    sha = sha256_of(s.key_points_file)
    append_key_points_run(STRATEGY, {s.key_points_file.name: sha}, s.runs_file)


def require_frozen_key_points(s: ScoringSet) -> None:
    record = latest_run(s.runs_file, "key_points", STRATEGY)
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
    rules.validate(checks, n_points)
    values = rules.derive(checks)
    stored = {r["code"]: r for r in read_csv(s.checks_file, rules.CHECKS_HEADER)}
    stored[code] = rules.to_row(code, checks)
    order = [r["code"] for r in rows]
    write_csv(
        s.checks_file,
        rules.CHECKS_HEADER,
        sorted(stored.values(), key=lambda r: order.index(r["code"])),
    )
    row.update({c: str(v) for c, v in values.items()} | {"notes": notes})
    write_csv(s.sheet_file, SHEET_HEADER, rows)
    return values


def load_checks(s: ScoringSet) -> dict[str, dict]:
    """The stored checks of every scored code."""
    return {r["code"]: rules.from_row(r)[1] for r in read_csv(s.checks_file, rules.CHECKS_HEADER)}


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
