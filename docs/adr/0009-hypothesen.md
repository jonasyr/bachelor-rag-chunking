# 0009. Drei geschärfte Hypothesen H1–H3, explorativ

## Status

Angenommen (D9 im Leitfaden; Quelle: Chat, ersetzt die alten H1–H3 der Baseline); Auswertungsart geändert durch
[ADR 0044](0044-statistische-auswertung.md): R@5, MRR und Gesamtwert werden nach vorab festgelegtem Plan konfirmatorisch
getestet; die übrigen p-Werte (H2-Korrelationen) gelten als explorativ, alle übrigen Auswertungen sind deskriptiv
([Nachtrag 0044](0044-statistische-auswertung.md#nachtrag-22102026-konfirmatorische-tests)). Darstellung in der Arbeit:
[Nachtrag 22.10.2026](#nachtrag-22102026-darstellung-in-der-arbeit)

## Kontext

- Die geschärften Hypothesen ersetzen die der Baseline, um die nicht-offensichtlichen Dimensionen zu betonen ([Leitfaden §3](../explanation/research-design.md)).
- Dass strukturbasiertes Chunking naives Chunking offensichtlich schlägt, ist empirisch nicht gesichert (Qu et al. 2025, Leitfaden §4.4).
- Für die statistische Auswertung reicht eine deskriptive Analyse; Signifikanztests sind optional (Leitfaden §12.7).

## Entscheidung

Wir werden drei Hypothesen explorativ untersuchen: H1 starke Baseline, H2 Entkopplung von Retrieval- und Antwortqualität, H3 Wechselwirkung mit dem Fragetyp (Wortlaut in [Leitfaden §4.3](../explanation/research-design.md)).
Wir werden sie deskriptiv auswerten, nicht inferenzstatistisch.

## Konsequenzen

- Neutral: H3 braucht Fragetypen im Fragenkatalog ([ADR 0017](0017-fragenkatalog.md)).
- Neutral: H2 braucht die Korrelation von Retrieval- und Antwortwerten, z. B. als Scatterplot (Leitfaden §14).

## Nachtrag 22.10.2026: Darstellung in der Arbeit

Von Jonas entschieden; der Wortlaut stand zuvor in der Statuszeile. H1–H3 bleiben Leitannahmen. Die Tests aus
[ADR 0044](0044-statistische-auswertung.md) stehen vor dem Hauptlauf fest. Die Statuszeile sagte außerdem: alle p-Werte
gelten als explorativ, keine Hypothese gilt als konfirmatorisch bestätigt. Präzisiert am selben Tag durch den [Nachtrag
zu ADR 0044](0044-statistische-auswertung.md#nachtrag-22102026-konfirmatorische-tests): die Tests von R@5, MRR und
Gesamtwert sind konfirmatorisch, alle übrigen p-Werte explorativ.
