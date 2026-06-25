# Suggested Commands

## Project is pre-implementation (June 2026)
No `src/` or scripts exist yet. Commands below reflect the planned structure from `docs/Ground_Truth_Projektleitfaden.md`.

## Environment setup (planned)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in OPENAI_API_KEY
```

## Pipeline entry points (planned, under `src/`)
```bash
python src/ingest.py          # load Vue.js snapshot → documents.jsonl
python src/preprocess.py      # clean Markdown
python src/chunking.py        # produce chunks_c1/c2/c3.jsonl
python src/embed.py           # embed chunks → Chroma indices
python src/retrieve.py        # run retrieval for question set
python src/generate.py        # generate answers via LLM
python src/evaluate_retrieval.py   # compute Recall@k, Precision@k, MRR
python src/evaluate_answers.py     # apply rubric scoring
```

## Minimal prototype sequence (do this first)
Load one Markdown file → produce C1/C2/C3 chunks → embed → build Chroma index → query one question → show Top-5 → generate answer. Only scale to full pipeline once prototype works.

## Analysis
```bash
jupyter notebook notebooks/analysis.ipynb
```

## Streamlit demo
```bash
streamlit run app/streamlit_app.py
```

## Corpus snapshot (Vue.js)
```bash
git clone https://github.com/vuejs/docs.git
# check out a specific commit, copy src/guide/essentials/, src/guide/components/,
# src/guide/reusability/, src/guide/best-practices/ into data/raw/vue_docs_snapshot/
# document commit hash in corpus_manifest.csv
```

## Git
```bash
rtk git status
rtk git log
rtk git diff
```
