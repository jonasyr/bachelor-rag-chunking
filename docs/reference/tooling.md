# Werkzeuge und Repository

> Seitentyp: Nachschlagen (reference). Stand: 14.10.2026. Übersicht: [Dokumentation](../README.md).

## Tech-Stack

Entscheidungen: [ADR 0015](../adr/0015-tech-stack.md) (Stack), [ADR 0016](../adr/0016-modell-neutralitaet.md)
(Modellwahl), [ADR 0023](../adr/0023-embedding-modell.md) (Embedding-Modell und Pins). Parameterwerte:
[Konfiguration](configuration.md). Abhängigkeiten und Pins: `pyproject.toml`, `uv.lock`.

| Zweck | Werkzeug |
|-------|----------|
| Sprache | Python ≥ 3.11 |
| Paketverwaltung | **uv** + `pyproject.toml` (inkl. `uv.lock` für reproduzierbare Installs; Gruppe `dev`: pytest, Jupyter) |
| Dokumentverarbeitung | Standardbibliothek: `re`, `html`, `pathlib`, `csv`, `json` (`src/preprocess.py`) |
| Token-Zählung | `tiktoken` 0.13.0 (gepinnt), gekapselt in `src/tokens.py` ([ADR 0019](../adr/0019-korpus-ausschnitt.md)) |
| Embeddings | OpenAI API (`openai` 2.44.0, gepinnt), Modell `config.EMBEDDING_MODEL` ([ADR 0023](../adr/0023-embedding-modell.md)) |
| Vector Store | Chroma (`chromadb` 1.5.9, gepinnt; lokal, persistent; Kosinus, exakte Suche geprüft; [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)) |
| Numerik | NumPy (Vektordateien `.npz`, exakter Kosinus) |
| LLM | `gpt-6-luna` über die OpenAI Chat Completions API, Effort `none`, Temperatur 0 (`src/llm_client.py`, [ADR 0033](../adr/0033-antwortmodell.md)) |
| Umgebung | `python-dotenv` (`.env`) |
| Datenanalyse | Pandas |
| Diagramme | Matplotlib / Plotly |
| App/Dashboard | Streamlit (`app/catalogue_editor.py`, später `app/streamlit_app.py`) |
| Evaluation | eigene Skripte + optional RAGAS |

Pandas, Matplotlib/Plotly, Streamlit und RAGAS sind deklariert, werden aber erst in der Auswertung genutzt.

`OPENAI_API_KEY` (aus der Umgebung oder `.env`) wird nur gelesen, wenn ein Schritt die API aufruft
(`src/embedding_client.py`: `embed.py` und `retrieve.py` bei neuen Vektoren; `src/llm_client.py`: `generate.py`). Tests und die
übrigen Schritte brauchen keinen Schlüssel; fehlt er bei einem API-Aufruf, bricht der Schritt mit einer Meldung ab.

## Repository-Struktur

