# Research Context

## Research Question
*Wie beeinflussen unterschiedliche Chunking-Strategien die Retrieval- und Antwortqualität eines Retrieval-Augmented-Generation-Systems bei der Beantwortung projektspezifischer Fragen auf Basis technischer Open-Source-Dokumentation?*

## Sub-questions
1. Which chunking strategies suit technical project documentation in a RAG context?
2. How do strategies differ in retrieval quality (Recall@k, Precision@k, MRR)?
3. How do they affect answer quality (correctness, completeness, groundedness, hallucination-freedom)?
4. What trade-offs exist (chunk size, context coverage, redundancy, retrieval precision, cost, answer quality)?
5. What practical recommendations follow for RAG systems on technical docs?

## Hypotheses (binding, exploratory — H1–H3, D9)
- **H1 — Strong Baseline:** Structure-based chunking (C3) outperforms fixed-size without overlap (C1) in retrieval quality, but does **not** consistently outperform fixed-size with overlap (C2), because overlap largely compensates boundary information loss.
- **H2 — Retrieval–Answer Decoupling:** Retrieval quality differences transfer only **partially** to answer quality, because the LLM can compensate for moderate retrieval deficits.
- **H3 — Question-Type Interaction:** The relative suitability of strategies **varies by question type**; structure-based favours conceptual, cross-section questions while fixed-size suffices for narrowly scoped factual questions.

Hypotheses are evaluated descriptively, **not** via inferential statistics (exploratory, not confirmatory).

## Research Gap (three pillars)
1. **Different corpus:** Vue.js vs. already-informally-used FastAPI/Supabase/Stripe.
2. **Different domain:** developer-oriented frontend framework docs; existing controlled chunking comparisons are mostly in unrelated domains (enterprise/oil-and-gas: Taiwo & Yusoff 2026; clinical decision support: Gomez-Cabello et al. 2025).
3. **Stricter methodology:** manual reference-based primary evaluation; question-type differentiation; reproducibility via snapshot.

## Literature (15 verified sources, all in `literatur.bib`)
| BibTeX key | Role |
|-----------|------|
| `lewis2020rag` | RAG foundation paper |
| `gao2023ragsurvey` | RAG survey, pipeline components |
| `yu2025ragevalsurvey` | Component-level RAG evaluation |
| `es2024ragas` | RAGAS — automated secondary evaluation |
| `karpukhin2020dpr` | Dense Retrieval (DPR) |
| `manning2008ir` | IR metrics: Precision, Recall, MRR |
| `reimers2019sbert` | Sentence embeddings / semantic similarity |
| `devlin2019bert` | Transformer contextual representations |
| `hladena2025chunksize` | Chunk size effect on RAG performance |
| `jimenoyepes2024chunking` | Structure/element-based chunking |
| `finardi2024chronicles` | Retriever + chunk + generator as joint factors |
| `ji2023hallucination` | Hallucination in NLG (definition anchor) |
| `taiwo2026chunking` | Chunking in oil & gas docs — domain gap evidence |
| `gomezcabello2025chunking` | Chunking in clinical docs — domain gap evidence |
| `qu2025semanticchunking` | Semantic/structural ≠ consistently better → justifies C2 as strong baseline |

## Non-citable but relevant
Practitioner blog post (May 2026) with nearly identical setup (FastAPI/Supabase/Stripe, frozen QA set, single variable, RAGAS, heading-based chunking). **Not a citable scientific source.** Should appear briefly in "Verwandte Arbeiten" to show awareness and sharpen the distinction (peer-review methodology, different corpus, German academic thesis).

## Hallucination definition
An answer contains a hallucination when it includes information neither supported by the retrieved context passages nor by the reference answer, or when it contradicts them (Ji et al. 2023).

## Question catalogue
~40 questions (min 30, optimum 40–50, max 60). Five types:
| Type | Count | Example |
|------|------:|---------|
| Factual | 10 | Which lifecycle hooks are available in the Composition API? |
| Procedural | 10 | How do you define props in a component using `<script setup>`? |
| Conceptual | 10 | What is a composable in Vue and what problem does it solve? |
| Comparative | 5 | What is the difference between the Options API and the Composition API? |
| Edge/Error | 5 | What happens if a child component mutates a prop directly? |

Ground truth fields per question: `question_id`, `question`, `question_type`, `expected_answer`, `relevant_doc_ids`, `relevant_section_ids`, `difficulty`, `notes`.

**Ground truth must be finalized BEFORE running any evaluation.** Never adjust retroactively.
