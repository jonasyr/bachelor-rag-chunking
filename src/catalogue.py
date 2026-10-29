"""Question catalogue tools (ADR 0017, 0027, 0029, 0030).

Find, show and check; the questions and relevance judgements are written by hand. Reads only
the processed corpus and the catalogue files, never chunks, vectors, Chroma or retrieval
results, so the annotation stays blind (ADR 0027).

    sections            write the section lookup list (config.SECTION_INDEX_FILE)
    find TERM           sections whose own text contains TERM (case-insensitive, literal)
    show SECTION_ID     heading path, tokens and exact text of a section
    check [--draft]     coverage check (ADR 0029); --draft fails only on errors
    freeze              strict check, then record SHA-256 of both files (ADR 0030)
    screen              closed-book answers of new or changed questions (ADR 0040; calls the API)
"""

import argparse
import csv
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import closed_book
import tokens
from catalogue_overlap import overlap_section_ids, read_overlap
from catalogue_plan import (
    draw_plan,
    plan_findings,
    plan_integrity,
    plan_summary,
    read_plan,
    too_short_errors,
    write_plan,
)
from catalogue_review import ensure_review_file, read_review, review_errors, review_summary
from config import (
    AREA_MIN_QUESTIONS,
    CATALOGUE_CAMEL_BOUNDARY,
    CATALOGUE_DUPLICATE_EXCERPT_WORDS,
    CATALOGUE_DUPLICATE_MAX_SECTIONS,
    CATALOGUE_DUPLICATE_MIN_WORDS,
    CATALOGUE_DUPLICATE_SKIP_FENCES,
    CATALOGUE_EXCERPT_CHARS,
    CATALOGUE_FOLD_MIN_LENGTH,
    CATALOGUE_FREEZE_FILE,
    CATALOGUE_HEADING_SEPARATOR,
    CATALOGUE_OVERLAP_FILE,
    CATALOGUE_PLAN_FILE,
    CATALOGUE_PREFIX_MIN,
    CATALOGUE_PREFIX_SLACK,
    CATALOGUE_REPORT_MIN_PAGES,
    CATALOGUE_REVIEW_FILE,
    CATALOGUE_STOPWORDS,
    CATALOGUE_WORD_PATTERN,
    CLOSED_BOOK_FILE,
    DETAIL_MAX_ANSWER_WORDS,
    DOCUMENTS_FILE,
    GENERATION_RUNS_FILE,
    GROUND_TRUTH_FILE,
    MULTI_SECTION_MIN_SECTIONS,
    PILOT_DIR,
    QUESTION_CLASSES,
    QUESTION_TYPE_HINTS,
    QUESTION_TYPES,
    QUESTIONS_FILE,
    SECTION_INDEX_FILE,
    SECTIONS_FILE,
    SINGLE_CLASS_SECTIONS,
)
from embed import load_jsonl
from freeze import write_freeze
from llm_client import Completer, Completion, complete
from retrieve import (
    GROUND_TRUTH_HEADER,
    QUESTIONS_HEADER,
    QUESTIONS_REQUIRED,
    read_rows,
    relevant_sections,
)
from run_log import append_generation_run, sha256_of

WORD_RE = re.compile(CATALOGUE_WORD_PATTERN)
CAMEL_RE = re.compile(CATALOGUE_CAMEL_BOUNDARY)
STOPWORDS = frozenset(CATALOGUE_STOPWORDS)


