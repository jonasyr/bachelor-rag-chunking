"""Reads and writes the catalogue for the editor (ADR 0029, 0031).

Only the catalogue files and the corpus; never chunks, vectors or retrieval results (ADR 0027).
Paths are module globals from config, read at call time, so the editor and its tests share them.
Every write is refused once the freeze record exists (ADR 0030).
"""

import html
import re

from atomic_csv import read_csv, write_csv
from catalogue import CAMEL_RE, Corpus, same_word
from catalogue_plan import mark_used, read_plan, save_plan, slot_row
from catalogue_plan import skip_slot as catalogue_skip
from catalogue_review import decide, read_review
from config import (
    CATALOGUE_FREEZE_FILE,
    CATALOGUE_PLAN_FILE,
    CATALOGUE_REVIEW_FILE,
    DOCUMENTS_FILE,
    GROUND_TRUTH_FILE,
    ID_SEPARATOR,
    PILOT_DIR,
    QUESTION_ID_FORMAT,
    QUESTION_ID_PATTERN,
    QUESTION_TYPES,
    QUESTIONS_FILE,
    SECTIONS_FILE,
    VUE_DOCS_SITE_URL,
)
from preprocess import closes_fence, fence_marker
from retrieve import GROUND_TRUTH_HEADER, QUESTIONS_HEADER

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
QUESTION_ID_RE = re.compile(QUESTION_ID_PATTERN)


def _read(path, header: list[str]) -> list[dict]:
    rows = read_csv(path, header)
    ids = [r["question_id"] for r in rows]
    repeated = sorted({qid for qid in ids if ids.count(qid) > 1})
    if repeated:
        raise ValueError(f"{path}: duplicate question_id {repeated}")
    return rows


def write_rows(path, header: list[str], rows: list[dict]) -> None:
    """Atomic write, rows sorted by question_id (deterministic)."""
    write_csv(path, header, sorted(rows, key=lambda r: r["question_id"]))


def load_catalogue() -> tuple[list[dict], dict[str, dict]]:
    """Questions (sorted by ID) and ground truth by question ID; empty files are fine."""
    questions = sorted(_read(QUESTIONS_FILE, QUESTIONS_HEADER), key=lambda q: q["question_id"])
    truth = {r["question_id"]: r for r in _read(GROUND_TRUTH_FILE, GROUND_TRUTH_HEADER)}
    return questions, truth


