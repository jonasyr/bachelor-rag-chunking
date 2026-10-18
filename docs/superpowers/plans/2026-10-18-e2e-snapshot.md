# e2e Snapshot and MDX Preprocessing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Vue.js corpus by the e2e documentation (`tester-army/e2e` `docs/` at `ef977f4`): snapshot, ingest
and a content-preserving MDX conversion that feeds the existing section parser.

**Architecture:** `snapshot.py` copies the 60 `.mdx` pages plus `docs.json` and the provider snippet. `ingest.py`
takes title (frontmatter) and area (`docs.json` group). New `src/mdx.py` turns one MDX page into Markdown with
explicit `{#anchor}` headings (anchors = the site's slugs); `preprocess.clean_markdown` keeps its contract
(anchored Markdown → `CleanResult`) with all Vue rules removed, so every downstream fixture keeps working.

**Tech Stack:** Python 3.12, pytest, tiktoken; git for the snapshot. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-10-18-e2e-snapshot-design.md`

## Global Constraints

- All parameters only in `src/config.py`; strategy keys/IDs unchanged.
- Tests never call the OpenAI API; snapshot tests use a local git repository.
- `documents.jsonl` keys exactly `doc_id, path, title, area, text, tokens`; `sections.jsonl` unchanged.
- A chunk's `text` stays the exact slice of its document; chunks and sections share `src/tokens.py` (ADR 0019, 0021).
- Conventional Commits with German subjects, no AI attribution; never commit `.env`.
- Code inside fences unchanged apart from the info string, its indentation and trailing whitespace.
- Every rule fails loudly; nothing unknown is dropped silently.

## Review Focus

1. A component, HTML tag or JSX expression the rules do not know: must raise with page and line, never pass through
   or vanish (test in Task 3: unknown component, stray `{expr}`).
2. A fence indented inside a component (`<Step>`, `<Accordion>`): its `#` comment lines must not become headings
   (test in Task 3: indented fence dedented, comment stays code).
3. A heading whose slug collides with the generated H1 anchor or another heading: must raise (Task 4 test via
   `clean_markdown` duplicate anchor; H1 uses the path slug).
4. Navigation and pages drifting apart (page added or removed upstream): snapshot and ingest must stop (Task 1 and
   Task 4 tests).
5. Running `preprocess.py` twice or on a stale `documents.jsonl`: must refuse (Task 4 test).

---

### Task 1: Corpus configuration and snapshot

**Files:**
- Modify: `src/config.py` (Corpus section, `DATA_RAW`, `SYSTEM_PROMPT`, site URL)
- Modify: `src/snapshot.py`
- Modify: `src/mdx.py` (create with `nav_areas` only; Task 2 extends it)
- Test: `tests/test_snapshot.py` (rewrite)
- Modify: `docs/reference/prompts.md` (prompt text, so `tests/test_prompt.py` keeps passing)

**Interfaces:**
- Produces: config keys `CORPUS_REPO_URL`, `CORPUS_COMMIT`, `CORPUS_ROOT`, `CORPUS_PAGE_SUFFIX`, `CORPUS_NAV_FILE`,
  `CORPUS_PROVIDER_SNIPPET`, `CORPUS_SUPPORT_FILES`, `CORPUS_AREAS`, `CORPUS_SITE_URL`; `DATA_RAW` →
  `data/raw/e2e_docs_snapshot`. `mdx.nav_areas(nav: dict) -> dict[str, str]` (page without suffix → area, navigation
  order). `snapshot.snapshot(repo_url, commit, out_dir, info_file, root, suffix, nav_file, support) -> int`.

- [ ] **Step 1: Replace the corpus keys in `src/config.py`**

Replace `DATA_RAW = ROOT / "data" / "raw" / "vue_docs_snapshot"` by
`DATA_RAW = ROOT / "data" / "raw" / "e2e_docs_snapshot"`, and the block from `# Corpus (D19, D25)` through
`VUE_DOCS_EXCLUDED = (...)` by:

```python
# ---------------------------------------------------------------------------
# Corpus (D19, D38)
# ---------------------------------------------------------------------------
CORPUS_REPO_URL = "https://github.com/tester-army/e2e.git"
CORPUS_COMMIT = "ef977f4856da009cac26d78d2e9bb14e5991ee41"  # 17.10.2026 (D38)
CORPUS_ROOT = "docs"  # documentation root in the repository; the snapshot mirrors it in DATA_RAW
CORPUS_PAGE_SUFFIX = ".mdx"  # every page below CORPUS_ROOT; the set must equal the navigation's pages
CORPUS_NAV_FILE = "docs.json"  # Mintlify navigation: tabs, groups, pages
CORPUS_PROVIDER_SNIPPET = "snippets/model-provider.jsx"  # data of the <ModelProvider> component
CORPUS_SUPPORT_FILES = (CORPUS_NAV_FILE, CORPUS_PROVIDER_SNIPPET)  # copied with the pages
# Areas: the navigation groups in order; pages listed directly under a tab (Examples) form one area named
# after the tab (D38). ingest.py stops if the navigation differs.
CORPUS_AREAS = (
    "Get started",
    "Platforms",
    "Features",
    "Models and agents",
    "Run in CI",
    "Hosted browsers and devices",
    "Extend",
    "Deep dive",
    "Migrate",
    "Test API",
    "Project",
    "Web",
    "Mobile",
    "Engine contract",
    "Examples",
)
```

Keep `TOKEN_ENCODING` and `SECTION_MAX_LEVEL` below it. Replace

```python
# Editor: site-relative doc links ("/api/...") in the formatted view point to the public docs
VUE_DOCS_SITE_URL = "https://vuejs.org"
```

by

```python
# Editor: site-relative doc links ("/ci#mobile-jobs") in the formatted view point to the public docs
CORPUS_SITE_URL = "https://e2e.tester.army/docs"
```

Above `AREA_MIN_QUESTIONS` change the comment to: `# Minimum number of questions with a relevant section in an
area; a question counts for every area it touches (D29). Vue areas until step 4 sets the e2e quotas (plan.md).` and
add the same "Vue areas until step 4" note to `CATALOGUE_AREA_SLOTS`. In `SYSTEM_PROMPT` replace
`about Vue.js based solely on` by `about the e2e testing framework based solely on` (line break after `based`
moves accordingly):

```python
SYSTEM_PROMPT = """You are a helpful assistant that answers questions about the e2e testing framework
based solely on the provided documentation excerpts.
Do not use any knowledge outside the provided context.
If the context does not contain sufficient information to answer the question,
state that explicitly."""
```

Update the same text in `docs/reference/prompts.md` (the test compares both).

- [ ] **Step 2: Write the failing snapshot tests** (`tests/test_snapshot.py`, full rewrite)

```python
import hashlib
import json
import subprocess

import pytest

from snapshot import snapshot

GIT_ID = ["-c", "user.name=test", "-c", "user.email=test@example.invalid"]
NAV = {
    "navigation": {
        "tabs": [
            {"tab": "Documentation", "groups": [{"group": "Start", "pages": ["index", "ci/a"]}]},
            {"tab": "Examples", "pages": ["examples"]},
        ]
    }
}
SUPPORT = ("docs.json", "snippets/p.jsx")


def git(cwd, *args):
    return subprocess.run(
        ["git", *GIT_ID, *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def make_origin(tmp_path, nav=NAV, extra=None):
    repo = tmp_path / "origin"
    files = {
        "docs/index.mdx": "---\ntitle: Home\n---\n",
        "docs/ci/a.mdx": "---\ntitle: A\n---\n",
        "docs/examples.mdx": "---\ntitle: Examples\n---\n",
        "docs/docs.json": json.dumps(nav),
        "docs/snippets/p.jsx": "export const P = 1;\n",
        "docs/images/x.png": "binary",
        "README.md": "# Repo\n",
        **(extra or {}),
    }
    for rel, text in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(repo.parent, "init", "-q", str(repo))
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "init")
    return repo, git(repo, "rev-parse", "HEAD")


@pytest.fixture
def origin(tmp_path):
    return make_origin(tmp_path)


def run(repo, sha, out, info, **kw):
    kw = {"root": "docs", "suffix": ".mdx", "nav_file": "docs.json", "support": SUPPORT, **kw}
    return snapshot(repo.as_uri(), sha, out, info, **kw)


def test_snapshot_copies_pages_and_support_files_and_writes_checksums(origin, tmp_path):
    repo, sha = origin
    out = tmp_path / "raw"
    (out / "old").mkdir(parents=True)
    (out / "old" / "stale.mdx").write_text("old")
    (out / ".gitkeep").write_text("")
    info = tmp_path / "corpus_snapshot.txt"

    assert run(repo, sha, out, info) == 5

    copied = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    assert copied == [
        ".gitkeep",
        "ci/a.mdx",
        "docs.json",
        "examples.mdx",
        "index.mdx",
        "snippets/p.jsx",
    ]
    text = info.read_text(encoding="utf-8")
    assert f"commit: {sha}" in text and "files: 5" in text and "root: docs" in text
    digest = hashlib.sha256((out / "ci" / "a.mdx").read_bytes()).hexdigest()
    assert f"{digest}  ci/a.mdx" in text
    assert "  snippets/p.jsx" in text


def test_snapshot_rejects_a_page_missing_from_the_navigation(tmp_path):
    repo, sha = make_origin(tmp_path, extra={"docs/draft.mdx": "---\ntitle: D\n---\n"})
    out = tmp_path / "raw"
    with pytest.raises(ValueError, match=r"only pages \['draft'\]"):
        run(repo, sha, out, tmp_path / "S.txt")
    assert not out.exists()  # checked before anything is copied


def test_snapshot_rejects_a_navigation_page_without_file(tmp_path):
    nav = json.loads(json.dumps(NAV))
    nav["navigation"]["tabs"][0]["groups"][0]["pages"].append("gone")
    repo, sha = make_origin(tmp_path, nav=nav)
    with pytest.raises(ValueError, match=r"only navigation \['gone'\]"):
        run(repo, sha, tmp_path / "raw", tmp_path / "S.txt")


def test_snapshot_rejects_a_missing_support_file(origin, tmp_path):
    repo, sha = origin
    with pytest.raises(FileNotFoundError, match="snippets/missing.jsx"):
        run(
            repo,
            sha,
            tmp_path / "raw",
            tmp_path / "S.txt",
            support=("docs.json", "snippets/missing.jsx"),
        )


def test_snapshot_bytes_ignore_users_autocrlf(origin, tmp_path, monkeypatch):
    repo, sha = origin
    config = tmp_path / "gitconfig"
    config.write_text("[core]\n\tautocrlf = true\n", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    out = tmp_path / "raw"

    run(repo, sha, out, tmp_path / "S.txt")

    assert (out / "index.mdx").read_bytes() == b"---\ntitle: Home\n---\n"


def test_snapshot_rejects_unknown_commit(origin, tmp_path):
    repo, _ = origin
    with pytest.raises(RuntimeError, match="git fetch"):
        run(repo, "0" * 40, tmp_path / "raw", tmp_path / "S.txt")


def test_snapshot_keeps_an_existing_matching_record(origin, tmp_path):
    repo, sha = origin
    out, info = tmp_path / "raw", tmp_path / "corpus_snapshot.txt"
    run(repo, sha, out, info)
    recorded = info.read_text(encoding="utf-8").replace(
        "snapshot_date: ", "snapshot_date: 2000-01-01 # "
    )
    info.write_text(recorded, encoding="utf-8")

    run(repo, sha, out, info)

    assert info.read_text(encoding="utf-8") == recorded


def test_snapshot_rejects_files_that_differ_from_the_record(origin, tmp_path):
    repo, sha = origin
    out, info = tmp_path / "raw", tmp_path / "corpus_snapshot.txt"
    run(repo, sha, out, info)
    info.write_text(
        info.read_text(encoding="utf-8").replace("ci/a.mdx", "ci/z.mdx"), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="does not match the record"):
        run(repo, sha, out, info)
```

Add to the same file a unit test for `nav_areas`:

```python
from mdx import nav_areas


def test_nav_areas_maps_pages_to_groups_and_direct_tab_pages_to_the_tab():
    assert nav_areas(NAV) == {"index": "Start", "ci/a": "Start", "examples": "Examples"}


def test_nav_areas_rejects_a_page_listed_twice():
    nav = {"navigation": {"tabs": [{"tab": "T", "groups": [{"group": "G", "pages": ["a", "a"]}]}]}}
    with pytest.raises(ValueError, match="listed twice"):
        nav_areas(nav)
```

- [ ] **Step 3: Run them to verify they fail**

Run: `uv run pytest tests/test_snapshot.py -q`
Expected: FAIL (`ImportError` for `mdx`, `TypeError` for the new `snapshot` keywords).

- [ ] **Step 4: Create `src/mdx.py` with `nav_areas`**

```python
"""MDX pages of the e2e documentation (Mintlify) to Markdown (ADR 0038).

nav_areas reads the navigation (docs.json). Task 2 and 3 of the snapshot plan add the frontmatter, slug,
provider snippet and page conversion.
"""


def nav_areas(nav: dict) -> dict[str, str]:
    """Page (path without suffix) -> area, in navigation order: the page's group, or the tab for pages
    listed directly under a tab."""
    areas: dict[str, str] = {}
    for tab in nav["navigation"]["tabs"]:
        entries = [(group["group"], group["pages"]) for group in tab.get("groups", [])]
        if "pages" in tab:
            entries.append((tab["tab"], tab["pages"]))
        for area, pages in entries:
            for page in pages:
                if not isinstance(page, str):
                    raise ValueError(f"nested navigation entry in {area!r}: {page!r}")
                if page in areas:
                    raise ValueError(f"page {page!r} listed twice in the navigation")
                areas[page] = area
    return areas
```

(Task 3 replaces the module docstring with the final one.)

- [ ] **Step 5: Rewrite `src/snapshot.py`**

Module docstring:

```python
"""Create the corpus snapshot (ADR 0019, ADR 0038).

Fetches config.CORPUS_COMMIT of config.CORPUS_REPO_URL (shallow), copies every page (*.mdx) below
config.CORPUS_ROOT plus config.CORPUS_SUPPORT_FILES (navigation, provider snippet) to
data/raw/e2e_docs_snapshot/ (same relative paths) and writes docs/corpus_snapshot.txt (versioned) with
repository, commit, dates, root and a sha256 per file. The pages must equal the navigation's pages.
"""
```

Imports: add `import json`; from config import `CORPUS_COMMIT, CORPUS_NAV_FILE, CORPUS_PAGE_SUFFIX,
CORPUS_REPO_URL, CORPUS_ROOT, CORPUS_SUPPORT_FILES, DATA_RAW, SNAPSHOT_INFO_FILE`; `from mdx import nav_areas`.
Keep `CHECKSUM_LINE_RE`, `GIT`, `_git`, `fetch_commit`, `_checksums`. Replace `copy_markdown` by:

```python
def copy_corpus(
    src_root: Path, out_dir: Path, suffix: str, nav_file: str, support: tuple[str, ...]
) -> list[Path]:
    """Replace the contents of out_dir (except dotfiles at its top, e.g. .gitkeep) with the pages
    (*suffix below src_root) and the support files; return the copied paths relative to out_dir.

    Everything is checked before anything is copied: the support files exist and the pages equal the
    navigation's pages, so neither list can drift silently.
    """
    missing = [s for s in support if not (src_root / s).is_file()]
    if missing:
        raise FileNotFoundError(f"support files not in the checkout: {missing}")
    pages = sorted(p.relative_to(src_root).as_posix() for p in src_root.rglob(f"*{suffix}"))
    found = {p.removesuffix(suffix) for p in pages}
    listed = set(nav_areas(json.loads((src_root / nav_file).read_text(encoding="utf-8"))))
    if found != listed:
        raise ValueError(
            f"pages and navigation differ: only pages {sorted(found - listed)}, "
            f"only navigation {sorted(listed - found)}"
        )
    if out_dir.exists():
        for child in out_dir.iterdir():
            if child.name.startswith("."):
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    copied: list[Path] = []
    for rel in [*pages, *support]:
        dst = out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_root / rel, dst)
        copied.append(Path(rel))
    return sorted(copied, key=lambda p: p.as_posix())
```

and `snapshot` by:

```python
def snapshot(
    repo_url: str = CORPUS_REPO_URL,
    commit: str = CORPUS_COMMIT,
    out_dir: Path = DATA_RAW,
    info_file: Path = SNAPSHOT_INFO_FILE,
    root: str = CORPUS_ROOT,
    suffix: str = CORPUS_PAGE_SUFFIX,
    nav_file: str = CORPUS_NAV_FILE,
    support: tuple[str, ...] = CORPUS_SUPPORT_FILES,
) -> int:
    """Fetch the pinned commit, copy pages and support files, then write or verify the record."""
    if shutil.which("git") is None:
        raise RuntimeError("git is required to create the snapshot")
    with tempfile.TemporaryDirectory() as tmp:
        checkout = Path(tmp)
        commit_date = fetch_commit(repo_url, commit, checkout)
        files = copy_corpus(checkout / root, out_dir, suffix, nav_file, support)
    lines = [
        f"repository: {repo_url}",
        f"commit: {commit}",
        f"commit_date: {commit_date}",
        f"snapshot_date: {date.today().isoformat()}",
        f"root: {root}",
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

`out_dir.mkdir` is no longer needed before the fetch (`copy_corpus` creates parents). `__main__` unchanged.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_snapshot.py tests/test_prompt.py -q`
Expected: PASS (11 + prompt tests).

- [ ] **Step 7: Commit**

```bash
git add src/config.py src/snapshot.py src/mdx.py tests/test_snapshot.py docs/reference/prompts.md
git commit -m "feat(corpus): Snapshot der e2e-Doku mit Navigationsprüfung"
```

(Other modules still import the removed `VUE_DOCS_*` keys until Task 4; run only the named tests here.)

---

### Task 2: Frontmatter, slug and provider snippet (`src/mdx.py`)

**Files:**
- Modify: `src/mdx.py`
- Test: `tests/test_mdx.py` (create)

**Interfaces:**
- Consumes: `nav_areas` (Task 1).
- Produces: `parse_frontmatter(text) -> tuple[dict[str, str], str]`; `slug(heading) -> str`;
  `parse_js_literal(src, pos=0) -> tuple[object, int]`; `ProviderSnippet` (frozen dataclass: `providers: list[dict]`,
  `install: str`, `config: str`, `model: str`, `reads_at_load: str`); `parse_provider_snippet(jsx) -> ProviderSnippet`;
  `render_provider(show, snippet) -> list[str]`.

- [ ] **Step 1: Write the failing tests** (`tests/test_mdx.py`)

```python
import pytest

from mdx import parse_frontmatter, parse_js_literal, parse_provider_snippet, render_provider, slug

SNIPPET = """export const ModelProvider = ({ show }) => {
  const providers = [
    {
      id: 'gateway',
      name: 'Vercel AI Gateway',
      group: 'AI SDK',
      packages: [],
      code: "import { gateway } from 'ai';",
      model: "gateway('openai/x')",
      env: ['AI_GATEWAY_API_KEY'],
      note: 'You can use a token instead.',
      docs: 'https://ai-sdk.dev/gateway',
    },
    {
      id: 'vertex',
      name: 'Google Vertex AI',
      group: 'AI SDK',
      packages: ['@ai-sdk/google-vertex'],
      code: `import { createVertex } from '@ai-sdk/google-vertex';

const vertex = createVertex({ project: 'p|q' });`,
      model: "vertex('gemini')",
      env: ['GOOGLE_VERTEX_PROJECT', 'GOOGLE_VERTEX_LOCATION'],
      docs: 'https://ai-sdk.dev/vertex',
      readsAtLoad: true,
    },
  ];
  const managers = [
    ['npm', 'npm install -D'],
    ['pnpm', 'pnpm add -D'],
  ];
  const config = `import type { E2EConfig } from 'e2e';
${provider.code}

export default { agents: { default: { model: ${provider.model} } } } satisfies E2EConfig;`;
  const model = `${provider.code}

const agent = { model: ${provider.model} };`;
  const note = provider.readsAtLoad
    ? 'This provider reads the variables when the config loads.'
    : null;
};
"""


def test_parse_frontmatter_reads_quoted_and_plain_values():
    meta, body = parse_frontmatter(
        '﻿---\ntitle: "e2e/runner"\ndescription: Run a suite.\n"og:image": "x.png"\n---\n\nBody\n'
    )
    assert meta == {"title": "e2e/runner", "description": "Run a suite.", "og:image": "x.png"}
    assert body == "\nBody\n"


@pytest.mark.parametrize(
    ("text", "message"),
    [("# No frontmatter\n", "no frontmatter"), ("---\ntitle: >\n  folded\n---\n", "unsupported")],
)
def test_parse_frontmatter_rejects(text, message):
    with pytest.raises(ValueError, match=message):
        parse_frontmatter(text)


@pytest.mark.parametrize(
    ("heading", "anchor"),
    [  # observed on the live site, 18.10.2026
        ("`.env` files", "env-files"),
        ("agent.act", "agent-act"),
        ("For scripts: report.json", "for-scripts-report-json"),
        ("What `--reporter` does to reporter objects", "what-reporter-does-to-reporter-objects"),
        ("`ExpectCall`, `SoftExpectCall`, and `Expect`", "expectcall-softexpectcall-and-expect"),
        ("One flow, several personas", "one-flow-several-personas"),
        ("See [the guide](/guide) first", "see-the-guide-first"),
    ],
)
def test_slug_matches_the_site(heading, anchor):
    assert slug(heading) == anchor


def test_parse_js_literal_reads_nested_values_and_escapes():
    src = "[{a: 'x\\'y', \"b\": [1, 2.5, true, null], c: `l1\nl2`,}, ] rest"
    value, end = parse_js_literal(src)
    assert value == [{"a": "x'y", "b": [1, 2.5, True, None], "c": "l1\nl2"}]
    assert src[end:] == " rest"


@pytest.mark.parametrize("src", ["[a]", "{a 1}", "`${x}`", "[1 2]"])
def test_parse_js_literal_rejects_non_literals(src):
    with pytest.raises(ValueError):
        parse_js_literal(src)


def test_parse_provider_snippet():
    snippet = parse_provider_snippet(SNIPPET)
    assert [p["id"] for p in snippet.providers] == ["gateway", "vertex"]
    assert snippet.install == "npm install -D"
    assert snippet.reads_at_load == "This provider reads the variables when the config loads."
    assert "${provider.code}" in snippet.config


def test_parse_provider_snippet_rejects_unknown_keys():
    with pytest.raises(ValueError, match="provider keys"):
        parse_provider_snippet(SNIPPET.replace("readsAtLoad: true", "extra: true"))


def test_render_provider_select_is_a_table_of_all_providers():
    rows = render_provider("select", parse_provider_snippet(SNIPPET))
    assert rows[0] == "| Provider | Group | Packages | Variables | Import | Model | Note |"
    assert rows[2] == (
        "| [Vercel AI Gateway](https://ai-sdk.dev/gateway) | AI SDK |  | `AI_GATEWAY_API_KEY` | "
        "`import { gateway } from 'ai';` | `gateway('openai/x')` | You can use a token instead. |"
    )
    assert "createVertex({ project: 'p\\|q' });`" in rows[3]
    assert rows[3].endswith("| This provider reads the variables when the config loads. |")
    assert len(rows) == 4


def test_render_provider_parts_show_the_default_selection():
    snippet = parse_provider_snippet(SNIPPET)
    assert render_provider("install", snippet) == [
        "**Install · Vercel AI Gateway**",
        "",
        "```bash",
        "npm install -D ai",
        "```",
    ]
    assert render_provider("env", snippet) == [
        "**Environment · Vercel AI Gateway**",
        "",
        "```bash",
        "export AI_GATEWAY_API_KEY=...",
        "```",
        "",
        "You can use a token instead.",
    ]
    config = render_provider("config", snippet)
    assert config[:3] == ["**e2e.config.ts · Vercel AI Gateway**", "", "```ts"]
    assert "import { gateway } from 'ai';" in config
    assert "export default { agents: { default: { model: gateway('openai/x') } } } satisfies E2EConfig;" in config
    assert render_provider("model", snippet)[0] == "**Model setup · Vercel AI Gateway**"


def test_render_provider_rejects_unknown_show():
    with pytest.raises(ValueError, match="show='other'"):
        render_provider("other", parse_provider_snippet(SNIPPET))
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_mdx.py -q`
Expected: FAIL with `ImportError: cannot import name 'parse_frontmatter'`.

- [ ] **Step 3: Implement in `src/mdx.py`** (add below the docstring; `nav_areas` stays)

```python
import re
from dataclasses import dataclass

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)
FRONTMATTER_LINE_RE = re.compile(r'^"?([\w:]+)"?:\s*(.*?)\s*$')
LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
JS_TOKEN_RE = re.compile(
    r"""\s*(?:
      (?P<str>'(?:[^'\\\n]|\\.)*'|"(?:[^"\\\n]|\\.)*")
    | (?P<tpl>`(?:[^`\\$]|\\.|\$(?!\{))*`)
    | (?P<word>[A-Za-z_$][\w$]*)
    | (?P<num>-?\d+(?:\.\d+)?)
    | (?P<punct>[\[\]{}:,])
    )""",
    re.S | re.X,
)
JS_CONSTANTS = {"true": True, "false": False, "null": None}
PROVIDER_REQUIRED = {"id", "name", "group", "packages", "code", "model", "env", "docs"}
PROVIDER_OPTIONAL = {"note", "readsAtLoad"}
PROVIDER_PARTS = {"install": "Install", "env": "Environment", "config": "e2e.config.ts", "model": "Model setup"}
READS_AT_LOAD_RE = re.compile(r"provider\.readsAtLoad\s*\?\s*('(?:[^'\\]|\\.)*')")
PLACEHOLDER_RE = re.compile(r"\$\{provider\.(\w+)\}")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """(keys, body) of a page. Values are single-line scalars, optionally quoted; anything else raises."""
    text = text.lstrip("﻿").replace("\r\n", "\n")
    m = FRONTMATTER_RE.match(text)
    if m is None:
        raise ValueError("no frontmatter")
    meta: dict[str, str] = {}
    for line in m.group(1).split("\n"):
        if not line.strip():
            continue
        f = FRONTMATTER_LINE_RE.match(line)
        if f is None or f.group(2) in (">", "|", ">-", "|-"):
            raise ValueError(f"unsupported frontmatter line: {line!r}")
        value = f.group(2)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        meta[f.group(1)] = value
    return meta, text[m.end() :]