class Corpus:
    """Documents and sections of the processed corpus; sections in sections.jsonl order."""

    def __init__(self, documents: list[dict], sections: list[dict]):
        self.docs = {d["doc_id"]: d for d in documents}
        self.sections = sections
        self.by_id = {s["section_id"]: s for s in sections}
        self._h1 = {s["doc_id"]: s for s in sections if s["level"] == 1}
        self._starts: dict[str, list[int]] = {}
        self._duplicates: dict[int, tuple[dict, dict]] = {}  # shared_passages index per run length

    def char_span(self, section: dict) -> tuple[int, int]:
        """Character range of the section in its document text (same slice as the chunks)."""
        doc_id = section["doc_id"]
        text = self.docs[doc_id]["text"]
        if doc_id not in self._starts:
            self._starts[doc_id] = tokens.token_starts(text)
        starts = self._starts[doc_id]

        def char(token: int) -> int:
            return starts[token] if token < len(starts) else len(text)

        return char(section["start_token"]), char(section["end_token"])

    def text(self, section: dict) -> str:
        start, end = self.char_span(section)
        return self.docs[section["doc_id"]]["text"][start:end]

    def area(self, section: dict) -> str:
        """Area of the section's document (documents.jsonl `area`: its navigation group, D38)."""
        return self.docs[section["doc_id"]]["area"]

    def page_title(self, section: dict) -> str:
        return self._h1[section["doc_id"]]["title"]

    def enclosing(self, section: dict) -> list[dict]:
        """The sections that contain this one, outermost first, followed by the section itself."""
        outer = [
            s
            for s in self.sections
            if s["doc_id"] == section["doc_id"]
            and s["level"] < section["level"]
            and s["start_token"] <= section["start_token"]
            and section["end_token"] <= s["end_token"]
        ]
        return sorted(outer, key=lambda s: s["level"]) + [section]

    def heading_path(self, section: dict) -> str:
        return CATALOGUE_HEADING_SEPARATOR.join(s["title"] for s in self.enclosing(section))


def load_corpus(
    documents_file: Path = DOCUMENTS_FILE, sections_file: Path = SECTIONS_FILE
) -> Corpus:
    return Corpus(
        load_jsonl(documents_file, "run src/preprocess.py first"),
        load_jsonl(sections_file, "run src/preprocess.py first"),
    )


def section_index(corpus: Corpus) -> str:
    """Markdown lookup list: one row per section, in sections.jsonl order."""
    lines = [
        "# Section index",
        "",
        f"Generated by `uv run python src/catalogue.py sections` from `{DOCUMENTS_FILE.name}` and "
        f"`{SECTIONS_FILE.name}`; do not edit. {len(corpus.sections)} sections.",
        "",
        "| section_id | area | path | heading path | tokens |",
        "|---|---|---|---|---:|",
    ]
    for s in corpus.sections:
        path = corpus.docs[s["doc_id"]]["path"]
        heading = corpus.heading_path(s).replace("|", "\\|")
        length = s["end_token"] - s["start_token"]
        lines.append(f"| `{s['section_id']}` | {corpus.area(s)} | {path} | {heading} | {length} |")
    return "\n".join(lines) + "\n"


def write_section_index(corpus: Corpus, out_file: Path = SECTION_INDEX_FILE) -> int:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(section_index(corpus), encoding="utf-8")
    return len(corpus.sections)


def _excerpt(text: str, start: int, end: int, lower: int, upper: int) -> str:
    """Match with up to CATALOGUE_EXCERPT_CHARS of context, never beyond [lower, upper)."""
    window = text[
        max(lower, start - CATALOGUE_EXCERPT_CHARS) : min(upper, end + CATALOGUE_EXCERPT_CHARS)
    ]
    return " ".join(window.split())


def nested(a: dict, b: dict) -> bool:
    """True if one of the two sections lies inside the other (same document)."""
    if a["doc_id"] != b["doc_id"]:
        return False
    inside = a["start_token"] <= b["start_token"] and b["end_token"] <= a["end_token"]
    return inside or (b["start_token"] <= a["start_token"] and a["end_token"] <= b["end_token"])


def own_spans(corpus: Corpus, section: dict) -> list[tuple[int, int]]:
    """Character ranges of the section's own text: its range minus its subsections."""
    start, end = corpus.char_span(section)
    children = sorted(
        corpus.char_span(c)
        for c in corpus.sections
        if c["level"] > section["level"] and c is not section and nested(section, c)
    )
    spans, at = [], start
    for a, b in children:
        if a > at:
            spans.append((at, a))
        at = max(at, b)
    if at < end:
        spans.append((at, end))
    return spans


def own_text(corpus: Corpus, section: dict) -> str:
    """The section's text without its subsections (what `find` searches)."""
    text = corpus.docs[section["doc_id"]]["text"]
    return "\n".join(text[a:b] for a, b in own_spans(corpus, section))


