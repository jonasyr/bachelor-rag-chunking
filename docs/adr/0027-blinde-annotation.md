# 0027. Relevanz-Annotation blind vor jedem Retrieval; nachträgliche Ergänzungen nur als Sensitivität

## Status

Angenommen (14.10.2026; präzisiert [ADR 0017](0017-fragenkatalog.md); technisch umgesetzt durch
[ADR 0030](0030-einfrieren-des-fragenkatalogs.md))

## Kontext

- ADR 0017 verlangt, dass Referenzantworten und relevante Quellen vor der Evaluation feststehen; offen blieb, ob das
  schon vor dem Retrieval gilt und wie mit späteren Ergänzungen umzugehen ist.
- In Pilotprobe 2 (16 schwere Fragen) wurde die Annotation nach Sicht der Retrieval-Ergebnisse um drei Abschnitte
  ergänzt; das ist im [Experiment-Protokoll](../reference/experiment-record.md) offengelegt.
- Das Codex-Review von PR #6 zeigte: Ergänzungen nach Sicht der Ergebnisse lassen das Retrieval auf die Relevanzurteile
  zurückwirken; auch offengelegt sind solche Werte keine gültige Evidenz.
- Die blinde Fassung wurde aus der ursprünglichen Datei Byte für Byte wiederhergestellt; ihre SHA-256 ist gleich der im
  ersten API-Lauf protokollierten (`data/pilot/hard/runs.jsonl`, erste Zeile).

## Entscheidung

Wir werden die Relevanz-Annotation (`relevant_section_ids`) vollständig festlegen, bevor irgendein Retrieval-Lauf auf
diesen Fragen stattfindet; das gilt für Pilotproben und für den echten Fragenkatalog.
Wir werden Ergänzungen nach einem Retrieval-Lauf nur als getrennte, ausdrücklich gekennzeichnete Sensitivitätsanalyse
berichten, nie als Hauptwerte.

## Konsequenzen

- Gut: Die Hauptwerte beruhen auf Relevanzurteilen, die das Retrieval nicht kennen konnten; die Ground Truth bleibt
  unabhängig von den Ergebnissen ([ADR 0006](0006-nur-chunking-variiert.md)).
- Gut: Die Pilotwerte sind nach derselben Regel berichtet: blinde Annotation als Hauptwerte, die ergänzte Fassung nur
  als Sensitivität.
- Schlecht: Lücken in der Annotation, die erst das Retrieval sichtbar macht, bleiben in den Hauptwerten; wie stark sie
  die Werte verschieben, zeigt nur die Sensitivitätsanalyse. Das wird in den Limitationen genannt.
- Neutral: Annotationsfehler lassen sich nur vor dem ersten Retrieval-Lauf korrigieren; die Abschnitts-Nachschlageliste
  und die Abdeckungsprüfung ([Plan](../plan.md)) unterstützen die Annotation vorher.
