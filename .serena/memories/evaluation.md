# Evaluation

Metrics, rubric, rule-based scoring, K0, RAGAS, second rater, statistics: `docs/reference/evaluation.md`
(ADR 0007, 0008, 0012, 0013, 0035–0037, 0041, 0044, 0046, 0047). Procedure and order: `docs/how-to/run-the-experiment.md`.
- Relevance annotation is blind (before any retrieval); later additions count only as a sensitivity analysis (ADR 0027).
- The scoring page never opens `scoring_key.csv` (`tests/test_scoring_page.py`); key-point text is Jonas's only; the
  check wording lives in `config.RUBRIC_*` (the form and the LLM cross-check read it): `evaluation.md#regelbasierte-bewertung`.
- K0 is scored only after `scores.csv` exists (enforced), with the K0 rule variant (no `grounded`): `#kontrolle-k0`.
- Second rating without a second person (ADR 0046 addendum): repeat rating (`second_rater.py --mode mark|repeat`,
  `SCORING_RATER=R1W`, key file only after `close --repeat`) and LLM cross-check (`llm_rater.py`); the check wording is
  `config.RUBRIC_*`, shared by the app and the LLM: `docs/reference/evaluation.md#zweitbewertung`,
  steps `docs/how-to/run-the-experiment.md#hybride-bewertung-ohne-zweite-person`; hybrid scoring (Jonas 24 questions, LLM all, no repeat rating): ADR 0051.
- RAGAS, second-rater and LLM cross-check steps are one-shot and never overwrite; options: `docs/reference/tooling.md#skripte-und-optionen`;
  test isolation (autouse fixtures): `docs/reference/tooling.md#tests`.
