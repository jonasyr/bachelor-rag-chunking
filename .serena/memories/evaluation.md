# Evaluation Design

## Retrieval Metrics (primary level 1)
Computed per question per strategy, then averaged:
- **Recall@k** = |R_q ∩ T_{q,k}| / |R_q| — share of relevant sources found in top-k
- **Hit@k** = 1 if ≥1 relevant source in top-k, else 0 — simplified, easy to report
- **Precision@k** = |R_q ∩ T_{q,k}| / k — share of top-k that are relevant
- **MRR** = (1/|Q|) · Σ 1/rank_q — ranking quality, position of first relevant hit

k is fixed at **5** (top-k = 5, constant). Do not vary k.

## Answer Quality Rubric (primary level 2, 0–2 scale)
| Criterion | 0 | 1 | 2 |
|-----------|---|---|---|
| Korrektheit (Correctness) | wrong | partially correct | correct |
| Vollständigkeit (Completeness) | key points missing | partially complete | complete |
| Quellenbezug (Groundedness) | not supported | partially supported | clearly supported by sources |
| Halluzinationsfreiheit (No hallucination) | false/unsupported claims | minor unsupported additions | no hallucinations |
| Verständlichkeit (Clarity) | unclear | understandable with weaknesses | clear and precise |

**Total score:** Q = (K + V + G + H + L) / 5, range 0–2. Optional normalized: Q_norm = (Q/2)·100.  
All criteria equally weighted (no safety-critical domain, easier to defend than complex weights).

## Triangulation (binding, D7)
- **Primary:** manual reference-based evaluation (own ground truth, not circular, defensible).
- **Secondary:** RAGAS framework (Es et al. 2024) — Faithfulness + Context Relevance (scalable, reproducible).
- **Validity indicator:** agreement between manual and RAGAS is reported. Agreement → robustness; disagreement → finding about metric reliability.
- RAGAS is **never** the sole basis. LLM-as-a-judge has known reliability limits (Yu et al. 2025).

## Efficiency / Cost Metrics (D8)
Per strategy, record: chunk count, index size, prompt tokens, completion tokens.  
Report as: "X% better retrieval quality at Y× cost" — quality vs. cost comparison.

## Statistical Analysis
Descriptive statistics only (sufficient for exploratory thesis):
- Mean, median, standard deviation, boxplots per strategy.
- Breakdown by question type (tests H3).
- Correlation: retrieval score vs. answer score (tests H2 decoupling).
- Optional: Friedman test (multiple related groups), Wilcoxon signed-rank (pairwise) — only if statistically confident.

## Inter-rater Reliability (recommended)
10–20% of answers independently rated by a second person.  
Agreement measure: simple agreement = matching scores / total, or mean absolute deviation on 0–2 scale. Cohen's Kappa optional.

## Planned Visualizations
| Figure | Purpose |
|--------|---------|
| Bar chart Recall@5 per strategy | Retrieval comparison |
| Bar chart MRR per strategy | Ranking quality |
| Boxplot answer score per strategy | Answer quality distribution |
| Heatmap question × strategy | Where does each strategy work/fail? |
| Scatterplot retrieval score vs. answer score | H2: retrieval–answer decoupling |
| Bar chart question types | Catalogue composition |
| Chunk length histogram per strategy | Chunk size distribution differences |
| Cost/token comparison | Efficiency (D8) |

## Internal Validity
Secured by: constant parameters across conditions, same corpus/questions/prompts/models, temperature = 0.  
External validity limited to one corpus (Vue.js) — findings are indicative, not universal. This limitation must be stated explicitly in the thesis.
