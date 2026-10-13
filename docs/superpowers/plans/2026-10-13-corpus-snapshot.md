# Corpus Snapshot, Ingest and Preprocessing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `vuejs/docs` `src/guide/` at the pinned commit into a Composition-API-only `documents.jsonl`, a
`sections.jsonl` with token spans per anchored section, and `docs/corpus_manifest.csv`.

**Architecture:** Four small modules in `src/`: `tokens.py` (shared `cl100k_base` tokenisation), `snapshot.py`
(shallow git fetch + copy + checksums), `ingest.py` (raw Markdown → `documents.jsonl`), `preprocess.py` (line-based
state machine that tracks code fences and HTML block depth, then section spans and manifest). Every step persists its
artefact; every corpus anomaly raises instead of being skipped.

**Tech Stack:** Python 3.13 via uv, tiktoken 0.13.0, pytest, git (CLI), ruff via pre-commit.

**Verification of this plan:** all code below was applied to a throwaway clone on 13.10.2026: pre-commit clean,
45 tests passing, real pipeline run on the pinned commit (52 documents, 560 sections, 139,342 tokens).

**Spec:** `docs/superpowers/specs/2026-10-13-corpus-snapshot-design.md` (decision: `docs/adr/0019-korpus-ausschnitt.md`).

## Global Constraints

- All parameters (paths, commit, encoding, thresholds) live only in `src/config.py`.
- Commit `b75d188ab16bf83bd1f364a77dfd2315be8f3fa4`, subdir `src/guide`, encoding `cl100k_base`, `tiktoken==0.13.0`.
- `documents.jsonl` keys exactly `doc_id, path, title, text, tokens` in that order (`docs/reference/data-formats.md`).
- `section_id = {doc_id}#{anchor}`; sections are H1–H3; spans `[start_token, end_token)` in the cleaned text.
- Manifest header exactly `file_id,path,title,section,tokens,included`.
- No OpenAI calls. No personal data in code, tests or commits (public repo); test git identities use `example.invalid`.
- Scripts are run from the repo root as `uv run python src/<step>.py`; modules import siblings as top-level
  (`from config import …`, `import tokens`); pytest gets `pythonpath = ["src"]`.
- Conventional Commits, no AI attribution lines; run `uvx pre-commit run --all-files` before each commit; push after
  each task.

## Review Focus

- Re-running `preprocess.py` on an already cleaned `documents.jsonl` must stop with a message to re-run `ingest.py`,
  not crash on "heading without anchor" or double-clean (test in Task 3).
- `class="options-api"` markup inside a code fence is documentation content and must survive unchanged (Task 2).
- Inline code such as `` `<div>` `` or `` `</div>` `` in prose must not change HTML block depth (Task 2).
- Re-running `snapshot.py` must remove stale files from an earlier snapshot but keep `data/raw/vue_docs_snapshot/.gitkeep` (Task 5).
- Running `ingest.py` before `snapshot.py` (empty snapshot folder) must fail with a hint to run `snapshot.py` (Task 4).

---

### Task 1: Configuration, dependencies and `tokens.py`

**Files:**
- Modify: `src/config.py` (paths block and two new blocks)
- Modify: `pyproject.toml`
- Create: `src/tokens.py`
- Test: `tests/test_tokens.py`

**Interfaces:**
- Produces: `config.SNAPSHOT_INFO_FILE: Path`, `config.SECTIONS_FILE: Path`, `config.CORPUS_MANIFEST_FILE: Path`,
  `config.VUE_DOCS_REPO_URL: str`, `config.VUE_DOCS_COMMIT: str`, `config.VUE_DOCS_SUBDIR: str`,
  `config.TOKEN_ENCODING: str`, `config.RELEVANCE_MIN_OVERLAP: int`, `config.SENSITIVITY_MIN_OVERLAP: int`;
  `tokens.encode(text: str) -> list[int]`, `tokens.count(text: str) -> int`,
  `tokens.decode(ids: list[int]) -> str`, `tokens.token_starts(text: str) -> list[int]`,
  `tokens.char_to_token(starts: list[int], char_offset: int) -> int`.

- [ ] **Step 1: Add config values**

In `src/config.py`, add to the paths section directly after `DOCUMENTS_FILE = DATA_PROCESSED / "documents.jsonl"`:

```python
SNAPSHOT_INFO_FILE = DATA_RAW / "SNAPSHOT.txt"
SECTIONS_FILE = DATA_PROCESSED / "sections.jsonl"
CORPUS_MANIFEST_FILE = DOCS_DIR / "corpus_manifest.csv"
```

Insert a new block before `# Chunking parameters (D5, D6)`:

```python
# ---------------------------------------------------------------------------
# Corpus (D19, docs/adr/0019-korpus-ausschnitt.md)
# ---------------------------------------------------------------------------
VUE_DOCS_REPO_URL = "https://github.com/vuejs/docs.git"
VUE_DOCS_COMMIT = "b75d188ab16bf83bd1f364a77dfd2315be8f3fa4"
VUE_DOCS_SUBDIR = "src/guide"
TOKEN_ENCODING = "cl100k_base"  # tiktoken 0.13.0, pinned in pyproject.toml

```

Append to the `# Retrieval parameters (D14)` block, after `TOP_K = 5 …`:

```python

# A chunk counts as relevant if its token span overlaps a relevant section by at least
# this many tokens (D19).
RELEVANCE_MIN_OVERLAP = 1
SENSITIVITY_MIN_OVERLAP = 100  # sensitivity check for the retrieval evaluation
```

- [ ] **Step 2: Pin tiktoken, add pytest**

In `pyproject.toml` replace `"tiktoken>=0.7.0",` with `"tiktoken==0.13.0",  # pinned (ADR 0019)`, add
`"pytest>=8.0",` to the `dev` list in `[dependency-groups]`, and append:

```toml

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

Run: `uv lock && uv sync`
Expected: lock updates, tiktoken stays 0.13.0, pytest installed.

- [ ] **Step 3: Write the failing tests**

`tests/test_tokens.py`:

```python
import tokens


def test_count_matches_encode():
    assert tokens.count("Hello world") == len(tokens.encode("Hello world")) == 2


def test_special_token_text_is_plain_text():
    assert tokens.count("<|endoftext|>") > 1


def test_token_starts_are_sorted_and_one_per_token():
    text = "ref() and reactive()\n\n## Heading\n"
    starts = tokens.token_starts(text)
    assert starts[0] == 0
    assert starts == sorted(starts)
    assert len(starts) == tokens.count(text)


