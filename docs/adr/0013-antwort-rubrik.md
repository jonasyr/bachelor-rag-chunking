# ADR 0013: Antwort-Rubrik: Skala 0–2, fünf Kriterien, gleich gewichtet

- **Status:** angenommen (D13, verbindlich)
- **Quelle:** Exposé/Baseline; Verhältnis zur Baseline: übernommen
- **Details:** [Ground-Truth-Leitfaden](../Ground_Truth_Projektleitfaden.md), §12.2

## Kontext

Die Antwortqualität muss nachvollziehbar und verteidigbar bewertet werden.

## Entscheidung

Kriterien Korrektheit, Vollständigkeit, Quellenbezug, Halluzinationsfreiheit, Verständlichkeit, je 0–2, gleich gewichtet.

## Folgen

Umsetzung in `src/evaluate_answers.py` und `scores.csv`; Rubrik im Leitfaden §12.2.
