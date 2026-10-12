# ADR 0006: Nur das Chunking variiert

- **Status:** angenommen (D6, verbindlich)
- **Quelle:** Exposé; Verhältnis zur Baseline: übernommen
- **Details:** [Ground-Truth-Leitfaden](../Ground_Truth_Projektleitfaden.md), §6

## Kontext

Der Einfluss der Chunking-Strategie soll isoliert bestimmt werden.

## Entscheidung

Konstant bleiben Korpus/Snapshot, Sprache (Englisch), Embedding-Modell, LLM, Temperatur 0, top-k 5, Prompt, Fragenset, Rubrik, Vector Store, Retrieval-Art (Dense) und Antwortformat.

## Folgen

Jede zusätzliche Variation (z. B. top-k) wäre eine zweite unabhängige Variable und ist ausgeschlossen.
