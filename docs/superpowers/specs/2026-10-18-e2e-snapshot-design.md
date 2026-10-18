# e2e snapshot and MDX preprocessing: design

Date: 18.10.2026. Status: approved in chat (18.10.2026). Decision basis: [ADR 0038](../../adr/0038-korpus-e2e.md),
formats: [data formats](../../reference/data-formats.md), corpus facts: [corpus](../../reference/corpus.md).
Step 2 of the corpus switch ([plan](../../plan.md#stand)); chunking, embeddings and K1 follow in step 3, areas'
quotas and the sampling plan in step 4.

## Goal

Turn `tester-army/e2e` `docs/` at commit `ef977f4856da009cac26d78d2e9bb14e5991ee41` into `documents.jsonl`,
`sections.jsonl`, `section_index.md` and `docs/corpus_manifest.csv`, losing as little content as possible: every
piece of text a reader of the site can see stays, only navigation chrome, media embeds and images go. Reproducible,
test-first, no OpenAI calls.

Success criteria:

- `snapshot.py`, `ingest.py`, `preprocess.py` run in that order from the repo root without options.
- 60 documents `D001`–`D060`, one per page of the `docs.json` navigation; the page set must equal the navigation.
- No MDX component, JSX expression, `import`/`export` line or HTML tag remains outside code (integration test).
- Code inside fences is unchanged apart from the info string and trailing whitespace.
- Every H1–H3 heading yields one `section_id = {doc_id}#{anchor}`, unique across the corpus; H2/H3 anchors equal the
  anchors of the live site.
- `uv run pytest` and `uvx pre-commit run --all-files` pass.

## Corpus facts (measured 18.10.2026 at ef977f4)

- 60 `.mdx` pages: 40 directly in `docs/`, plus `ci/` (4), `integrations/` (7), `migrate/` (5), `reference/` (16);
  all 60 and only these are in `docs.json` (tabs Documentation, Reference, Examples). No other `.mdx` exists below
  `docs/`.
- Frontmatter keys: `title` (60), `description` (60), `sidebarTitle`, `icon`, `og:image`, `twitter:image`; all
  single-line scalars, some double-quoted. No page body has an H1.
- No explicit heading anchors. The site's anchors follow one rule, checked against the live pages for all 503
  fetchable H2/H3 headings (the page `mcp` is shadowed by Mintlify's MCP endpoint at `/docs/mcp`): drop link targets
  and backticks, lowercase, replace each run of characters other than `a-z0-9` by `-`, strip `-` at both ends
  (`` `.env` files `` → `env-files`, `agent.act` → `agent-act`, `For scripts: report.json` →
  `for-scripts-report-json`). No two H2/H3 headings of a page share a slug.
- Components outside code (opening and closing tags counted): `Card` 208, `CodeGroup` 140, `Note` 104, `CardGroup`
  86, `Accordion` 86, `Tab` 48, `Warning` 30, `SetupPrompt` 20, `Tabs` 18, `Prompt` 10, `Step` 10, `Video` 8,
  `AccordionGroup` 8, `ModelProvider` 8, `Steps` 4, `ShowMore` 2, `VideoCard` 2, `Tip` 2; HTML: `<video>` 4,
  `<a id>` 7, `<span id>` 1. `import` lines in 17 pages, `export const` prompt templates in 10 pages.
- Fence info strings: a language, optionally followed by `title="…"`, a bare label (`bash npm`, `bash Claude`,
  `bash macOS`) and the flags `expandable`, `wrap`.

## Units

| Unit | Responsibility |
|---|---|
| `src/config.py` | `VUE_DOCS_*` replaced by corpus-neutral keys: `CORPUS_REPO_URL`, `CORPUS_COMMIT`, `CORPUS_ROOT = "docs"`, `CORPUS_PAGE_SUFFIX = ".mdx"`, `CORPUS_NAV_FILE = "docs.json"`, `CORPUS_PROVIDER_SNIPPET = "snippets/model-provider.jsx"`, `CORPUS_AREAS` (the 15 navigation groups in order, Examples tab as one area), `CORPUS_SITE_URL = "https://e2e.tester.army/docs"`; `DATA_RAW = data/raw/e2e_docs_snapshot`. `SYSTEM_PROMPT` says "the e2e testing framework" instead of "Vue.js". |
| `src/snapshot.py` | Fetch the pinned commit (unchanged), copy every `*.mdx` below `CORPUS_ROOT` plus the navigation file and the provider snippet to `DATA_RAW` (same relative paths), check that the pages equal the navigation's pages, write or verify `docs/corpus_snapshot.txt` (repository, commit, dates, files, SHA-256 per file including the two support files). The exclusion mechanism goes: nothing is excluded, and the navigation check replaces it. |
| `src/ingest.py` | Read the pages sorted by POSIX path, `D001…` in that order; `title` from the frontmatter (`title`), `area` = navigation group of the page; raw `text`, `tokens`; write `documents.jsonl`. Stops if a page lacks `title` or is not in the navigation, or the navigation's groups differ from `CORPUS_AREAS`. |
| `src/mdx.py` (new) | Pure functions: `parse_frontmatter`, `slug`, `parse_providers(jsx) -> list[dict]` (the provider list of the snippet, read with a small JS-literal parser), `render_provider(show, providers)`. |
| `src/preprocess.py` | `clean_markdown(text, providers) -> CleanResult` rewritten for MDX (rules below); `section_spans` unchanged; `preprocess()` loads the provider list from the snapshot, rewrites `documents.jsonl`, writes `sections.jsonl` and the manifest (`section` = area). All Vue rules go (they stay in the git history). |
| `src/catalogue.py` | `Corpus.area(section)` returns the document's `area` field instead of the first path segment, so the section index shows the navigation group. Quotas (`AREA_MIN_QUESTIONS`, `CATALOGUE_AREA_SLOTS`, `CATALOGUE_RESERVE`) keep their Vue keys until step 4 replaces them; the catalogue tools are not used before. |
| `src/catalogue_store.py` | Site-relative links use `CORPUS_SITE_URL`. |

## Cleaning rules (outside code fences; fence content stays verbatim)

| Input | Output |
|---|---|
| Frontmatter | `# {title}`, blank line, `{description}` as the first paragraph; `sidebarTitle`, `icon` and image keys dropped |
| `import …` lines | dropped |
| `export const NAME = \`…\`;` (multi-line template) | kept as the value of NAME for a `<Prompt>` that names it; the line block itself dropped |
| `<SetupPrompt>` with `<Prompt description={NAME} …/>` | `**Agent prompt**` (the snippet's header text), then the template's text as a ```` ```text ```` block (`` \` `` unescaped) |
| `<Note>`, `<Warning>`, `<Tip>` | a line `**Note**` / `**Warning**` / `**Tip**`, then the content |
| `<Accordion title="T">`, `<Tab title="T">` | a line `**T**`, then the content |
| `<Steps>` / `<Step title="T">` | a line `**N. T**` (N counts the steps of the block from 1), then the content |
| `<AccordionGroup>`, `<Tabs>`, `<CodeGroup>`, `<CardGroup>`, `<ShowMore>`, `<Video>` and all closing tags | wrapper lines dropped, content kept |
| `<Card title="T" href="H">body</Card>` | `- [T](H): body` (body joined to one line; without `href`: `- **T**: body`) |
| `<VideoCard title="T" subtitle="S" …/>` | `- **T**: S` |
| `<video …/>` (inside `<Video>`, caption kept) | dropped |
| `<a id="…" />`, `<span id="…" />` (legacy anchors) | dropped |
| `<ModelProvider show="select" />` | Markdown table of all providers: provider, group, packages, variables, import, model, note (with the snippet's sentence for providers that read their variables at load) |
| `<ModelProvider show="install\|env\|config\|model" />` | what the site shows without a selection (first provider, npm): a line `**Install · Vercel AI Gateway**` (and so on) and the code block the snippet builds |
| Fence info `lang title="X" flags` or `lang Label flags` | a line `**X**` / `**Label**` before the fence; the fence keeps only the language |
| H1–H3 heading | anchor = `slug(heading)`; the generated H1's anchor = `slug(path without suffix)` (the site has no H1 anchor, and `reference/config`'s title slug collides with an H3) |
| Any other component, JSX expression or HTML tag outside inline code | error naming the page and line |

Indentation inside components is kept; it carries no meaning for headings (at most 3 spaces) or token spans.

## Error handling

Every rule fails loudly: unknown component, unbalanced component, `<Prompt>` naming an unknown export, unknown
`show`, a provider list that does not parse to the expected keys, duplicate anchor, document without exactly one H1.
`preprocess()` refuses to run twice (input still starts with frontmatter).

## Testing

- Unit tests per rule in `tests/test_clean_markdown.py` (rewritten) and `tests/test_mdx.py` (slug cases from the live
  site, frontmatter, provider parser on a small literal, provider renderings).
- `tests/test_snapshot.py`, `tests/test_ingest.py`: local git repository with `.mdx` pages, a navigation file and a
  snippet; navigation mismatch and missing title fail.
- `tests/test_corpus_integration.py` on the real snapshot: 60 files, every page cleans, no leftover markup, unique
  section IDs, text slices exact. Skips without a snapshot, as before.
- Counts (documents, sections, tokens) go to the experiment record.

## Documentation

`corpus.md`, `how-to/create-corpus-snapshot.md`, `data-formats.md` (`documents.jsonl` gains `area`),
`configuration.md`, `prompts.md`, `tooling.md`, `experiment-record.md`, `plan.md`, README (Apache-2.0 and NOTICE of
the e2e docs), `.gitignore` (new raw directory), AGENTS.md purpose line, Serena memories.

## Out of scope

Chunking, embeddings, K1 size (step 3); area quotas, sampling plan, stopwords, closed-book screen and K0 (step 4).