def slug(heading: str) -> str:
    """The site's anchor of a heading: link targets and backticks dropped, lowercase, every run of other
    characters than a-z0-9 replaced by "-", "-" stripped at both ends (checked against the live site)."""
    text = LINK_RE.sub(r"\1", heading).replace("`", "").lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def _unescape(body: str) -> str:
    return re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), body, flags=re.S)


def _punct(src: str, pos: int, char: str) -> int | None:
    m = JS_TOKEN_RE.match(src, pos)
    return m.end() if m is not None and m.group("punct") == char else None


def _after_item(src: str, pos: int, close: str) -> int:
    comma = _punct(src, pos, ",")
    if comma is not None:
        return comma
    if _punct(src, pos, close) is not None:
        return pos
    raise ValueError(f"expected ',' or {close!r} at {src[pos : pos + 40]!r}")


def parse_js_literal(src: str, pos: int = 0) -> tuple[object, int]:
    """The JavaScript literal (array, object, string, template without interpolation, number,
    true/false/null) at pos, and the position after it."""
    m = JS_TOKEN_RE.match(src, pos)
    if m is None:
        raise ValueError(f"unsupported JavaScript at {src[pos : pos + 40]!r}")
    kind, text = m.lastgroup, m.group(m.lastgroup)
    if kind in ("str", "tpl"):
        return _unescape(text[1:-1]), m.end()
    if kind == "num":
        return (float(text) if "." in text else int(text)), m.end()
    if kind == "word":
        if text not in JS_CONSTANTS:
            raise ValueError(f"unsupported JavaScript identifier {text!r}")
        return JS_CONSTANTS[text], m.end()
    pos = m.end()
    if text == "[":
        items: list[object] = []
        while (close := _punct(src, pos, "]")) is None:
            value, pos = parse_js_literal(src, pos)
            items.append(value)
            pos = _after_item(src, pos, "]")
        return items, close
    if text == "{":
        obj: dict[str, object] = {}
        while (close := _punct(src, pos, "}")) is None:
            key = JS_TOKEN_RE.match(src, pos)
            if key is None or key.lastgroup not in ("word", "str"):
                raise ValueError(f"expected a key at {src[pos : pos + 40]!r}")
            name = key.group("word") or _unescape(key.group("str")[1:-1])
            colon = _punct(src, key.end(), ":")
            if colon is None:
                raise ValueError(f"expected ':' after {name!r}")
            obj[name], pos = parse_js_literal(src, colon)
            pos = _after_item(src, pos, "}")
        return obj, close
    raise ValueError(f"unexpected {text!r} at {src[pos - 1 : pos + 40]!r}")


