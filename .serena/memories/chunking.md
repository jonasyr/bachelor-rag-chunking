# Chunking

Strategies and parameters: ADR 0005 / `docs/explanation/research-design.md`; values only in `src/config.py`. C2 is a strong baseline (ADR 0010).
- C3 rules (floor 50, merge before split, no short tails): ADR 0021; chunk text is always the exact document slice
  (no prepended headings) — `check_chunks` enforces it and C1/C3 reassemble each document.
- `strategy` field values come from `config.STRATEGY_IDS` (`fixed_500_no_overlap`, `fixed_500_overlap_100`,
  `structure_h2h3`); short keys `C1`–`C3` in CLI, file names and CSV `strategy` columns.
- C4 (semantic) only if the 09.11. milestone (ground truth frozen) is met on time (`docs/plan.md`).
