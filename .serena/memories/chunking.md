# Chunking Strategies

Three strategies are binding (D5). C4 is optional only.

| ID | Strategy | Parameters | Strength | Weakness |
|----|----------|-----------|---------|---------|
| **C1** | Fixed-size, no overlap | 500 tokens, overlap 0 | Simple, reproducible, baseline | Context break at boundaries |
| **C2** | Fixed-size, with overlap | 500 tokens, overlap 100 tokens | Better coverage; **strong baseline** (not a strawman) | More chunks, more redundancy, higher cost |
| **C3** | Structure-based (Markdown headings) | Split at H2/H3 boundaries; max 800 tokens per chunk; subdivide large sections by paragraph | Preserves semantic units | Variable chunk sizes; some Vue.js sections (e.g. "Reactivity Fundamentals") are very long — requires careful max-size handling |
| C4 | Semantic (optional) | Split by semantic similarity | Theoretically appealing | Extra model dependency, high compute cost; only implement if phases 1–4 complete early |

## Key invariant
**Only the chunking strategy is the independent variable.** Corpus/snapshot, language (English), embedding model, LLM, temperature (0), top-k (5), prompt, question set, rubric, vector store type, retrieval method (Dense/vector) — all constant.

## Why C2 is not a trivial baseline
Qu, Bao & Tu (2025) show that semantic/structure-based chunking does **not consistently outperform** fixed-size chunking with overlap, and the added complexity is often unjustified. The research value is not "who wins" but: effect size, cost trade-off, metric dependence, retrieval–answer decoupling (H2), and question-type interaction (H3).

## C3 note for Vue.js
Some sections (e.g. "Reactivity Fundamentals") are long and will produce oversized chunks. The paragraph-level subdivision rule and the 800-token cap must be implemented carefully and documented in the methodology chapter. Both the floor and ceiling parameters must be stated and justified.

## Strategy IDs in code and data
Use `"fixed_500_no_overlap"`, `"fixed_500_overlap_100"`, `"structure_h2h3"` as the `strategy` field values in all JSONL/CSV outputs (or agree on canonical names in `src/config.py` and use consistently).
