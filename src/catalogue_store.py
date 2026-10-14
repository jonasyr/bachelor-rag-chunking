"""Reads and writes the catalogue for the editor (ADR 0029, 0031).

Only the catalogue files and the corpus; never chunks, vectors or retrieval results (ADR 0027).
Paths are module globals from config, read at call time, so the editor and its tests share them.
Every write is refused once the freeze record exists (ADR 0030).
"""

import csv
import html
import re

from catalogue import Corpus, same_word
from catalogue_plan import mark_used, read_plan, save_plan, slot_row
from catalogue_review import decide, read_review
from config import (
    CATALOGUE_FREEZE_FILE,
    CATALOGUE_PLAN_FILE,
    CATALOGUE_REVIEW_FILE,
    DOCUMENTS_FILE,
    GROUND_TRUTH_FILE,
    ID_SEPARATOR,
    PILOT_DIR,
    QUESTION_TYPES,
    QUESTIONS_FILE,
    SECTIONS_FILE,
)
from retrieve import GROUND_TRUTH_HEADER, QUESTIONS_HEADER

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _read(path, header: list[str]) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames and list(reader.fieldnames) != header:
            raise ValueError(f"{path} has columns {reader.fieldnames}, expected {header}")
        return [dict(r) for r in reader]


def _write(path, header: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: r["question_id"]))


def load_catalogue() -> tuple[list[dict], dict[str, dict]]:
    """Questions (sorted by ID) and ground truth by question ID; empty files are fine."""
    questions = sorted(_read(QUESTIONS_FILE, QUESTIONS_HEADER), key=lambda q: q["question_id"])
    truth = {r["question_id"]: r for r in _read(GROUND_TRUTH_FILE, GROUND_TRUTH_HEADER)}
    return questions, truth


def next_question_id(questions: list[dict]) -> str:
    numbers = [int(q["question_id"][1:]) for q in questions if q["question_id"][1:].isdigit()]
    return f"Q{max(numbers, default=0) + 1:03d}"


def is_frozen() -> bool:
    return CATALOGUE_FREEZE_FILE.exists()


def _refuse_if_frozen() -> None:
    if is_frozen():
        raise PermissionError("the catalogue is frozen (ADR 0030); it can no longer be edited")


def save_question(
    corpus: Corpus,
    slot_id: str,
    question: str,
    qtype: str,
    answer: str,
    notes: str,
    section_ids: list[str],
    question_id: str | None = None,
) -> str:
    """Insert or update the question of a slot; the slot's starting section always comes first."""
    _refuse_if_frozen()
    question, answer, notes = question.strip(), answer.strip(), notes.strip()
    if not question:
        raise ValueError("question is empty")
    if not answer:
        raise ValueError("reference answer is empty")
    if qtype not in QUESTION_TYPES:
        raise ValueError(f"unknown type {qtype!r}; allowed {list(QUESTION_TYPES)}")
    plan = read_plan(CATALOGUE_PLAN_FILE)
    row = slot_row(plan, slot_id)
    if question_id:
        owner = next(
            (r for r in plan if r["status"] == "used" and r["question_id"] == question_id), None
        )
        if owner is not None and owner["slot_id"] != slot_id:
            raise ValueError(f"{question_id} belongs to slot {owner['slot_id']}, not {slot_id}")
    unknown = [s for s in section_ids if s not in corpus.by_id]
    if unknown:
        raise ValueError(f"unknown section IDs {unknown}")
    ids = list(dict.fromkeys([row["section_id"], *section_ids]))
    docs = list(dict.fromkeys(corpus.by_id[s]["doc_id"] for s in ids))
    questions, truth = load_catalogue()
    qid = question_id or (
        row["question_id"] if row["status"] == "used" else next_question_id(questions)
    )
    mark_used(plan, slot_id, qid)
    questions = [q for q in questions if q["question_id"] != qid] + [
        {
            "question_id": qid,
            "question": question,
            "type": qtype,
            "difficulty": row["class"],
            "notes": notes,
        }
    ]
    truth[qid] = {
        "question_id": qid,
        "expected_answer": answer,
        "relevant_doc_ids": ID_SEPARATOR.join(docs),
        "relevant_section_ids": ID_SEPARATOR.join(ids),
    }
    _write(QUESTIONS_FILE, QUESTIONS_HEADER, questions)
    _write(GROUND_TRUTH_FILE, GROUND_TRUTH_HEADER, list(truth.values()))
    save_plan(CATALOGUE_PLAN_FILE, plan)
    return qid


def accept_suggestion(corpus: Corpus, index: int, reason: str, today: str) -> dict:
    """Accept a review suggestion; a missing_section is added to the question's annotation."""
    _refuse_if_frozen()
    row = read_review(CATALOGUE_REVIEW_FILE)[index]
    if row["kind"] == "missing_section" and row["decision"] == "open":
        questions, truth = load_catalogue()
        entry = truth[row["question_id"]]
        ids = list(
            dict.fromkeys([*entry["relevant_section_ids"].split(ID_SEPARATOR), row["section_id"]])
        )
        entry["relevant_section_ids"] = ID_SEPARATOR.join(ids)
        entry["relevant_doc_ids"] = ID_SEPARATOR.join(
            dict.fromkeys(corpus.by_id[s]["doc_id"] for s in ids)
        )
        _write(GROUND_TRUTH_FILE, GROUND_TRUTH_HEADER, list(truth.values()))
    return decide(CATALOGUE_REVIEW_FILE, index, "accepted", reason, today)


def reject_suggestion(index: int, reason: str, today: str) -> dict:
    _refuse_if_frozen()
    return decide(CATALOGUE_REVIEW_FILE, index, "rejected", reason, today)


def highlight(text: str, words: list[str]) -> str:
    """HTML-escaped text; tokens matching any of `words` (ADR 0029 word rule) are marked."""
    out, last = [], 0
    for match in TOKEN_RE.finditer(text):
        out.append(html.escape(text[last : match.start()]))
        token = match.group()
        if any(same_word(token.lower(), w) for w in words):
            out.append(f'<mark class="hl">{html.escape(token)}</mark>')
        else:
            out.append(html.escape(token))
        last = match.end()
    out.append(html.escape(text[last:]))
    return "".join(out)
