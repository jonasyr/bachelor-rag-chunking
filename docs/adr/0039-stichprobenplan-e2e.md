# 0039. Stichprobenplan und Bereichsquoten auf e2e

## Status

Angenommen (18.10.2026; ersetzt die Slotzahlen von [ADR 0031](0031-stichprobenplan-und-ki-durchsicht.md) und die
Bereichsuntergrenzen von [ADR 0029](0029-fragetypen-und-konstruktionsklassen.md); folgt aus
[ADR 0038](0038-korpus-e2e.md)); „nie getunt“ (Kontext) steht nicht in ADR 0031, sondern im Kommentar zu
`config.CATALOGUE_SEED` (Commit b57fc65, 15.10.2026)

## Kontext

- Mit dem Korpuswechsel (ADR 0038) gibt es 15 Bereiche statt drei: die Gruppen der Navigation `docs.json`
  ([Korpus](../reference/corpus.md#bereiche)). Die Vue-Quoten (12 API, 3 Style Guide, 33 Guide) folgten den
  Tokenanteilen; der größte Bereich (Guide, 71 %) hatte keine Untergrenze und war Puffer.
- Auf e2e hat kein Bereich eine solche Mehrheit: Project 24,4 %, Test API 14,8 %, alle übrigen unter 9 %; Examples
  (eine Seite, 547 Tokens) 0,2 %.
- Der Vue-Plan (`catalogue_plan.csv`, gezogen 14.10.2026) war versioniert, aber nie benutzt: Es gab noch keine Frage.
- ADR 0031 legt den Seed als nie getunt fest; ein neuer Seed erlaubte, eine Ziehung auszuwählen.

## Entscheidung

Wir werden die 48 Slots nach dem Tokenanteil der Bereiche nach dem Preprocessing verteilen, jeder Bereich mindestens
einen Slot, die übrigen 33 nach größtem Rest über die Anteile oberhalb eines Slots: Get started 2, Platforms 2,
Features 2, Models and agents 2, Run in CI 2, Hosted browsers and devices 2, Extend 1, Deep dive 3, Migrate 4,
Test API 7, Project 12, Web 2, Mobile 2, Engine contract 4, Examples 1.
Wir werden je Bereich so viele Reserveabschnitte ziehen wie Slots und in jedem Bereich mindestens so viele Fragen mit
einem relevanten Abschnitt verlangen wie Slots (eine Frage zählt für jeden berührten Bereich, ADR 0029).
Wir werden den Seed `20261014`, die Ziehung, die Sprunggründe und die KI-Durchsicht aus ADR 0031 unverändert
übernehmen; in den Stoppwörtern ersetzt `e2e` die Vue-Einträge `v` und `vue`.
Wir werden den Vue-Plan unverändert nach `data/evaluation/archive_vue/` verschieben und den e2e-Plan einmal unter dem
bisherigen Pfad ziehen ([Experiment-Protokoll](../reference/experiment-record.md#stichprobenplan-e2e)).

## Konsequenzen

- Positiv: Jeder Bereich kommt im Katalog vor, die Verteilung folgt derselben Regel wie bei Vue und ist in einem Satz
  begründbar; die Zahlen stehen als Literale in `src/config.py` und verschieben sich nicht mit dem Korpus.
- Negativ: Examples bekommt einen Slot für eine kleine Seite; eine Frage, die ihren Bereich verlässt, muss umgeschrieben
  oder anders annotiert werden, weil kein Bereich als Puffer dient.
- Neutral: Die Vorgabe „nie überschreiben“ bleibt erhalten: Der Vue-Plan ist archiviert, nicht ersetzt.
