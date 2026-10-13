# 0009. Drei geschärfte Hypothesen H1–H3, explorativ

## Status

Angenommen (D9 im Leitfaden; Quelle: Chat, ersetzt die alten H1–H3 der Baseline)

## Kontext

- Die geschärften Hypothesen ersetzen die der Baseline, um die nicht-offensichtlichen Dimensionen zu betonen ([Leitfaden §3](../Ground_Truth_Projektleitfaden.md#3-was-sich-gegenüber-der-ursprünglichen-baseline-geändert-hat)).
- Dass strukturbasiertes Chunking naives Chunking offensichtlich schlägt, ist empirisch nicht gesichert (Qu et al. 2025, Leitfaden §4.4).
- Für die statistische Auswertung reicht eine deskriptive Analyse; Signifikanztests sind optional (Leitfaden §12.7).

## Entscheidung

Wir werden drei Hypothesen explorativ untersuchen: H1 starke Baseline, H2 Entkopplung von Retrieval- und Antwortqualität, H3 Wechselwirkung mit dem Fragetyp (Wortlaut in [Leitfaden §4.3](../Ground_Truth_Projektleitfaden.md#43-hypothesen-verbindlich-explorativ)).
Wir werden sie deskriptiv auswerten, nicht inferenzstatistisch.

## Konsequenzen

- Neutral: H3 braucht Fragetypen im Fragenkatalog ([ADR 0017](0017-fragenkatalog.md)).
- Neutral: H2 braucht die Korrelation von Retrieval- und Antwortwerten, z. B. als Scatterplot (Leitfaden §14).
