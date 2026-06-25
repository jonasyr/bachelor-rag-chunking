# Decision Log (D1–D18) — All Binding

Source: `docs/Ground_Truth_Projektleitfaden.md` §2.

| # | Decision | Notes |
|---|----------|-------|
| D1 | **Corpus: Vue.js** (`vuejs/docs`, Markdown, `src/` directory) | Replaces FastAPI — abgrenzung from practitioner blog with FastAPI/Supabase/Stripe |
| D2 | **Citation: biblatex + biber, APA 7, `\parencite{}`** | — |
| D3 | **No industry partner** (no Peano or similar) | — |
| D4 | **Work period: July–December 2026**, submission 15.12.2026 (finalization) / 31.12.2026 (official deadline) | — |
| D5 | **Three strategies: C1** (fixed, no overlap), **C2** (fixed, overlap 100), **C3** (structure-based H2/H3). C4 semantic = optional only | — |
| D6 | **Only chunking varies** — all other pipeline components constant | Core experimental design invariant |
| D7 | **Triangulation: manual primary, RAGAS secondary**, agreement = validity indicator | RAGAS role upgraded from "optional" to binding secondary |
| D8 | **Cost/efficiency as explicit dependent variable** (chunk count, index size, token usage) | Added; not in original baseline |
| D9 | **Hypotheses H1–H3 (exploratory, descriptive)** — see `mem:research` | Replaces original baseline H1–H3 |
| D10 | **C2 (fixed + overlap) = strong baseline**, not a strawman (backed by Qu et al. 2025) | Protects against "trivial comparison" objection |
| D11 | **Research gap = developer-oriented Open-Source software docs** — existing comparisons are in unrelated domains | Documented gap, justifies contribution |
| D12 | **Retrieval metrics: Recall@k, Precision@k, MRR** (+Hit@k as simplified variant) | — |
| D13 | **Answer rubric: 0–2 scale, 5 criteria, equal weight** | — |
| D14 | **temperature = 0, top-k = 5** (constants) | Must never be varied; would introduce second IV |
| D15 | **Tech stack: Python, OpenAI API, Chroma, tiktoken, Pandas, Matplotlib/Plotly, Streamlit, optional RAGAS** | See `mem:tech_stack` |
| D16 | **Model neutrality**: exact GPT model + SDK version fixed at implementation time, documented in methodology, held constant | Never refer to model names in writing without version record |
| D17 | **Question catalogue: ~40 questions**, reference answers + annotated sources as ground truth | Must be finalized before evaluation |
| D18 | **Literature: 15 verified sources** in `literatur.bib` | See full table in `mem:research` |

## What is explicitly OUT OF SCOPE (unchanged from baseline)
LLM/embedding model comparison; RAG vs. no-RAG as primary question; fine-tuning; local LLMs; purely automated evaluation; private corporate data; multimodal/PDF documents with diagrams; C4 unless ahead of schedule.

## Corpus change rationale (D1)
FastAPI was replaced by Vue.js because a practitioner blog (May 2026) had already implemented a near-identical experimental setup on FastAPI/Supabase/Stripe (same single-variable design, frozen QA set, RAGAS, heading-based chunking). Vue.js provides clear domain and corpus differentiation while retaining question-type diversity.

## Timeline summary
| Period | Phase |
|--------|-------|
| 01–31.07 | Prep + literature |
| 01–31.08 | Corpus/snapshot + question catalogue |
| 07–28.09 | Implementation |
| 28.09–26.10 | Evaluation + analysis |
| 26.10–23.11 | Writing |
| 23.11–14.12 | Revision + proofreading |
| 15.12 | Submission |
