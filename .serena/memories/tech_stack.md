# Tech Stack

All binding per Decision Log (see `mem:decisions` D15–D16).

| Purpose | Tool / Library |
|---------|---------------|
| Language | Python (primary), Markdown (corpus + docs) |
| Document processing | `python-markdown`, `pathlib`, `regex` |
| Token counting | `tiktoken` |
| Embeddings | OpenAI API — `text-embedding-3-large` (default) or `text-embedding-3-small` (cost/speed focus) |
| Vector store | **Chroma** (local, persistent) — one index per chunking strategy |
| LLM | Fixed GPT model via OpenAI API (exact version pinned at implementation time, documented, held constant throughout evaluation) |
| Data analysis | `pandas` |
| Visualization | `matplotlib` / `plotly` |
| Dashboard / demo | `streamlit` (`app/streamlit_app.py`) |
| Evaluation (secondary) | `ragas` (optional but planned as secondary triangulation) |
| Citation / bibliography | `biblatex` + `biber`, APA 7, `\parencite` |

## Serena config
- Languages: `python` (primary) + `markdown`
- Config: `.serena/project.yml` — committed to repo
- Index covers: 11 Python files (`src/` + `app/`) + 5 Markdown files (`docs/`)

## Critical Constraints
- **temperature = 0** for all LLM calls (reproducibility, internal validity).
- **top-k = 5** — constant across all strategies. Do NOT vary top-k (would introduce a second independent variable).
- Exact model version, SDK version, API version, and query dates must be recorded in the methodology chapter at implementation time — never reference a snapshot model name in the writing without that record.
- Embedding language: corpus is English; questions and reference answers must also be English (embedding space consistency).
- `pyproject.toml` + `uv.lock` are the canonical dependency source (installed via `uv sync`). There is no `requirements.txt`.
