# bachelor-rag-chunking

**Einfluss von Chunking-Strategien auf die Retrieval- und Antwortqualität eines RAG-Systems für technische Projektdokumentation**

Bachelor's thesis — B.Sc. Informatik, IU Internationale Hochschule.  
Author: Jonas Weirauch · Supervisor: Prof. Klaus Quibeldey-Cirkel · Deadline: 31.12.2026

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
```

## Pipeline (run in order)

```bash
# 1. Fetch Vue.js snapshot (see docs/methodology.md §Snapshot)
#    Clone vuejs/docs, pin a commit, copy relevant src/guide/ folders to
#    data/raw/vue_docs_snapshot/

# 2. Ingest
python src/ingest.py

# 3. Preprocess
python src/preprocess.py

# 4. Chunk (all three strategies)
python src/chunking.py

# 5. Embed + build Chroma indices
python src/embed.py

# 6. Retrieve
python src/retrieve.py

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
python src/ingest.py && python src/preprocess.py && python src/chunking.py
python src/embed.py --strategy C1
python src/retrieve.py --strategy C1
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
├── src/              Pipeline scripts (ingest → preprocess → chunking → embed → retrieve → generate → evaluate)
├── data/raw/         Vue.js snapshot (not committed)
├── data/processed/   Intermediate artefacts — documents.jsonl, chunks_*.jsonl (not committed)
├── data/evaluation/  questions.csv, ground_truth.csv, scores.csv
├── docs/             Thesis documents, methodology notes, prompts, corpus manifest
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
