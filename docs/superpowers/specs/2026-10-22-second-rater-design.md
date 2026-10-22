# Zweitbewertung (ADR 0046) — Design

Stand 22.10.2026; Entscheidungen von Jonas im Gespräch vom 22.10.2026, freigegeben 22.10.2026, umgesetzt in PR #40; Rückfragen des Builder-Checks am 22.10.2026 von Jonas beantwortet.

## Zweck

Eine zweite Person (Pseudonym `R2`) bewertet 12 Fragen × C1–C3 (36 der 144 Antworten) blind und unabhängig mit
denselben Prüffragen und den eingefrorenen Kernpunkten. Die Arbeit beziffert damit, wie stark die Werte von der
bewertenden Person abhängen (ADR 0007, 0046). Die Werte der Arbeit bleiben Jonas' Bewertung; R2 ändert `scores.csv`
nie.

## Ziele

- Ziehung der 12 Fragen mit festem Seed, geschichtet nach Fragetyp und Konstruktionsklasse, nach dem Einfrieren des
  Katalogs und vor Jonas' eigener Bewertung; die Ziehung kennt keine Ergebnisse.
- Ein eigener Bewertungssatz für R2, den die App wie die übrigen Sätze anbietet (gleiches Formular, gleiche Regeln,
  gleiche eingefrorene Kernpunkte), ohne Schlüssel und ohne Jonas' Prüfantworten.
- Übereinstimmung je Prüffrage und je Kriterium mit Bootstrap-Konfidenzintervall über Fragen, als generierte
  Anhangstabelle `agreement.tex` (Anhang B) und als Liste der Abweichungen zum Besprechen.
- Alles läuft auch auf einem Pilot-Set (`--set DIR`), wie die übrigen Schritte.

## Nicht-Ziele

- Keine Ersatzverfahren jetzt: kein Intra-Rater-Satz, kein Sprachmodell als Gegenprobe (Jonas, 22.10.2026: erst,
  wenn bis Mitte November keine Person gefunden ist). Der Code nimmt aber jede zweite Bewertung eines Ordners an, so
  dass der Intra-Rater-Fall später nur ein weiterer Ordner ist.
- Keine Zweitbewertung von K0 (ADR 0046, ADR 0041) und keine Zweitannotation der Relevanz (bleibt vorgemerkt).
- Kein Cohens Kappa (ADR 0046). Keine neue Abhängigkeit: AC1, AC2 und α sind eigener Code (Jonas, 22.10.2026).
- Keine Tabelle in Kapitel 4; der Verweis im Text schreibt Jonas.

## Anti-Ziele (wäre ein Fehlschlag, auch wenn es läuft)

- Die Ziehung hängt von Ergebnissen ab oder wird nach Beginn der eigenen Bewertung (wieder) ausgeführt.
- R2 sieht Strategie, Schlüssel oder Jonas' Antworten auf die Prüffragen.
- R2 bewertet mit anderen Kernpunkten als den eingefrorenen.
- Name oder Kontaktdaten der zweiten Person stehen in einer Datei, einem Laufeintrag, einem Log oder einer Ausgabe.
- Eine unvollständige Zweitbewertung wird ausgewertet, ohne dass es auffällt.
- R2-Werte fließen in `scores.csv`, `scoring_checks.csv` oder die Kernpunkte zurück.

## Entscheidungen (von Jonas, 22.10.2026; ADR 0046)

- Umfang 12 Fragen × C1–C3 (25 %), geschichtet nach `type` und `difficulty` (Konstruktionsklasse), fester Seed.
- R2 bewertet in der App, in einem eigenen Satz unter `data/evaluation/second_rater/` (Nachtrag zu ADR 0046: R2-Werte
  liegen nur unter `data/evaluation/`).
- Maße (ADR 0046): einfache Übereinstimmung; Gwets AC1 für die Ja/Nein-Prüffragen und die Kernpunkte; Gwets AC2 mit
  ordinalen Gewichten für die fünf Kriterien (0–2) und die beiden dreistufigen, geordneten Prüffragen `grounded`
  (all/some/none) und `hallucination` (none/minor/substantive); Krippendorffs α (ordinal) zum Vergleich; je Maß ein
  Bootstrap-Konfidenzintervall über Fragen. Die AC2-Regel für die zwei geordneten Prüffragen präzisiert ADR 0046 (Jonas,
  22.10.2026) und kommt als Nachtrag in die ADR.
