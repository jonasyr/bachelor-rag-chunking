# 0017. Fragenkatalog: etwa 40 Fragen mit Referenzantworten

## Status

Angenommen (D17 im Leitfaden; Quelle: Exposé/Baseline, übernommen); präzisiert durch [ADR 0027](0027-blinde-annotation.md) (Relevanz-Annotation blind vor jedem Retrieval)

## Kontext

- Referenzantworten und relevante Quellen müssen vor der Evaluation feststehen, um nachträgliche, ergebnisorientierte Anpassungen auszuschließen ([Leitfaden §11](../reference/question-catalogue.md)).
- Der Fragenkatalog ist eine der wichtigsten Eigenleistungen und dauert länger als gedacht (Leitfaden §11, §16).
- Korpus und Embedding-Raum sind englisch (Leitfaden §19).

## Entscheidung

Wir werden etwa 40 Fragen erstellen (mindestens 30, höchstens 60), verteilt auf fünf Typen (faktisch, prozedural, konzeptuell, vergleichend, Einschränkung/Fehler), jeweils mit Referenzantwort und annotierten relevanten Quellen, auf Englisch.

## Konsequenzen

- Neutral: Die Ground Truth wird vor jeder Evaluation finalisiert und danach nicht mehr angepasst.
- Neutral: Die Fragetypen ermöglichen die Prüfung von H3 ([ADR 0009](0009-hypothesen.md)).
- Schlecht: Die Erstellung braucht bewusst eingeplante Zeit (Leitfaden §16).
