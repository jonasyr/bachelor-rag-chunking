# 0022. H1-Abschnitte in der Ground Truth nur, wenn die ganze Seite die Antwort ist

## Status

Angenommen (13.10.2026; ergänzt [ADR 0019](0019-korpus-ausschnitt.md) und [ADR 0017](0017-fragenkatalog.md)); der
H1-Anker ist seit [ADR 0042](0042-mdx-umwandlung.md) der Slug des Seitenpfads; Zahlen im Kontext: Korpus `b75d188`
(13.10.2026); aktuelle Werte im [Experiment-Protokoll](../reference/experiment-record.md)

## Kontext

- ADR 0019 bildet `section_id` aus den Ankern der H2/H3-Überschriften. Die Umsetzung erfasst zusätzlich die H1 jeder
  Seite: `sections.jsonl` enthält 52 H1-, 279 H2- und 229 H3-Abschnitte; jeder H1-Abschnitt umfasst die ganze Seite.
- Ein Chunk gilt als relevant, wenn er einen relevanten Abschnitt überlappt (ADR 0019). Ein H1-Abschnitt in
  `relevant_section_ids` machte damit jeden Chunk der Seite relevant, unabhängig von der Strategie.
- Die Ground Truth muss vor der Evaluation feststehen und nachvollziehbar annotiert sein (ADR 0017).

## Entscheidung

Wir werden `section_id` für H1-, H2- und H3-Überschriften bilden.
Wir werden in `relevant_section_ids` H2/H3-Abschnitte annotieren und einen H1-Abschnitt nur dann, wenn die ganze Seite
die Antwort ist; das wird in der Spalte `notes` von `questions.csv` begründet.

## Konsequenzen

- Gut: Relevanzurteile bleiben so eng wie die Frage; Precision@k wird nicht durch ganzseitige Abschnitte aufgebläht.
- Gut: Seitenübergreifende Überblicksfragen lassen sich trotzdem korrekt annotieren.
- Neutral: Die Regel und die Zahl der H1-Annotationen werden im Methodikkapitel genannt.
- Schlecht: Die Grenze „ganze Seite ist die Antwort“ bleibt ein Urteil der annotierenden Person.