def test_char_to_token_bounds_and_heading_alignment():
    text = "# Title\n\nIntro.\n\n## A\n\ntext\n"
    starts = tokens.token_starts(text)
    assert tokens.char_to_token(starts, 0) == 0
    assert tokens.char_to_token(starts, len(text)) == len(starts)
    i = tokens.char_to_token(starts, text.index("## A"))
    assert tokens.decode(tokens.encode(text)[i:]).startswith("## A")


def test_decode_round_trip():
    text = "const count = ref(0)\n"
    assert tokens.decode(tokens.encode(text)) == text
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `uv run pytest tests/test_tokens.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'tokens'`

- [ ] **Step 5: Implement `src/tokens.py`**

```python
"""Token counting shared by ingest, preprocess and chunking (ADR 0019).

One encoding (config.TOKEN_ENCODING) for all steps, so chunk and section token spans share
one index space.
"""

from bisect import bisect_left
from functools import cache

import tiktoken

from config import TOKEN_ENCODING


@cache
def _encoding() -> tiktoken.Encoding:
    return tiktoken.get_encoding(TOKEN_ENCODING)


def encode(text: str) -> list[int]:
    """Token ids of text; special-token strings are treated as plain text."""
    return _encoding().encode(text, disallowed_special=())


def decode(ids: list[int]) -> str:
    """Text of a token id sequence."""
    return _encoding().decode(ids)


def count(text: str) -> int:
    """Number of tokens in text."""
    return len(encode(text))


def token_starts(text: str) -> list[int]:
    """Character offset at which each token of text starts."""
    _, offsets = _encoding().decode_with_offsets(encode(text))
    return offsets


def char_to_token(starts: list[int], char_offset: int) -> int:
    """Index of the first token starting at or after char_offset (len(starts) at the end)."""
    return bisect_left(starts, char_offset)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_tokens.py -q`
Expected: 5 passed

- [ ] **Step 7: Commit and push**

```bash
uvx pre-commit run --all-files
git add src/config.py src/tokens.py tests/test_tokens.py pyproject.toml uv.lock
git commit -m "feat(tokens): gemeinsame cl100k_base-Tokenisierung und Korpus-Konfiguration"
git push
```

---

### Task 2: `clean_markdown` in `preprocess.py`

**Files:**
- Modify: `src/preprocess.py` (replace the stub; `preprocess()` itself follows in Task 3)
- Test: `tests/test_clean_markdown.py`

**Interfaces:**
- Consumes: nothing from Task 1 at runtime except imports.
- Produces: `preprocess.Heading(level: int, title: str, anchor: str, offset: int)` (frozen dataclass),
  `preprocess.CleanResult(text: str, headings: list[Heading])`, `preprocess.clean_markdown(text: str) -> CleanResult`
  (raises `ValueError` on corpus anomalies).

- [ ] **Step 1: Write the failing tests**

`tests/test_clean_markdown.py`:

```python
import pytest

from preprocess import clean_markdown

DOC = "# Title {#title}\n\n"


def clean(body: str) -> str:
    return clean_markdown(DOC + body).text


def test_bom_and_frontmatter_removed():
    result = clean_markdown("﻿---\noutline: deep\n---\n\n# T {#t}\n\nBody\n")
    assert result.text == "# T\n\nBody\n"


def test_options_block_with_nested_div_dropped():
    body = '<div class="options-api">\n\nOpt\n<div>\ninner\n</div>\n</div>\n\nAfter\n'
    assert clean(body) == "# Title\n\nAfter\n"


def test_composition_block_unwrapped():
    assert clean('<div class="composition-api">\n\nComp\n\n</div>\n') == "# Title\n\nComp\n"


def test_options_and_composition_paragraphs():
    body = (
        '<p class="options-api">\nOpt para\n</p>\n\n<p class="composition-api">\nComp para\n</p>\n'
    )
    assert clean(body) == "# Title\n\nComp para\n"


def test_options_markup_inside_code_fence_survives():
    body = '```vue-html\n<div class="options-api">x</div>\n```\n'
    assert clean(body) == '# Title\n\n```vue-html\n<div class="options-api">x</div>\n```\n'


def test_inline_code_divs_do_not_change_depth():
    body = 'Use `<div>` here.\n\n<div class="composition-api">\n\nSee `</div>` too\n\n</div>\n'
    assert clean(body) == "# Title\n\nUse `<div>` here.\n\nSee `</div>` too\n"


def test_inline_api_spans():
    body = (
        'Pick <span class="options-api">Options</span>'
        '<span class="composition-api">Composition</span> API.\n'
    )
    assert clean(body) == "# Title\n\nPick Composition API.\n"


def test_page_script_comments_components_demo_and_containers():
    body = (
        '<script setup>\nimport X from "./X.vue"\n</script>\n\n'
        "<!-- hidden\nmulti -->\nText <!-- inline --> kept\n\n"
        '<VueSchoolLink href="u" title="t"/>\n\n'
        '<div class="demo">\n<button>x</button>\n</div>\n\n'
        "::: tip Note\nBe careful.\n:::\n"
    )
    assert clean(body) == "# Title\n\nText kept\n\nNote\nBe careful.\n"


def test_promo_blocks_details_and_images():
    body = (
        '<ScrimbaLink href="u" title="t">\nWatch\n</ScrimbaLink>\n\n'
        "<details>\n<summary>Usage before 3.5</summary>\n\nOld way\n\n</details>\n\n"
        '<img alt="diagram" src="./x.png">\n\n'
        'See docs <sup class="vt-badge ts" />\n'
    )
    assert clean(body) == "# Title\n\nUsage before 3.5\n\nOld way\n\nSee docs\n"


def test_fence_info_strings_reduced_and_indented_fences_tracked():
    listed = "- item\n\n   ```vue-html\n   <div>\n   ```\n"
    body = "```js{2-6}\ncode\n```\n\n```sh [npm]\nnpm i\n```\n\n" + listed
    expected = "# Title\n\n```js\ncode\n```\n\n```sh\nnpm i\n```\n\n" + listed
    assert clean(body) == expected


def test_headings_recorded_with_offsets_and_anchors_removed():
    result = clean_markdown(DOC + "## A {#a}\n\ntext\n\n### B {#b}\n\n#### Deep\n\n## C {#c}\n")
    assert [(h.level, h.anchor, h.title) for h in result.headings] == [
        (1, "title", "Title"),
        (2, "a", "A"),
        (3, "b", "B"),
        (2, "c", "C"),
    ]
    for h in result.headings:
        assert result.text[h.offset :].startswith("#" * h.level + " " + h.title + "\n")
    assert "{#" not in result.text
    assert "#### Deep" in result.text


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("```js\nx\n", "unclosed code fence"),
        ('<div class="options-api">\nx\n', "unclosed HTML block"),
        ('<div class="composition-api">\nx\n', "unclosed composition-api wrapper"),
        ("<!-- open\n", "unclosed HTML comment"),
        ("## Sub\n", "heading without anchor"),
        ("## A {#a}\n\n## B {#a}\n", "duplicate anchor"),
        ("# Second {#second}\n", "exactly one H1"),
        ("<table>\n", "unhandled HTML"),
        ('x <b class="options-api">y</b>\n', "options-api markup"),
    ],
)
def test_anomalies_raise(body, message):
    with pytest.raises(ValueError, match=message):
        clean_markdown(DOC + body)


