# Methodology Notes

Working notes for the methodology chapter of the thesis.
Decisions are binding only when recorded in `Ground_Truth_Projektleitfaden.md`.

---

## Snapshot

- **Repository:** `vuejs/docs` (https://github.com/vuejs/docs)
- **Commit:** _to be filled in_
- **Snapshot date:** _to be filled in_
- **Paths used:** see `corpus_manifest.csv`
- **Total files:** _to be filled in_
- **Total tokens:** _to be filled in_

---

## Model versions (fill in at implementation time)

| Component | Version | First-use date |
|-----------|---------|---------------|
| LLM | | |
| Embedding model | | |
| OpenAI Python SDK | | |
| ChromaDB | | |
| tiktoken | | |

---

## Reproducibility checklist

- [ ] Snapshot commit hash documented above and in `corpus_manifest.csv`
- [ ] Exact model versions recorded above
- [ ] `ground_truth.csv` finalised before any evaluation run
- [ ] All intermediate artefacts saved (`documents.jsonl`, `chunks_*.jsonl`, `retrieved_results.csv`, `generated_answers.csv`)
- [ ] Prompts unchanged across all strategy runs (see `prompts.md`)
- [ ] temperature = 0 verified in `config.py`
