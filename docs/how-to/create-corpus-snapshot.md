# Korpus-Snapshot erstellen

> Seitentyp: Anleitung (how-to). Stand: aus dem Projektleitfaden (Juni 2026, aktualisiert 13.10.2026). Übersicht: [Dokumentation](../README.md).

Ausschnitt und Commit: [Korpus](../reference/corpus.md) ([ADR 0019](../adr/0019-korpus-ausschnitt.md)). Ergebnis in [Experiment-Protokoll](../reference/experiment-record.md) und `docs/corpus_manifest.csv` eintragen.

1. `uv run python src/snapshot.py` — holt den Commit aus `config.VUE_DOCS_COMMIT`, kopiert `src/guide/` nach
   `data/raw/vue_docs_snapshot/guide/` und schreibt `SNAPSHOT.txt` (Commit, Datum, SHA-256 je Datei).
2. `uv run python src/ingest.py` — schreibt `data/processed/documents.jsonl`.
3. `uv run python src/preprocess.py` — bereinigt die Texte, schreibt `sections.jsonl` und `docs/corpus_manifest.csv`.
4. Werte aus `SNAPSHOT.txt` und die Token-Summe ins [Experiment-Protokoll](../reference/experiment-record.md)
   übernehmen, `docs/corpus_manifest.csv` committen.

Prüfen: `uv run pytest` (die Integrationstests in `tests/test_corpus_integration.py` laufen nur mit vorhandenem Snapshot).

**Snapshot-Steckbrief (Vorlage):**
```
Projekt: Vue.js (vuejs/docs)
Quelle: offizielles GitHub-Repository
Commit: b75d188ab16bf83bd1f364a77dfd2315be8f3fa4
Datum des Snapshots: 13.10.2026
Verwendete Pfade:
- src/guide/ (rekursiv, nur Composition API)
Dateiformat: Markdown
Anzahl Dateien: 52
Gesamtumfang: 139.500 Tokens (cl100k_base, nach Preprocessing), 560 Abschnitte
```
