# Tech stack

Stack and model rules: `docs/reference/tooling.md`, ADR 0015, 0016, 0023, 0024, 0033, 0047 (RAGAS pins: `tooling.md#ragas-pins`); dependencies in
`pyproject.toml`/`uv.lock` (no requirements.txt).
- Chroma: always `embedding_function=None`, telemetry off, `cosine` (default would be `l2`). Env vars: `tooling.md#umgebungsvariablen`.
- The answer model is an alias without dated snapshot: `generate.py` compares the model's `created` time before/after
  the run; enter the reported model (`model_reported`) in `docs/reference/experiment-record.md` after each real run.
- Prompt texts live in `config.py` and must match `docs/reference/prompts.md` (`tests/test_prompt.py`).
- Serena language servers: python, markdown (`.serena/project.yml`).
