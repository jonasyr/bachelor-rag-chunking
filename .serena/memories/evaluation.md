# Evaluation

Metrics, rubric, triangulation, efficiency, statistics, visualisations: Leitfaden §12–§14; ADR 0007, 0008, 0012, 0013.
- k is fixed at 5 — never vary it.
- RAGAS is secondary only; the manual rubric is primary. Report agreement between both.
- Ground truth (`data/evaluation/ground_truth.csv`) must be final before any evaluation run; never adjust afterwards.
