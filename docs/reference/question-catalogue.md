# Fragenkatalog (Ground Truth)

> Seitentyp: Nachschlagen (reference). Stand: 14.10.2026. Übersicht: [Dokumentation](../README.md).

**Umfang:** ca. 40 Fragen (Minimum 30, optimal 40–50, nicht über 60; [ADR 0017](../adr/0017-fragenkatalog.md)). Der
Fragenkatalog ist eine der wichtigsten Eigenleistungen.

**Fragetypen und Beispiele (Vue.js, englisch):**

| Typ | Anzahl | Beispiel |
|-----|------:|----------|
| Faktisch | 10 | Which lifecycle hooks are available in the Composition API? |
| Prozedural | 10 | How do you define props in a component using `<script setup>`? |
| Konzeptuell | 10 | What is a composable in Vue and what problem does it solve? |
| Vergleichend | 5 | What is the difference between the Options API and the Composition API? |
| Einschränkung/Fehler | 5 | What happens if a child component mutates a prop directly? |

**Felder:** zwei Dateien, Formate in [Datenartefakte und Formate](data-formats.md#fragen-und-ground-truth):

- `questions.csv`: `question_id`, `question`, `type`, `difficulty`, `notes`
- `ground_truth.csv`: `question_id`, `expected_answer`, `relevant_doc_ids`, `relevant_section_ids`

Die erlaubten Werte von `type` und `difficulty` sind noch offen ([Plan](../plan.md)).

## Regeln für Annotation und Aufbau

- Referenzantworten und relevante Abschnitte stehen fest, bevor irgendein Retrieval auf den Fragen läuft; spätere
  Ergänzungen nur als gekennzeichnete Sensitivitätsanalyse ([ADR 0017](../adr/0017-fragenkatalog.md),
  [ADR 0027](../adr/0027-blinde-annotation.md)).
- H2/H3-Abschnitte annotieren, einen H1-Abschnitt nur, wenn die ganze Seite die Antwort ist
  ([ADR 0022](../adr/0022-h1-abschnitte-in-ground-truth.md)).
- Relevante Abschnitte im ganzen Korpus suchen, auch in der API-Referenz, nicht nur auf der naheliegenden Seite.
- Einen festen Anteil schwerer Fragen vorsehen: Antworten aus mehreren Abschnitten oder Seiten, Detailfragen zu kurzen
  Abschnitten, Paraphrasen ohne die Begriffe der Überschrift. Einfache Fragen mit genau einem passenden Abschnitt
  trennen die Strategien nicht (Deckeneffekt).
- MRR und Recall@5 neben Hit@5 berichten; Hit@5 allein unterscheidet die Strategien kaum.

Die letzten drei Regeln folgen aus den Pilotproben
([Experiment-Protokoll](experiment-record.md#pilotproben-auf-dem-erweiterten-korpus-14102026)).
