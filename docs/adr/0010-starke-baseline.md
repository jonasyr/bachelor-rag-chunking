# 0010. Fixed-size mit Overlap ist eine starke Baseline

## Status

Angenommen (D10 im Leitfaden; Quelle: Chat, ergänzt die Baseline)

## Kontext

- Qu, Bao & Tu (2025) zeigen, dass semantisch oder strukturell motiviertes Chunking größenbasiertes Chunking nicht konsistent übertrifft und der Mehraufwand oft nicht gerechtfertigt ist ([Leitfaden §4.4](../explanation/research-design.md#warum-das-thema-nicht-trivial-ist)).
- Ohne diese Einordnung könnte die Arbeit als trivialer Vergleich gelten (Leitfaden §3).

## Entscheidung

Wir werden C2 (fixed-size mit Overlap) ausdrücklich als leistungsfähige Baseline behandeln, nicht als Strohmann.

## Konsequenzen

- Gut: Die Arbeit ist gegen den Vorwurf der Trivialität abgesichert (Leitfaden §3).
- Neutral: Der Erkenntnisgewinn liegt in Effektgröße, Kosten, Metrikabhängigkeit, Retrieval-Antwort-Entkopplung und Fragetyp-Effekten (Leitfaden §4.4); H1 formuliert das ([ADR 0009](0009-hypothesen.md)).
