# Repository Setup & Scaffold — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Minimal, spec-compliant repository scaffold that establishes directory structure, central config, correctly-headed CSV templates, and empty-but-named source stubs — nothing more. No implementation.

**Architecture:** One central `src/config.py` holds all parameters. All other `src/` files are stubs (docstring + `raise NotImplementedError`). CSV files exist with correct headers per §10 of the Ground Truth. The corpus snapshot directory is empty and waits for the manual clone step documented in the README.

**Tech Stack:** Python 3.11+, OpenAI API, ChromaDB, tiktoken — versions pinned in `requirements.txt`.

## Global Constraints

Per `docs/Ground_Truth_Projektleitfaden.md` (verbindlich):
- `temperature = 0`, `top_k = 5` — constants, never vary
- Only `src/config.py` holds numeric parameters and paths
- Chunking strategies: C1 (500t, overlap 0), C2 (500t, overlap 100), C3 (H2/H3, max 800t)
- CSV schemas exact as §10 — no extra columns in the data files
- Language: corpus + questions + reference answers = English; thesis text = German

---

## Audit: What Exists vs. What Is Needed

| File / Dir | Current state | Target state |
|------------|--------------|--------------|
| `src/config.py` | ✅ Complete, correct | Keep as-is |
| `src/ingest.py` | ⚠️ Full implementation | Stub only |
| `src/preprocess.py` | ⚠️ Full implementation | Stub only |
| `src/chunking.py` | ⚠️ Full implementation | Stub only |
| `src/embed.py` | ⚠️ Full implementation | Stub only |
| `src/retrieve.py` | ⚠️ Full implementation | Stub only |
| `src/generate.py` | ⚠️ Full implementation | Stub only |
| `src/evaluate_retrieval.py` | ⚠️ Full implementation | Stub only |
| `src/evaluate_answers.py` | ⚠️ Full implementation | Stub only |
| `app/streamlit_app.py` | ⚠️ Full Streamlit app | Placeholder |
| `notebooks/analysis.ipynb` | ⚠️ Full notebook | Placeholder |
| `data/evaluation/questions.csv` | ❌ Wrong column name (`question_type` → should be `type` per §10); has sample data | Headers only, correct schema |
| `data/evaluation/ground_truth.csv` | ✅ Correct headers; has sample data | Headers only |
| `docs/corpus_manifest.csv` | ✅ Correct headers; has sample rows | Headers only |
| `.gitignore` | ✅ Correct | Keep |
| `.env.example` | ✅ Correct | Keep |
| `requirements.txt` | ✅ Correct | Keep |
| `README.md` | ✅ Correct | Keep |
| `docs/prompts.md` | ✅ Correct | Keep |
| `docs/methodology.md` | ✅ Correct | Keep |

---

## Task 1: Fix CSV templates (exact §10 schemas, headers only)

**Files:**
- Overwrite: `data/evaluation/questions.csv`
- Overwrite: `data/evaluation/ground_truth.csv`
- Overwrite: `docs/corpus_manifest.csv`

**Spec §10 schemas (verbatim):**
```
questions.csv:        question_id, question, type, difficulty
ground_truth.csv:     question_id, expected_answer, relevant_doc_ids, relevant_section_ids
retrieved_results.csv (generated later): question_id, strategy, rank, chunk_id, score, is_relevant
generated_answers.csv (generated later): question_id, strategy, answer, sources, prompt_tokens, completion_tokens
scores.csv (generated later):            question_id, strategy, correctness, completeness, groundedness, no_hallucination, clarity, total_score
corpus_manifest.csv:  file_id, path, title, section, tokens, included
```

- [ ] **Step 1: Overwrite `data/evaluation/questions.csv` with headers only**
```
question_id,question,type,difficulty
```

- [ ] **Step 2: Overwrite `data/evaluation/ground_truth.csv` with headers only**
```
question_id,expected_answer,relevant_doc_ids,relevant_section_ids
```

- [ ] **Step 3: Overwrite `docs/corpus_manifest.csv` with headers only**
```
file_id,path,title,section,tokens,included
```

- [ ] **Step 4: Verify**
```bash
head -1 data/evaluation/questions.csv
# → question_id,question,type,difficulty
head -1 data/evaluation/ground_truth.csv
# → question_id,expected_answer,relevant_doc_ids,relevant_section_ids
```

- [ ] **Step 5: Commit**
```bash
git add data/evaluation/questions.csv data/evaluation/ground_truth.csv docs/corpus_manifest.csv
git commit -m "chore: fix CSV schemas to match Ground Truth §10 exactly (headers only)"
```

---

## Task 2: Replace src/ pipeline scripts with stubs

**Files:** All of `src/ingest.py`, `src/preprocess.py`, `src/chunking.py`, `src/embed.py`, `src/retrieve.py`, `src/generate.py`, `src/evaluate_retrieval.py`, `src/evaluate_answers.py`

**Rule:** Each stub contains only: module docstring, imports from `config`, and function signatures with `raise NotImplementedError`. No logic.

