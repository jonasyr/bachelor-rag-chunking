# Tech stack

Stack and model rules: `docs/reference/tooling.md`, ADR 0015, ADR 0016; dependencies in `pyproject.toml`/`uv.lock` (no requirements.txt).
- Embedding model `text-embedding-3-large` (3,072 dims), `openai==2.44.0`, `chromadb==1.5.9`: ADR 0023/0024.
  Chroma: always `embedding_function=None`, telemetry off, `cosine` (default would be `l2`).
- `LLM_MODEL` in `config.py` is a placeholder until pinned; record model/SDK versions and dates in `docs/reference/experiment-record.md`.
- Serena language servers: python, markdown (`.serena/project.yml`).