def test_missing_h1_raises():
    with pytest.raises(ValueError, match="exactly one H1"):
        clean_markdown("## A {#a}\n")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_clean_markdown.py -q`
Expected: FAIL with `ImportError: cannot import name 'clean_markdown'`

- [ ] **Step 3: Implement `clean_markdown`**

Replace the whole content of `src/preprocess.py` with:

```python
"""Preprocess / clean Markdown (ADR 0019).

Reads documents.jsonl and keeps Composition API content only: drops frontmatter, Options API
blocks, page scripts, demos, sponsor/navigation HTML, comments and container markers, and
records the anchored H1-H3 sections. Rewrites documents.jsonl in place, writes sections.jsonl
and the corpus manifest.
"""

import re
from dataclasses import dataclass


SECTION_MAX_LEVEL = 3
# HTML blocks starting a line outside code fences are page furniture (Options API variants,
# demos, sponsor boxes, navigation, promo links) and are dropped, except composition-api
# wrappers, which are unwrapped. Any other HTML line outside fences is an error.
UNWRAP_CLASS = "composition-api"
DROP_BLOCK_TAGS = ("div", "p", "ScrimbaLink", "VueSchoolLink")
DROP_LINE_TAGS = ("img", "details", "/details", "br")

FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([\w+-]*)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
ANCHOR_RE = re.compile(r"\s*\{#([^}]+)\}\s*$")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
BLOCK_OPEN_RE = re.compile(r"^\s*<(" + "|".join(DROP_BLOCK_TAGS) + r")\b([^>]*)>")
UNWRAP_OPEN_RE = re.compile(r'^\s*<(div|p) class="' + UNWRAP_CLASS + r'">\s*$')
LINE_TAG_RE = re.compile(r"^\s*<(" + "|".join(DROP_LINE_TAGS) + r")\b[^>]*>\s*$")
SUMMARY_RE = re.compile(r"^\s*<summary>(.*?)</summary>\s*$")
PAGE_TAG_RE = re.compile(r"^<(script|style)\b")
COMPONENT_LINE_RE = re.compile(r"^\s*<[A-Z][\w-]*\b[^>]*/>\s*$")
CONTAINER_OPEN_RE = re.compile(r"^\s*:::+\s*([a-z][\w-]*)\s*(.*?)\s*$")
CONTAINER_CLOSE_RE = re.compile(r"^\s*:::+\s*$")
COMMENT_RE = re.compile(r"\s*<!--.*?-->")
OPTIONS_SPAN_RE = re.compile(r'<span class="options-api">.*?</span>')
COMPOSITION_SPAN_RE = re.compile(r'<span class="composition-api">(.*?)</span>')
EMPTY_SPAN_RE = re.compile(r'<span id="[^"]*"></span>')
INLINE_SELF_CLOSING_RE = re.compile(r"\s*<(sup|[A-Z][\w-]*)\b[^>]*/>")
HTML_LINE_RE = re.compile(r"^\s*</?[A-Za-z]")


@dataclass(frozen=True)
class Heading:
    level: int
    title: str
    anchor: str
    offset: int  # character offset of the heading line in the cleaned text


@dataclass(frozen=True)
class CleanResult:
    text: str
    headings: list[Heading]


def _tag_balance(tag: str, line: str) -> int:
    """Opened minus closed <tag> elements on line, ignoring inline code and self-closing tags."""
    line = INLINE_CODE_RE.sub("", line)
    opens = len(re.findall(rf"<{tag}\b[^>]*(?<!/)>", line))
    return opens - len(re.findall(rf"</{tag}\s*>", line))


def _strip_frontmatter(lines: list[str]) -> list[str]:
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return lines[i + 1 :]
        raise ValueError("unclosed frontmatter")
    return lines


