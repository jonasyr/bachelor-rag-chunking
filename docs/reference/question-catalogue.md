# Fragenkatalog (Ground Truth)

> Seitentyp: Nachschlagen (reference). Stand: 19.10.2026. Übersicht: [Dokumentation](../README.md).

**Umfang:** 48 Fragen ([ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md), im Rahmen von [ADR 0017](../adr/0017-fragenkatalog.md): 30–60). Der
Fragenkatalog ist eine der wichtigsten Eigenleistungen.

**Fragetypen (englisch):**

| Typ | Wert (`type`) | Anzahl | Form (Platzhalter) |
|-----|---------------|------:|----------|
| Faktisch | `factual` | 12 | Which … does … support? |
| Prozedural | `procedural` | 12 | How do I …? |
| Konzeptuell | `conceptual` | 12 | What is … and why …? |
| Vergleichend | `comparative` | 6 | What is the difference between … and …? |
| Einschränkung/Fehler | `limitation` | 6 | What happens if …? |

Die Platzhalter zeigen nur die Form; Beispiele aus dem e2e-Korpus trägt Jonas mit den ersten Katalogfragen nach.

**Konstruktionsklassen (`difficulty`, je 12 Fragen):**

| Wert | Regel |
|------|-------|
| `single` | genau ein relevanter Abschnitt; dessen Hauptinhalt ist die Antwort |
| `multi-section` | mindestens zwei relevante Abschnitte, alle für die Antwort nötig; ein Abschnitt innerhalb eines anderen angegebenen zählt nicht mit |
| `detail` | genau ein Abschnitt; die Antwort ist ein einzelnes Faktum (Referenzantwort höchstens 30 Wörter) |
| `paraphrase` | genau ein Abschnitt; die Frage teilt kein Inhaltswort mit dem Titel des Abschnitts oder seiner Seite |

Wortvergleich, Begründung und Umfang: [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md). **Bereiche:** je Bereich
mindestens so viele Fragen mit einem relevanten Abschnitt darin, wie der Bereich Slots hat (`config.AREA_MIN_QUESTIONS`,
[Konfiguration](configuration.md#fragenkatalog); Zahlen je Bereich: [Korpus](corpus.md#bereiche);
[ADR 0039](../adr/0039-stichprobenplan-e2e.md)); eine Frage zählt für jeden Bereich, den sie berührt.

**Felder:** zwei Dateien, Formate in [Datenartefakte und Formate](data-formats.md#fragen-und-ground-truth):

- `questions.csv`: `question_id`, `question`, `type`, `difficulty`, `notes`
- `ground_truth.csv`: `question_id`, `expected_answer`, `relevant_doc_ids`, `relevant_section_ids`

**Auswahl der Themen:** Je Slot zieht ein fester Stichprobenplan einen Ausgangsabschnitt (nach Textlänge, Seed
`config.CATALOGUE_SEED`) und eine Konstruktionsklasse; Jonas wählt den Typ und schreibt Frage, Antwort und Annotation.
Sprünge nur mit festem Grund, KI-Vorschläge werden protokolliert und von Jonas entschieden ([ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md));
Slots und Reserve je Bereich nach [ADR 0039](../adr/0039-stichprobenplan-e2e.md) (`config.CATALOGUE_AREA_SLOTS`,
`config.CATALOGUE_RESERVE`).

Die Fragen werden mit `src/catalogue.py screen` ohne Kontext beantwortet ([ADR 0040](../adr/0040-closed-book-pruefung.md)),
mit `src/catalogue.py check` geprüft und mit `src/catalogue.py freeze` eingefroren
([ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md)); Ablauf:
[Fragenkatalog erstellen](../how-to/build-the-question-catalogue.md).

## Regeln für Annotation und Aufbau

- Referenzantworten und relevante Abschnitte stehen fest, bevor irgendein Retrieval auf den Fragen läuft; spätere
  Ergänzungen nur als gekennzeichnete Sensitivitätsanalyse ([ADR 0017](../adr/0017-fragenkatalog.md),
  [ADR 0027](../adr/0027-blinde-annotation.md)).
- H2/H3-Abschnitte annotieren, einen H1-Abschnitt nur, wenn die ganze Seite die Antwort ist
  ([ADR 0022](../adr/0022-h1-abschnitte-in-ground-truth.md)).
- Relevante Abschnitte im ganzen Korpus suchen, auch im Tab Reference, nicht nur auf der naheliegenden Seite.
- Einen festen Anteil schwerer Fragen vorsehen: Antworten aus mehreren Abschnitten oder Seiten, Detailfragen zu kurzen
  Abschnitten, Paraphrasen ohne die Begriffe der Überschrift. Einfache Fragen mit genau einem passenden Abschnitt
  trennen die Strategien nicht (Deckeneffekt).

Die letzten beiden Regeln folgen aus den Pilotproben auf dem Vue-Korpus
([Experiment-Protokoll](experiment-record.md#pilotproben-auf-dem-erweiterten-korpus-14102026)); welche Retrieval-Metriken
deshalb neben Hit@5 berichtet werden, steht in [Evaluation](evaluation.md#retrieval-evaluation).

**Closed-Book-Prüfung.** Jede Frage wird ohne Kontext beantwortet; trifft die Antwort den Kernpunkt der
Referenzantwort, ist die Frage retrieval-unabhängig (`hit`) und bleibt im Katalog, markiert in
`closed_book_screen.csv` (Spalte `core_point`). Mindestens `ceil(2/3 × 48)` = 32 Fragen müssen retrieval-abhängig
sein (`config.CLOSED_BOOK_MIN_DEPENDENT_SHARE`); eingefroren wird erst, wenn jede Frage zu ihrem aktuellen Fragetext
beantwortet und zu ihrer aktuellen Referenzantwort beurteilt ist ([ADR 0040](../adr/0040-closed-book-pruefung.md)).
