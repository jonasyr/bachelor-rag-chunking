# Korpus-Snapshot erstellen

> Seitentyp: Anleitung (how-to). Stand: aus dem Projektleitfaden (Juni 2026, aktualisiert 13.10.2026). Übersicht: [Dokumentation](../README.md).

Ausschnitt und Commit: [Korpus](../reference/corpus.md) ([ADR 0025](../adr/0025-korpus-guide-api-styleguide.md)). Ergebnis in [Experiment-Protokoll](../reference/experiment-record.md) und `docs/corpus_manifest.csv` eintragen.

1. `uv run python src/snapshot.py` — holt den Commit aus `config.VUE_DOCS_COMMIT`, kopiert die Bereiche aus
   `config.VUE_DOCS_AREAS` (ohne `config.VUE_DOCS_EXCLUDED`) nach `data/raw/vue_docs_snapshot/<bereich>/` und schreibt
   `docs/corpus_snapshot.txt` (Commit, Daten, Bereiche, Ausschlüsse, SHA-256 je Datei; versioniert). Jede Ausnahme muss
   genau eine Markdown-Datei entfernen, sonst bricht das Skript vor dem Kopieren ab. Existiert die Datei
   schon, prüft das Skript die geholten Dateien dagegen und bricht bei Abweichung ab; ein neuer Snapshot braucht
   das bewusste Löschen der Datei.
2. `uv run python src/ingest.py` — schreibt `data/processed/documents.jsonl`.
3. `uv run python src/preprocess.py` — bereinigt die Texte, schreibt `sections.jsonl` und `docs/corpus_manifest.csv`.
4. Werte aus `docs/corpus_snapshot.txt` und die Token-Summe ins [Experiment-Protokoll](../reference/experiment-record.md)
   übernehmen, `docs/corpus_snapshot.txt` und `docs/corpus_manifest.csv` committen.

Prüfen: `uv run pytest` (die Integrationstests in `tests/test_corpus_integration.py` laufen nur mit vorhandenem Snapshot).

**Snapshot-Steckbrief (Vorlage):**
```
Projekt: Vue.js (vuejs/docs)
Quelle: offizielles GitHub-Repository
Commit: 40aa88af0094f7bab4aaf786e55c748a6a251d88
Datum des Snapshots: 14.10.2026
Verwendete Pfade:
- src/guide/, src/api/, src/style-guide/ (rekursiv, nur Composition API)
- ohne api/index.md, api/component-instance.md, api/options-*.md
Dateiformat: Markdown
Anzahl Dateien: 79
Gesamtumfang: 165.723 Tokens (cl100k_base, nach Preprocessing), 813 Abschnitte
```
