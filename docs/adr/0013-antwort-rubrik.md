# 0013. Antwort-Rubrik: Skala 0–2, fünf Kriterien, gleich gewichtet

## Status

Angenommen (D13 im Leitfaden; Quelle: Exposé/Baseline, übernommen; blinde Bewertung ergänzt durch
[ADR 0032](0032-blinde-rubrik-bewertung.md); Stufen operationalisiert durch [ADR 0035](0035-regelbasierte-bewertung.md);
ergänzt durch [ADR 0044](0044-statistische-auswertung.md)); die optionale Normierung auf 0–100 ist nicht umgesetzt,
der Gesamtwert bleibt auf 0–2 (`total_score`)

## Kontext

- Unterfrage 3 fragt nach Korrektheit, Vollständigkeit, Quellenbezug und Halluzinationsfreiheit der Antworten (Leitfaden §1).
- Es wird keine priorisierte Domäne (Medizin, Recht, Sicherheit) untersucht; gleiche Gewichte sind leichter zu begründen als komplexe Gewichtungen ([Leitfaden §12.2](../reference/evaluation.md)).

## Entscheidung

Wir werden Antworten nach fünf Kriterien bewerten: Korrektheit, Vollständigkeit, Quellenbezug, Halluzinationsfreiheit und Verständlichkeit, je auf einer Skala von 0 bis 2 und gleich gewichtet.

## Konsequenzen

- Neutral: Der Gesamtscore ist der Mittelwert der fünf Kriterien (0–2), optional normiert auf 0–100 (Leitfaden §12.2).
- Neutral: Umsetzung in [`src/evaluate_answers.py`](../../src/evaluate_answers.py) und `scores.csv`; die Kriterien stehen als `RUBRIC_CRITERIA` in [`src/config.py`](../../src/config.py).