def find(corpus: Corpus, term: str) -> list[tuple[dict, str]]:
    """Sections whose own text contains term (literal, case-insensitive), with an excerpt.

    A match inside a subsection is reported for the innermost section only, not again for its
    parents; sections in sections.jsonl order.
    """
    if not term.strip():
        raise ValueError("empty search term")
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    hits = []
    for s in corpus.sections:
        start, end = corpus.char_span(s)
        text = corpus.docs[s["doc_id"]]["text"]
        for a, b in own_spans(corpus, s):
            match = pattern.search(text, a, b)
            if match:
                hits.append((s, _excerpt(text, match.start(), match.end(), start, end)))
                break
    return hits


def _words_and_examples(text: str) -> tuple[list[str], list[bool]]:
    """Lowercase words of the text and, per word, whether it lies in a code example block
    (config.CATALOGUE_DUPLICATE_SKIP_FENCES); same words in the same order as WORD_RE."""
    words, example, fence = [], [], None
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            info = stripped[3:].split()
            fence = None if fence is not None else (info[0].lower() if info else "")
        found = WORD_RE.findall(line.lower())
        words += found
        example += [fence in CATALOGUE_DUPLICATE_SKIP_FENCES] * len(found)
    return words, example


def _counts(example: list[bool], i: int, n: int) -> bool:
    """A run counts unless all its words lie in a code example."""
    return not all(example[i : i + n])


def _duplicate_index(corpus: Corpus, min_words: int) -> tuple[dict, dict]:
    """Words of every section's own text (with their example flags) and the sections containing
    each counting run of min_words."""
    if min_words not in corpus._duplicates:
        words = {s["section_id"]: _words_and_examples(own_text(corpus, s)) for s in corpus.sections}
        index: dict[tuple[str, ...], set[str]] = {}
        for sid, (ws, example) in words.items():
            for i in range(len(ws) - min_words + 1):
                if _counts(example, i, min_words):
                    index.setdefault(tuple(ws[i : i + min_words]), set()).add(sid)
        corpus._duplicates[min_words] = (words, index)
    return corpus._duplicates[min_words]


def shared_passages(
    corpus: Corpus,
    section_id: str,
    min_words: int = CATALOGUE_DUPLICATE_MIN_WORDS,
    excerpt_words: int = CATALOGUE_DUPLICATE_EXCERPT_WORDS,
    max_sections: int = CATALOGUE_DUPLICATE_MAX_SECTIONS,
) -> list[tuple[dict, str]]:
    """Other sections whose own text shares a run of at least min_words words with this one.

    A run found in more than max_sections sections is a template and does not count. One row
    per section with the longest shared run as excerpt, longest first; sections that contain this
    one or lie inside it do not count (ADR 0029: they add no text).
    """
    seed = corpus.by_id[section_id]
    words, index = _duplicate_index(corpus, min_words)
    ws, example = words[section_id]
    own = own_text(corpus, seed)
    spans = [m.span() for m in WORD_RE.finditer(own.lower())]  # same words as ws, with positions
    positions: dict[str, list[int]] = {}
    for i in range(len(ws) - min_words + 1):
        if not _counts(example, i, min_words):
            continue
        holders = index.get(tuple(ws[i : i + min_words]), set())
        if len(holders) > max_sections:
            continue
        for other in holders:
            positions.setdefault(other, []).append(i)
    hits = []
    for s in corpus.sections:
        found = positions.get(s["section_id"])
        if not found or s is seed or nested(seed, s):
            continue
        best_start, best_len, run_start, run_len = found[0], 1, found[0], 1
        for prev, cur in zip(found, found[1:], strict=False):
            run_start, run_len = (run_start, run_len + 1) if cur == prev + 1 else (cur, 1)
            if run_len > best_len:
                best_start, best_len = run_start, run_len
        length = best_len + min_words - 1
        shown = min(length, excerpt_words)
        a, b = spans[best_start][0], spans[best_start + shown - 1][1]
        excerpt = " ".join(own[a:b].split()) + (" …" if length > excerpt_words else "")
        hits.append((length, s, excerpt))
    hits.sort(key=lambda h: -h[0])  # stable: equal lengths stay in sections.jsonl order
    return [(s, excerpt) for _, s, excerpt in hits]


def suggest_type(question: str) -> tuple[str, str] | None:
    """The question type the wording points to and the phrase that did (config hints), or None."""
    text = question.replace("\u2019", "'").lower().strip()
    for qtype, pattern in QUESTION_TYPE_HINTS:
        match = re.search(pattern, text)
        if match:
            return qtype, match.group(0)
    return None