- [ ] **Step 1: Overwrite `src/ingest.py`**
```python
"""Ingest Vue.js snapshot.

Reads .md files from data/raw/vue_docs_snapshot/,
writes data/processed/documents.jsonl.

Schema: {"doc_id", "path", "title", "text", "tokens"}
"""
from pathlib import Path
from config import DATA_RAW, DOCUMENTS_FILE


def ingest(snapshot_dir: Path = DATA_RAW, out_file: Path = DOCUMENTS_FILE) -> None:
    """Load all .md files, count tokens, write documents.jsonl."""
    raise NotImplementedError


if __name__ == "__main__":
    ingest()
```

- [ ] **Step 2: Overwrite `src/preprocess.py`**
```python
"""Preprocess / clean Markdown.

Reads documents.jsonl, strips frontmatter and VitePress directives,
normalises whitespace. Writes cleaned records back in-place.
"""
from pathlib import Path
from config import DOCUMENTS_FILE


def preprocess(doc_file: Path = DOCUMENTS_FILE) -> None:
    """Clean text field of every record in documents.jsonl in-place."""
    raise NotImplementedError


if __name__ == "__main__":
    preprocess()
```

- [ ] **Step 3: Overwrite `src/chunking.py`**
```python
"""Chunking strategies C1, C2, C3.

Reads documents.jsonl, writes chunks_c1/c2/c3.jsonl.

C1: fixed-size 500 tokens, overlap 0          (config.C1_CHUNK_SIZE / C1_OVERLAP)
C2: fixed-size 500 tokens, overlap 100        (config.C2_CHUNK_SIZE / C2_OVERLAP)
C3: structure-based H2/H3, max 800 tokens     (config.C3_MAX_TOKENS)

Chunk schema: {"chunk_id", "doc_id", "strategy", "text", "start_token", "end_token"}
"""
from pathlib import Path
from config import CHUNK_FILES, DOCUMENTS_FILE


def chunk(strategy_key: str, docs_file: Path = DOCUMENTS_FILE) -> None:
    """Produce chunks for one strategy key ('C1', 'C2', or 'C3')."""
    raise NotImplementedError


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--strategy", choices=["C1", "C2", "C3", "all"], default="all")
    args = p.parse_args()
    keys = ["C1", "C2", "C3"] if args.strategy == "all" else [args.strategy]
    for k in keys:
        chunk(k)
```

- [ ] **Step 4: Overwrite `src/embed.py`**
```python
"""Embed chunks and build Chroma vector indices.

One persistent collection per strategy (config.CHROMA_COLLECTIONS).
Uses OpenAI Embeddings API (config.EMBEDDING_MODEL).
"""
from config import CHROMA_COLLECTIONS


def embed_and_store(strategy_key: str) -> None:
    """Embed all chunks for strategy_key and upsert into Chroma."""
    raise NotImplementedError


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--strategy", choices=["C1", "C2", "C3", "all"], default="all")
    args = p.parse_args()
    keys = ["C1", "C2", "C3"] if args.strategy == "all" else [args.strategy]
    for k in keys:
        embed_and_store(k)
```

- [ ] **Step 5: Overwrite `src/retrieve.py`**
```python
"""Retrieval.

For every question in questions.csv × every strategy,
retrieve top-k chunks and write retrieved_results.csv.

Output schema (§10): question_id, strategy, rank, chunk_id, score, is_relevant
"""
from config import RETRIEVED_RESULTS_FILE, TOP_K


def retrieve(strategy_keys: list[str]) -> None:
    """Query Chroma for each question, write retrieved_results.csv."""
    raise NotImplementedError


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--strategy", choices=["C1", "C2", "C3", "all"], default="all")
    args = p.parse_args()
    keys = ["C1", "C2", "C3"] if args.strategy == "all" else [args.strategy]
    retrieve(keys)
```

- [ ] **Step 6: Overwrite `src/generate.py`**
```python
"""Answer generation.

Assembles prompt from top-k chunks (see docs/prompts.md),
calls LLM (config.LLM_MODEL, temperature=0), writes generated_answers.csv.

Output schema (§10): question_id, strategy, answer, sources, prompt_tokens, completion_tokens
"""
from config import GENERATED_ANSWERS_FILE, LLM_MODEL, LLM_TEMPERATURE


def generate_answers(strategy_keys: list[str]) -> None:
    """Generate LLM answers for each question × strategy, write generated_answers.csv."""
    raise NotImplementedError


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--strategy", choices=["C1", "C2", "C3", "all"], default="all")
    args = p.parse_args()
    keys = ["C1", "C2", "C3"] if args.strategy == "all" else [args.strategy]
    generate_answers(keys)
```

- [ ] **Step 7: Overwrite `src/evaluate_retrieval.py`**
```python
"""Retrieval evaluation.

Computes Recall@k, Precision@k, Hit@k, MRR per strategy and question type.
Reads retrieved_results.csv + ground_truth.csv.
"""
from config import RETRIEVED_RESULTS_FILE, GROUND_TRUTH_FILE, TOP_K


def evaluate(k: int = TOP_K) -> None:
    """Print retrieval metric summary per strategy (+ breakdown by question type)."""
    raise NotImplementedError


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--k", type=int, default=TOP_K)
    args = p.parse_args()
    evaluate(args.k)
```

