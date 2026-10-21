# 0045. Retrieval-Ergebnisse des Hauptlaufs versioniert

## Status

Angenommen (21.10.2026; ändert die Versionierungsliste in [Datenformate](../reference/data-formats.md#versioniert-und-ignoriert) und den Status von [ADR 0024](0024-referenzvektoren-und-exakte-suche.md))

## Kontext

- Fragevektoren (`query_embeddings.npz`), `retrieved_results.csv`, `retrieved_results_control.csv` und die
  Retrieval-Metriken waren ignoriert, weil sie sich neu erzeugen lassen.
- Neu erzeugen heißt neue Fragevektoren über die API; sie sind nicht bitgleich (Modellstand-Prüfung Kosinus 0,99994,
  [Experiment-Protokoll](../reference/experiment-record.md#pilot-e2e-1920102026)), und ein anderes Top-5 ist möglich.
- Jeder spätere Schritt prüft Prüfsummen gegen diese Dateien: der `generate`-Eintrag gegen `retrieved_results.csv`,
  `analyse.py` gegen die Retrieval-Metriken ([ADR 0044](0044-statistische-auswertung.md)). Gehen sie verloren, lassen
  sich Antworten und Bewertungen nicht mehr an ihr Retrieval binden.
- Die Laufeinträge `embed`, `retrieve` und `evaluate_retrieval` stehen in `data/processed/embedding_runs.jsonl`, das
  mit `data/processed/` ignoriert war; ohne sie bricht `analyse.py` auf einem neuen Klon ab.
- Das Repo ist öffentlich und bekommt eine DOI; die Dateien sind klein (48 Fragen: etwa 0,6 MB Vektoren, wenige
  Kilobyte CSV).

## Entscheidung

Wir werden `data/evaluation/query_embeddings.npz`, `retrieved_results.csv`, `retrieved_results_control.csv`,
`retrieval_scores.csv` und `retrieval_scores_control.csv` sowie das Laufprotokoll
`data/processed/embedding_runs.jsonl` versionieren und nach dem jeweiligen Schritt committen
([Experiment durchführen](../how-to/run-the-experiment.md#hauptlauf-auf-einen-blick)). Die Fragevektoren der
Pilot-Sets bleiben ignoriert.

## Konsequenzen

- Positiv: Der Hauptlauf ist ohne API-Aufruf nachvollziehbar; die Prüfsummenkette vom Retrieval bis zur Auswertung
  bleibt auf jedem Klon prüfbar.
- Negativ: Etwa 0,6 MB Binärdaten im Repo; das Laufprotokoll liegt als einzige versionierte Datei in `data/processed/`.
- Neutral: Chunk-Vektoren und Chroma-Index bleiben ignoriert; sie sind groß und werden über die Modellstand-Prüfung
  abgesichert.
