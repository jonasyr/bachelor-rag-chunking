# Tech stack

Stack and model rules: `docs/reference/tooling.md`, ADR 0015, ADR 0016; dependencies in `pyproject.toml`/`uv.lock` (no requirements.txt).
- Embedding model `text-embedding-3-large` (3,072 dims), `openai==2.44.0`, `chromadb==1.5.9`: ADR 0023/0024.
  Chroma: always `embedding_function=None`, telemetry off, `cosine` (default would be `l2`).
- Answer model `gpt-6-luna`, effort `none`, temperature 0 (ADR 0033); the API reports no dated version and no
  fingerprint, so `generate.py` compares the model's `created` time before/after the run; after the first real run, enter the model the
  API reported (`model_reported`) in `docs/reference/experiment-record.md`. Prompt text lives in `config.py` and
  must match `docs/reference/prompts.md` (`tests/test_prompt.py`).
- Serena language servers: python, markdown (`.serena/project.yml`).