def show(corpus: Corpus, section_id: str) -> str:
    section = corpus.by_id.get(section_id)
    if section is None:
        raise ValueError(f"unknown section {section_id}")
    length = section["end_token"] - section["start_token"]
    head = f"{section_id}  {corpus.heading_path(section)}  ({length} tokens)"
    return f"{head}\n\n{corpus.text(section)}"


def content_words(text: str) -> set[str]:
    """Lowercase words of text without stopwords; camelCase also by its parts (ADR 0029)."""
    words = WORD_RE.findall(text.lower()) + WORD_RE.findall(CAMEL_RE.sub(" ", text).lower())
    return {w for w in words if w not in STOPWORDS}


def forms(word: str) -> set[str]:
    """The word and its candidate singular forms; two words match if their forms intersect.

    Errs towards a match (values -> valu as well as value), the safe side for a rule that must
    catch shared words.
    """
    result = {word}
    if len(word) >= CATALOGUE_FOLD_MIN_LENGTH:
        if word.endswith("s"):
            result.add(word[:-1])
        if word.endswith("es"):
            result.add(word[:-2])
        if word.endswith("ies"):
            result.add(word[:-3] + "y")
    return result


def same_word(a: str, b: str) -> bool:
    """Plural forms intersect, or a long enough common prefix (watch/watchers, mounted/mounting)."""
    if forms(a) & forms(b):
        return True
    prefix = len(os.path.commonprefix([a, b]))
    return prefix >= max(CATALOGUE_PREFIX_MIN, min(len(a), len(b)) - CATALOGUE_PREFIX_SLACK)


def shared_words(question: str, headings: list[str]) -> list[str]:
    """Question words that match a heading word, sorted."""
    heading_words = {w for heading in headings for w in content_words(heading)}
    return sorted(w for w in content_words(question) if any(same_word(w, h) for h in heading_words))


def heading_texts(corpus: Corpus, sections: list[dict]) -> list[str]:
    """Titles of the sections and of their pages: the heading words of a question (ADR 0029)."""
    return [title for s in sections for title in (s["title"], corpus.page_title(s))]


def nested_pairs(sections: list[dict]) -> list[tuple[str, str]]:
    """(child, parent) section IDs where a listed section lies inside another listed one."""
    return [
        (child["section_id"], parent["section_id"])
        for child in sections
        for parent in sections
        if parent["doc_id"] == child["doc_id"]
        and parent["level"] < child["level"]
        and parent["start_token"] <= child["start_token"]
        and child["end_token"] <= parent["end_token"]
    ]


def class_findings(corpus: Corpus, question: dict, truth: dict, sections: list[dict]) -> list[str]:
    """Violations of the construction-class rules of ADR 0029 for one question.

    A section inside another listed section adds no text, so it does not count as a further
    section for `multi-section`.
    """
    cls, count = question["difficulty"], len(sections)
    nested = nested_pairs(sections)
    found = [f"{child} lies inside {parent}" for child, parent in nested]
    if cls == "multi-section":
        independent = count - len({child for child, _ in nested})
        if independent < MULTI_SECTION_MIN_SECTIONS:
            found.append(
                f"multi-section needs at least {MULTI_SECTION_MIN_SECTIONS} relevant sections, "
                f"has {independent}"
            )
    elif count != SINGLE_CLASS_SECTIONS:
        noun = "section" if SINGLE_CLASS_SECTIONS == 1 else "sections"
        found.append(f"{cls} needs exactly {SINGLE_CLASS_SECTIONS} relevant {noun}, has {count}")
    if cls == "detail":
        words = len(truth["expected_answer"].split())
        if words > DETAIL_MAX_ANSWER_WORDS:
            found.append(f"detail answer has {words} words, at most {DETAIL_MAX_ANSWER_WORDS}")
    if cls == "paraphrase":
        shared = shared_words(question["question"], heading_texts(corpus, sections))
        if shared:
            found.append(f"paraphrase shares heading words {shared}")
    return found


