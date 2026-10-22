# bachelor-rag-chunking

**Einfluss von Chunking-Strategien auf die Retrieval- und Antwortqualität eines RAG-Systems für technische Projektdokumentation**

Bachelor's thesis — B.Sc. Informatik, IU Internationale Hochschule.  
Author: Jonas Weirauch · Supervisor: Prof. Klaus Quibeldey-Cirkel · Deadline: 24.12.2026

Status: [`docs/plan.md`](docs/plan.md#stand). Documentation index: [`docs/README.md`](docs/README.md).

## Overview

Controlled comparison of chunking strategies in a RAG pipeline on the documentation of the e2e testing
framework ([ADR 0038](docs/adr/0038-korpus-e2e.md)). Only the chunking strategy
varies; every other component is held constant ([ADR 0006](docs/adr/0006-nur-chunking-variiert.md)).

| Strategy | Description |
|----------|-------------|
| C1 | Fixed-size windows, no overlap |
| C2 | Fixed-size windows with overlap (strong baseline) |
| C3 | Structure-based: sections between H1–H3 headings, with a size floor and ceiling |

Decisions: [ADR 0005](docs/adr/0005-drei-chunking-strategien.md), [ADR 0021](docs/adr/0021-c3-grenzen.md); parameter
values: [`docs/reference/configuration.md`](docs/reference/configuration.md) (set only in `src/config.py`). K1 is a
size-matched control for C3, used in retrieval only ([ADR 0026](docs/adr/0026-c3-vergleichbarkeit.md)); K0 answers the
same questions without retrieval ([ADR 0041](docs/adr/0041-kontrolle-k0.md)).

## Install

```bash
uv sync                  # dependencies + dev group into .venv
cp .env.example .env     # then add your OPENAI_API_KEY
```

Full setup (pre-commit, check): [`docs/how-to/set-up.md`](docs/how-to/set-up.md).

## How it runs

Scripts run from the repository root (`uv run python src/<step>.py`). The order of the steps, their checks and commit
points live in [`docs/how-to/run-the-experiment.md`](docs/how-to/run-the-experiment.md); the options of every script
in [`docs/reference/tooling.md`](docs/reference/tooling.md).

1. Corpus: snapshot of the e2e docs, conversion to sections ([how-to](docs/how-to/create-corpus-snapshot.md)).
2. Chunks and index: C1–C3 and the control K1, embeddings ([how-to](docs/how-to/run-the-experiment.md)).
3. Question catalogue: written by hand in the app, closed-book screen, frozen
   ([how-to](docs/how-to/build-the-question-catalogue.md)).
4. Runs: retrieval for C1–C3 and K1, answers for C1–C3 and K0 ([how-to](docs/how-to/run-the-experiment.md)).
5. Scoring: blind rule-based scoring, second rating, RAGAS
   ([how-to](docs/how-to/run-the-experiment.md), method: [`docs/reference/evaluation.md`](docs/reference/evaluation.md)).
6. Analysis for the thesis: tables and figures in `output/` ([how-to](docs/how-to/deliver-results-to-thesis.md)).

Repository layout: [`docs/reference/tooling.md`](docs/reference/tooling.md#repository-struktur).

## License

### This repository

Code and documentation: [MIT](LICENSE), © 2026 Jonas Weirauch.

### Third-party content in this repository

- `.claude/agents/codex-reviewer.md` contains the review rubric of [openai/codex](https://github.com/openai/codex)
  under the Apache License 2.0 ([copy](LICENSES/Apache-2.0.txt)); the file states its changes.
- e2e documentation (see below): derived artefacts such as `docs/corpus_manifest.csv` refer to it, and the pilot sets
  `data/pilot/e2e/` and `data/pilot/e2e_jonas/` quote short excerpts, under its licence.
- `data/corpus_probe/` quotes single sentences of the 24 candidate documentations of the corpus selection, each under
  its own licence (list: [`docs/reference/corpus-selection.md`](docs/reference/corpus-selection.md#lizenzen)).
- Until 18.10.2026 the corpus was the [Vue.js documentation](https://github.com/vuejs/docs) © Yuxi (Evan) You and Vue
  documentation contributors, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); excerpts of it remain in the
  historical pilot sets `data/pilot/`, `data/pilot/hard/` and `data/pilot/hard_posthoc/`.

### Corpus (not redistributed)

The [e2e documentation](https://github.com/tester-army/e2e/tree/main/docs) © 2026 TesterArmy, Inc., licensed under the
Apache License 2.0 ([copy](LICENSES/Apache-2.0.txt)). Its NOTICE reads: "This product includes software developed at
TesterArmy, Inc. (https://tester.army)." It is downloaded at run time (`src/snapshot.py`, commit in `src/config.py`)
and not redistributed here. It is modified before use; the conversion rules are listed in
[`docs/reference/corpus.md`](docs/reference/corpus.md) (decisions: ADR 0019, ADR 0038).
