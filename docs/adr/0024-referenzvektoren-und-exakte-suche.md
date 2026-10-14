# 0024. Referenzvektoren speichern und exakt suchen

## Status

Angenommen (13.10.2026; konkretisiert [ADR 0015](0015-tech-stack.md)); Zahlen im Kontext: Korpus `b75d188` (13.10.2026); aktuelle Werte im [Experiment-Protokoll](../reference/experiment-record.md); welche Dateien unter `data/` versioniert sind, steht in [Werkzeuge](../reference/tooling.md) (nicht versioniert sind u. a. `data/processed/` und `query_embeddings.npz`, nicht ganz `data/`)

## Kontext

- Für `text-embedding-3-large` führt OpenAI nur den Alias selbst als Snapshot; eine datierte Version gibt es nicht
  (`openai2026te3large`). Das Modell hinter dem Namen kann sich ändern, und wiederholte Aufrufe liefern nicht
  zwingend bitgleiche Vektoren.
- Chroma sucht mit einem HNSW-Index approximativ; Standard sind die Metrik `l2` und `ef_search` = 100
  (`chroma2026configure`).
- OpenAI-Vektoren sind auf Länge 1 normiert; Kosinus und Skalarprodukt ergeben dieselbe Rangfolge
  (`openai2026embeddingsguide`).
- Eine Messung am 13.10.2026 (je drei Chunks pro Strategie erneut eingebettet) ergab für denselben Text eine
  Kosinus-Ähnlichkeit von mindestens 0,99996 zum gespeicherten Vektor, nur 7 von 9 Vektoren waren bitgleich;
  verschiedene Chunks erreichen höchstens 0,84.
- Die Fragevektoren entstehen erst nach dem Einfrieren der Ground Truth, Wochen nach den Chunk-Vektoren; ändert
  OpenAI in der Zwischenzeit das Modell hinter dem Alias, lägen Fragen und Chunks in verschiedenen Vektorräumen
  (Hinweis aus dem Codex-Review von PR #5).
- Nichtdeterminismus in allem, was in die Evaluation eingeht, verletzt die Code-Review-Regeln (`AGENTS.md`); mit
  höchstens 493 Vektoren je Strategie ist eine exakte Suche billig.

## Entscheidung

Wir werden Chunk- und Fragevektoren einmal erzeugen und mit Modellname, IDs und Texten speichern (`embeddings_cN.npz`,
`query_embeddings.npz`); die Chroma-Indizes werden nur aus diesen Vektoren gebaut, eine Neuberechnung erfordert das
bewusste Löschen der Datei.
Wir werden Chroma mit der Metrik `cosine` und `ef_search` mindestens in Größe der Sammlung betreiben, jedes Top-k gegen
eine exakte NumPy-Kosinus-Rangfolge prüfen (Toleranz 1e-5), bei Abweichung abbrechen und Gleichstände nach `chunk_id`
ordnen. Telemetrie und Chromas eingebaute Embedding-Funktion bleiben abgeschaltet.
Wir werden vor jedem Hinzufügen neuer Vektoren (weitere Strategie oder Fragen) den ersten, mittleren und letzten
gespeicherten Text jeder vorhandenen Vektordatei erneut einbetten und abbrechen, wenn die Kosinus-Ähnlichkeit zum
gespeicherten Vektor unter 0,999 liegt (`CANARY_MIN_COSINE`); dann werden alle Vektordateien bewusst gelöscht und
gemeinsam neu erzeugt. Der gemessene Wert steht im Laufprotokoll, getrennt von den Kosten der Strategien.
Wir werden das Retrieval immer über alle Strategien gemeinsam aus denselben Eingaben ausführen und
`retrieved_results.csv` dabei vollständig neu schreiben; Teilläufe einzelner Strategien gibt es nicht.

## Konsequenzen

- Gut: Indexaufbau und Retrieval lassen sich ohne API-Aufruf byte-gleich wiederholen; die Top-5 sind nachweislich
  exakt.
- Neutral: Die Vektordateien sind nicht versioniert (`data/` ist ausgeschlossen) und werden für die Archivierung
  (DOI) gesondert gesichert.
- Gut: Alle Strategien eines Ergebnisses beruhen auf demselben Lauf mit identischen Eingaben; ältere Zeilen können
  nicht mit neuen vermischt werden (Codex-Reviews von PR #5).
- Gut: Alle Vektoren einer Auswertung stammen nachweislich aus demselben Modellstand, auch wenn Fragen Wochen später
  eingebettet werden ([ADR 0006](0006-nur-chunking-variiert.md)).
- Schlecht: Die zusätzlichen Prüfungen kosten etwas Laufzeit und je Prüfung wenige Tausend Tokens (unter 0,001 USD).
