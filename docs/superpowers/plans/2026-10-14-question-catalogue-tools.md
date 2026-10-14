# Question Catalogue Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tools to find, show and check the 48-question catalogue against the 813 corpus sections, plus a freeze
that makes retrieval on an unfrozen or changed catalogue impossible.

**Architecture:** One CLI module `src/catalogue.py` (subcommands `sections`, `find`, `show`, `check`, `freeze`) built
on a small `Corpus` class over `documents.jsonl`/`sections.jsonl`; it reuses the format validation of `retrieve.py`.
A separate module `src/freeze.py` writes and verifies the freeze record, so `retrieve.py` can call it without a
circular import. All parameters in `src/config.py`.

**Tech Stack:** Python 3.13 (uv), tiktoken via `src/tokens.py`, pytest, ruff (pre-commit), Pyright.

**Spec:** `docs/superpowers/specs/2026-10-14-question-catalogue-tools-design.md`

## Global Constraints

- All parameters (paths, quotas, thresholds, word lists) live only in `src/config.py` (AGENTS.md).
- No tool in this plan reads chunks, vectors, Chroma or retrieval results, and none calls the OpenAI API (ADR 0027).
- Tests never call the OpenAI API and need no network beyond tiktoken's one-time `cl100k_base` download.
- `type` ∈ {`factual`, `procedural`, `conceptual`, `comparative`, `limitation`}, quotas 12/12/12/6/6.
- `difficulty` ∈ {`single`, `multi-section`, `detail`, `paraphrase`}, quotas 12 each; total exactly 48.
- Area floors `{"api": 12, "style-guide": 3}`; a question counts for every area it touches.
- `DETAIL_MAX_ANSWER_WORDS = 30`.
- Pilot sets under `data/pilot/` are not changed and not subject to the rules; the freeze gate covers only
  `config.QUESTIONS_FILE`/`config.GROUND_TRUTH_FILE`.
- Conventional Commits with German subject like the existing history; never `Co-Authored-By` or AI attribution.
- Line length 100 (ruff); Pyright 0 errors.
- Run every command from the repo root `code/`.

## Review Focus

1. A section title containing `|` (Markdown table separator) must not break `section_index.md` → escaped as `\|`
   (test in Task 1).
2. A search term with regex characters (`v-model.lazy`, `defineProps<`) must match literally, an empty term must be an
   error (tests in Task 2).
3. A catalogue row with an unknown `type` or `difficulty` must be reported as an error by question ID, not crash the
   quota count or be silently counted (test in Task 4).
4. `retrieve.py` called with the main `questions.csv` but a different `ground_truth.csv` (mixed paths) must be refused
   like an unfrozen catalogue (test in Task 5).
5. `freeze` on a catalogue that fails the strict check must not write any record, and must never overwrite an existing
   one (tests in Task 5).

---

### Task 1: Configuration, corpus model and section lookup list

**Files:**
- Modify: `src/config.py` (paths block after `SECTIONS_FILE` and after `GROUND_TRUTH_FILE`; new block
  "Question catalogue" after the relevance keys)
- Create: `src/catalogue.py`
- Create: `tests/test_catalogue.py`

**Interfaces:**
- Produces: `config.SECTION_INDEX_FILE: Path`, `config.CATALOGUE_FREEZE_FILE: Path`,
  `config.QUESTION_TYPES: dict[str, int]`, `config.QUESTION_CLASSES: dict[str, int]`,
  `config.AREA_MIN_QUESTIONS: dict[str, int]`, `config.DETAIL_MAX_ANSWER_WORDS: int`,
  `config.CATALOGUE_STOPWORDS: tuple[str, ...]`, `config.CATALOGUE_WORD_PATTERN: str`,
  `config.CATALOGUE_FOLD_MIN_LENGTH: int`.
- Produces: `class Corpus(documents: list[dict], sections: list[dict])` with attributes `docs: dict[str, dict]`,
  `sections: list[dict]`, `by_id: dict[str, dict]` and methods `char_span(section) -> tuple[int, int]`,
  `text(section) -> str`, `area(section) -> str`, `page_title(section) -> str`, `enclosing(section) -> list[dict]`,
  `heading_path(section) -> str`; `load_corpus(documents_file: Path = DOCUMENTS_FILE, sections_file: Path =
  SECTIONS_FILE) -> Corpus`; `section_index(corpus: Corpus) -> str`;
  `write_section_index(corpus: Corpus, out_file: Path = SECTION_INDEX_FILE) -> int`.
- Produces (tests): fixtures `corpus_files(tmp_path) -> tuple[Path, Path]` and `corpus(corpus_files) -> Corpus` in
  `tests/test_catalogue.py`.

- [ ] **Step 1: Add the configuration keys**

In `src/config.py`, after the line `SECTIONS_FILE = DATA_PROCESSED / "sections.jsonl"` add:

```python
SECTION_INDEX_FILE = DATA_PROCESSED / "section_index.md"  # lookup list for annotation (D29)
```

After the line `GROUND_TRUTH_FILE = DATA_EVAL / "ground_truth.csv"` add:

```python
CATALOGUE_FREEZE_FILE = DATA_EVAL / "catalogue_freeze.json"  # SHA-256 of the frozen catalogue (D30)
```

After the line `SENSITIVITY_MIN_OVERLAP = 100  # sensitivity check for the retrieval evaluation` add:

```python

# ---------------------------------------------------------------------------
# Question catalogue (D17, D29, D30)
# ---------------------------------------------------------------------------
# Allowed values of questions.csv `type` and `difficulty` with their quotas; both sum to the
# catalogue size (48). `difficulty` holds the construction class (D29).
QUESTION_TYPES = {"factual": 12, "procedural": 12, "conceptual": 12, "comparative": 6, "limitation": 6}
QUESTION_CLASSES = {"single": 12, "multi-section": 12, "detail": 12, "paraphrase": 12}
# Minimum number of questions with a relevant section in an area (keys of VUE_DOCS_AREAS); a
# question counts for every area it touches (D29).
AREA_MIN_QUESTIONS = {"api": 12, "style-guide": 3}
DETAIL_MAX_ANSWER_WORDS = 30  # `detail`: reference answer at most this many words (D29)
# Word comparison for the paraphrase rule (D29): lowercase words matching the pattern, minus
# stopwords; words of at least CATALOGUE_FOLD_MIN_LENGTH characters also match without a
# trailing s/es and with ies -> y.
CATALOGUE_WORD_PATTERN = r"[a-z0-9]+"
CATALOGUE_FOLD_MIN_LENGTH = 4
CATALOGUE_STOPWORDS = (
    "a", "about", "am", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by",
    "can", "could", "did", "do", "does", "done", "for", "from", "had", "has", "have", "he",
    "here", "how", "i", "if", "in", "into", "is", "it", "its", "may", "me", "might", "must",
    "my", "no", "not", "of", "on", "onto", "or", "our", "over", "shall", "she", "should", "so",
    "than", "that", "the", "their", "them", "then", "there", "these", "they", "this", "those",
    "to", "under", "vue", "was", "we", "were", "what", "when", "where", "which", "who", "whom",
    "whose", "why", "will", "with", "without", "would", "you", "your",
)  # fmt: skip
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_catalogue.py`:

