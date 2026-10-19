# Fragenkatalog erstellen

> Seitentyp: Anleitung (how-to). Übersicht: [Dokumentation](../README.md).

Ziel: 48 Fragen mit Referenzantwort und relevanten Abschnitten, geprüft und eingefroren, bevor irgendein Retrieval auf
ihnen läuft. Regeln, Werte und Quoten: [Fragenkatalog](../reference/question-catalogue.md),
[ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md); Themenauswahl und KI-Durchsicht:
[ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md); blinde Annotation:
[ADR 0027](../adr/0027-blinde-annotation.md); Einfrieren: [ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md).
Formate: [Datenartefakte und Formate](../reference/data-formats.md#fragen-und-ground-truth).

Voraussetzung: Snapshot, Ingest und Preprocessing sind gelaufen ([Korpus-Snapshot erstellen](create-corpus-snapshot.md)).

## Schritte

1. Der Stichprobenplan ist gezogen (18.10.2026, [Experiment-Protokoll](../reference/experiment-record.md#stichprobenplan-e2e));
   nur nach einem neuen ADR wird er so neu gezogen und sofort committet:

   ```bash
   uv run python src/catalogue.py plan
   git add data/evaluation/catalogue_plan.csv data/evaluation/catalogue_review.csv
   git commit -m "chore(data): Stichprobenplan des Fragenkatalogs gezogen"
   ```

   Der Plan legt für 48 Slots je einen Ausgangsabschnitt und eine Konstruktionsklasse fest (je Bereich nach
   Tokenanteil, [Korpus](../reference/corpus.md#bereiche)) und wird nie überschrieben.

2. Den Editor starten (nur auf diesem Rechner erreichbar; die Option gilt unabhängig vom Arbeitsverzeichnis):

   ```bash
   uv run streamlit run app/catalogue_editor.py --server.address localhost
   ```

   Der Abschnitt erscheint formatiert (Markdown); „Source text“ zeigt den genauen Text, auf den sich die Relevanzregel
   bezieht. Je Slot: den Ausgangsabschnitt lesen, Frage, Typ und Referenzantwort schreiben und weitere relevante Abschnitte über
   „Find more sections“ suchen und hinzufügen, auch in anderen Bereichen. Der Ausgangsabschnitt gehört
   immer zur Annotation. Während des Schreibens markiert der Editor Wörter der Frage, die in den Überschriften
   vorkommen; bei `paraphrase` müssen sie umformuliert werden, bei `detail` zeigt die Prüfung die Länge der Antwort.
   „Save question“ schreibt `questions.csv` und `ground_truth.csv` und springt zum nächsten offenen Slot. Passt ein
   Abschnitt nicht, „Skip this section“ mit einem der vier Gründe; der nächste Reserveabschnitt desselben Bereichs
   übernimmt den Slot. Pilotfragen nicht übernehmen; die Prüfung meldet exakte Kopien (gleicher Wortlaut ohne
   Satzzeichen und Groß-/Kleinschreibung), umformulierte erkennt sie nicht. Ohne Editor helfen
   `catalogue.py sections`, `find` und `show` (Nachschlageliste, Suche, Abschnittstext).

3. Nach jedem Block von 8 Fragen: Claude bitten, „Block N durchzusehen“. Claude liest nur Fragen, Annotation und
   Korpustext und trägt Vorschläge als offene Zeilen in `catalogue_review.csv` ein; im Tab „Review“ jeden Vorschlag
   annehmen oder mit Grund ablehnen. Ein angenommener fehlender Abschnitt wird der Annotation hinzugefügt; Formulierungen
   und Fakten ändert man selbst im Tab „Write“.

4. Nach jedem Block auch die Closed-Book-Prüfung ([ADR 0040](../adr/0040-closed-book-pruefung.md)): Das
   Antwortmodell beantwortet jede neue oder geänderte Frage ohne Kontext (ruft die API auf, wenige Cent je Block):

   ```bash
   uv run python src/catalogue.py screen
   ```

   Im Tab „Closed-book“ je Antwort entscheiden: „Hits the core point“, wenn sie den Kernpunkt der Referenzantwort
   vollständig trifft, sonst „Misses it“ (auch bei teilweise richtig). Höchstens 16 von 48 Fragen dürfen treffen; die
   Seitenleiste zeigt den Stand. Eine getroffene Frage darf bleiben; wer sie umformuliert, lässt `screen` erneut laufen.

5. Jederzeit prüfen:

   ```bash
   uv run python src/catalogue.py check --draft
   ```

   `ERROR` (Format, unbekannte Werte oder IDs, veränderter Plan) sofort beheben; `WARNING` (Quoten, Bereiche,
   Klassenregeln, Dubletten, offene Vorschläge, ungeprüfte oder unbeurteilte Closed-Book-Antworten) zeigt, was bis
   zum Ende fehlt. Kein Retrieval und keine Embedding-Suche auf den Fragen, bevor der Katalog eingefroren ist.

6. Wenn alle 48 Fragen fertig und alle Vorschläge und Closed-Book-Antworten entschieden sind: streng prüfen,
   einfrieren und alle Katalogdateien zusammen committen.

   ```bash
   uv run python src/catalogue.py check
   uv run python src/catalogue.py freeze
   git add data/evaluation/questions.csv data/evaluation/ground_truth.csv data/evaluation/catalogue_plan.csv \
     data/evaluation/catalogue_review.csv data/evaluation/closed_book_screen.csv \
     data/evaluation/catalogue_freeze.json
   git commit -m "chore(data): Fragenkatalog eingefroren"
   ```

   Danach läuft `src/retrieve.py` auf dem Katalog; vorher bricht es ab. Ein späteres Ändern einer der beiden
   Katalogdateien oder ein neu gebautes `sections.jsonl` bzw. `documents.jsonl` lässt `retrieve.py` wieder abbrechen;
   der Editor ist nach dem Einfrieren schreibgeschützt; ein erneutes Einfrieren braucht ein neues ADR.
