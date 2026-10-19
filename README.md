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
| C3 | Structure-based: sections between H1–H3 headings, 50–800 tokens per chunk |

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

## Pipeline

Run each script from the repository root with `uv run python <script>`, in this order; the steps with their checks
are in [`docs/how-to/run-the-experiment.md`](docs/how-to/run-the-experiment.md), the options of every script in
[`docs/reference/tooling.md`](docs/reference/tooling.md).

1. Corpus: `src/snapshot.py` → `src/ingest.py` → `src/preprocess.py`
   ([`docs/how-to/create-corpus-snapshot.md`](docs/how-to/create-corpus-snapshot.md)).
2. Chunks and indices: `src/chunking.py` (C1–C3 and K1), `src/embed.py` (needs `OPENAI_API_KEY`).
3. Question catalogue: sampling plan, editor (`uv run streamlit run app/catalogue_editor.py`), closed-book screen
   (`src/catalogue.py screen`, needs `OPENAI_API_KEY`), `src/catalogue.py check` and `freeze`
   ([`docs/how-to/build-the-question-catalogue.md`](docs/how-to/build-the-question-catalogue.md)); retrieval,
   generation and evaluation refuse to run on a catalogue that is not frozen.
4. Retrieval: `src/retrieve.py` (C1–C3), then `src/retrieve.py --control` (K1); new query embeddings need
   `OPENAI_API_KEY`.
5. Answers: `src/generate.py` (C1–C3 and, in the same run, the control K0 without retrieval; needs `OPENAI_API_KEY`).
6. Evaluation: `src/evaluate_retrieval.py`, then with `--control` (K1); `src/evaluate_answers.py --mode scaffold`,
   rule-based scoring on the app page "Scoring", `--mode summarise`; after C1–C3 the control K0 the same way with
   `--mode scaffold --control` and `--mode summarise --control`.

Analysis notebook (skeleton, runs after the pipeline): `notebooks/analysis.ipynb`. The Streamlit demo
(`app/streamlit_app.py`) is a placeholder and not implemented.

Repository layout: [`docs/reference/tooling.md`](docs/reference/tooling.md).

## License

- Code and documentation of this repository: [MIT](LICENSE), © 2026 Jonas Weirauch.
- `.claude/agents/codex-reviewer.md` contains the review rubric of [openai/codex](https://github.com/openai/codex)
  under the Apache License 2.0 ([copy](LICENSES/Apache-2.0.txt)); the file states its changes.
- Corpus: the [e2e documentation](https://github.com/tester-army/e2e/tree/main/docs) © 2026 TesterArmy, Inc.,
  licensed under the Apache License 2.0 ([copy](LICENSES/Apache-2.0.txt)). Its NOTICE reads: "This product includes
  software developed at TesterArmy, Inc. (https://tester.army)." It is downloaded at run time (`src/snapshot.py`,
  commit in `src/config.py`) and not redistributed here; derived artefacts such as `docs/corpus_manifest.csv` refer to
  it, and `data/corpus_probe/` quotes short excerpts under the same licence. It is modified before
  use; the conversion rules are listed in [`docs/reference/corpus.md`](docs/reference/corpus.md) (decisions: ADR 0019,
  ADR 0038).
- Until 18.10.2026 the corpus was the [Vue.js documentation](https://github.com/vuejs/docs) © Yuxi (Evan) You and Vue
  documentation contributors, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); excerpts of it remain in
  `data/corpus_probe/` and in the historical pilot sets under `data/pilot/` (all from the Vue.js corpus).