```python
import json

import pytest

import tokens
from catalogue import load_corpus, section_index, write_section_index
from config import (
    AREA_MIN_QUESTIONS,
    QUESTION_CLASSES,
    QUESTION_TYPES,
    VUE_DOCS_AREAS,
)
from preprocess import clean_markdown, section_spans

PAGES = {
    "api/reactivity-core.md": (
        "# Reactivity API: Core {#core}\n\n## ref() {#ref}\n\n"
        "Takes an inner value and returns a reactive ref object.\n\n## computed() {#computed}\n\n"
        "Takes a getter function and returns a readonly ref.\n"
    ),
    "guide/essentials/watchers.md": (
        "# Watchers {#watchers}\n\nWatchers run side effects.\n\n## Deep Watchers {#deep}\n\n"
        "A deep watcher tracks nested props. Use the once option.\n\n### Once Watchers {#once}\n\n"
        "Set once: true to run the callback only one time.\n\n## Side Effect Cleanup {#cleanup}\n\n"
        "Register cleanup with onWatcherCleanup.\n"
    ),
    "style-guide/rules-essential.md": (
        "# Priority A Rules: Essential {#essential}\n\n"
        "## Use multi-word component names {#multi-word}\n\n"
        "User component names should always be multi-word, except for root App components.\n"
    ),
}


def build_corpus(tmp_path, pages):
    docs, sections = [], []
    for number, (path, page) in enumerate(sorted(pages.items()), start=1):
        doc_id = f"D{number:03d}"
        result = clean_markdown(page)
        spans = section_spans(doc_id, result)
        docs.append(
            {
                "doc_id": doc_id,
                "path": path,
                "title": spans[0]["title"],
                "text": result.text,
                "tokens": tokens.count(result.text),
            }
        )
        sections.extend(spans)
    docs_file, sections_file = tmp_path / "documents.jsonl", tmp_path / "sections.jsonl"
    docs_file.write_text("".join(json.dumps(d) + "\n" for d in docs), encoding="utf-8")
    sections_file.write_text("".join(json.dumps(s) + "\n" for s in sections), encoding="utf-8")
    return docs_file, sections_file


@pytest.fixture
def corpus_files(tmp_path):
    return build_corpus(tmp_path, PAGES)


@pytest.fixture
def corpus(corpus_files):
    return load_corpus(*corpus_files)


def test_config_quotas_are_consistent():
    assert sum(QUESTION_TYPES.values()) == sum(QUESTION_CLASSES.values()) == 48
    assert set(AREA_MIN_QUESTIONS) <= set(VUE_DOCS_AREAS)


def test_corpus_text_is_the_exact_token_slice(corpus):
    once = corpus.by_id["D002#once"]
    doc = corpus.docs["D002"]
    starts = tokens.token_starts(doc["text"])
    assert corpus.text(once) == doc["text"][starts[once["start_token"]] : starts[once["end_token"]]]
    assert corpus.text(once).startswith("### Once Watchers")


def test_heading_path_area_and_page_title(corpus):
    once = corpus.by_id["D002#once"]
    assert corpus.heading_path(once) == "Watchers › Deep Watchers › Once Watchers"
    assert corpus.heading_path(corpus.by_id["D001#core"]) == "Reactivity API: Core"
    assert corpus.area(once) == "guide"
    assert corpus.area(corpus.by_id["D003#multi-word"]) == "style-guide"
    assert corpus.page_title(once) == "Watchers"


def test_section_index_has_one_row_per_section_in_order(corpus):
    lines = section_index(corpus).splitlines()
    rows = [line for line in lines if line.startswith("| `")]
    assert [row.split("`")[1] for row in rows] == [s["section_id"] for s in corpus.sections]
    once = corpus.by_id["D002#once"]
    tokens_once = once["end_token"] - once["start_token"]
    assert (
        f"| `D002#once` | guide | guide/essentials/watchers.md | "
        f"Watchers › Deep Watchers › Once Watchers | {tokens_once} |"
    ) in rows


def test_section_index_escapes_pipes_in_titles(tmp_path):
    pages = {"guide/a.md": "# A | B {#a}\n\nText.\n"}
    index = section_index(load_corpus(*build_corpus(tmp_path, pages)))
    assert "| A \\| B |" in index


def test_write_section_index_is_deterministic(corpus, tmp_path):
    out = tmp_path / "index.md"
    assert write_section_index(corpus, out) == len(corpus.sections)
    first = out.read_bytes()
    write_section_index(corpus, out)
    assert out.read_bytes() == first
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_catalogue.py -q`
Expected: FAIL (collection error: `ModuleNotFoundError: No module named 'catalogue'`).

- [ ] **Step 4: Write the implementation**

Create `src/catalogue.py`:

```python
"""Question catalogue tools (ADR 0017, 0027, 0029, 0030).

Find, show and check; the questions and relevance judgements are written by hand. Reads only
the processed corpus and the catalogue files, never chunks, vectors, Chroma or retrieval
results, so the annotation stays blind (ADR 0027).

    sections            write the section lookup list (config.SECTION_INDEX_FILE)
    find TERM           sections whose own text contains TERM (case-insensitive, literal)
    show SECTION_ID     heading path, tokens and exact text of a section
    check [--draft]     coverage check (ADR 0029); --draft fails only on errors
    freeze              strict check, then record SHA-256 of both files (ADR 0030)
"""

from pathlib import Path

import tokens
from config import DOCUMENTS_FILE, SECTION_INDEX_FILE, SECTIONS_FILE
from embed import load_jsonl

HEADING_SEPARATOR = " › "


class Corpus:
    """Documents and sections of the processed corpus; sections in sections.jsonl order."""

    def __init__(self, documents: list[dict], sections: list[dict]):
        self.docs = {d["doc_id"]: d for d in documents}
        self.sections = sections
        self.by_id = {s["section_id"]: s for s in sections}
        self._h1 = {s["doc_id"]: s for s in sections if s["level"] == 1}
        self._starts: dict[str, list[int]] = {}

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
        """First path segment of the section's document: a key of config.VUE_DOCS_AREAS."""
        return self.docs[section["doc_id"]]["path"].split("/")[0]

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
        return HEADING_SEPARATOR.join(s["title"] for s in self.enclosing(section))


def load_corpus(documents_file: Path = DOCUMENTS_FILE, sections_file: Path = SECTIONS_FILE) -> Corpus:
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
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_catalogue.py -q`
Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add src/config.py src/catalogue.py tests/test_catalogue.py
git commit -m "feat(catalogue): Korpusmodell und Abschnitts-Nachschlageliste"
```

---

### Task 2: `find` and `show`

**Files:**
- Modify: `src/catalogue.py`
- Modify: `tests/test_catalogue.py`

**Interfaces:**
- Consumes: `Corpus`, fixture `corpus` (Task 1).
- Produces: `find(corpus: Corpus, term: str) -> list[tuple[dict, str]]` (section, one-line excerpt);
  `show(corpus: Corpus, section_id: str) -> str`; module constant `EXCERPT_CHARS = 60`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_catalogue.py` (and add `find, show` to the `from catalogue import ...` line):

```python
def test_find_reports_only_the_innermost_section(corpus):
    hits = find(corpus, "callback only")
    assert [s["section_id"] for s, _ in hits] == ["D002#once"]
    assert "callback only one time" in hits[0][1]


def test_find_is_case_insensitive_and_reports_each_owning_section(corpus):
    ids = [s["section_id"] for s, _ in find(corpus, "ONCE")]
    assert ids == ["D002#deep", "D002#once"]  # "Use the once option" is in Deep's own text


def test_find_matches_regex_characters_literally(corpus):
    assert [s["section_id"] for s, _ in find(corpus, "ref()")] == ["D001#ref"]
    assert find(corpus, "r.f") == []


def test_find_rejects_an_empty_term(corpus):
    with pytest.raises(ValueError, match="empty search term"):
        find(corpus, "  ")


def test_show_prints_heading_path_tokens_and_exact_text(corpus):
    once = corpus.by_id["D002#once"]
    out = show(corpus, "D002#once")
    assert out.splitlines()[0] == (
        f"D002#once  Watchers › Deep Watchers › Once Watchers  "
        f"({once['end_token'] - once['start_token']} tokens)"
    )
    assert out.endswith(corpus.text(once))


def test_show_rejects_an_unknown_section(corpus):
    with pytest.raises(ValueError, match="unknown section D009#x"):
        show(corpus, "D009#x")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_catalogue.py -q`
Expected: FAIL (`ImportError: cannot import name 'find' from 'catalogue'`).

- [ ] **Step 3: Write the implementation**

In `src/catalogue.py` add `import re` above `from pathlib import Path`, add `EXCERPT_CHARS = 60` below
`HEADING_SEPARATOR`, and append:

```python
def _excerpt(text: str, start: int, end: int) -> str:
    return " ".join(text[max(0, start - EXCERPT_CHARS) : end + EXCERPT_CHARS].split())