def h1_findings(question: dict, sections: list[dict]) -> list[str]:
    """H1 sections (a whole page) listed without a reason in `notes` (ADR 0022)."""
    if question.get("notes", "").strip():
        return []
    return [
        f"{s['section_id']} is a whole page (H1); give the reason in notes (ADR 0022)"
        for s in sections
        if s["level"] == 1
    ]


@dataclass
class Report:
    """Result of the coverage check: errors always fail, findings only in strict mode."""

    errors: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)
    types: dict[str, int] = field(default_factory=dict)
    classes: dict[str, int] = field(default_factory=dict)
    closed_book: dict[str, int] = field(default_factory=dict)


def _has_rows(path: Path) -> bool:
    """False only for an existing file without any row below the header."""
    if not path.exists():
        return True  # read_rows reports the missing file
    with path.open(encoding="utf-8", newline="") as f:
        return sum(1 for record in csv.reader(f) if record) > 1


def normalised_question(text: str) -> str:
    """Question text for the duplicate check: lowercase words only."""
    return " ".join(WORD_RE.findall(text.lower()))


def _table(questions: list[dict]) -> list[str]:
    cells = Counter((q["type"], q["difficulty"]) for q in questions)
    head = f"| type \\ difficulty | {' | '.join(QUESTION_CLASSES)} | total | quota |"
    lines = [head, "|---" * (len(QUESTION_CLASSES) + 3) + "|"]
    for qtype, quota in QUESTION_TYPES.items():
        counts = [cells[(qtype, cls)] for cls in QUESTION_CLASSES]
        lines.append(f"| {qtype} | {' | '.join(map(str, counts))} | {sum(counts)} | {quota} |")
    totals = [sum(cells[(t, cls)] for t in QUESTION_TYPES) for cls in QUESTION_CLASSES]
    lines.append(f"| total | {' | '.join(map(str, totals))} | {sum(totals)} | |")
    quotas = " | ".join(str(n) for n in QUESTION_CLASSES.values())
    lines.append(f"| quota | {quotas} | {sum(QUESTION_CLASSES.values())} | |")
    return lines


def _overview(
    corpus: Corpus, questions: list[dict], truth: dict, relevant: dict, areas: Counter
) -> list[str]:
    lines = [f"Questions: {len(questions)} (quota {sum(QUESTION_TYPES.values())})", ""]
    lines += _table(questions)
    split = ", ".join(
        f"{a} {areas[a]}"
        + (f" (at least {AREA_MIN_QUESTIONS[a]})" if a in AREA_MIN_QUESTIONS else "")
        for a in [*AREA_MIN_QUESTIONS, *sorted(set(areas) - set(AREA_MIN_QUESTIONS))]
    )
    lines += ["", f"Areas (questions with a relevant section there): {split}"]
    multi = [q for q in questions if q["difficulty"] == "multi-section"]
    pages = CATALOGUE_REPORT_MIN_PAGES
    spread = sum(
        1 for q in multi if len({s["doc_id"] for s in relevant[q["question_id"]]}) >= pages
    )
    lines.append(f"multi-section on at least {pages} pages: {spread} of {len(multi)}")
    for q in questions:
        qid, sections = q["question_id"], relevant[q["question_id"]]
        if q["difficulty"] == "detail":
            length = sum(s["end_token"] - s["start_token"] for s in sections)
            words = len(truth[qid]["expected_answer"].split())
            lines.append(f"detail {qid}: section {length} tokens, answer {words} words")
        if q["difficulty"] in ("detail", "multi-section"):
            shared = shared_words(q["question"], heading_texts(corpus, sections))
            if shared:
                lines.append(f"heading words in {q['difficulty']} {qid}: {shared}")
    return lines


