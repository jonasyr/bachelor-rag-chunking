# Ergebnisse nachvollziehen

*[Doku-Index](../README.md) · Anleitung · Verwandt: [Einrichten](set-up.md), [Experiment durchführen](run-the-experiment.md), [Datenformate](../reference/data-formats.md#versioniert-und-ignoriert), [ADR 0048](../adr/0048-korpus-und-chunk-vektoren-versioniert.md)*

Für Begutachtende und alle, die die Zahlen der Arbeit aus dem Repo nachrechnen wollen. Ohne API-Schlüssel und, ab
Schritt 2, ohne Netz entstehen Korpusdateien, Index, Retrieval, Retrieval-Metriken und alle Tabellen und Abbildungen
neu; `git` zeigt danach, ob sie mit den versionierten Dateien übereinstimmen. Stand 26.10.2026: der Hauptlauf steht
noch aus ([Plan](../plan.md#stand)); Schritte 1–3 sind auf einer frischen Kopie geprüft, Schritte 4–6 gelten, sobald
seine Dateien im Repo liegen.

## Was sich wiederholen lässt und was nicht

| Teil | Wiederholbar | Grund |
|---|---|---|
| Korpus, Abschnitte, Chunks | bitgleich | Snapshot versioniert, Aufbereitung deterministisch ([ADR 0048](../adr/0048-korpus-und-chunk-vektoren-versioniert.md)) |
| Index und Retrieval, Retrieval-Metriken | bitgleich | Chunk- und Fragevektoren versioniert, exakte Suche ([ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md), [ADR 0045](../adr/0045-retrieval-ergebnisse-versioniert.md)) |
| Tabellen, Kennzahlen, Abbildungen (`output/`) | bitgleich (Abbildungen nur mit Arial, Schritt 5) | aus versionierten Primärdaten berechnet ([ADR 0044](../adr/0044-statistische-auswertung.md)) |
| Antworten, Bewertungen, Zweitbewertung, RAGAS-Werte | nein; die versionierten Dateien sind die Primärdaten | Sprachmodelle antworten auch bei Temperatur 0 nicht bitgleich, Bewertungen sind menschliche Urteile ([ADR 0033](../adr/0033-antwortmodell.md), [ADR 0032](../adr/0032-blinde-rubrik-bewertung.md), [ADR 0046](../adr/0046-zweitbewertung.md), [ADR 0047](../adr/0047-ragas-als-triangulation.md)); die Skripte überschreiben sie nie |

Jeder Schritt prüft die SHA-256 seiner Eingaben gegen das Laufprotokoll und bricht bei einer Abweichung mit dem Befehl
ab, der fehlt; ein stilles Abweichen gibt es nicht.

## Schritte

1. Klonen und einrichten: `git clone https://github.com/jonasyr/bachelor-rag-chunking.git`, darin `uv sync`
   ([Einrichten](set-up.md), Schritte 0–1; kein `.env` nötig).
2. Korpusdateien aus dem versionierten Snapshot neu erzeugen:

   ```bash
   uv run python src/ingest.py
   uv run python src/preprocess.py
   uv run python src/chunking.py
   ```

   Danach meldet `git status` keine Änderung an `docs/corpus_manifest.csv`. Wer den Snapshot zusätzlich gegen das
   Original-Repository prüfen will: `uv run python src/snapshot.py` (braucht Netz; bricht ab, wenn der geholte Commit
   nicht zu `docs/corpus_snapshot.txt` passt).
3. Index aus den versionierten Vektoren aufbauen: `uv run python src/embed.py`. Erwartet je Strategie
   `0 tokens, USD 0.0000, api_called=False`.
4. Retrieval und Retrieval-Metriken wiederholen:

   ```bash
   uv run python src/retrieve.py
   uv run python src/retrieve.py --control
   uv run python src/evaluate_retrieval.py
   uv run python src/evaluate_retrieval.py --control
   ```

5. Auswertung: `uv run python src/analyse.py`. Die Abbildungen nutzen Arial; ohne PaperLab-Checkout `PAPERLAB_FONTS`
   auf einen Ordner mit `arial282/Arial282-Regular.ttf` setzen
   ([Umgebungsvariablen](../reference/tooling.md#umgebungsvariablen)), sonst entstehen sie in DejaVu Sans und
   unterscheiden sich von den versionierten.
6. Vergleichen: `git status --short` und `git diff --stat`. Unverändert sein müssen `data/evaluation/` und `output/`;
   neue Zeilen in `data/processed/embedding_runs.jsonl` und `data/evaluation/generation_runs.jsonl` sind erwartet
   (jeder Lauf wird protokolliert, [Laufprotokoll](../reference/data-formats.md#laufprotokoll)).
