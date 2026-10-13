# Chunking C1–C3: design

Date: 13.10.2026. Status: approved in chat. Decision basis: [ADR 0005](../../adr/0005-drei-chunking-strategien.md),
[ADR 0006](../../adr/0006-nur-chunking-variiert.md), [ADR 0010](../../adr/0010-starke-baseline.md), new ADR 0021
(C3 bounds); formats: [data formats](../../reference/data-formats.md).

## Goal

Turn `data/processed/documents.jsonl` (cleaned corpus, 52 documents, 117,594 tokens) into `chunks_c1.jsonl`,
`chunks_c2.jsonl` and `chunks_c3.jsonl` so that only the segmentation differs between strategies. No OpenAI calls.

Success criteria:

- `uv run python src/chunking.py [--strategy C1|C2|C3|all]` writes the three files with keys exactly
  `chunk_id, doc_id, strategy, text, start_token, end_token`.
- Every chunk's `text` is the exact slice of its document for `[start_token, end_token)`; nothing is prepended,
  stripped or normalised.
- C1 and C3 tile each document exactly (no gap, no overlap); C2 covers each document, consecutive chunks overlap by
  exactly `C2_OVERLAP` tokens (only the last window can be shorter than `C2_CHUNK_SIZE`).
- Size limits: C1/C2 chunks ≤ 500 tokens, C3 chunks ≤ 800 tokens.
- `uv run pytest` and `uvx pre-commit run --all-files` pass.

## Token space

All spans are positions in the token sequence of the document's cleaned `text` produced by `src/tokens.py`
(`cl100k_base`), the same space as `sections.jsonl`. A chunk's `text` is cut by characters at
`token_starts(text)[start_token]` up to `token_starts(text)[end_token]` (or the end of the text), which avoids broken
multi-byte characters that decoding a token slice can produce. Re-encoding a chunk's `text` alone may yield a slightly
different token count than `end_token − start_token` (BPE merges at the cut); the span is authoritative.

## Units (`src/chunking.py`)

| Function | Responsibility |
|---|---|
| `fixed_size_spans(n_tokens, size, overlap) -> list[tuple[int, int]]` | Windows starting at 0 with step `size − overlap`; each window is `[start, min(start + size, n))`; stops after the window that reaches `n`. `n == 0` gives no spans; `overlap >= size` or `size <= 0` raises `ValueError`. C1 = (500, 0), C2 = (500, 100). |
| `paragraph_breaks(text, starts, lo, hi) -> list[int]` | Token positions inside `(lo, hi)` where a paragraph starts: the first token at or after the character following a blank line, ignoring blank lines inside fenced code blocks. |
| `structure_spans(n_tokens, boundaries, breaks, max_tokens, min_tokens) -> list[tuple[int, int]]` | C3: (1) segments between consecutive heading boundaries (H1–H3 `start_token` values from `sections.jsonl`, plus `n`); (2) merge (before splitting): a segment shorter than `min_tokens` is always joined with the following segment (chains accumulate); a short last segment is joined with the previous one; (3) split: a segment longer than `max_tokens` is cut at the furthest paragraph break that keeps the piece between `min_tokens` and `max_tokens` and leaves a rest of at least `min_tokens`; without such a break the cut is hard at `min(start + max_tokens, end − min_tokens)`. Hence no C3 chunk is shorter than `min_tokens` unless its whole document is. |
| `make_chunks(doc, spans, key) -> list[dict]` | Chunk records with `chunk_id = {key}_{doc_id}_{seq:04d}` (seq from 1 per document and strategy), `strategy = STRATEGY_IDS[key]`, `text` = character slice. |
| `check_chunks(doc, chunks, key)` | Runtime invariants (below); raises `ValueError` naming the chunk. |
| `chunk(key, docs_file, sections_file, out_file) -> int` | Reads inputs, builds and checks chunks for all documents, writes the JSONL file, returns the chunk count. |

CLI (unchanged): `--strategy C1|C2|C3|all` (default `all`); prints per strategy the chunk count and min/mean/max
span length.

## Invariants (checked at runtime and in tests)

- Spans are non-empty and within `[0, n]`; IDs unique per file.
- C1, C3: spans are sorted, the first starts at 0, each starts where the previous ends, the last ends at `n`.
- C2: the first starts at 0, the last ends at `n`, consecutive starts differ by exactly `size − overlap`, and every
  window except the last has length `size` (so neighbours overlap by exactly `overlap` tokens).
- Lengths: C1/C2 ≤ `C1_CHUNK_SIZE`/`C2_CHUNK_SIZE`; C3 ≤ `C3_MAX_TOKENS`.
- `text == doc_text[char(start):char(end)]`.

## Configuration (`src/config.py`)

Add `C3_MIN_TOKENS = 50` next to `C3_MAX_TOKENS` (ADR 0021). Existing `C1_*`, `C2_*`, `C3_MAX_TOKENS`, `STRATEGY_IDS`,
`CHUNK_FILES` are used unchanged.

## Error handling

`FileNotFoundError` with a hint for missing `documents.jsonl` (run `preprocess.py`) or `sections.jsonl`;
`ValueError` if `sections.jsonl` does not describe the current `documents.jsonl` (last section end ≠ token count, or a section start not at a `#` line — e.g. `ingest.py` re-run without `preprocess.py`; checked for every strategy), if a document has no sections, a section belongs to an unknown document, or the H1 section does not start at
token 0; `ValueError` for invalid window parameters and for any violated invariant.

## Tests (`tests/test_chunking.py`, written first)

- `fixed_size_spans`: `n < size`, `n == size`, exact multiple, C2 step and final window, `n == 0`, invalid overlap.
- `paragraph_breaks`: blank lines split; blank lines inside a fence do not.
- `structure_spans`: plain segments, forward merge (also chains and into an oversized segment), short last segment
  merged backward, paragraph split, no tail under the floor, oversized single paragraph cut hard, tiling.
- `make_chunks` / `chunk`: exact keys and order, IDs, `strategy` values, text slices, written file, error hints.
- `tests/test_corpus_integration.py`: on the real processed corpus (skipped without it), all invariants for C1–C3 and
  plausible counts (C2 > C1, every C3 chunk between 50 and 800 tokens).

## Docs to update

ADR 0021 (floor 50, merge before split, paragraph split without short tails, hard cut as last resort) + ADR index;
`docs/explanation/research-design.md` C3 note (link to ADR 0021); `docs/reference/tooling.md` status;
`docs/reference/experiment-record.md` chunk counts per strategy; Serena memory `chunking`.

## Out of scope

Embedding, retrieval, relevance computation (they consume these files next).
