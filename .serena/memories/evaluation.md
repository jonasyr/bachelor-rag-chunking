# Evaluation

Metrics, rubric, rule-based scoring, K0, efficiency: `docs/reference/evaluation.md`; ADR 0007, 0008, 0012, 0013, 0035–0037, 0041.
- k is fixed at 5 — never vary it.
- Rule-based scoring is primary; RAGAS runs as fixed triangulation after `summarise` (judge `gpt-6-sol`, four metrics, ADR 0047; no code yet). Second rater: 12 questions × C1–C3, AC1/AC2 + Krippendorff's α, no Cohen's kappa (ADR 0046; sampling and agreement code not yet built).
- Ground truth (`data/evaluation/ground_truth.csv`) must be final before any evaluation run; never adjust afterwards.
- Relevance annotation is blind (before any retrieval); later additions count only as a sensitivity analysis (ADR 0027).
- Scoring page never opens `scoring_key.csv` (`tests/test_scoring_page.py`); key-point text is Jonas's only; the form
  help texts (`POINT_HELP`/`HELP` in `app/scoring_page.py`) must match `evaluation.md#regelbasierte-bewertung`.
- K0 is scored only after `scores.csv` exists (enforced), with the K0 rule variant (no `grounded`): `#kontrolle-k0`.