def check(
    corpus: Corpus,
    questions_file: Path = QUESTIONS_FILE,
    ground_truth_file: Path = GROUND_TRUTH_FILE,
    pilot_dir: Path = PILOT_DIR,
    plan_file: Path = CATALOGUE_PLAN_FILE,
    review_file: Path = CATALOGUE_REVIEW_FILE,
    fresh_plan: list[dict] | None = None,
    closed_book_file: Path | None = None,
    overlap_file: Path | None = None,
) -> Report:
    """Coverage check of the catalogue (ADR 0029); never reads retrieval results."""
    report = Report()
    overlap_file = overlap_file or CATALOGUE_OVERLAP_FILE
    try:
        unknown = overlap_section_ids(read_overlap(overlap_file)) - set(corpus.by_id)
        if unknown:
            report.errors.append(f"{overlap_file.name}: unknown section IDs {sorted(unknown)}")
    except ValueError as error:
        report.errors.append(str(error))
    if not _has_rows(questions_file):
        report.errors.append(f"{questions_file.name} has no questions yet")
        return report
    try:
        questions = read_rows(
            questions_file, "question catalogue", QUESTIONS_HEADER, QUESTIONS_REQUIRED
        )
        truth_rows = read_rows(
            ground_truth_file, "ground truth", GROUND_TRUTH_HEADER, GROUND_TRUTH_HEADER
        )
        relevant = relevant_sections(questions, truth_rows, corpus.sections)
    except (FileNotFoundError, ValueError) as error:
        report.errors.append(str(error))
        return report
    questions.sort(key=lambda q: q["question_id"])
    truth = {row["question_id"]: row for row in truth_rows}

    for q in questions:
        qid = q["question_id"]
        if q["type"] not in QUESTION_TYPES:
            report.errors.append(
                f"{qid}: unknown type {q['type']!r}; allowed {list(QUESTION_TYPES)}"
            )
        if q["difficulty"] not in QUESTION_CLASSES:
            report.errors.append(
                f"{qid}: unknown difficulty {q['difficulty']!r}; allowed {list(QUESTION_CLASSES)}"
            )
            continue
        report.findings += [
            f"{qid}: {m}" for m in class_findings(corpus, q, truth[qid], relevant[qid])
        ]
        report.findings += [f"{qid}: {m}" for m in h1_findings(q, relevant[qid])]

    types = Counter(q["type"] for q in questions)
    classes = Counter(q["difficulty"] for q in questions)
    report.types = {t: types[t] for t in QUESTION_TYPES}
    report.classes = {c: classes[c] for c in QUESTION_CLASSES}
    for name, quotas, counts in (
        ("type", QUESTION_TYPES, types),
        ("difficulty", QUESTION_CLASSES, classes),
    ):
        for value, quota in quotas.items():
            if counts[value] != quota:
                report.findings.append(f"{name} {value}: {counts[value]} questions, quota {quota}")

    areas = Counter(
        area for q in questions for area in {corpus.area(s) for s in relevant[q["question_id"]]}
    )
    for area, floor in AREA_MIN_QUESTIONS.items():
        if areas[area] < floor:
            report.findings.append(f"area {area}: {areas[area]} questions, at least {floor}")

    seen: dict[str, str] = {}
    for q in questions:
        key = normalised_question(q["question"])
        if key in seen:
            report.findings.append(f"{q['question_id']}: same question as {seen[key]}")
        else:
            seen[key] = q["question_id"]
    for path in sorted(pilot_dir.rglob(QUESTIONS_FILE.name)):
        label = path.parent.relative_to(pilot_dir).as_posix()
        try:
            rows = read_rows(path, "pilot questions", QUESTIONS_HEADER, QUESTIONS_REQUIRED)
        except ValueError as error:
            report.errors.append(f"pilot set {label}: {error}")
            continue
        for row in rows:
            key = normalised_question(row["question"])
            if key in seen:
                where = f"{label}/{row['question_id']}" if label != "." else row["question_id"]
                report.findings.append(f"{seen[key]}: same question as pilot {where}")

    try:
        plan = read_plan(plan_file)
    except (FileNotFoundError, ValueError) as error:
        report.errors.append(str(error))
        plan = None
    plan_lines: list[str] = []
    if plan is not None:
        errors, findings = plan_findings(plan, questions, relevant, set(corpus.by_id))
        report.errors += errors
        report.findings += findings
        plan_lines = plan_summary(plan)
        if fresh_plan is None:
            try:
                fresh_plan = draw_plan(corpus)  # deterministic: the plan must match it (ADR 0031)
            except ValueError as error:
                report.errors.append(f"cannot redraw the plan to compare: {error}")
        if fresh_plan is not None:
            report.errors += plan_integrity(plan, fresh_plan)
        report.errors += too_short_errors(plan, corpus)
    if not review_file.exists():
        report.findings.append(
            f"{review_file.name} is missing; `catalogue.py plan` creates it (ADR 0031)"
        )
    try:
        review = read_review(review_file)
    except ValueError as error:
        report.errors.append(str(error))
        review = []
    report.errors += review_errors(review, {q["question_id"] for q in questions}, set(corpus.by_id))
    for number, r in enumerate(review, start=2):
        annotated = {s["section_id"] for s in relevant.get(r["question_id"], [])}
        if (
            r["kind"] == "missing_section"
            and r["decision"] == "accepted"
            and (r["section_id"] not in annotated)
        ):
            report.findings.append(
                f"{r['question_id']}: accepted section {r['section_id']} (review row {number}) "
                "is no longer annotated"
            )
    still_open = sum(1 for r in review if r["decision"] == "open")
    if still_open:
        report.findings.append(f"{still_open} review suggestion(s) still open")
    n_quota = sum(QUESTION_TYPES.values())
    try:
        screen_rows = closed_book.read_screen(closed_book_file or CLOSED_BOOK_FILE)
    except ValueError as error:
        report.errors.append(str(error))
        screen_rows = []
    errors, findings = closed_book.findings(screen_rows, questions, truth, n_quota)
    report.errors += errors
    report.findings += findings
    report.closed_book = closed_book.counts(screen_rows, questions, truth)
    plan_lines.append(review_summary(review))
    plan_lines.append(closed_book.summary(report.closed_book, n_quota))
    report.lines = _overview(corpus, questions, truth, relevant, areas) + plan_lines
    return report


