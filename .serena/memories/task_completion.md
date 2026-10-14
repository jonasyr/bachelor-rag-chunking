# Definition of done

- `uvx pre-commit run --all-files` passes (ruff lint + format, checks); `uv run pytest` passes (corpus integration tests need the local snapshot; they skip without it). Note:
  `pre-commit run --all-files` skips untracked files — `git add` new files before running it.
- No parameters outside `src/config.py`; temperature 0 and top-k 5 unchanged.
- Intermediate artefacts persisted; LLM/embedding calls record model name and date.
- Docs updated where the fact lives (`docs/`, then links; `/loadout:docs-sync`).
- Branch → PR → Codex review (`AGENTS.md` § Code Review Rules) → merge after Jonas approves → only then bump
  PaperLab's submodule pointer, to a commit on `main` (if the thesis depends on the change).
