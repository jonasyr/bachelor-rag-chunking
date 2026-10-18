# 0025. Korpus: Guide, API-Referenz (Composition) und Style Guide auf `40aa88a`

## Status

Angenommen (14.10.2026; ersetzt Ausschnitt und Commit von [ADR 0019](0019-korpus-ausschnitt.md), dessen übrige Regeln gelten weiter); ersetzt durch [ADR 0038](0038-korpus-e2e.md) (18.10.2026)

## Kontext

- Echte Open-Source-Dokumentation ist geschichtet: Konzepte (Guide), Referenz (API) und Konventionen (Style Guide); dasselbe Thema steht oft an mehreren Stellen. Ein reiner Guide-Korpus bildet das nicht ab.
- Das Exposé begrenzt den Korpus „bewusst auf ausgewählte Bereiche“; drei benannte Bereiche erfüllen das.
- Messung auf dem gepinnten Commit: API 22 Seiten, Style Guide 5 Seiten; alle H1–H3-Überschriften tragen Anker. Die API-Seiten brauchten vier neue, getestete Bereinigungsregeln: escapte `\<` sind Text, `<br>` in Überschriften wird ein Leerzeichen, `v-pre` um Inline-Code wird entpackt, und ATX-Überschriften dürfen bis zu drei Leerzeichen eingerückt sein (CommonMark; die API rückt sie in Listenpunkten ein). Der Guide bleibt damit Byte für Byte gleich.
- Tutorial: 15 Schritte (rund 6.500 Tokens) für einen interaktiven Editor; der Code liegt in eigenen Dateien, der Inhalt wiederholt den Guide (Beinahe-Duplikate, zusätzlicher Annotationsaufwand).
- Options-API-Referenzseiten (`options-*`, `component-instance`): Die Website zeigt immer nur einen API-Stil (Umschalter); zwei Stile wären Beinahe-Duplikate, Fragen hätten zwei richtige Antworten, gemischter Kontext verschlechtert Antworten unabhängig vom Chunking ([ADR 0006](0006-nur-chunking-variiert.md)). `api/index.md` ist ein generiertes Inhaltsverzeichnis ohne eigenen Text.
- `vuejs/docs` `main` lag am 14.10.2026 acht Commits vor `b75d188` (letzter Commit 15.09.2026); im Ausschnitt änderten sich nur sechs Guide-Dateien (+13/−9 Zeilen), davon fünf inhaltlich (bei `teleport.md` entfiel nur ein Werbelink). Alle Artefakte werden ohnehin neu gebaut, ausgewertet ist noch nichts.

## Entscheidung

Wir werden als Korpus alle Markdown-Dateien unter `src/guide/`, `src/api/` und `src/style-guide/` aus `vuejs/docs` auf Commit `40aa88af0094f7bab4aaf786e55c748a6a251d88` verwenden, ohne `api/index.md`, `api/component-instance.md` und `api/options-{composition,lifecycle,misc,rendering,state}.md`.
Wir werden Tutorial, Beispiele und Projektseiten (about, ecosystem, partners usw.) nicht aufnehmen.
Bereiche und Ausschlüsse stehen in [`src/config.py`](../../src/config.py) (`VUE_DOCS_AREAS`, `VUE_DOCS_EXCLUDED`); jede Ausnahme muss genau eine Markdown-Datei entfernen, sonst bricht der Snapshot ab.

## Konsequenzen

- Gut: realistische, geschichtete Dokumentation mit 79 Seiten, 165.723 Tokens und 813 Abschnitten (Guide 117.694, API 42.488, Style Guide 5.541 Tokens); das Retrieval muss zwischen Konzept, Referenz und Konvention unterscheiden.
- Gut: Prüfungen belegt ([Experiment-Protokoll](../reference/experiment-record.md)): Guide-Bereinigung unverändert (V1), nur die fünf inhaltlich geänderten Guide-Dateien weichen ab (V2), Dateiliste gleich dem GitHub-Baum des Commits (V3).
- Schlecht: mehr Annotationsaufwand; viele Fragen haben relevante Abschnitte in Guide und API. Die Abschnitts-Nachschlageliste stützt das.
- Neutral: Ergebnisse gelten für Nutzer der Composition API; das steht in den Limitationen.
- Neutral: Doc-IDs wurden neu vergeben (die 22 API-Seiten stehen vorn); die Pilot-Ground-Truth wurde per Skript über Pfad und Anker abgebildet, ohne ein Relevanzurteil zu ändern.