def exit_code(report: Report, draft: bool) -> int:
    """1 on any error; findings fail only the strict check (and therefore the freeze)."""
    return int(bool(report.errors) or (not draft and bool(report.findings)))


def freeze_catalogue(
    corpus: Corpus,
    questions_file: Path = QUESTIONS_FILE,
    ground_truth_file: Path = GROUND_TRUTH_FILE,
    freeze_file: Path = CATALOGUE_FREEZE_FILE,
    pilot_dir: Path = PILOT_DIR,
    sections_file: Path = SECTIONS_FILE,
    documents_file: Path = DOCUMENTS_FILE,
    plan_file: Path = CATALOGUE_PLAN_FILE,
    review_file: Path = CATALOGUE_REVIEW_FILE,
    fresh_plan: list[dict] | None = None,
    closed_book_file: Path | None = None,
    overlap_file: Path | None = None,
) -> dict:
    """Strict check, then the freeze record (ADR 0030); nothing is written if the check fails.

    `sections_file` and `documents_file` must be the files `corpus` was loaded from; their hashes
    pin which text the section IDs refer to.
    """
    closed_book_file = closed_book_file or CLOSED_BOOK_FILE
    overlap_file = overlap_file or CATALOGUE_OVERLAP_FILE
    report = check(
        corpus,
        questions_file,
        ground_truth_file,
        pilot_dir,
        plan_file,
        review_file,
        fresh_plan,
        closed_book_file=closed_book_file,
        overlap_file=overlap_file,
    )
    if exit_code(report, draft=False):
        raise ValueError(
            "the catalogue does not pass the strict check; run `src/catalogue.py check`"
        )
    summary = {
        "questions": sum(report.classes.values()),
        "types": report.types,
        "classes": report.classes,
        "closed_book": {k: report.closed_book[k] for k in ("dependent", "known")},
    }
    recorded = tuple(
        p for p in (plan_file, review_file, closed_book_file, overlap_file) if p.exists()
    )
    return write_freeze(
        questions_file,
        ground_truth_file,
        sections_file,
        documents_file,
        freeze_file,
        summary,
        recorded=recorded,
    )


