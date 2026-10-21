# bachelor-rag-chunking — Core

Code of Jonas Weirauch's bachelor thesis (IU, B.Sc. Informatik, submission 24.12.2026): RAG pipeline on the e2e docs
(ADR 0038; corpus choice `docs/reference/corpus-selection.md`), only the chunking strategy varies.
Facts live in `docs/` — start at `docs/README.md`; research design `docs/explanation/research-design.md`
(ADRs outrank it and the exposé: paragraph "Was gilt bei Widersprüchen").

Status (what is done, next step): `docs/plan.md#stand` — never restate it here.
Workflow: branch → PR → Codex review (`AGENTS.md` § Code Review Rules, `.claude/agents/codex-reviewer.md`) → merge
after Jonas approves. Repo is public — no personal data (matriculation number etc.).
Commands: `AGENTS.md` (table) and `docs/reference/tooling.md`; run scripts from the repo root. `--help` only works
where argparse exists: `snapshot.py`, `ingest.py`, `preprocess.py` run their step instead (snapshot replaces `data/raw/`).
Tools: use Serena (project `bachelor-rag-chunking`) and codebase-memory for code work, also in subagents. The
codebase-memory project name is the path form `home-jonas-Documents-Code-PaperLab-scientific-papers-thesis-thesis-semester-7-rag-chunking_jonas-code`;
`bachelor-rag-chunking` there returns "function not found". Reindex: `index_repository` and `serena project index`.

## Memories
- Step order and refusals, catalogue, closed-book screen, K0, embedding and corpus gotchas: `mem:pipeline`
- C1/C2/C3 and the controls K1/K0 (ADR 0021, 0026, 0041): `mem:chunking`
- Metrics, rule-based scoring, K0 scoring guards: `mem:evaluation`
- Research question, hypotheses, literature pointers: `mem:research`
- Where decisions live and how to add one: `mem:decisions`
- Stack and model pinning: `mem:tech_stack`
- Naming, IDs, CSV rules, scope guard: `mem:conventions`
- Definition of done: `mem:task_completion`; how memories are kept: `mem:memory_maintenance`
