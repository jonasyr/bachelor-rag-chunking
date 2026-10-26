# Auf zwei Rechnern arbeiten

*[Doku-Index](../README.md) · Anleitung · Verwandt: [Einrichten](set-up.md), [Experiment durchführen](run-the-experiment.md), [Datenformate](../reference/data-formats.md#versioniert-und-ignoriert)*

Jonas arbeitet am Laptop (dort entstanden Snapshot, Chunks und Vektoren) und am PC. Alles, was kein Lauf exakt
wiederholt, ist versioniert ([ADR 0048](../adr/0048-korpus-und-chunk-vektoren-versioniert.md)); der Rest entsteht
auf jedem Rechner ohne API-Aufruf neu, und jeder Schritt prüft die Prüfsummen seiner Eingaben.

## Einen Rechner einrichten (einmal)

1. [Einrichten](set-up.md) (Klon, `uv sync`, `.env`, pre-commit).
2. Korpusdateien neu erzeugen: `uv run python src/ingest.py`, `uv run python src/preprocess.py`,
   `uv run python src/chunking.py`, dann `uv run python src/catalogue.py sections` für die Nachschlageliste.
3. Index aus den versionierten Vektoren: `uv run python src/embed.py` (kein API-Aufruf, 0 Tokens).

## Wechseln

1. Auf dem einen Rechner alles committen und pushen, auf dem anderen `git pull`.
2. Haben sich Snapshot, `src/config.py` oder die Vektoren geändert, Schritte 2–3 oben wiederholen; ein Schritt, der
   veraltete Dateien findet, bricht ab und nennt den Befehl.
3. Bewerten: fehlen nach dem Pull Lesepaket und `scoring_items.jsonl` (ignoriert), `--mode scaffold` mit denselben
   Optionen erneut ausführen; Bogen und Schlüssel existieren, also werden nur diese beiden Dateien wiederhergestellt
   ([Experiment durchführen](run-the-experiment.md#bewerten-schritte-5-und-6)). `scores.csv` entsteht mit `--mode summarise` neu.

## Regeln

- Schritte mit API-Aufruf, die genau einmal laufen (Closed-Book-Prüfung, `generate.py`, `ragas_eval.py`), auf einem
  Rechner ausführen und das Ergebnis sofort committen und pushen, bevor der andere Rechner weiterarbeitet.
- Von Schritt 6 bis Schritt 9 des Hauptlaufs wird nicht gepusht (R2 darf Jonas' Werte nicht sehen,
  [Experiment durchführen](run-the-experiment.md#hauptlauf-auf-einen-blick)); in dieser Zeit auf einem Rechner bleiben.
- Nie auf beiden Rechnern einbetten: neue Vektoren kosten Geld und weichen ab; die Vektoren kommen nur über Git.
