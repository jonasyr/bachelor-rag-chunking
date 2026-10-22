# Pipeline

Order and procedure: `docs/how-to/run-the-experiment.md`; script options, env vars and repo tree:
`docs/reference/tooling.md`; artefacts and run logs: `docs/reference/data-formats.md`; corpus rules: `docs/reference/corpus.md`.
- Each step checks its predecessor's latest run record (`run_log.require_run`): after changing questions or chunk files
  re-run retrieve before generate, generate before scaffold. `retrieve.py` rewrites its result files on every run.
- Every step after the catalogue refuses the main catalogue until `catalogue_freeze.json` matches (ADR 0030) — never
  delete the record to get past it; test recipe: `docs/reference/tooling.md#tests`.
- Catalogue: all editor writes go through `src/catalogue_store.py`; Claude's review only appends `open` rows to
  `catalogue_review.csv`; never run `catalogue.py plan` twice (new plan needs a new ADR).
- Closed-book screen (`catalogue.py screen`, calls the API) and K0 (written by `generate.py`): ADR 0040, 0041.
- MDX: unknown components/HTML/JSX raise on purpose — add a test + rule in `src/mdx.py`, never silence it or
  special-case a page (ADR 0042).
- Embedding vectors are stored once (ADR 0024); to re-embed, delete the `.npz` deliberately, never edit it.
- A corpus change renumbers doc IDs; remapping annotations is a scripted, reviewed step, never by hand
  (precedent: `scripts/remap_pilot.py`, ADR 0025, historical, does not apply to e2e).
- Analysis: `src/analyse.py` (ADR 0044); `--set DIR` writes `DIR/output/`; procedure `evaluation.md#statistische-auswertung`.
- Main-run query vectors and retrieval results are versioned (ADR 0045), pilot vectors are not.
