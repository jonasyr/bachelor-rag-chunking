# Experiment durchführen

> Seitentyp: Anleitung (how-to). Übersicht: [Dokumentation](../README.md).

Voraussetzungen: [Einrichten](set-up.md), [Korpus-Snapshot](create-corpus-snapshot.md), Fragenkatalog und Ground Truth
fertig und eingefroren ([Fragenkatalog erstellen](build-the-question-catalogue.md),
[Fragenkatalog](../reference/question-catalogue.md),
[ADR 0017](../adr/0017-fragenkatalog.md), [ADR 0027](../adr/0027-blinde-annotation.md)). Nur das Chunking variiert
([ADR 0006](../adr/0006-nur-chunking-variiert.md)). Welche Schritte schon umgesetzt sind: [Plan](../plan.md#stand).

## Hauptlauf auf einen Blick

Für den e2e-Korpus sind Schritt 1–3 (Snapshot, Chunks, Embeddings) erledigt und werden nicht wiederholt; der Hauptlauf
beginnt mit dem eingefrorenen Katalog ([Fragenkatalog erstellen](build-the-question-catalogue.md), Schritt 6). Nach
jedem Block die versionierten Dateien committen ([Datenformate](../reference/data-formats.md#versioniert-und-ignoriert));
Retrieval-Ergebnisse und Fragevektoren sind ignoriert und bleiben nur lokal.

```bash
# 0. Katalog eingefroren? (sonst brechen 1 und 2 vor jedem API-Aufruf ab)
uv run python src/catalogue.py check

# 1. Retrieval C1–C3 und K1 (Fragevektoren: ein API-Aufruf, danach aus data/evaluation/query_embeddings.npz)
uv run python src/retrieve.py
uv run python src/retrieve.py --control

# 2. Antworten C1–C3 und K0, genau einmal (überschreibt nie), sofort committen
uv run python src/generate.py
git add data/evaluation/generated_answers.csv data/evaluation/generated_answers_control.csv \
  data/evaluation/generation_runs.jsonl
git commit -m "chore(data): Antworten des Hauptlaufs"

# 3. Retrieval-Metriken und Bewertungsbogen C1–C3
uv run python src/evaluate_retrieval.py
uv run python src/evaluate_retrieval.py --control
uv run python src/evaluate_answers.py --mode scaffold
#    App, Seite „Scoring“: Kernpunkte prüfen und einfrieren, dann jede Antwort blind bewerten (Schritt 6 unten)
uv run python src/evaluate_answers.py --mode summarise
git add data/evaluation/scoring_sheet.csv data/evaluation/scoring_key.csv data/evaluation/key_points.csv \
  data/evaluation/scoring_checks.csv data/evaluation/generation_runs.jsonl
git commit -m "chore(data): Bewertung C1–C3"

# 4. Kontrolle K0 (erst nach scores.csv)
uv run python src/evaluate_answers.py --mode scaffold --control
#    App, Satz „Main catalogue: control K0“: jede Antwort prüfen
uv run python src/evaluate_answers.py --mode summarise --control
git add data/evaluation/scoring_items_control.jsonl data/evaluation/scoring_sheet_control.csv \
  data/evaluation/scoring_checks_control.csv data/evaluation/generation_runs.jsonl
git commit -m "chore(data): Bewertung K0"

# 5. Auswertung für die Arbeit
uv run python src/analyse.py
git add output/tables output/figures output/analysis.json
git commit -m "chore(data): Auswertung des Hauptlaufs"
```

Danach Branch, Pull Request und Submodul-Zeiger: [Ergebnisse in die Arbeit übernehmen](deliver-results-to-thesis.md).
Bricht ein Schritt ab, nennt die Meldung den Befehl, der den fehlenden oder veralteten Laufeintrag schreibt.

**Kosten** (geschätzt aus dem Pilot e2e, 16 Fragen, mal 3 für 48 Fragen): Generierung C1–C3 und K0 etwa 0,04 USD
(Pilot 0,0128 USD), Fragevektoren unter 0,001 USD (Pilot 0,00006 USD); die Closed-Book-Prüfung beim Schreiben des
Katalogs kostet je Durchgang etwa so viel wie K0 (Pilot 0,0006 USD für 16 Fragen). Der Probelauf dieser Befehlsfolge
ist im [Experiment-Protokoll](../reference/experiment-record.md#probelauf-hauptlauf-21102026) festgehalten.

## Schritte

1. Snapshot, Ingest, Preprocessing: siehe [Korpus-Snapshot erstellen](create-corpus-snapshot.md).
2. Chunking für C1–C3 und die Kontrolle K1: `uv run python src/chunking.py`
3. Embeddings und ein Chroma-Index je Strategie (und für K1): `uv run python src/embed.py` (braucht `OPENAI_API_KEY`)
4. Retrieval für C1–C3, danach für die Kontrolle K1 ([ADR 0026](../adr/0026-c3-vergleichbarkeit.md)):
   `uv run python src/retrieve.py` und `uv run python src/retrieve.py --control` (neue Frage-Embeddings brauchen
   `OPENAI_API_KEY`; ohne eingefrorenen Katalog bricht es ab)
5. Antworten generieren (C1–C3 und im selben Lauf die Kontrolle K0 ohne Retrieval, K1 nicht):
   `uv run python src/generate.py` (braucht `OPENAI_API_KEY`; einmal, die Dateien `generated_answers.csv` und
   `generated_answers_control.csv` werden nie überschrieben, [ADR 0033](../adr/0033-antwortmodell.md),
   [ADR 0041](../adr/0041-kontrolle-k0.md))
6. Auswerten: `uv run python src/evaluate_retrieval.py` und `uv run python src/evaluate_retrieval.py --control`; für die Rubrik
   `uv run python src/evaluate_answers.py --mode scaffold`, dann blind bewerten
   ([ADR 0032](../adr/0032-blinde-rubrik-bewertung.md), [ADR 0034](../adr/0034-bewertung-in-der-app.md)): in der App
   (`uv run streamlit run app/catalogue_editor.py --server.address localhost`, Seite „Scoring“), regelbasiert nach
   [ADR 0035](../adr/0035-regelbasierte-bewertung.md): Schritt „Key points“ je Frage 1–4 Kernpunkte prüfen (aus der
   Referenzantwort vorbefüllt, [ADR 0037](../adr/0037-praezisierte-pruefregeln-und-vorbefuellte-kernpunkte.md); nur
   Frage und Referenzantwort sichtbar), wo nötig weiter teilen, speichern und einfrieren (gilt nur für dieses
   Scaffold; nach einem neuen Scaffold erneut einfrieren); Schritt „Score“ je Code die Prüffragen beantworten, die fünf
   Werte folgen aus den Regeln ([Evaluation](../reference/evaluation.md#regelbasierte-bewertung); `notes` frei, z. B.
   wenn eine Regel nicht passt). Von Hand eingetragene Werte nimmt `summarise` bei einem neuen Scaffold nicht an
   ([ADR 0036](../adr/0036-regelbasierte-bewertung-verpflichtend.md)); das Lesepaket `data/evaluation/scoring_packet.md`
   ist nur Lesekopie. Zweitbewertung: siehe [Evaluation](../reference/evaluation.md#zweitbewertung-empfohlen);
   `scoring_key.csv` nie öffnen; zum Schluss `uv run python src/evaluate_answers.py --mode summarise` (schreibt `scores.csv`).
   Fehlt die nicht versionierte `scoring_items.jsonl` (neuer Klon, anderer Rechner), `--mode scaffold` mit denselben
   Optionen erneut ausführen: Er schreibt nur Lesepaket und Einträge neu, Bogen und Schlüssel bleiben unverändert.
7. Kontrolle K0 bewerten, erst nach der C1–C3-Auswertung ([ADR 0041](../adr/0041-kontrolle-k0.md); das Scaffold
   verlangt ein vorhandenes `scores.csv`): K0 nutzt dieselben eingefrorenen Kernpunkte und die Prüffragen ohne
   Quellenbezug und ist nicht blind (ohne Auszüge erkennbar); die Auswertung vergleicht K0 mit C1–C3 über die Kriterien
   aus `config.CONTROL_CRITERIA`, auch getrennt nach dem Closed-Book-Urteil.

   ```bash
   uv run python src/evaluate_answers.py --mode scaffold --control
   # Seite „Scoring“, Satz „Main catalogue: control K0“: jede Antwort prüfen
   uv run python src/evaluate_answers.py --mode summarise --control
   ```

8. Auswertung für die Arbeit, als Letztes, wenn der Hauptkatalog eingefroren ist und alle Ergebnisdateien zu den
   aktuellen Läufen gehören ([ADR 0044](../adr/0044-statistische-auswertung.md)): `uv run python src/analyse.py`.
   Die Retrieval-Metriken aus Schritt 6 haben schon ihren Laufeintrag; nur wenn sie älter sind als das letzte
   Retrieval, `evaluate_retrieval.py` (und `--control`) erneut ausführen.

   `analyse.py` schreibt `output/tables/*.tex`, `output/figures/*.pdf` und `output/analysis.json` und bricht ab, wenn
   der Katalog nicht eingefroren ist oder eine Ergebnisdatei nicht zum letzten Laufeintrag passt (dann den Schritt
   wiederholen); entfallene Teile meldet es als `note:`. Weiter: [Ergebnisse in die Arbeit übernehmen](deliver-results-to-thesis.md).

Optionen der Skripte: [Werkzeuge](../reference/tooling.md); Ausgabedateien: [Datenformate](../reference/data-formats.md).

## Vor jedem Evaluationslauf prüfen

- [ ] Snapshot-Commit in `docs/corpus_snapshot.txt` und im [Experiment-Protokoll](../reference/experiment-record.md)
- [ ] Exakte Modellversionen im Experiment-Protokoll eingetragen
- [ ] `questions.csv` und `ground_truth.csv` fertig und danach unverändert (der Retrieval-Lauf protokolliert ihre
      SHA-256)
- [ ] Jedes Zwischenartefakt gespeichert, nicht nur das Endergebnis (alle Dateien aus
      [Datenformate](../reference/data-formats.md), auch `retrieved_results_control.csv` und die Lauf-Protokolle)
- [ ] Prompts in allen Strategieläufen unverändert, für K0 der Closed-Book-Prompt ([Prompts](../reference/prompts.md))
- [ ] `LLM_TEMPERATURE` und `TOP_K` in `src/config.py` unverändert ([Konfiguration](../reference/configuration.md),
      [ADR 0014](../adr/0014-temperatur-und-topk.md))
