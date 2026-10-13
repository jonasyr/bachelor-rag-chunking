# Corpus snapshot, ingest and preprocessing: design

Date: 13.10.2026. Status: approved in chat. Decision basis: [ADR 0019](../../adr/0019-korpus-ausschnitt.md),
formats: [data formats](../../reference/data-formats.md), corpus facts: [corpus](../../reference/corpus.md).

## Goal

Turn `vuejs/docs` `src/guide/` at commit `b75d188ab16bf83bd1f364a77dfd2315be8f3fa4` into a cleaned,
Composition-API-only `documents.jsonl`, a `sections.jsonl` with token spans per anchored section, and
`docs/corpus_manifest.csv`. Reproducible, test-first, no OpenAI calls.

Success criteria:

- `snapshot.py`, `ingest.py`, `preprocess.py` run in that order from the repo root without options.
- 52 documents `D001`–`D052`; `documents.jsonl` keys exactly `doc_id, path, title, text, tokens`.
- No `options-api` markup remains; code inside fences is unchanged apart from the info string.
- Every H1–H3 heading yields one `section_id = {doc_id}#{anchor}`, unique across the corpus.
- `uv run pytest` and `uvx pre-commit run --all-files` pass.

## Units

| Unit | Responsibility | Depends on |
|---|---|---|
| `src/tokens.py` (new) | `encode`, `decode`, `count`, `token_starts(text)` (character offset of each token) and `char_to_token(starts, offset)` with `config.TOKEN_ENCODING`. Shared with the later chunking step so `start_token`/`end_token` and section spans use one index space. | tiktoken |
| `src/snapshot.py` (new, no CLI options) | Shallow `git fetch` of `config.VUE_DOCS_COMMIT` from `config.VUE_DOCS_REPO_URL` into a temporary directory, verify `HEAD` equals the pinned hash, replace the contents of `DATA_RAW` (keeping `.gitkeep`) with `{VUE_DOCS_SUBDIR}/**/*.md` stored as `guide/…`, write `DATA_RAW/SNAPSHOT.txt` (repo, commit, commit date, snapshot date, file count, sha256 per file). | git, config |
| `src/ingest.py` | Read `DATA_RAW/guide/**/*.md` sorted by POSIX path, assign `D001…` in that order, `title` = H1 text without anchor, raw `text`, `tokens` = token count; write `documents.jsonl`. | tokens, config |
| `src/preprocess.py` | Pure `clean_markdown(text) -> CleanResult(text, headings)`; `section_spans(...)`; `preprocess()` rewrites `documents.jsonl` in place (`text`, `tokens`), writes `sections.jsonl` and `docs/corpus_manifest.csv`. | tokens, config |

## Cleaning rules

