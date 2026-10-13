# bachelor-rag-chunking

> Agent entry point. Keep it short: facts live in `docs/`; this file maps them.

## Purpose

Code of the bachelor's thesis "Einfluss von Chunking-Strategien auf die Retrieval- und Antwortqualität eines
RAG-Systems für technische Projektdokumentation" (Jonas Weirauch, IU, submission 24.12.2026). A RAG pipeline on the
Vue.js documentation in which only the chunking strategy (C1/C2/C3) varies. Status 13.10.2026: corpus fixed (ADR 0019);
`snapshot.py`, `ingest.py`, `preprocess.py` implemented and tested, later steps are stubs (`docs/plan.md`).
Public repo (DOI planned); used by the private PaperLab repo as submodule `code/`.

## Commands

| Task | Command |
|---|---|
| Install | `uv sync` (then `cp .env.example .env`, add `OPENAI_API_KEY`) |
| Lint/format | `uvx pre-commit run --all-files` (ruff + checks; also runs on commit after `pre-commit install`) |
| Test | `uv run pytest` (`tests/`; corpus integration tests skip until the snapshot exists, e.g. in CI) |
| Run | `uv run python src/<step>.py` — order: `README.md` (snapshot → ingest → preprocess → …), options: `docs/reference/tooling.md` |

## Conventions

- All parameters (paths, chunk sizes, models, top-k, temperature) live only in `src/config.py`.
- Invariants: only chunking varies; `temperature = 0`, `top_k = 5`; prompt constant (`docs/reference/prompts.md`); ground
  truth final before any evaluation (ADR 0006, 0014, 0017).
- Strategy keys `C1`/`C2`/`C3`; strategy field values and IDs as in `config.STRATEGY_IDS`; data formats exactly as in
  `docs/reference/data-formats.md` (`questions.csv` includes `notes`).
- Corpus, questions and answers in English; thesis text in German (lives in PaperLab).
- Conventional Commits; no AI attribution lines. Never commit `.env`. Plans go to `docs/superpowers/plans/` (versioned).

## Map

- `docs/README.md` — documentation index (single source of truth)
- `docs/how-to/`, `docs/reference/`, `docs/explanation/` — tasks, exact facts (formats, metrics, prompts), research design
- `docs/plan.md` — schedule (to 24.12.2026) and open decisions
- `docs/adr/` — decisions D1–D19
- `.serena/memories/` — agent working notes; `core` is the entry point, each memory links into `docs/`
