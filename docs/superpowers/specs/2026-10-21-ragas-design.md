# RAGAS-Lauf (ADR 0047) — Design

Stand 21.10.2026; von Jonas freigegeben am 21.10.2026 (Entscheidungen in ADR 0047 und in diesem Gespräch).

## Zweck

RAGAS liefert eine zweite, automatische Sicht auf die 144 Antworten C1–C3 neben der regelbasierten Bewertung
(ADR 0007, 0047). Die Arbeit berichtet RAGAS beschreibend und vor allem, wie gut es mit der eigenen Bewertung und den
Retrieval-Metriken übereinstimmt; eine Abweichung ist selbst ein Befund. RAGAS ist nie Grundlage einer Aussage über
die Strategien und fließt nie zurück.

## Ziele

- Ein neuer Schritt `src/ragas_eval.py` bewertet jede Antwort C1–C3 mit vier Metriken: Faithfulness, Response
  Relevancy, Context Precision und Context Recall (beide mit Referenz).
- Er läuft auf dem Hauptkatalog und auf Pilot-Sets (`--set DIR`), wie die übrigen Schritte.
- `analyse.py` schreibt daraus zwei Tabellen für Kapitel 4.2.
- Zwei gleiche Läufe auf dem Pilot e2e zeigen, wie stabil das Richtermodell ist.

## Nicht-Ziele

- Kein RAGAS für K0 (ohne Kontext entfallen drei Metriken) und K1 (ohne Antworten).
- Keine Tests, keine p-Werte, keine Abbildung zu RAGAS (Jonas, 21.10.2026: nur zwei Tabellen).
- Keine Testsatz-Generierung und keine weiteren RAGAS-Metriken (Factual Correctness u. a.).
- Kein Neubewerten: RAGAS ändert `scores.csv`, Kernpunkte, Fragen, Referenzen und Relevanzurteile nie (ADR 0017).

## Anti-Ziele (wäre ein Fehlschlag, auch wenn es läuft)

- RAGAS bewertet andere Passagen als die, die das Antwortmodell gesehen hat.
- Ein Teil der Antworten bekommt Werte, ein Teil nicht, und das fällt nicht auf (fehlende oder NaN-Werte werden
  nicht gezählt und berichtet).
- Ein zweiter Lauf überschreibt still einen gespeicherten Lauf.
- Ein Test erreicht die OpenAI-API.

## Entscheidungen (von Jonas)

- Richtermodell `gpt-6-sol` (nicht das Antwortmodell `gpt-6-luna`), `temperature = 0`, fester `seed`,
  `reasoning_effort = "none"` wie beim Antwortmodell (ADR 0033); Embeddings für Response Relevancy:
  `text-embedding-3-large` (ADR 0023).
- Die vier Metriken oben (ADR 0047); Response Relevancy mit `strictness = 1` statt des RAGAS-Standards 3: bei
  `temperature = 0` und festem Seed stellt RAGAS dreimal denselben Prompt, die drei Fragen wären gleich (Review von
  Task 3; Jonas, 21.10.2026, ändert seine frühere Wahl von 3).
- NaN nach Definition der Metrik (z. B. Faithfulness ohne prüfbare Aussage bei einer ablehnenden Antwort, Context
  Recall ohne Zuordnung) ist ein gültiges Ergebnis: leere Zelle plus Grund, gezählt je Metrik und Strategie und in den
  Tabellen genannt. RAGAS 0.4.3 gibt zu einem solchen NaN keinen Grund an (Faithfulness, Context Recall, Context
  Precision; Fehler lösen dort eine Ausnahme aus); der Bewerter trägt darum je Metrik einen festen Grund ein, der die
  Fälle der gepinnten Version nennt (Jonas, 21.10.2026). Response Relevancy gibt im nichtssagenden Fall 0, nicht NaN. Mittelwerte über die vorhandenen Werte; Kendalls W und paarweise r nur über Fragen mit Wert in
  allen drei Strategien; Spearmans ρ ohne das betroffene Paar.
- Das Richtermodell wird wie das Antwortmodell überwacht (ADR 0033): meldet die API im Lauf mehr als ein Modell oder
  mehr als einen `system_fingerprint`, oder ändert sich der Erstellungszeitpunkt des Modellobjekts zwischen Beginn
  und Ende, wird nichts geschrieben.
