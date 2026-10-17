# Experiment durchführen

> Seitentyp: Anleitung (how-to). Übersicht: [Dokumentation](../README.md).

Voraussetzungen: [Einrichten](set-up.md), [Korpus-Snapshot](create-corpus-snapshot.md), Fragenkatalog und Ground Truth
fertig und eingefroren ([Fragenkatalog erstellen](build-the-question-catalogue.md),
[Fragenkatalog](../reference/question-catalogue.md),
[ADR 0017](../adr/0017-fragenkatalog.md), [ADR 0027](../adr/0027-blinde-annotation.md)). Nur das Chunking variiert
([ADR 0006](../adr/0006-nur-chunking-variiert.md)). Welche Schritte schon umgesetzt sind: [Plan](../plan.md#stand).

## Schritte

1. Snapshot, Ingest, Preprocessing: siehe [Korpus-Snapshot erstellen](create-corpus-snapshot.md).
2. Chunking für C1–C3 und die Kontrolle K1: `uv run python src/chunking.py`
3. Embeddings und ein Chroma-Index je Strategie (und für K1): `uv run python src/embed.py` (braucht `OPENAI_API_KEY`)
4. Retrieval für C1–C3, danach für die Kontrolle K1 ([ADR 0026](../adr/0026-c3-vergleichbarkeit.md)):
   `uv run python src/retrieve.py` und `uv run python src/retrieve.py --control`
5. Antworten generieren (nur C1–C3, K1 nicht): `uv run python src/generate.py` (braucht `OPENAI_API_KEY`; einmal, die
   Datei wird nie überschrieben, [ADR 0033](../adr/0033-antwortmodell.md))
6. Auswerten: `uv run python src/evaluate_retrieval.py` und `uv run python src/evaluate_retrieval.py --control`; für die Rubrik
   `uv run python src/evaluate_answers.py --mode scaffold`, dann blind bewerten
   ([ADR 0032](../adr/0032-blinde-rubrik-bewertung.md), [ADR 0034](../adr/0034-bewertung-in-der-app.md)): in der App
   (`uv run streamlit run app/catalogue_editor.py --server.address localhost`, Seite „Scoring“) je Code 0–2 je Kriterium
   eintragen (`notes` frei). Lesepaket `data/evaluation/scoring_packet.md` und Bogen `data/evaluation/scoring_sheet.csv`
   nur noch für die Zweitbewertung oder ohne App; `scoring_key.csv` dabei nie öffnen; zum Schluss `uv run python src/evaluate_answers.py --mode summarise` (schreibt `scores.csv`).

Optionen der Skripte: [Werkzeuge](../reference/tooling.md); Ausgabedateien: [Datenformate](../reference/data-formats.md).

## Vor jedem Evaluationslauf prüfen

- [ ] Snapshot-Commit in `docs/corpus_snapshot.txt` und im [Experiment-Protokoll](../reference/experiment-record.md)
- [ ] Exakte Modellversionen im Experiment-Protokoll eingetragen
- [ ] `questions.csv` und `ground_truth.csv` fertig und danach unverändert (der Retrieval-Lauf protokolliert ihre
      SHA-256)
- [ ] Jedes Zwischenartefakt gespeichert, nicht nur das Endergebnis (alle Dateien aus
      [Datenformate](../reference/data-formats.md), auch `retrieved_results_control.csv` und die Lauf-Protokolle)
- [ ] Prompts in allen Strategieläufen unverändert ([Prompts](../reference/prompts.md))
- [ ] `LLM_TEMPERATURE` und `TOP_K` in `src/config.py` unverändert ([Konfiguration](../reference/configuration.md),
      [ADR 0014](../adr/0014-temperatur-und-topk.md))
