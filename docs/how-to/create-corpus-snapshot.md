# Korpus-Snapshot erstellen

> Seitentyp: Anleitung (how-to). Übersicht: [Dokumentation](../README.md).

Welcher Commit und welche Regeln: [Korpus](../reference/corpus.md) ([ADR 0038](../adr/0038-korpus-e2e.md)); die
Werte stehen in `src/config.py` ([Konfiguration](../reference/configuration.md#korpus)). Gemessene Zahlen des
aktuellen Snapshots: [Experiment-Protokoll](../reference/experiment-record.md).

1. `uv run python src/snapshot.py` holt den Commit aus `config.CORPUS_COMMIT`, kopiert alle `*.mdx` unter
   `config.CORPUS_ROOT` sowie `config.CORPUS_SUPPORT_FILES` (`docs.json`, `snippets/model-provider.jsx`) nach
   `data/raw/e2e_docs_snapshot/` und schreibt `docs/corpus_snapshot.txt` (Commit, Daten, SHA-256 je Datei).
   Erwartet: `62 files`. Weichen die Seiten von der Navigation ab (Seite neu, entfernt oder umbenannt), bricht das
   Skript vor dem Kopieren ab und nennt die Seiten. Existiert `docs/corpus_snapshot.txt` schon, prüft das Skript die
   geholten Dateien dagegen und bricht bei Abweichung ab (die Dateien unter `data/raw/` sind dann bereits ersetzt).
   Für einen neuen Snapshot die Datei bewusst löschen.
2. `uv run python src/ingest.py` schreibt `data/processed/documents.jsonl` (Titel aus dem Frontmatter, Bereich aus
   der Navigation). Erwartet: `60 documents`. Bricht ab, wenn die Gruppen der Navigation nicht
   `config.CORPUS_AREAS` entsprechen.
3. `uv run python src/preprocess.py` wandelt die MDX-Seiten um (schreibt `documents.jsonl` neu) und erzeugt
   `data/processed/sections.jsonl` und `docs/corpus_manifest.csv`. Erwartet: `60 documents, 571 sections`. Eine
   unbekannte Komponente oder ein unbekanntes Tag bricht mit Seite und Zeile ab: dann eine Regel in `src/mdx.py`
   ergänzen (zuerst ein Test in `tests/test_mdx.py`), nie eine Seite einzeln behandeln.
4. `uv run python src/catalogue.py sections` schreibt die Nachschlageliste `data/processed/section_index.md`.
5. Prüfen: `uv run pytest` (die Integrationstests in `tests/test_corpus_integration.py` laufen nur mit vorhandenem
   Snapshot). Weicht das gerundete Mittel der C3-Chunks von `config.K1_CHUNK_SIZE` ab, nennt der K1-Test den neuen
   Wert ([ADR 0026](../adr/0026-c3-vergleichbarkeit.md)).
6. Dateizahl, Tokens und Abschnitte ins [Experiment-Protokoll](../reference/experiment-record.md) übernehmen; die
   erzeugten Dateien `docs/corpus_snapshot.txt` und `docs/corpus_manifest.csv` unverändert committen.
