# Corpus extension and C3 comparability: design

Date: 14.10.2026. Status: approved in chat (sections 1 and 2). Decisions: new ADR 0025 (corpus scope and commit,
replaces the scope of [ADR 0019](../../adr/0019-korpus-ausschnitt.md)), new ADR 0026 (C3 comparability), addendum to
[ADR 0021](../../adr/0021-c3-grenzen.md); existing [ADR 0005](../../adr/0005-drei-chunking-strategien.md),
[ADR 0006](../../adr/0006-nur-chunking-variiert.md), [ADR 0008](../../adr/0008-kosten-als-variable.md),
[ADR 0014](../../adr/0014-temperatur-und-topk.md), [ADR 0017](../../adr/0017-fragenkatalog.md),
[ADR 0020](../../adr/0020-playground-urls-kuerzen.md), [ADR 0024](../../adr/0024-referenzvektoren-und-exakte-suche.md).

## Goal

1. Extend the corpus from the Vue guide to the layered structure of real open-source documentation: concepts (guide),
   reference (API, Composition only) and conventions (style guide), pinned to the current `vuejs/docs` commit.
2. Make C3 comparable with C1/C2 without changing any strategy: a declared size-matched control, a sensitivity rule
   that does not exclude small chunks by construction, size and context reported as metrics, and a documented reason
   for the 800-token ceiling.

Both happen before the ground truth is frozen (milestone 09.11.2026, ADR 0017); no evaluation exists yet. The two
pilot probes (experiment record, 14.10.2026) are disclosed there; the decisions below rest on the design argument and
the literature, not on pilot numbers.

Success criteria:

- `snapshot.py` → `preprocess.py` → `chunking.py` → `embed.py` → `retrieve.py` run on the new corpus; every artefact
  matches `docs/reference/data-formats.md`.
- The guide part of the new corpus differs from the old one only by the 6 files changed upstream between the commits.
- Both pilot sets are remapped by script; every annotated section that changed text is listed and checked by hand.
- The control strategy never appears in `STRATEGY_IDS`; no answer generation runs for it.
- `uv run pytest`, pre-commit and Pyright pass; no test calls the OpenAI API.

## Decisions and evidence

