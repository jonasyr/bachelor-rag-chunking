# bachelor-rag-chunking

> Agent entry point. Keep it short: facts live in `docs/`; this file maps them.

## Purpose

Code of the bachelor's thesis "Einfluss von Chunking-Strategien auf die Retrieval- und Antwortqualität eines
RAG-Systems für technische Projektdokumentation" (Jonas Weirauch, IU, submission 24.12.2026). A RAG pipeline on the
Vue.js documentation in which only the chunking strategy (C1/C2/C3) varies. Status 13.10.2026: corpus fixed (ADR 0019);
`snapshot.py`, `ingest.py`, `preprocess.py`, `chunking.py` implemented and tested, later steps are stubs (`docs/plan.md`).
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
- Every change goes through a branch and a pull request; never push to `main` directly. Each PR gets a Codex review
  (`@codex review` on GitHub, or the `codex-reviewer` agent in `.claude/agents/` as stand-in) and is merged only after
  Jonas approves.

## Code Review Rules

Both Codex's GitHub review and the `codex-reviewer` agent apply these rules; cite the one a finding rests on.

### Experiment validity
- Only the chunking strategy (C1/C2/C3) may differ between runs. Anything else that differs per strategy (corpus,
  prompt, model, `temperature`, `top_k`, questions, retrieval) breaks the experiment: P1 (ADR 0006, 0014).
- The ground truth (`questions.csv`, `ground_truth.csv`) is final before any evaluation; a change that lets results
  feed back into questions, answers or relevance judgements is P1 (ADR 0017).
- Chunks and sections share the token space of `src/tokens.py`, and a chunk's `text` is the exact slice of its
  document (ADR 0019, 0021). A change that breaks either invalidates the relevance rule: P1.
- Anything that feeds the evaluation is deterministic (fixed seeds, stable sort orders and IDs); nondeterminism there
  is P2.

### Configuration and formats
- A parameter hard-coded outside `src/config.py` (path, size, model, `top_k`, temperature) is P2.
- Data artefacts deviating from `docs/reference/data-formats.md`, or strategy keys/IDs not taken from
  `config.STRATEGY_IDS`, are P1: later steps and the thesis tables depend on them.

### Secrets and privacy
- `.env`, API keys and personal data (e-mail, matriculation number) are never committed, logged or printed; the repo
  is public. P1.

### Tests
- Tests never call the OpenAI API or the network (the snapshot tests use a local git repository); one that can is P1.

## Map

- `docs/README.md` — documentation index (single source of truth)
- `docs/how-to/`, `docs/reference/`, `docs/explanation/` — tasks, exact facts (formats, metrics, prompts), research design
- `docs/plan.md` — schedule (to 24.12.2026) and open decisions
- `docs/adr/` — decisions D1–D21
- `.serena/memories/` — agent working notes; `core` is the entry point, each memory links into `docs/`
- `.claude/agents/codex-reviewer.md` — stand-in for Codex's GitHub review (rubric + the Code Review Rules above)