def clean_markdown(text: str) -> CleanResult:
    """Return Composition-API-only Markdown and its anchored H1-H3 headings."""
    text = text.lstrip("﻿").replace("\r\n", "\n")
    lines = _strip_frontmatter(text.split("\n"))

    out: list[str] = []
    pending: list[tuple[int, int, str, str]] = []  # (out line index, level, title, anchor)
    fence: str | None = None  # marker of the open code fence
    drop: tuple[str, int] | None = None  # (tag, depth) of the HTML block being dropped
    unwrap: list[tuple[str, int]] = []  # (tag, depth) of open composition-api wrappers
    page_tag: str | None = None  # open <script>/<style> being dropped
    in_comment = False

    def emit(line: str) -> None:
        line = line.rstrip()
        if not line and (not out or not out[-1]):
            return
        out.append(line)

    for line in lines:
        m = FENCE_RE.match(line)
        if fence is not None:
            if m and m.group(2)[0] == fence[0] and len(m.group(2)) >= len(fence) and not m.group(3):
                fence = None
            if drop is None:
                emit(line)
            continue
        if m:
            fence = m.group(2)
            if drop is None:
                emit(f"{m.group(1)}{m.group(2)}{m.group(3)}")
            continue
        if drop is not None:
            depth = drop[1] + _tag_balance(drop[0], line)
            drop = (drop[0], depth) if depth > 0 else None
            continue
        if page_tag:
            if f"</{page_tag}>" in line:
                page_tag = None
            continue
        if in_comment:
            if "-->" not in line:
                continue
            line, in_comment = line.split("-->", 1)[1], False
        line = COMMENT_RE.sub("", line)
        if "<!--" in line:
            line, in_comment = line.split("<!--", 1)[0], True
        u = UNWRAP_OPEN_RE.match(line)
        if u:
            unwrap.append((u.group(1), 1))
            continue
        if unwrap:
            tag, depth = unwrap[-1]
            depth += _tag_balance(tag, line)
            if depth == 0:
                unwrap.pop()
                if line.strip() == f"</{tag}>":
                    continue
                raise ValueError(f"composition-api wrapper closed mid-line: {line!r}")
            unwrap[-1] = (tag, depth)
        b = BLOCK_OPEN_RE.match(line)
        if b:
            depth = _tag_balance(b.group(1), line)
            drop = (b.group(1), depth) if depth > 0 else None
            continue
        tag = PAGE_TAG_RE.match(line)
        if tag:
            if f"</{tag.group(1)}>" not in line:
                page_tag = tag.group(1)
            continue
        s = SUMMARY_RE.match(line)
        if s:
            line = s.group(1)
        if LINE_TAG_RE.match(line) or COMPONENT_LINE_RE.match(line):
            continue
        if CONTAINER_CLOSE_RE.match(line):
            continue
        c = CONTAINER_OPEN_RE.match(line)
        if c:
            if c.group(2):
                emit(c.group(2))
            continue
        line = OPTIONS_SPAN_RE.sub("", line)
        line = COMPOSITION_SPAN_RE.sub(r"\1", line)
        line = EMPTY_SPAN_RE.sub("", line)
        line = INLINE_SELF_CLOSING_RE.sub("", line)
        if 'class="options-api"' in line:
            raise ValueError(f"options-api markup left after cleaning: {line!r}")
        if HTML_LINE_RE.match(line):
            raise ValueError(f"unhandled HTML outside code fences: {line!r}")
        h = HEADING_RE.match(line)
        if h:
            level, title = len(h.group(1)), h.group(2)
            a = ANCHOR_RE.search(title)
            if a:
                title = title[: a.start()]
            if level <= SECTION_MAX_LEVEL:
                if not a:
                    raise ValueError(f"heading without anchor: {line!r}")
                emit("")
                pending.append((len(out), level, title, a.group(1)))
            line = f"{h.group(1)} {title}"
        emit(line)

    for state, what in (
        (fence, "code fence"),
        (drop, "HTML block"),
        (unwrap, "composition-api wrapper"),
        (page_tag, "<script>/<style>"),
        (in_comment, "HTML comment"),
    ):
        if state:
            raise ValueError(f"unclosed {what}")
    while out and not out[-1]:
        out.pop()

    starts, pos = [], 0
    for line in out:
        starts.append(pos)
        pos += len(line) + 1
    headings = [Heading(lv, t, a, starts[i]) for i, lv, t, a in pending]
    anchors = [h.anchor for h in headings]
    if len(set(anchors)) != len(anchors):
        raise ValueError(
            f"duplicate anchor: {sorted({a for a in anchors if anchors.count(a) > 1})}"
        )
    if sum(h.level == 1 for h in headings) != 1:
        raise ValueError("document needs exactly one H1")
    return CleanResult("\n".join(out) + "\n", headings)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_clean_markdown.py -q`
Expected: all passed. If a fixture expectation differs only in blank-line placement, fix the implementation, not the
expectation, unless the expectation contradicts the cleaning rules in the spec.

- [ ] **Step 5: Commit and push**

```bash
uvx pre-commit run --all-files
git add src/preprocess.py tests/test_clean_markdown.py
git commit -m "feat(preprocess): Markdown-Bereinigung auf Composition API mit Abschnittsankern"
git push
```

---

### Task 3: Section spans, `preprocess()` and the manifest

**Files:**
- Modify: `src/preprocess.py` (add imports, `section_spans`, `manifest_section`, `preprocess`, `__main__`)
- Test: `tests/test_preprocess.py`

**Interfaces:**
- Consumes: `tokens.token_starts`, `tokens.char_to_token`, `tokens.count` (Task 1); `clean_markdown`, `CleanResult` (Task 2);
  `config.DOCUMENTS_FILE`, `config.SECTIONS_FILE`, `config.CORPUS_MANIFEST_FILE`.
- Produces: `preprocess.section_spans(doc_id: str, result: CleanResult) -> list[dict]` (keys `section_id, doc_id,
  anchor, title, level, start_token, end_token`), `preprocess.manifest_section(path: str) -> str` (raises
  `ValueError` for a folder missing from `SECTION_NAMES`),
  `preprocess.preprocess(doc_file: Path = DOCUMENTS_FILE, sections_file: Path = SECTIONS_FILE,
  manifest_file: Path = CORPUS_MANIFEST_FILE) -> tuple[int, int]` (documents, sections).

- [ ] **Step 1: Write the failing tests**

`tests/test_preprocess.py`:

```python
import csv
import json

import pytest

import tokens
from preprocess import clean_markdown, manifest_section, preprocess, section_spans

RAW_A = (
    '# A Page {#a-page}\n\n<div class="options-api">\n\nOld\n\n</div>\n\n## Part {#part}\n\nText.\n'
)
RAW_B = "# Intro {#intro}\n\nHello.\n"


def write_docs(path, docs):
    path.write_text("".join(json.dumps(d) + "\n" for d in docs), encoding="utf-8")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


@pytest.fixture
def files(tmp_path):
    docs = tmp_path / "documents.jsonl"
    write_docs(
        docs,
        [
            {
                "doc_id": "D001",
                "path": "guide/essentials/a.md",
                "title": "A Page",
                "text": RAW_A,
                "tokens": 0,
            },
            {
                "doc_id": "D002",
                "path": "guide/introduction.md",
                "title": "Intro",
                "text": RAW_B,
                "tokens": 0,
            },
        ],
    )
    return docs, tmp_path / "sections.jsonl", tmp_path / "corpus_manifest.csv"


