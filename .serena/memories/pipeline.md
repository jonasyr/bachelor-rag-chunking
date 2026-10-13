# Pipeline

Flow, repo layout and data formats: `docs/explanation/research-design.md`, `docs/reference/tooling.md`, `docs/reference/data-formats.md`; commands and order: `README.md`.
- All `src/*.py` except `config.py` are stubs (`raise NotImplementedError`); implement in pipeline order, minimal
  prototype first (`docs/how-to/run-the-experiment.md`: load → C1–C3 → embed → Chroma per strategy → one question → top-5 → answer).
- `ingest.py`/`preprocess.py` take no CLI options; the per-strategy scripts take `--strategy C1|C2|C3|all`.
- Persist every intermediate artefact (`data/processed/`, `data/evaluation/`); raw and processed data are gitignored,
  their folders survive via `.gitkeep` negation rules in `.gitignore`.
- Results for the thesis go to `output/tables/*.tex`, `output/figures/*.pdf` (`docs/how-to/deliver-results-to-thesis.md`).
