# ADR 0007: Evaluation als Triangulation: manuell primär, RAGAS sekundär

- **Status:** angenommen (D7, verbindlich)
- **Quelle:** Chat; Verhältnis zur Baseline: verschärft (Baseline: RAGAS nur optional)
- **Details:** [Ground-Truth-Leitfaden](../Ground_Truth_Projektleitfaden.md), §12.3

## Kontext

LLM-as-a-Judge hat bekannte Grenzen der Verlässlichkeit; eine rein automatische Bewertung ist ausgeschlossen.

## Entscheidung

Primär wird manuell und referenzbasiert bewertet, sekundär mit RAGAS (Faithfulness, Context Relevance). Die Übereinstimmung beider wird als Validitätsindikator berichtet.

## Folgen

RAGAS ist nie alleinige Grundlage. Übereinstimmung spricht für Robustheit, Abweichung ist ein Befund zur Verlässlichkeit der Metrik.
