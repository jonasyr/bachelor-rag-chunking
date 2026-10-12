# ADR 0012: Retrieval-Metriken: Recall@k, Precision@k, MRR (+ Hit@k)

- **Status:** angenommen (D12, verbindlich)
- **Quelle:** Exposé/Baseline; Verhältnis zur Baseline: übernommen
- **Details:** [Ground-Truth-Leitfaden](../Ground_Truth_Projektleitfaden.md), §12.1

## Kontext

Die Retrieval-Qualität braucht etablierte IR-Metriken.

## Entscheidung

Je Frage und Strategie Recall@k, Precision@k und MRR, vereinfacht zusätzlich Hit@k; k = 5.

## Folgen

Umsetzung in `src/evaluate_retrieval.py`; Definitionen im Leitfaden §12.1.