```
bachelor-rag-chunking/
├── README.md  AGENTS.md  CLAUDE.md          (Einstieg; CLAUDE.md enthält nur @AGENTS.md)
├── pyproject.toml  uv.lock  .env.example  .pre-commit-config.yaml
├── LICENSE  LICENSES/                       (MIT; Apache-2.0 für die Codex-Rubrik, siehe README)
├── .github/workflows/ci.yml                 (CI)
├── .claude/  .codex/                        (Agenten-Einstellungen, u. a. codex-reviewer)
├── .serena/                                 (Agenten-Notizen, versioniert)
├── src/
│   ├── config.py                            (alle Parameter; Konfiguration)
│   ├── snapshot.py  ingest.py  preprocess.py  tokens.py
│   ├── chunking.py
│   ├── embedding_client.py  canary.py  embed.py  run_log.py
│   ├── llm_client.py  prompt.py
│   ├── vector_index.py  relevance.py  retrieve.py  freeze.py
│   ├── catalogue.py                         (Fragenkatalog: Plan, Nachschlageliste, Suche, Prüfung, Einfrieren)
│   ├── catalogue_plan.py  catalogue_review.py  catalogue_store.py  atomic_csv.py
│   └── generate.py  evaluate_retrieval.py  evaluate_answers.py
├── scripts/
│   ├── difficulty_probe.py                  (Pilotproben)
│   ├── remap_pilot.py                       (einmalig: Pilot-IDs auf neuen Korpus abbilden)
│   └── corpus_probe/                        (Korpusauswahl: Lückentext-Probe, ADR 0038)
├── tests/                                   (pytest; conftest.py, test_*.py)
├── data/
│   ├── raw/vue_docs_snapshot/               (Snapshot: api/, guide/, style-guide/)
│   ├── processed/                           (documents, sections, chunks_*, embeddings_*, embedding_runs)
│   ├── evaluation/                          (questions, ground_truth, query_embeddings, retrieved_results*, generation_runs, …)
│   ├── pilot/                               (Pilot-Sets: ., hard/, hard_posthoc/)
│   └── corpus_probe/                        (Korpusauswahl: Kandidaten, Ergebnisse, Wertung)
├── chroma_db/                               (Chroma-Index, entsteht beim ersten embed.py)
├── output/                                  (tables/*.tex, figures/*.pdf; entsteht mit der Auswertung)
├── notebooks/analysis.ipynb
├── app/catalogue_editor.py                  (Router der App, nur localhost)
├── app/catalogue_page.py                    (Seite „Catalogue“: Editor des Fragenkatalogs)
├── app/scoring_page.py                      (Seite „Scoring“: blinde Bewertung)
├── app/ui_theme.py                          (gemeinsames Theme der Seiten)
├── app/streamlit_app.py                     (spätere RAG-Demo)
├── .streamlit/config.toml                   (Thema und localhost-Bindung des Editors)
└── docs/
    ├── README.md                            (Index der Dokumentation)
    ├── plan.md                              (Zeitplan, Stand, offene Entscheidungen)
    ├── explanation/  how-to/  reference/    (Diátaxis; reference/configuration.md = config.py)
    ├── adr/                                 (Entscheidungen 0001–0031)
    ├── superpowers/specs/  superpowers/plans/   (datierte Entwürfe und Umsetzungspläne; Momentaufnahmen)
    ├── corpus_snapshot.txt                  (Snapshot-Datensatz)
    └── corpus_manifest.csv                  (Korpusmanifest)
```

Dateien in `data/` und ihre Formate: [Datenartefakte und Formate](data-formats.md).

## Versioniert und ignoriert

Nach `.gitignore`:

| Pfad | Status |
|---|---|
| `data/raw/vue_docs_snapshot/*`, `data/processed/*` | ignoriert; die Ordner bleiben über `.gitkeep` erhalten |
| `chroma_db/` | ignoriert (ganzer Ordner, kein `.gitkeep`; entsteht beim ersten `embed.py`) |
| `data/evaluation/retrieved_results*.csv`, `retrieval_scores*.csv`, `scoring_packet.md`, `scoring_items.jsonl`, `scores.csv`, `query_embeddings.npz` | ignoriert |
| `data/evaluation/generated_answers.csv` (Primärdaten, nicht exakt wiederholbar, [ADR 0033](../adr/0033-antwortmodell.md)), `scoring_sheet.csv`, `scoring_key.csv`, `key_points.csv`, `scoring_checks.csv` (Primärdaten der Bewertung) | versioniert |
| `data/evaluation/questions.csv`, `ground_truth.csv`, `catalogue_plan.csv`, `catalogue_review.csv`, `catalogue_freeze.json`, `generation_runs.jsonl` | versioniert |
| `data/pilot/**/query_embeddings.npz`, `scoring_packet.md`, `scoring_items.jsonl`, `scores.csv` | ignoriert; alle übrigen Pilotdateien versioniert |
| `*.pdf` | ignoriert, außer `output/figures/*.pdf` |
| `docs/corpus_snapshot.txt`, `docs/corpus_manifest.csv` | versioniert |
| `.env`, `.venv/`, `__pycache__/`, `.vscode/` | ignoriert |