def find(corpus: Corpus, term: str) -> list[tuple[dict, str]]:
    """Sections whose own text contains term (literal, case-insensitive), with an excerpt.

    A match inside a subsection is reported for the innermost section only, not again for its
    parents; sections in sections.jsonl order.
    """
    if not term.strip():
        raise ValueError("empty search term")
    pattern = re.compile(re.escape(term.strip()), re.IGNORECASE)
    hits = []
    for s in corpus.sections:
        start, end = corpus.char_span(s)
        children = [
            corpus.char_span(c)
            for c in corpus.sections
            if c["doc_id"] == s["doc_id"]
            and c["level"] > s["level"]
            and s["start_token"] <= c["start_token"]
            and c["end_token"] <= s["end_token"]
        ]
        text = corpus.docs[s["doc_id"]]["text"]
        for match in pattern.finditer(text, start, end):
            if not any(a <= match.start() < b for a, b in children):
                hits.append((s, _excerpt(text, match.start(), match.end())))
                break
    return hits


def show(corpus: Corpus, section_id: str) -> str:
    section = corpus.by_id.get(section_id)
    if section is None:
        raise ValueError(f"unknown section {section_id}")
    length = section["end_token"] - section["start_token"]
    head = f"{section_id}  {corpus.heading_path(section)}  ({length} tokens)"
    return f"{head}\n\n{corpus.text(section)}"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_catalogue.py -q`
Expected: 12 passed.

- [ ] **Step 5: Commit**

```bash
git add src/catalogue.py tests/test_catalogue.py
git commit -m "feat(catalogue): Textsuche und Abschnittsanzeige"
```

---

### Task 3: Word comparison and class rules

**Files:**
- Modify: `src/catalogue.py`
- Modify: `tests/test_catalogue.py`

**Interfaces:**
- Consumes: `Corpus` (Task 1); config keys from Task 1.
- Produces: `content_words(text: str) -> set[str]`; `forms(word: str) -> set[str]`;
  `shared_words(question: str, headings: list[str]) -> list[str]`;
  `heading_texts(corpus: Corpus, sections: list[dict]) -> list[str]`;
  `class_findings(corpus: Corpus, question: dict, truth: dict, sections: list[dict]) -> list[str]`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_catalogue.py` (add `class_findings, content_words, forms, shared_words` to the import):

```python
def test_content_words_drop_stopwords_and_punctuation():
    assert content_words("How do I use ref() in Vue?") == {"use", "ref"}


def test_forms_fold_plural_endings_only_for_longer_words():
    assert forms("values") == {"values", "value", "valu"}
    assert forms("watches") == {"watches", "watche", "watch"}
    assert forms("dependencies") >= {"dependency"}
    assert forms("refs") == {"refs", "ref"}
    assert forms("its") == {"its"}  # shorter than CATALOGUE_FOLD_MIN_LENGTH


@pytest.mark.parametrize(
    ("question", "heading", "shared"),
    [
        ("Which values can it hold?", "Value Bindings", ["values"]),
        ("How do props work?", "Prop Validation", ["props"]),
        ("What are refs?", "ref()", ["refs"]),
        ("What does a dependency do?", "Optional Dependencies", ["dependency"]),
        ("How do I skip later renders?", "v-once", []),
    ],
)
def test_shared_words(question, heading, shared):
    assert shared_words(question, [heading]) == shared


def question(difficulty, text="Question number one"):
    return {"question_id": "Q001", "question": text, "type": "factual", "difficulty": difficulty}


def truth(answer="Short answer."):
    return {"question_id": "Q001", "expected_answer": answer}


def test_single_needs_exactly_one_section(corpus):
    one, two = [corpus.by_id["D001#ref"]], [corpus.by_id["D001#ref"], corpus.by_id["D002#once"]]
    assert class_findings(corpus, question("single"), truth(), one) == []
    assert class_findings(corpus, question("single"), truth(), two) == [
        "single needs exactly 1 relevant section, has 2"
    ]


def test_multi_section_needs_two_sections(corpus):
    one, two = [corpus.by_id["D001#ref"]], [corpus.by_id["D001#ref"], corpus.by_id["D002#once"]]
    assert class_findings(corpus, question("multi-section"), truth(), two) == []
    assert class_findings(corpus, question("multi-section"), truth(), one) == [
        "multi-section needs at least 2 relevant sections, has 1"
    ]


def test_detail_limits_the_answer_length(corpus):
    one = [corpus.by_id["D002#once"]]
    assert class_findings(corpus, question("detail"), truth("word " * 30), one) == []
    assert class_findings(corpus, question("detail"), truth("word " * 31), one) == [
        "detail answer has 31 words, at most 30"
    ]


def test_paraphrase_must_not_share_section_or_page_heading_words(corpus):
    once = [corpus.by_id["D002#once"]]  # headings "Once Watchers" and page title "Watchers"
    ok = question("paraphrase", "How do I run a callback a single time?")
    assert class_findings(corpus, ok, truth(), once) == []
    page_word = question("paraphrase", "How do watchers fire?")
    assert class_findings(corpus, page_word, truth(), once) == [
        "paraphrase shares heading words ['watchers']"
    ]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_catalogue.py -q`
Expected: FAIL (`ImportError: cannot import name 'class_findings' from 'catalogue'`).

- [ ] **Step 3: Write the implementation**

In `src/catalogue.py` extend the config import to

```python
from config import (
    CATALOGUE_FOLD_MIN_LENGTH,
    CATALOGUE_STOPWORDS,
    CATALOGUE_WORD_PATTERN,
    DETAIL_MAX_ANSWER_WORDS,
    DOCUMENTS_FILE,
    SECTION_INDEX_FILE,
    SECTIONS_FILE,
)
```

add below `EXCERPT_CHARS`:

```python
WORD_RE = re.compile(CATALOGUE_WORD_PATTERN)
STOPWORDS = frozenset(CATALOGUE_STOPWORDS)
```

and append:

```python
def content_words(text: str) -> set[str]:
    """Lowercase words of text without stopwords (ADR 0029)."""
    return {w for w in WORD_RE.findall(text.lower()) if w not in STOPWORDS}


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


def shared_words(question: str, headings: list[str]) -> list[str]:
    """Question words that match a heading word, sorted."""
    heading_forms: set[str] = set()
    for heading in headings:
        for word in content_words(heading):
            heading_forms |= forms(word)
    return sorted(w for w in content_words(question) if forms(w) & heading_forms)


def heading_texts(corpus: Corpus, sections: list[dict]) -> list[str]:
    """Titles of the sections and of their pages: the heading words of a question (ADR 0029)."""
    return [title for s in sections for title in (s["title"], corpus.page_title(s))]


def class_findings(corpus: Corpus, question: dict, truth: dict, sections: list[dict]) -> list[str]:
    """Violations of the construction-class rules of ADR 0029 for one question."""
    cls, count = question["difficulty"], len(sections)
    found = []
    if cls == "multi-section":
        if count < 2:
            found.append(f"multi-section needs at least 2 relevant sections, has {count}")
    elif count != 1:
        found.append(f"{cls} needs exactly 1 relevant section, has {count}")
    if cls == "detail":
        words = len(truth["expected_answer"].split())
        if words > DETAIL_MAX_ANSWER_WORDS:
            found.append(f"detail answer has {words} words, at most {DETAIL_MAX_ANSWER_WORDS}")
    if cls == "paraphrase":
        shared = shared_words(question["question"], heading_texts(corpus, sections))
        if shared:
            found.append(f"paraphrase shares heading words {shared}")
    return found
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_catalogue.py -q`
Expected: 23 passed.

- [ ] **Step 5: Commit**

```bash
git add src/catalogue.py tests/test_catalogue.py
git commit -m "feat(catalogue): Wortvergleich und Regeln der Konstruktionsklassen"
```

---

### Task 4: Coverage check

**Files:**
- Modify: `src/catalogue.py`
- Modify: `tests/test_catalogue.py`

**Interfaces:**
- Consumes: Task 1–3 functions; `retrieve.read_rows`, `retrieve.relevant_sections`, `retrieve.QUESTIONS_HEADER`,
  `retrieve.QUESTIONS_REQUIRED`, `retrieve.GROUND_TRUTH_HEADER` (unchanged).
- Produces: `@dataclass class Report` with fields `errors: list[str]`, `findings: list[str]`, `lines: list[str]`,
  `types: dict[str, int]`, `classes: dict[str, int]`;
  `check(corpus: Corpus, questions_file: Path = QUESTIONS_FILE, ground_truth_file: Path = GROUND_TRUTH_FILE,
  pilot_dir: Path = PILOT_DIR) -> Report`; `exit_code(report: Report, draft: bool) -> int`;
  `normalised_question(text: str) -> str`.
