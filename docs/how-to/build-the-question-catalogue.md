# Fragenkatalog erstellen

*[Doku-Index](../README.md) · Anleitung · Verwandt: [Fragenkatalog](../reference/question-catalogue.md), [Experiment durchführen](run-the-experiment.md), [Plan](../plan.md#zeitplan)*

Ziel: alle Fragen des Katalogs ([Quoten](../reference/question-catalogue.md)) mit Referenzantwort und relevanten Abschnitten, geprüft und eingefroren, bevor irgendein Retrieval auf
ihnen läuft. Regeln, Werte und Quoten: [Fragenkatalog](../reference/question-catalogue.md),
[ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md); Themenauswahl und KI-Durchsicht:
[ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md); blinde Annotation:
[ADR 0027](../adr/0027-blinde-annotation.md); Einfrieren: [ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md).
Formate: [Datenartefakte und Formate](../reference/data-formats.md#fragen-und-ground-truth).

Voraussetzung: Snapshot, Ingest und Preprocessing sind gelaufen ([Korpus-Snapshot erstellen](create-corpus-snapshot.md)).

## Schritte

1. Stichprobenplan (einmalig; gezogen, siehe
   [Experiment-Protokoll](../reference/experiment-record.md#stichprobenplan-e2e)). Neu gezogen wird er nur nach einem
   neuen ADR: `catalogue.py plan` überschreibt keinen bestehenden Plan, also die
   alte Datei zuerst nach `data/evaluation/archive_…/` verschieben (wie `archive_vue/`), dann ziehen und sofort
   committen:

   ```bash
   uv run python src/catalogue.py plan
   git add data/evaluation/catalogue_plan.csv data/evaluation/catalogue_review.csv
   git commit -m "chore(data): Stichprobenplan des Fragenkatalogs gezogen"
   ```

   Der Plan legt je Slot einen Ausgangsabschnitt und eine Konstruktionsklasse fest (je Bereich nach Tokenanteil,
   [Korpus](../reference/corpus.md#bereiche)) und wird nie neu gezogen; der Editor ändert darin nur `status`,
   `skip_reason` und `question_id` sowie bei einem Sprung `slot_id` und `class` der nachrückenden Reservezeile
   ([Datenformate](../reference/data-formats.md#fragen-und-ground-truth)). Der Zug ist deterministisch: Ein neuer Plan unterscheidet sich nur bei geänderten
   Parametern des Zugs ([Konfiguration](../reference/configuration.md#fragenkatalog)) oder geändertem Korpus, und
   `catalogue.py check` meldet einen Plan, der nicht zu einem frischen Zug passt, als `ERROR`.

2. Den Editor starten (nur auf diesem Rechner erreichbar; die Option gilt unabhängig vom Arbeitsverzeichnis):

   ```bash
   uv run streamlit run app/catalogue_editor.py --server.address localhost
   ```

   Der Abschnitt erscheint formatiert (Markdown); „Source text“ zeigt den genauen Text, auf den sich die Relevanzregel
   bezieht. Je Slot: den Ausgangsabschnitt lesen, Frage, Typ und Referenzantwort schreiben und weitere relevante Abschnitte über
   „Find more sections“ suchen und hinzufügen, auch in anderen Bereichen. Der Ausgangsabschnitt gehört
   immer zur Annotation. Wer einen H1-Abschnitt (eine ganze Seite) annotiert, nennt den Grund in `notes`
   ([ADR 0022](../adr/0022-h1-abschnitte-in-ground-truth.md)); ohne Grund meldet die Prüfung ihn. Während des Schreibens markiert der Editor Wörter der Frage, die in den Überschriften
   vorkommen; bei `paraphrase` müssen sie umformuliert werden, bei `detail` zeigt die Prüfung die Länge der Antwort.
   „Save question“ schreibt `questions.csv`, `ground_truth.csv` und den Status im Plan und springt zum nächsten offenen
   Slot. Passt ein Abschnitt nicht, „Skip this section“ mit einem der festen Gründe (`config.CATALOGUE_SKIP_REASONS`); der nächste Reserveabschnitt desselben Bereichs
   übernimmt den Slot. Pilotfragen nicht übernehmen; die Prüfung meldet exakte Kopien (gleicher Wortlaut ohne
   Satzzeichen und Groß-/Kleinschreibung), umformulierte erkennt sie nicht. Ohne Editor helfen
   `catalogue.py sections`, `find` und `show` (Nachschlageliste, Suche, Abschnittstext).

3. Nach jedem Block von 8 Fragen (Takt und Termin des Einfrierens: [Plan](../plan.md#zeitplan)): Claude bitten,
   „Block N durchzusehen“. Claude liest nur `questions.csv`, `ground_truth.csv` und den Korpustext
   (`sections.jsonl`, `documents.jsonl`), nie Chunks, Vektoren oder Retrieval-Ergebnisse
   ([ADR 0027](../adr/0027-blinde-annotation.md)), schreibt selbst keine Frage, Antwort oder Annotation und hängt
   Vorschläge als Zeilen mit `decision = open` an `catalogue_review.csv` an (`kind`: übersehener Abschnitt, Formulierung,
   Fakt, Klasse; Format: [Datenformate](../reference/data-formats.md#fragen-und-ground-truth)). Im Tab „Review“ jeden
   Vorschlag annehmen oder mit Grund ablehnen. Ein angenommener fehlender Abschnitt wird der Annotation hinzugefügt; Formulierungen
   und Fakten ändert man selbst im Tab „Write“.

4. Nach jedem Block auch die Closed-Book-Prüfung ([ADR 0040](../adr/0040-closed-book-pruefung.md)): Das
   Antwortmodell beantwortet jede neue oder geänderte Frage ohne Kontext (ruft die API auf; im Pilot etwa 0,0003 USD je 8 Fragen):

   ```bash
   uv run python src/catalogue.py screen
   ```

   Im Tab „Closed-book“ je Antwort entscheiden: „Hits the core point“, wenn sie den Kernpunkt der Referenzantwort
   vollständig trifft, sonst „Misses it“ (auch bei teilweise richtig). Wie viele Fragen treffen dürfen, legt
   `config.CLOSED_BOOK_MIN_DEPENDENT_SHARE` fest ([Fragenkatalog](../reference/question-catalogue.md)); die
   Seitenleiste zeigt den Stand. Eine getroffene Frage darf bleiben; wer sie umformuliert, lässt `screen` erneut laufen.
   Eine geänderte Referenzantwort öffnet nur das Urteil neu, ein neues `screen` ist dann nicht nötig.
   Danach den Block zusammen committen: `screen` schreibt die Antworten nach `closed_book_screen.csv` und einen
   Laufeintrag nach `generation_runs.jsonl`.

   ```bash
   git add data/evaluation/questions.csv data/evaluation/ground_truth.csv data/evaluation/catalogue_plan.csv \
     data/evaluation/catalogue_review.csv data/evaluation/closed_book_screen.csv data/evaluation/generation_runs.jsonl
   git commit -m "chore(data): Fragenkatalog Block N"
   ```

5. Jederzeit prüfen:

   ```bash
   uv run python src/catalogue.py check --draft
   ```

   `ERROR` (Format, unbekannte Werte oder IDs, veränderter Plan) sofort beheben; `WARNING` (Quoten, Bereiche,
   Klassenregeln, Dubletten, H1-Abschnitt ohne Grund in `notes`, offene Vorschläge, angenommener Abschnitt nicht mehr annotiert, ungeprüfte oder
   unbeurteilte Closed-Book-Antworten, zu viele Treffer) zeigt, was bis zum Ende fehlt. Die strenge Prüfung ohne
   `--draft` meldet dieselben Punkte als `FINDING` und scheitert an ihnen. Kein Retrieval und keine Embedding-Suche auf den Fragen, bevor der Katalog eingefroren ist.

6. Wenn alle Fragen fertig und alle Vorschläge und Closed-Book-Antworten entschieden sind: streng prüfen,
   einfrieren (`freeze` wiederholt die strenge Prüfung selbst) und alle Katalogdateien zusammen committen.

   ```bash
   uv run python src/catalogue.py check
   uv run python src/catalogue.py freeze
   git add data/evaluation/questions.csv data/evaluation/ground_truth.csv data/evaluation/catalogue_plan.csv \
     data/evaluation/catalogue_review.csv data/evaluation/closed_book_screen.csv \
     data/evaluation/generation_runs.jsonl data/evaluation/catalogue_freeze.json
   git commit -m "chore(data): Fragenkatalog eingefroren"
   ```

   Danach läuft `src/retrieve.py` auf dem Katalog; vorher bricht es ab. Ein späteres Ändern von `questions.csv` oder
   `ground_truth.csv` oder ein inhaltlich geändertes `sections.jsonl` bzw. `documents.jsonl` lässt `retrieve.py` wieder
   abbrechen; der Editor ist nach dem Einfrieren schreibgeschützt; ein erneutes Einfrieren braucht ein neues ADR.
   Der Freeze-Datensatz hält auch die Regelversion der Bewertung (`config.RUBRIC_RULES_VERSION`); ändert sie sich
   danach, brechen Scaffold und Summarise des Hauptlaufs ab, denn er wird nach den eingefrorenen Regeln bewertet
   ([ADR 0035](../adr/0035-regelbasierte-bewertung.md), [ADR 0043](../adr/0043-praezisierung-direct-und-teilantworten.md)).
