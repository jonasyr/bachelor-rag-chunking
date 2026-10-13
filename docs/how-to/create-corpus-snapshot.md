# Korpus-Snapshot erstellen

> Seitentyp: Anleitung (how-to). Stand: aus dem Projektleitfaden (Juni 2026, aktualisiert 13.10.2026). Übersicht: [Dokumentation](../README.md).

Welche Pfade: [Korpus](../reference/corpus.md); der genaue Ausschnitt ist noch offen ([Plan](../plan.md)). Ergebnis in [Experiment-Protokoll](../reference/experiment-record.md) und `docs/corpus_manifest.csv` eintragen.

1. Repository klonen.
2. Konkreten Commit auswählen und **Commit-Hash dokumentieren**.
3. Relevante Markdown-Dateien in separaten Ordner kopieren.
4. Optional als ZIP archivieren, **Prüfsumme** erzeugen.
5. Im Anhang/Repository dokumentieren.

**Snapshot-Steckbrief (Vorlage):**
```
Projekt: Vue.js (vuejs/docs)
Quelle: offizielles GitHub-Repository
Commit: <commit-hash>
Datum des Snapshots: <Datum>
Verwendete Pfade:
- src/guide/essentials/
- src/guide/components/
- src/guide/reusability/
- src/guide/best-practices/
Dateiformat: Markdown
Anzahl Dateien: <n>
Gesamtumfang: <n> Tokens / Wörter
```
