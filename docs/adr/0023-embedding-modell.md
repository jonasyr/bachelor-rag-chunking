# 0023. Embedding-Modell: text-embedding-3-large mit 3.072 Dimensionen

## Status

Angenommen (13.10.2026; konkretisiert [ADR 0015](0015-tech-stack.md) und [ADR 0016](0016-modell-neutralitaet.md)); Zahlen im Kontext: Korpus `b75d188` (13.10.2026); aktuelle Werte im [Experiment-Protokoll](../reference/experiment-record.md)

## Kontext

- ADR 0016 verlangt, das Embedding-Modell zum Implementierungszeitpunkt festzulegen; offen war `-large` oder `-small`.
- Die aktuellen Embedding-Modelle von OpenAI sind `text-embedding-3-small` und `text-embedding-3-large`, eingeführt
  im Januar 2024; ein Nachfolger ist nicht veröffentlicht (Stand 13.10.2026; `openai2024embeddingmodels`,
  `openai2026te3large`).
- Laut OpenAI erreicht `-large` auf MTEB 64,6 %, `-small` 62,3 %; beide verarbeiten bis 8.192 Tokens je Eingabe und
  nutzen die Kodierung `cl100k_base` wie `src/tokens.py` (`openai2026embeddingsguide`). C3-Chunks haben höchstens
  800 Tokens ([ADR 0021](0021-c3-grenzen.md)).
- Preise: 0,13 USD (`-large`) bzw. 0,02 USD (`-small`) je 1 Mio. Eingabe-Tokens (`openai2026te3large`). Alle Chunks
  zusammen (C1 117.594, C2 142.894, C3 117.594 Tokens) kosten mit `-large` rund 0,05 USD, mit `-small` rund 0,008 USD.
- Das Embedding-Modell ist für alle Strategien identisch ([ADR 0006](0006-nur-chunking-variiert.md)); ein schwächeres
  Modell kann Unterschiede zwischen den Strategien verdecken.

## Entscheidung

Wir werden für Chunks und Fragen aller Strategien `text-embedding-3-large` mit der Standarddimension 3.072 verwenden.
Wir werden das OpenAI-SDK (2.44.0) und Chroma (1.5.9) in `pyproject.toml` pinnen; Modell, Dimension, Stapelgröße und
Preis stehen in [`src/config.py`](../../src/config.py).

## Konsequenzen

- Gut: Das stärkere Modell macht Unterschiede zwischen den Chunking-Strategien besser sichtbar; die Mehrkosten sind
  vernachlässigbar.
- Gut: Gleiche Tokenisierung wie bei Chunking und Relevanz; kein Chunk wird abgeschnitten.
- Neutral: OpenAI bietet keinen datierten Snapshot des Modells; die Reproduzierbarkeit sichert
  [ADR 0024](0024-referenzvektoren-und-exakte-suche.md).
- Schlecht: Lokal betriebene Open-Weight-Modelle erreichen auf MTEB inzwischen höhere Werte; sie scheiden nach ADR 0015
  aus und werden in der Arbeit als Einschränkung genannt.
