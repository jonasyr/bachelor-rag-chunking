# Pipeline

Flow and layout: `docs/explanation/research-design.md`, `docs/reference/tooling.md` (repo tree, script options);
data formats: `docs/reference/data-formats.md`; order and procedure: `README.md`, `docs/how-to/run-the-experiment.md`.
- No stubs left: every `src/*.py` is implemented and tested. `generate.py` (ADR 0033) never overwrites
  `generated_answers.csv`; tests use a fake completer, never the API (`tests/test_generate.py`). Each step checks
  the latest run record of its predecessor (`run_log.require_run`): re-run retrieve before generate, generate before
  scaffold, whenever questions or chunk files change.
  `evaluate_retrieval.py` recomputes relevance from chunks and refuses results whose `is_relevant` disagrees. Status and next step: `docs/plan.md#stand`.
- Question catalogue: `src/catalogue.py` (sections/find/show/check/freeze), how-to
  `docs/how-to/build-the-question-catalogue.md`; `retrieve.py` refuses the main catalogue until
  `catalogue_freeze.json` matches (ADR 0030) — never delete the record to get past it; tests monkeypatch
  `freeze.QUESTIONS_FILE`/`GROUND_TRUTH_FILE` instead.
- Catalogue authoring (ADR 0031): editor `uv run streamlit run app/catalogue_editor.py --server.address localhost`; all writes
  go through `src/catalogue_store.py` (atomic, strict). Claude's review only appends `open` rows to
  `data/evaluation/catalogue_review.csv` and never edits questions/ground truth; never run `catalogue.py plan` twice.
- Scoring page (ADR 0034): app/scoring_page.py + src/scoring_store.py read only scoring_items.jsonl and the sheet, never the key; tests/test_scoring_page.py checks that statically.
- Rule-based scoring (ADR 0035): key points -> freeze (run record with sha) -> checks -> scoring_rules.derive; summarise verifies sheet vs scoring_checks.csv. Details: docs/reference/evaluation.md#regelbasierte-bewertung. Key point text is Jonas's only. New scaffolds carry "scoring":"rules" (ADR 0036): summarise then refuses hand-entered sheets. ADR 0037: key points pre-filled from the reference (scoring_rules.split_reference, Jonas confirms); check rules in the form help texts (POINT_HELP/HELP in app/scoring_page.py) and evaluation.md.
- Section spans for relevance: `data/processed/sections.jsonl`; chunk `start_token`/`end_token` must come from
  `src/tokens.py` so chunks and sections share one index space.
- `preprocess.py` rewrites `documents.jsonl` in place and refuses a second run (re-run `ingest.py` first);
  `chunking.py` refuses input whose `sections.jsonl` does not match `documents.jsonl` (ingest re-run without
  preprocess); unknown MDX components/HTML/JSX raise on purpose — add a test + rule in `src/mdx.py` (`to_markdown`), never
  silence it or special-case a page. Rules: `docs/reference/corpus.md#aufbereitung-mdx--markdown`.
- Embedding vectors are stored once (`embeddings_cN.npz`, `query_embeddings.npz`, ADR 0024); to re-embed, delete the
  file deliberately — never edit it. Tests use the `fake_embedder` fixture (`tests/conftest.py`), never the API.
- Corpus (ADR 0038): pages must equal the `docs.json` navigation; areas = navigation groups (`config.CORPUS_AREAS`,
  `area` in documents.jsonl). Anchors = site slugs (`mdx.slug`), H1 anchor = path slug. Doc IDs follow path order —
  a corpus change renumbers them; remap annotations by path + anchor (`scripts/remap_pilot.py`), never by hand.
- Closed-book screen: `catalogue.py screen` (API) → `closed_book_screen.csv` → editor tab Closed-book; check/freeze
  need all judged and ≤ 16 hits. Code `src/closed_book.py`; ADR 0040, docs/reference/data-formats.md.
- Control K0: generate.py writes generated_answers_control.csv in the same run; scoring via
  `evaluate_answers.py --control` (src/control_k0.py) only after scores.csv; page set "…: control K0" (no grounded).
  ADR 0041, docs/reference/evaluation.md#kontrolle-k0.
- Catalogue quotas: 15 e2e areas, slots = reserve = minimum by token share (ADR 0039); plan drawn 18.10.2026, Vue plan in `data/evaluation/archive_vue/`.
- Raw and processed data are gitignored; their folders survive via `.gitkeep` negation rules in `.gitignore`.
- Results for the thesis: `docs/how-to/deliver-results-to-thesis.md` (`output/figures/*.pdf` is versioned via a
  `.gitignore` exception to `*.pdf`).