- Verblindung (Jonas, 22.10.2026): R2 bewertet an Jonas' Rechner in einem R2-Modus der App (Umgebungsvariable, z. B.
  `SCORING_RATER=R2`), der nur den R2-Satz zeigt und die Katalogseite und alle übrigen Sätze ausblendet; R2 sieht das
  Repo nicht. Bis R2 die Bewertung abgeschlossen hat, pusht Jonas seine `scoring_checks.csv` und `scoring_sheet.csv`
  nicht (Regel in `evaluation.md`, nicht technisch erzwungen).
- Pilot-Sets (Jonas, 22.10.2026): die Schutzregeln „noch keine eigenen Werte“ und „`scores.csv` fehlt“ warnen bei
  `--set` nur, statt abzubrechen; im Hauptkatalog bleiben sie harte Abbrüche.
- Abschluss (Entscheidung Claude): R2s Bewertung wird mit `--mode close` abgeschlossen; erst dann wertet `analyse.py` sie
  aus (wie jede Ergebnisdatei nur mit aktuellem Laufeintrag, ADR 0044).
- Eigene Implementierung in `src/stats.py`, Tests gegen veröffentlichte Rechenbeispiele (Gwet, 2014; Krippendorff).
- Bericht als Anhangstabelle `agreement.tex` (Anhang B), nicht in Kapitel 4.
- Ersatzverfahren erst bei Bedarf (siehe Nicht-Ziele).

## Ablauf

1. **Ziehung** (`src/second_rater.py --mode draw`): nach dem Einfrieren des Katalogs (`require_frozen`), vor jeder
   eigenen Bewertung. Schreibt `data/evaluation/second_rater_sample.csv` (`question_id`, `type`, `difficulty`,
   sortiert nach `question_id`) und einen Laufeintrag (Schritt `second_rater_draw`: Datum, Seed, Anzahl, Prüfsumme
   von `questions.csv` und der Ausgabe). Liest nur `questions.csv`.
2. **Satz für R2** (`--mode export`): nach `evaluate_answers.py --mode scaffold` und nach dem Einfrieren der
   Kernpunkte, solange `scores.csv` noch nicht existiert. Schreibt `data/evaluation/second_rater/` mit
   `scoring_items.jsonl` (nur die 36 Einträge der gezogenen Fragen, unverändert mit denselben Codes und derselben
   gemischten Reihenfolge), `key_points.csv` (die eingefrorenen Kernpunkte der 12 Fragen), `runs.jsonl` (die
   Einträge, die die App für Satz und Kernpunkte verlangt) und eine leere `scoring_sheet.csv`; kein Schlüssel, keine
   Prüfantworten. Laufeintrag `second_rater_export` mit Prüfsummen von Ziehung, Item-Datei und Kernpunkten.
3. **Bewertung durch R2** in der App: der Satz erscheint als „Second rater“; das Formular schreibt
   `scoring_checks.csv` und `scoring_sheet.csv` in diesen Ordner. Die Kernpunkte sind dort nicht bearbeitbar.
4. **Abschluss** (`--mode close`): prüft, dass alle 36 Codes Prüfantworten und Werte haben und die Werte aus den
   Prüfantworten nach den aktuellen Regeln folgen, schreibt den Laufeintrag `second_rater_close` (Prüfsummen von
   `scoring_checks.csv`, `scoring_sheet.csv`, Kernpunkten und Items im R2-Ordner, Regelversion, Pseudonym `R2`) und
   macht den Satz in der App schreibgeschützt (wie `is_read_only` nach `scores.csv`).