| Decision | Evidence | Alternatives rejected |
|---|---|---|
| Scope: `src/guide/` (52), `src/api/` (22), `src/style-guide/` (5), about 79 documents (ADR 0025) | Real documentation is layered (concept, reference, conventions); topics recur across layers, which is the realistic retrieval case the thesis studies. Measured at the pinned commit with the current cleaner: API 18 of 22 pages clean, 31,134 tokens, 159 anchored headings, 0 headings without anchor; style guide 5 pages, 5,541 tokens, 36 anchored headings. The exposé limits the corpus "bewusst auf ausgewählte Bereiche"; three named areas fulfil that. | Guide only (no reference layer, less realistic); everything (tutorial, examples, about, ecosystem: contradicts the exposé wording). |
| Exclude the tutorial (ADR 0025) | 15 steps, about 6,500 tokens; each step describes an interactive editor whose code lives in separate files, and repeats the guide's essentials (step 2 explains `reactive()`/`ref()` and links to "Guide - Reactivity Fundamentals"). Near-duplicates would compete for the 5 slots and every question would need annotation against the tutorial too. | Include it (duplicates, annotation burden for about 4 % more text). |
| Exclude Options-API-only API pages: `options-state`, `options-lifecycle`, `options-composition`, `options-rendering`, `options-misc`, `component-instance`; exclude the generated index `api/index.md` (ADR 0025) | Same reasons as ADR 0019 for the guide: the docs site shows one API style at a time (preference switch), the two styles are near-duplicates that distort Precision@k/MRR, a question would have two correct answers, and mixed-style context degrades answers for reasons unrelated to chunking (ADR 0006). `api/index.md` is a Vue component listing links, no prose. | Keep both styles (duplicates, ambiguous ground truth). |
| Pin `vuejs/docs` at `40aa88af0094f7bab4aaf786e55c748a6a251d88` (15.09.2026) (ADR 0025) | GitHub compare `b75d188...main` on 14.10.2026: 8 commits ahead, 0 behind; in scope only 6 guide files change (+13/−9 lines: TransitionGroup wrapper note, scoped styles in slots, essentials conclusion moved to lifecycle, link fixes). All artefacts are rebuilt anyway; nothing is evaluated yet. | Stay on `b75d188` (older, broken links, no saving). |
| Size-matched control `K1`: fixed-size, no overlap, size = round(mean token length of the C3 chunks on the final corpus), fixed in `config.py`; retrieval only (ADR 0026) | C3 differs from C1/C2 in structure and size (old corpus: C3 median 202 vs 500 tokens; mean 239). Chunk size alone changes retrieval: smaller chunks raise precision while recall stays roughly flat (Smith & Troynikov 2024, `text-embedding-3-large`, 5 retrieved chunks); the best size depends on the question type (Bhat et al. 2025). K1 separates the two: same size as C3, no structure. The size follows a rule, not a choice. | Repack C3 to about 500 tokens (changes the exposé's strategy after a pilot; looks like tuning); equal token budget instead of `top_k = 5` (breaks ADR 0014 and the exposé). |
| Sensitivity rule: a chunk is relevant if it overlaps a relevant section by at least `min(SENSITIVITY_MIN_OVERLAP, chunk length)` tokens (ADR 0026) | Old corpus: 76 of 493 C3 chunks are shorter than 100 tokens and could never be relevant under a fixed 100-token minimum, even when fully inside the section; the rule would be biased against C3 by construction. With the minimum applied as `min(m, length)`, the main rule (`m = 1`) is unchanged. | Fixed 100 tokens (biased); share-based rule (new parameter without precedent). |
| Report chunk count, median and mean chunk size, and context tokens per answer for every strategy (ADR 0026) | Old corpus at top 5: mean context C1 ≈ 2,260, C2 ≈ 2,340, C3 ≈ 1,190 tokens; the difference matters for answer quality (H2) and is a cost (ADR 0008). The exposé already plans efficiency metrics. | Not reporting (hides a confounder). |
| Keep `C3_MAX_TOKENS = 800`, document the reason (addendum to ADR 0021) | The 8,192-token input limit of the embedding model is a technical maximum, not a recommendation. Larger chunks dilute the vector (Smith & Troynikov 2024) and, at fixed `top_k`, give C3 more context than C1/C2 (ADR 0006). Measured: without any ceiling the largest section after merging is 1,410 (guide) / 1,467 (API) tokens; 800 splits 12 of about 650 merged segments. | No ceiling (largest chunk ≈ 1,470, more context per hit); 500 (cuts more sections, departs from ADR 0005). |

Sources were checked on 14.10.2026 and go to `docs/reference/literature.md` (section "Technische Quellen"):
Smith, B., & Troynikov, A. (2024, 3. Juli). *Evaluating chunking strategies for retrieval*. Chroma.
https://www.trychroma.com/research/evaluating-chunking — Bhat, S. R., Rudat, M., Spiekermann, J., & Flores-Herr, N.
(2025). *Rethinking chunk size for long-document retrieval: A multi-dataset analysis* (arXiv:2505.21700).
https://arxiv.org/abs/2505.21700 — GitHub compare `vuejs/docs` `b75d188...main` (accessed 14.10.2026).

## Units

### Configuration (`src/config.py`)

- `VUE_DOCS_COMMIT = "40aa88af0094f7bab4aaf786e55c748a6a251d88"`.
- `VUE_DOCS_AREAS = ("api", "guide", "style-guide")`: folders below `src/` in the repo and below the snapshot dir;
  replaces `VUE_DOCS_SUBDIR` and `SNAPSHOT_SUBDIR`.
- `VUE_DOCS_EXCLUDED = ("api/index.md", "api/options-state.md", …, "api/component-instance.md")`: paths relative to
  `src/`, each must exist at the commit (a missing one is an error, so the list cannot rot silently).
- `CONTROL_STRATEGIES = {"K1": "fixed_<n>_no_overlap"}`, `K1_CHUNK_SIZE = <n>`, its chunk, vector and collection
  entries next to the existing ones. `<n>` is filled in once from the final C3 chunks (task in the plan).

### Snapshot (`src/snapshot.py`)

Copies every Markdown file of the configured areas minus the exclusions to `data/raw/vue_docs_snapshot/<area>/…`;
the record `docs/corpus_snapshot.txt` lists commit and SHA-256 per file and is verified, never overwritten, as now.

### Ingest and preprocessing (`src/ingest.py`, `src/preprocess.py`)

- Ingest reads all areas sorted by path (`api/…` < `guide/…` < `style-guide/…`) and assigns `D001…`.
- Preprocessing gains three rules, each test-first, everything else unknown still fails loudly:
  1. Escaped angle brackets in headings and text (`\<script setup>`, `PropType\<T>`) are literal text, not HTML.
  2. `<br>` inside a heading becomes a space (`# Composition API: <br>Dependency Injection`).
  3. The inline HTML case in `api/built-in-directives.md` (exact construct identified test-first during the task).
- Manifest and section names cover the new areas.

### Chunking, embedding, retrieval

- `chunking.py` builds K1 with the existing `fixed_size_spans`; the CLI accepts `K1`.
- `embed.py` embeds K1 like any strategy (canary check covers all stored files).
- Retrieval for K1 runs separately from the experiment set (`retrieve.py` keeps "always all of `STRATEGY_IDS`"),
  writing `retrieved_results_control.csv` in the format of `retrieved_results.csv`.
- `relevance.is_relevant` applies `min(min_overlap, chunk length)`.

### Pilot remap (`scripts/remap_pilot.py`, one-off)

Maps old doc and section IDs to new ones via the document path and the anchor; lists every annotated section whose
text differs between the commits; fails on any section that no longer exists.

### Metrics report

`scripts/difficulty_probe.py` additionally prints chunk count, median/mean chunk size and mean context tokens of the
top 5 per strategy, K1 included. The evaluation script later reuses the same functions.

## Data flow

snapshot (3 areas, 79 files) → ingest (`documents.jsonl`) → preprocess (`sections.jsonl`, manifest) → chunking
(C1, C2, C3, then K1 with the size from C3) → embed (4 files, about USD 0.07) → retrieve (C1–C3) + control retrieval
(K1) → pilot probes on the new corpus → experiment record.

## Error handling

- Excluded path missing at the commit, unknown HTML, a heading without anchor: abort with the file name.
- K1 size not yet set or inconsistent with the current C3 chunks: abort with the measured mean.
- Remap: a vanished section aborts; changed text is listed, not silently accepted.

## Testing

- Snapshot: areas and exclusions applied; missing exclusion fails (local git repo fixture, as now).
- Preprocess: one test per new rule plus a regression test that the guide cleaning is unchanged.
- Relevance: fully covered 60-token chunk relevant at `m = 100`; 500-token chunk with 40 overlapping tokens not
  relevant; `m = 1` unchanged.
- Control: `K1` not in `STRATEGY_IDS`; its size comes from config; `retrieve.py` still rejects partial strategy sets.
- Corpus integration tests updated to the new counts (skip without snapshot, as now).

## Documentation

ADR 0025, ADR 0026, addendum to ADR 0021; `docs/reference/corpus.md`, `data-formats.md` (control file),
`experiment-record.md` (new snapshot, chunk and embedding figures, pilots rerun), `literature.md`, `plan.md`,
`AGENTS.md` status line and `.serena/memories`.

## Out of scope

Answer generation for K1; repacking or otherwise changing C3; the question catalogue itself (next step, with the
section lookup list and coverage check).
