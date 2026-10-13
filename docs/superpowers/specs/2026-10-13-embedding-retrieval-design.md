# Embedding, vector index and retrieval: design

Date: 13.10.2026. Status: approved in chat. Decisions: new ADR 0023 (embedding model) and ADR 0024 (exact search,
reference vectors); existing [ADR 0006](../../adr/0006-nur-chunking-variiert.md),
[ADR 0008](../../adr/0008-kosten-als-variable.md), [ADR 0012](../../adr/0012-retrieval-metriken.md),
[ADR 0014](../../adr/0014-temperatur-und-topk.md), [ADR 0015](../../adr/0015-tech-stack.md),
[ADR 0016](../../adr/0016-modell-neutralitaet.md), [ADR 0017](../../adr/0017-fragenkatalog.md),
[ADR 0019](../../adr/0019-korpus-ausschnitt.md), [ADR 0022](../../adr/0022-h1-abschnitte-in-ground-truth.md).

## Goal

Embed the chunks of C1–C3 with one fixed model, build one Chroma index per strategy, retrieve the top 5 chunks per
question and strategy with provably exact cosine search, and mark each hit as relevant by token overlap with the
annotated sections. Everything must be reproducible from stored artefacts and only the chunking may differ between
strategies.

Scope: the code and its tests now; embedding the real chunks after an explicit OK (costs about USD 0.05); the real
retrieval run only after the ground truth is frozen (milestone 09.11.2026, ADR 0017).

Success criteria:

- `embed.py` and `retrieve.py` run from the repo root; outputs match `docs/reference/data-formats.md` exactly.
- A rebuild of the indices and a repeated retrieval run reproduce `retrieved_results.csv` byte for byte without any
  API call (stored reference vectors).
- Every Chroma top 5 is checked against an exact NumPy cosine ranking; a mismatch aborts the run.
- No test calls the OpenAI API; `uv run pytest`, pre-commit and Pyright pass.

## Decisions and evidence

Sources were checked on 13.10.2026 and go to `docs/reference/literature.md` (section "Technische Quellen").

