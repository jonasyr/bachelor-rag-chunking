# bachelor-rag-chunking — Core

Code of Jonas Weirauch's bachelor thesis (IU, B.Sc. Informatik, supervisor Prof. Klaus Quibeldey-Cirkel,
submission 24.12.2026): RAG pipeline on the e2e docs (ADR 0038; corpus switched, rebuild in progress,
corpus choice in `docs/reference/corpus-selection.md`), only the chunking strategy varies.
Facts live in `docs/` — start at `docs/README.md`; research design `docs/explanation/research-design.md`
(Rangfolge: ADRs bindend — section "Rangfolge bei Widersprüchen").

Status (what is implemented, next step): `docs/plan.md#stand` — never restate it here.
Workflow: branch → PR → Codex review (`AGENTS.md` § Code Review Rules, `.claude/agents/codex-reviewer.md`) → merge
after Jonas approves. Repo is public — no personal data (matriculation number etc.).

## Memories
- Pipeline gotchas (token spans, preprocessing, re-embedding, corpus IDs) and what is still a stub: `mem:pipeline`
- C1/C2/C3 and the control K1 (ADR 0021, 0026): `mem:chunking`
- Metrics, rubric, triangulation pointers: `mem:evaluation`
- Research question, hypotheses, literature pointers: `mem:research`
- Where decisions live (ADRs, open ones): `mem:decisions`
- Stack and model pinning: `mem:tech_stack`
- Naming, IDs, CSV rules, scope guard: `mem:conventions`
- Commands: `mem:suggested_commands`; definition of done: `mem:task_completion`
