# Conventions

Hard rules: `AGENTS.md` (Conventions); data formats: `docs/reference/data-formats.md` — never add CSV columns (`questions.csv` has `notes`).
- IDs: documents `D001`…, questions `Q001`… (48 questions, ADR 0029), chunks `{STRATEGY}_{DOC_ID}_{SEQ}`
  (`docs/reference/data-formats.md`).
- Scope guard (what is deliberately not part of the thesis): `docs/explanation/research-design.md`, section
  "Abgrenzung des Umfangs". Check it before proposing extra comparisons.
- Claude never writes a judgement (questions, reference answers, relevance, key points, closed-book verdicts, scores,
  R2's values): list and ADRs in `docs/explanation/research-design.md#warum-die-evaluation-so-angelegt-ist`.
- Thesis text, IU formatting and writing rules live in the private PaperLab repo (`IU_Source_of_Truth.md`,
  `./paperlab check`), not here.
