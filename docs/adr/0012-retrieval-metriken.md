# 0012. Retrieval-Metriken: Recall@k, Precision@k, MRR (+ Hit@k)

## Status

Angenommen (D12 im Leitfaden; Quelle: Exposé/Baseline, übernommen)

## Kontext

- Unterfrage 2 fragt nach Unterschieden der Retrieval-Qualität, gemessen mit Recall@k, Precision@k und MRR (Leitfaden §1).
- Die Literaturbasis enthält `manning2008ir` als Quelle für die IR-Metriken Precision, Recall und MRR (Leitfaden §18).
- top-k ist konstant 5 ([ADR 0014](0014-temperatur-und-topk.md)).

## Entscheidung

Wir werden je Frage und Strategie Recall@k, Precision@k und MRR berechnen, zusätzlich vereinfacht Hit@k, jeweils mit k = 5 (Definitionen in [Leitfaden §12.1](../reference/evaluation.md)).

## Konsequenzen

- Neutral: Umsetzung in [`src/evaluate_retrieval.py`](../../src/evaluate_retrieval.py) auf Basis von `retrieved_results.csv`.
- Neutral: Die Metriken brauchen vorab annotierte relevante Quellen je Frage ([ADR 0017](0017-fragenkatalog.md)).