@dataclass(frozen=True)
class ProviderSnippet:
    """Data of the <ModelProvider> snippet: the provider list, the first package manager's install
    command, the templates of the config and model views, and the note for readsAtLoad providers."""

    providers: list[dict]
    install: str
    config: str
    model: str
    reads_at_load: str


def _const(jsx: str, name: str) -> object:
    marker = f"const {name} = "
    start = jsx.find(marker)
    if start < 0:
        raise ValueError(f"provider snippet: no `{marker.strip()}`")
    return parse_js_literal(jsx, start + len(marker))[0]


def _template(jsx: str, name: str) -> str:
    m = re.search(rf"const {name} = `((?:[^`\\]|\\.)*)`;", jsx, re.S)
    if m is None:
        raise ValueError(f"provider snippet: no template `const {name}`")
    return _unescape(m.group(1))


def parse_provider_snippet(jsx: str) -> ProviderSnippet:
    providers, managers = _const(jsx, "providers"), _const(jsx, "managers")
    if not isinstance(providers, list) or not providers:
        raise ValueError("provider snippet: empty provider list")
    for p in providers:
        keys = set(p) if isinstance(p, dict) else set()
        if not PROVIDER_REQUIRED <= keys <= PROVIDER_REQUIRED | PROVIDER_OPTIONAL:
            raise ValueError(f"provider snippet: unexpected provider keys {sorted(keys)}")
    ids = [p["id"] for p in providers]
    if len(set(ids)) != len(ids):
        raise ValueError("provider snippet: duplicate provider id")
    note = READS_AT_LOAD_RE.search(jsx)
    if note is None:
        raise ValueError("provider snippet: no readsAtLoad note")
    return ProviderSnippet(
        providers=providers,
        install=managers[0][1],
        config=_template(jsx, "config"),
        model=_template(jsx, "model"),
        reads_at_load=str(parse_js_literal(note.group(1))[0]),
    )