- Produces (tests): helpers `write_catalogue(tmp_path, rows) -> tuple[Path, Path]` and `valid_rows() -> list[tuple]`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_catalogue.py` (add `import csv` at the top, `check, exit_code` to the catalogue import and
`from retrieve import GROUND_TRUTH_HEADER, QUESTIONS_HEADER`):

```python
def write_catalogue(tmp_path, rows):
    """rows: (question_id, question, type, difficulty, expected_answer, [section_ids])."""
    questions, truth_file = tmp_path / "questions.csv", tmp_path / "ground_truth.csv"
    with questions.open("w", encoding="utf-8", newline="") as qf, truth_file.open(
        "w", encoding="utf-8", newline=""
    ) as tf:
        qw, tw = csv.writer(qf, lineterminator="\n"), csv.writer(tf, lineterminator="\n")
        qw.writerow(QUESTIONS_HEADER)
        tw.writerow(GROUND_TRUTH_HEADER)
        for qid, text, qtype, cls, answer, sids in rows:
            qw.writerow([qid, text, qtype, cls, ""])
            docs = ";".join(dict.fromkeys(sid.split("#")[0] for sid in sids))
            tw.writerow([qid, answer, docs, ";".join(sids)])
    return questions, truth_file


def valid_rows():
    """A catalogue that meets every quota, floor and rule on the test corpus."""
    types = [t for t, n in QUESTION_TYPES.items() for _ in range(n)]
    classes = [c for c, n in QUESTION_CLASSES.items() for _ in range(n)]
    rows = []
    for i, (qtype, cls) in enumerate(zip(types, classes, strict=True)):
        if i < AREA_MIN_QUESTIONS["api"]:
            first = "D001#ref"
        elif i < AREA_MIN_QUESTIONS["api"] + AREA_MIN_QUESTIONS["style-guide"]:
            first = "D003#multi-word"
        else:
            first = "D002#once"
        sids = [first, "D002#cleanup"] if cls == "multi-section" else [first]
        rows.append((f"Q{i + 1:03d}", f"Question number zq{i}", qtype, cls, "Short answer.", sids))
    return rows


@pytest.fixture
def pilot(tmp_path):
    pilot_dir = tmp_path / "pilot"
    (pilot_dir / "hard").mkdir(parents=True)
    (pilot_dir / "hard" / "questions.csv").write_text(
        "question_id,question,type,difficulty,notes\n"
        "H01,How do I copy a pilot question?,factual,hard,pilot detail\n",
        encoding="utf-8",
    )
    return pilot_dir


def run_check(corpus, tmp_path, rows, pilot_dir):
    return check(corpus, *write_catalogue(tmp_path, rows), pilot_dir=pilot_dir)


def test_valid_catalogue_passes_strictly(corpus, tmp_path, pilot):
    report = run_check(corpus, tmp_path, valid_rows(), pilot)
    assert report.errors == [] and report.findings == []
    assert exit_code(report, draft=False) == 0
    assert report.types == QUESTION_TYPES and report.classes == QUESTION_CLASSES
    text = "\n".join(report.lines)
    assert "| total |" in text and "api 12 (at least 12)" in text


def test_format_errors_fail_even_in_draft(corpus, tmp_path, pilot):
    rows = valid_rows()
    rows[0] = (*rows[0][:5], ["D009#missing"])
    report = run_check(corpus, tmp_path, rows, pilot)
    assert any("unknown section IDs ['D009#missing']" in e for e in report.errors)
    assert exit_code(report, draft=True) == 1


def test_unknown_values_are_errors_by_question(corpus, tmp_path, pilot):
    rows = valid_rows()
    rows[0] = (rows[0][0], rows[0][1], "trivia", "hard", *rows[0][4:])
    report = run_check(corpus, tmp_path, rows, pilot)
    assert "Q001: unknown type 'trivia'" in "\n".join(report.errors)
    assert "Q001: unknown difficulty 'hard'" in "\n".join(report.errors)
    assert exit_code(report, draft=True) == 1


def test_quota_and_floor_findings_are_warnings_in_draft(corpus, tmp_path, pilot):
    report = run_check(corpus, tmp_path, valid_rows()[:20], pilot)
    assert report.errors == []
    joined = "\n".join(report.findings)
    assert "type factual: 12 questions, quota 12" not in joined
    assert "type procedural: 8 questions, quota 12" in joined
    assert "difficulty multi-section: 8 questions, quota 12" in joined
    assert "area style-guide: 3 questions, at least 3" not in joined
    assert exit_code(report, draft=True) == 0
    assert exit_code(report, draft=False) == 1


def test_area_floor_counts_cross_area_questions_for_each_area(corpus, tmp_path, pilot):
    rows = valid_rows()
    rows = [r for r in rows if not r[5][0].startswith("D003")]  # drop the style-guide questions
    report = run_check(corpus, tmp_path, rows, pilot)
    assert "area style-guide: 0 questions, at least 3" in report.findings


def test_class_rule_findings_carry_the_question_id(corpus, tmp_path, pilot):
    rows = valid_rows()
    index = next(i for i, r in enumerate(rows) if r[3] == "paraphrase")
    qid = rows[index][0]
    rows[index] = (qid, "How do watchers fire?", *rows[index][2:])
    report = run_check(corpus, tmp_path, rows, pilot)
    assert f"{qid}: paraphrase shares heading words ['watchers']" in report.findings


def test_duplicates_within_the_catalogue_and_against_pilots(corpus, tmp_path, pilot):
    rows = valid_rows()
    rows[1] = (rows[1][0], "question NUMBER zq0!", *rows[1][2:])
    rows[2] = (rows[2][0], "How do I copy a pilot question", *rows[2][2:])
    report = run_check(corpus, tmp_path, rows, pilot)
    assert "Q002: same question as Q001" in report.findings
    assert "Q003: same question as pilot hard/H01" in report.findings
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_catalogue.py -q`
Expected: FAIL (`ImportError: cannot import name 'check' from 'catalogue'`).

- [ ] **Step 3: Write the implementation**

In `src/catalogue.py`:
- add `from collections import Counter` and `from dataclasses import dataclass, field` to the imports;
- extend the config import with `AREA_MIN_QUESTIONS, GROUND_TRUTH_FILE, PILOT_DIR, QUESTION_CLASSES,
  QUESTION_TYPES, QUESTIONS_FILE` (keep it sorted, ruff's isort enforces it);
- add `from retrieve import GROUND_TRUTH_HEADER, QUESTIONS_HEADER, QUESTIONS_REQUIRED, read_rows,
  relevant_sections` after `from embed import load_jsonl`;
- append:

```python
@dataclass
class Report:
    """Result of the coverage check: errors always fail, findings only in strict mode."""

    errors: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)
    types: dict[str, int] = field(default_factory=dict)
    classes: dict[str, int] = field(default_factory=dict)


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
        f"{a} {areas[a]}" + (f" (at least {AREA_MIN_QUESTIONS[a]})" if a in AREA_MIN_QUESTIONS else "")
        for a in sorted(set(areas) | set(AREA_MIN_QUESTIONS))
    )
    lines += ["", f"Areas (questions with a relevant section there): {split}"]
    multi = [q for q in questions if q["difficulty"] == "multi-section"]
    spread = sum(1 for q in multi if len({s["doc_id"] for s in relevant[q["question_id"]]}) > 1)
    lines.append(f"multi-section on at least 2 pages: {spread} of {len(multi)}")
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
) -> Report:
    """Coverage check of the catalogue (ADR 0029); never reads retrieval results."""
    report = Report()
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
            report.errors.append(f"{qid}: unknown type {q['type']!r}; allowed {list(QUESTION_TYPES)}")
        if q["difficulty"] not in QUESTION_CLASSES:
            report.errors.append(
                f"{qid}: unknown difficulty {q['difficulty']!r}; allowed {list(QUESTION_CLASSES)}"
            )
            continue
        report.findings += [
            f"{qid}: {m}" for m in class_findings(corpus, q, truth[qid], relevant[qid])
        ]

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
        rows = read_rows(path, "pilot questions", QUESTIONS_HEADER, QUESTIONS_REQUIRED)
        for row in rows:
            key = normalised_question(row["question"])
            if key in seen:
                where = f"{label}/{row['question_id']}" if label != "." else row["question_id"]
                report.findings.append(f"{seen[key]}: same question as pilot {where}")

    report.lines = _overview(corpus, questions, truth, relevant, areas)
    return report


