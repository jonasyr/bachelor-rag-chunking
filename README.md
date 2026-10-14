# bachelor-rag-chunking

**Einfluss von Chunking-Strategien auf die Retrieval- und Antwortqualität eines RAG-Systems für technische Projektdokumentation**

Bachelor's thesis — B.Sc. Informatik, IU Internationale Hochschule.  
Author: Jonas Weirauch · Supervisor: Prof. Klaus Quibeldey-Cirkel · Deadline: 24.12.2026

---

## Overview

Controlled comparison of three chunking strategies on the Vue.js documentation corpus.
Only the chunking strategy varies; all other pipeline components are held constant.

| Strategy | Description | Params |
|----------|-------------|--------|
| C1 | Fixed-size, no overlap | 500 tokens, overlap 0 |
| C2 | Fixed-size, with overlap (strong baseline) | 500 tokens, overlap 100 |
| C3 | Structure-based (Markdown H2/H3) | max 800 tokens per section |

---

## Setup

```bash
uv sync                  # installs all dependencies + dev group into .venv
cp .env.example .env
# Add your OPENAI_API_KEY to .env
source .venv/bin/activate
uv tool install pre-commit && pre-commit install   # ruff and checks before each commit
```

`snapshot.py`, `ingest.py`, `preprocess.py`, `chunking.py`, `embed.py` and `retrieve.py` are implemented and tested (`uv run pytest`); the later steps are still stubs. Tooling, CI and the link to the thesis repo:
[`docs/README.md`](docs/README.md).

## Pipeline (run in order)

```bash
# 1. Fetch the pinned Vue.js snapshot: guide, API reference, style guide (ADR 0025; docs/how-to/create-corpus-snapshot.md)
python src/snapshot.py

# 2. Ingest
python src/ingest.py

# 3. Preprocess
python src/preprocess.py

# 4. Chunk (C1-C3 and the size-matched control K1, ADR 0026)
python src/chunking.py

# 5. Embed + build Chroma indices
python src/embed.py

# 6. Retrieve (C1-C3; then the control K1)
python src/retrieve.py
python src/retrieve.py --control

# 7. Generate answers
python src/generate.py

# 8a. Retrieval evaluation
python src/evaluate_retrieval.py

# 8b. Answer evaluation — scaffold score sheet, fill manually, then summarise
python src/evaluate_answers.py --mode scaffold
# open data/evaluation/scores.csv, fill in rubric scores (0–2)
python src/evaluate_answers.py --mode summarise
```

## Minimal prototype (run this first)

```bash
python src/snapshot.py && python src/ingest.py && python src/preprocess.py && python src/chunking.py
python src/embed.py
python src/retrieve.py   # always all strategies (ADR 0024)
python src/generate.py --strategy C1
```

## Interactive demo

```bash
streamlit run app/streamlit_app.py
```

## Analysis

```bash
jupyter notebook notebooks/analysis.ipynb
```

---

## Repository structure

```
├── tests/            pytest suite (uv run pytest)
├── src/              Pipeline scripts (snapshot → ingest → preprocess → chunking → embed → retrieve → generate → evaluate)
├── data/raw/         Vue.js snapshot (not committed)
├── data/processed/   Intermediate artefacts — documents.jsonl, sections.jsonl, chunks_*.jsonl (not committed)
├── data/evaluation/  questions.csv, ground_truth.csv, scores.csv
├── docs/             Documentation index (docs/README.md), master reference, ADRs, methodology, prompts
├── notebooks/        Analysis and visualisation
├── app/              Streamlit demo
└── chroma_db/        Persistent vector store (not committed)
```

## Key constraints (never change without updating methodology)

- `temperature = 0` — all LLM calls
- `top_k = 5` — retrieval, constant across strategies
- All parameters live in `src/config.py`
- Ground truth must be finalised **before** running evaluation
- Every intermediate artefact is saved to disk

Details and reasons: [`docs/README.md`](docs/README.md) (master reference, decisions in `docs/adr/`).

## License

- Code and documentation of this repository: [MIT](LICENSE), © 2026 Jonas Weirauch.
- `.claude/agents/codex-reviewer.md` contains the review rubric of [openai/codex](https://github.com/openai/codex)
  under the Apache License 2.0 ([copy](LICENSES/Apache-2.0.txt)); the file states its changes.
- Corpus: the [Vue.js documentation](https://github.com/vuejs/docs) © Yuxi (Evan) You and Vue documentation
  contributors, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It is downloaded at run time
  (`src/snapshot.py`, commit in `src/config.py`) and not redistributed here; derived artefacts such as
  `docs/corpus_manifest.csv` refer to it. It is modified before use; the cleaning steps are listed in
  [`docs/reference/corpus.md`](docs/reference/corpus.md) (decisions: ADR 0019, ADR 0020).