5. **Auswertung** in `analyse.py`: liegt ein `second_rater_close`-Eintrag vor und passen die Dateien noch dazu, schreibt es
   `agreement.tex` und `second_rater_disagreements.csv`; fehlt sie oder ist sie unvollständig, entfällt beides mit
   Hinweis in `notes` (wie bei RAGAS). Jonas' Werte kommen aus seinem `scoring_checks.csv` und `scoring_sheet.csv`,
   verglichen Code für Code; der Schlüssel wird dafür nicht gebraucht.

## Schutzregeln

- Ziehung: Abbruch, wenn der Katalog nicht eingefroren ist, wenn `scoring_sheet.csv` oder `scoring_checks.csv` des
  Hauptlaufs schon einen Wert enthält, oder wenn die Ziehungsdatei existiert (nie überschreiben). Die Ziehung liest
  keine Ergebnisdatei.
- Export: Abbruch, wenn Ziehung, Item-Datei oder eingefrorene Kernpunkte fehlen, wenn eine gezogene Frage nicht genau
  drei Items hat, wenn die Prüfsumme der Ziehung nicht zu ihrem Laufeintrag passt, wenn `scores.csv` existiert, oder
  wenn der R2-Ordner schon Werte enthält.
- Pilot-Sets: die beiden Prüfungen auf schon vorhandene eigene Werte (Ziehung) und auf `scores.csv` (Export) warnen
  nur (siehe Entscheidungen).
- Auswertung: die Kernpunkte im R2-Ordner müssen gleich den eingefrorenen sein, die Items gleich denen in Jonas'
  Item-Datei, und beide Bewertungen unter derselben Regelversion (`rules_version`) entstanden sein; sonst Abbruch mit
  klarer Meldung.
- Nur das Pseudonym `R2` erscheint in Dateien, Laufeinträgen und Ausgaben; kein Feld für einen Namen.
- Alle Parameter in `src/config.py`: Anzahl (12), Seed, Ordner- und Dateinamen, Bootstrap-Wiederholungen,
  Konfidenzniveau, Bootstrap-Seed, Pseudonym.

## Ziehung im Detail

- Zielzahlen je Fragetyp und je Klasse proportional zu den Quoten des Katalogs (`QUESTION_TYPES`,
  `QUESTION_CLASSES`), gerundet nach größtem Rest; Gleichstände entscheidet der Seed. Im Hauptkatalog: je Klasse 3;
  factual, procedural, conceptual je 3; comparative und limitation zusammen 3 (2 + 1, welcher Typ 2 bekommt,
  entscheidet der Seed).
- Gezogen wird so, dass beide Randverteilungen genau stimmen (z. B. wiederholtes Mischen mit dem Seed, bis eine
  Auswahl beide Zielzahlen trifft, oder ein gleichwertiges deterministisches Verfahren). Gleicher Seed und gleiche
  `questions.csv` ergeben dieselbe Ziehung.
- Pilot-Sets: Anzahl über eine Option (z. B. `--questions N`), Zielzahlen proportional zu den tatsächlichen Anteilen
  im Set; ist keine Auswahl mit beiden Randverteilungen möglich, Abbruch mit Meldung.

## Übereinstimmung im Detail

- Einheiten: die 36 Antworten (Codes). Je Antwort vergleicht die Auswertung
  - die acht Prüffragen aus `scoring_rules.CHECKS` (wie gespeichert, also mit den festen Werten bei ablehnenden
    Antworten),
  - die Markierungen der Kernpunkte (`covered`/`missing`), gepoolt über alle Kernpunkte als eine Zeile,
  - die fünf Kriterien 0–2 aus den Bewertungsbögen.
- Maße je Zeile: n, einfache Übereinstimmung (Anteil gleicher Werte), AC1 (Ja/Nein-Prüffragen und Kernpunkte) bzw.
  AC2 mit Gwets ordinalen Gewichten (`grounded`, `hallucination` und die Kriterien), Krippendorffs α (ordinal; bei zwei
  Kategorien gleich dem nominalen). Ist α in einer Bootstrap-Stichprobe nicht bestimmbar, zählt die Stichprobe nicht
  für dessen Intervall; die Fußnote nennt die Zahl der verworfenen Stichproben.
- Konfidenzintervall: Bootstrap über die 12 Fragen (alle Antworten einer Frage zusammen), Perzentil-Intervall,
  Wiederholungen, Niveau und Seed aus `config`.