def exit_code(report: Report, draft: bool) -> int:
    """1 on any error; findings fail only the strict check (and therefore the freeze)."""
    return int(bool(report.errors) or (not draft and bool(report.findings)))
```

Note: `_table` counts only allowed values; questions with an unknown value appear in the errors and in the
`Questions:` total, so the table total and the overall total differ exactly when an error is reported.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_catalogue.py -q`
Expected: 30 passed.

- [ ] **Step 5: Commit**

```bash
git add src/catalogue.py tests/test_catalogue.py
git commit -m "feat(catalogue): Abdeckungsprüfung mit Quoten, Bereichen und Dubletten"
```

---

### Task 5: Freeze record and retrieval gate

**Files:**
- Create: `src/freeze.py`
- Modify: `src/catalogue.py` (add `freeze_catalogue`)
- Modify: `src/retrieve.py` (import, new parameter, gate call, docstring)
- Create: `tests/test_freeze.py`
- Modify: `tests/conftest.py` (shared catalogue fixtures move here)
- Modify: `tests/test_catalogue.py` (imports the moved helpers)
- Modify: `tests/test_retrieve.py` (three tests)

**Interfaces:**
- Consumes: `check`, `exit_code`, `Report` (Task 4); `run_log.sha256_of`.
- Produces: `freeze.write_freeze(questions_file: Path, ground_truth_file: Path, freeze_file: Path =
  CATALOGUE_FREEZE_FILE, summary: dict | None = None) -> dict`;
  `freeze.is_main_catalogue(questions_file: Path, ground_truth_file: Path) -> bool`;
  `freeze.require_frozen(questions_file: Path, ground_truth_file: Path, freeze_file: Path = CATALOGUE_FREEZE_FILE)
  -> None` (raises `RuntimeError`);
  `catalogue.freeze_catalogue(corpus: Corpus, questions_file: Path = QUESTIONS_FILE, ground_truth_file: Path =
  GROUND_TRUTH_FILE, freeze_file: Path = CATALOGUE_FREEZE_FILE, pilot_dir: Path = PILOT_DIR) -> dict`
  (raises `ValueError` when the strict check fails);
  `retrieve.retrieve(..., freeze_file: Path = CATALOGUE_FREEZE_FILE)`.

- [ ] **Step 1: Move the shared test helpers, then write the failing tests**

Move `PAGES`, `build_corpus`, the fixtures `corpus_files`, `corpus` and `pilot`, and the helpers `write_catalogue`
and `valid_rows` (with their imports) unchanged from `tests/test_catalogue.py` to `tests/conftest.py`; pytest shares
fixtures through `conftest.py`, and helper functions are imported from it as `test_retrieve.py` already does
(`from conftest import FakeEmbedder`). In `tests/test_catalogue.py` add
`from conftest import PAGES, build_corpus, valid_rows, write_catalogue` and remove the moved code. Run
`uv run pytest tests/test_catalogue.py -q`: 30 passed, unchanged.

Create `tests/test_freeze.py`:

```python
import json

import pytest
from conftest import valid_rows, write_catalogue

import freeze
from catalogue import freeze_catalogue
from run_log import sha256_of


@pytest.fixture
def main_catalogue(tmp_path, monkeypatch):
    questions, truth = write_catalogue(tmp_path, valid_rows())
    monkeypatch.setattr(freeze, "QUESTIONS_FILE", questions)
    monkeypatch.setattr(freeze, "GROUND_TRUTH_FILE", truth)
    return questions, truth


def test_freeze_writes_hashes_counts_and_date(corpus, main_catalogue, pilot, tmp_path):
    questions, truth = main_catalogue
    out = tmp_path / "catalogue_freeze.json"
    record = freeze_catalogue(corpus, questions, truth, out, pilot)
    stored = json.loads(out.read_text(encoding="utf-8"))
    assert stored == record
    assert stored["sha256"] == {"questions.csv": sha256_of(questions), "ground_truth.csv": sha256_of(truth)}
    assert stored["questions"] == 48 and stored["types"]["comparative"] == 6
    assert set(stored) == {"date", "questions", "types", "classes", "sha256"}


def test_freeze_refuses_a_failing_catalogue_and_writes_nothing(corpus, tmp_path, pilot):
    questions, truth = write_catalogue(tmp_path, valid_rows()[:47])
    out = tmp_path / "catalogue_freeze.json"
    with pytest.raises(ValueError, match="strict check"):
        freeze_catalogue(corpus, questions, truth, out, pilot)
    assert not out.exists()


def test_freeze_never_overwrites_a_record(corpus, main_catalogue, pilot, tmp_path):
    out = tmp_path / "catalogue_freeze.json"
    freeze_catalogue(corpus, *main_catalogue, out, pilot)
    before = out.read_bytes()
    with pytest.raises(FileExistsError, match="ADR 0030"):
        freeze_catalogue(corpus, *main_catalogue, out, pilot)
    assert out.read_bytes() == before


def test_require_frozen_ignores_other_catalogues(tmp_path):
    other_q, other_t = tmp_path / "q.csv", tmp_path / "t.csv"
    freeze.require_frozen(other_q, other_t, tmp_path / "missing.json")  # no error, no file read


def test_require_frozen_refuses_missing_record(main_catalogue, tmp_path):
    with pytest.raises(RuntimeError, match="not frozen"):
        freeze.require_frozen(*main_catalogue, tmp_path / "missing.json")


def test_require_frozen_refuses_changed_file(main_catalogue, tmp_path):
    out = tmp_path / "freeze.json"
    freeze.write_freeze(*main_catalogue, out)
    questions, truth = main_catalogue
    truth.write_text(truth.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="ground_truth.csv changed since the freeze"):
        freeze.require_frozen(questions, truth, out)


def test_require_frozen_refuses_mixed_paths(main_catalogue, tmp_path):
    out = tmp_path / "freeze.json"
    freeze.write_freeze(*main_catalogue, out)
    other_truth = tmp_path / "other" / "ground_truth.csv"
    other_truth.parent.mkdir()
    other_truth.write_text("question_id,expected_answer,relevant_doc_ids,relevant_section_ids\n")
    with pytest.raises(RuntimeError, match="changed since the freeze"):
        freeze.require_frozen(main_catalogue[0], other_truth, out)
```

Append to `tests/test_retrieve.py` (add `import freeze` to the imports):

```python
@pytest.fixture
def as_main_catalogue(setup, monkeypatch):
    paths = setup[0]
    monkeypatch.setattr(freeze, "QUESTIONS_FILE", paths["questions_file"])
    monkeypatch.setattr(freeze, "GROUND_TRUTH_FILE", paths["ground_truth_file"])
    return setup


def test_main_catalogue_needs_a_freeze_before_any_api_call(as_main_catalogue, tmp_path):
    paths, _, _, fake = as_main_catalogue
    with pytest.raises(RuntimeError, match="not frozen"):
        retrieve(embedder=fake, freeze_file=tmp_path / "freeze.json", **paths)
    assert fake.calls == [] and not paths["out_file"].exists()


def test_main_catalogue_runs_when_frozen(as_main_catalogue, tmp_path):
    paths, _, _, fake = as_main_catalogue
    record = tmp_path / "freeze.json"
    freeze.write_freeze(paths["questions_file"], paths["ground_truth_file"], record)
    assert retrieve(embedder=fake, freeze_file=record, **paths) > 0


def test_main_catalogue_changed_after_freeze_is_refused(as_main_catalogue, tmp_path):
    paths, _, _, fake = as_main_catalogue
    record = tmp_path / "freeze.json"
    freeze.write_freeze(paths["questions_file"], paths["ground_truth_file"], record)
    q = paths["questions_file"]
    q.write_text(q.read_text(encoding="utf-8").replace("How do watchers", "How do Watchers"))
    with pytest.raises(RuntimeError, match="questions.csv changed since the freeze"):
        retrieve(embedder=fake, freeze_file=record, **paths)
    assert fake.calls == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_freeze.py tests/test_retrieve.py -q`
Expected: FAIL (`ModuleNotFoundError: No module named 'freeze'`).

- [ ] **Step 3: Write `src/freeze.py`**