Input is decoded as UTF-8 with a leading BOM removed (`plugins.md` has one). A line-based state machine tracks fenced
code blocks (```` ``` ```` / `~~~`, also indented inside lists) and `<div>` depth. Rules apply only
outside fences; fence content stays verbatim, the opening info string is reduced to the language
(```` ```js{2-6} ```` → ```` ```js ````, ```` ```sh [npm] ```` → ```` ```sh ````).

| Element | Treatment |
|---|---|
| YAML frontmatter at file start | dropped |
| `<div class="composition-api">`, `<p class="composition-api">` | wrapper lines removed, content kept |
| any other HTML block starting a line with `<div`, `<p`, `<ScrimbaLink`, `<VueSchoolLink` (Options API variants, demos, sponsor boxes, navigation tiles, promo links) | dropped with content up to the matching close tag (nesting counted, inline code ignored) |
| `<span class="options-api">…</span>` / `<span class="composition-api">…</span>` | dropped / unwrapped |
| page-level `<script …>…</script>`, `<style …>…</style>` | dropped |
| `<img>`, `<details>`, `</details>`, `<br>` lines; self-closing components (`<VueSchoolLink … />`); inline `<sup class="vt-badge ts" />`; empty `<span id="…"></span>` | dropped |
| version badge `<sup class="vt-badge" data-text="3.5+" />` | becomes `(3.5+)` (factual content) |
| trailing `\*` / `\*\*` API-style markers on headings | removed |
| `<summary>Text</summary>` | becomes `Text` |
| HTML comments `<!-- … -->` (also multi-line) | dropped |
| containers `:::tip`, `::: tip`, `:::warning`, `:::danger`, `:::info`, `:::details`, `::: code-group` (optional space, optional title) | opening line becomes the title text (or nothing), body kept, closing `:::` dropped |
| `{#anchor}` at end of a heading | recorded, then removed from the heading |
| blank-line runs | collapsed to one blank line; trailing whitespace stripped |
| any other HTML line outside fences | error (no silent leftovers) |

## Sections

- H1, H2 and H3 are sections; H4+ belong to their parent.
- A section spans from its heading line to the start of the next heading of the same or higher level (an H2 includes
  its H3s; the H1 spans the whole document).
- Spans are `[start_token, end_token)` positions in the token sequence of the cleaned `text`.
- New artifact `data/processed/sections.jsonl` (documented in `docs/reference/data-formats.md`):
  `{"section_id":"D001#ref-vs-reactive","doc_id":"D001","anchor":"ref-vs-reactive","title":"…","level":2,"start_token":812,"end_token":1240}`

## Manifest

`docs/corpus_manifest.csv` with the existing header `file_id,path,title,section,tokens,included`; `section` comes
from an explicit map of the folders below `guide/` (`best-practices` → `Best Practices`, `typescript` → `TypeScript`,
…; an unknown folder is an error), top-level pages get `Guide`; `tokens` after preprocessing; `included` = `yes` for all rows.

## Configuration (`src/config.py`)

`VUE_DOCS_REPO_URL`, `VUE_DOCS_COMMIT`, `VUE_DOCS_SUBDIR = "src/guide"`, `TOKEN_ENCODING = "cl100k_base"`,
`SECTIONS_FILE`, `CORPUS_MANIFEST_FILE`, `SNAPSHOT_INFO_FILE`, `RELEVANCE_MIN_OVERLAP = 1`,
`SENSITIVITY_MIN_OVERLAP = 100` (the last two are used by the retrieval evaluation later; values from ADR 0019).

Dependencies: pin `tiktoken==0.13.0` (ADR 0019); add `pytest` to the dev group.

## Error handling

Fail loudly with a clear message (exception, non-zero exit) on: commit mismatch, missing `git`, unbalanced `<div>` or
unclosed fence/comment, H1–H3 without anchor, duplicate anchor in a document, missing or multiple H1, leftover
`options-api` after cleaning, `documents.jsonl` missing when `preprocess.py` runs. Silent data damage is worse than a
crash for a thesis corpus.

## Tests (`tests/`, written first)

- `test_tokens.py`: `char_to_token` is monotonic and consistent with `encode`.
- `test_preprocess.py`: fixtures for nested options div, options div inside a code fence (must survive),
  inline spans, composition unwrap, frontmatter, page script, demo div, comments, containers, info strings, anchor
  removal, every error case; span nesting (H2 contains H3, H1 = whole doc); `sections.jsonl` and manifest exact keys/header.
- `test_ingest.py`: ID order by path, title extraction, exact JSONL keys, on a temporary snapshot directory.
- `test_snapshot.py`: copy/verify logic against a local temporary git repository (no network).
- `test_corpus_integration.py`: on the real snapshot, skipped when absent: 52 documents, unique `section_id`s,
  no `options-api` in any `text`.

## Docs to update

`docs/reference/data-formats.md` (`sections.jsonl`), `docs/reference/tooling.md` (`snapshot.py`, `tests/`),
`docs/how-to/create-corpus-snapshot.md` (concrete commands), `docs/reference/experiment-record.md` (snapshot date,
token total, tiktoken version), `README.md` pipeline order, Serena memory `pipeline`.

## Out of scope

Chunking, embeddings, retrieval, evaluation logic (only the two relevance thresholds are added to config).
