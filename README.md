# bachelor-rag-chunking

**Einfluss von Chunking-Strategien auf die Retrieval- und Antwortqualität eines RAG-Systems für technische Projektdokumentation**

Bachelor's thesis — B.Sc. Informatik, IU Internationale Hochschule.  
Author: Jonas Weirauch · Supervisor: Prof. Klaus Quibeldey-Cirkel · Deadline: 24.12.2026

Status: [`docs/plan.md`](docs/plan.md#stand). Documentation index: [`docs/README.md`](docs/README.md).

## Overview

Controlled comparison of chunking strategies in a RAG pipeline on the Vue.js documentation. Only the chunking strategy
varies; every other component is held constant ([ADR 0006](docs/adr/0006-nur-chunking-variiert.md)).

| Strategy | Description |
|----------|-------------|
| C1 | Fixed-size windows, no overlap |
| C2 | Fixed-size windows with overlap (strong baseline) |
| C3 | Structure-based: sections between H1–H3 headings, 50–800 tokens per chunk |

Decisions: [ADR 0005](docs/adr/0005-drei-chunking-strategien.md), [ADR 0021](docs/adr/0021-c3-grenzen.md); parameter
values: [`docs/reference/configuration.md`](docs/reference/configuration.md) (set only in `src/config.py`). K1 is a
size-matched control for C3, used in retrieval only ([ADR 0026](docs/adr/0026-c3-vergleichbarkeit.md)).

## Install

```bash
uv sync                  # dependencies + dev group into .venv
cp .env.example .env     # then add your OPENAI_API_KEY
```

Full setup (pre-commit, check): [`docs/how-to/set-up.md`](docs/how-to/set-up.md).

## Pipeline (run in order)

Run from the repository root; options of every script: [`docs/reference/tooling.md`](docs/reference/tooling.md).
Procedure and checks before an evaluation run: [`docs/how-to/run-the-experiment.md`](docs/how-to/run-the-experiment.md).

```bash
uv run python src/snapshot.py      # 1. fetch the pinned Vue.js snapshot (docs/how-to/create-corpus-snapshot.md)
uv run python src/ingest.py        # 2. ingest
uv run python src/preprocess.py    # 3. clean, extract sections
uv run python src/chunking.py      # 4. chunk C1–C3 and the control K1
uv run python src/embed.py         # 5. embed, build Chroma indices
uv run python src/retrieve.py      # 6. retrieve (all strategies), then the control:
uv run python src/retrieve.py --control
uv run python src/generate.py      # 7. generate answers C1–C3 once (needs OPENAI_API_KEY)
uv run python src/evaluate_retrieval.py                          # 8a. retrieval metrics, then the control:
uv run python src/evaluate_retrieval.py --control
uv run python src/evaluate_answers.py --mode scaffold            # 8b. blind scoring: read the packet, fill the sheet
uv run python src/evaluate_answers.py --mode summarise
```

Analysis notebook (skeleton, runs after the pipeline): `notebooks/analysis.ipynb`. The Streamlit demo
(`app/streamlit_app.py`) is a placeholder and not implemented.

Repository layout: [`docs/reference/tooling.md`](docs/reference/tooling.md).

## License

- Code and documentation of this repository: [MIT](LICENSE), © 2026 Jonas Weirauch.
- `.claude/agents/codex-reviewer.md` contains the review rubric of [openai/codex](https://github.com/openai/codex)
  under the Apache License 2.0 ([copy](LICENSES/Apache-2.0.txt)); the file states its changes.
- Corpus: the [Vue.js documentation](https://github.com/vuejs/docs) © Yuxi (Evan) You and Vue documentation
  contributors, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It is downloaded at run time
  (`src/snapshot.py`, commit in `src/config.py`) and not redistributed here; derived artefacts such as
  `docs/corpus_manifest.csv` refer to it. It is modified before use; the cleaning steps are listed in
  [`docs/reference/corpus.md`](docs/reference/corpus.md) (decisions: ADR 0019, ADR 0020; scope: ADR 0025).
