# Experiment durchführen

> Seitentyp: Anleitung (how-to). Übersicht: [Dokumentation](../README.md).

Voraussetzungen: [Einrichten](set-up.md), [Korpus-Snapshot](create-corpus-snapshot.md), Fragenkatalog und Ground Truth
fertig ([Fragenkatalog](../reference/question-catalogue.md)). Nur das Chunking variiert
([ADR 0006](../adr/0006-nur-chunking-variiert.md)).

## Reihenfolge

**Phase 1 – Vorbereitung:** Thema/Forschungsfrage finalisieren, Korpus (Vue.js) festlegen, Snapshot erstellen, Literaturbasis aufbauen.
**Phase 2 – Korpus und Ground Truth:** Dokumente sichten, relevante Bereiche wählen, bereinigen, Fragenkatalog erstellen, Referenzantworten formulieren, relevante Stellen annotieren.
**Phase 3 – Implementierung:** Preprocessing, Chunking C1/C2/C3, Embeddings, Vektorindizes pro Strategie, Retrieval, Antwortgenerierung, Datenspeicherung.
**Phase 4 – Evaluation:** Retrieval-Metriken berechnen, Antworten generieren und nach Rubrik bewerten, RAGAS-Sekundärbewertung, Übereinstimmung prüfen, Effizienz erfassen, Visualisierungen.
**Phase 5 – Schreiben:** Einleitung, Grundlagen, Verwandte Arbeiten, Methodik, Implementierung, Evaluation, Diskussion, Fazit.

**Minimaler Prototyp zuerst:** Markdown laden → C1/C2/C3 erzeugen → embedden → Chroma-Index pro Strategie → eine Frage abfragen → Top-5 anzeigen → Antwort generieren. Erst wenn das läuft, die große Evaluation.

Befehle je Schritt: [README](../../README.md#pipeline-run-in-order); Optionen: [Werkzeuge](../reference/tooling.md).

## Vor jedem Evaluationslauf prüfen

- [ ] Commit des Snapshots im [Experiment-Protokoll](../reference/experiment-record.md) und in `docs/corpus_manifest.csv`
- [ ] Exakte Modellversionen im Experiment-Protokoll eingetragen
- [ ] `ground_truth.csv` vor jedem Evaluationslauf fertig und danach unverändert
- [ ] Alle Zwischenstände gespeichert (`documents.jsonl`, `chunks_*.jsonl`, `retrieved_results.csv`, `generated_answers.csv`)
- [ ] Prompts in allen Strategieläufen unverändert ([Prompts](../reference/prompts.md))
- [ ] `LLM_TEMPERATURE = 0.0` in `src/config.py`