- Lauf erst nach der regelbasierten Bewertung C1–C3; einmal ausgeführt, gespeichert, nie überschrieben (ADR 0047).
- Pilot e2e: zwei gleiche Läufe mit echten API-Aufrufen (wenige Cent); der Vergleich beider Läufe ist die
  Stabilitätszahl für die Arbeit. Der Hauptlauf bleibt ein Lauf.
- Bericht: eine Tabelle mit den vier Mittelwerten je Strategie und Effektstärken (wie die Nebenmetriken, ADR 0044,
  ohne p-Werte) und eine Tabelle mit Spearmans ρ je Metrik und Gegenstück, beide in Kapitel 4.2.

## Eingaben je Antwort

- `user_input`: die Frage aus `questions.csv`.
- `response`: die Antwort aus `generated_answers.csv`.
- `retrieved_contexts`: die Texte der Chunks aus der Spalte `sources` derselben Zeile, in dieser Reihenfolge, jeder
  Chunk als eigenes Element (genau die Passagen, die das Antwortmodell sah; `prompt.context` nummeriert sie nur).
- `reference`: `expected_answer` aus `ground_truth.csv` (eingefroren).

## Schutzregeln (wie bei den übrigen Schritten)

- Hauptkatalog: nur eingefroren (`require_frozen`), nur wenn `generated_answers.csv` die Ausgabe des letzten
  `generate`-Laufs ist und ein aktueller `summarise`-Eintrag über C1–C3 existiert (die regelbasierte Bewertung ist
  abgeschlossen). Pilot-Sets dürfen den `summarise`-Eintrag nicht haben (ihre Bewertungen entstanden unter einer
  älteren Regelversion, ADR 0043/0044); das wird gemeldet, nicht verweigert.
- Alles wird vor dem ersten API-Aufruf geprüft.
- Alles oder nichts: Scheitert eine Antwort (Fehler nach den Wiederholungen des Clients, Wert außerhalb 0–1, NaN
  einer Metrik ohne festen Grund, Wechsel des Richtermodells), wird nichts geschrieben. Ein NaN nach Definition der
  Metrik ist kein Fehler (siehe Entscheidungen).
- Ausgabedatei existiert schon: Abbruch, wie bei `generate.py` (bewusst löschen, um neu zu laufen). Für den zweiten
  Pilotlauf ein eigener Ausgabename (siehe unten), kein Überschreiben.
- Laufeintrag im Laufprotokoll der Generierung (`generation_runs.jsonl`, im Set `runs.jsonl`): Schritt `ragas`,
  Strategie `C1,C2,C3`, Datum, Richtermodell (konfiguriert und von der API gemeldet), Embedding-Modell,
  RAGAS-Version, Seed, `strictness`, Prüfsummen der Eingaben (Antworten, `retrieved_results.csv`, Fragen, Ground
  Truth, Chunk-Dateien, im Hauptkatalog auch `scores.csv`, damit der Lauf an das `summarise` gebunden ist, nach dem er
  lief) und der Ausgabe, Anzahl NaN je Metrik, Tokens und Kosten getrennt nach Richter und Embeddings.
- Alle Parameter (Modelle, Seed, Temperatur, Metrikliste, Dateinamen, Preise) stehen nur in `src/config.py`;
  `ragas` wird in `pyproject.toml` exakt gepinnt (heute im Lockfile 0.4.3, deklariert nur `>=0.1.0`).

## Ausgaben

- `data/evaluation/ragas_scores.csv` (im Set: `DIR/ragas_scores.csv`): eine Zeile je Frage und Strategie C1–C3,
  Spalten `question_id`, `strategy`, `faithfulness`, `response_relevancy`, `context_precision`, `context_recall`
  (Werte 0–1, feste Nachkommastellen aus `config`, leer bei NaN nach Definition der Metrik) und `nan_reasons`
  (Metrik und Grund je leerer Zelle, sonst leer), sortiert nach Frage und Strategie.
- Versioniert (Primärdaten, die kein Lauf exakt wiederholt, wie die Antworten; ADR 0033, 0045); Format und Status in
  `docs/reference/data-formats.md` nachtragen.
- Zweiter Pilotlauf: eine Option (z. B. `--repeat`) schreibt `ragas_scores_repeat.csv` mit eigenem Laufeintrag
  unter dem Schritt `ragas_repeat` (Entscheidung Claude: so bleibt der letzte `ragas`-Eintrag der von
  `ragas_scores.csv`, und `require_run` findet beide Läufe getrennt); nur für Pilot-Sets erlaubt.

## Auswertung in `analyse.py`