def _note(provider: dict, snippet: ProviderSnippet) -> str:
    parts = [snippet.reads_at_load if provider.get("readsAtLoad") else "", provider.get("note", "")]
    return " ".join(p for p in parts if p)


def _cell(text: str) -> str:
    return re.sub(r"\s+", " ", text).replace("|", "\\|").strip()


def _fill(template: str, provider: dict) -> str:
    text = PLACEHOLDER_RE.sub(lambda m: str(provider[m.group(1)]), template)
    if "${" in text:
        raise ValueError(f"provider snippet: unknown placeholder in {template[:40]!r}")
    return text


def render_provider(show: str, snippet: ProviderSnippet) -> list[str]:
    """Markdown lines for <ModelProvider show=...>: `select` lists every provider as a table; the parts
    show what the site shows before any selection (first provider, first package manager)."""
    if show == "select":
        rows = [
            "| Provider | Group | Packages | Variables | Import | Model | Note |",
            "|---|---|---|---|---|---|---|",
        ]
        for p in snippet.providers:
            cells = [
                f"[{p['name']}]({p['docs']})",
                p["group"],
                ", ".join(f"`{x}`" for x in p["packages"]),
                ", ".join(f"`{x}`" for x in p["env"]),
                f"`{p['code']}`",
                f"`{p['model']}`",
                _note(p, snippet),
            ]
            rows.append("| " + " | ".join(_cell(c) for c in cells) + " |")
        return rows
    if show not in PROVIDER_PARTS:
        raise ValueError(f"unknown <ModelProvider show={show!r}>")
    p = snippet.providers[0]
    lines = [f"**{PROVIDER_PARTS[show]} · {p['name']}**", ""]
    if show == "install":
        code = ("bash", " ".join([snippet.install, "ai", *p["packages"]]))
    elif show == "env":
        code = ("bash", "\n".join(f"export {name}=..." for name in p["env"])) if p["env"] else None
    else:
        code = ("ts", _fill(snippet.config if show == "config" else snippet.model, p))
    lines += [f"```{code[0]}", *code[1].split("\n"), "```"] if code else ["No variables."]
    if show == "env" and _note(p, snippet):
        lines += ["", _note(p, snippet)]
    return lines
```

Note: `_cell` keeps empty cells empty, so the gateway row has `|  |` for no packages (the test expects two spaces).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_mdx.py tests/test_snapshot.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/mdx.py tests/test_mdx.py
git commit -m "feat(corpus): Frontmatter, Anker-Slugs und Anbieterliste aus der e2e-Doku"
```

---

### Task 3: MDX page to anchored Markdown (`mdx.to_markdown`)

**Files:**
- Modify: `src/mdx.py`
- Test: `tests/test_mdx.py` (append)

**Interfaces:**
- Consumes: `parse_frontmatter`, `slug`, `parse_js_literal`, `ProviderSnippet`, `render_provider` (Task 2);
  `config.SECTION_MAX_LEVEL`.
- Produces: `to_markdown(text: str, page: str, snippet: ProviderSnippet | None = None) -> str` — Markdown whose H1
  is `# {title} {#slug(page)}` and whose H2/H3 carry `{#slug(heading)}`; input for `preprocess.clean_markdown`.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_mdx.py`)

```python
from mdx import to_markdown


def page(body, title="Guide", description="About it."):
    return f'---\ntitle: {title}\ndescription: {description}\nicon: "x"\n---\n\n{body}'


def md(body, **kw):
    return to_markdown(page(body, **kw), "ci/guide")


def test_frontmatter_becomes_anchored_h1_and_first_paragraph():
    assert md("Text.\n") == "# Guide {#ci-guide}\n\nAbout it.\n\nText.\n"


def test_headings_get_the_site_slug_and_h4_stays_plain():
    out = md("## For scripts: report.json\n\n### `agent.act`\n\n#### Deep\n")
    assert "## For scripts: report.json {#for-scripts-report-json}" in out
    assert "### `agent.act` {#agent-act}" in out
    assert "#### Deep\n" in out


def test_body_h1_raises():
    with pytest.raises(ValueError, match="H1 in the page body"):
        md("# Second title\n")


def test_imports_dropped_and_prompt_export_rendered_in_setup_prompt():
    body = (
        "import { SetupPrompt } from '../snippets/setup-prompt-card.jsx';\n\n"
        "export const setupPrompt = `Read \\`ci.md\\`.\n\n1. Add the workflow.`;\n\n"
        "Intro.\n\n<SetupPrompt>\n\n"
        '<Prompt description={setupPrompt} children={setupPrompt} actions={["copy", "cursor"]} />\n\n'
        "</SetupPrompt>\n"
    )
    out = md(body)
    assert "import" not in out and "export" not in out
    assert "Intro.\n\n**Agent prompt**\n\n```text\nRead `ci.md`.\n\n1. Add the workflow.\n```\n" in out


def test_admonitions_accordions_tabs_become_labels():
    body = (
        "<Note>\nKeep it.\n</Note>\n\n<Warning>Inline warning.</Warning>\n\n"
        '<AccordionGroup>\n<Accordion title="Why">\nBecause.\n</Accordion>\n</AccordionGroup>\n\n'
        '<Tabs>\n<Tab title="tests/a.e2e.ts">\nTab text.\n</Tab>\n</Tabs>\n'
    )
    out = md(body)
    for expected in ("**Note**\nKeep it.", "**Warning**\nInline warning.", "**Why**\nBecause.",
                     "**tests/a.e2e.ts**\nTab text."):
        assert expected in out


def test_steps_are_numbered():
    body = '<Steps>\n  <Step title="Install">\n  Run it.\n  </Step>\n  <Step title="Configure">\n  Set it.\n  </Step>\n</Steps>\n'
    out = md(body)
    assert "**1. Install**\n  Run it." in out and "**2. Configure**\n  Set it." in out


def test_cards_become_list_items():
    body = (
        "<CardGroup cols={2}>\n"
        '<Card title="Project tools" icon="wrench" href="/tools">\n  Add tools\n  per project.\n</Card>\n'
        '<Card title="Plain">\nNo link.\n</Card>\n'
        "</CardGroup>\n"
    )
    out = md(body)
    assert "- [Project tools](/tools): Add tools per project.\n- **Plain**: No link.\n" in out


def test_videos_keep_captions_and_video_cards_keep_title_and_subtitle():
    body = (
        '<Video>\n  <video src="/images/x.mp4" aria-label="Clip." muted loop playsInline controls />\n\n'
        "  Each browser is one session.\n</Video>\n\n"
        '<VideoCard\n  id="abc"\n  title="Watch it"\n  subtitle="In two minutes."\n/>\n'
    )
    out = md(body)
    assert "Each browser is one session." in out and "<video" not in out
    assert "- **Watch it**: In two minutes." in out


def test_legacy_anchors_and_show_more_dropped_and_blank_runs_collapse():
    out = md('<a id="flags" />\n\n<ShowMore id="steps">\n\n1. One.\n\n</ShowMore>\n\n<span id="x" />\n')
    assert out == "# Guide {#ci-guide}\n\nAbout it.\n\n1. One.\n"


def test_fence_titles_become_labels_and_code_stays_verbatim():
    body = (
        '```ts title="tests/a.e2e.ts" expandable\nconst a = 1;  \n```\n\n'
        "<CodeGroup>\n```bash npm\nnpm i e2e\n```\n```bash pnpm\npnpm add e2e\n```\n</CodeGroup>\n"
    )
    out = md(body)
    assert "**tests/a.e2e.ts**\n```ts\nconst a = 1;\n```" in out
    assert "**npm**\n```bash\nnpm i e2e\n```\n\n**pnpm**\n```bash\npnpm add e2e\n```" in out


def test_indented_fence_inside_a_component_is_dedented():
    body = '<Steps>\n  <Step title="Run">\n    ```bash\n    # a comment\n    e2e run\n    ```\n  </Step>\n</Steps>\n'
    out = md(body)
    assert "```bash\n# a comment\ne2e run\n```" in out
    assert "{#a-comment}" not in out


def test_model_provider_uses_the_snippet():
    snippet = parse_provider_snippet(SNIPPET)
    out = to_markdown(page('<ModelProvider show="install" />\n'), "models", snippet)
    assert "**Install · Vercel AI Gateway**\n\n```bash\nnpm install -D ai\n```" in out


def test_model_provider_without_snippet_raises():
    with pytest.raises(ValueError, match="provider snippet"):
        md('<ModelProvider show="select" />\n')


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("<Frame>\nx\n</Frame>\n", "unknown component <Frame>"),
        ("<Note>\nopen\n", "unclosed <Note>"),
        ("<Note>\nx\n</Warning>\n", "</Warning> closes <Note>"),
        ("Text with {expression}.\n", "unhandled markup"),
        ("Text with <b>bold</b>.\n", "unhandled markup"),
        ("<SetupPrompt>\n<Prompt children={missing} />\n</SetupPrompt>\n", "unknown export 'missing'"),
        ("<Prompt children={x} />\n", "<Prompt> outside <SetupPrompt>"),
        ("<Step title=\"x\">\ny\n</Step>\n", "<Step> outside <Steps>"),
        ("```ts\nopen\n", "unclosed code fence"),
        ("```ts lines={1}\nx\n```\n", "fence info"),
    ],
)
def test_unhandled_input_raises(body, message):
    with pytest.raises(ValueError, match=message):
        md(body)


def test_errors_name_the_line():
    with pytest.raises(ValueError, match="line 4"):
        md("Fine.\n\n<Frame>\n")
```

Line numbers count the body lines after the frontmatter from 1 (the page fixture starts the body with a blank
line, so `<Frame>` is body line 4).

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_mdx.py -q`
Expected: FAIL with `ImportError: cannot import name 'to_markdown'`.

