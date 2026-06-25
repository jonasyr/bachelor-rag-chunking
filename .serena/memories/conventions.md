# Conventions

## Data file naming
- Chunk files: `chunks_c1.jsonl`, `chunks_c2.jsonl`, `chunks_c3.jsonl` — suffix = strategy ID.
- Strategy IDs: `C1` = fixed no overlap, `C2` = fixed with overlap, `C3` = structure-based. Use these exact IDs in column values and filenames.
- Question IDs: `Q001`–`Q040` (zero-padded 3 digits).
- Document IDs: `D001`, `D002`, … (corpus manifest IDs).
- Chunk IDs: `{STRATEGY}_{DOC_ID}_{SEQUENCE}` e.g. `C1_D001_0001`.

## CSV schemas (exact §10 — never add columns to these files)
- `questions.csv`: `question_id, question, type, difficulty`
- `ground_truth.csv`: `question_id, expected_answer, relevant_doc_ids, relevant_section_ids`
- `retrieved_results.csv`: `question_id, strategy, rank, chunk_id, score, is_relevant`
- `generated_answers.csv`: `question_id, strategy, answer, sources, prompt_tokens, completion_tokens`
- `scores.csv`: `question_id, strategy, correctness, completeness, groundedness, no_hallucination, clarity, total_score`

## Python conventions
- `src/config.py` is the single source for all parameters (chunk sizes, overlap, top-k, temperature, model names, paths).
- Never hardcode paths or model names outside `src/config.py`.
- All scripts in `src/` must be runnable standalone (argparse + `if __name__ == "__main__"`).
- All scripts currently are stubs (`raise NotImplementedError`) — implement one at a time per pipeline order.

## Git / repo
- `.serena/` is committed (tracked) — contains `project.yml` and memories.
- `.env` is gitignored — copy from `.env.example` and add `OPENAI_API_KEY`.
- `data/raw/`, `data/processed/`, `chroma_db/`, `*.pdf`, `docs/superpowers/` are all gitignored.

## Writing / academic conventions (IU)
- Citation style: APA 7, `biblatex` + `biber`, `\parencite{}` in LaTeX.
- BibTeX keys from `mem:research` literature table (e.g. `lewis2020rag`, `qu2025semanticchunking`).
- Only cite sources that appear in `literatur.bib` and are actually used.
- No first-person (`ich`, `wir`, `man`), no colloquialisms, no exclamation marks.
- Passive / neutral constructions preferred.
- Max 3 heading levels (1 / 1.1 / 1.1.1). Each sub-heading needs ≥ 2 sub-items.
- A heading is only created if ≥ ~0.5 page of text follows it.
- Results chapter: no interpretation — interpretation only in Diskussion.
- Main body: 40 pages ± 10% (36–44 pages).
- Figures/tables: source citation directly below at 10pt. Figures/table lists required if ≥ 3.

## Scope guard (explicitly OUT OF SCOPE — do not add)
- Comparing multiple LLMs or embedding models.
- RAG vs. no-RAG as primary question.
- Fine-tuning any model.
- Local/open-source LLMs.
- Purely automated evaluation without manual ground truth.
- Private/corporate data.
- Multimodal documents (PDFs with diagrams, images).
- C4 (semantic chunking) — only if phases 1–4 complete ahead of schedule.

## Corpus language
Vue.js corpus is English. All questions, reference answers, and annotation must also be in English to stay consistent with the embedding space. Thesis text is German.