- `analysis_data` lädt `ragas_scores.csv`, wenn vorhanden, und prüft sie gegen ihren `ragas`-Eintrag (Ausgabe und
  Eingaben, wie bei den übrigen Ergebnisdateien); fehlt sie, entfallen die Tabellen mit Hinweis in `notes`.
- Tabelle `ragas`: vier Mittelwerte je Strategie, Kendalls W und paarweise r mit Median-Differenz (deskriptiv,
  `stats.effect_sizes`), IU-Format wie die übrigen Tabellen (kurzer Titel, `\source{Eigene Darstellung. …}`).
- Tabelle `ragas_agreement`: Spearmans ρ und n je Antwort (gepoolt über C1–C3 und je Strategie) für
  - Faithfulness ~ Quellenbezug (`groundedness`) und ~ Halluzinationsfreiheit (`no_hallucination`) aus `scores.csv`;
  - Response Relevancy ~ `answers_question` (yes = 1, no = 0) aus `scoring_checks.csv`, über `scoring_key.csv`
    entblindet;
  - Context Precision ~ P@5, Context Recall ~ R@5 (Hauptregel) aus `retrieval_scores.csv`.
  Das gepoolte ρ ohne p-Wert (jede Frage dreifach, wie in `correlation`). Ist eine Seite konstant (z. B. alle
  `answers_question` = yes), steht „nicht bestimmbar“ statt einer Zahl (`stats.spearman` meldet das schon).
- `analysis.json` bekommt beide Blöcke.
- Kapitel 4.2 der Arbeit (PaperLab, `sections/04_ergebnisse.tex`) bindet beide Tabellen über `\ergebnistabelle` ein.

## Stabilität (Pilot)

- Nach den zwei Pilotläufen: je Metrik mittlere absolute Differenz und Spearmans ρ zwischen Lauf 1 und Lauf 2, dazu
  der Anteil gleicher Werte; ins Experiment-Protokoll und als Zahl für die Grenzen der Arbeit. Ob das ein eigener
  Befehl oder Teil von `analyse.py --set` ist, entscheidet der Plan.

## Tests

- Kein Test erreicht die API: der Richter und die Embeddings werden injiziert (Fake), wie `completer` in
  `generate.py`.
- Abgedeckt sein müssen: Kontext = genau die `sources` in Reihenfolge; Abbruch vor jedem Aufruf bei nicht
  eingefrorenem Katalog, veralteten Antworten, fehlendem `summarise` (Hauptkatalog), vorhandener Ausgabe; nichts
  geschrieben bei einem Fehler, NaN oder Wert außerhalb 0–1 in irgendeiner Antwort; Laufeintrag mit Prüfsummen;
  `--repeat` nur für Pilot-Sets; Tabellen und Übereinstimmung auf synthetischen Daten (auch konstante Seite).

## Entscheidungen von Claude (zur Prüfung durch Jonas)

- Schritt `ragas_repeat` für den zweiten Pilotlauf (siehe Ausgaben).
- `retrieved_results.csv` und (Hauptkatalog) `scores.csv` unter den Prüfsummen des Laufeintrags (siehe Schutzregeln).
- Jeder Chunk ein eigenes Element von `retrieved_contexts`, ohne die Nummerierung von `prompt.context`.

## Dem Planer überlassen

- Wie RAGAS 0.4.x konkret aufgerufen wird (Collections-API, `llm_factory`, `embedding_factory`, asynchron oder
  nicht) und ob `temperature`, `seed` und `reasoning_effort` dort durchgereicht werden; geht das nicht, ist das vor
  der Umsetzung zu melden.
- Wie Tokens erfasst werden (z. B. über den OpenAI-Client), solange Richter- und Embedding-Kosten im Laufeintrag
  stehen.
- Nebenläufigkeit, Wiederholungen und Zeitlimits des Clients.
- Ob die Option für den zweiten Lauf `--repeat` heißt.

## Doku

- ADR 0047 bleibt gültig; `docs/reference/evaluation.md` (Abschnitt Triangulation: „Code dafür gibt es noch nicht“
  ersetzen), `data-formats.md` (neue Datei, Laufeintrag), `tooling.md` (Befehl, Optionen),
  `how-to/run-the-experiment.md` (Schritt nach der K0-Bewertung, Commit), `configuration.md` (neue Schlüssel),
  `experiment-record.md` (Pilotläufe, Stabilität, Kosten), `plan.md` (Backlog), Serena-Memory `evaluation`.