```python
"""Freeze record of the question catalogue (ADR 0030).

`write_freeze` records the SHA-256 of questions.csv and ground_truth.csv after the strict
coverage check passed (src/catalogue.py freeze). `require_frozen` lets retrieval use the main
catalogue only while both files still match that record, so the ground truth is final before
any retrieval (ADR 0017, 0027). Other catalogues (pilot sets, tests) are not affected.
"""

import json
from datetime import date
from pathlib import Path

from config import CATALOGUE_FREEZE_FILE, GROUND_TRUTH_FILE, QUESTIONS_FILE
from run_log import sha256_of


def write_freeze(
    questions_file: Path,
    ground_truth_file: Path,
    freeze_file: Path = CATALOGUE_FREEZE_FILE,
    summary: dict | None = None,
) -> dict:
    """Write the record once; an existing record is never overwritten."""
    if freeze_file.exists():
        raise FileExistsError(
            f"{freeze_file} exists: the catalogue is frozen. A new freeze needs a new ADR and "
            "deleting the record by hand (ADR 0030)"
        )
    record = {
        "date": date.today().isoformat(),
        **(summary or {}),
        "sha256": {
            questions_file.name: sha256_of(questions_file),
            ground_truth_file.name: sha256_of(ground_truth_file),
        },
    }
    freeze_file.parent.mkdir(parents=True, exist_ok=True)
    freeze_file.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


def is_main_catalogue(questions_file: Path, ground_truth_file: Path) -> bool:
    """True if either file is the experiment's catalogue (config.QUESTIONS_FILE/GROUND_TRUTH_FILE)."""
    main = {QUESTIONS_FILE.resolve(), GROUND_TRUTH_FILE.resolve()}
    return bool({questions_file.resolve(), ground_truth_file.resolve()} & main)


def require_frozen(
    questions_file: Path, ground_truth_file: Path, freeze_file: Path = CATALOGUE_FREEZE_FILE
) -> None:
    """Raise unless the main catalogue is frozen and unchanged; other catalogues pass."""
    if not is_main_catalogue(questions_file, ground_truth_file):
        return
    if not freeze_file.exists():
        raise RuntimeError(
            "the question catalogue is not frozen; run `uv run python src/catalogue.py freeze` "
            "first (ADR 0030)"
        )
    record = json.loads(freeze_file.read_text(encoding="utf-8"))
    for path in (questions_file, ground_truth_file):
        if record["sha256"].get(path.name) != sha256_of(path):
            raise RuntimeError(
                f"{path.name} changed since the freeze on {record['date']} (ADR 0030)"
            )
```

- [ ] **Step 4: Add `freeze_catalogue` to `src/catalogue.py`**

Extend the config import with `CATALOGUE_FREEZE_FILE`, add `from freeze import write_freeze` after
`from embed import load_jsonl`, and append:

```python
def freeze_catalogue(
    corpus: Corpus,
    questions_file: Path = QUESTIONS_FILE,
    ground_truth_file: Path = GROUND_TRUTH_FILE,
    freeze_file: Path = CATALOGUE_FREEZE_FILE,
    pilot_dir: Path = PILOT_DIR,
) -> dict:
    """Strict check, then the freeze record (ADR 0030); nothing is written if the check fails."""
    report = check(corpus, questions_file, ground_truth_file, pilot_dir)
    if exit_code(report, draft=False):
        raise ValueError(
            "the catalogue does not pass the strict check; run `src/catalogue.py check`"
        )
    summary = {
        "questions": sum(report.classes.values()),
        "types": report.types,
        "classes": report.classes,
    }
    return write_freeze(questions_file, ground_truth_file, freeze_file, summary)
```

- [ ] **Step 5: Gate `retrieve()`**

In `src/retrieve.py`:
- add `CATALOGUE_FREEZE_FILE,` to the `from config import (...)` list (alphabetical, before `CHROMA_COLLECTIONS`);
- add `from freeze import require_frozen` after `from embedding_client import Embedder, embed_texts`;
- add the parameter `freeze_file: Path = CATALOGUE_FREEZE_FILE,` after `collections: dict[str, str] =
  CHROMA_COLLECTIONS,` in the signature of `retrieve`;
- insert as the first statement of the body, before `if strategies not in (STRATEGY_IDS, CONTROL_STRATEGIES):`:

```python
    require_frozen(questions_file, ground_truth_file, freeze_file)  # ADR 0030, before any API call
```

- in the module docstring, after the sentence ending "can be checked later (ADR 0017).", add:
  "The main catalogue (config.QUESTIONS_FILE/GROUND_TRUTH_FILE) is used only while it matches its freeze record
  (src/freeze.py, ADR 0030)."

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_freeze.py tests/test_retrieve.py tests/test_difficulty_probe.py -q`
Expected: all pass (7 in `test_freeze.py`, the existing `test_retrieve.py` tests plus 3 new ones,
`test_difficulty_probe.py` unchanged).

- [ ] **Step 7: Run the whole suite and Pyright**

Run: `uv run pytest -q && uv run pyright src tests scripts`
Expected: all tests pass; `0 errors`.

- [ ] **Step 8: Commit**

```bash
git add src/freeze.py src/catalogue.py src/retrieve.py tests/test_freeze.py tests/test_retrieve.py
git commit -m "feat(catalogue): Einfrieren des Fragenkatalogs und Sperre im Retrieval"
```

---

### Task 6: Command line and real-corpus integration

**Files:**
- Modify: `src/catalogue.py` (add `main`)
- Modify: `tests/test_corpus_integration.py`
- Modify: `tests/test_catalogue.py` (CLI tests)

**Interfaces:**
- Consumes: everything above.
- Produces: `main(argv: list[str] | None = None) -> int`; `python src/catalogue.py <command>`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_catalogue.py` (add `main` to the import; `import catalogue` at the top):

```python
@pytest.fixture
def cli(corpus_files, tmp_path, monkeypatch, pilot):
    docs_file, sections_file = corpus_files
    monkeypatch.setattr(catalogue, "DOCUMENTS_FILE", docs_file)
    monkeypatch.setattr(catalogue, "SECTIONS_FILE", sections_file)
    monkeypatch.setattr(catalogue, "SECTION_INDEX_FILE", tmp_path / "section_index.md")
    questions, truth = write_catalogue(tmp_path, valid_rows())
    monkeypatch.setattr(catalogue, "QUESTIONS_FILE", questions)
    monkeypatch.setattr(catalogue, "GROUND_TRUTH_FILE", truth)
    monkeypatch.setattr(catalogue, "PILOT_DIR", pilot)
    monkeypatch.setattr(catalogue, "CATALOGUE_FREEZE_FILE", tmp_path / "freeze.json")
    return tmp_path


def test_cli_sections_find_show(cli, capsys):
    assert main(["sections"]) == 0
    assert (cli / "section_index.md").exists()
    assert main(["find", "callback only"]) == 0
    assert "D002#once" in capsys.readouterr().out
    assert main(["show", "D009#x"]) == 1
    assert "unknown section D009#x" in capsys.readouterr().err


def test_cli_check_and_freeze(cli, capsys):
    assert main(["check"]) == 0
    assert main(["freeze"]) == 0
    assert (cli / "freeze.json").exists()
    assert main(["freeze"]) == 1
    assert "ADR 0030" in capsys.readouterr().err
```

`main` must read the module globals at call time (not as default arguments) so the monkeypatched paths apply.

Append to `tests/test_corpus_integration.py` (imports: `from catalogue import find, load_corpus, section_index`):