- Nicht bestimmbar (z. B. α, wenn beide Personen nur eine Kategorie vergeben): `NOT_DETERMINABLE` wie in den übrigen
  Tabellen, mit Grund in der Fußnote; AC1/AC2 sind dann definiert und werden berichtet.
- `second_rater_disagreements.csv` (in `output/`, im Set `DIR/output/`): je abweichender Prüffrage, Kernpunkt oder
  Kriterium eine Zeile mit Code, Frage, Feld, Wert Jonas, Wert R2; zum Besprechen. Sie enthält keine Strategie.

## Tabelle `agreement`

- Titel „Übereinstimmung der Erst- und Zweitbewertung“, Label `tab:agreement`, IU-Format wie die übrigen Tabellen
  (`latex_table`, deutsches Dezimalkomma, `\source{Eigene Darstellung. …}`), Zeilen gruppiert in Prüffragen,
  Kernpunkte und Kriterien.
- Spalten: Merkmal, n, Übereinstimmung, AC1/AC2 [KI], α [KI].
- Wird in `TABLE_NAMES` aufgenommen (dann 13 Tabellen) und in `write_tables` übersprungen, wenn keine vollständige
  Zweitbewertung vorliegt. PaperLab bindet sie in Anhang B ein (`\ergebnistabelle{agreement}`).

## App

- `scoring_store.scoring_sets()` findet zusätzlich den R2-Satz unter `data/evaluation/second_rater/` und in Pilot-Sets
  unter `DIR/second_rater/`; Name „Second rater“ bzw. „Pilot: DIR: second rater“.
- Der Satz zeigt die Kernpunkte nur an (eingefroren, nicht bearbeitbar) und hat keinen Schritt „summarise“.
- Der R2-Ordner eines Pilot-Sets wird nicht zusätzlich als gewöhnlicher Pilot-Satz gefunden.
- R2-Modus: mit der Umgebungsvariable zeigt die App nur den R2-Satz (Hauptkatalog, sonst den einzigen vorhandenen
  Pilot-R2-Satz) und blendet die Katalogseite aus; ohne sie bleibt alles wie heute.

## Erprobung

- Tests mit Fixtures (keine API, kein Netz): Ziehung (Zielzahlen, Determinismus, Abbruchfälle), Export (Inhalt,
  keine Schlüssel- oder Prüfdateien, Abbruchfälle), Statistik (Rechenbeispiele aus der Literatur, Grenzfälle),
  Auswertung (Abweichungen, Unvollständigkeit, Regelversion), Tabelle (IU-Regeln).
- Probelauf auf dem Pilot e2e: Ziehung und Export laufen (mit Warnungen, da der Pilot schon bewertet ist), die App
  zeigt den Satz im R2-Modus. R2-Werte schreibt Claude nicht; füllt Jonas den Pilot-Satz zur Probe selbst aus, entsteht
  eine echte Tabelle, sofern seine Pilot-Prüfantworten unter derselben Regelversion entstanden sind (sonst meldet die
  Auswertung den Unterschied klar).

## Dokumentation

- `docs/reference/evaluation.md#zweitbewertung` (Ablauf statt „noch umzusetzen“, Ordner `data/evaluation/second_rater/`
  statt `data/pilot/zweitbewertung`, Push-Regel), Nachtrag in ADR 0046 (AC2 für die geordneten Prüffragen), `docs/reference/data-formats.md`
  (Ziehung, R2-Ordner, Abweichungsliste, Tabelle), `docs/reference/tooling.md` (Befehle),
  `docs/reference/configuration.md` (neue Schlüssel), `docs/plan.md#stand`.

## Dem Bauenden überlassen

- Modul- und Funktionsnamen, Dateiaufteilung (z. B. Statistik in `stats.py`, Schritt in `src/second_rater.py`).
- Das genaue Verfahren der geschichteten Ziehung, solange es deterministisch ist und beide Randverteilungen trifft.
- Der Bootstrap-Wert für Wiederholungen (Vorschlag 2000) und die Formatierung der Intervalle.