## Skripte und Optionen

Alle Schritte laufen aus der Repo-Wurzel (`uv run python src/<schritt>.py` bzw. `scripts/<skript>.py`, Optionen mit
`--help`); Reihenfolge: `README.md`. Stand der Umsetzung: [Plan](../plan.md#stand).

| Skript | Optionen |
|---|---|
| `snapshot.py`, `ingest.py`, `preprocess.py` | keine |
| `chunking.py`, `embed.py` | `--strategy C1\|C2\|C3\|K1\|all` (Standard `all` = C1–C3, dann die Kontrolle K1; [ADR 0026](../adr/0026-c3-vergleichbarkeit.md)) |
| `retrieve.py` | ohne Option alle Strategien C1–C3 ([ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)); `--control` nur die Kontrolle K1; bricht auf dem Hauptkatalog ohne passenden Freeze-Datensatz ab ([ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md)) |
| `catalogue.py` | `plan` (Stichprobenplan einmal ziehen, [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md)), `sections` (Nachschlageliste schreiben), `find TERM` (wörtliche Suche, Groß-/Kleinschreibung egal, nur der innerste Abschnitt), `show SECTION_ID`, `check [--draft]` (Abdeckungsprüfung; `--draft` scheitert nur an Fehlern), `freeze` (strenge Prüfung, dann Freeze-Datensatz); [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md), [ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md) |
| `app/catalogue_editor.py` | `uv run streamlit run app/catalogue_editor.py --server.address localhost` (die Option bindet unabhängig vom Arbeitsverzeichnis; `.streamlit/config.toml` gilt nur beim Start aus der Repo-Wurzel); zwei Seiten: „Catalogue“ (schreibgeschützt nach dem Einfrieren, [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md)) und „Scoring“ (blinde Bewertung, schreibgeschützt nach dem Entblinden, [ADR 0034](../adr/0034-bewertung-in-der-app.md)) |
| `generate.py` | ohne Option alle Strategien C1–C3 in einem Lauf (K1 bekommt keine Antworten, [ADR 0026](../adr/0026-c3-vergleichbarkeit.md)); `--set DIR` ein Pilot-Set (z. B. `data/pilot/hard`); braucht `OPENAI_API_KEY`; überschreibt nie eine vorhandene `generated_answers.csv`, bricht vor dem ersten API-Aufruf ab, wenn die Ergebnisdatei nicht aus dem letzten Retrieval-Lauf über die aktuellen Fragen und Chunk-Dateien stammt, und ohne Schreiben bei abgeschnittener oder leerer Antwort oder wechselndem Modell oder Fingerabdruck, auf dem Hauptkatalog ohne passenden Freeze-Datensatz ([ADR 0033](../adr/0033-antwortmodell.md), [ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md)) |
| `evaluate_retrieval.py` | `--control` die Kontrolle K1; k ist immer `config.TOP_K` ([ADR 0014](../adr/0014-temperatur-und-topk.md)); schreibt `retrieval_scores*.csv` und gibt die Mittel je Strategie, Fragetyp und Konstruktionsklasse für Haupt- und Sensitivitätsregel aus; bricht auf dem Hauptkatalog ohne passenden Freeze-Datensatz ab und wenn `is_relevant` nicht zur Ground Truth passt |
| `evaluate_answers.py` | `--mode scaffold\|summarise` (Pflicht): `scaffold` schreibt aus `generated_answers.csv` Lesepaket, Bewertungsbogen und Schlüssel der blinden Bewertung ([ADR 0032](../adr/0032-blinde-rubrik-bewertung.md); nie über einen vorhandenen Bogen oder Schlüssel; nur, wenn Antworten und Chunk-Dateien die des letzten Generierungslaufs sind, [ADR 0033](../adr/0033-antwortmodell.md)); beide nur mit eingefrorenem Hauptkatalog ([ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md)) und nur, wenn jede Frage des Katalogs genau eine Zeile je Strategie C1–C3 hat; `summarise` prüft den Bogen gegen den Schlüssel und jede Bewertung (ganze Zahl 0–2), schreibt `scores.csv` mit `total_score` und gibt Mittel, Median und Standardabweichung je Strategie, Fragetyp und Konstruktionsklasse aus; `--set DIR` ein Pilot-Set (Dateien im Set-Ordner, Antworten aus `generate.py --set`), `--limit N` nur mit `--set`: die ersten N Fragen nach ID (in beiden Modi gleich angeben; der Hauptkatalog wird immer vollständig bewertet) |
| `scripts/difficulty_probe.py` | `[SET_DIR]`: Pilot-Set, relativ zur Repo-Wurzel (Standard `config.PILOT_DIR` = `data/pilot`); läuft C1–C3 und K1, schreibt die Ergebnisdateien des Sets; Sets: [Datenformate](data-formats.md#pilot-sets) |
| `scripts/remap_pilot.py` | einmalig: `OLD_DIR PILOT_DIR [PILOT_DIR …]` (Pfade relativ zum Arbeitsverzeichnis, also der Repo-Wurzel); bildet die Pilot-Ground-Truth über Pfad und Anker auf neue IDs ab und überschreibt sie ([ADR 0025](../adr/0025-korpus-guide-api-styleguide.md)) |
| `scripts/corpus_probe/` | `probe_corpus.sh NAME [--recorded]` (ein Kandidat aus `candidates.csv` auf seinem Commit; ruft die OpenAI-API; `--recorded` wiederholt die aufgezeichneten Proben), einzeln `to_docs.py NAME SOURCE`, `build_probes.py NAME [--recorded]`, `run_probes.py NAME PRODUCT`; `summarise.py` (Wertung aus den abgelegten Daten, ohne API); `question_probe.py sample|answer|blind|unblind|summary` (Closed-Book-Fragen, `answer` ruft die API); Verfahren: [Korpusauswahl](corpus-selection.md) |

## Qualitätswerkzeuge

| Werkzeug | Was | Wo |
|---|---|---|
| ruff | Lint (E, F, W, I, B, UP; F401 bis zur Implementierung aus) und Formatierung, Zeilenlänge 100 | `pyproject.toml` `[tool.ruff]` |
| pre-commit | ruff (mit `--fix`) und ruff-format, große Dateien (> 5 MB), private Schlüssel, Merge-Konflikte, YAML/TOML, Zeilenende am Dateiende, Leerzeichen am Zeilenende | `.pre-commit-config.yaml` |
| pytest | siehe [Tests](#tests) | `tests/`, `pyproject.toml` `[tool.pytest.ini_options]` |
| Pyright (Editor) | Typprüfung mit uv-venv und `src/` als Importpfad | `pyproject.toml` `[tool.pyright]` |
| GitHub Actions | `uv sync`, alle pre-commit-Hooks, `compileall` für `src/` und `app/`, `pytest` (bei Push auf `main` und jedem Pull Request) | `.github/workflows/ci.yml` |

## Tests

- Konfiguration: `pythonpath = ["src"]` (Tests importieren Module über den bloßen Namen, z. B. `import chunking`),
  `testpaths = ["tests"]`.
- Fixture `fake_embedder` (`tests/conftest.py`): `FakeEmbedder` liefert deterministische 16-dimensionale
  Einheitsvektoren aus dem Text-Hash und zeichnet jeden Aufruf auf; ein anderer `salt` simuliert ein geändertes Modell
  hinter demselben Namen. Kein Test ruft die OpenAI API auf.
- Korpus-Integrationstests (`tests/test_corpus_integration.py`) werden übersprungen, solange (1) kein Snapshot in
  `data/raw/vue_docs_snapshot/` liegt (Bereichsordner fehlen), (2) `data/processed/sections.jsonl` fehlt (nicht vorverarbeitet) oder (3) die
  Vektordatei einer Strategie fehlt (nicht eingebettet). In CI greifen alle drei.