```python
@pytest.mark.skipif(not SECTIONS_FILE.exists(), reason="not preprocessed; run src/preprocess.py")
def test_section_index_covers_the_real_corpus():
    corpus = load_corpus()
    rows = [line for line in section_index(corpus).splitlines() if line.startswith("| `")]
    ids = [row.split("`")[1] for row in rows]
    assert len(rows) == len(corpus.sections) == 813
    assert all(sid in corpus.by_id for sid in ids)
    assert {row.split(" | ")[1] for row in rows} == {"api", "guide", "style-guide"}
    assert any(s["section_id"].startswith("D") for s, _ in find(corpus, "defineProps"))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_catalogue.py tests/test_corpus_integration.py -q`
Expected: FAIL (`ImportError: cannot import name 'main' from 'catalogue'`).

- [ ] **Step 3: Write `main`**

Add `import argparse` and `import sys` to the imports of `src/catalogue.py` and append:

```python
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
    args = parser.parse_args(argv)

    corpus = load_corpus(DOCUMENTS_FILE, SECTIONS_FILE)
    if args.command == "sections":
        count = write_section_index(corpus, SECTION_INDEX_FILE)
        print(f"{count} sections -> {SECTION_INDEX_FILE}")
        return 0
    if args.command == "find":
        hits = find(corpus, args.term)
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

    report = check(corpus, QUESTIONS_FILE, GROUND_TRUTH_FILE, PILOT_DIR)
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
            corpus, QUESTIONS_FILE, GROUND_TRUTH_FILE, CATALOGUE_FREEZE_FILE, PILOT_DIR
        )
    except (FileExistsError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"frozen on {record['date']} -> {CATALOGUE_FREEZE_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_catalogue.py tests/test_corpus_integration.py -q`
Expected: all pass (32 in `test_catalogue.py`; the integration test runs because `sections.jsonl` exists locally).

- [ ] **Step 5: Run the tools on the real corpus and read the output**

```bash
uv run python src/catalogue.py sections
head -8 data/processed/section_index.md
uv run python src/catalogue.py find "v-model.lazy"
uv run python src/catalogue.py show "$(uv run python src/catalogue.py find defineProps | head -1 | cut -d' ' -f1)" | head -5
uv run python src/catalogue.py check --draft; echo "exit $?"
uv run python src/retrieve.py; echo "exit $?"
```

Expected: `813 sections -> …/section_index.md`; the table header and first rows; at least one hit for `v-model.lazy`
in the guide; a section heading line with a token count; `check --draft` prints one `ERROR` ("has no rows", the
catalogue is still empty) and `exit 1`; `retrieve.py` aborts with "the question catalogue is not frozen" and
`exit 1` without any API call (no new line in `data/processed/embedding_runs.jsonl`: compare `wc -l` before and
after).

- [ ] **Step 6: Whole suite, offline and strict**

Run: `uv run pytest -q -W error::DeprecationWarning && uv run pyright src tests scripts && uvx pre-commit run --all-files`
Expected: all pass, `0 errors`, all hooks pass.

- [ ] **Step 7: Commit**

```bash
git add src/catalogue.py tests/test_catalogue.py tests/test_corpus_integration.py
git commit -m "feat(catalogue): Kommandozeile und Integrationstest auf dem echten Korpus"
```

---

### Task 7: Decisions and documentation

**Files:**
- Create: `docs/adr/0029-fragetypen-und-konstruktionsklassen.md`
- Create: `docs/adr/0030-einfrieren-des-fragenkatalogs.md`
- Create: `docs/how-to/build-the-question-catalogue.md`
- Modify: `docs/adr/0017-fragenkatalog.md` (status line only), `docs/adr/README.md`,
  `docs/reference/question-catalogue.md`, `docs/reference/data-formats.md`, `docs/reference/configuration.md`,
  `docs/reference/tooling.md`, `docs/plan.md`, `docs/README.md`, `AGENTS.md` (map line "decisions D1–D28"),
  `.serena/memories/core.md` (or the memory that lists next steps)

**Interfaces:**
- Consumes: final names and values from Tasks 1–6.

- [ ] **Step 1: ADR 0029**

Create `docs/adr/0029-fragetypen-und-konstruktionsklassen.md`:

```markdown
# 0029. Fragetypen, Konstruktionsklassen und Quoten des Fragenkatalogs

## Status

Angenommen (14.10.2026; präzisiert [ADR 0017](0017-fragenkatalog.md))

## Kontext

- ADR 0017 legt etwa 40 Fragen (30–60) in fünf Typen im Verhältnis 2:2:2:1:1 fest; das Exposé nennt „etwa 40 Fragen“.
  H3 ([ADR 0009](0009-hypothesen.md)) braucht neben dem Typ die Unterscheidung abschnittsübergreifender Fragen.
- Pilotprobe 2 ([Experiment-Protokoll](../reference/experiment-record.md#pilotproben-auf-dem-erweiterten-korpus-14102026)):
  Einfache Fragen erreichen bei allen Strategien Hit@5 = 1,0 (Deckeneffekt); die Konstruktion der Frage
  (mehrere Abschnitte, Detail, Paraphrase) trennt C3 und K1.
- Eine subjektive Schwierigkeit (leicht/mittel/schwer) ist nicht prüfbar; eine Konstruktionsklasse lässt sich gegen die
  eigene Annotation prüfen, ohne Retrieval-Ergebnisse ([ADR 0027](0027-blinde-annotation.md)).
- Messungen: H2/H3-Abschnitte Median 211 Tokens (p25 120, p75 356); die relevanten Abschnitte der Pilot-Detailfragen
  sind 22–546 Tokens lang (Detail ist eine Eigenschaft der Antwort, nicht der Abschnittslänge); 5 von 7
  Pilot-Paraphrasen teilen kein Wort mit der Überschrift.
- Korpusanteile ([ADR 0025](0025-korpus-guide-api-styleguide.md)): Guide 71 %, API 26 %, Style Guide 3 % der Tokens.
- Umfang: Der Standardfehler eines Mittelwerts sinkt mit √n. 48 statt 40 Fragen senken ihn um etwa 9 %; mit 12 Fragen
  je Klasse sind bei gepaartem Vergleich (80 % Power, α = 0,05) nur große Effekte (d ≈ 0,89) erkennbar, über alle
  48 Fragen d ≈ 0,41. Mehraufwand gegenüber 40: etwa 8 Stunden Fragen und Annotation, 24 Antworten mehr zu bewerten.

## Entscheidung

Wir werden 48 Fragen erstellen: `type` ∈ {`factual`, `procedural`, `conceptual`, `comparative`, `limitation`} mit
12/12/12/6/6 Fragen und `difficulty` als Konstruktionsklasse ∈ {`single`, `multi-section`, `detail`, `paraphrase`}
mit je 12 Fragen.
Wir werden die Klassen so definieren: `single` genau ein relevanter Abschnitt, dessen Hauptinhalt die Antwort ist;
`multi-section` mindestens zwei relevante Abschnitte, die alle nötig sind; `detail` genau ein Abschnitt, die Antwort
ist ein einzelnes Faktum (Referenzantwort höchstens 30 Wörter); `paraphrase` genau ein Abschnitt, die Frage teilt kein
Inhaltswort mit dem Titel des Abschnitts oder seiner Seite.
Wir werden Wörter so vergleichen: Kleinschreibung, Wörter `[a-z0-9]+`, ohne Stoppwörter (`config.CATALOGUE_STOPWORDS`);
Wörter ab vier Zeichen stehen auch ohne Endung `s`/`es` und mit `ies` → `y`; zwei Wörter gelten als gleich, wenn sich
diese Formen überschneiden.
Wir werden mindestens 12 Fragen mit einem relevanten Abschnitt in der API-Referenz und mindestens 3 im Style Guide
verlangen; eine Frage zählt für jeden Bereich, den sie berührt.
Werte und Grenzen stehen in [`src/config.py`](../../src/config.py); `src/catalogue.py check` prüft sie.

## Konsequenzen

- Gut: H3 lässt sich nach Typ und nach Konstruktion auswerten; die Klassen sind vor jedem Retrieval festgelegt und
  maschinell geprüft.
- Gut: Der Deckeneffekt einfacher Fragen bleibt sichtbar (`single` als Referenzgruppe), statt den Katalog zu prägen.
- Neutral: 48 statt „etwa 40“ Fragen; die Arbeit nennt die Abweichung vom Exposé und ihren Grund.
- Schlecht: Je Klasse sind nur große Effekte erkennbar; Ergebnisse je Klasse bleiben explorativ (ADR 0009).
- Schlecht: Der Wortvergleich ist bewusst grob; er meldet eher zu viel Überlappung, und die Kleinheit eines Details
  bleibt ein Urteil (die Prüfung zeigt Abschnitts- und Antwortlänge an).
```

- [ ] **Step 2: ADR 0030**

Create `docs/adr/0030-einfrieren-des-fragenkatalogs.md`:

```markdown
# 0030. Einfrieren des Fragenkatalogs als technische Sperre

## Status

Angenommen (14.10.2026; setzt [ADR 0017](0017-fragenkatalog.md) und [ADR 0027](0027-blinde-annotation.md) technisch um)

## Kontext

- Ground Truth und Relevanz-Annotation müssen vor jedem Retrieval feststehen (ADR 0017, 0027). Bisher ist das eine
  Zusage; das Laufprotokoll von `retrieve.py` zeigt erst nachträglich, mit welchen Dateien gerechnet wurde.
- Meilenstein 09.11.2026: Ground Truth eingefroren ([ADR 0028](0028-c4-bedingung.md)).

## Entscheidung

Wir werden den Katalog mit `src/catalogue.py freeze` einfrieren: Nur wenn die strenge Prüfung (ADR 0029) besteht,
schreibt der Befehl `data/evaluation/catalogue_freeze.json` mit Datum, Anzahlen je Typ und Klasse und den SHA-256 von
`questions.csv` und `ground_truth.csv`; ein vorhandener Datensatz wird nie überschrieben.
Wir werden `retrieve.py` auf dem Hauptkatalog (`config.QUESTIONS_FILE`, `config.GROUND_TRUTH_FILE`) nur laufen lassen,
wenn beide Prüfsummen zum Datensatz passen; die Prüfung steht vor jedem API-Aufruf. Pilot-Sets sind nicht betroffen.
Ein erneutes Einfrieren braucht ein neues ADR mit Begründung und das Löschen des Datensatzes von Hand.

## Konsequenzen

- Gut: „Ground Truth vor Retrieval“ ist im Code erzwungen und mit Datum belegt; der Datensatz ist versioniert und
  zitierfähig.
- Neutral: Generierung und Bewertung bauen auf den Retrieval-Ergebnissen auf und erben die Sperre.
- Schlecht: Eine Korrektur nach dem Einfrieren (z. B. ein Tippfehler) braucht ein ADR; das ist gewollt.
```

- [ ] **Step 3: Update the existing pages**

Make these exact edits (German, like the surrounding text):

1. `docs/adr/0017-fragenkatalog.md`, Status line: append `; Typen, Klassen und Quoten in [ADR 0029](0029-fragetypen-und-konstruktionsklassen.md), Einfrieren in [ADR 0030](0030-einfrieren-des-fragenkatalogs.md)`.
2. `docs/adr/README.md`: add rows for 0029 and 0030 in the index table, same format as the 0028 row; change any
   "D1–D28" to "D1–D30".
3. `docs/reference/question-catalogue.md`:
   - "**Umfang:**" line → `**Umfang:** 48 Fragen ([ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md),
     im Rahmen von [ADR 0017](../adr/0017-fragenkatalog.md): 30–60).`
   - Type table: column "Anzahl" → 12/12/12/6/6; add a column `Wert` with `factual`, `procedural`, `conceptual`,
     `comparative`, `limitation`; replace the comparative example by
     `What is the difference between ref() and reactive()?`.
   - Replace "Die erlaubten Werte von `type` und `difficulty` sind noch offen ([Plan](../plan.md))." by a table of
     the four construction classes (value, rule, count 12) exactly as in ADR 0029, the area floors (API ≥ 12, Style
     Guide ≥ 3) and the sentence "Geprüft mit `src/catalogue.py check`; Ablauf:
     [Fragenkatalog erstellen](../how-to/build-the-question-catalogue.md)."
4. `docs/reference/data-formats.md`, section "Fragen und Ground Truth": after the `questions.csv` example add
   "`type` und `difficulty` nehmen nur die Werte aus [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md)
   an (`config.QUESTION_TYPES`, `config.QUESTION_CLASSES`); die Pilot-Sets sind davon ausgenommen." Change the
   example row to `Q001,"What is the difference between ref and reactive in Vue?",comparative,multi-section,`.
   Add two subsections at the end of the section: `section_index.md` (generated Markdown table: `section_id`, area,
   path, heading path, tokens; not versioned, in `data/processed/`) and `catalogue_freeze.json` (example:
   `{"date": "2026-11-09", "questions": 48, "types": {...}, "classes": {...}, "sha256": {"questions.csv": "…",
   "ground_truth.csv": "…"}}`; versioned; ADR 0030).
5. `docs/reference/configuration.md`: rows for `SECTION_INDEX_FILE` (after `SECTIONS_FILE`) and
   `CATALOGUE_FREEZE_FILE` (after `GROUND_TRUTH_FILE`) in "Pfade"; a new section "## Fragenkatalog" after the
   relevance keys with rows for `QUESTION_TYPES`, `QUESTION_CLASSES`, `AREA_MIN_QUESTIONS`,
   `DETAIL_MAX_ANSWER_WORDS`, `CATALOGUE_WORD_PATTERN`, `CATALOGUE_FOLD_MIN_LENGTH`, `CATALOGUE_STOPWORDS`
   (value, meaning, ADR 0029/0030), same column layout as the other sections.
6. `docs/reference/tooling.md`: add `src/catalogue.py` and `src/freeze.py` to the file tree and a table row for
   `src/catalogue.py` with its five subcommands and `--draft`; add to the `retrieve.py` row: "bricht auf dem
   Hauptkatalog ohne passenden Freeze-Datensatz ab (ADR 0030)".
7. New `docs/how-to/build-the-question-catalogue.md` (Seitentyp how-to): steps 1) `uv run python src/catalogue.py
   sections` and open `data/processed/section_index.md`; 2) write a question into `data/evaluation/questions.csv`
   with `type` and `difficulty`; 3) find all relevant sections with `find`/`show`, also in the API reference, before
   any retrieval, and note them in `ground_truth.csv`; 4) `check --draft` after each batch; 5) when all 48 are done,
   `check` (strict) and `freeze`, then commit `catalogue_freeze.json` together with both CSV files. Link ADR 0027,
   0029, 0030 and the reference page.
