# Evaluation

Metrics, rubric, rule-based scoring, K0, RAGAS, second rater, statistics: `docs/reference/evaluation.md`
(ADR 0007, 0008, 0012, 0013, 0035–0037, 0041, 0044, 0046, 0047). Procedure and order: `docs/how-to/run-the-experiment.md`.
- Relevance annotation is blind (before any retrieval); later additions count only as a sensitivity analysis (ADR 0027).
- The scoring page never opens `scoring_key.csv` (`tests/test_scoring_page.py`); key-point text is Jonas's only; the form
  help texts (`POINT_HELP`/`HELP` in `app/scoring_page.py`) must match `evaluation.md#regelbasierte-bewertung`.
- K0 is scored only after `scores.csv` exists (enforced), with the K0 rule variant (no `grounded`): `#kontrolle-k0`.
- RAGAS and second-rater steps are one-shot and never overwrite; options: `docs/reference/tooling.md#skripte-und-optionen`;
  test isolation (autouse fixtures): `docs/reference/tooling.md#tests`.