- [ ] **Step 3: Implement `to_markdown`** (append to `src/mdx.py`; add `from config import SECTION_MAX_LEVEL`)

Replace the module docstring by:

```python
"""MDX pages of the e2e documentation (Mintlify) to Markdown (ADR 0038).

to_markdown turns one page into Markdown with an anchored H1 from the frontmatter (title, then the
description as first paragraph) and the site's anchor on every H2/H3 heading. Every text a reader of the
site sees is kept: admonitions, accordions, tabs and steps become bold labels, cards and video cards list
items, agent prompts text blocks, the provider snippet a table and code blocks; code fence titles become
labels. Only imports, media embeds and legacy anchors go. Anything else raises, naming the body line.
preprocess.py then records the sections.
"""
```

Code:

```python
FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)\s*$")
IMPORT_RE = re.compile(r"""^import\s.+\sfrom\s+['"][^'"]+['"];?$""")
EXPORT_RE = re.compile(r"^export const (\w+) = ")
TAG_START_RE = re.compile(r"^\s*</?(?:[A-Z]\w*|video|a|span)\b")
TAG_RE = re.compile(r"<(/?)([A-Za-z]\w*)(.*?)(/?)>", re.S)
ATTR = r'([\w-]+)(?:=(?:"([^"]*)"|(\{[^{}]*\})))?'
ATTR_RE = re.compile(ATTR)
ATTRS_RE = re.compile(rf"(?:\s+{ATTR})*\s*")
INLINE_PAIR_RE = re.compile(r"^(\s*)(<([A-Z]\w*)(?:\s[^<>]*)?>)(.+)(</\3>)\s*$")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
MARKUP_RE = re.compile(r"</?[A-Za-z][\w-]*(?:\s[^>]*)?/?>|\{[^}]*\}")
FENCE_FLAGS = ("expandable", "wrap")
ADMONITIONS = ("Note", "Warning", "Tip")
LABELLED = ("Accordion", "Tab")
WRAPPERS = ("AccordionGroup", "Tabs", "CodeGroup", "CardGroup", "ShowMore", "Video", "SetupPrompt", "Steps")
DROPPED = ("video", "a", "span")  # media embeds and legacy anchors, always self-closing
PROMPT_LABEL = "Agent prompt"  # header text of the SetupPrompt snippet


@dataclass
class _Frame:
    name: str
    attrs: dict[str, str]
    count: int = 0  # steps so far (Steps)
    body: list[str] | None = None  # collected lines (Card)


def _tag_end(text: str) -> int:
    """Index of the ">" ending the tag at the start of text (quotes and braces skipped), or -1."""
    quote, depth = "", 0
    for k, ch in enumerate(text):
        if quote:
            quote = "" if ch == quote else quote
        elif ch in "\"'":
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == ">" and depth == 0:
            return k
    return -1


def _fence_info(info: str) -> tuple[str, str]:
    """(language, label) of a fence info string: `ts title="a.ts" expandable` -> ("ts", "a.ts"),
    `bash npm` -> ("bash", "npm")."""
    title = re.search(r'title="([^"]*)"', info)
    words = re.sub(r'\s*title="[^"]*"', "", info).split()
    rest = [w for w in words[1:] if w not in FENCE_FLAGS]
    if any(c in w for w in rest for c in "={}") or (title and rest):
        raise ValueError(f"unsupported fence info {info!r}")
    return (words[0] if words else ""), (title.group(1) if title else " ".join(rest))


def _dedent(line: str, indent: int) -> str:
    return line[min(indent, len(line) - len(line.lstrip(" "))) :]


def to_markdown(text: str, page: str, snippet: ProviderSnippet | None = None) -> str:
    meta, body = parse_frontmatter(text)
    if not meta.get("title"):
        raise ValueError("no title in the frontmatter")
    out = [f"# {meta['title']} {{#{slug(page)}}}", ""]
    if meta.get("description"):
        out += [meta["description"], ""]
    lines = body.split("\n")
    exports: dict[str, str] = {}
    stack: list[_Frame] = []
    fence: tuple[str, int] | None = None  # (marker, indent) of the open fence
    i = 0

    def fail(message: str) -> None:
        raise ValueError(f"line {i}: {message}")

    def emit(line: str) -> None:
        if stack and stack[-1].body is not None:
            stack[-1].body.append(line)
        elif line.strip() or out[-1].strip():  # runs of blank lines collapse to one
            out.append(line)

    def label(textline: str) -> None:
        emit("")
        emit(textline)

    def open_tag(name: str, attrs: dict[str, str]) -> None:
        frame = _Frame(name, attrs)
        if name in ADMONITIONS:
            label(f"**{name}**")
        elif name in LABELLED:
            label(f"**{attrs.get('title', '')}**")
        elif name == "Step":
            if not stack or stack[-1].name != "Steps":
                fail("<Step> outside <Steps>")
            stack[-1].count += 1
            label(f"**{stack[-1].count}. {attrs.get('title', '')}**")
        elif name == "Card":
            frame.body = []
        elif name not in WRAPPERS:
            fail(f"unknown component <{name}>")
        stack.append(frame)

    def close_tag(name: str) -> None:
        if not stack or stack[-1].name != name:
            fail(f"</{name}> closes <{stack[-1].name if stack else 'nothing'}>")
        frame = stack.pop()
        if frame.body is not None:
            card = " ".join(t.strip() for t in frame.body if t.strip())
            title, href = frame.attrs.get("title", ""), frame.attrs.get("href")
            head = f"[{title}]({href})" if href else f"**{title}**"
            emit(f"- {head}: {card}" if card else f"- {head}")
        elif name in ADMONITIONS or name in LABELLED or name == "Step":
            emit("")

    def self_closing(name: str, attrs: dict[str, str]) -> None:
        if name in DROPPED:
            return
        if name == "ModelProvider":
            if snippet is None:
                fail("<ModelProvider> needs the provider snippet")
            label("")
            for row in render_provider(attrs.get("show", ""), snippet):
                emit(row)
            emit("")
        elif name == "Prompt":
            if not stack or stack[-1].name != "SetupPrompt":
                fail("<Prompt> outside <SetupPrompt>")
            ref = attrs.get("children", "").strip("{} ")
            if ref not in exports:
                fail(f"<Prompt> names unknown export {ref!r}")
            label(f"**{PROMPT_LABEL}**")
            emit("")
            for row in ["```text", *exports[ref].split("\n"), "```"]:
                emit(row)
        elif name == "VideoCard":
            emit(f"- **{attrs.get('title', '')}**: {attrs.get('subtitle', '')}")
        else:
            fail(f"unknown component <{name} />")

    while i < len(lines):
        line = lines[i].rstrip()
        i += 1
        f = FENCE_RE.match(line)
        if fence is not None:
            marker, indent = fence
            if f and f.group(2)[0] == marker[0] and len(f.group(2)) >= len(marker) and not f.group(3).strip():
                fence = None
                emit(f.group(2))
            else:
                emit(_dedent(line, indent))
            continue
        if f and not (f.group(2)[0] == "`" and "`" in f.group(3)):
            try:
                lang, name = _fence_info(f.group(3).strip())
            except ValueError as e:
                fail(str(e))
            if stack and stack[-1].body is not None:
                fail("code fence inside <Card>")
            if name:
                emit("")
                emit(f"**{name}**")
            fence = (f.group(2), len(f.group(1)))
            emit(f"{f.group(2)}{lang}")
            continue
        stripped = line.strip()
        if not stack and IMPORT_RE.match(stripped):
            continue
        e = EXPORT_RE.match(line)
        if e:
            block = "\n".join(lines[i - 1 :])
            try:
                value, end = parse_js_literal(block, e.end())
            except ValueError as err:
                fail(f"export {e.group(1)}: {err}")
            tail = re.match(r"[ \t]*;?[ \t]*(?:\n|$)", block[end:])
            if not isinstance(value, str) or tail is None:
                fail(f"export {e.group(1)} is not a string constant")
            exports[e.group(1)] = value
            i += block[: end + tail.end()].rstrip("\n").count("\n")
            continue
        pair = INLINE_PAIR_RE.match(line)
        if pair:
            lines[i:i] = [pair.group(4), pair.group(1) + pair.group(5)]
            line = pair.group(1) + pair.group(2)
        if TAG_START_RE.match(line):
            tag = line.strip()
            while (end := _tag_end(tag)) < 0:
                if i >= len(lines):
                    fail(f"unclosed tag {tag[:40]!r}")
                tag += "\n" + lines[i].strip()
                i += 1
            if tag[end + 1 :].strip():
                fail(f"text after a tag: {tag!r}")
            t = TAG_RE.fullmatch(tag[: end + 1])
            if t is None or not ATTRS_RE.fullmatch(t.group(3)):
                fail(f"unparsed tag {tag!r}")
            closing, name, raw, selfclose = t.groups()
            attrs = {a.group(1): a.group(2) if a.group(2) is not None else (a.group(3) or "")
                     for a in ATTR_RE.finditer(raw)}
            if closing:
                close_tag(name)
            elif selfclose:
                self_closing(name, attrs)
            elif name in DROPPED:
                fail(f"<{name}> must be self-closing")
            else:
                open_tag(name, attrs)
            continue
        h = HEADING_RE.match(line)
        if h:
            level, title = len(h.group(1)), h.group(2)
            if level == 1:
                fail("H1 in the page body")
            if level <= SECTION_MAX_LEVEL:
                anchor = slug(title)
                if not anchor:
                    fail(f"heading without slug: {line!r}")
                emit(f"{h.group(1)} {title} {{#{anchor}}}")
                continue
        if MARKUP_RE.search(INLINE_CODE_RE.sub("", line)):
            fail(f"unhandled markup: {line!r}")
        emit(line)

    if fence is not None:
        raise ValueError("unclosed code fence")
    if stack:
        raise ValueError(f"unclosed <{stack[-1].name}>")
    return "\n".join(out).rstrip("\n") + "\n"
```

Notes for the implementer:
- `fail` raises; the type checker does not know that, so after `fail(...)` inside `try/except` no value is used.
  If ruff/pyright complains about possibly unbound names, annotate `fail` with `-> NoReturn` (`from typing import
  NoReturn`).
