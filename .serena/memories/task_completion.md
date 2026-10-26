# Definition of done

- `uvx pre-commit run --all-files` passes (ruff lint + format, checks); `uv run pytest` passes (corpus integration tests skip without snapshot; tests: `docs/reference/tooling.md#tests`). `git add` new files first: pre-commit skips
  untracked files (`docs/reference/tooling.md#qualitätswerkzeuge`).
- No parameters outside `src/config.py`; temperature 0 and top-k 5 unchanged.
- Intermediate artefacts persisted; LLM/embedding calls record model name and date.
- Docs updated where the fact lives (`docs/`, then links; `/loadout:docs-sync`).
- Branch → PR → Codex review (`AGENTS.md` § Code Review Rules) → merge after Jonas approves → only then bump
  PaperLab's submodule pointer, to a commit on `main` (if the thesis depends on the change).
