# Definition of done

- `uvx pre-commit run --all-files` passes (ruff lint + format, checks); `uv run pytest` once `tests/` exists.
- No parameters outside `src/config.py`; temperature 0 and top-k 5 unchanged.
- Intermediate artefacts persisted; LLM/embedding calls record model name and date.
- Docs updated where the fact lives (`docs/`, then links; `/loadout:docs-sync`). Push, then bump the submodule
  pointer in PaperLab if the thesis depends on the change.
