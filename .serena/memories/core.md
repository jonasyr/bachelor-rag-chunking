# bachelor-rag-chunking — Core

Code of Jonas Weirauch's bachelor thesis (IU, B.Sc. Informatik, supervisor Prof. Dr.-Ing. Klaus Quibeldey-Cirkel,
submission 24.12.2026): RAG pipeline on Vue.js docs, only the chunking strategy varies.
Facts live in `docs/` — start at `docs/README.md`; research design `docs/explanation/research-design.md`
(conflict priority: its §0).

Status 14.10.2026: corpus = guide + API (Composition) + style guide at vuejs/docs 40aa88a, 79 pages (ADR 0025;
cleaning rules ADR 0019/0020); control K1 + fair sensitivity rule (ADR 0026); snapshot to retrieval implemented and
tested (embeddings stored, ADR 0023/0024); pilot probes in `data/pilot/` (not the catalogue); generation and evaluation are stubs; real retrieval waits for the frozen ground truth; schedule in `docs/plan.md`; ruff/pre-commit/CI in place. Workflow: branch → PR → Codex
review (`AGENTS.md` § Code Review Rules, `.claude/agents/codex-reviewer.md`) → merge after Jonas approves. Repo is public — no personal data (matriculation number etc.).

## Memories
- Pipeline order, what is implemented, token-span and preprocessing gotchas: `mem:pipeline`
- C1/C2/C3 details and the C3 bounds (ADR 0021): `mem:chunking`
- Metrics, rubric, triangulation pointers: `mem:evaluation`
- Research question, hypotheses, literature pointers: `mem:research`
- Where decisions live (ADRs, open ones): `mem:decisions`
- Stack and model pinning: `mem:tech_stack`
- Naming, IDs, CSV rules, scope guard: `mem:conventions`
- Commands: `mem:suggested_commands`; definition of done: `mem:task_completion`
