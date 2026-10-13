# Pipeline

Flow, repo layout and data formats: `docs/explanation/research-design.md`, `docs/reference/tooling.md`, `docs/reference/data-formats.md`; commands and order: `README.md`.
- Section spans for relevance: `data/processed/sections.jsonl` (`docs/reference/data-formats.md`); chunk
  `start_token`/`end_token` must come from `src/tokens.py` so chunks and sections share one index space.
- `preprocess.py` rewrites `documents.jsonl` in place and refuses a second run (re-run `ingest.py` first); unknown HTML
  in the corpus raises on purpose — add a test + rule in `preprocess.py`, never silence it.
- Implemented: `snapshot.py`, `ingest.py`, `preprocess.py`, `tokens.py`, `chunking.py` (tests in `tests/`). Other `src/*.py` are stubs (`raise NotImplementedError`); implement in pipeline order, minimal
  prototype first (`docs/how-to/run-the-experiment.md`: load → C1–C3 → embed → Chroma per strategy → one question → top-5 → answer).
- `ingest.py`/`preprocess.py` take no CLI options; the per-strategy scripts take `--strategy C1|C2|C3|all`.
- Persist every intermediate artefact (`data/processed/`, `data/evaluation/`); raw and processed data are gitignored,
  their folders survive via `.gitkeep` negation rules in `.gitignore`.
- Results for the thesis go to `output/tables/*.tex`, `output/figures/*.pdf` (`docs/how-to/deliver-results-to-thesis.md`).