8. `docs/README.md`: link the new how-to in the how-to list.
9. `docs/plan.md`: in "## Stand" replace "Nächster Schritt: Werkzeuge für den Fragenkatalog (siehe [Offene
   Entscheidungen](#offene-entscheidungen--vor-beginn-zu-bestätigen))." by "Fragenkatalog-Werkzeuge umgesetzt
   (`src/catalogue.py`, [ADR 0029](adr/0029-fragetypen-und-konstruktionsklassen.md),
   [ADR 0030](adr/0030-einfrieren-des-fragenkatalogs.md)). Nächster Schritt: 48 Fragen schreiben und annotieren,
   Einfrieren bis 09.11.2026." In "Offene Entscheidungen" replace the bullet "Fragenkatalog-Werkzeuge (vereinbart
   14.10.2026) …" by "**Fragenkatalog:** entschieden: 48 Fragen, Typen und Klassen mit Quoten
   ([ADR 0029](adr/0029-fragetypen-und-konstruktionsklassen.md)), Einfrieren als Sperre
   ([ADR 0030](adr/0030-einfrieren-des-fragenkatalogs.md))."
10. `AGENTS.md`: map line "`docs/adr/` — decisions D1–D28" → "D1–D30".
11. Serena memory with the project status (`.serena/memories/core.md` or the one that names next steps): replace the
    next-step line by a 1–2 line summary pointing to `docs/plan.md#stand` and the how-to.

- [ ] **Step 4: Validate links and claims**

Run:

```bash
uv run python - <<'EOF'
import re, pathlib
bad = []
for md in pathlib.Path(".").rglob("*.md"):
    if any(p in md.parts for p in (".venv", "node_modules", "data")):
        continue
    for target in re.findall(r"\]\(([^)#\s]+)", md.read_text(encoding="utf-8")):
        if target.startswith(("http", "mailto")):
            continue
        if not (md.parent / target).resolve().exists():
            bad.append(f"{md}: {target}")
print("\n".join(bad) or "all links resolve")
EOF
grep -rn "noch offen\|D1–D28\|10/10/10/5/5\|Options API and the Composition API" docs AGENTS.md README.md .serena/memories || echo "no stale claims"
```

Expected: `all links resolve`; `no stale claims`.

- [ ] **Step 5: Commit**

```bash
git add docs AGENTS.md .serena/memories
git commit -m "docs: Fragenkatalog-Werkzeuge, ADR 0029 und 0030"
```

---

## After the last task

- Final whole-branch review (top tier), then push, open the PR against `main`, comment `@codex review`, act on its
  findings, merge only after Jonas approves, then bump the PaperLab pointer to the merge commit on `main`.
