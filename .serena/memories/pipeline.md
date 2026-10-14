# Pipeline

Flow and layout: `docs/explanation/research-design.md`, `docs/reference/tooling.md` (repo tree, script options);
data formats: `docs/reference/data-formats.md`; order and procedure: `README.md`, `docs/how-to/run-the-experiment.md`.
- Stubs (`raise NotImplementedError`): only `generate.py`, `evaluate_retrieval.py`, `evaluate_answers.py`; all other
  `src/*.py` are implemented and tested. Next: `generate.py` (prototype: one question, top-5, answer).
- Section spans for relevance: `data/processed/sections.jsonl`; chunk `start_token`/`end_token` must come from
  `src/tokens.py` so chunks and sections share one index space.
- `preprocess.py` rewrites `documents.jsonl` in place and refuses a second run (re-run `ingest.py` first);
  `chunking.py` refuses input whose `sections.jsonl` does not match `documents.jsonl` (ingest re-run without
  preprocess); unknown HTML in the corpus raises on purpose — add a test + rule in `preprocess.py`, never silence it.
- Embedding vectors are stored once (`embeddings_cN.npz`, `query_embeddings.npz`, ADR 0024); to re-embed, delete the
  file deliberately — never edit it. Tests use the `fake_embedder` fixture (`tests/conftest.py`), never the API.
- Corpus areas/exclusions only in `config.VUE_DOCS_AREAS`/`VUE_DOCS_EXCLUDED` (ADR 0025); every exclusion must remove
  exactly one .md file. Doc IDs follow path order (api < guide < style-guide) — a corpus change renumbers them; remap
  annotations by path + anchor (`scripts/remap_pilot.py`), never by hand.
- Headings may be indented up to 3 spaces (CommonMark); `\<` stays escaped in text, titles show `<` (`docs/reference/corpus.md`).
- Raw and processed data are gitignored; their folders survive via `.gitkeep` negation rules in `.gitignore`.
- Results for the thesis: `docs/how-to/deliver-results-to-thesis.md` (`output/figures/*.pdf` is versioned via a
  `.gitignore` exception to `*.pdf`).
