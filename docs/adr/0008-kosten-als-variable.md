# 0008. Kosten/Effizienz als eigene abhängige Variable

## Status

Angenommen (D8 im Leitfaden; Quelle: Chat, ergänzt die Baseline)

## Kontext

- Die Strategien unterscheiden sich im Aufwand: C2 erzeugt mehr Chunks, mehr Redundanz und höhere Kosten ([Leitfaden §6](../explanation/research-design.md)).
- Unterfrage 4 fragt nach Trade-offs zwischen Chunk-Größe, Redundanz, Retrieval-Präzision, Kosten und Antwortqualität (Leitfaden §1).
- Der Erkenntnisgewinn liegt unter anderem in Effektgröße und Kosten, nicht nur darin, welche Strategie gewinnt (Leitfaden §4.4).

## Entscheidung

Wir werden je Strategie Chunk-Anzahl, Indexgröße sowie Prompt- und Completion-Tokens erfassen ([Leitfaden §12.4](../reference/evaluation.md)).

## Konsequenzen

- Neutral: Qualitätsunterschiede werden den Kosten gegenübergestellt („X % bessere Retrieval-Qualität bei Y× Kosten“, Leitfaden §12.4).
- Neutral: `generated_answers.csv` enthält dafür die Spalten `prompt_tokens` und `completion_tokens` (Leitfaden §10).
