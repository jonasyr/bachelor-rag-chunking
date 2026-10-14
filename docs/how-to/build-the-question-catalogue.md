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

1. Den Stichprobenplan einmal ziehen und sofort committen:

   ```bash
   uv run python src/catalogue.py plan
   git add data/evaluation/catalogue_plan.csv data/evaluation/catalogue_review.csv
   git commit -m "chore(data): Stichprobenplan des Fragenkatalogs gezogen"
   ```

   Der Plan legt für 48 Slots je einen Ausgangsabschnitt und eine Konstruktionsklasse fest (12 API, 3 Style Guide,
   33 Guide) und wird nie überschrieben.

2. Den Editor starten (nur auf diesem Rechner erreichbar):

   ```bash
   uv run streamlit run app/catalogue_editor.py
   ```

   Je Slot: den Ausgangsabschnitt lesen, Frage, Typ und Referenzantwort schreiben und weitere relevante Abschnitte über
   „Find more sections“ suchen und hinzufügen, auch in der API-Referenz und im Style Guide. Der Ausgangsabschnitt gehört
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

4. Jederzeit prüfen:

   ```bash
   uv run python src/catalogue.py check --draft
   ```

   `ERROR` (Format, unbekannte Werte oder IDs, veränderter Plan) sofort beheben; `WARNING` (Quoten, Bereiche,
   Klassenregeln, Dubletten, offene Vorschläge) zeigt, was bis zum Ende fehlt. Kein Retrieval und keine
   Embedding-Suche auf den Fragen, bevor der Katalog eingefroren ist.

5. Wenn alle 48 Fragen fertig und alle Vorschläge entschieden sind: streng prüfen, einfrieren und alle Katalogdateien
   zusammen committen.

   ```bash
   uv run python src/catalogue.py check
   uv run python src/catalogue.py freeze
   git add data/evaluation/questions.csv data/evaluation/ground_truth.csv data/evaluation/catalogue_plan.csv \
     data/evaluation/catalogue_review.csv data/evaluation/catalogue_freeze.json
   git commit -m "chore(data): Fragenkatalog eingefroren"
   ```

   Danach läuft `src/retrieve.py` auf dem Katalog; vorher bricht es ab. Ein späteres Ändern einer der beiden
   Katalogdateien oder ein neu gebautes `sections.jsonl` bzw. `documents.jsonl` lässt `retrieve.py` wieder abbrechen;
   der Editor ist nach dem Einfrieren schreibgeschützt; ein erneutes Einfrieren braucht ein neues ADR.
