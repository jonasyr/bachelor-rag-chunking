# RAG Pipeline Architecture & Repository Layout

## Pipeline Flow
```
Vue.js docs snapshot (data/raw/vue_docs_snapshot/)
  → ingest.py        → documents.jsonl
  → preprocess.py    → cleaned Markdown
  → chunking.py      → chunks_c1.jsonl, chunks_c2.jsonl, chunks_c3.jsonl
  → embed.py         → Chroma vector store (one index per strategy, persistent)
  → retrieve.py      → retrieved_results.csv  (question × strategy × top-k)
  → generate.py      → generated_answers.csv
  → evaluate_retrieval.py → Recall@k, Precision@k, MRR per strategy
  → evaluate_answers.py   → scores.csv (rubric 0–2, 5 criteria)
  → notebooks/analysis.ipynb + app/streamlit_app.py
```

**Invariant:** All other components (corpus, embedding model, LLM, temperature, top-k, prompt, question set, rubric, vector store, retrieval method) are held constant. Only the chunking strategy varies.

## Planned Repository Layout
```
bachelor-rag-chunking/
├── README.md
├── pyproject.toml
├── uv.lock
├── .env.example
├── data/
│   ├── raw/vue_docs_snapshot/          ← Vue.js Markdown files
│   ├── processed/
│   │   ├── documents.jsonl
│   │   ├── chunks_c1.jsonl
│   │   ├── chunks_c2.jsonl
│   │   └── chunks_c3.jsonl
│   └── evaluation/
│       ├── questions.csv
│       ├── ground_truth.csv
│       ├── retrieved_results.csv
│       ├── generated_answers.csv
│       └── scores.csv
├── src/
│   ├── config.py                       ← ALL parameters live here
│   ├── ingest.py
│   ├── preprocess.py
│   ├── chunking.py
│   ├── embed.py
│   ├── retrieve.py
│   ├── generate.py
│   ├── evaluate_retrieval.py
│   └── evaluate_answers.py
├── notebooks/analysis.ipynb
├── app/streamlit_app.py
└── docs/
    ├── Ground_Truth_Projektleitfaden.md  ← master reference
    ├── Exposee.md / Exposee.pdf
    ├── methodology.md
    ├── prompts.md
    └── corpus_manifest.csv
```

## Data Schemas (exact — do not drift)

**documents.jsonl**
```json
{"doc_id":"D001","path":"guide/essentials/reactivity-fundamentals.md","title":"Reactivity Fundamentals","text":"...","tokens":1700}
```

**chunks_c1.jsonl** (same shape for c2/c3, strategy field differs)
```json
{"chunk_id":"C1_D001_0001","doc_id":"D001","strategy":"fixed_500_no_overlap","text":"...","start_token":0,"end_token":500}
```

**questions.csv**
```
question_id,question,type,difficulty
Q001,"What is the difference between ref and reactive in Vue?",conceptual,medium
```

**ground_truth.csv**
```
question_id,expected_answer,relevant_doc_ids,relevant_section_ids
Q001,"ref wraps any value...",D001,"D001#ref-vs-reactive"
```

**retrieved_results.csv**
```
question_id,strategy,rank,chunk_id,score,is_relevant
Q001,C1,1,C1_D001_0001,0.84,1
```

**generated_answers.csv**
```
question_id,strategy,answer,sources,prompt_tokens,completion_tokens
Q001,C1,"...",C1_D001_0001,1200,180
```

**scores.csv**
```
question_id,strategy,correctness,completeness,groundedness,no_hallucination,clarity,total_score
Q001,C1,2,2,2,2,2,2.0
```

## Corpus: Vue.js
- Repo: `vuejs/docs`, content under `src/`
- Snapshot: specific commit hash must be documented in `docs/corpus_manifest.csv`
- Relevant sections: `src/guide/essentials/`, `src/guide/components/`, `src/guide/reusability/`, `src/guide/best-practices/` (optionally parts of `src/api/`)
- Target: ~50–100 Markdown files
- Language: English

## corpus_manifest.csv schema
```
file_id,path,title,section,tokens,included
D001,guide/essentials/reactivity-fundamentals.md,Reactivity Fundamentals,Essentials,1700,yes
```
