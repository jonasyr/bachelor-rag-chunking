# Korpus-Snapshot erstellen

> Seitentyp: Anleitung (how-to). Übersicht: [Dokumentation](../README.md).

Welche Bereiche und welcher Commit: [Korpus](../reference/corpus.md)
([ADR 0025](../adr/0025-korpus-guide-api-styleguide.md)); die Werte stehen in `src/config.py`
([Konfiguration](../reference/configuration.md)). Gemessene Zahlen des aktuellen Snapshots:
[Experiment-Protokoll](../reference/experiment-record.md).

1. `uv run python src/snapshot.py` holt den Commit aus `config.VUE_DOCS_COMMIT`, kopiert die Bereiche aus
   `config.VUE_DOCS_AREAS` (ohne `config.VUE_DOCS_EXCLUDED`) nach `data/raw/vue_docs_snapshot/<bereich>/` und schreibt
   `docs/corpus_snapshot.txt` (Commit, Daten, Bereiche, Ausschlüsse, SHA-256 je Datei). Jede Ausnahme muss genau eine
   Markdown-Datei entfernen, sonst bricht das Skript vor dem Kopieren ab. Existiert `docs/corpus_snapshot.txt` schon,
   prüft das Skript die geholten Dateien dagegen und bricht bei Abweichung ab (die Dateien unter `data/raw/` sind dann
   bereits ersetzt). Für einen neuen Snapshot die Datei bewusst löschen.
2. `uv run python src/ingest.py` schreibt `data/processed/documents.jsonl`.
3. `uv run python src/preprocess.py` bereinigt die Texte (schreibt `documents.jsonl` neu) und erzeugt
   `data/processed/sections.jsonl` und `docs/corpus_manifest.csv`.
4. Prüfen: `uv run pytest` (die Integrationstests in `tests/test_corpus_integration.py` laufen nur mit vorhandenem
   Snapshot).
5. Dateizahl und Token-Summe ins [Experiment-Protokoll](../reference/experiment-record.md) übernehmen; die erzeugten
   Dateien `docs/corpus_snapshot.txt` und `docs/corpus_manifest.csv` unverändert committen.
