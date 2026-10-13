# 0024. Referenzvektoren speichern und exakt suchen

## Status

Angenommen (13.10.2026; konkretisiert [ADR 0015](0015-tech-stack.md))

## Kontext

- Für `text-embedding-3-large` führt OpenAI nur den Alias selbst als Snapshot; eine datierte Version gibt es nicht
  (`openai2026te3large`). Das Modell hinter dem Namen kann sich ändern, und wiederholte Aufrufe liefern nicht
  zwingend bitgleiche Vektoren.
- Chroma sucht mit einem HNSW-Index approximativ; Standard sind die Metrik `l2` und `ef_search` = 100
  (`chroma2026configure`).
- OpenAI-Vektoren sind auf Länge 1 normiert; Kosinus und Skalarprodukt ergeben dieselbe Rangfolge
  (`openai2026embeddingsguide`).
- Nichtdeterminismus in allem, was in die Evaluation eingeht, verletzt die Code-Review-Regeln (`AGENTS.md`); mit
  höchstens 493 Vektoren je Strategie ist eine exakte Suche billig.

## Entscheidung

Wir werden Chunk- und Fragevektoren einmal erzeugen und mit IDs und Texten speichern (`embeddings_cN.npz`,
`query_embeddings.npz`); die Chroma-Indizes werden nur aus diesen Vektoren gebaut, eine Neuberechnung erfordert das
bewusste Löschen der Datei.
Wir werden Chroma mit der Metrik `cosine` und `ef_search` mindestens in Größe der Sammlung betreiben, jedes Top-k gegen
eine exakte NumPy-Kosinus-Rangfolge prüfen (Toleranz 1e-5), bei Abweichung abbrechen und Gleichstände nach `chunk_id`
ordnen. Telemetrie und Chromas eingebaute Embedding-Funktion bleiben abgeschaltet.

## Konsequenzen

- Gut: Indexaufbau und Retrieval lassen sich ohne API-Aufruf byte-gleich wiederholen; die Top-5 sind nachweislich
  exakt.
- Neutral: Die Vektordateien sind nicht versioniert (`data/` ist ausgeschlossen) und werden für die Archivierung
  (DOI) gesondert gesichert.
- Schlecht: Die zusätzliche Prüfung kostet etwas Laufzeit; bei dieser Korpusgröße vernachlässigbar.
