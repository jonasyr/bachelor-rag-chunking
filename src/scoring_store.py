"""Blind scoring in the app (ADR 0032, 0034).

Reads a set's blind item file (scoring_items.jsonl from evaluate_answers.py --mode scaffold)
and its scoring sheet, and writes the sheet; it never opens the key, so nothing here can show
which strategy an answer comes from. Once scores.csv exists the scores were unblinded and the
sheet is read-only. Paths are module globals from config, read at call time, so the page and
its tests share them.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from markdown_it import MarkdownIt

from atomic_csv import read_csv, write_csv
from config import (
    PILOT_DIR,
    RUBRIC_CRITERIA,
    RUBRIC_MAX_SCORE,
    SCORES_FILE,
    SCORING_ITEMS_FILE,
    SCORING_SHEET_FILE,
)
from evaluate_answers import SHEET_HEADER

TEXT_MARKDOWN = MarkdownIt("commonmark", {"html": False}).enable("table")  # model text: no raw HTML


@dataclass(frozen=True)
class ScoringSet:
    name: str
    items_file: Path
    sheet_file: Path
    scores_file: Path


def scoring_sets() -> list[ScoringSet]:
    """The main run and every pilot folder that holds an item file."""
    sets = []
    if SCORING_ITEMS_FILE.exists():
        sets.append(
            ScoringSet("Main catalogue", SCORING_ITEMS_FILE, SCORING_SHEET_FILE, SCORES_FILE)
        )
    for items in sorted(PILOT_DIR.rglob(SCORING_ITEMS_FILE.name)):
        folder = items.parent
        rel = folder.relative_to(PILOT_DIR).as_posix()
        name = "Pilot" if rel == "." else f"Pilot: {rel}"
        sets.append(
            ScoringSet(name, items, folder / SCORING_SHEET_FILE.name, folder / SCORES_FILE.name)
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
            f"{s.items_file} does not match {s.sheet_file}; move sheet and key away and run "
            "src/evaluate_answers.py --mode scaffold again"
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


def is_read_only(s: ScoringSet) -> bool:
    return s.scores_file.exists()


def save_score(s: ScoringSet, code: str, values: dict[str, int], notes: str) -> None:
    """Rewrite the sheet atomically with only this code's row changed."""
    if is_read_only(s):
        raise PermissionError(f"{s.scores_file} exists: the scores were unblinded, read-only")
    if sorted(values) != sorted(RUBRIC_CRITERIA):
        raise ValueError(f"values must cover exactly the criteria {RUBRIC_CRITERIA}")
    for criterion, value in values.items():
        if type(value) is not int or not 0 <= value <= RUBRIC_MAX_SCORE:
            raise ValueError(f"{criterion} must be an integer 0-{RUBRIC_MAX_SCORE}, got {value!r}")
    rows = _sheet(s)
    row = next((r for r in rows if r["code"] == code), None)
    if row is None:
        raise ValueError(f"unknown code {code} in {s.sheet_file}")
    row.update({c: str(v) for c, v in values.items()} | {"notes": notes})
    write_csv(s.sheet_file, SHEET_HEADER, rows)


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
