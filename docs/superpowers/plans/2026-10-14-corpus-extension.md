# Corpus extension and C3 comparability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the corpus to guide + API reference (Composition) + style guide at `vuejs/docs` `40aa88a`, add the size-matched control K1 and the fair sensitivity rule, rebuild every artefact, and validate each step against the old corpus and against independent sources.

**Architecture:** Snapshot and ingest learn a list of areas plus an exclusion list (config only); the cleaner learns three narrowly tested API cases and must leave the guide byte-identical. K1 is a fixed-size strategy kept *outside* `STRATEGY_IDS` with its own `CONTROL_*` mappings, so the experiment code paths (retrieve's "always all strategies", tests, probe) stay untouched; `retrieve()` accepts exactly the experiment set or exactly the control set. The pilot ground truth is remapped by path and anchor, never by hand.

**Tech Stack:** Python 3.13 (uv), tiktoken 0.13.0 `cl100k_base`, openai 2.44.0, chromadb 1.5.9, pytest, ruff via pre-commit.

**Spec:** `docs/superpowers/specs/2026-10-14-corpus-extension-design.md`

## Global Constraints

- All parameters live only in `src/config.py` (AGENTS.md). Values: `VUE_DOCS_COMMIT = "40aa88af0094f7bab4aaf786e55c748a6a251d88"`, areas `("api", "guide", "style-guide")`, 7 exclusions (Task 3), `C3_MAX_TOKENS = 800`, `C3_MIN_TOKENS = 50`, `SENSITIVITY_MIN_OVERLAP = 100`, `RELEVANCE_MIN_OVERLAP = 1`, `TOP_K = 5`.
- Only the chunking varies between strategies (ADR 0006); K1 is a control, never in `STRATEGY_IDS`, never in answer generation.
- Chunk `text` is the exact document slice; chunks and sections share the token space of `src/tokens.py` (ADR 0019, 0021).
- Tests never call the OpenAI API; the only network a test may need is tiktoken's one-time encoding download.
- Conventional Commits, no AI attribution lines, never commit `.env`; commit and push after each task (branch `feat/corpus-extension`, never `main`).
- Code edits through Serena symbolic tools (`replace_symbol_body`, `insert_after_symbol`, `replace_content`); before changing a symbol run `find_referencing_symbols` (Serena) or `trace_path` (codebase-memory, project `home-jonas-Documents-Code-PaperLab-scientific-papers-thesis-thesis-semester-7-rag-chunking_jonas-code`) and update every reference. Re-index codebase-memory after Task 4.
- Every chained shell gate uses `set -e`; pre-commit failures are detected with `grep Failed`, never by eye.
- API spend in this plan: only Task 7 (about USD 0.09), approved with the spec.
- Scratch directory for backups and downloads: `$S=${TMPDIR:-/tmp}/rag-chunking-scratch` (any local directory, never inside the repo).

## Review Focus

1. A misspelled exclusion path (file absent at the commit) must abort the snapshot, never silently include or skip a page — test in Task 3.
2. A K1 size that no longer equals the rounded C3 mean (e.g. after the corpus changed) must abort chunking with the measured value — test in Task 4.
3. Mixing the control into the experiment (a K1 entry in the experiment mappings, or a subset of `STRATEGY_IDS`) must be refused by `retrieve()` — test in Task 4.
4. An escaped `\<` inside inline code stays untouched, and real unescaped HTML in the same line as an escape must still raise — test in Task 2.
5. Under the sensitivity rule a short chunk counts only if it overlaps by its full length *inside the right document*; partial or foreign-document overlap never counts — test in Task 1.

## Validation ledger (executed in the tasks, results go to the experiment record)

| ID | What is proven | Task |
|---|---|---|
| V1 | New cleaner + new ingest reproduce the old guide artefacts byte for byte | 2, 3 |
| V2 | At the new commit only the 6 upstream-changed guide files differ after cleaning | 5 |
| V3 | Snapshot file list equals GitHub's tree at the commit (independent source) | 5 |
| V4 | The four formerly failing API pages read correctly at the fixed spots (manual) | 5 |
| V5 | All chunk invariants hold for C1–C3 and K1; K1 size equals the rule | 5 |
| V6 | Billed embedding tokens equal locally counted tokens; canary against the old vectors | 7 |
| V7 | Retrieval exact (verified top-k) and a rerun is byte-identical without API | 7 |
| V8 | Every pilot section resolves; changed texts listed and checked by hand | 6 |
| V9 | Suite green online, offline (`unshare -rn`) and with `-W error::DeprecationWarning`; pre-commit | 9 |

---

### Task 1: Fair sensitivity rule in `relevance.is_relevant`

**Files:**
- Modify: `src/relevance.py` (`is_relevant`)
- Test: `tests/test_relevance.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `is_relevant(chunk: dict, sections: list[dict], min_overlap: int) -> bool`, threshold `max(1, min(min_overlap, chunk length))`. Callers unchanged (`retrieve.py`, `tests/test_retrieve.py`).

- [ ] **Step 1: Write the failing tests** (append to `tests/test_relevance.py`)

```python
def test_short_chunk_fully_inside_meets_the_sensitivity_threshold():
    assert is_relevant(chunk("D001", 120, 180), [SECTION], 100)  # 60 tokens, all inside


def test_long_chunk_needs_the_full_threshold():
    assert not is_relevant(chunk("D001", 160, 660), [SECTION], 100)  # 500 tokens, 40 overlap


def test_short_chunk_partly_outside_does_not_count():
    assert not is_relevant(chunk("D001", 170, 230), [SECTION], 100)  # 60 tokens, 30 overlap


def test_short_chunk_of_another_document_never_counts():
    assert not is_relevant(chunk("D002", 120, 180), [SECTION], 100)


def test_main_rule_unchanged_for_short_chunks():
    assert is_relevant(chunk("D001", 199, 230), [SECTION], 1)  # one shared token
    assert not is_relevant(chunk("D001", 200, 230), [SECTION], 1)  # touching only
```

- [ ] **Step 2: Run, expect RED**

Run: `uv run pytest tests/test_relevance.py -q`
Expected: 1 failed (`test_short_chunk_fully_inside_meets_the_sensitivity_threshold`), the others pass.

- [ ] **Step 3: Implement** (Serena `replace_symbol_body` on `is_relevant`)

```python
def is_relevant(chunk: dict, sections: list[dict], min_overlap: int) -> bool:
    """True if the chunk overlaps a section by at least min(min_overlap, chunk length) tokens.

    Capping the threshold at the chunk length keeps a chunk shorter than min_overlap eligible
    when it lies fully inside a relevant section; at least one shared token is always needed
    (ADR 0026).
    """
    needed = max(1, min(min_overlap, chunk["end_token"] - chunk["start_token"]))
    return any(overlap_tokens(chunk, s) >= needed for s in sections)
```

- [ ] **Step 4: Run, expect GREEN**

Run: `uv run pytest tests/test_relevance.py tests/test_retrieve.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
set -e; git add src/relevance.py tests/test_relevance.py
uvx pre-commit run --files src/relevance.py tests/test_relevance.py | tee /tmp/pc.txt; ! grep -q Failed /tmp/pc.txt
git commit -m "feat(relevance): Sensitivitätsschwelle höchstens Chunk-Länge"
git push
```

---

### Task 2: Cleaner rules for the API pages; guide stays byte-identical (V1)

**Files:**
- Modify: `src/preprocess.py` (new constants `ESCAPED_LT_RE`, `BR_RE`; changed `V_PRE_SPAN_RE`; new `heading_title`; `clean_markdown`)
- Modify: `src/ingest.py` (`title_of`)
- Test: `tests/test_clean_markdown.py`, `tests/test_ingest.py`

**Interfaces:**
- Produces: `preprocess.heading_title(raw: str) -> str` (inline `<br>` → space, `\<` → `<`), used by `ingest.title_of` and for `Heading.title`. Cleaned *text* keeps the CommonMark escape `\<` (source-faithful and distinguishable from leftover HTML).

- [ ] **Step 1: Write the failing tests** (append to `tests/test_clean_markdown.py`)

```python
def test_escaped_angle_brackets_are_text_not_html():
    result = clean_markdown(
        "# \\<script setup> {#script-setup}\n\n## PropType\\<T> {#proptype-t}\n\nUse `a\\<b`.\n"
    )
    assert result.text == "# \\<script setup>\n\n## PropType\\<T>\n\nUse `a\\<b`.\n"
    assert [h.title for h in result.headings] == ["<script setup>", "PropType<T>"]


def test_real_html_next_to_an_escape_still_raises():
    with pytest.raises(ValueError, match="unhandled inline HTML"):
        clean("Keep \\<this> but <em>not</em> this.\n")


def test_inline_line_break_becomes_a_space():
    result = clean_markdown("# Composition API: <br>Dependency Injection {#di}\n\nA<br/>B\n")
    assert result.text == "# Composition API: Dependency Injection\n\nA B\n"
    assert result.headings[0].title == "Composition API: Dependency Injection"


def test_v_pre_span_around_inline_code_with_tags():
    body = "(ie. <span v-pre>`<span>Keep {{x}}</span>`</span>).\n"
    assert clean(body) == "# Title\n\n(ie. `<span>Keep {{x}}</span>`).\n"
```

Append to `tests/test_ingest.py`:

```python
def test_title_of_normalises_api_heading_markup():
    assert title_of("# \\<script setup> {#script-setup}\n") == "<script setup>"
    assert title_of("# Composition API: <br>Dependency Injection {#di}\n") == (
        "Composition API: Dependency Injection"
    )
```

- [ ] **Step 2: Run, expect RED**

Run: `uv run pytest tests/test_clean_markdown.py tests/test_ingest.py -q`
Expected: 4 failed (escaped, line break, v-pre, title_of); `test_real_html_next_to_an_escape_still_raises` passes already.

- [ ] **Step 3: Implement**

In `src/preprocess.py`, replace the `V_PRE_SPAN_RE` line and add two constants directly below `WBR_RE`:

```python
# A v-pre span holds inline code (which may itself contain tags) or plain text.
V_PRE_SPAN_RE = re.compile(r"<span v-pre>((?:`[^`]*`|[^`<])*)</span>")
BR_RE = re.compile(r"\s*<br\s*/?>\s*")  # inline line break (API page titles): a space
ESCAPED_LT_RE = re.compile(r"\\<")  # CommonMark escape: literal "<", never a tag
```

Add after `has_anchored_heading`:

```python
def heading_title(raw: str) -> str:
    """Display title of a heading: inline line breaks as spaces, escaped `\\<` as `<`."""
    return ESCAPED_LT_RE.sub("<", BR_RE.sub(" ", raw)).strip()
```

In `clean_markdown`, add `(BR_RE, " "),` to the substitution tuple right after `(WBR_RE, ""),`, and change the two checks and the heading handling (Serena `replace_content`):

```python
        prose = ESCAPED_LT_RE.sub("", INLINE_CODE_RE.sub("", line))
```

(replaces `prose = INLINE_CODE_RE.sub("", line)`), and

```python
                pending.append((len(out), level, heading_title(title), a.group(1)))
```

(replaces `pending.append((len(out), level, title, a.group(1)))`).

In `src/ingest.py`: import `heading_title` from `preprocess` and change the return in `title_of` to `return heading_title(m.group(1))`.

- [ ] **Step 4: Run, expect GREEN**

Run: `uv run pytest -q`
Expected: all pass (165 + 9 new).

- [ ] **Step 5: V1 — guide artefacts byte-identical with the new cleaner**

The current `data/raw/vue_docs_snapshot/guide` and `data/processed/*` are from `b75d188`. Run:

```bash
set -e; uv run python - <<'EOF'
import filecmp, sys, tempfile
from pathlib import Path
sys.path.insert(0, "src")
from config import CORPUS_MANIFEST_FILE, DATA_RAW, DOCUMENTS_FILE, SECTIONS_FILE
from ingest import ingest
from preprocess import preprocess
t = Path(tempfile.mkdtemp())
ingest(DATA_RAW, t / "d.jsonl")
preprocess(t / "d.jsonl", t / "s.jsonl", t / "m.csv")
same = [filecmp.cmp(a, b, shallow=False) for a, b in
        ((t / "d.jsonl", DOCUMENTS_FILE), (t / "s.jsonl", SECTIONS_FILE), (t / "m.csv", CORPUS_MANIFEST_FILE))]
print("V1", same); assert all(same)
EOF
```

Expected: `V1 [True, True, True]`. If not: stop, systematic-debugging; the guide must not change.

- [ ] **Step 6: Commit**

```bash
set -e; git add src/preprocess.py src/ingest.py tests/test_clean_markdown.py tests/test_ingest.py
uvx pre-commit run --all-files | tee /tmp/pc.txt; ! grep -q Failed /tmp/pc.txt
git commit -m "feat(preprocess): API-Sonderfälle (escapte Klammern, <br>, v-pre um Code)"
git push
```

---

### Task 3: Snapshot and ingest over several areas with exclusions; manifest sections

**Files:**
- Modify: `src/config.py` (corpus block), `src/snapshot.py` (`copy_markdown`, `snapshot`, `__main__`), `src/ingest.py` (`ingest`, docstring), `src/preprocess.py` (`manifest_section`, new `AREA_SECTIONS`)
- Test: `tests/test_snapshot.py` (rewrite fixture and calls), `tests/test_ingest.py`, `tests/test_preprocess.py`

**Interfaces:**
- Produces: config `VUE_DOCS_ROOT = "src"`, `VUE_DOCS_AREAS`, `VUE_DOCS_EXCLUDED` (remove `VUE_DOCS_SUBDIR`, `SNAPSHOT_SUBDIR`; Serena `find_referencing_symbols` confirms only `snapshot.py`, `ingest.py` use them).
- `snapshot(repo_url=…, commit=…, out_dir=DATA_RAW, info_file=SNAPSHOT_INFO_FILE, root=VUE_DOCS_ROOT, areas=VUE_DOCS_AREAS, excluded=VUE_DOCS_EXCLUDED) -> int`
- `copy_markdown(src_root: Path, out_dir: Path, areas: tuple[str, ...], excluded: tuple[str, ...]) -> list[Path]`
- `ingest(snapshot_dir=DATA_RAW, out_file=DOCUMENTS_FILE, areas=VUE_DOCS_AREAS) -> int`
- `manifest_section(path)`: `api/…` → `"API Reference"`, `style-guide/…` → `"Style Guide"`, guide unchanged, any other area raises.

- [ ] **Step 1: Config** (commit stays `b75d188` in this task; Task 5 switches it). Replace the corpus block lines `VUE_DOCS_SUBDIR = …` and `SNAPSHOT_SUBDIR = …` with:

```python
VUE_DOCS_ROOT = "src"  # documentation root in the repository
# Areas below VUE_DOCS_ROOT; the snapshot mirrors them below DATA_RAW (D25).
VUE_DOCS_AREAS = ("api", "guide", "style-guide")
# Paths below VUE_DOCS_ROOT left out of the corpus (D25): Options-API-only reference pages and the
# generated API index. Each must exist at the commit, so the list cannot rot silently.
VUE_DOCS_EXCLUDED = (
    "api/component-instance.md",
    "api/index.md",
    "api/options-composition.md",
    "api/options-lifecycle.md",
    "api/options-misc.md",
    "api/options-rendering.md",
    "api/options-state.md",
)
```

and change the section comment `# Corpus (D19, …)` to `# Corpus (D19, D25)`.

- [ ] **Step 2: Write the failing tests.** Replace the `origin` fixture and every `snapshot(...)` call in `tests/test_snapshot.py`:

```python
AREAS = ("api", "guide", "style-guide")
EXCLUDED = ("api/index.md", "api/options-state.md")


@pytest.fixture
def origin(tmp_path):
    repo = tmp_path / "origin"
    for rel, text in {
        "src/api/x.md": "# X {#x}\n",
        "src/api/index.md": "# Index {#index}\n",
        "src/api/options-state.md": "# Opt {#opt}\n",
        "src/guide/a.md": "# A {#a}\n",
        "src/guide/sub/b.md": "# B {#b}\n",
        "src/guide/img.png": "binary",
        "src/style-guide/s.md": "# S {#s}\n",
        "src/tutorial/t.md": "# T {#t}\n",
    }.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(repo.parent, "init", "-q", str(repo))
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "init")
    return repo, git(repo, "rev-parse", "HEAD")


def run(repo, sha, out, info, **kw):
    kw = {"areas": AREAS, "excluded": EXCLUDED, **kw}
    return snapshot(repo.as_uri(), sha, out, info, **kw)


def test_snapshot_copies_areas_minus_exclusions_and_writes_checksums(origin, tmp_path):
    repo, sha = origin
    out = tmp_path / "raw"
    (out / "guide").mkdir(parents=True)
    (out / ".gitkeep").write_text("")
    (out / "guide" / "stale.md").write_text("old")
    info = out / "SNAPSHOT.txt"

    assert run(repo, sha, out, info) == 4

    copied = sorted(p.relative_to(out).as_posix() for p in out.rglob("*.md"))
    assert copied == ["api/x.md", "guide/a.md", "guide/sub/b.md", "style-guide/s.md"]
    assert (out / ".gitkeep").exists()
    text = info.read_text(encoding="utf-8")
    assert f"commit: {sha}" in text and "files: 4" in text
    assert "areas: api, guide, style-guide" in text
    assert "excluded: api/index.md, api/options-state.md" in text
    digest = hashlib.sha256((out / "guide" / "a.md").read_bytes()).hexdigest()
    assert f"{digest}  guide/a.md" in text


def test_snapshot_rejects_an_exclusion_missing_at_the_commit(origin, tmp_path):
    repo, sha = origin
    with pytest.raises(FileNotFoundError, match="excluded files not in the checkout"):
        run(repo, sha, tmp_path / "raw", tmp_path / "S.txt", excluded=("api/typo.md",))


def test_snapshot_rejects_an_exclusion_outside_the_areas(origin, tmp_path):
    repo, sha = origin
    with pytest.raises(ValueError, match="outside the areas"):
        run(repo, sha, tmp_path / "raw", tmp_path / "S.txt", excluded=("tutorial/t.md",))


def test_snapshot_rejects_a_missing_area(origin, tmp_path):
    repo, sha = origin
    with pytest.raises(FileNotFoundError, match="src/missing"):
        run(repo, sha, tmp_path / "raw", tmp_path / "S.txt", areas=("missing",), excluded=())
```

Adapt the remaining four tests to `run(...)`: `test_snapshot_bytes_ignore_users_autocrlf` (`run(repo, sha, out, out / "SNAPSHOT.txt")`), `test_snapshot_rejects_unknown_commit` (`run(repo, "0" * 40, …)`), `test_snapshot_keeps_an_existing_matching_record` and `test_snapshot_rejects_files_that_differ_from_the_record` (both `run(repo, sha, out, info)`); delete `test_snapshot_rejects_missing_subdir` (replaced above).

Append to `tests/test_ingest.py`:

```python
def test_ingest_orders_all_areas_by_path(tmp_path):
    snap = tmp_path / "snap"
    make_snapshot(
        snap,
        {
            "style-guide/rules.md": "# Rules {#rules}\n",
            "guide/intro.md": "# Intro {#intro}\n",
            "api/core.md": "# Core {#core}\n",
        },
    )
    out = tmp_path / "documents.jsonl"
    assert ingest(snap, out, areas=("api", "guide", "style-guide")) == 3
    docs = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [(d["doc_id"], d["path"]) for d in docs] == [
        ("D001", "api/core.md"),
        ("D002", "guide/intro.md"),
        ("D003", "style-guide/rules.md"),
    ]


def test_ingest_requires_every_area(tmp_path):
    make_snapshot(tmp_path / "snap", {"guide/intro.md": "# Intro {#intro}\n"})
    with pytest.raises(FileNotFoundError, match="api"):
        ingest(tmp_path / "snap", tmp_path / "d.jsonl", areas=("api", "guide"))
```

In `test_ingest_assigns_ids_by_path_and_writes_exact_keys` change the call to `ingest(snap, out, areas=("guide",))`.

In `tests/test_preprocess.py` extend the `test_manifest_section` parameters with `("api/reactivity-core.md", "API Reference")` and `("style-guide/rules-essential.md", "Style Guide")`, and add:

```python
def test_manifest_section_unknown_area_raises():
    with pytest.raises(ValueError, match="no manifest section"):
        manifest_section("tutorial/step-1.md")
```

- [ ] **Step 3: Run, expect RED**

Run: `uv run pytest tests/test_snapshot.py tests/test_ingest.py tests/test_preprocess.py -q`
Expected: import error in `snapshot.py`/`ingest.py` (`SNAPSHOT_SUBDIR` gone) → collection errors. That is the RED for this task.

- [ ] **Step 4: Implement `snapshot.py`** (Serena `replace_symbol_body` for `copy_markdown` and `snapshot`; update imports, module docstring and `__main__`)

```python
def copy_markdown(
    src_root: Path, out_dir: Path, areas: tuple[str, ...], excluded: tuple[str, ...]
) -> list[Path]:
    """Replace out_dir/<area> with the *.md files below src_root/<area>, minus `excluded`
    (paths relative to src_root); return the copied paths relative to out_dir."""
    outside = [e for e in excluded if e.split("/", 1)[0] not in areas]
    if outside:
        raise ValueError(f"excluded files outside the areas {list(areas)}: {outside}")
    missing = [e for e in excluded if not (src_root / e).is_file()]
    if missing:
        raise FileNotFoundError(f"excluded files not in the checkout: {missing}")
    copied: list[Path] = []
    for area in areas:
        src_dir = src_root / area
        if not src_dir.is_dir():
            raise FileNotFoundError(f"{src_dir} not found in the checkout")
        files = [
            p for p in sorted(src_dir.rglob("*.md"))
            if p.relative_to(src_root).as_posix() not in excluded
        ]
        if not files:
            raise FileNotFoundError(f"no Markdown files below {src_dir}")
        target = out_dir / area
        if target.exists():
            shutil.rmtree(target)
        for src in files:
            dst = out_dir / src.relative_to(src_root)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(dst.relative_to(out_dir))
    return sorted(copied, key=lambda p: p.as_posix())


def snapshot(
    repo_url: str = VUE_DOCS_REPO_URL,
    commit: str = VUE_DOCS_COMMIT,
    out_dir: Path = DATA_RAW,
    info_file: Path = SNAPSHOT_INFO_FILE,
    root: str = VUE_DOCS_ROOT,
    areas: tuple[str, ...] = VUE_DOCS_AREAS,
    excluded: tuple[str, ...] = VUE_DOCS_EXCLUDED,
) -> int:
    """Fetch the pinned commit, copy the Markdown files of the areas, then write or verify the
    record."""
    if shutil.which("git") is None:
        raise RuntimeError("git is required to create the snapshot")
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        checkout = Path(tmp)
        commit_date = fetch_commit(repo_url, commit, checkout)
        files = copy_markdown(checkout / root, out_dir, areas, excluded)
    lines = [
        f"repository: {repo_url}",
        f"commit: {commit}",
        f"commit_date: {commit_date}",
        f"snapshot_date: {date.today().isoformat()}",
        f"areas: {', '.join(areas)}",
        f"excluded: {', '.join(excluded)}",
        f"files: {len(files)}",
        "",
    ]
    lines += [
        f"{hashlib.sha256((out_dir / f).read_bytes()).hexdigest()}  {f.as_posix()}" for f in files
    ]
    if info_file.exists():
        # The versioned record is the reference: verify against it instead of rewriting it.
        recorded = info_file.read_text(encoding="utf-8").splitlines()
        if f"commit: {commit}" not in recorded or _checksums(recorded) != _checksums(lines):
            raise ValueError(
                f"fetched snapshot does not match the record {info_file}; "
                "delete the record to store a new snapshot"
            )
        return len(files)
    info_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(files)
```

Imports: replace `SNAPSHOT_SUBDIR` and `VUE_DOCS_SUBDIR` with `VUE_DOCS_AREAS`, `VUE_DOCS_EXCLUDED`, `VUE_DOCS_ROOT`. Module docstring: "…copies every Markdown file of config.VUE_DOCS_AREAS below config.VUE_DOCS_ROOT, minus config.VUE_DOCS_EXCLUDED, to data/raw/vue_docs_snapshot/<area>/ and writes docs/corpus_snapshot.txt…". `__main__`: `print(f"{snapshot()} files -> {DATA_RAW}")`.

- [ ] **Step 5: Implement `ingest`** (Serena `replace_symbol_body`; import `VUE_DOCS_AREAS` instead of `SNAPSHOT_SUBDIR`; docstring "Reads <area>/**/*.md for every configured area …")

```python
def ingest(
    snapshot_dir: Path = DATA_RAW,
    out_file: Path = DOCUMENTS_FILE,
    areas: tuple[str, ...] = VUE_DOCS_AREAS,
) -> int:
    """Load the Markdown files of all areas, count tokens, write documents.jsonl; return count."""
    files: list[Path] = []
    for area in areas:
        found = list((snapshot_dir / area).glob("**/*.md"))
        if not found:
            raise FileNotFoundError(
                f"no Markdown files under {snapshot_dir / area}; run src/snapshot.py first"
            )
        files += found
    files.sort(key=lambda p: p.relative_to(snapshot_dir).as_posix())
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
```

- [ ] **Step 6: Implement `manifest_section`** (add `AREA_SECTIONS = {"api": "API Reference", "style-guide": "Style Guide"}` above `SECTION_NAMES`, comment `# Manifest section of the areas without subfolders (D25)`)

```python
def manifest_section(path: str) -> str:
    """Manifest `section` column: the area name, or for guide/<folder>/<page>.md the folder."""
    parts = path.split("/")
    if parts[0] in AREA_SECTIONS:
        return AREA_SECTIONS[parts[0]]
    if parts[0] != "guide":
        raise ValueError(f"{path}: no manifest section for area {parts[0]!r}")
    if len(parts) == 2:
        return "Guide"
    if parts[1] not in SECTION_NAMES:
        raise ValueError(f"{path}: no manifest section for folder {parts[1]!r}")
    return SECTION_NAMES[parts[1]]
```

- [ ] **Step 7: Run, expect GREEN**

Run: `uv run pytest -q`
Expected: all pass, except corpus integration tests, which still skip or pass on the old snapshot (only `guide/` exists; `test_every_snapshot_file_cleans` still points at `GUIDE` until Task 5).

- [ ] **Step 8: V1 again with the multi-area ingest**

Run the Task 2 Step 5 script with `ingest(DATA_RAW, t / "d.jsonl", areas=("guide",))`.
Expected: `V1 [True, True, True]`.

- [ ] **Step 9: Commit**

```bash
set -e; git add src/config.py src/snapshot.py src/ingest.py src/preprocess.py tests/test_snapshot.py tests/test_ingest.py tests/test_preprocess.py
uvx pre-commit run --all-files | tee /tmp/pc.txt; ! grep -q Failed /tmp/pc.txt
git commit -m "feat(snapshot): mehrere Bereiche mit Ausschlussliste"
git push
```

---

### Task 4: Size-matched control K1 (chunking, embedding, control retrieval)

**Files:**
- Modify: `src/config.py`, `src/chunking.py`, `src/embed.py`, `src/canary.py`, `src/retrieve.py`
- Create: `tests/test_control_strategy.py`
- Test: `tests/test_retrieve.py`, `tests/test_embed.py`

**Interfaces:**
- Produces (config): `K1_CHUNK_SIZE: int`, `K1_OVERLAP = 0`, `CONTROL_STRATEGIES = {"K1": f"fixed_{K1_CHUNK_SIZE}_no_overlap"}`, `CONTROL_CHUNK_FILES`, `CONTROL_EMBEDDING_FILES`, `CONTROL_COLLECTIONS`, `CONTROL_RETRIEVED_FILE`.
- `chunking.rounded_mean(values: list[int]) -> int` (half up), `chunking.control_size(docs: list[dict], sections: dict[str, list[dict]]) -> int`, `chunk("K1", …)` aborts unless `K1_CHUNK_SIZE == control_size(...)`.
- `embed.strategy_keys("all") -> [*STRATEGY_IDS, *CONTROL_STRATEGIES]`; `embed_and_store` resolves files/collections for K1.
- `retrieve(…, strategies: dict[str, str] = STRATEGY_IDS, collections: dict[str, str] = CHROMA_COLLECTIONS)`; `retrieve_control(embedder=…, client=None, **paths) -> int`; CLI `--control`.

- [ ] **Step 1: Config.** After `C3_MIN_TOKENS` add:

```python
# Size-matched control (D26): fixed windows of the rounded mean C3 chunk length, no overlap;
# retrieval only. Not in STRATEGY_IDS: the experiment compares C1-C3 (D5). chunking.py aborts if
# this value no longer equals the rule (round half up of the mean C3 chunk length).
K1_CHUNK_SIZE = 239  # tokens; measured on the current corpus, re-set in Task 5
K1_OVERLAP = 0
CONTROL_STRATEGIES = {"K1": f"fixed_{K1_CHUNK_SIZE}_no_overlap"}
```

After `CHROMA_COLLECTIONS` add:

```python
CONTROL_CHUNK_FILES = {"K1": DATA_PROCESSED / "chunks_k1.jsonl"}
CONTROL_EMBEDDING_FILES = {"K1": DATA_PROCESSED / "embeddings_k1.npz"}
CONTROL_COLLECTIONS = {"K1": "rag_k1"}
```

and below `RETRIEVED_RESULTS_FILE`: `CONTROL_RETRIEVED_FILE = DATA_EVAL / "retrieved_results_control.csv"`.

- [ ] **Step 2: Write the failing tests** — create `tests/test_control_strategy.py`:

```python
import json

import pytest

import chunking
from chunking import check_chunks, chunk, control_size, rounded_mean
from config import CONTROL_STRATEGIES, K1_CHUNK_SIZE, STRATEGY_IDS
from preprocess import clean_markdown, section_spans

import tokens


@pytest.fixture
def inputs(tmp_path):
    docs, sections = [], []
    for i, n in enumerate((3, 9), start=1):
        body = "\n\n".join(f"Paragraph {j}. " + "Reactive state " * 30 for j in range(n))
        markdown = f"# Page {i} {{#p{i}}}\n\n## Part {{#part}}\n\n{body}\n"
        result = clean_markdown(markdown)
        doc_id = f"D{i:03d}"
        docs.append({"doc_id": doc_id, "path": f"guide/p{i}.md", "title": f"Page {i}",
                     "text": result.text, "tokens": tokens.count(result.text)})
        sections.extend(section_spans(doc_id, result))
    docs_file, sections_file = tmp_path / "documents.jsonl", tmp_path / "sections.jsonl"
    docs_file.write_text("".join(json.dumps(d) + "\n" for d in docs), encoding="utf-8")
    sections_file.write_text("".join(json.dumps(s) + "\n" for s in sections), encoding="utf-8")
    by_doc = {d["doc_id"]: [s for s in sections if s["doc_id"] == d["doc_id"]] for d in docs}
    return docs, by_doc, docs_file, sections_file


def test_control_is_kept_apart_from_the_experiment():
    assert list(CONTROL_STRATEGIES) == ["K1"]
    assert set(CONTROL_STRATEGIES).isdisjoint(STRATEGY_IDS)
    assert CONTROL_STRATEGIES["K1"] == f"fixed_{K1_CHUNK_SIZE}_no_overlap"


@pytest.mark.parametrize(("values", "expected"), [([238, 239], 239), ([1, 2, 2], 2), ([5], 5)])
def test_rounded_mean_rounds_half_up(values, expected):
    assert rounded_mean(values) == expected


def test_k1_uses_the_c3_mean_as_window(inputs, tmp_path, monkeypatch):
    docs, by_doc, docs_file, sections_file = inputs
    size = control_size(docs, by_doc)
    monkeypatch.setattr(chunking, "K1_CHUNK_SIZE", size)
    monkeypatch.setitem(chunking.FIXED_WINDOWS, "K1", (size, 0))
    monkeypatch.setitem(chunking.MAX_LENGTH, "K1", size)
    out = tmp_path / "chunks_k1.jsonl"
    assert chunk("K1", docs_file, sections_file, out) > 0
    chunks = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert {c["strategy"] for c in chunks} == {CONTROL_STRATEGIES["K1"]}
    assert all(c["chunk_id"].startswith("K1_") for c in chunks)
    for doc in docs:
        own = [c for c in chunks if c["doc_id"] == doc["doc_id"]]
        check_chunks(doc, own, "K1")
        assert all(c["end_token"] - c["start_token"] == size for c in own[:-1])


def test_k1_refuses_a_size_that_is_not_the_c3_mean(inputs, tmp_path, monkeypatch):
    docs, by_doc, docs_file, sections_file = inputs
    monkeypatch.setattr(chunking, "K1_CHUNK_SIZE", control_size(docs, by_doc) + 1)
    with pytest.raises(ValueError, match="set config.K1_CHUNK_SIZE"):
        chunk("K1", docs_file, sections_file, tmp_path / "k1.jsonl")
```

Append to `tests/test_retrieve.py` (add imports `from config import CHROMA_COLLECTIONS, CONTROL_STRATEGIES, STRATEGY_IDS`):

```python
def control_paths(paths, tmp_path):
    return {
        **paths,
        "chunk_files": {"K1": paths["chunk_files"]["C1"]},
        "vector_files": {"K1": paths["vector_files"]["C1"]},
        "out_file": tmp_path / "retrieved_results_control.csv",
    }


def test_control_retrieval_writes_only_the_control(setup, tmp_path):
    paths, *_ = setup
    n = retrieve(
        embedder=FakeEmbedder(),
        strategies=CONTROL_STRATEGIES,
        collections={"K1": CHROMA_COLLECTIONS["C1"]},
        **control_paths(paths, tmp_path),
    )
    rows = read_out(tmp_path / "retrieved_results_control.csv")
    assert rows[0] == HEADER and n == 2 * 5 == len(rows) - 1
    assert {r[1] for r in rows[1:]} == {"K1"}
    assert json.loads(paths["runs_file"].read_text().splitlines()[-1])["strategy"] == "K1"


def test_a_partial_strategy_set_is_refused(setup):
    paths, *_ = setup
    with pytest.raises(ValueError, match="experiment set or the control set"):
        retrieve(embedder=FakeEmbedder(), strategies={"C1": STRATEGY_IDS["C1"]}, **paths)


def test_control_files_in_the_experiment_are_refused(setup):
    paths, *_ = setup
    mixed = {**paths, "chunk_files": {**paths["chunk_files"], "K1": paths["chunk_files"]["C1"]}}
    with pytest.raises(ValueError, match="must cover exactly the strategies"):
        retrieve(embedder=FakeEmbedder(), **mixed)
```

In `tests/test_embed.py` replace `test_cli_strategies_come_from_the_config`:

```python
def test_cli_strategies_come_from_the_config(monkeypatch):
    import embed

    monkeypatch.setattr(embed, "STRATEGY_IDS", {"C1": "a", "C2": "b", "C3": "c", "C4": "d"})
    monkeypatch.setattr(embed, "CONTROL_STRATEGIES", {"K1": "k"})
    assert embed.strategy_keys("all") == ["C1", "C2", "C3", "C4", "K1"]
    assert embed.strategy_keys("K1") == ["K1"]
```

- [ ] **Step 3: Run, expect RED**

Run: `uv run pytest tests/test_control_strategy.py tests/test_retrieve.py tests/test_embed.py -q`
Expected: ImportError (`control_size`/`rounded_mean`) and failures for the new retrieve/embed tests.

- [ ] **Step 4: Implement `chunking.py`** (Serena; references checked in this plan: `make_chunks`, `chunk`, `summary`, CLI)

Imports add `math`, `CHUNKS_C3_FILE` is *not* needed; add `CONTROL_CHUNK_FILES`, `CONTROL_STRATEGIES`, `K1_CHUNK_SIZE`, `K1_OVERLAP`. Replace the two module dicts:

```python
ALL_STRATEGIES = {**STRATEGY_IDS, **CONTROL_STRATEGIES}  # experiment + control (D26)
ALL_CHUNK_FILES = {**CHUNK_FILES, **CONTROL_CHUNK_FILES}
FIXED_WINDOWS = {
    "C1": (C1_CHUNK_SIZE, C1_OVERLAP),
    "C2": (C2_CHUNK_SIZE, C2_OVERLAP),
    "K1": (K1_CHUNK_SIZE, K1_OVERLAP),
}
MAX_LENGTH = {"C1": C1_CHUNK_SIZE, "C2": C2_CHUNK_SIZE, "C3": C3_MAX_TOKENS, "K1": K1_CHUNK_SIZE}
```

In `make_chunks` use `"strategy": ALL_STRATEGIES[key]`. Add after `structure_spans`:

```python
def rounded_mean(values: list[int]) -> int:
    """Mean rounded half up (the K1 size rule, D26)."""
    return math.floor(statistics.mean(values) + 0.5)


def _spans(key: str, doc: dict, doc_sections: list[dict]) -> list[Span]:
    """Spans of one document for strategy key."""
    n = doc["tokens"]
    if key in FIXED_WINDOWS:
        return fixed_size_spans(n, *FIXED_WINDOWS[key])
    heads = [s["start_token"] for s in doc_sections]
    if min(heads) != 0:
        raise ValueError(f"{doc['doc_id']}: the first section does not start at token 0")
    breaks = paragraph_breaks(doc["text"], tokens.token_starts(doc["text"]), 0, n)
    return structure_spans(n, heads, breaks, C3_MAX_TOKENS, C3_MIN_TOKENS)


def control_size(docs: list[dict], sections: dict[str, list[dict]]) -> int:
    """K1 window size by rule: rounded mean length of the C3 chunks of these documents."""
    return rounded_mean(
        [b - a for d in docs for a, b in _spans("C3", d, sections[d["doc_id"]])]
    )
```

Replace `chunk`:

```python
def chunk(
    strategy_key: str,
    docs_file: Path = DOCUMENTS_FILE,
    sections_file: Path = SECTIONS_FILE,
    out_file: Path | None = None,
) -> int:
    """Produce the chunk file for strategy_key (C1-C3 or the control K1); return the count."""
    if strategy_key not in ALL_STRATEGIES:
        raise ValueError(f"unknown strategy {strategy_key!r}")
    out_file = out_file or ALL_CHUNK_FILES[strategy_key]
    docs = _read_jsonl(docs_file, "run src/preprocess.py first")
    sections = _sections_by_doc(docs, sections_file)
    if strategy_key in CONTROL_STRATEGIES:
        measured = control_size(docs, sections)
        if measured != K1_CHUNK_SIZE:
            raise ValueError(
                f"K1_CHUNK_SIZE is {K1_CHUNK_SIZE}, the C3 chunks have a rounded mean of "
                f"{measured} tokens; set config.K1_CHUNK_SIZE = {measured}"
            )

    chunks: list[dict] = []
    for doc in docs:
        doc_chunks = make_chunks(doc, _spans(strategy_key, doc, sections[doc["doc_id"]]), strategy_key)
        check_chunks(doc, doc_chunks, strategy_key)
        chunks.extend(doc_chunks)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    return len(chunks)
```

Note: the test monkeypatches `chunking.K1_CHUNK_SIZE`, so `chunk` must read the module global (as above), not a value captured at import.

`summary`: `out_file = out_file or ALL_CHUNK_FILES[strategy_key]`. CLI: description "Chunk documents.jsonl with C1-C3 and the control K1.", `choices=[*ALL_STRATEGIES, "all"]`, `keys = list(ALL_STRATEGIES) if args.strategy == "all" else [args.strategy]` (K1 last, after C3). Module docstring: add line `K1: control, fixed-size = rounded mean C3 length, overlap 0 (config.K1_CHUNK_SIZE, ADR 0026)`.

- [ ] **Step 5: Implement `embed.py` and `canary.py`**

`embed.py` imports add `CONTROL_CHUNK_FILES`, `CONTROL_COLLECTIONS`, `CONTROL_EMBEDDING_FILES`, `CONTROL_STRATEGIES`. Module constants after imports:

```python
ALL_CHUNK_FILES = {**CHUNK_FILES, **CONTROL_CHUNK_FILES}
ALL_EMBEDDING_FILES = {**EMBEDDING_FILES, **CONTROL_EMBEDDING_FILES}
ALL_COLLECTIONS = {**CHROMA_COLLECTIONS, **CONTROL_COLLECTIONS}
```

`strategy_keys`:

```python
def strategy_keys(choice: str) -> list[str]:
    """CLI choice -> keys: "all" means every experiment strategy, then the control (D26)."""
    return [*STRATEGY_IDS, *CONTROL_STRATEGIES] if choice == "all" else [choice]
```

In `embed_and_store`: `chunk_file = chunk_file or ALL_CHUNK_FILES[strategy_key]`, `vector_file = vector_file or ALL_EMBEDDING_FILES[strategy_key]`, `siblings = [f for k, f in ALL_EMBEDDING_FILES.items() if k != strategy_key]`, collection `ALL_COLLECTIONS[strategy_key]`. CLI `choices=[*STRATEGY_IDS, *CONTROL_STRATEGIES, "all"]`.

`canary.py`: import `CONTROL_EMBEDDING_FILES`; `stored_files = [*EMBEDDING_FILES.values(), *CONTROL_EMBEDDING_FILES.values(), QUERY_EMBEDDINGS_FILE]`.

- [ ] **Step 6: Implement `retrieve.py`.** Imports add `CONTROL_CHUNK_FILES`, `CONTROL_COLLECTIONS`, `CONTROL_EMBEDDING_FILES`, `CONTROL_RETRIEVED_FILE`, `CONTROL_STRATEGIES`. Signature gains `strategies: dict[str, str] = STRATEGY_IDS, collections: dict[str, str] = CHROMA_COLLECTIONS` (last two parameters). Replace the mapping check at the start of the body:

```python
    if strategies not in (STRATEGY_IDS, CONTROL_STRATEGIES):
        raise ValueError("strategies must be the experiment set or the control set (D26)")
    for name, mapping in (
        ("chunk_files", chunk_files),
        ("vector_files", vector_files),
        ("collections", collections),
    ):
        if sorted(mapping) != sorted(strategies):
            raise ValueError(
                f"{name} must cover exactly the strategies {sorted(strategies)}, "
                f"got {sorted(mapping)}"
            )
```

Replace `for key in STRATEGY_IDS` in `missing` with `for key in strategies`; `strategies = list(STRATEGY_IDS)` becomes `keys = list(strategies)  # always the complete set` and every later use of the local list (`for key in strategies:` loop, `sources += …`, `"strategy": ",".join(...)`) uses `keys`; `client.get_collection(collections[key])`. Add after `retrieve`:

```python
def retrieve_control(embedder: Embedder = embed_texts, client: Any = None, **paths: Any) -> int:
    """Retrieval for the size-matched control K1 (ADR 0026): same questions, query vectors and
    ground truth as the experiment, own chunk, vector, index and result files."""
    defaults: dict[str, Any] = {
        "chunk_files": CONTROL_CHUNK_FILES,
        "vector_files": CONTROL_EMBEDDING_FILES,
        "out_file": CONTROL_RETRIEVED_FILE,
    }
    return retrieve(
        embedder,
        client,
        strategies=CONTROL_STRATEGIES,
        collections=CONTROL_COLLECTIONS,
        **{**defaults, **paths},
    )
```

CLI:

```python
if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(
        description="Retrieve the top-k chunks per question for all strategies at once."
    )
    p.add_argument("--control", action="store_true", help="the size-matched control K1 instead")
    if p.parse_args().control:
        print(f"{retrieve_control()} rows -> {CONTROL_RETRIEVED_FILE}")
    else:
        print(f"{retrieve()} rows -> {RETRIEVED_RESULTS_FILE}")
```

Module docstring: add "`--control` runs the size-matched control K1 into retrieved_results_control.csv (ADR 0026)."

- [ ] **Step 7: Run, expect GREEN; regression on the real (old) corpus**

Run: `uv run pytest -q`
Expected: all pass. Then confirm the rule on the current real corpus (old commit, no API):

```bash
set -e; uv run python - <<'EOF'
import sys; sys.path.insert(0, "src")
from chunking import _read_jsonl, _sections_by_doc, control_size
from config import DOCUMENTS_FILE, SECTIONS_FILE
docs = _read_jsonl(DOCUMENTS_FILE, ""); print("K1 size on old corpus:", control_size(docs, _sections_by_doc(docs, SECTIONS_FILE)))
EOF
```

Expected: `239` (mean 238.53 of 493 C3 chunks).

- [ ] **Step 8: Re-index and verify no stale reference** — `index_repository` (codebase-memory, mode full); `search_graph` with `query: "STRATEGY_IDS CHUNK_FILES EMBEDDING_FILES CHROMA_COLLECTIONS"` and Serena `find_referencing_symbols` for `STRATEGY_IDS`; every hit outside `retrieve`'s experiment default, the tests and `difficulty_probe.py` must use the `ALL_*`/`CONTROL_*` mappings where K1 is meant. Expected: no unintended reference.

- [ ] **Step 9: Commit**

```bash
set -e; git add src tests
uvx pre-commit run --all-files | tee /tmp/pc.txt; ! grep -q Failed /tmp/pc.txt
git commit -m "feat(control): größengleiche Kontrolle K1 neben C1-C3"
git push
```

---

### Task 5: Rebuild the corpus at `40aa88a` and validate (V2–V5; no API)

**Files:**
- Modify: `src/config.py` (`VUE_DOCS_COMMIT`, `K1_CHUNK_SIZE`), `docs/corpus_snapshot.txt` (new record), `docs/corpus_manifest.csv`, `tests/test_corpus_integration.py`

- [ ] **Step 1: Back up the old corpus artefacts** (needed for V2, the remap and the canary)

```bash
set -e; S=${TMPDIR:-/tmp}/rag-chunking-scratch
mkdir -p $S/old_corpus
cp data/processed/documents.jsonl data/processed/sections.jsonl data/processed/chunks_c*.jsonl docs/corpus_manifest.csv docs/corpus_snapshot.txt $S/old_corpus/
cp data/processed/embeddings_c*.npz $S/old_corpus/
sha256sum $S/old_corpus/* > $S/old_corpus/SHA256SUMS; wc -l $S/old_corpus/SHA256SUMS
```

Expected: 11 files listed.

- [ ] **Step 2: Switch the commit and replace the record deliberately.** In `src/config.py`: `VUE_DOCS_COMMIT = "40aa88af0094f7bab4aaf786e55c748a6a251d88"`. Then:

```bash
set -e; git rm -q docs/corpus_snapshot.txt
rm -rf data/raw/vue_docs_snapshot/guide
uv run python src/snapshot.py
```

Expected: `79 files -> …/data/raw/vue_docs_snapshot`.

- [ ] **Step 3: V3 — file list equals GitHub's tree** (independent source)

```bash
set -e; uv run python - <<'EOF'
import json, sys, urllib.request
sys.path.insert(0, "src")
from config import DATA_RAW, VUE_DOCS_AREAS, VUE_DOCS_COMMIT, VUE_DOCS_EXCLUDED, VUE_DOCS_ROOT
url = f"https://api.github.com/repos/vuejs/docs/git/trees/{VUE_DOCS_COMMIT}?recursive=1"
tree = json.load(urllib.request.urlopen(url))["tree"]
remote = {t["path"][len(VUE_DOCS_ROOT) + 1:] for t in tree if t["path"].endswith(".md")
          and t["path"].split("/")[1] in VUE_DOCS_AREAS} - set(VUE_DOCS_EXCLUDED)
local = {p.relative_to(DATA_RAW).as_posix() for p in DATA_RAW.rglob("*.md")}
print("V3", len(remote), len(local), remote == local); assert remote == local
EOF
```

Expected: `V3 79 79 True`.

- [ ] **Step 4: Ingest and preprocess**

Run: `uv run python src/ingest.py && uv run python src/preprocess.py`
Expected: `79 documents`; preprocess prints document and section counts without error (all four former API failures cleaned).

- [ ] **Step 5: V2 — only the 6 upstream-changed guide files differ**

```bash
set -e; S=${TMPDIR:-/tmp}/rag-chunking-scratch
uv run python - "$S/old_corpus" <<'EOF'
import json, sys
from pathlib import Path
old = {d["path"]: d for d in map(json.loads, open(Path(sys.argv[1]) / "documents.jsonl"))}
new = {d["path"]: d for d in map(json.loads, open("data/processed/documents.jsonl"))}
changed = sorted(p for p in old if old[p]["text"] != new[p]["text"])
print("V2 guide pages:", len(old), "changed:", changed)
assert set(old) <= set(new) and changed == sorted([
    "guide/built-ins/teleport.md", "guide/built-ins/transition-group.md",
    "guide/components/slots.md", "guide/essentials/component-basics.md",
    "guide/essentials/lifecycle.md", "guide/extras/render-function.md"])
EOF
```

Expected: 52 guide pages, exactly these 6 changed. If a changed file's cleaned text is identical (e.g. a change only in a dropped promo block), the assertion lists fewer: read that file's upstream change in the GitHub compare `b75d188...40aa88a`, then record the finding and adjust the expected list with a ledger ruling — never silence an unexpected extra file.

- [ ] **Step 6: V4 — read the formerly failing API spots by hand**

```bash
uv run python - <<'EOF'
import json
for d in map(json.loads, open("data/processed/documents.jsonl")):
    if d["path"] in {"api/built-in-directives.md", "api/composition-api-dependency-injection.md",
                     "api/sfc-script-setup.md", "api/utility-types.md"}:
        lines = [l for l in d["text"].splitlines() if "textContent" in l or l.startswith("#")][:6]
        print("==", d["doc_id"], d["path"], "|", d["title"]); print("\n".join(lines))
EOF
```

Expected (read, do not skim): titles `<script setup>`, `Composition API: Dependency Injection`; headings `\<script setup>`, `PropType\<T>` …; the `v-text` line ends with `` (ie. `<span>Keep this but update a {{dynamicPortion}}</span>`). `` with no stray `</span>`. Record anything unexpected.

- [ ] **Step 7: Integration tests for the new corpus.** In `tests/test_corpus_integration.py`: import `VUE_DOCS_AREAS`; replace `GUIDE = DATA_RAW / "guide"` and `EXPECTED_FILES = 52  # ADR 0019` with

```python
SNAPSHOT_DIRS = [DATA_RAW / area for area in VUE_DOCS_AREAS]
HAS_SNAPSHOT = all(d.is_dir() for d in SNAPSHOT_DIRS)
EXPECTED_FILES = 79  # ADR 0025: guide 52, API 22, style guide 5


def snapshot_files():
    return sorted(p for d in SNAPSHOT_DIRS for p in d.rglob("*.md"))
```

Use `@pytest.mark.skipif(not HAS_SNAPSHOT, …)` and `snapshot_files()` in `test_every_snapshot_file_cleans` and `test_snapshot_matches_the_versioned_checksums` (`files = {p.relative_to(DATA_RAW).as_posix(): p for p in snapshot_files()}`). In the markup regex prefix the tag alternative with `(?<!\\)`: `r'(?<!\\)</?[A-Za-z][\w-]*(?:\s[^>]*)?/?>|class="options-api"|\{#|vuejs\.org/#'`. Add:

```python
@pytest.mark.skipif(not SECTIONS_FILE.exists(), reason="not preprocessed; run src/preprocess.py")
def test_corpus_areas_and_exclusions():
    docs = [json.loads(line) for line in DOCUMENTS_FILE.read_text(encoding="utf-8").splitlines()]
    areas = [d["path"].split("/", 1)[0] for d in docs]
    assert {a: areas.count(a) for a in VUE_DOCS_AREAS} == {"api": 22, "guide": 52, "style-guide": 5}
    assert not {d["path"] for d in docs} & set(VUE_DOCS_EXCLUDED)
```

and `test_real_corpus_chunks` parametrized over `[*STRATEGY_IDS, *CONTROL_STRATEGIES]` (K1 joins after Step 8 sets its size). Run: `uv run pytest tests/test_corpus_integration.py -q` → all pass except `test_real_corpus_chunks[K1]` (size still 239 unless the new mean happens to be 239) and the vector test for the outdated embeddings (`ids` mismatch) — both expected until Steps 8 and Task 7.

- [ ] **Step 8: V5 — chunk, set K1 by rule, measure the ceiling**

```bash
set -e; uv run python src/chunking.py --strategy C1; uv run python src/chunking.py --strategy C2; uv run python src/chunking.py --strategy C3
uv run python - <<'EOF'
import sys; sys.path.insert(0, "src")
from chunking import _read_jsonl, _sections_by_doc, control_size, paragraph_breaks, structure_spans
from config import C3_MIN_TOKENS, DOCUMENTS_FILE, SECTIONS_FILE
import tokens
docs = _read_jsonl(DOCUMENTS_FILE, ""); secs = _sections_by_doc(docs, SECTIONS_FILE)
print("K1 size by rule:", control_size(docs, secs))
for cap in (800, 10**6):
    L = []
    for d in docs:
        n = d["tokens"]; heads = [s["start_token"] for s in secs[d["doc_id"]]]
        L += [b - a for a, b in structure_spans(n, heads, paragraph_breaks(d["text"], tokens.token_starts(d["text"]), 0, n), cap, C3_MIN_TOKENS)]
    print(f"cap {cap}: chunks {len(L)}, >800 {sum(x > 800 for x in L)}, max {max(L)}")
print("sections:", sum(len(v) for v in secs.values()), "tokens:", sum(d["tokens"] for d in docs))
EOF
```

Set `K1_CHUNK_SIZE` in `src/config.py` to the printed size (comment: `# tokens; rounded mean of the C3 chunks at 40aa88a, measured 14.10.2026`), then:

Run: `uv run python src/chunking.py --strategy K1 && uv run pytest tests/test_corpus_integration.py -q -k "not reference_vectors"`
Expected: K1 summary line; all selected integration tests pass. Note every printed number for the docs (Task 8).

- [ ] **Step 9: Commit**

```bash
set -e; git add src/config.py docs/corpus_snapshot.txt docs/corpus_manifest.csv tests/test_corpus_integration.py
uvx pre-commit run --all-files | tee /tmp/pc.txt; ! grep -q Failed /tmp/pc.txt
git commit -m "feat(corpus): Guide, API-Referenz und Style Guide auf vuejs/docs 40aa88a"
git push
```

---

### Task 6: Remap the pilot ground truth (V8; no API)

**Files:**
- Create: `scripts/remap_pilot.py`
- Modify: `data/pilot/ground_truth.csv`, `data/pilot/hard/ground_truth.csv`

- [ ] **Step 1: Write the script**

```python
"""One-off: remap the pilot ground truth from the old corpus IDs to the new ones (ADR 0025).

Documents are matched by path, sections by anchor; title and level must agree. Prints every
annotated section and marks those whose cleaned text changed between the corpora, so they can be
checked by hand. Aborts if a document or section no longer exists.

Usage: uv run python scripts/remap_pilot.py OLD_DIR PILOT_DIR [PILOT_DIR ...]
OLD_DIR holds documents.jsonl and sections.jsonl of the old corpus.
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import tokens  # noqa: E402
from config import DOCUMENTS_FILE, ID_SEPARATOR, SECTIONS_FILE  # noqa: E402
from retrieve import GROUND_TRUTH_HEADER, split_ids  # noqa: E402


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def section_text(doc: dict, section: dict) -> str:
    starts = tokens.token_starts(doc["text"])

    def char(t: int) -> int:
        return starts[t] if t < len(starts) else len(doc["text"])

    return doc["text"][char(section["start_token"]) : char(section["end_token"])]


def main(old_dir: Path, pilots: list[Path]) -> None:
    old_docs = {d["doc_id"]: d for d in load(old_dir / "documents.jsonl")}
    old_secs = {s["section_id"]: s for s in load(old_dir / "sections.jsonl")}
    new_docs = {d["path"]: d for d in load(DOCUMENTS_FILE)}
    new_secs = {s["section_id"]: s for s in load(SECTIONS_FILE)}
    for pilot in pilots:
        path = pilot / "ground_truth.csv"
        with path.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            mapped = []
            for sid in split_ids(row["relevant_section_ids"]):
                old = old_secs[sid]
                old_doc = old_docs[old["doc_id"]]
                if old_doc["path"] not in new_docs:
                    raise SystemExit(f"{sid}: {old_doc['path']} is not in the new corpus")
                new_doc = new_docs[old_doc["path"]]
                new_sid = f"{new_doc['doc_id']}#{old['anchor']}"
                new = new_secs.get(new_sid)
                if new is None or (new["title"], new["level"]) != (old["title"], old["level"]):
                    raise SystemExit(f"{sid}: no matching section {new_sid} in {old_doc['path']}")
                same = section_text(old_doc, old) == section_text(new_doc, new)
                flag = "" if same else "  TEXT CHANGED: check by hand"
                print(f"{pilot.name}/{row['question_id']}: {sid} -> {new_sid}{flag}")
                mapped.append(new_sid)
            row["relevant_section_ids"] = ID_SEPARATOR.join(mapped)
            row["relevant_doc_ids"] = ID_SEPARATOR.join(dict.fromkeys(s.split("#")[0] for s in mapped))
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=GROUND_TRUTH_HEADER, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main(Path(sys.argv[1]), [Path(p) for p in sys.argv[2:]])
```

- [ ] **Step 2: Run it**

```bash
set -e; S=${TMPDIR:-/tmp}/rag-chunking-scratch
uv run python scripts/remap_pilot.py $S/old_corpus data/pilot data/pilot/hard | tee $S/remap.txt
git diff --stat data/pilot
```

Expected: 8 + 23 mapped lines, no abort; `git diff` changes only the two ID columns (expected answers byte-identical — check `git diff --word-diff data/pilot`).

- [ ] **Step 3: V8 — hand check every "TEXT CHANGED" line.** For each, print old and new section text side by side (`section_text`) and confirm the annotation still holds (the answer is still in the section). Record each verdict in the experiment record (Task 8). If an annotation no longer holds: stop and ask Jonas — the pilot is not the ground truth, but a silent change would still be a result-driven edit.

- [ ] **Step 4: Commit**

```bash
set -e; git add scripts/remap_pilot.py data/pilot/ground_truth.csv data/pilot/hard/ground_truth.csv
uvx pre-commit run --all-files | tee /tmp/pc.txt; ! grep -q Failed /tmp/pc.txt
git commit -m "chore(pilot): Pilot-Ground-Truth auf neue Korpus-IDs abgebildet"
git push
```

---

### Task 7: Embed, retrieve, probe on the new corpus (V6, V7; API about USD 0.09)

**Files:**
- Modify: `scripts/difficulty_probe.py` (control run, size and context table)
- Modify (artefacts): `data/pilot/*/retrieved_results*.csv`, `data/pilot/*/runs.jsonl`

- [ ] **Step 1: Extend the probe** (Serena `replace_symbol_body` on `main`; imports add `CONTROL_CHUNK_FILES`, `CONTROL_STRATEGIES`; `from retrieve import retrieve, retrieve_control, split_ids`; add `import statistics`)

```python
def main(pilot: Path) -> None:
    out, control_out = pilot / "retrieved_results.csv", pilot / "retrieved_results_control.csv"
    common = {
        "questions_file": pilot / "questions.csv",
        "ground_truth_file": pilot / "ground_truth.csv",
        "query_file": pilot / "query_embeddings.npz",
        "runs_file": pilot / "runs.jsonl",
    }
    retrieve(out_file=out, **common)
    retrieve_control(out_file=control_out, **common)
    keys = [*STRATEGY_IDS, *CONTROL_STRATEGIES]
    files = {**CHUNK_FILES, **CONTROL_CHUNK_FILES}
    sections = {s["section_id"]: s for s in load_jsonl(SECTIONS_FILE, "")}
    gold = {
        r["question_id"]: split_ids(r["relevant_section_ids"])
        for r in read_csv(pilot / "ground_truth.csv")
    }
    kind = {
        r["question_id"]: r["notes"].removeprefix("pilot").strip() or "all"
        for r in read_csv(pilot / "questions.csv")
    }
    chunks = {c["chunk_id"]: c for k in keys for c in load_jsonl(files[k], "")}
    rows = read_csv(out) + read_csv(control_out)

    per_q: dict[tuple[str, str], tuple[float, ...]] = {}
    first: dict[tuple[str, str], str] = {}
    context: dict[str, list[int]] = {k: [] for k in keys}
    for key in keys:
        for qid, wanted in gold.items():
            ranked = sorted(
                (r for r in rows if r["question_id"] == qid and r["strategy"] == key),
                key=lambda r: int(r["rank"]),
            )
            flags = [r["is_relevant"] == "1" for r in ranked]
            covered = {
                sid
                for sid in wanted
                for r in ranked
                if overlap_tokens(chunks[r["chunk_id"]], sections[sid]) >= RELEVANCE_MIN_OVERLAP
            }
            per_q[key, qid] = scores(flags, wanted, covered)
            first[key, qid] = str(flags.index(True) + 1) if any(flags) else "-"
            context[key].append(
                sum(chunks[r["chunk_id"]]["end_token"] - chunks[r["chunk_id"]]["start_token"] for r in ranked)
            )

    print(f"{'strategy':8} {'chunks':>6} {'median':>6} {'mean':>6} {'context@5':>9}   (K1 = control)")
    for key in keys:
        lengths = [c["end_token"] - c["start_token"] for c in chunks.values() if c["chunk_id"].startswith(f"{key}_")]
        print(f"{key:8} {len(lengths):6} {statistics.median(lengths):6.0f} "
              f"{statistics.mean(lengths):6.0f} {statistics.mean(context[key]):9.0f}")

    groups = {"all": list(gold)} | {
        k: [q for q in gold if kind[q] == k] for k in dict.fromkeys(kind.values()) if k != "all"
    }
    for name, qids in groups.items():
        print(f"\n{name} (n={len(qids)})")
        print(f"{'strategy':8} {'Hit@5':>6} {'MRR':>6} {'P@5':>6} {'R@5':>6}")
        for key in keys:
            means = [sum(per_q[key, q][i] for q in qids) / len(qids) for i in range(4)]
            print(f"{key:8} " + " ".join(f"{m:6.2f}" for m in means))

    print("\nrank of the first relevant chunk (- = none in top 5), R@5 if below 1")
    print(f"{'question':8} {'kind':14} " + " ".join(f"{k:>9}" for k in keys))
    for qid in gold:
        cells = [
            first[key, qid] + (f" R{per_q[key, qid][3]:.2f}" if per_q[key, qid][3] < 1 else "")
            for key in keys
        ]
        print(f"{qid:8} {kind[qid]:14} " + " ".join(f"{c:>9}" for c in cells))

    for run in [json.loads(line) for line in (pilot / "runs.jsonl").read_text().splitlines()][-2:]:
        print(
            f"\n{run['strategy']}: {run['input_tokens']} question tokens USD {run['cost_usd']:.6f}, "
            f"vintage check {run['canary_input_tokens']} tokens USD {run['canary_cost_usd']:.6f}, "
            f"canary cosine {run['canary_min_cosine']}"
        )
```

Docstring: add "Also runs the size-matched control K1 (ADR 0026) and prints chunk size and context tokens per strategy." Run `uvx pre-commit run --files scripts/difficulty_probe.py` (ruff-format wraps the long lines; rerun until no `Failed`).

- [ ] **Step 2: Embed with a canary against the old vectors** (V6)

```bash
set -e; S=${TMPDIR:-/tmp}/rag-chunking-scratch
rm data/processed/embeddings_c1.npz data/processed/embeddings_c2.npz data/processed/embeddings_c3.npz   # backed up in Task 5
uv run python - "$S/old_corpus" <<'EOF'
import sys; from pathlib import Path
sys.path.insert(0, "src")
from embed import embed_and_store
old = sorted(Path(sys.argv[1]).glob("embeddings_c*.npz"))
run = embed_and_store("C1", siblings=old)   # model vintage checked against the 13.10. vectors
print("C1", run["vectors"], run["input_tokens"], run["cost_usd"], run["canary_min_cosine"])
EOF
uv run python src/embed.py --strategy C2; uv run python src/embed.py --strategy C3; uv run python src/embed.py --strategy K1
```

Expected: C1 canary cosine ≥ 0.999 (else the run aborts: stop and report); C2, C3, K1 each check against the files already embedded. Then verify billed = counted:

```bash
set -e; uv run python - <<'EOF'
import json
runs = [json.loads(l) for l in open("data/processed/embedding_runs.jsonl")][-4:]
for r in runs:
    key = r["strategy"]; f = f"data/processed/chunks_{key.lower()}.jsonl"
    counted = sum(c["end_token"] - c["start_token"] for c in map(json.loads, open(f)))
    print("V6", key, r["input_tokens"], counted, r["input_tokens"] == counted, round(r["cost_usd"], 4))
    assert r["input_tokens"] == counted
EOF
```

Expected: four `True` lines; total cost about USD 0.09. Then `uv run pytest tests/test_corpus_integration.py -q` → all pass (vectors match chunks, unit length).

- [ ] **Step 3: Probes on the new corpus** (questions unchanged, so stored query vectors are reused; the K1 control run reuses them too)

```bash
set -e; uv run python scripts/difficulty_probe.py | tee $S/probe1_new.txt; uv run python scripts/difficulty_probe.py data/pilot/hard | tee $S/probe2_new.txt
```

Expected: both complete (every top 5 verified exact); per-strategy and K1 tables printed.

- [ ] **Step 4: V7 — rerun is byte-identical without API**

```bash
set -e; sha256sum data/pilot/retrieved_results*.csv data/pilot/hard/retrieved_results*.csv > $S/r1.txt
uv run python scripts/difficulty_probe.py >/dev/null; uv run python scripts/difficulty_probe.py data/pilot/hard >/dev/null
sha256sum data/pilot/retrieved_results*.csv data/pilot/hard/retrieved_results*.csv | diff - $S/r1.txt && echo V7 identical
tail -4 data/pilot/runs.jsonl data/pilot/hard/runs.jsonl | grep -c '"api_called": false'
```

Expected: `V7 identical`; the rerun log lines show `api_called: false`.

- [ ] **Step 5: Commit**

```bash
set -e; git add scripts/difficulty_probe.py data/pilot
uvx pre-commit run --all-files | tee /tmp/pc.txt; ! grep -q Failed /tmp/pc.txt
git commit -m "feat(pilot): Proben auf neuem Korpus mit Kontrolle K1"
git push
```

---

### Task 8: Documentation (ADR 0025, ADR 0026, addendum ADR 0021, references)

**Files:**
- Create: `docs/adr/0025-korpus-guide-api-styleguide.md`, `docs/adr/0026-c3-vergleichbarkeit.md`
- Modify: `docs/adr/0019-korpus-ausschnitt.md` (status), `docs/adr/0021-c3-grenzen.md` (addendum), `docs/adr/README.md`, `docs/reference/corpus.md`, `docs/reference/data-formats.md`, `docs/reference/experiment-record.md`, `docs/reference/literature.md`, `docs/reference/tooling.md`, `docs/how-to/create-corpus-snapshot.md`, `docs/explanation/research-design.md`, `docs/plan.md`, `AGENTS.md`, `README.md` (if it lists steps), `.serena/memories/{core,pipeline,chunking,decisions}.md`

Numbers marked ‹T5.8› / ‹T7.2› / ‹T7.3› come from the printed output of that task step; copy them exactly.

- [ ] **Step 1: ADR 0025** (German, same structure as ADR 0019)

```markdown
# 0025. Korpus: Guide, API-Referenz (Composition) und Style Guide auf `40aa88a`

## Status

Angenommen (14.10.2026; ersetzt Ausschnitt und Commit von [ADR 0019](0019-korpus-ausschnitt.md), dessen übrige Regeln gelten weiter)

## Kontext

- Echte Open-Source-Dokumentation ist geschichtet: Konzepte (Guide), Referenz (API) und Konventionen (Style Guide); dasselbe Thema steht oft an mehreren Stellen. Ein reiner Guide-Korpus bildet das nicht ab.
- Das Exposé begrenzt den Korpus „bewusst auf ausgewählte Bereiche“; drei benannte Bereiche erfüllen das.
- Messung auf dem gepinnten Commit: API 22 Seiten, Style Guide 5 Seiten; alle H1–H3-Überschriften tragen Anker. Vier API-Seiten brauchten drei neue, getestete Bereinigungsregeln (escapte `\<`, `<br>` in Überschriften, `v-pre` um Inline-Code); der Guide bleibt damit Byte für Byte gleich.
- Tutorial: 15 Schritte (rund 6.500 Tokens) für einen interaktiven Editor; der Code liegt in eigenen Dateien, der Inhalt wiederholt den Guide (Beinahe-Duplikate, Annotationsaufwand).
- Options-API-Referenzseiten (`options-*`, `component-instance`): Die Website zeigt immer nur einen API-Stil; zwei Stile wären Beinahe-Duplikate, Fragen hätten zwei richtige Antworten, gemischter Kontext verschlechtert Antworten unabhängig vom Chunking (ADR 0006). `api/index.md` ist ein generiertes Inhaltsverzeichnis ohne Text.
- `vuejs/docs` `main` lag am 14.10.2026 acht Commits vor `b75d188` (letzter 15.09.2026); im Ausschnitt änderten sich nur sechs Guide-Dateien (+13/−9 Zeilen). Alle Artefakte werden ohnehin neu gebaut, ausgewertet ist noch nichts.

## Entscheidung

Wir werden als Korpus alle Markdown-Dateien unter `src/guide/`, `src/api/` und `src/style-guide/` aus `vuejs/docs` auf Commit `40aa88af0094f7bab4aaf786e55c748a6a251d88` verwenden, ohne `api/index.md`, `api/component-instance.md` und `api/options-{composition,lifecycle,misc,rendering,state}.md`.
Wir werden Tutorial, Beispiele und Projektseiten (about, ecosystem, partners usw.) nicht aufnehmen.
Bereiche und Ausschlüsse stehen in [`src/config.py`](../../src/config.py) (`VUE_DOCS_AREAS`, `VUE_DOCS_EXCLUDED`).

## Konsequenzen

- Gut: realistische, geschichtete Dokumentation mit ‹T5.8 docs› Seiten und ‹T5.8 tokens› Tokens; Retrieval muss zwischen Guide, Referenz und Konventionen unterscheiden.
- Gut: Prüfungen belegt: Guide-Bereinigung unverändert (V1), nur die sechs geänderten Guide-Dateien weichen ab (V2), Dateiliste gleich dem GitHub-Baum (V3).
- Schlecht: mehr Annotationsaufwand; viele Fragen haben relevante Abschnitte in Guide und API. Die Abschnitts-Nachschlageliste stützt das.
- Neutral: Ergebnisse gelten für Composition-API-Nutzer; das steht in den Limitationen.
- Neutral: Doc-IDs wurden neu vergeben; die Pilot-Ground-Truth wurde per Skript über Pfad und Anker abgebildet.
```

- [ ] **Step 2: ADR 0026**

```markdown
# 0026. C3-Vergleichbarkeit: Größenkontrolle K1 und faire Sensitivitätsregel

## Status

Angenommen (14.10.2026; ergänzt [ADR 0005](0005-drei-chunking-strategien.md), [ADR 0019](0019-korpus-ausschnitt.md) und [ADR 0021](0021-c3-grenzen.md))

## Kontext

- C3 unterscheidet sich von C1/C2 in Struktur und Größe: auf dem Korpus Median ‹T7.3 C3 median› gegen 500 Tokens, Kontext bei top 5 im Mittel ‹T7.3 C3 context› gegen ‹T7.3 C1 context› Tokens. Ohne Kontrolle ist nicht trennbar, ob ein Unterschied aus der Struktur oder aus der Größe kommt.
- Kleinere Chunks erhöhen die Precision bei etwa gleichem Recall (Smith & Troynikov, 2024, mit `text-embedding-3-large` und fünf abgerufenen Chunks); die beste Größe hängt vom Fragetyp ab (Bhat et al., 2025).
- Die geplante Sensitivitätsprüfung (Mindestüberlappung 100 Tokens) hätte jeden Chunk unter 100 Tokens grundsätzlich ausgeschlossen, auch vollständig im relevanten Abschnitt liegende; das benachteiligt C3 systematisch.
- Die Entscheidung fällt vor dem Einfrieren der Ground Truth (ADR 0017). Zwei Pilotproben existieren und sind im Experiment-Protokoll offengelegt; die Begründung stützt sich auf das Design-Argument und die Literatur, nicht auf Pilotwerte.

## Entscheidung

Wir werden eine größengleiche Kontrolle K1 bilden: Fixed-size ohne Overlap mit der kaufmännisch gerundeten (0,5 aufwärts) mittleren C3-Chunklänge als Fenstergröße, festgelegt in `config.K1_CHUNK_SIZE` und von `chunking.py` gegen die Regel geprüft. K1 ist nicht Teil von `STRATEGY_IDS`, durchläuft Chunking, Embedding und Retrieval, aber keine Antwortgenerierung.
Wir werden in der Sensitivitätsprüfung einen Chunk als relevant werten, wenn er einen relevanten Abschnitt um mindestens min(100, Chunk-Länge) Tokens überlappt; die Hauptregel (jede Überlappung) bleibt.
Wir werden für jede Strategie Chunk-Anzahl, Median und Mittel der Chunk-Länge sowie die Kontext-Tokens je Antwort berichten.

## Konsequenzen

- Gut: Struktur- und Größeneffekt werden trennbar: Schlägt C3 C1 und K1 nicht, liegt der Effekt in der Größe; schlägt C3 auch K1, in der Struktur.
- Gut: Die Sensitivitätsprüfung benachteiligt kleine Chunks nicht mehr konstruktionsbedingt.
- Neutral: K1 kostet etwa ‹T7.2 K1 cost› USD Embedding; keine Generierungskosten.
- Schlecht: Eine vierte Retrieval-Reihe vergrößert die Auswertung; sie wird als Kontrollanalyse, nicht als vierte Strategie berichtet.
```

- [ ] **Step 3: ADR 0021 addendum** (append)

```markdown
## Nachtrag (14.10.2026): Begründung der Obergrenze 800

- Die Eingabegrenze des Embedding-Modells (8.192 Tokens) ist ein technisches Maximum, keine Empfehlung. Längere Chunks verdünnen den Vektor eines Chunks (Smith & Troynikov, 2024) und gäben C3 bei festem `top_k` mehr Kontext als C1/C2 ([ADR 0006](0006-nur-chunking-variiert.md)).
- Gemessen auf dem Korpus nach [ADR 0025](0025-korpus-guide-api-styleguide.md): Ohne Obergrenze wäre der längste Chunk ‹T5.8 max without cap› Tokens lang; die Grenze 800 teilt ‹T5.8 >800 count› von ‹T5.8 chunks without cap› Segmenten. Sie wirkt also nur auf wenige lange Abschnitte.
```

- [ ] **Step 4: References.** Exact edits:
  - `0019`: status line add „Ausschnitt und Commit ersetzt durch [ADR 0025](0025-korpus-guide-api-styleguide.md) (14.10.2026)“.
  - `docs/adr/README.md`: rows for 0025 and 0026, 0019 status „Teilweise ersetzt (0025)“.
  - `corpus.md`: table (commit `40aa88a…` 15.09.2026, Pfade drei Bereiche minus Ausschlüsse, Dateien 79, Umfang ‹T5.8›), area breakdown, relevance bullet with the new sensitivity rule; manifest example rows re-read from the new `corpus_manifest.csv`.
  - `data-formats.md`: `chunks_k1.jsonl` (`strategy` `fixed_<K1>_no_overlap`), `embeddings_k1.npz`, `retrieved_results_control.csv` (same columns as `retrieved_results.csv`, only `K1`), sentence that `retrieve.py --control` writes it.
  - `experiment-record.md`: section „Korpuserweiterung (14.10.2026)“ with snapshot (commit, 79 files), V1–V8 results, chunk table C1–C3/K1, embedding table (tokens, cost, canary), both probes on the new corpus incl. K1 and context tokens; mark the two earlier probe sections „alter Korpus (`b75d188`, nur Guide)“; list each V8 verdict.
  - `literature.md`: rows `smith2024chunking` and `bhat2025chunksize` (APA from the spec) and the GitHub compare source, accessed 14.10.2026.
  - `tooling.md`: CLI `chunking.py --strategy K1|all`, `embed.py --strategy K1|all`, `retrieve.py --control`, `scripts/remap_pilot.py`.
  - `create-corpus-snapshot.md`: three areas, exclusions, record lines `areas`/`excluded`.
  - `research-design.md`: strategy table note on K1 as control; C3 line with sizes; sensitivity rule.
  - `plan.md`: mark corpus decision done; next: section lookup list, coverage check, catalogue.
  - `AGENTS.md`: status line (corpus ADR 0025, K1), map „decisions D1–D26“.
  - Serena memories `core`, `pipeline`, `chunking`, `decisions`: one-line updates with links (Serena `edit_memory`).

- [ ] **Step 5: Link check and commit**

```bash
set -e; uv run python - <<'EOF'
import re, pathlib
bad = []
for md in pathlib.Path("docs").rglob("*.md"):
    for target in re.findall(r"\]\(([^)#]+\.md)", md.read_text(encoding="utf-8")):
        if not (md.parent / target).resolve().exists(): bad.append((str(md), target))
print(bad); assert not bad
EOF
git add docs AGENTS.md README.md .serena/memories
uvx pre-commit run --all-files | tee /tmp/pc.txt; ! grep -q Failed /tmp/pc.txt
git commit -m "docs(adr): ADR 0025 Korpus, ADR 0026 C3-Vergleichbarkeit, Nachtrag ADR 0021"
git push
```

---

### Task 9: Final verification (V9), review, PR

- [ ] **Step 1: Full verification**

```bash
set -e
uv run pytest -q
unshare -rn uv run --offline pytest -q -p no:cacheprovider
uv run pytest -q -W error::DeprecationWarning
uvx pre-commit run --all-files | tee /tmp/pc.txt; ! grep -q Failed /tmp/pc.txt
uvx pyright src scripts
```

Expected: every suite green with the same pass count; pyright 0 errors on `src` and `scripts` (warnings recorded in the PR).

- [ ] **Step 2: Review.** Dispatch the `codex-reviewer` agent on `feat/corpus-extension` against `main` (or `@codex review` on the PR if the quota is back; watch with the scratchpad watcher). Fix every P0–P2 test-first; record P3 as deferred minors.
- [ ] **Step 3: PR.** `gh pr create --base main` titled `feat(corpus): Guide, API und Style Guide; Kontrolle K1` with a body listing: spec and plan paths, ADR 0025/0026, V1–V9 results, cost, the included probe commits from `chore/difficulty-probe`. No attribution lines. Merge only after Jonas approves; afterwards remind Jonas to bump the PaperLab submodule pointer to the merge commit on `main`.
