# 0028. C4 nur, wenn der Meilenstein 09.11.2026 (Ground Truth eingefroren) planmäßig erreicht ist

## Status

Angenommen (14.10.2026; präzisiert [ADR 0005](0005-drei-chunking-strategien.md)); Auswertung einer C4 festgelegt im
[Nachtrag 22.10.2026](#nachtrag-22102026-c4-nur-deskriptiv) (Jonas)

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

## Nachtrag 22.10.2026: C4 nur deskriptiv

Von Jonas entschieden; ändert die Bedingung oben nicht. Kommt C4, wird sie nur beschreibend berichtet: außerhalb des
Testplans von [ADR 0044](0044-statistische-auswertung.md) (Friedman und Wilcoxon bleiben bei C1–C3), ohne Zweitbewertung
([ADR 0046](0046-zweitbewertung.md)) und ohne RAGAS ([ADR 0047](0047-ragas-als-triangulation.md)). Diese ADRs und die
Invarianten in `AGENTS.md` bleiben damit unverändert.