| Decision | Evidence | Alternatives rejected |
|---|---|---|
| Model `text-embedding-3-large`, default 3,072 dimensions (ADR 0023) | OpenAI embeddings guide: MTEB 64.6 % (large) vs 62.3 % (small); max input 8,192 tokens; `cl100k_base` tokenizer (same as `src/tokens.py`). Model page: USD 0.13 per 1M tokens, single snapshot `text-embedding-3-large`. Corpus cost: C1 117,594 + C2 142,894 + C3 117,594 = 378,082 tokens ≈ USD 0.05. | `-small` (USD 0.02/1M; weaker model compresses strategy differences, saving is cents); local open-weight models (contradict ADR 0015, hardware dependence). |
| Store reference vectors once, build indices from them (ADR 0024) | OpenAI offers no dated snapshot for embedding models (model page lists only the alias), so the model behind the name can change; repeated calls are not guaranteed bit-identical. | Re-embedding per run (not reproducible). |
| Exact cosine search in Chroma, verified against NumPy (ADR 0024) | Chroma uses an approximate HNSW index; recall depends on `ef_search` (Chroma docs, "Configure"). OpenAI vectors are normalised to length 1, so cosine and dot product rank identically (OpenAI embeddings guide). With ≤ 500 vectors per strategy exact search is cheap. | Chroma defaults (approximate, not verifiable); NumPy only (needs a new ADR replacing ADR 0015's vector store). |
| Batches of 100 texts | API reference: ≤ 2,048 inputs and ≤ 300,000 tokens per request, ≤ 8,192 tokens per input; 100 × ≤ 800 tokens = ≤ 80,000 tokens. | One request per chunk (slow), maximal batches (no benefit). |
| Pin `openai==2.44.0`, `chromadb==1.5.9` | ADR 0016: versions fixed at implementation time and documented. | Ranges (`>=`), which let behaviour drift. |

## Units

| Unit | Responsibility |
|---|---|
| `src/embedding_client.py` (new) | `embed_texts(texts: list[str]) -> EmbeddingResult(vectors: np.ndarray[float32, (n, d)], input_tokens: int)`: OpenAI SDK, model `config.EMBEDDING_MODEL`, batches of `config.EMBEDDING_BATCH_SIZE`, SDK retries, order preserved; raises if `OPENAI_API_KEY` is missing (message points to `.env`, never prints the key) or if the dimension differs from `config.EMBEDDING_DIMENSIONS`. Loaded lazily so tests and other steps never need the key. |
| `src/vector_index.py` (new) | Chroma helpers: `build_collection(client, name, ids, vectors, metadatas)` (delete + create with `{"hnsw": {"space": "cosine", "ef_search": n, "ef_construction": max(n, 100)}}`, add in order), `query(collection, vector, k)`; `exact_top_k(vectors, ids, query, k) -> list[(chunk_id, score)]` sorted by score descending, then `chunk_id`. |
| `src/relevance.py` (new) | `overlap_tokens(chunk, section) -> int` (same document only; `[start, end)` spans, touching spans give 0); `is_relevant(chunk, sections, min_overlap) -> bool`. Used by `retrieve.py` (`config.RELEVANCE_MIN_OVERLAP`) and later by `evaluate_retrieval.py` (sensitivity, `config.SENSITIVITY_MIN_OVERLAP`). |
| `src/embed.py` | Per strategy: if `embeddings_cN.npz` exists and its `ids` and `texts` equal the chunk file's IDs and texts in order, reuse it (no API call); if it exists but differs, stop with a hint to delete it deliberately; otherwise embed and write it. Then rebuild the Chroma collection from the stored vectors and append a run record to `embedding_runs.jsonl`. CLI unchanged: `--strategy C1|C2|C3|all`. |
| `src/retrieve.py` | Reads `questions.csv`, `ground_truth.csv`, `sections.jsonl` and the chunk files; refuses empty question or ground-truth files; embeds the questions once into `query_embeddings.npz` (same reuse/refusal rule, keyed by `question_id` and question text); per question (sorted by `question_id`) and strategy queries Chroma (`n_results = TOP_K`), checks the result set and scores against `exact_top_k` (score tolerance 1e-5), writes the exact ranking with ranks 1–5, `score` = cosine similarity (6 decimals) and `is_relevant` (any overlap, ADR 0019); records SHA-256 of `questions.csv` and `ground_truth.csv` in the run log. |

## Artefacts and formats (added to `docs/reference/data-formats.md`)

- `data/processed/embeddings_c1.npz` (c2, c3): arrays `model`, `ids`, `texts` (str), `vectors` (float32, n × 3,072); reused only if model, IDs and texts match. Gitignored.
- `data/evaluation/query_embeddings.npz`: arrays `ids` (question IDs), `texts` (questions), `vectors`. Gitignored.
- `data/processed/embedding_runs.jsonl`: one record per embed or retrieval run:
  `{"step","strategy","model","dimensions","date","openai_sdk","chromadb","vectors","input_tokens","cost_usd","api_called","vector_bytes","inputs_sha256"}`.
- `ground_truth.csv`: several IDs in `relevant_doc_ids` / `relevant_section_ids` are separated by `;`.
- `retrieved_results.csv`: unchanged header `question_id,strategy,rank,chunk_id,score,is_relevant`.

## Configuration (`src/config.py`)

`EMBEDDING_MODEL = "text-embedding-3-large"`, `EMBEDDING_DIMENSIONS = 3072`, `EMBEDDING_BATCH_SIZE = 100`,
`EMBEDDING_PRICE_PER_MTOK = 0.13` (source and access date in a comment), `EMBEDDING_FILES` (per strategy),
`QUERY_EMBEDDINGS_FILE`, `EMBEDDING_RUNS_FILE`, `SCORE_TOLERANCE = 1e-5`, `ID_SEPARATOR = ";"`.

## Model-vintage check (added after the Codex review of PR #5)

Before new vectors join an existing set (another strategy or the questions), `src/canary.py` re-embeds the first,
middle and last stored text of each existing vector file and aborts if the cosine to the stored vector is below
`CANARY_MIN_COSINE = 0.999` (measured 13.10.2026: same model ≥ 0.99996, different chunks ≤ 0.84). The lowest value
goes to the run log as `canary_min_cosine`.

## Error handling

Fail loudly with a hint: missing API key; vectors not matching the chunk file; unexpected dimension; Chroma result
set or scores differing from the exact ranking; empty or missing questions/ground truth; a `relevant_section_id` not
in `sections.jsonl`; a question without ground truth.

## Tests (TDD; no network)

- `embedding_client`: batching and order with a fake SDK client; missing key; wrong dimension.
- `relevance`: overlap inside, partial, touching (0), other document (0); thresholds 1 and 100.
- `vector_index`: exact top-k with ties ordered by `chunk_id`; Chroma (tmp dir, cosine) agrees with `exact_top_k` on
  random normalised vectors; a forced mismatch is detected.
- `embed`: first run calls the fake embedder and writes npz + run record; second run reuses without a call; changed
  chunks make it stop.
- `retrieve`: exact CSV header and order, ranks 1–5, relevance flags from a small fixture, refusal on empty ground
  truth, unknown section ID, SHA-256 in the run log.

## Docs to update

ADR 0023, ADR 0024 (+ index); `docs/reference/literature.md` "Technische Quellen" (APA, access date 13.10.2026);
`docs/reference/data-formats.md`; `docs/reference/tooling.md` (embeddings row, status, `.env`); `docs/plan.md`
(model decision closed); `docs/reference/experiment-record.md` (model, SDK versions, date, tokens, cost after the
real run); Serena memories `tech_stack`, `pipeline`.

## Out of scope

Answer generation (`generate.py`, LLM choice), answer evaluation, `evaluate_retrieval.py` metrics (they consume
`retrieved_results.csv` and `relevance.py` next).
