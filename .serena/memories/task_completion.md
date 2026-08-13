# Task Completion Checklist

When a coding task on this project is considered done:

## Code Quality
- [ ] No hardcoded paths, model names, or parameters outside `src/config.py`
- [ ] All intermediate outputs saved to `data/` (reproducibility requirement)
- [ ] Script runnable standalone (`if __name__ == "__main__"` or argparse)
- [ ] `temperature=0` and `top-k=5` enforced — never vary these accidentally

## Reproducibility
- [ ] Any LLM/embedding call logs model name + API response date to output metadata
- [ ] Corpus snapshot commit hash documented in `docs/corpus_manifest.csv`
- [ ] Chunk artefacts use exact naming: `chunks_c1.jsonl`, `chunks_c2.jsonl`, `chunks_c3.jsonl`

## Data Integrity
- [ ] Ground truth (`ground_truth.csv`) finalized **before** running evaluation — never adjust retroactively to match results
- [ ] RAGAS is only used as secondary evaluation — primary is always manual rubric

## Before Committing
```bash
# No linter/formatter enforced yet — project is pre-implementation.
# Dependencies: uv sync  (pyproject.toml + uv.lock)
# Once tooling is added as a dev dependency:
# uv run pytest        (if tests exist)
# uv run ruff check src/
```

> When linter/formatter/test commands are established, update this memory.
