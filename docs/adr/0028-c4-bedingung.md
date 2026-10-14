# 0028. C4 nur, wenn der Meilenstein 09.11.2026 (Ground Truth eingefroren) planmäßig erreicht ist

## Status

Angenommen (14.10.2026; präzisiert [ADR 0005](0005-drei-chunking-strategien.md))

## Kontext

- ADR 0005 macht semantisches Chunking (C4) davon abhängig, dass „die Phasen 1–4 planmäßig laufen“. Dieser Phasenplan
  (Juni 2026) gilt nicht mehr; der aktuelle Zeitplan steht im [Plan](../plan.md) und kennt keine Phasen 1–4.
- Der Plan setzt am 09.11.2026 den Meilenstein „Ground Truth eingefroren“ ([ADR 0017](0017-fragenkatalog.md)); seine
  Puffer-Regel streicht zuerst C4, wenn dieser Meilenstein rutscht, nicht die Schreibphase.
- C4 bringt Mehraufwand und eine weitere Modellabhängigkeit (ADR 0005); der Fragenkatalog ist der größte Zeitposten
  vor der Auswertung.

## Entscheidung

Wir werden C4 nur umsetzen, wenn der Meilenstein 09.11.2026 (Ground Truth eingefroren) planmäßig erreicht ist; sonst
entfällt C4.

## Konsequenzen

- Gut: Die Bedingung aus ADR 0005 ist an einem prüfbaren Datum festgemacht statt an einem veralteten Phasenplan.
- Gut: Die Kernstrategien C1–C3 und die Schreibphase haben Vorrang vor einer optionalen Erweiterung.
- Neutral: Ob C4 kommt, entscheidet sich am 09.11.2026; das Ergebnis wird im [Plan](../plan.md) festgehalten.
- Schlecht: Fällt C4 weg, bleibt semantisches Chunking ungeprüft; das wird in den Limitationen genannt.
