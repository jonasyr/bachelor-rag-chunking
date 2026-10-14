# 0030. Einfrieren des Fragenkatalogs als technische Sperre

## Status

Angenommen (14.10.2026; setzt [ADR 0017](0017-fragenkatalog.md) und [ADR 0027](0027-blinde-annotation.md) technisch um)

## Kontext

- Ground Truth und Relevanz-Annotation müssen vor jedem Retrieval feststehen (ADR 0017, 0027). Bisher ist das eine
  Zusage; das Laufprotokoll von `retrieve.py` zeigt erst nachträglich, mit welchen Dateien gerechnet wurde.
- Meilenstein 09.11.2026: Ground Truth eingefroren ([ADR 0028](0028-c4-bedingung.md)).

## Entscheidung

Wir werden den Katalog mit `src/catalogue.py freeze` einfrieren: Nur wenn die strenge Prüfung
([ADR 0029](0029-fragetypen-und-konstruktionsklassen.md)) besteht, schreibt der Befehl
`data/evaluation/catalogue_freeze.json` mit Datum, Anzahlen je Typ und Klasse und den SHA-256 von `questions.csv`,
`ground_truth.csv`, `sections.jsonl` und `documents.jsonl` (Abschnitte und Text, auf die sich die annotierten IDs
beziehen); ein vorhandener Datensatz wird nie überschrieben.
Wir werden `retrieve.py` auf dem Hauptkatalog (`config.QUESTIONS_FILE`, `config.GROUND_TRUTH_FILE`) nur laufen lassen,
wenn alle vier Prüfsummen zum Datensatz passen; die Prüfung steht vor jedem API-Aufruf und gilt auch für die Kontrolle K1.
Pilot-Sets sind nicht betroffen.
Ein erneutes Einfrieren braucht ein neues ADR mit Begründung und das Löschen des Datensatzes von Hand.

## Konsequenzen

- Gut: „Ground Truth vor Retrieval“ ist im Code erzwungen und mit Datum belegt; der Datensatz ist versioniert und
  zitierfähig und zeigt allein, auf welchen Korpus (Text und Abschnittseinteilung) sich die Relevanzurteile beziehen.
- Neutral: Ein neu gebauter Korpus mit anderem `sections.jsonl` oder `documents.jsonl` sperrt das Retrieval ebenfalls; die Annotation müsste
  dann abgebildet und neu eingefroren werden.
- Neutral: Generierung und Bewertung bauen auf den Retrieval-Ergebnissen auf und erben die Sperre.
- Neutral: Die Sperre prüft Pfade; eine Kopie des Katalogs an anderer Stelle umgeht sie. Das Laufprotokoll hält die
  Prüfsummen jedes Retrieval-Laufs fest, so dass ein solcher Lauf nachweisbar bleibt.
- Schlecht: Eine Korrektur nach dem Einfrieren (z. B. ein Tippfehler) braucht ein ADR; das ist gewollt.