- `emit` collapses runs of blank lines (labels add one before themselves), so the output has single blank lines;
  `clean_markdown` collapses again, which is harmless.
- The closing-fence branch emits the marker at column 0; opening fences too, so `clean_markdown`'s fence detection
  (at most 3 spaces) always sees them.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_mdx.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/mdx.py tests/test_mdx.py
git commit -m "feat(corpus): MDX-Seiten der e2e-Doku verlustarm in Markdown umwandeln"
```

---

### Task 4: Ingest, preprocessing, catalogue area and link

**Files:**
- Modify: `src/ingest.py`, `src/preprocess.py`, `src/catalogue.py:102-104`, `src/catalogue_store.py:31,297`
- Test: `tests/test_ingest.py` (rewrite), `tests/test_preprocess.py` (rewrite), `tests/test_clean_markdown.py`
  (rewrite: generic rules only), `tests/test_catalogue.py:29-38`, `tests/conftest.py` (`build_corpus` adds `area`),
  `tests/test_chunking_records.py:122` (raw fixture), any other fixture that builds documents for `Corpus.area`

**Interfaces:**
- Consumes: `nav_areas`, `parse_frontmatter`, `parse_provider_snippet`, `to_markdown` (Tasks 1–3); config keys
  (Task 1).
- Produces: `ingest(snapshot_dir, out_file, suffix, nav_file, areas) -> int`; documents with `area`;
  `preprocess(doc_file, sections_file, manifest_file, snippet_file) -> tuple[int, int]`;
  `clean_markdown(text) -> CleanResult` (anchored Markdown, unchanged contract); `Corpus.area(section) -> str`
  (document's `area`).

- [ ] **Step 1: Write the failing ingest tests** (`tests/test_ingest.py`, full rewrite)

```python
import json

import pytest

import tokens
from ingest import ingest

NAV = {
    "navigation": {
        "tabs": [
            {"tab": "Docs", "groups": [{"group": "Start", "pages": ["index", "ci/a"]}]},
            {"tab": "Examples", "pages": ["examples"]},
        ]
    }
}
PAGES = {
    "index.mdx": "---\ntitle: Introduction\ndescription: Hi.\n---\n\nText.\n",
    "ci/a.mdx": '﻿---\ntitle: "GitHub Actions"\n---\n\nRun it.\n',
    "examples.mdx": "---\ntitle: Example projects\n---\n",
}


def make_snapshot(root, pages=PAGES, nav=NAV):
    for rel, text in pages.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (root / "docs.json").write_text(json.dumps(nav), encoding="utf-8")


def run(snap, out, areas=("Start", "Examples")):
    return ingest(snap, out, ".mdx", "docs.json", areas)


def test_ingest_assigns_ids_by_path_with_title_and_area(tmp_path):
    make_snapshot(tmp_path / "snap")
    out = tmp_path / "processed" / "documents.jsonl"
    assert run(tmp_path / "snap", out) == 3

    docs = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [(d["doc_id"], d["path"], d["title"], d["area"]) for d in docs] == [
        ("D001", "ci/a.mdx", "GitHub Actions", "Start"),
        ("D002", "examples.mdx", "Example projects", "Examples"),
        ("D003", "index.mdx", "Introduction", "Start"),
    ]
    assert list(docs[0]) == ["doc_id", "path", "title", "area", "text", "tokens"]
    assert docs[0]["text"].startswith("---\n")  # raw text, BOM removed
    assert docs[0]["tokens"] == tokens.count(docs[0]["text"])


def test_ingest_without_snapshot_points_to_snapshot_script(tmp_path):
    with pytest.raises(FileNotFoundError, match="run src/snapshot.py"):
        run(tmp_path / "empty", tmp_path / "documents.jsonl")


def test_ingest_rejects_areas_that_differ_from_the_config(tmp_path):
    make_snapshot(tmp_path / "snap")
    with pytest.raises(ValueError, match="CORPUS_AREAS"):
        run(tmp_path / "snap", tmp_path / "d.jsonl", areas=("Start",))


def test_ingest_rejects_a_page_outside_the_navigation(tmp_path):
    make_snapshot(tmp_path / "snap", {**PAGES, "draft.mdx": "---\ntitle: D\n---\n"})
    with pytest.raises(ValueError, match="draft.mdx: not in the navigation"):
        run(tmp_path / "snap", tmp_path / "d.jsonl")


def test_ingest_rejects_a_navigation_page_without_file(tmp_path):
    pages = {k: v for k, v in PAGES.items() if k != "examples.mdx"}
    make_snapshot(tmp_path / "snap", pages)
    with pytest.raises(ValueError, match="examples"):
        run(tmp_path / "snap", tmp_path / "d.jsonl")


def test_ingest_requires_a_title(tmp_path):
    make_snapshot(tmp_path / "snap", {**PAGES, "index.mdx": "---\ndescription: x\n---\n"})
    with pytest.raises(ValueError, match="index.mdx: no title"):
        run(tmp_path / "snap", tmp_path / "d.jsonl")
```

- [ ] **Step 2: Write the failing preprocess and clean_markdown tests**

`tests/test_preprocess.py` (full rewrite):

```python
import csv
import json

import pytest

import tokens
from preprocess import clean_markdown, preprocess, section_spans
from test_mdx import SNIPPET

RAW_A = (
    "---\ntitle: A Page\ndescription: About A.\n---\n\n"
    "import { X } from './snippets/x.jsx';\n\n## Part\n\n<Note>\nText.\n</Note>\n"
)
RAW_B = "---\ntitle: Intro\n---\n\nHello.\n"


def write_docs(path, docs):
    path.write_text("".join(json.dumps(d) + "\n" for d in docs), encoding="utf-8")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def doc(doc_id, path, title, area, text):
    return {"doc_id": doc_id, "path": path, "title": title, "area": area, "text": text, "tokens": 0}


@pytest.fixture
def files(tmp_path):
    docs = tmp_path / "documents.jsonl"
    write_docs(
        docs,
        [
            doc("D001", "features/a.mdx", "A Page", "Features", RAW_A),
            doc("D002", "index.mdx", "Intro", "Get started", RAW_B),
        ],
    )
    snippet = tmp_path / "model-provider.jsx"
    snippet.write_text(SNIPPET, encoding="utf-8")
    return docs, tmp_path / "sections.jsonl", tmp_path / "corpus_manifest.csv", snippet


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
    assert by_id["D007#c"]["end_token"] == n
    assert list(spans[0]) == [
        "section_id", "doc_id", "anchor", "title", "level", "start_token", "end_token",
    ]  # fmt: skip


def test_preprocess_writes_documents_sections_and_manifest(files):
    assert preprocess(*files) == (2, 3)
    docs, sections, manifest, _ = files

    out = read_jsonl(docs)
    assert [list(d) for d in out] == [["doc_id", "path", "title", "area", "text", "tokens"]] * 2
    assert out[0]["text"] == "# A Page\n\nAbout A.\n\n## Part\n\n**Note**\nText.\n"
    assert out[0]["tokens"] == tokens.count(out[0]["text"])
    assert [s["section_id"] for s in read_jsonl(sections)] == [
        "D001#features-a",
        "D001#part",
        "D002#index",
    ]
    with manifest.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["file_id", "path", "title", "section", "tokens", "included"]
    assert rows[1] == ["D001", "features/a.mdx", "A Page", "Features", str(out[0]["tokens"]), "yes"]
    assert rows[2][3] == "Get started"


def test_rerun_on_cleaned_documents_asks_for_ingest(files):
    preprocess(*files)
    with pytest.raises(RuntimeError, match="run src/ingest.py"):
        preprocess(*files)


def test_anomaly_reports_document_path(files):
    docs = files[0]
    write_docs(docs, [doc("D001", "x.mdx", "X", "Features", "---\ntitle: X\n---\n\n<Frame>\n")])
    with pytest.raises(ValueError, match="x.mdx: line 2: unknown component <Frame>"):
        preprocess(*files)


def test_missing_documents_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="run src/ingest.py"):
        preprocess(tmp_path / "m.jsonl", tmp_path / "s.jsonl", tmp_path / "m.csv", tmp_path / "p.jsx")


def test_missing_snippet_points_to_snapshot(files, tmp_path):
    docs, sections, manifest, _ = files
    with pytest.raises(FileNotFoundError, match="run src/snapshot.py"):
        preprocess(docs, sections, manifest, tmp_path / "missing.jsx")
```

`tests/test_clean_markdown.py` (full rewrite, generic rules):

```python
import pytest

from preprocess import clean_markdown, fence_marker


def test_bom_crlf_and_blank_runs_normalised():
    result = clean_markdown("﻿# T {#t}\r\n\r\n\r\n\r\nText.\r\n")
    assert result.text == "# T\n\nText.\n"


def test_headings_recorded_with_offsets_and_anchors_removed():
    text = "# Page {#page}\n\nIntro.\n\n## Part `a` {#part-a}\n\n#### Deep\n\nx\n"
    result = clean_markdown(text)
    assert result.text == "# Page\n\nIntro.\n\n## Part `a`\n\n#### Deep\n\nx\n"
    assert [(h.level, h.title, h.anchor) for h in result.headings] == [
        (1, "Page", "page"),
        (2, "Part `a`", "part-a"),
    ]
    assert result.text[result.headings[1].offset :].startswith("## Part")


def test_fence_info_strings_reduced_and_code_untouched():
    text = "# T {#t}\n\n```ts {1}\n## not a heading <div>\n```\n\n~~~bash\n# comment\n~~~\n"
    result = clean_markdown(text)
    assert "```ts\n## not a heading <div>\n```" in result.text
    assert "~~~bash\n# comment\n~~~" in result.text
    assert len(result.headings) == 1


def test_fence_closes_only_with_same_marker():
    assert fence_marker("```ts") == "```"
    assert fence_marker("``` a`b") is None
    result = clean_markdown("# T {#t}\n\n~~~\n```\n## x {#x}\n~~~\n")
    assert len(result.headings) == 1


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("# T {#t}\n\n## Y\n", "heading without anchor"),
        ("# T {#t}\n\n## A {#a}\n\n## B {#a}\n", "duplicate anchor"),
        ("## Only {#o}\n", "exactly one H1"),
        ("# A {#a}\n\n# B {#b}\n", "exactly one H1"),
        ("# T {#t}\n\n```ts\nopen\n", "unclosed code fence"),
        ("# T {#t}\n\n<div>\n", "unhandled HTML"),
        ("# T {#t}\n\nSee <b>this</b>.\n", "unhandled inline HTML"),
    ],
)
def test_anomalies_raise(body, message):
    with pytest.raises(ValueError, match=message):
        clean_markdown(body)


