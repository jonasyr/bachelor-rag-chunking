"""Closed-book screen of the question catalogue (ADR 0038, 0040).

`catalogue.py screen` lets the answer model answer every catalogue question once without any
context (prompt.closed_book_messages); Jonas judges in the editor whether that answer hits the
core point of his reference answer. A question it hits is retrieval-independent and stays marked
in the catalogue. Each row keeps the SHA-256 of the question the answer belongs to and of the
reference answer the verdict belongs to, so an edit reopens exactly what it affects. Reads only
the catalogue, never chunks or retrieval results (ADR 0027).
"""

import hashlib
import math
from pathlib import Path

from atomic_csv import read_csv, write_csv
from config import CLOSED_BOOK_MIN_DEPENDENT_SHARE, CLOSED_BOOK_VERDICTS
from llm_client import Completer, Completion
from prompt import closed_book_messages

SCREEN_HEADER = [
    "question_id", "question_sha256", "reference_sha256", "answer", "model", "core_point",
    "note", "date",
]  # fmt: skip
NOT_SCREENED = "not screened"
NOT_JUDGED = "not judged"


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_screen(path: Path) -> list[dict]:
    """Rows of the screen file; a missing file has none."""
    rows = read_csv(path, SCREEN_HEADER)
    ids = [r["question_id"] for r in rows]
    repeated = sorted({qid for qid in ids if ids.count(qid) > 1})
    if repeated:
        raise ValueError(f"{path}: duplicate question_id {repeated}")
    return rows


def save_screen(path: Path, rows: list[dict]) -> None:
    """Atomic write, rows sorted by question_id (deterministic)."""
    write_csv(path, SCREEN_HEADER, sorted(rows, key=lambda r: r["question_id"]))


def min_dependent(n_questions: int) -> int:
    return math.ceil(CLOSED_BOOK_MIN_DEPENDENT_SHARE * n_questions)


def _reference(truth: dict, question_id: str) -> str:
    return truth.get(question_id, {}).get("expected_answer", "")


def status(row: dict | None, question: str, reference: str) -> str:
    if row is None or row["question_sha256"] != text_sha256(question):
        return NOT_SCREENED
    if not row["core_point"] or row["reference_sha256"] != text_sha256(reference):
        return NOT_JUDGED
    return row["core_point"]


def states(rows: list[dict], questions: list[dict], truth: dict) -> dict[str, str]:
    by_id = {r["question_id"]: r for r in rows}
    return {
        q["question_id"]: status(
            by_id.get(q["question_id"]), q["question"], _reference(truth, q["question_id"])
        )
        for q in questions
    }


def screen(
    questions: list[dict],
    truth: dict,
    completer: Completer,
    path: Path,
    done: list[Completion],
) -> None:
    """Answer every question without a current answer; save after each answer.

    Rows of questions no longer in the catalogue are dropped. Every reply, a cut-off or empty one
    included, is appended to `done`, so the caller can log every billed request.
    """
    keep = {q["question_id"] for q in questions}
    rows = {r["question_id"]: r for r in read_screen(path) if r["question_id"] in keep}
    save_screen(path, list(rows.values()))
    for q in questions:
        qid = q["question_id"]
        if status(rows.get(qid), q["question"], _reference(truth, qid)) != NOT_SCREENED:
            continue
        reply = completer(closed_book_messages(q["question"]))
        done.append(reply)  # billed even if unusable, so the run record counts it
        if reply.finish_reason != "stop" or not reply.text.strip():
            raise RuntimeError(
                f"{qid}: the answer ended with finish_reason={reply.finish_reason!r} or is empty; "
                "the answers before it are saved (ADR 0040)"
            )
        rows[qid] = dict.fromkeys(SCREEN_HEADER, "") | {
            "question_id": qid,
            "question_sha256": text_sha256(q["question"]),
            "answer": reply.text.strip(),
            "model": reply.model,
        }
        save_screen(path, list(rows.values()))


def judge(
    path: Path,
    question_id: str,
    question: str,
    reference: str,
    verdict: str,
    note: str,
    today: str,
) -> dict:
    """Record Jonas' verdict for the current question text and reference answer."""
    if verdict not in CLOSED_BOOK_VERDICTS or not verdict:
        raise ValueError("the verdict must be hit or miss")
    rows = read_screen(path)
    row = next((r for r in rows if r["question_id"] == question_id), None)
    if row is None:
        raise ValueError(f"{question_id} is not screened; run `catalogue.py screen`")
    if row["question_sha256"] != text_sha256(question):
        raise ValueError(f"{question_id} changed since it was screened; run `catalogue.py screen`")
    row.update(
        core_point=verdict,
        note=note.strip(),
        reference_sha256=text_sha256(reference),
        date=today,
    )
    save_screen(path, rows)
    return row


def counts(rows: list[dict], questions: list[dict], truth: dict) -> dict[str, int]:
    found = list(states(rows, questions, truth).values())
    return {
        "dependent": found.count("miss"),
        "known": found.count("hit"),
        "not_screened": found.count(NOT_SCREENED),
        "not_judged": found.count(NOT_JUDGED),
    }


def findings(
    rows: list[dict], questions: list[dict], truth: dict, n_quota: int
) -> tuple[list[str], list[str]]:
    """Errors (malformed rows) and findings (open work, too many hits) of the screen."""
    known_ids = {q["question_id"] for q in questions}
    errors = []
    for r in rows:
        if r["question_id"] not in known_ids:
            errors.append(f"closed-book row {r['question_id']}: question is not in the catalogue")
        if r["core_point"] not in CLOSED_BOOK_VERDICTS:
            errors.append(
                f"closed-book row {r['question_id']}: unknown core_point {r['core_point']!r}"
            )
    found = states(rows, questions, truth)
    result = []
    unscreened = [qid for qid, s in found.items() if s == NOT_SCREENED]
    if unscreened:
        result.append(
            f"closed-book: not screened {', '.join(unscreened)}; run `catalogue.py screen` "
            "(ADR 0040)"
        )
    unjudged = [qid for qid, s in found.items() if s == NOT_JUDGED]
    if unjudged:
        result.append(
            f"closed-book: not judged {', '.join(unjudged)}; judge it in the editor tab Closed-book"
        )
    hits = sum(1 for s in found.values() if s == "hit")
    allowed = n_quota - min_dependent(n_quota)
    if hits > allowed:
        result.append(
            f"closed-book: {hits} questions hit without context, at most {allowed} of {n_quota} "
            "(ADR 0038)"
        )
    return errors, result


def summary(c: dict[str, int], n_quota: int) -> str:
    return (
        f"Closed-book: {c['dependent']} retrieval-dependent (at least {min_dependent(n_quota)}), "
        f"{c['known']} known, {c['not_screened']} not screened, {c['not_judged']} not judged"
    )
