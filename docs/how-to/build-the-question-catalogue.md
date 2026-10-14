# Fragenkatalog erstellen

> Seitentyp: Anleitung (how-to). Übersicht: [Dokumentation](../README.md).

Ziel: 48 Fragen mit Referenzantwort und relevanten Abschnitten, geprüft und eingefroren, bevor irgendein Retrieval auf
ihnen läuft. Regeln, Werte und Quoten: [Fragenkatalog](../reference/question-catalogue.md),
[ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md); blinde Annotation:
[ADR 0027](../adr/0027-blinde-annotation.md); Einfrieren: [ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md).
Formate: [Datenartefakte und Formate](../reference/data-formats.md#fragen-und-ground-truth).

Voraussetzung: Snapshot, Ingest und Preprocessing sind gelaufen ([Korpus-Snapshot erstellen](create-corpus-snapshot.md)).

## Schritte

1. Nachschlageliste erzeugen und öffnen:

   ```bash
   uv run python src/catalogue.py sections
   ```

   `data/processed/section_index.md` listet alle Abschnitte mit `section_id`, Bereich, Seite, Überschriftenpfad und
   Länge in Tokens.

2. Frage in `data/evaluation/questions.csv` eintragen, mit `type` und `difficulty` (Konstruktionsklasse) aus der
   [Referenz](../reference/question-catalogue.md). Pilotfragen nicht übernehmen; die Prüfung meldet exakte Kopien (gleicher Wortlaut ohne Satzzeichen und
   Groß-/Kleinschreibung), umformulierte Pilotfragen erkennt sie nicht.

3. Alle relevanten Abschnitte suchen, auch in der API-Referenz und im Style Guide, nicht nur auf der naheliegenden Seite:

   ```bash
   uv run python src/catalogue.py find "v-model"
   uv run python src/catalogue.py show "D046#lazy"
   ```

   `find` sucht wörtlich und meldet nur den innersten Abschnitt eines Treffers; `show` zeigt den genauen Text, den
   auch die Relevanzregel verwendet. Referenzantwort, `relevant_section_ids` und `relevant_doc_ids` in
   `data/evaluation/ground_truth.csv` eintragen. Kein Retrieval und keine Embedding-Suche auf den Fragen, bevor der
   Katalog eingefroren ist.

4. Nach jedem Block von Fragen prüfen:

   ```bash
   uv run python src/catalogue.py check --draft
   ```

   `ERROR` (Format, unbekannte Werte oder IDs) sofort beheben; `WARNING` (Quoten, Bereiche, Klassenregeln, Dubletten)
   zeigt, was bis zum Ende noch fehlt. Bei `paraphrase` die gemeldeten Überschriftswörter umformulieren; bei `detail`
   die angezeigte Abschnitts- und Antwortlänge prüfen.

5. Wenn alle 48 Fragen fertig sind: streng prüfen und einfrieren, dann alle drei Dateien zusammen committen.

   ```bash
   uv run python src/catalogue.py check
   uv run python src/catalogue.py freeze
   git add data/evaluation/questions.csv data/evaluation/ground_truth.csv data/evaluation/catalogue_freeze.json
   git commit -m "chore(data): Fragenkatalog eingefroren"
   ```

   Danach läuft `src/retrieve.py` auf dem Katalog; vorher bricht es ab. Ein späteres Ändern einer der beiden Dateien
   oder ein neu gebautes `sections.jsonl` bzw. `documents.jsonl` lässt `retrieve.py` wieder abbrechen; ein erneutes Einfrieren braucht ein neues ADR.
