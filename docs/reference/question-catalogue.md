# Fragenkatalog (Ground Truth)

> Seitentyp: Nachschlagen (reference). Stand: 14.10.2026. Übersicht: [Dokumentation](../README.md).

**Umfang:** 48 Fragen ([ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md), im Rahmen von [ADR 0017](../adr/0017-fragenkatalog.md): 30–60). Der
Fragenkatalog ist eine der wichtigsten Eigenleistungen.

**Fragetypen und Beispiele (Vue.js, englisch):**

| Typ | Wert (`type`) | Anzahl | Beispiel |
|-----|---------------|------:|----------|
| Faktisch | `factual` | 12 | Which lifecycle hooks are available in the Composition API? |
| Prozedural | `procedural` | 12 | How do you define props in a component using `<script setup>`? |
| Konzeptuell | `conceptual` | 12 | What is a composable in Vue and what problem does it solve? |
| Vergleichend | `comparative` | 6 | What is the difference between `ref()` and `reactive()`? |
| Einschränkung/Fehler | `limitation` | 6 | What happens if a child component mutates a prop directly? |

**Konstruktionsklassen (`difficulty`, je 12 Fragen):**

| Wert | Regel |
|------|-------|
| `single` | genau ein relevanter Abschnitt; dessen Hauptinhalt ist die Antwort |
| `multi-section` | mindestens zwei relevante Abschnitte, alle für die Antwort nötig; ein Abschnitt innerhalb eines anderen angegebenen zählt nicht mit |
| `detail` | genau ein Abschnitt; die Antwort ist ein einzelnes Faktum (Referenzantwort höchstens 30 Wörter) |
| `paraphrase` | genau ein Abschnitt; die Frage teilt kein Inhaltswort mit dem Titel des Abschnitts oder seiner Seite |

Wortvergleich, Begründung und Umfang: [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md). **Bereiche:** mindestens 12 Fragen mit einem relevanten Abschnitt
in der API-Referenz, mindestens 3 im Style Guide; eine Frage zählt für jeden Bereich, den sie berührt.

**Felder:** zwei Dateien, Formate in [Datenartefakte und Formate](data-formats.md#fragen-und-ground-truth):

- `questions.csv`: `question_id`, `question`, `type`, `difficulty`, `notes`
- `ground_truth.csv`: `question_id`, `expected_answer`, `relevant_doc_ids`, `relevant_section_ids`

Geprüft mit `src/catalogue.py check`, eingefroren mit `src/catalogue.py freeze` ([ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md)); Ablauf:
[Fragenkatalog erstellen](../how-to/build-the-question-catalogue.md).

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