def test_section_spans_nest_and_cover_document():
    result = clean_markdown(
        "# T {#t}\n\nIntro.\n\n## A {#a}\n\ntext\n\n### B {#b}\n\nmore\n\n## C {#c}\n\nend\n"
    )
    spans = section_spans("D007", result)
    n = tokens.count(result.text)
    by_id = {s["section_id"]: s for s in spans}
    assert list(by_id) == ["D007#t", "D007#a", "D007#b", "D007#c"]
    assert (by_id["D007#t"]["start_token"], by_id["D007#t"]["end_token"]) == (0, n)
    assert by_id["D007#a"]["end_token"] == by_id["D007#c"]["start_token"]
    assert by_id["D007#b"]["end_token"] == by_id["D007#c"]["start_token"]
    assert by_id["D007#a"]["start_token"] < by_id["D007#b"]["start_token"]
    assert by_id["D007#c"]["end_token"] == n
    assert list(spans[0]) == [
        "section_id",
        "doc_id",
        "anchor",
        "title",
        "level",
        "start_token",
        "end_token",
    ]


@pytest.mark.parametrize(
    ("path", "section"),
    [
        ("guide/essentials/a.md", "Essentials"),
        ("guide/best-practices/performance.md", "Best Practices"),
        ("guide/typescript/overview.md", "TypeScript"),
        ("guide/introduction.md", "Guide"),
    ],
)
def test_manifest_section(path, section):
    assert manifest_section(path) == section


def test_manifest_section_unknown_folder_raises():
    with pytest.raises(ValueError, match="no manifest section"):
        manifest_section("guide/new-folder/page.md")


def test_preprocess_writes_documents_sections_and_manifest(files):
    docs, sections, manifest = files
    assert preprocess(docs, sections, manifest) == (2, 3)

    out = read_jsonl(docs)
    assert [list(d) for d in out] == [["doc_id", "path", "title", "text", "tokens"]] * 2
    assert out[0]["text"] == "# A Page\n\n## Part\n\nText.\n"
    assert out[0]["tokens"] == tokens.count(out[0]["text"])

    assert [s["section_id"] for s in read_jsonl(sections)] == [
        "D001#a-page",
        "D001#part",
        "D002#intro",
    ]

    with manifest.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["file_id", "path", "title", "section", "tokens", "included"]
    assert rows[1] == [
        "D001",
        "guide/essentials/a.md",
        "A Page",
        "Essentials",
        str(out[0]["tokens"]),
        "yes",
    ]
    assert rows[2][3] == "Guide"


def test_rerun_on_cleaned_documents_asks_for_ingest(files):
    docs, sections, manifest = files
    preprocess(docs, sections, manifest)
    with pytest.raises(RuntimeError, match="run src/ingest.py"):
        preprocess(docs, sections, manifest)


def test_anomaly_reports_document_path(files):
    docs, sections, manifest = files
    write_docs(
        docs,
        [
            {
                "doc_id": "D001",
                "path": "guide/x.md",
                "title": "X",
                "text": "# X {#x}\n\n## Y\n",
                "tokens": 0,
            }
        ],
    )
    with pytest.raises(ValueError, match="guide/x.md: heading without anchor"):
        preprocess(docs, sections, manifest)


def test_missing_documents_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="run src/ingest.py"):
        preprocess(tmp_path / "missing.jsonl", tmp_path / "s.jsonl", tmp_path / "m.csv")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_preprocess.py -q`
Expected: FAIL with `ImportError: cannot import name 'manifest_section'`

- [ ] **Step 3: Implement**

In `src/preprocess.py`, replace the import block (`import re` / `from dataclasses import dataclass`) with:

```python
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

import tokens
from config import CORPUS_MANIFEST_FILE, DOCUMENTS_FILE, SECTIONS_FILE
```

Add after the `HTML_LINE_RE` constant:

```python
MANIFEST_HEADER = ["file_id", "path", "title", "section", "tokens", "included"]
# Manifest `section` per folder below guide/ (pages directly in guide/ get "Guide").
SECTION_NAMES = {
    "best-practices": "Best Practices",
    "built-ins": "Built-ins",
    "components": "Components",
    "essentials": "Essentials",
    "extras": "Extras",
    "reusability": "Reusability",
    "scaling-up": "Scaling Up",
    "typescript": "TypeScript",
}
```

Append at the end of the file:

```python
def section_spans(doc_id: str, result: CleanResult) -> list[dict]:
    """Token span of every heading up to the next heading of the same or a higher level."""
    starts = tokens.token_starts(result.text)
    spans = []
    for i, h in enumerate(result.headings):
        end = next(
            (o.offset for o in result.headings[i + 1 :] if o.level <= h.level), len(result.text)
        )
        spans.append(
            {
                "section_id": f"{doc_id}#{h.anchor}",
                "doc_id": doc_id,
                "anchor": h.anchor,
                "title": h.title,
                "level": h.level,
                "start_token": tokens.char_to_token(starts, h.offset),
                "end_token": tokens.char_to_token(starts, end),
            }
        )
    return spans


def manifest_section(path: str) -> str:
    """Manifest `section` column for a path like guide/<folder>/<page>.md."""
    parts = path.split("/")
    if len(parts) == 2:
        return "Guide"
    if parts[1] not in SECTION_NAMES:
        raise ValueError(f"{path}: no manifest section for folder {parts[1]!r}")
    return SECTION_NAMES[parts[1]]


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def preprocess(
    doc_file: Path = DOCUMENTS_FILE,
    sections_file: Path = SECTIONS_FILE,
    manifest_file: Path = CORPUS_MANIFEST_FILE,
) -> tuple[int, int]:
    """Clean documents.jsonl in place; write sections.jsonl and the corpus manifest."""
    if not doc_file.exists():
        raise FileNotFoundError(f"{doc_file} not found; run src/ingest.py first")
    docs = [json.loads(line) for line in doc_file.read_text(encoding="utf-8").splitlines() if line]
    if docs and all("{#" not in d["text"] for d in docs):
        raise RuntimeError(f"{doc_file} is already preprocessed; run src/ingest.py first")

    sections: list[dict] = []
    for doc in docs:
        try:
            result = clean_markdown(doc["text"])
        except ValueError as e:
            raise ValueError(f"{doc['path']}: {e}") from e
        doc["text"] = result.text
        doc["tokens"] = tokens.count(result.text)
        sections.extend(section_spans(doc["doc_id"], result))

    _write_jsonl(doc_file, docs)
    _write_jsonl(sections_file, sections)
    with manifest_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(MANIFEST_HEADER)
        for d in docs:
            writer.writerow(
                [
                    d["doc_id"],
                    d["path"],
                    d["title"],
                    manifest_section(d["path"]),
                    d["tokens"],
                    "yes",
                ]
            )
    return len(docs), len(sections)