- [ ] **Step 8: Overwrite `src/evaluate_answers.py`**
```python
"""Answer quality evaluation (manual rubric 0–2, 5 criteria).

--mode scaffold  Write scores.csv with unscored rows for manual annotation.
--mode summarise Read completed scores.csv and print summary statistics.

Rubric criteria: correctness, completeness, groundedness, no_hallucination, clarity
Output schema (§10): question_id, strategy, correctness, completeness, groundedness,
                      no_hallucination, clarity, total_score
"""
from config import GENERATED_ANSWERS_FILE, SCORES_FILE, RUBRIC_CRITERIA


def scaffold() -> None:
    """Write scores.csv with -1 placeholders for manual scoring."""
    raise NotImplementedError


def summarise() -> None:
    """Read filled scores.csv and print per-strategy and per-type summary."""
    raise NotImplementedError


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["scaffold", "summarise"], required=True)
    args = p.parse_args()
    {"scaffold": scaffold, "summarise": summarise}[args.mode]()
```

- [ ] **Step 9: Verify — all stubs importable, none runnable**
```bash
python -c "
import sys; sys.path.insert(0,'src')
import ingest, preprocess, chunking, embed, retrieve, generate
import evaluate_retrieval, evaluate_answers
print('All stubs import OK')
"
```
Expected: `All stubs import OK`

- [ ] **Step 10: Commit**
```bash
git add src/
git commit -m "chore: replace implementation files with interface stubs"
```

---

## Task 3: Simplify notebook and Streamlit app to minimal placeholders

**Files:**
- Overwrite: `notebooks/analysis.ipynb`
- Overwrite: `app/streamlit_app.py`

- [ ] **Step 1: Overwrite `app/streamlit_app.py`**
```python
"""Interactive RAG demo — Streamlit dashboard.

Placeholder. Implement after src/retrieve.py and src/generate.py are complete.

Usage:
    streamlit run app/streamlit_app.py
"""
import streamlit as st

st.title("RAG Chunking Strategy Comparison")
st.info("Dashboard not yet implemented. Run the pipeline scripts in src/ first.")
```

- [ ] **Step 2: Overwrite `notebooks/analysis.ipynb` with minimal kernel-only notebook**

Replace with a notebook that only sets up imports and documents what it will contain — no analysis code yet.

```json
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# RAG Chunking Analysis\n",
    "\n",
    "Visualisation and analysis of retrieval + answer evaluation results.\n",
    "Run after all pipeline steps (src/ingest → ... → src/evaluate_answers) are complete.\n",
    "\n",
    "Planned sections:\n",
    "1. Retrieval metrics (Recall@k, MRR, Precision@k) per strategy\n",
    "2. Answer quality (rubric 0–2) per strategy\n",
    "3. Retrieval–answer correlation (H2: decoupling)\n",
    "4. Question-type breakdown (H3: interaction)\n",
    "5. Efficiency / cost comparison"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import sys\n",
    "sys.path.insert(0, '../src')\n",
    "\n",
    "import pandas as pd\n",
    "import matplotlib.pyplot as plt\n",
    "import plotly.express as px\n",
    "\n",
    "from config import (\n",
    "    RETRIEVED_RESULTS_FILE, GENERATED_ANSWERS_FILE,\n",
    "    SCORES_FILE, QUESTIONS_FILE, TOP_K,\n",
    ")\n",
    "print('Imports OK — ready to analyse once pipeline is complete.')"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
  "language_info": {"name": "python", "version": "3.11.0"}
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
```

- [ ] **Step 3: Verify notebook renders**
```bash
jupyter nbconvert --to notebook --execute notebooks/analysis.ipynb --output /tmp/test_nb.ipynb 2>&1 | tail -5
```
Expected: no errors (imports will succeed; pipeline files won't exist yet but the cell just checks imports).

- [ ] **Step 4: Commit**
```bash
git add app/streamlit_app.py notebooks/analysis.ipynb
git commit -m "chore: reduce notebook and Streamlit app to minimal placeholders"
```

---

## Self-Review

### Spec coverage
| §Ground Truth requirement | Covered? |
|--------------------------|---------|
| §9 exact directory structure | ✅ created in initial setup, untouched |
| §10 CSV schemas | ✅ Task 1 |
| §8 tech stack in requirements.txt | ✅ kept from initial setup |
| §8 config.py as single param source | ✅ kept from initial setup |
| §6 C1/C2/C3 parameters in config | ✅ kept from initial setup |
| §14 D6: only chunking varies (stubs enforce no logic) | ✅ Task 2 |
| §15 pipeline order documented | ✅ README kept |
| Nothing implemented prematurely | ✅ Tasks 2–3 |

### Placeholder scan
No `TBD` or vague language — all stubs show exact function signatures, schemas reference §10 explicitly.

### What is deliberately NOT in this plan
- Any implementation logic (that belongs to the implementation phase, Phase 3 per §15)
- The corpus snapshot clone (manual step, documented in README and docs/methodology.md)
- The question catalogue (manual curation, Phase 2 per §15)
- Tests (appropriate once implementation begins)