def test_escaped_lt_and_inline_code_are_not_html():
    result = clean_markdown("# T {#t}\n\nUse `<div>` and \\<b> literally.\n")
    assert "Use `<div>` and \\<b> literally." in result.text
```

- [ ] **Step 3: Adjust the other fixtures**

- `tests/conftest.py` `build_corpus`: add `"area": path.split("/")[0],` after `"title"` (keeps the catalogue tests'
  Vue-like areas; the fixtures are independent of the real corpus).
- `tests/test_catalogue.py`: import `CATALOGUE_AREA_SLOTS` instead of `VUE_DOCS_AREAS`; the assertion becomes
  `assert set(AREA_MIN_QUESTIONS) <= set(CATALOGUE_AREA_SLOTS)`.
- `tests/test_chunking_records.py:122`: `raw = "---\ntitle: Intro\n---\n\nShort page.\n"` (a raw MDX page, not
  cleaned; the test still expects the sections mismatch).
- Run `grep -rn '"title":' tests/ | grep -v conftest` and add `"area"` wherever a test builds documents that reach
  `Corpus.area` (found by the failing run in Step 4).

- [ ] **Step 4: Run them to verify they fail**

Run: `uv run pytest tests/test_ingest.py tests/test_preprocess.py tests/test_clean_markdown.py -q`
Expected: FAIL (`ingest()` keywords, `preprocess()` takes 3 arguments, Vue rules still active).

- [ ] **Step 5: Rewrite `src/ingest.py`**

```python
"""Ingest the e2e snapshot (ADR 0038).

Reads every page (*.mdx) of data/raw/e2e_docs_snapshot/ sorted by path, assigns D001, D002, ... in
that order and writes data/processed/documents.jsonl with the raw text. The title comes from the
frontmatter, the area from the navigation (config.CORPUS_NAV_FILE), whose groups must equal
config.CORPUS_AREAS and whose pages must equal the snapshot's pages.

Output schema: {"doc_id", "path", "title", "area", "text", "tokens"}
"""

import json
from pathlib import Path

import tokens
from config import CORPUS_AREAS, CORPUS_NAV_FILE, CORPUS_PAGE_SUFFIX, DATA_RAW, DOCUMENTS_FILE
from mdx import nav_areas, parse_frontmatter


