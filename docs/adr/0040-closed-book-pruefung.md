# 0040. Closed-Book-Prüfung des Fragenkatalogs

## Status

Angenommen (19.10.2026; füllt die offene Frage aus [ADR 0038](0038-korpus-e2e.md), wer den Kernpunkt beurteilt; ergänzt
[ADR 0017](0017-fragenkatalog.md), [ADR 0030](0030-einfrieren-des-fragenkatalogs.md) und [ADR 0031](0031-stichprobenplan-und-ki-durchsicht.md); Prompt auch
für K0: [ADR 0041](0041-kontrolle-k0.md)); die Blockgröße 8 (Kontext) steht nicht in ADR 0031, sondern in
[plan.md](../plan.md) und [Fragenkatalog erstellen](../how-to/build-the-question-catalogue.md)

## Kontext

- ADR 0038 verlangt, jede Katalogfrage vor dem Einfrieren ohne Kontext beantworten zu lassen; trifft die Antwort den
  Kernpunkt, ist die Frage retrieval-unabhängig. Mindestens zwei Drittel müssen retrieval-abhängig sein.
- In der Diagnose beantwortete das Antwortmodell 1 von 20 e2e-Fragen ohne Dokumentation richtig. Bei so seltenen
  Treffern schwankt ein Übereinstimmungsmaß wie κ stark: eine abweichende Beurteilung bewegt es zwischen 1 und 0.
- Der RAG-Prompt bindet das Modell an die Ausschnitte; ohne Ausschnitte lehnt es fast immer ab und zeigt nicht, was es
  weiß.
- Der Katalog entsteht in Blöcken von 8 Fragen mit einer KI-Durchsicht nach jedem Block (ADR 0031).

## Entscheidung

Wir werden nach jedem Block mit `catalogue.py screen` jede neue oder geänderte Frage vom Antwortmodell (Modell,
Temperatur 0, Seed und Token-Limit der Antwortgenerierung) mit einem eigenen Closed-Book-Prompt beantworten lassen;
derselbe Prompt dient der Kontrolle K0 ([Prompts](../reference/prompts.md#closed-book-prompt-prüfung-und-k0)).
Wir werden die Antworten in `data/evaluation/closed_book_screen.csv` ablegen; Jonas beurteilt im Editor-Tab
„Closed-book“, ob eine Antwort den Kernpunkt seiner Referenzantwort vollständig trifft (`hit`) oder nicht (`miss`,
auch bei teilweise richtig). Der Editor ruft die API nie auf; beim Schreiben sind keine Modellantworten sichtbar.
Wir werden eine `hit`-Frage im Katalog lassen und markieren; Jonas darf sie umformulieren, dann fragt `screen` neu.
Wir werden das Einfrieren verweigern, solange eine Frage auf ihrem aktuellen Text ungeprüft oder unbeurteilt ist oder
mehr als 16 von 48 Fragen `hit` sind (`config.CLOSED_BOOK_MIN_DEPENDENT_SHARE`); der Freeze-Record hält die Zahlen fest.

## Konsequenzen

- Positiv: Der Katalog misst nachweislich überwiegend Retrieval; die Markierung erlaubt, die Ergebnisse getrennt für
  retrieval-abhängige und -unabhängige Fragen zu berichten. Prüfung und K0 messen dieselbe Bedingung.
- Negativ: Jonas beurteilt Antworten auf seine eigenen Fragen, nicht blind; das steht als Grenze in der Arbeit. Ein
  LLM-Richter mit κ-Prüfung wurde verworfen (instabil bei seltenen Treffern, kaum Zeitersparnis bei 48 Fragen).
- Neutral: Antworten ohne Kontext dürfen zum Umformulieren führen. Sie enthalten keine Information über Retrieval,
  Chunks oder Strategien; der Vergleich C1–C3 bleibt unverzerrt (ADR 0017, 0027). Ein gezieltes Ersetzen aller
  bekannten Fragen ist nicht verlangt, damit der Katalog nicht auf abseitige Details gefiltert wird.
- Neutral: Jeder Lauf steht mit Modell, Tokens und Kosten in `generation_runs.jsonl` (Schritt `closed_book_screen`).
