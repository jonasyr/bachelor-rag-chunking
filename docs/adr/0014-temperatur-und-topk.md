# 0014. Temperatur 0 und top-k 5 konstant

## Status

Angenommen (D14 im Leitfaden; Quelle: Baseline, übernommen)

## Kontext

- Temperatur 0 ist Teil der Absicherung von interner Validität und Reliabilität ([Leitfaden §13](../explanation/research-design.md)).
- Würde top-k zusätzlich variiert, entstünde eine zweite unabhängige Variable ([Leitfaden §8](../reference/tooling.md)).

## Entscheidung

Wir werden `LLM_TEMPERATURE = 0.0` und `TOP_K = 5` in [`src/config.py`](../../src/config.py) setzen und für alle Strategien gleich halten.

## Konsequenzen

- Gut: Antworten sind möglichst reproduzierbar, Unterschiede bleiben dem Chunking zuordenbar ([ADR 0006](0006-nur-chunking-variiert.md)).
- Schlecht: Der Einfluss von top-k wird nicht untersucht.