def ingest(
    snapshot_dir: Path = DATA_RAW,
    out_file: Path = DOCUMENTS_FILE,
    suffix: str = CORPUS_PAGE_SUFFIX,
    nav_file: str = CORPUS_NAV_FILE,
    areas: tuple[str, ...] = CORPUS_AREAS,
) -> int:
    """Load the pages, take title and area, count tokens, write documents.jsonl; return count."""
    nav_path = snapshot_dir / nav_file
    if not nav_path.is_file():
        raise FileNotFoundError(f"{nav_path} not found; run src/snapshot.py first")
    page_areas = nav_areas(json.loads(nav_path.read_text(encoding="utf-8")))
    found_areas = tuple(dict.fromkeys(page_areas.values()))
    if found_areas != tuple(areas):
        raise ValueError(f"navigation areas {list(found_areas)} differ from config.CORPUS_AREAS")
    files = sorted(snapshot_dir.rglob(f"*{suffix}"), key=lambda p: p.relative_to(snapshot_dir).as_posix())
    pages = {p.relative_to(snapshot_dir).as_posix().removesuffix(suffix) for p in files}
    for page in pages:
        if page not in page_areas:
            raise ValueError(f"{page}{suffix}: not in the navigation")
    missing = sorted(set(page_areas) - pages)
    if missing:
        raise ValueError(f"navigation pages without a file: {missing}")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        for i, path in enumerate(files, start=1):
            rel = path.relative_to(snapshot_dir).as_posix()
            text = path.read_text(encoding="utf-8-sig")
            try:
                meta, _ = parse_frontmatter(text)
            except ValueError as e:
                raise ValueError(f"{rel}: {e}") from e
            if not meta.get("title"):
                raise ValueError(f"{rel}: no title in the frontmatter")
            record = {
                "doc_id": f"D{i:03d}",
                "path": rel,
                "title": meta["title"],
                "area": page_areas[rel.removesuffix(suffix)],
                "text": text,
                "tokens": tokens.count(text),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return len(files)


if __name__ == "__main__":
    print(f"{ingest()} documents -> {DOCUMENTS_FILE}")
```

Empty snapshot directory: `nav_path` is missing, so the first check fires (test expects "run src/snapshot.py").

- [ ] **Step 6: Rewrite `src/preprocess.py`**

Keep `FENCE_RE`, `FENCE_LANG_RE`, `HEADING_RE`, `ANCHOR_RE`, `INLINE_CODE_RE`, `ESCAPED_LT_RE`, `INLINE_TAG_RE`,
`HTML_LINE_RE`, `MANIFEST_HEADER`, `Heading`, `CleanResult`, `fence_marker`, `closes_fence`, `section_spans`,
`_write_jsonl`. Delete every Vue rule and helper (`UNWRAP_CLASS`, `DROP_*`, `API_MARKER_RE`, block/line/span/badge/
listing/tool-URL patterns, `_tag_balance`, `_code_spans`, `_sub_outside_code`, `_find_outside_code`,
`has_anchored_heading`, `heading_title`, `_strip_frontmatter`, `AREA_SECTIONS`, `SECTION_NAMES`,
`manifest_section`). New docstring and functions:

```python
"""Preprocess the e2e pages (ADR 0019, ADR 0038).

Reads documents.jsonl (raw MDX from ingest.py), converts every page with mdx.to_markdown (content-
preserving; anchors = the site's slugs) and records the anchored H1-H3 sections with clean_markdown.
Rewrites documents.jsonl in place, writes sections.jsonl and the corpus manifest (section = area).
"""

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

import tokens
from config import (
    CORPUS_MANIFEST_FILE,
    CORPUS_PAGE_SUFFIX,
    CORPUS_PROVIDER_SNIPPET,
    DATA_RAW,
    DOCUMENTS_FILE,
    SECTION_MAX_LEVEL,
    SECTIONS_FILE,
)
from mdx import parse_provider_snippet, to_markdown


def clean_markdown(text: str) -> CleanResult:
    """Anchored Markdown (from mdx.to_markdown) -> text without anchors and its H1-H3 headings.

    Fences are tracked and their info string reduced to the language; runs of blank lines collapse;
    every H1-H3 needs an anchor, anchors are unique, exactly one H1; HTML outside code raises.
    """
    text = text.lstrip("﻿").replace("\r\n", "\n")
    out: list[str] = []
    pending: list[tuple[int, int, str, str]] = []  # (out line index, level, title, anchor)
    fence: str | None = None

    def emit(line: str) -> None:
        line = line.rstrip()
        if not line and (not out or not out[-1]):
            return
        out.append(line)

    for line in text.split("\n"):
        if fence is not None:
            if closes_fence(line, fence):
                fence = None
            emit(line)
            continue
        marker = fence_marker(line)
        if marker is not None:
            fence = marker
            m = FENCE_RE.match(line)
            assert m is not None
            lang = FENCE_LANG_RE.match(m.group(3))
            emit(f"{m.group(1)}{marker}{lang.group(1) if lang else ''}")
            continue
        prose = ESCAPED_LT_RE.sub(r"\1", INLINE_CODE_RE.sub("", line))
        if HTML_LINE_RE.match(line):
            raise ValueError(f"unhandled HTML outside code fences: {line!r}")
        if INLINE_TAG_RE.search(prose):
            raise ValueError(f"unhandled inline HTML outside code: {line!r}")
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
                pending.append((len(out), level, ESCAPED_LT_RE.sub(r"\1<", title).strip(), a.group(1)))
            line = f"{h.group(1)} {title}"
        emit(line)

    if fence:
        raise ValueError("unclosed code fence")
    while out and not out[-1]:
        out.pop()
    starts, pos = [], 0
    for line in out:
        starts.append(pos)
        pos += len(line) + 1
    headings = [Heading(lv, t, a, starts[i]) for i, lv, t, a in pending]
    anchors = [h.anchor for h in headings]
    if len(set(anchors)) != len(anchors):
        raise ValueError(f"duplicate anchor: {sorted({a for a in anchors if anchors.count(a) > 1})}")
    if sum(h.level == 1 for h in headings) != 1:
        raise ValueError("document needs exactly one H1")
    return CleanResult("\n".join(out) + "\n", headings)


def preprocess(
    doc_file: Path = DOCUMENTS_FILE,
    sections_file: Path = SECTIONS_FILE,
    manifest_file: Path = CORPUS_MANIFEST_FILE,
    snippet_file: Path = DATA_RAW / CORPUS_PROVIDER_SNIPPET,
) -> tuple[int, int]:
    """Convert and clean documents.jsonl in place; write sections.jsonl and the corpus manifest."""
    if not doc_file.exists():
        raise FileNotFoundError(f"{doc_file} not found; run src/ingest.py first")
    if not snippet_file.is_file():
        raise FileNotFoundError(f"{snippet_file} not found; run src/snapshot.py first")
    docs = [json.loads(line) for line in doc_file.read_text(encoding="utf-8").splitlines() if line]
    if docs and not any(d["text"].startswith("---\n") for d in docs):
        raise RuntimeError(f"{doc_file} is already preprocessed; run src/ingest.py first")
    snippet = parse_provider_snippet(snippet_file.read_text(encoding="utf-8"))

    sections: list[dict] = []
    for doc in docs:
        try:
            result = clean_markdown(
                to_markdown(doc["text"], doc["path"].removesuffix(CORPUS_PAGE_SUFFIX), snippet)
            )
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
            writer.writerow([d["doc_id"], d["path"], d["title"], d["area"], d["tokens"], "yes"])
    return len(docs), len(sections)
```

`CleanResult` and `Heading` must be defined above `clean_markdown` (they are). Keep `__main__`. Remove `import
html` (unused now); keep `re` (patterns).

- [ ] **Step 7: Catalogue area and site link**

`src/catalogue.py` `Corpus.area`:

```python
    def area(self, section: dict) -> str:
        """Area of the section's document (documents.jsonl `area`: its navigation group, D38)."""
        return self.docs[section["doc_id"]]["area"]
```

`src/catalogue_store.py`: import `CORPUS_SITE_URL` instead of `VUE_DOCS_SITE_URL` and use it on line 297.

- [ ] **Step 8: Run the whole suite**

Run: `uv run pytest -q 2>&1 | tail -20`
Expected: PASS, except the real-corpus tests in `tests/test_corpus_integration.py` (Task 5 rewrites them); they skip
or fail only on Vue constants. Fix every other failure (missing `"area"` in a fixture, a removed import).

- [ ] **Step 9: Commit**

```bash
git add src/ingest.py src/preprocess.py src/catalogue.py src/catalogue_store.py tests/
git commit -m "feat(corpus): Ingest und Aufbereitung der e2e-Seiten mit Bereich je Seite"
```

---

### Task 5: Real run, integration tests and K1 size

**Files:**
- Modify: `tests/test_corpus_integration.py`, `.gitignore`, `src/config.py` (`K1_CHUNK_SIZE` and its comment),
  `docs/corpus_snapshot.txt` (new record), `docs/corpus_manifest.csv` (regenerated), `data/raw/e2e_docs_snapshot/.gitkeep`

**Interfaces:**
- Consumes: everything above.
- Produces: the real `documents.jsonl`, `sections.jsonl`, `section_index.md`, the versioned record and manifest; the
  measured counts for Task 6.

- [ ] **Step 1: Point `.gitignore` at the new raw directory**

Replace the three `vue_docs_snapshot` lines by `!data/raw/e2e_docs_snapshot/`, `data/raw/e2e_docs_snapshot/*`,
`!data/raw/e2e_docs_snapshot/.gitkeep`; create `data/raw/e2e_docs_snapshot/.gitkeep`; `git rm --cached
data/raw/vue_docs_snapshot/.gitkeep` (the local Vue snapshot stays on disk, ignored).

- [ ] **Step 2: Create the snapshot** (network: GitHub)

```bash
git rm -q docs/corpus_snapshot.txt   # the Vue record stays in the history
uv run python src/snapshot.py
```

Expected: `62 files -> …/data/raw/e2e_docs_snapshot` (60 pages + 2 support files).

- [ ] **Step 3: Ingest, preprocess, section index**

```bash
uv run python src/ingest.py && uv run python src/preprocess.py && uv run python src/catalogue.py index
```

Expected: `60 documents`, then `60 documents, N sections`. If a page fails, the message names page and line: extend
the rule in `src/mdx.py` test-first (Task 3 style), never special-case the page. Record each such extension as a
ruling. Check for leftover escapes once: `grep -c '\\\\[<{]' data/processed/documents.jsonl` (an MDX escape
`\<`/`\{` in prose would stay as text; if any appear, add an unescape rule test-first). (`catalogue.py index`: use
the subcommand that writes `section_index.md`; check `uv run python src/catalogue.py --help`.)

- [ ] **Step 4: Rewrite the real-corpus tests** (`tests/test_corpus_integration.py`)

Change the top:

```python
from config import (
    C3_MAX_TOKENS,
    C3_MIN_TOKENS,
    CHUNK_FILES,
    CONTROL_STRATEGIES,
    CORPUS_AREAS,
    CORPUS_NAV_FILE,
    CORPUS_PAGE_SUFFIX,
    CORPUS_PROVIDER_SNIPPET,
    CORPUS_SUPPORT_FILES,
    DATA_RAW,
    DOCUMENTS_FILE,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_FILES,
    SECTIONS_FILE,
    SNAPSHOT_INFO_FILE,
    STRATEGY_IDS,
)
from mdx import parse_provider_snippet, to_markdown
from preprocess import ESCAPED_LT_RE, clean_markdown

HAS_SNAPSHOT = (DATA_RAW / CORPUS_NAV_FILE).is_file()
EXPECTED_FILES = 60  # ADR 0038: every page of the navigation at ef977f4
AREA_PAGES = {
    "Get started": 5, "Platforms": 3, "Features": 6, "Models and agents": 3, "Run in CI": 6,
    "Hosted browsers and devices": 7, "Extend": 3, "Deep dive": 5, "Migrate": 5, "Test API": 5,
    "Project": 8, "Web": 1, "Mobile": 1, "Engine contract": 1, "Examples": 1,
}  # fmt: skip


def snapshot_files():
    return sorted(DATA_RAW.rglob(f"*{CORPUS_PAGE_SUFFIX}"))
```

- `test_every_snapshot_file_cleans`: parse the snippet once
  (`parse_provider_snippet((DATA_RAW / CORPUS_PROVIDER_SNIPPET).read_text(encoding="utf-8"))`), then for every page
  `clean_markdown(to_markdown(text, rel.removesuffix(CORPUS_PAGE_SUFFIX), snippet))` and assert the first heading is
  level 1.
- `test_processed_artifacts_are_consistent`: leftover pattern becomes
  `r"</?[A-Za-z][\w-]*(?:\s[^>]*)?/?>|\{#|^\s*(?:import|export) "` with `re.M`; everything else unchanged.
- `test_snapshot_matches_the_versioned_checksums`: `files` = pages plus `CORPUS_SUPPORT_FILES`.
- `test_corpus_areas_and_exclusions` → `test_corpus_areas`: `Counter(d["area"] for d in docs) == AREA_PAGES` and
  `list(AREA_PAGES) == list(CORPUS_AREAS)`.
- `test_section_index_covers_the_real_corpus`: section count = the measured `N` from Step 3; areas
  `== set(CORPUS_AREAS)`; `find(corpus, "toHaveScreenshot")` finds a section.

- [ ] **Step 5: Measure K1 and set it**

Run: `uv run python -c "import sys; sys.path.insert(0, 'src'); from chunking import chunk; chunk('K1', out_file=__import__('pathlib').Path('/tmp/k1.jsonl'))"`
Expected: `ValueError: K1_CHUNK_SIZE is 231, the C3 chunks have a rounded mean of M tokens; set config.K1_CHUNK_SIZE = M`.
Set `K1_CHUNK_SIZE = M` with the comment `# tokens; rounded mean of the C3 chunks at ef977f4, measured 18.10.2026`.
(Use the scratchpad instead of `/tmp` for the output file.)

- [ ] **Step 6: Run the whole suite and the linters**

Run: `uv run pytest -q 2>&1 | tail -5 && uvx pre-commit run --all-files`
Expected: all pass. `test_reference_vectors_match_their_chunks` still compares the old (Vue) chunk files with their
vectors and passes; step 3 rebuilds both.

- [ ] **Step 7: Commit**

```bash
git add .gitignore data/raw/e2e_docs_snapshot/.gitkeep docs/corpus_snapshot.txt docs/corpus_manifest.csv src/config.py tests/test_corpus_integration.py
git commit -m "feat(corpus): e2e-Snapshot erstellt, Integrationstests und K1-Fenster neu"
```

---

### Task 6: Documentation

**Files:** `docs/reference/corpus.md`, `docs/how-to/create-corpus-snapshot.md`, `docs/reference/data-formats.md`,
`docs/reference/configuration.md`, `docs/reference/tooling.md`, `docs/reference/experiment-record.md`,
`docs/plan.md`, `README.md`, `AGENTS.md`, `.serena/memories/core.md`, `docs/explanation/research-design.md` (corpus
sentences only)

- [ ] **Step 1: Update each file** (German, existing style)

- `corpus.md`: source (repo, commit ef977f4, 17.10.2026, Apache-2.0), scope (60 pages = navigation, 15 areas with
  page counts), measured documents/tokens/sections from Task 5, the conversion rules (table from the spec, with the
  slug rule and its live check), what is dropped and why; Vue description moves to a short "bis 18.10.2026" note
  linking ADR 0025/0038.
- `create-corpus-snapshot.md`: commands, expected outputs (62 files, 60 documents), what to do on a navigation
  mismatch or an unknown component.
- `data-formats.md`: `documents.jsonl` gains `area` (navigation group); example lines with e2e values; manifest
  `section` = area.
- `configuration.md`: the new `CORPUS_*` keys replace `VUE_DOCS_*`; `DATA_RAW`; `CORPUS_SITE_URL`; `K1_CHUNK_SIZE`
  new value; quota keys marked "Vue-Bereiche bis Schritt 4".
- `tooling.md`: snapshot/ingest/preprocess descriptions.
- `experiment-record.md`: new "Snapshot (e2e)" table (repo, commit, dates, files, documents, tokens, sections) and
  the K1 measurement; the Vue rows stay as history under a heading "bis 18.10.2026 (Vue.js)".
- `plan.md` `#stand`: step 2 done (date), step 3 next.
- `README.md`: corpus line → e2e; license section: e2e docs © TesterArmy, Inc., Apache License 2.0
  ([copy](LICENSES/Apache-2.0.txt)), NOTICE text quoted, downloaded at run time; excerpts in `data/corpus_probe/`
  under the same terms.
- `AGENTS.md` purpose: drop "(the switch from Vue.js is in progress)" only if steps 3–5 are noted in plan.md; else
  change it to "(corpus switched; rebuild in progress)".
- `.serena/memories/core.md`: one line on `src/mdx.py` and where the rules are documented.
- `research-design.md`: corpus sentences → e2e with link to ADR 0038.

- [ ] **Step 2: Check links and lint**

Run: `uvx pre-commit run --all-files && grep -rn "VUE_DOCS\|vue_docs_snapshot" src tests docs/reference docs/how-to README.md AGENTS.md`
Expected: lint passes; grep finds nothing outside history notes.

- [ ] **Step 3: Commit**

```bash
git add docs README.md AGENTS.md .serena/memories/core.md
git commit -m "docs(corpus): e2e-Korpus, Aufbereitungsregeln und Messwerte dokumentiert"
```

After Task 6: final whole-branch review (Codex review on the PR, or the `codex-reviewer` agent), then PR, Jonas checks
`data/processed/section_index.md`, merge after approval, bump the PaperLab pointer.