def next_question_id(questions: list[dict], plan: list[dict] | None = None) -> str:
    """One above the highest ID in the catalogue or in a used plan row, so no ID is reused."""
    ids = [q["question_id"] for q in questions]
    ids += [r["question_id"] for r in plan or [] if r["status"] == "used"]
    numbers = [int(i[1:]) for i in ids if QUESTION_ID_RE.fullmatch(i)]
    return QUESTION_ID_FORMAT.format(max(numbers, default=0) + 1)


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
    if row["section_id"] not in corpus.by_id:
        raise ValueError(
            f"starting section {row['section_id']} of slot {slot_id} is not in sections.jsonl"
        )
    unknown = [s for s in section_ids if s not in corpus.by_id]
    if unknown:
        raise ValueError(f"unknown section IDs {unknown}")
    ids = list(dict.fromkeys([row["section_id"], *section_ids]))
    docs = list(dict.fromkeys(corpus.by_id[s]["doc_id"] for s in ids))
    questions, truth = load_catalogue()
    qid = question_id or (
        row["question_id"] if row["status"] == "used" else next_question_id(questions, plan)
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
    # Plan first: if a later write fails, the slot already names the ID and a retry reuses it.
    save_plan(CATALOGUE_PLAN_FILE, plan)
    write_rows(GROUND_TRUTH_FILE, GROUND_TRUTH_HEADER, list(truth.values()))
    write_rows(QUESTIONS_FILE, QUESTIONS_HEADER, questions)
    return qid


def accept_suggestion(corpus: Corpus, index: int, reason: str, today: str) -> dict:
    """Accept a review suggestion; a missing_section is added to the question's annotation."""
    _refuse_if_frozen()
    row = read_review(CATALOGUE_REVIEW_FILE)[index]
    if row["kind"] == "missing_section" and row["decision"] == "open":
        if row["section_id"] not in corpus.by_id:
            raise ValueError(f"suggested section {row['section_id']} is not in sections.jsonl")
        questions, truth = load_catalogue()
        if row["question_id"] not in truth:
            raise ValueError(f"{row['question_id']} has no ground truth row")
        entry = truth[row["question_id"]]
        ids = list(
            dict.fromkeys([*entry["relevant_section_ids"].split(ID_SEPARATOR), row["section_id"]])
        )
        entry["relevant_section_ids"] = ID_SEPARATOR.join(ids)
        entry["relevant_doc_ids"] = ID_SEPARATOR.join(
            dict.fromkeys(corpus.by_id[s]["doc_id"] for s in ids)
        )
        write_rows(GROUND_TRUTH_FILE, GROUND_TRUTH_HEADER, list(truth.values()))
    return decide(CATALOGUE_REVIEW_FILE, index, "accepted", reason, today)


def skip_slot(corpus: Corpus, slot_id: str, reason: str) -> dict:
    """Skip an open slot (ADR 0031); refused after the freeze."""
    _refuse_if_frozen()
    return catalogue_skip(CATALOGUE_PLAN_FILE, slot_id, reason, corpus, CATALOGUE_FREEZE_FILE)


def reject_suggestion(index: int, reason: str, today: str) -> dict:
    _refuse_if_frozen()
    return decide(CATALOGUE_REVIEW_FILE, index, "rejected", reason, today)


def highlight(text: str, words: list[str]) -> str:
    """HTML-escaped text; tokens matching any of `words` (ADR 0029 word rule) are marked."""
    out, last = [], 0
    for match in TOKEN_RE.finditer(text):
        out.append(html.escape(text[last : match.start()]))
        token = match.group()
        forms = {token.lower(), *CAMEL_RE.sub(" ", token).lower().split()}  # like content_words
        if any(same_word(f, w) for f in forms for w in words):
            out.append(f'<mark class="hl">{html.escape(token)}</mark>')
        else:
            out.append(html.escape(token))
        last = match.end()
    out.append(html.escape(text[last:]))
    return "".join(out)


def segments(text: str) -> list[tuple[bool, str]]:
    """(is_code, text) pieces; fences recognised as in preprocessing (``` or ~~~, any length).

    An unclosed fence runs to the end of the text, as in CommonMark.
    """
    out: list[tuple[bool, str]] = []
    buffer: list[str] = []
    marker: str | None = None
    for line in text.splitlines(keepends=True):
        bare = line.rstrip("\n")
        if marker is None:
            opened = fence_marker(bare)
            if opened is not None:
                if buffer:
                    out.append((False, "".join(buffer)))
                buffer, marker = [line], opened
            else:
                buffer.append(line)
            continue
        buffer.append(line)
        if closes_fence(bare, marker):
            block = "".join(buffer)
            tail = "\n" if block.endswith("\n") else ""
            out.append((True, block[: len(block) - len(tail)]))
            buffer, marker = ([tail] if tail else []), None
    if buffer:
        out.append((marker is not None, "".join(buffer)))
    return out


def page_html(text: str, words: list[str]) -> str:
    """The section text for the source page: highlighted, fenced code blocks in monospace."""
    return "".join(
        f'<span class="code">{highlight(piece, words)}</span>' if code else highlight(piece, words)
        for code, piece in segments(text)
    )


LINK_TARGET_RE = re.compile(r"\]\([^)\s]*\)")


def code_spans(text: str) -> list[tuple[int, int]]:
    """Inline code spans as in CommonMark: a backtick run closed by a run of the same length."""
    spans, i, n = [], 0, len(text)
    while i < n:
        if text[i] != "`":
            i += 1
            continue
        j = i
        while j < n and text[j] == "`":
            j += 1
        run, k, end = j - i, j, None
        while k < n:
            if text[k] != "`":
                k += 1
                continue
            m = k
            while m < n and text[m] == "`":
                m += 1
            if m - k == run:
                end = m
                break
            k = m
        if end is None:
            i = j  # unmatched run: plain backticks
        else:
            spans.append((i, end))
            i = end
    return spans


def _protected(text: str) -> list[tuple[int, int]]:
    """Inline code spans and link targets outside them, in text order."""
    spans = code_spans(text)
    links = [
        m.span()
        for m in LINK_TARGET_RE.finditer(text)
        if not any(a <= m.start() < b for a, b in spans)
    ]
    return sorted(spans + links)


def _mark(text: str, words: list[str]) -> str:
    """Mark matching tokens in Markdown prose; HTML entities like &lt; are left alone."""
    out, last = [], 0
    for match in TOKEN_RE.finditer(text):
        token = match.group()
        forms = {token.lower(), *CAMEL_RE.sub(" ", token).lower().split()}
        entity = match.start() > 0 and text[match.start() - 1] == "&"
        out.append(text[last : match.start()])
        if not entity and any(same_word(f, w) for f in forms for w in words):
            out.append(f'<mark class="hl">{token}</mark>')
        else:
            out.append(token)
        last = match.end()
    out.append(text[last:])
    return "".join(out)


def _prose(text: str, words: list[str]) -> str:
    """Tags shown as text, words marked; inline code untouched; site links made absolute."""
    out, last = [], 0
    for start, end in _protected(text):
        plain = text[last:start].replace("\\<", "&lt;").replace("<", "&lt;")
        out.append(_mark(plain, words))
        piece = text[start:end]
        if piece.startswith("](/"):
            piece = f"]({VUE_DOCS_SITE_URL}{piece[2:-1]})"
        out.append(piece)
        last = end
    plain = text[last:].replace("\\<", "&lt;").replace("<", "&lt;")
    out.append(_mark(plain, words))
    return "".join(out)


def markdown_with_highlights(text: str, words: list[str]) -> str:
    """The section as Markdown for the formatted view: fenced code blocks stay untouched."""
    return "".join(piece if code else _prose(piece, words) for code, piece in segments(text))
