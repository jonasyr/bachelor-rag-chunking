"""Editor aids for writing a question (ADR 0049): what else covers the section, and what still
blocks saving. They never set a question, answer, type or relevance judgement themselves.
"""

import re

from catalogue import Corpus, nested, shared_passages
from config import QUESTION_TYPES


def also_covered(
    corpus: Corpus, seed: dict, overlap: dict[str, list[tuple[str, str]]]
) -> list[dict]:
    """Sections with the same text (mechanical, longest first) or content (overlap list).

    One row per section: `section`, `kind` ("same text" or "related"), `detail` (shared words or
    the note) and `note` (the overlap note, "" if none).
    """
    notes = dict(overlap.get(seed["section_id"], []))
    rows = [
        {
            "section": s,
            "kind": "same text",
            "detail": excerpt,
            "note": notes.get(s["section_id"], ""),
        }
        for s, excerpt in shared_passages(corpus, seed["section_id"])
    ]
    seen = {r["section"]["section_id"] for r in rows}
    for other, note in overlap.get(seed["section_id"], []):
        section = corpus.by_id.get(other)
        if section is None or other in seen or nested(seed, section):
            continue
        rows.append({"section": section, "kind": "related", "detail": note, "note": note})
        seen.add(other)
    return rows


def type_quota_left(questions: list[dict], qtype: str, qid: str | None) -> int:
    """Open places of a type; the question being edited does not count against it."""
    used = sum(1 for q in questions if q["type"] == qtype and q["question_id"] != qid)
    return QUESTION_TYPES[qtype] - used


def save_blocker(
    question: str,
    answer: str,
    qtype: str | None,
    items: list[tuple[bool, str]],
    questions: list[dict],
    qid: str | None,
) -> str | None:
    """The first reason the question cannot be saved yet, or None."""
    if not question.strip():
        return "Write a question"
    if not answer.strip():
        return "Write a reference answer"
    if qtype is None:
        return "Choose a type"
    problem = next((text for ok, text in items if not ok), None)
    if problem:
        return f"Not met: {problem}"
    left = type_quota_left(questions, qtype, qid)
    if left <= 0:
        used = QUESTION_TYPES[qtype] - left
        return f"The {qtype} quota is full ({used} of {QUESTION_TYPES[qtype]} written)"
    return None


def plain_excerpt(text: str) -> str:
    """A shared passage made readable: link text without targets, table cells joined by "·"."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r":?-{3,}:?", "", text)
    cells = [c.strip() for c in text.split("|")]
    return " · ".join(c for c in cells if c)
