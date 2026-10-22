# Chunking

Strategies: ADR 0005 / `docs/explanation/research-design.md`; parameter values and strategy IDs:
`docs/reference/configuration.md` (set only in `src/config.py`). C2 is a strong baseline (ADR 0010).
- C3 rules (floor 50, merge before split, no short tails): ADR 0021; chunk text is always the exact document slice
  (no prepended headings) — `check_chunks` enforces it and every strategy except C2 (C1, C3, K1) reassembles each document.
- Strategy keys and IDs: rules in `AGENTS.md`; never write the ID strings literally.
- K1 = size-matched control (ADR 0026): kept out of `STRATEGY_IDS` (own `CONTROL_*` mappings), retrieval only
  (`retrieve.py --control`); `chunk("K1")` aborts if the corpus changed and `K1_CHUNK_SIZE` no longer matches the
  rule — then set the printed value in config.
- K0 (ADR 0041) is no chunking strategy: answers without retrieval (`config.CONTROL_ANSWER_STRATEGIES`), no chunks.
- C4 (semantic) only if the 09.11.2026 milestone is met (ADR 0028); then reported descriptively only, outside the test
  plan (ADR 0044) and outside 0046/0047.
