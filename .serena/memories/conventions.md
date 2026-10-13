# Conventions

Hard rules: `AGENTS.md` (Conventions); data formats: `docs/reference/data-formats.md` — never add CSV columns (`questions.csv` has `notes`).
- IDs: documents `D001`…, questions `Q001`–`Q040`, chunks `{STRATEGY}_{DOC_ID}_{SEQ}` (e.g. `C1_D001_0001`).
- Scope guard (`docs/explanation/research-design.md`): no LLM/embedding comparison, no RAG-vs-no-RAG, no fine-tuning, no local LLMs, no
  private data, no multimodal docs.
- Thesis text, IU formatting and writing rules live in the private PaperLab repo (`IU_Source_of_Truth.md`,
  `./paperlab check`), not here.
