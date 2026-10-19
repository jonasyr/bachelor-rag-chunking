# Pipeline

Order and procedure: `docs/how-to/run-the-experiment.md`; script options and repo tree: `docs/reference/tooling.md`;
artefacts and run logs: `docs/reference/data-formats.md`; corpus rules: `docs/reference/corpus.md`.
- Each step checks its predecessor's latest run record (`run_log.require_run`): after changing questions or chunk files
  re-run retrieve before generate, generate before scaffold.
- `retrieve.py` refuses the main catalogue until `catalogue_freeze.json` matches (ADR 0030) — never delete the record to
  get past it; tests monkeypatch `freeze.QUESTIONS_FILE`/`GROUND_TRUTH_FILE` instead.
- Catalogue: all editor writes go through `src/catalogue_store.py`; Claude's review only appends `open` rows to
  `catalogue_review.csv`; never run `catalogue.py plan` twice (new plan needs a new ADR).
- Closed-book screen (`catalogue.py screen`, calls the API) and K0 (written by `generate.py`): ADR 0040, 0041. Tests
  redirect `catalogue.CLOSED_BOOK_FILE` (autouse fixture) and use fake completers.
- Chunk `start_token`/`end_token` come from `src/tokens.py` (same index space as `sections.jsonl`).
- MDX: unknown components/HTML/JSX raise on purpose — add a test + rule in `src/mdx.py`, never silence it or
  special-case a page (ADR 0042).
- Embedding vectors are stored once (ADR 0024); to re-embed, delete the `.npz` deliberately, never edit it. Tests use
  `fake_embedder`, never the API.
- A corpus change renumbers doc IDs: remap annotations with `scripts/remap_pilot.py`, never by hand.
- `pre-commit run --all-files` skips untracked files: `git add` new files first.
