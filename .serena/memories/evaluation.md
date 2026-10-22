# Evaluation

Metrics, rubric, rule-based scoring, K0, efficiency: `docs/reference/evaluation.md`; ADR 0007, 0008, 0012, 0013, 0035–0037, 0041.
- k is fixed at 5 — never vary it.
- Rule-based scoring is primary; RAGAS runs as fixed triangulation after `summarise` (judge `gpt-6-sol`, four metrics, ADR 0047): code `src/ragas_eval.py` + `src/ragas_client.py`, pilot done 21.10., main run still to do; see `evaluation.md#triangulation`, `tooling.md#ragas-pins`, `experiment-record.md#ragas-pilot-e2e-21102026`. Second rater (ADR 0046): `src/second_rater.py` draw → export → close, app R2 mode via `SCORING_RATER=R2`, agreement in `src/agreement.py` + table `agreement` (appendix B); draw right after the catalogue freeze, before own scoring; see `evaluation.md#zweitbewertung`. Gotcha: tests isolate `SECOND_RATER_DIR` and `SCORING_RATER` via an autouse fixture in `tests/conftest.py`.
- Ground truth (`data/evaluation/ground_truth.csv`) must be final before any evaluation run; never adjust afterwards.
- Relevance annotation is blind (before any retrieval); later additions count only as a sensitivity analysis (ADR 0027).
- Scoring page never opens `scoring_key.csv` (`tests/test_scoring_page.py`); key-point text is Jonas's only; the form
  help texts (`POINT_HELP`/`HELP` in `app/scoring_page.py`) must match `evaluation.md#regelbasierte-bewertung`.
- K0 is scored only after `scores.csv` exists (enforced), with the K0 rule variant (no `grounded`): `#kontrolle-k0`.
