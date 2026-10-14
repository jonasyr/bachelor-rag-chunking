# 0005. Drei Chunking-Strategien C1–C3, C4 optional

## Status

Angenommen (D5 im Leitfaden; Quelle: Exposé/Baseline, übernommen); C3-Grenzen konkretisiert durch [ADR 0021](0021-c3-grenzen.md); ergänzt durch [ADR 0026](0026-c3-vergleichbarkeit.md) (Größenkontrolle K1); C4-Bedingung präzisiert durch [ADR 0028](0028-c4-bedingung.md)

## Kontext

- Die Forschungsfrage fragt, wie unterschiedliche Chunking-Strategien die Retrieval- und Antwortqualität beeinflussen (Leitfaden §1).
- Die Strategien stehen in Spannung ([Leitfaden §6](../explanation/research-design.md)): Fixed-size ohne Overlap ist einfach und reproduzierbar, bricht aber Kontext an Grenzen. Mit Overlap verbessert sich die Abdeckung, dafür entstehen mehr Chunks, mehr Redundanz und höhere Kosten. Strukturbasiertes Chunking erhält semantische Einheiten, erzeugt aber uneinheitliche Chunkgrößen.
- Semantisches Chunking (C4) bringt Mehraufwand und eine weitere Modellabhängigkeit (Leitfaden §6).

## Entscheidung

Wir werden drei Strategien vergleichen: C1 fixed-size mit 500 Tokens ohne Overlap, C2 fixed-size mit 500 Tokens und 100 Tokens Overlap, C3 strukturbasiert an Markdown-Überschriften H2/H3 mit höchstens 800 Tokens, wobei große Abschnitte nach Absätzen unterteilt werden.
Wir werden C4 (semantisch) nur umsetzen, wenn die Phasen 1–4 planmäßig laufen.

## Konsequenzen

- Neutral: Die Parameter stehen ausschließlich in [`src/config.py`](../../src/config.py) (`C1_*`, `C2_*`, `C3_MAX_TOKENS`, `STRATEGY_IDS`).
- Schlecht: Lange Vue-Abschnitte (z. B. „Reactivity Fundamentals“) machen die Unterteilungsregel von C3 wichtig; Ober- und Untergrenze sowie die Absatz-Unterteilung sind im Methodikkapitel zu dokumentieren (Leitfaden §6).
- Neutral: Ob C4 kommt, ist offen (Leitfaden §19).