def run_screen(completer: Completer = complete, runs_file: Path = GENERATION_RUNS_FILE) -> int:
    """`screen`: closed-book answers of new or changed questions, one run record (ADR 0040)."""
    if CATALOGUE_FREEZE_FILE.exists():
        print("the catalogue is frozen (ADR 0030); the screen is final", file=sys.stderr)
        return 1
    try:
        questions = read_rows(
            QUESTIONS_FILE, "question catalogue", QUESTIONS_HEADER, QUESTIONS_REQUIRED
        )
        truth_rows = read_rows(
            GROUND_TRUTH_FILE, "ground truth", GROUND_TRUTH_HEADER, GROUND_TRUTH_HEADER
        )
    except (FileNotFoundError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    questions.sort(key=lambda q: q["question_id"])
    truth = {row["question_id"]: row for row in truth_rows}
    done: list[Completion] = []
    code = 0
    try:
        closed_book.screen(questions, truth, completer, CLOSED_BOOK_FILE, done)
    except Exception as error:  # API errors included: log what was paid for, then stop
        print(error, file=sys.stderr)
        code = 1
    if done:
        append_generation_run(
            {
                "step": "closed_book_screen",
                "answers": len(done),
                "model_reported": sorted({d.model for d in done}),
                "system_fingerprint": sorted({d.system_fingerprint or "" for d in done}),
                "outputs_sha256": {CLOSED_BOOK_FILE.name: sha256_of(CLOSED_BOOK_FILE)},
            },
            sum(d.prompt_tokens for d in done),
            sum(d.completion_tokens for d in done),
            runs_file,
        )
    print(f"{len(done)} questions answered without context -> {CLOSED_BOOK_FILE}")
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Question catalogue tools (ADR 0029, 0030).")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("sections", help=f"write the lookup list ({SECTION_INDEX_FILE.name})")
    find_cmd = commands.add_parser("find", help="sections whose own text contains TERM")
    find_cmd.add_argument("term")
    show_cmd = commands.add_parser("show", help="heading path, tokens and text of a section")
    show_cmd.add_argument("section_id")
    check_cmd = commands.add_parser("check", help="coverage check of the catalogue")
    check_cmd.add_argument("--draft", action="store_true", help="fail only on errors")
    commands.add_parser("freeze", help="strict check, then write the freeze record")
    commands.add_parser("plan", help="draw the sampling plan once (ADR 0031)")
    commands.add_parser(
        "screen", help="closed-book answers of new or changed questions (ADR 0040; calls the API)"
    )
    args = parser.parse_args(argv)
    if args.command == "screen":
        return run_screen()

    corpus = load_corpus(DOCUMENTS_FILE, SECTIONS_FILE)
    if args.command == "sections":
        count = write_section_index(corpus, SECTION_INDEX_FILE)
        print(f"{count} sections -> {SECTION_INDEX_FILE}")
        return 0
    if args.command == "find":
        try:
            hits = find(corpus, args.term)
        except ValueError as error:
            print(error, file=sys.stderr)
            return 1
        for section, excerpt in hits:
            print(f"{section['section_id']}  {corpus.heading_path(section)}\n    {excerpt}")
        print(f"{len(hits)} sections")
        return 0
    if args.command == "show":
        try:
            print(show(corpus, args.section_id))
        except ValueError as error:
            print(error, file=sys.stderr)
            return 1
        return 0

    if args.command == "plan":
        try:
            count = write_plan(corpus, CATALOGUE_PLAN_FILE)
        except (FileExistsError, ValueError) as error:
            print(error, file=sys.stderr)
            return 1
        print(f"{count} plan rows -> {CATALOGUE_PLAN_FILE}")
        ensure_review_file(CATALOGUE_REVIEW_FILE)
        return 0

    report = check(
        corpus,
        QUESTIONS_FILE,
        GROUND_TRUTH_FILE,
        PILOT_DIR,
        CATALOGUE_PLAN_FILE,
        CATALOGUE_REVIEW_FILE,
        closed_book_file=CLOSED_BOOK_FILE,
    )
    draft = args.command == "check" and args.draft
    print("\n".join(report.lines))
    for error in report.errors:
        print(f"ERROR {error}")
    for finding in report.findings:
        print(f"{'WARNING' if draft else 'FINDING'} {finding}")
    code = exit_code(report, draft)
    if args.command == "check" or code:
        return code
    try:
        record = freeze_catalogue(
            corpus,
            QUESTIONS_FILE,
            GROUND_TRUTH_FILE,
            CATALOGUE_FREEZE_FILE,
            PILOT_DIR,
            SECTIONS_FILE,
            DOCUMENTS_FILE,
            CATALOGUE_PLAN_FILE,
            CATALOGUE_REVIEW_FILE,
            closed_book_file=CLOSED_BOOK_FILE,
        )
    except (FileExistsError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"frozen on {record['date']} -> {CATALOGUE_FREEZE_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
