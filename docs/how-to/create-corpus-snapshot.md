# Korpus-Snapshot erstellen

> Seitentyp: Anleitung (how-to). Stand: aus dem Projektleitfaden (Juni 2026, aktualisiert 13.10.2026). Übersicht: [Dokumentation](../README.md).

Ausschnitt und Commit: [Korpus](../reference/corpus.md) ([ADR 0019](../adr/0019-korpus-ausschnitt.md)). Ergebnis in [Experiment-Protokoll](../reference/experiment-record.md) und `docs/corpus_manifest.csv` eintragen.

1. Repository klonen.
2. Konkreten Commit auswählen und **Commit-Hash dokumentieren**.
3. Relevante Markdown-Dateien in separaten Ordner kopieren.
4. Optional als ZIP archivieren, **Prüfsumme** erzeugen.
5. Im Anhang/Repository dokumentieren.

**Snapshot-Steckbrief (Vorlage):**
```
Projekt: Vue.js (vuejs/docs)
Quelle: offizielles GitHub-Repository
Commit: b75d188ab16bf83bd1f364a77dfd2315be8f3fa4
Datum des Snapshots: <Datum>
Verwendete Pfade:
- src/guide/ (rekursiv, nur Composition API)
Dateiformat: Markdown
Anzahl Dateien: <n>
Gesamtumfang: <n> Tokens / Wörter
```