if __name__ == "__main__":
    n_docs, n_sections = preprocess()
    print(
        f"{n_docs} documents, {n_sections} sections -> {DOCUMENTS_FILE.name}, {SECTIONS_FILE.name}"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest -q`
Expected: all passed (tokens, clean_markdown, preprocess)

- [ ] **Step 5: Commit and push**

```bash
uvx pre-commit run --all-files
git add src/preprocess.py tests/test_preprocess.py
git commit -m "feat(preprocess): Abschnitts-Token-Spannen, sections.jsonl und Korpusmanifest"
git push
```

---

### Task 4: `ingest.py`

**Files:**
- Modify: `src/ingest.py` (replace the stub)
- Test: `tests/test_ingest.py`

**Interfaces:**
- Consumes: `tokens.count` (Task 1); `config.DATA_RAW`, `config.DOCUMENTS_FILE`.
- Produces: `ingest.title_of(text: str) -> str`, `ingest.ingest(snapshot_dir: Path = DATA_RAW,
  out_file: Path = DOCUMENTS_FILE) -> int` (number of documents). Reads `snapshot_dir/guide/**/*.md`.

- [ ] **Step 1: Write the failing tests**

`tests/test_ingest.py`:

```python
import json

import pytest

import tokens
from ingest import ingest, title_of


def make_snapshot(root, files):
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def test_title_of_skips_frontmatter_bom_and_code():
    text = "﻿---\noutline: deep\n---\n\n```sh\n# not a title\n```\n\n# Real Title {#real}\n"
    assert title_of(text) == "Real Title"


def test_title_of_without_h1_raises():
    with pytest.raises(ValueError, match="no H1"):
        title_of("## Only H2 {#x}\n")


def test_ingest_assigns_ids_by_path_and_writes_exact_keys(tmp_path):
    snap = tmp_path / "snap"
    make_snapshot(
        snap,
        {
            "guide/introduction.md": "# Introduction {#introduction}\n",
            "guide/components/props.md": "﻿# Props {#props}\n\nText\n",
            "guide/essentials/a.md": "# A {#a}\n",
        },
    )
    out = tmp_path / "processed" / "documents.jsonl"
    assert ingest(snap, out) == 3

    docs = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [(d["doc_id"], d["path"], d["title"]) for d in docs] == [
        ("D001", "guide/components/props.md", "Props"),
        ("D002", "guide/essentials/a.md", "A"),
        ("D003", "guide/introduction.md", "Introduction"),
    ]
    assert list(docs[0]) == ["doc_id", "path", "title", "text", "tokens"]
    assert not docs[0]["text"].startswith("﻿")
    assert docs[0]["tokens"] == tokens.count(docs[0]["text"])


def test_ingest_without_snapshot_points_to_snapshot_script(tmp_path):
    with pytest.raises(FileNotFoundError, match="run src/snapshot.py"):
        ingest(tmp_path / "empty", tmp_path / "documents.jsonl")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_ingest.py -q`
Expected: FAIL with `ImportError: cannot import name 'title_of'`

- [ ] **Step 3: Implement `src/ingest.py`**

```python
"""Ingest Vue.js snapshot.

Reads guide/**/*.md from data/raw/vue_docs_snapshot/ sorted by path, assigns D001, D002, ...
in that order and writes data/processed/documents.jsonl with the raw text.

Output schema: {"doc_id", "path", "title", "text", "tokens"}
"""

import json
import re
from pathlib import Path

import tokens
from config import DATA_RAW, DOCUMENTS_FILE

H1_RE = re.compile(r"^#\s+(.*?)(?:\s*\{#[^}]+\})?\s*$")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")


def title_of(text: str) -> str:
    """Text of the first H1 outside code fences, without its anchor."""
    in_fence = False
    for line in text.lstrip("﻿").split("\n"):
        if FENCE_RE.match(line):
            in_fence = not in_fence
        elif not in_fence and (m := H1_RE.match(line)):
            return m.group(1)
    raise ValueError("no H1 found")


def ingest(snapshot_dir: Path = DATA_RAW, out_file: Path = DOCUMENTS_FILE) -> int:
    """Load all guide Markdown files, count tokens, write documents.jsonl; return the count."""
    files = sorted(
        snapshot_dir.glob("guide/**/*.md"), key=lambda p: p.relative_to(snapshot_dir).as_posix()
    )
    if not files:
        raise FileNotFoundError(
            f"no Markdown files under {snapshot_dir / 'guide'}; run src/snapshot.py first"
        )
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        for i, path in enumerate(files, start=1):
            rel = path.relative_to(snapshot_dir).as_posix()
            text = path.read_text(encoding="utf-8-sig")
            try:
                title = title_of(text)
            except ValueError as e:
                raise ValueError(f"{rel}: {e}") from e
            record = {
                "doc_id": f"D{i:03d}",
                "path": rel,
                "title": title,
                "text": text,
                "tokens": tokens.count(text),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return len(files)


if __name__ == "__main__":
    print(f"{ingest()} documents -> {DOCUMENTS_FILE}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_ingest.py -q`
Expected: 4 passed

- [ ] **Step 5: Commit and push**

```bash
uvx pre-commit run --all-files
git add src/ingest.py tests/test_ingest.py
git commit -m "feat(ingest): Snapshot-Dateien nach Pfad sortiert in documents.jsonl einlesen"
git push
```

---

### Task 5: `snapshot.py`

**Files:**
- Create: `src/snapshot.py`
- Test: `tests/test_snapshot.py`

**Interfaces:**
- Consumes: `config.DATA_RAW`, `config.SNAPSHOT_INFO_FILE`, `config.VUE_DOCS_REPO_URL`, `config.VUE_DOCS_COMMIT`,
  `config.VUE_DOCS_SUBDIR` (Task 1).
- Produces: `snapshot.snapshot(repo_url: str = VUE_DOCS_REPO_URL, commit: str = VUE_DOCS_COMMIT,
  subdir: str = VUE_DOCS_SUBDIR, out_dir: Path = DATA_RAW, info_file: Path = SNAPSHOT_INFO_FILE) -> int`
  (number of files); files land in `out_dir/guide/…`, which `ingest.py` reads.

- [ ] **Step 1: Write the failing tests**

`tests/test_snapshot.py` (local git repository, no network):

```python
import hashlib
import subprocess

import pytest

from snapshot import snapshot

GIT_ID = ["-c", "user.name=test", "-c", "user.email=test@example.invalid"]


def git(cwd, *args):
    return subprocess.run(
        ["git", *GIT_ID, *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def origin(tmp_path):
    repo = tmp_path / "origin"
    for rel, text in {
        "src/guide/a.md": "# A {#a}\n",
        "src/guide/sub/b.md": "# B {#b}\n",
        "src/guide/img.png": "binary",
        "src/other.md": "# Other {#other}\n",
    }.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(repo.parent, "init", "-q", str(repo))
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "init")
    return repo, git(repo, "rev-parse", "HEAD")


def test_snapshot_copies_guide_markdown_and_writes_checksums(origin, tmp_path):
    repo, sha = origin
    out = tmp_path / "raw"
    (out / "guide").mkdir(parents=True)
    (out / ".gitkeep").write_text("")
    (out / "guide" / "stale.md").write_text("old")
    info = out / "SNAPSHOT.txt"

    assert snapshot(repo.as_uri(), sha, "src/guide", out, info) == 2

    copied = sorted(
        p.relative_to(out).as_posix() for p in (out / "guide").rglob("*") if p.is_file()
    )
    assert copied == [
        "guide/a.md",
        "guide/sub/b.md",
    ]
    assert (out / ".gitkeep").exists()
    text = info.read_text(encoding="utf-8")
    assert f"commit: {sha}" in text
    assert "files: 2" in text
    digest = hashlib.sha256((out / "guide" / "a.md").read_bytes()).hexdigest()
    assert f"{digest}  guide/a.md" in text


def test_snapshot_rejects_unknown_commit(origin, tmp_path):
    repo, _ = origin
    with pytest.raises(RuntimeError, match="git fetch"):
        snapshot(repo.as_uri(), "0" * 40, "src/guide", tmp_path / "raw", tmp_path / "SNAPSHOT.txt")


def test_snapshot_rejects_missing_subdir(origin, tmp_path):
    repo, sha = origin
    with pytest.raises(FileNotFoundError, match="docs/missing"):
        snapshot(repo.as_uri(), sha, "docs/missing", tmp_path / "raw", tmp_path / "SNAPSHOT.txt")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_snapshot.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'snapshot'`

- [ ] **Step 3: Implement `src/snapshot.py`**

```python
"""Create the corpus snapshot (ADR 0019).

Fetches config.VUE_DOCS_COMMIT of config.VUE_DOCS_REPO_URL (shallow), replaces
data/raw/vue_docs_snapshot/guide/ with every Markdown file below config.VUE_DOCS_SUBDIR and
writes SNAPSHOT.txt with repository, commit, dates and a sha256 per file.
"""

import hashlib
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path

from config import DATA_RAW, SNAPSHOT_INFO_FILE, VUE_DOCS_COMMIT, VUE_DOCS_REPO_URL, VUE_DOCS_SUBDIR

TARGET_DIR = "guide"


def _git(cwd: Path, *args: str) -> str:
    try:
        result = subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git {' '.join(args)} failed: {e.stderr.strip()}") from e
    return result.stdout.strip()


def fetch_commit(repo_url: str, commit: str, dest: Path) -> str:
    """Check out commit of repo_url into dest (depth 1); return its committer date (ISO 8601)."""
    _git(dest, "init", "-q")
    _git(dest, "fetch", "-q", "--depth", "1", repo_url, commit)
    _git(dest, "checkout", "-q", "FETCH_HEAD")
    head = _git(dest, "rev-parse", "HEAD")
    if head != commit:
        raise RuntimeError(f"fetched {head}, expected {commit}")
    return _git(dest, "show", "-s", "--format=%cI", "HEAD")


def copy_markdown(src_dir: Path, out_dir: Path) -> list[Path]:
    """Replace out_dir/guide with the *.md files below src_dir; return paths relative to out_dir."""
    if not src_dir.is_dir():
        raise FileNotFoundError(f"{src_dir} not found in the checkout")
    target = out_dir / TARGET_DIR
    if target.exists():
        shutil.rmtree(target)
    copied = []
    for src in sorted(src_dir.rglob("*.md")):
        dst = target / src.relative_to(src_dir)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(dst.relative_to(out_dir))
    if not copied:
        raise FileNotFoundError(f"no Markdown files below {src_dir}")
    return copied


def snapshot(
    repo_url: str = VUE_DOCS_REPO_URL,
    commit: str = VUE_DOCS_COMMIT,
    subdir: str = VUE_DOCS_SUBDIR,
    out_dir: Path = DATA_RAW,
    info_file: Path = SNAPSHOT_INFO_FILE,
) -> int:
    """Fetch the pinned commit, copy its Markdown files and write SNAPSHOT.txt; return the count."""
    if shutil.which("git") is None:
        raise RuntimeError("git is required to create the snapshot")
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        checkout = Path(tmp)
        commit_date = fetch_commit(repo_url, commit, checkout)
        files = copy_markdown(checkout / subdir, out_dir)
    lines = [
        f"repository: {repo_url}",
        f"commit: {commit}",
        f"commit_date: {commit_date}",
        f"snapshot_date: {date.today().isoformat()}",
        f"files: {len(files)}",
        "",
    ]
    lines += [
        f"{hashlib.sha256((out_dir / f).read_bytes()).hexdigest()}  {f.as_posix()}" for f in files
    ]
    info_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(files)


if __name__ == "__main__":
    print(f"{snapshot()} files -> {DATA_RAW / TARGET_DIR}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_snapshot.py -q`
Expected: 3 passed

- [ ] **Step 5: Commit and push**

```bash
uvx pre-commit run --all-files
git add src/snapshot.py tests/test_snapshot.py
git commit -m "feat(snapshot): Vue-Doku auf festem Commit holen und mit Prüfsummen ablegen"
git push
```

---

### Task 6: Real run, integration test and documentation

**Files:**
- Create: `tests/test_corpus_integration.py`
- Modify: `docs/corpus_manifest.csv` (generated), `docs/reference/data-formats.md`, `docs/reference/tooling.md`,
  `docs/how-to/create-corpus-snapshot.md`, `docs/reference/experiment-record.md`, `docs/reference/corpus.md`,
  `README.md`, `docs/superpowers/specs/2026-10-13-corpus-snapshot-design.md` (only if implementation deviated),
  `.serena/memories/pipeline.md`

**Interfaces:**
- Consumes: everything above; the real snapshot in `data/raw/vue_docs_snapshot/` (gitignored).

- [ ] **Step 1: Write the integration test**

`tests/test_corpus_integration.py`:

```python
"""Checks on the real corpus; skipped until the snapshot and processed files exist."""

import json

import pytest

from config import DATA_RAW, DOCUMENTS_FILE, SECTIONS_FILE
from preprocess import clean_markdown

GUIDE = DATA_RAW / "guide"
EXPECTED_FILES = 52  # ADR 0019


@pytest.mark.skipif(not GUIDE.is_dir(), reason="no snapshot; run src/snapshot.py")
def test_every_snapshot_file_cleans():
    files = sorted(GUIDE.rglob("*.md"))
    assert len(files) == EXPECTED_FILES
    for path in files:
        result = clean_markdown(path.read_text(encoding="utf-8"))
        assert result.headings[0].level == 1, path


@pytest.mark.skipif(not SECTIONS_FILE.exists(), reason="not preprocessed; run src/preprocess.py")
def test_processed_artifacts_are_consistent():
    docs = [json.loads(line) for line in DOCUMENTS_FILE.read_text(encoding="utf-8").splitlines()]
    sections = [json.loads(line) for line in SECTIONS_FILE.read_text(encoding="utf-8").splitlines()]
    assert len(docs) == EXPECTED_FILES
    assert [d["doc_id"] for d in docs] == [f"D{i:03d}" for i in range(1, EXPECTED_FILES + 1)]
    ids = [s["section_id"] for s in sections]
    assert len(ids) == len(set(ids))
    tokens_by_doc = {d["doc_id"]: d["tokens"] for d in docs}
    for s in sections:
        assert 0 <= s["start_token"] < s["end_token"] <= tokens_by_doc[s["doc_id"]], s["section_id"]
```

- [ ] **Step 2: Run the pipeline on the real corpus**

```bash
uv run python src/snapshot.py
uv run python src/ingest.py
uv run python src/preprocess.py
```

Expected (verified in a dry run on 13.10.2026): `52 files`, `52 documents`, `52 documents, 560 sections`, 139,342 tokens
after preprocessing. If `preprocess.py` raises on a real file, add
a failing fixture for that construct to `tests/test_clean_markdown.py` first, then extend the cleaning rules
(never silence the error).

- [ ] **Step 3: Run all tests**

Run: `uv run pytest -q`
Expected: all passed, integration tests not skipped.

- [ ] **Step 4: Record the numbers**

Get them with:

```bash
cat data/raw/vue_docs_snapshot/SNAPSHOT.txt | head -6
uv run python -c "import json;d=[json.loads(l) for l in open('data/processed/documents.jsonl')];print(len(d), sum(x['tokens'] for x in d))"
wc -l data/processed/sections.jsonl
```

Fill in `docs/reference/experiment-record.md`: `Datum des Snapshots` (snapshot_date), `Gesamtumfang (Tokens)` (sum
after preprocessing, with "nach Preprocessing"), and the row `tiktoken | 0.13.0 | <today>`. In
`docs/reference/corpus.md` replace the `Umfang` row value with the token total and section count.

- [ ] **Step 5: Update the docs**

- `docs/reference/data-formats.md`: after the `chunks_c1.jsonl` block add

  ````markdown
  **`sections.jsonl`** (ein Eintrag je H1–H3-Abschnitt; Spanne in Tokens des bereinigten `text`, Ende exklusiv; [ADR 0019](../adr/0019-korpus-ausschnitt.md))
  ```json
  {"section_id":"D001#ref-vs-reactive","doc_id":"D001","anchor":"ref-vs-reactive","title":"ref vs. reactive","level":2,"start_token":812,"end_token":1240}
  ```
  ````

- `docs/reference/tooling.md`: in the repository tree add `snapshot.py` and `tokens.py` above `ingest.py` and a
  `tests/` line under `src/`; in the script table change the first row to `` | `snapshot.py`, `ingest.py`, `preprocess.py` | keine | ``;
  replace "Stand 13.10.2026 sind alle Schritte Gerüste (`raise NotImplementedError`)." with
  "Umgesetzt: `snapshot.py`, `ingest.py`, `preprocess.py`; die übrigen Schritte sind Gerüste (`raise NotImplementedError`).";
  change `(Entscheidungen D1–D18)` to `(Entscheidungen D1–D19)`.
- `docs/how-to/create-corpus-snapshot.md`: replace the numbered steps with

  ```markdown
  1. `uv run python src/snapshot.py` — holt den Commit aus `config.VUE_DOCS_COMMIT`, kopiert `src/guide/` nach
     `data/raw/vue_docs_snapshot/guide/` und schreibt `SNAPSHOT.txt` (Commit, Datum, SHA-256 je Datei).
  2. `uv run python src/ingest.py` — schreibt `data/processed/documents.jsonl`.
  3. `uv run python src/preprocess.py` — bereinigt die Texte, schreibt `sections.jsonl` und `docs/corpus_manifest.csv`.
  4. Werte aus `SNAPSHOT.txt` und die Token-Summe ins [Experiment-Protokoll](../reference/experiment-record.md)
     übernehmen, `docs/corpus_manifest.csv` committen.
  ```

  and fill `Anzahl Dateien: 52` and `Gesamtumfang` in the Steckbrief template with the real values.
- `README.md`: replace the step-1 comment lines with `# 1. Fetch the Vue.js snapshot (ADR 0019)` +
  `python src/snapshot.py`; prefix the minimal-prototype line with `python src/snapshot.py && `; change the `src/`
  tree line to `(snapshot → ingest → preprocess → chunking → …)`.
- `.serena/memories/pipeline.md`: replace the first bullet with "`snapshot.py`, `ingest.py`, `preprocess.py` are
  implemented (tests in `tests/`); the rest are stubs …" and add "- Section spans for relevance: `sections.jsonl`
  (`docs/reference/data-formats.md`); chunk spans must use `tokens.py` so both share one index space."
- Spec: if any cleaning rule or interface changed during implementation, update the matching spec section.

- [ ] **Step 6: Verify and commit**

```bash
uvx pre-commit run --all-files
uv run pytest -q
git status --short   # data/ must not appear except .gitkeep files; .env never
git add tests/test_corpus_integration.py docs README.md .serena/memories/pipeline.md
git commit -m "feat(corpus): Snapshot b75d188 verarbeitet, Manifest und Doku aktualisiert"
git push
```
