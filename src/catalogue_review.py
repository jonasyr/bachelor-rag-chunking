"""AI review log of the question catalogue (ADR 0031).

After each block, Claude appends suggestions with decision `open` (missed sections, wording,
facts, class), reading only the questions, the annotation and the corpus text (ADR 0027). Jonas
accepts or rejects each one with a reason; the freeze refuses while any row is open. The
summary line goes into the AI disclosure of the thesis.
"""

import csv
from pathlib import Path

from config import CATALOGUE_REVIEW_DECISIONS, CATALOGUE_REVIEW_FILE, CATALOGUE_REVIEW_KINDS

REVIEW_HEADER = [
    "round", "question_id", "kind", "suggestion", "section_id", "decision", "reason", "date",
]  # fmt: skip


def read_review(path: Path = CATALOGUE_REVIEW_FILE) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        records = [r for r in csv.reader(f) if r]
    if not records or records[0] != REVIEW_HEADER:
        found = records[0] if records else []
        raise ValueError(f"{path} has columns {found}, expected {REVIEW_HEADER}")
    for number, record in enumerate(records[1:], start=2):
        if len(record) != len(REVIEW_HEADER):
            raise ValueError(f"{path}: row {number} has {len(record)} fields")
    return [dict(zip(REVIEW_HEADER, r, strict=True)) for r in records[1:]]


def save_review(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_HEADER, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def ensure_review_file(path: Path = CATALOGUE_REVIEW_FILE) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        save_review(path, [])


def review_errors(rows: list[dict], question_ids: set[str], section_ids: set[str]) -> list[str]:
    errors = []
    for number, r in enumerate(rows, start=2):
        where = f"review row {number}"
        if not r["round"].isdigit():
            errors.append(f"{where}: round {r['round']!r} is not a number")
        if r["kind"] not in CATALOGUE_REVIEW_KINDS:
            errors.append(f"{where}: unknown kind {r['kind']!r}")
        if r["decision"] not in CATALOGUE_REVIEW_DECISIONS:
            errors.append(f"{where}: unknown decision {r['decision']!r}")
        if r["question_id"] not in question_ids:
            errors.append(f"{where}: question {r['question_id']} is not in the catalogue")
        if r["kind"] == "missing_section" and r["section_id"] not in section_ids:
            errors.append(
                f"{where}: missing_section needs a known section_id, got {r['section_id']!r}"
            )
        if r["kind"] != "missing_section" and r["section_id"]:
            errors.append(f"{where}: section_id only belongs to missing_section")
        if r["decision"] == "rejected" and not r["reason"].strip():
            errors.append(f"{where}: a rejected suggestion needs a reason")
    return errors


def decide(path: Path, index: int, decision: str, reason: str, today: str) -> dict:
    """Record Jonas' decision on the open suggestion at `index` (0-based, file order)."""
    if decision not in CATALOGUE_REVIEW_DECISIONS or decision == "open":
        raise ValueError("decision must be accepted or rejected")
    if decision == "rejected" and not reason.strip():
        raise ValueError("a rejected suggestion needs a reason")
    rows = read_review(path)
    row = rows[index]
    if row["decision"] != "open":
        raise ValueError(f"suggestion {index + 1} is already decided ({row['decision']})")
    row.update(decision=decision, reason=reason.strip(), date=today)
    save_review(path, rows)
    return row


def review_summary(rows: list[dict]) -> str:
    accepted = [r for r in rows if r["decision"] == "accepted"]
    kinds = ", ".join(
        f"{k} {n}"
        for k in CATALOGUE_REVIEW_KINDS
        if (n := sum(1 for r in accepted if r["kind"] == k))
    )
    rejected = sum(1 for r in rows if r["decision"] == "rejected")
    still_open = sum(1 for r in rows if r["decision"] == "open")
    return (
        f"AI review: {len(rows)} suggestions, {len(accepted)} accepted"
        + (f" ({kinds})" if kinds else "")
        + f", {rejected} rejected, {still_open} open"
    )
