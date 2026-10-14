# 0006. Nur das Chunking variiert

## Status

Angenommen (D6 im Leitfaden; Quelle: Exposé, übernommen)

## Kontext

- Ziel der Arbeit ist, den Einfluss der Chunking-Strategie auf Retrieval- und Antwortqualität isoliert zu bestimmen (Leitfaden §1).
- Die interne Validität wird über die Konstanthaltung aller anderen Parameter abgesichert ([Leitfaden §13](../explanation/research-design.md)).

## Entscheidung

Wir werden nur die Chunking-Strategie variieren.
Wir werden Korpus/Snapshot, Sprache (Englisch), Embedding-Modell, LLM, Temperatur 0, top-k 5, Prompt, Fragenset, Rubrik, Vector Store, Retrieval-Art (Dense) und Antwortformat für alle Strategien konstant halten ([Leitfaden §6](../explanation/research-design.md)).

## Konsequenzen

- Gut: Unterschiede in den Ergebnissen lassen sich der Chunking-Strategie zuordnen (Leitfaden §13).
- Schlecht: Jede zusätzliche Variation (z. B. top-k) wäre eine zweite unabhängige Variable und ist ausgeschlossen ([ADR 0014](0014-temperatur-und-topk.md)).
- Schlecht: Die externe Validität bleibt begrenzt, da nur ein Korpus untersucht wird (Leitfaden §13).
