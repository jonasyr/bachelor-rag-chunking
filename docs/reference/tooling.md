# Werkzeuge und Repository

*[Doku-Index](../README.md) · Referenz · Verwandt: [Konfiguration](configuration.md), [Datenformate](data-formats.md), [Experiment durchführen](../how-to/run-the-experiment.md)*

Stand: 22.10.2026.

## Tech-Stack

Entscheidungen: [ADR 0015](../adr/0015-tech-stack.md) (Stack), [ADR 0016](../adr/0016-modell-neutralitaet.md)
(Modellwahl), [ADR 0023](../adr/0023-embedding-modell.md) (Embedding-Modell und Pins). Parameterwerte:
[Konfiguration](configuration.md). Abhängigkeiten und Pins: `pyproject.toml`, `uv.lock`.

| Zweck | Werkzeug |
|-------|----------|
| Sprache | Python ≥ 3.11 |
| Paketverwaltung | **uv** + `pyproject.toml` (inkl. `uv.lock` für reproduzierbare Installs; Gruppe `dev`: pytest) |
| Dokumentverarbeitung | Standardbibliothek: `re`, `pathlib`, `csv`, `json` (`src/mdx.py`, `src/preprocess.py`) |
| Markdown-Darstellung | `markdown-it-py` (formatierte Ansicht in der App: `src/catalogue_store.py`, `src/scoring_store.py`) |
| Token-Zählung | `tiktoken` 0.13.0 (gepinnt), gekapselt in `src/tokens.py` ([ADR 0019](../adr/0019-korpus-ausschnitt.md)) |
| Embeddings | OpenAI API (`openai` 2.44.0, gepinnt), Modell `config.EMBEDDING_MODEL` ([ADR 0023](../adr/0023-embedding-modell.md)) |
| Vector Store | Chroma (`chromadb` 1.5.9, gepinnt; lokal, persistent; Kosinus, exakte Suche geprüft; [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)) |
| Numerik | NumPy (Vektordateien `.npz`, exakter Kosinus) |
| Statistik | SciPy (`scipy` 1.17.1, gepinnt; Friedman-, Wilcoxon-Test, Spearman in `src/stats.py`, [ADR 0044](../adr/0044-statistische-auswertung.md)) |
| LLM | `config.LLM_MODEL` über die OpenAI Chat Completions API, `config.LLM_REASONING_EFFORT`, `config.LLM_TEMPERATURE` (`src/llm_client.py`, [ADR 0033](../adr/0033-antwortmodell.md)) |
| Umgebung | `python-dotenv` (`.env`) |
| Datenanalyse | Pandas |
| Diagramme | Matplotlib (PDF-Abbildungen der Auswertung, `src/report_figures.py`) |
| App/Dashboard | Streamlit (`app/catalogue_editor.py` mit den Seiten Catalogue und Scoring) |
| Evaluation | eigene Skripte (regelbasierte Bewertung, [ADR 0035](../adr/0035-regelbasierte-bewertung.md)); RAGAS als feste Triangulation nach der regelbasierten Bewertung ([ADR 0047](../adr/0047-ragas-als-triangulation.md)) |

RAGAS läuft in `src/ragas_eval.py` ([Pins](#ragas-pins)). Telemetrie: Chroma bleibt abgeschaltet
([ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)); zu RAGAS siehe
[Umgebungsvariablen](#umgebungsvariablen).

### RAGAS-Pins

`ragas` 0.4.3 und `langchain-community` 0.4.1 sind in `pyproject.toml` exakt gepinnt. `ragas` bestimmt Prompts,
Rechenweg und die NaN-Fälle der Metriken (die Begründungen in `config.RAGAS_NAN_REASONS` nennen Stellen im Code dieser
Version), und `JudgeLLM` in `src/ragas_client.py` hängt an einer internen Methode; ein anderer Stand ändert die Werte
oder bricht den Aufbau (ein Test prüft die Bindung an die Version). `langchain-community` 0.4.2 hat ein Modul
entfernt, das `ragas` 0.4.3 noch importiert. Verfahren und Begründung der Einstellungen:
[Evaluation](evaluation.md#triangulation).

## Repository-Struktur

```
bachelor-rag-chunking/
├── README.md  AGENTS.md  CLAUDE.md     (Einstieg; CLAUDE.md enthält nur @AGENTS.md)
├── pyproject.toml  uv.lock  .env.example  .pre-commit-config.yaml
├── LICENSE  LICENSES/                  (MIT; Apache-2.0, siehe README)
├── .github/workflows/ci.yml            (CI)
├── .claude/  .codex/  .serena/         (Agenten-Einstellungen, codex-reviewer, Agenten-Notizen; versioniert)
├── src/                                (Pipeline; alle Parameter in config.py)
│   ├── snapshot.py ingest.py preprocess.py mdx.py    (Korpus)
│   ├── chunking.py embed.py retrieve.py               (Chunks, Vektoren, Retrieval)
│   ├── catalogue.py freeze.py closed_book.py          (Fragenkatalog, Einfrieren, Closed-Book-Prüfung)
│   ├── generate.py evaluate_retrieval.py evaluate_answers.py control_k0.py
│   ├── ragas_eval.py ragas_client.py                  (RAGAS, ADR 0047)
│   ├── second_rater.py agreement.py                   (Zweitbewertung und Übereinstimmung, ADR 0046)
│   ├── analyse.py analysis_data.py stats.py           (Auswertung, Tests und Effektstärken, ADR 0044)
│   ├── report_tables.py report_figures.py             (LaTeX-Tabellen, PDF-Abbildungen)
│   └── …                                              (Hilfsmodule, z. B. tokens.py, run_log.py, scoring_store.py)
├── app/                                (Streamlit: catalogue_editor.py = Router, Seiten Catalogue und Scoring)
├── .streamlit/config.toml              (Thema und localhost-Bindung der App)
├── scripts/                            (difficulty_probe.py, remap_pilot.py (historisch), corpus_probe/)
├── tests/                              (pytest, siehe Tests)
├── data/
│   ├── raw/e2e_docs_snapshot/          (Snapshot, nicht versioniert)
│   ├── processed/                      (documents, sections, chunks_*, embeddings_*, embedding_runs)
│   ├── evaluation/                     (Katalog, Ground Truth, Ergebnisse, second_rater/; archive_vue/)
│   ├── pilot/                          (Pilot-Sets: e2e/ (aktuell), e2e_jonas/; ., hard/, hard_posthoc/
│   │                                    historisch, Vue-IDs)
│   └── corpus_probe/                   (Korpusauswahl: Kandidaten, Ergebnisse, Wertung)
├── chroma_db/                          (Chroma-Index, entsteht beim ersten embed.py)
├── output/                             (tables/, figures/, analysis.json; schreibt analyse.py)
└── docs/                               (Index: docs/README.md)
```

Dateien in `data/` und ihre Formate: [Datenartefakte und Formate](data-formats.md); welche Dateien versioniert und
welche ignoriert sind: [Versioniert und ignoriert](data-formats.md#versioniert-und-ignoriert).

## Skripte und Optionen

Alle Schritte laufen aus der Repo-Wurzel (`uv run python src/<schritt>.py` bzw. `scripts/<skript>.py`); Reihenfolge:
[Experiment durchführen](../how-to/run-the-experiment.md). `--help` zeigt die Optionen nur bei den Skripten mit
argparse (`chunking.py`, `embed.py`, `retrieve.py`, `catalogue.py`, `generate.py`, `evaluate_retrieval.py`,
`evaluate_answers.py`, `second_rater.py`, `ragas_eval.py`, `analyse.py`). `snapshot.py`, `ingest.py` und
`preprocess.py` lesen keine Argumente: auch mit `--help` führen sie den Schritt aus, und `snapshot.py` lädt den Korpus
(flacher `git fetch`) und ersetzt den Inhalt von `data/raw/e2e_docs_snapshot/`.

| Skript | Optionen |
|---|---|
| `snapshot.py`, `ingest.py`, `preprocess.py` | keine (siehe oben); `preprocess.py` verweigert eine schon aufbereitete `documents.jsonl` (vorher `ingest.py`), und `chunking.py` bricht ab, wenn `sections.jsonl` nicht zu `documents.jsonl` passt ([Korpus-Snapshot erstellen](../how-to/create-corpus-snapshot.md)) |
| `chunking.py`, `embed.py` | `--strategy C1\|C2\|C3\|K1\|all` (Standard `all` = C1–C3, dann die Kontrolle K1; [ADR 0026](../adr/0026-c3-vergleichbarkeit.md)) |
| `retrieve.py` | ohne Option alle Strategien C1–C3 ([ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)); `--control` nur die Kontrolle K1; bricht auf dem Hauptkatalog ohne passenden Freeze-Datensatz ab ([ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md)) |
| `catalogue.py` | `plan` (Stichprobenplan einmal ziehen, [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md)), `sections` (Nachschlageliste schreiben), `find TERM` (wörtliche Suche, Groß-/Kleinschreibung egal, nur der innerste Abschnitt), `show SECTION_ID`, `check [--draft]` (Abdeckungsprüfung; `--draft` scheitert nur an Fehlern), `screen` (Closed-Book-Antworten neuer oder geänderter Fragen nach `closed_book_screen.csv`; ruft die API; verweigert nach dem Einfrieren; [ADR 0040](../adr/0040-closed-book-pruefung.md)), `freeze` (strenge Prüfung einschließlich Closed-Book-Prüfung: jede Frage geprüft und beurteilt, Anteil `config.CLOSED_BOOK_MIN_DEPENDENT_SHARE` retrieval-abhängig; dann Freeze-Datensatz); [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md), [ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md) |
| `app/catalogue_editor.py` | `uv run streamlit run app/catalogue_editor.py --server.address localhost` (die Option bindet unabhängig vom Arbeitsverzeichnis; `.streamlit/config.toml` gilt nur beim Start aus der Repo-Wurzel); zwei Seiten: „Catalogue“ (Reiter Write, Review und Closed-book, im letzten die Urteile `hit`/`miss`, [ADR 0040](../adr/0040-closed-book-pruefung.md); schreibgeschützt nach dem Einfrieren, [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md)) und „Scoring“ (blinde Bewertung, schreibgeschützt nach dem Entblinden, [ADR 0034](../adr/0034-bewertung-in-der-app.md)); mit `SCORING_RATER=R2` nur „Scoring“ mit dem Satz der zweiten Person ([ADR 0046](../adr/0046-zweitbewertung.md); siehe [Umgebungsvariablen](#umgebungsvariablen)) |
| `generate.py` | ohne Option alle Strategien C1–C3 und im selben Lauf die Kontrolle K0 ohne Retrieval (`generated_answers_control.csv`, [ADR 0041](../adr/0041-kontrolle-k0.md); K1 bekommt keine Antworten, [ADR 0026](../adr/0026-c3-vergleichbarkeit.md)); `--set DIR` ein Pilot-Set (z. B. `data/pilot/hard`); braucht `OPENAI_API_KEY`; überschreibt nie eine vorhandene `generated_answers.csv` oder `generated_answers_control.csv`, bricht vor dem ersten API-Aufruf ab, wenn die Ergebnisdatei nicht aus dem letzten Retrieval-Lauf über die aktuellen Fragen und Chunk-Dateien stammt, und ohne Schreiben bei abgeschnittener oder leerer Antwort, wechselndem Modell oder Fingerabdruck oder geänderter Erstellzeit des Modells hinter dem Alias; auf dem Hauptkatalog ohne passenden Freeze-Datensatz ([ADR 0033](../adr/0033-antwortmodell.md), [ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md)) |
| `evaluate_retrieval.py` | `--control` die Kontrolle K1; `--set DIR` ein Pilot-Set (Dateien und `runs.jsonl` im Set-Ordner); trägt einen Eintrag `evaluate_retrieval` ins Laufprotokoll ein ([Datenformate](data-formats.md#laufprotokoll)); k ist immer `config.TOP_K` ([ADR 0014](../adr/0014-temperatur-und-topk.md)); schreibt `retrieval_scores*.csv` und gibt die Mittel je Strategie, Fragetyp und Konstruktionsklasse für Haupt- und Sensitivitätsregel aus; bricht auf dem Hauptkatalog ohne passenden Freeze-Datensatz ab und wenn `is_relevant` nicht zur Ground Truth passt |
| `evaluate_answers.py` | `--mode scaffold\|summarise` (Pflicht): `scaffold` schreibt aus `generated_answers.csv` Lesepaket, Bewertungsbogen, Schlüssel und Einträge der Bewertungsseite (`scoring_items.jsonl`, [ADR 0034](../adr/0034-bewertung-in-der-app.md)) der blinden Bewertung ([ADR 0032](../adr/0032-blinde-rubrik-bewertung.md); nie über einen vorhandenen Bogen oder Schlüssel; nur, wenn Antworten und Chunk-Dateien die des letzten Generierungslaufs sind, [ADR 0033](../adr/0033-antwortmodell.md)); beide nur mit eingefrorenem Hauptkatalog ([ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md)) und nur, wenn jede Frage des Katalogs genau eine Zeile je Strategie C1–C3 hat; `summarise` prüft den Bogen gegen den Schlüssel und jede Bewertung (ganze Zahl 0–2), prüft mit `scoring_checks.csv` die eingefrorenen Kernpunkte und jede Bogenzeile gegen die aktuellen Regeln ([ADR 0035](../adr/0035-regelbasierte-bewertung.md), [ADR 0036](../adr/0036-regelbasierte-bewertung-verpflichtend.md)), schreibt `scores.csv` mit `total_score` und gibt Mittel, Median und Standardabweichung je Strategie, Fragetyp und Konstruktionsklasse aus; `--set DIR` ein Pilot-Set (Dateien im Set-Ordner, Antworten aus `generate.py --set`), `--limit N` nur mit `--set`: die ersten N Fragen nach ID (in beiden Modi gleich angeben; der Hauptkatalog wird immer vollständig bewertet); `--control` dieselben Modi für die Kontrolle K0 (`src/control_k0.py`, [ADR 0041](../adr/0041-kontrolle-k0.md)): `scaffold` erst, wenn `scores.csv` existiert, für deren Fragen; `summarise` schreibt `scores_control.csv` und vergleicht K0 mit C1–C3 über `config.CONTROL_CRITERIA`, auch nach Closed-Book-Urteil; nicht mit `--limit` |
| `second_rater.py` | Zweitbewertung ([ADR 0046](../adr/0046-zweitbewertung.md)): `--mode draw` zieht die 12 Fragen (nach dem Einfrieren, vor eigenen Werten; überschreibt nie), `--mode export` schreibt den Satz für R2 nach `data/evaluation/second_rater/`, `--mode close` schließt R2s Bewertung ab; `--set DIR` ein Pilot-Set (die Prüfungen auf eigene Werte und `scores.csv` warnen dort nur), `--questions N` nur mit `--mode draw --set`; Verfahren: [Evaluation](evaluation.md#zweitbewertung) |
| `ragas_eval.py` | ohne Option die Antworten C1–C3 des Hauptkatalogs nach `data/evaluation/ragas_scores.csv` ([ADR 0047](../adr/0047-ragas-als-triangulation.md)); `--set DIR` ein Pilot-Set (Dateien und `runs.jsonl` im Set-Ordner); `--repeat` (nur mit Pilot-Set) ein zweiter Lauf nach `ragas_scores_repeat.csv`, setzt den passenden `ragas`-Eintrag voraus; braucht `OPENAI_API_KEY`; überschreibt nie, bricht vor dem ersten API-Aufruf ab, wenn der Katalog nicht eingefroren ist, `generated_answers.csv` nicht aus dem letzten `generate`-Lauf stammt oder (Hauptkatalog) der `summarise`-Eintrag fehlt, und ohne Schreiben bei ungültigem Wert, Fehler des Richters oder wechselndem Modell, Fingerabdruck oder Erstellzeit; Formate: [Datenformate](data-formats.md#ragas), Verfahren: [Evaluation](evaluation.md#triangulation) |
| `analyse.py` | ohne Option die Auswertung des Hauptkatalogs nach `output/` (nur bei eingefrorenem Katalog und aktuellen Laufeinträgen von `evaluate_retrieval`, `summarise`, `summarise_control`); `--set DIR` ein Pilot-Set, schreibt nach `DIR/output/` (fehlt einem Pilot ein Laufeintrag, mit Hinweis); gibt die Hinweise zu entfallenen Teilen aus; Verfahren: [Evaluation](evaluation.md#statistische-auswertung), [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `scripts/difficulty_probe.py` | `SET_DIR` (Pflicht): Pilot-Set relativ zur Repo-Wurzel, auf dem e2e-Korpus `data/pilot/e2e`; die Vue-Sets laufen nur gegen einen wiederhergestellten Vue-Korpus; läuft C1–C3 und K1, schreibt die Ergebnisdateien des Sets; Sets: [Datenformate](data-formats.md#pilot-sets) |
| `scripts/remap_pilot.py` | einmalig, historisch (Korpuswechsel innerhalb von Vue.js; gilt nicht für e2e): `OLD_DIR PILOT_DIR [PILOT_DIR …]` (Pfade relativ zum Arbeitsverzeichnis, also der Repo-Wurzel); bildet die Pilot-Ground-Truth über Pfad und Anker auf neue IDs ab und überschreibt sie ([ADR 0025](../adr/0025-korpus-guide-api-styleguide.md)) |
| `scripts/corpus_probe/` | `probe_corpus.sh NAME [--recorded]` (ein Kandidat aus `candidates.csv` auf seinem Commit; ruft die OpenAI-API; `--recorded` wiederholt die aufgezeichneten Proben), einzeln `to_docs.py NAME SOURCE`, `build_probes.py NAME [--recorded]`, `run_probes.py NAME "PRODUCT" [--recorded]`; `summarise.py` (Wertung aus den abgelegten Daten, ohne API); `question_probe.py sample NAME…`, `answer NAME…`, `blind BATCH NAME…`, `unblind`, `summary` (Closed-Book-Fragen, `answer` ruft die API); Verfahren: [Korpusauswahl](corpus-selection.md) |

## Umgebungsvariablen

| Variable | Wirkung |
|---|---|
| `OPENAI_API_KEY` | Aus der Umgebung oder `.env` (`python-dotenv`); gelesen nur, wenn ein Schritt die API aufruft: `src/embedding_client.py` für `embed.py` und `retrieve.py` (bei neuen Fragevektoren, auch über `scripts/difficulty_probe.py`), `src/llm_client.py` für `generate.py` und `catalogue.py screen`, `src/ragas_client.py` für `ragas_eval.py`, außerdem `scripts/corpus_probe/run_probes.py` und `question_probe.py answer` (auch über `probe_corpus.sh`). Fehlt er bei einem API-Aufruf, bricht der Schritt mit einer Meldung ab. Tests und alle übrigen Schritte brauchen ihn nicht. |
| `SCORING_RATER` | Name aus `config.SECOND_RATER_ENV`. Ungesetzt: die volle App. `R2`: nur die Seite „Scoring“ mit dem Satz der zweiten Person ([ADR 0046](../adr/0046-zweitbewertung.md)). Jeder andere Wert bricht ab (`scoring_store.rater_mode`), damit ein Tippfehler nie die eigenen Sätze zeigt. |
| `PAPERLAB_FONTS` | Ordner mit der Schrift `config.FIGURE_FONT_FILE` (Arial) für die Abbildungen von `analyse.py`. Ungesetzt sucht `src/report_figures.py` im Ordner `fonts/` eines umgebenden PaperLab-Checkouts; ohne Fund zeichnet es in DejaVu Sans und gibt einen Hinweis aus. Nötig in einem eigenständigen Klon dieses Repos. |
| `RAGAS_DO_NOT_TRACK` | Wird nicht gelesen, sondern gesetzt: `src/ragas_client.py` setzt sie vor dem ersten RAGAS-Import aus `config.RAGAS_DO_NOT_TRACK` (`true`), `tests/conftest.py` beim Import. Das unterbindet nur das Senden der Nutzungsdaten; RAGAS 0.4.3 legt trotzdem eine zufällige Kennung unter `~/.local/share/ragas/uuid.json` an (keine personenbezogenen Daten, kein Netz). |

## Qualitätswerkzeuge

| Werkzeug | Was | Wo |
|---|---|---|
| ruff | Lint (E, F, W, I, B, UP; F401 bleibt vorerst aus; der Grund in `pyproject.toml`, ein noch nicht umgesetztes Gerüst, ist überholt und neu zu prüfen) und Formatierung, Zeilenlänge 100 | `pyproject.toml` `[tool.ruff]` |
| pre-commit | ruff (mit `--fix`) und ruff-format, große Dateien (> 5 MB), private Schlüssel, Merge-Konflikte, YAML/TOML, Zeilenende am Dateiende, Leerzeichen am Zeilenende | `.pre-commit-config.yaml` |
| pytest | siehe [Tests](#tests) | `tests/`, `pyproject.toml` `[tool.pytest.ini_options]` |
| Pyright (Editor) | Typprüfung mit uv-venv und `src/` als Importpfad | `pyproject.toml` `[tool.pyright]` |
| GitHub Actions | `uv sync`, alle pre-commit-Hooks, `compileall` für `src/` und `app/`, `pytest` (bei Push auf `main` und jedem Pull Request) | `.github/workflows/ci.yml` |

## Tests

- Konfiguration: `pythonpath = ["src"]` (Tests importieren Module über den bloßen Namen, z. B. `import chunking`),
  `testpaths = ["tests"]`.
- Kein Netz: Tests rufen nie die OpenAI-API auf und erreichen kein Netz außer dem einmaligen Download der
  `tiktoken`-Kodierung `cl100k_base`; die Snapshot-Tests nutzen ein lokales Git-Repository, `test_ragas_client.py`
  einen `httpx.MockTransport`. Ein Test, der anderes erreichen kann, ist ein P1-Befund
  ([AGENTS.md](../../AGENTS.md#tests)).
- Fixture `fake_embedder` (`tests/conftest.py`): `FakeEmbedder` liefert deterministische 16-dimensionale
  Einheitsvektoren aus dem Text-Hash und zeichnet jeden Aufruf auf; ein anderer `salt` simuliert ein geändertes Modell
  hinter demselben Namen. LLM-Schritte bekommen in Tests eine Fake-Funktion statt des Clients.
- Autouse-Fixtures in `tests/conftest.py` (gelten für jeden Test):
  - `test_area_minimums` setzt `catalogue.AREA_MIN_QUESTIONS` auf die Mindestzahlen des kleinen Testkorpus
    (`TEST_AREA_MIN`).
  - `second_rater_isolation` lenkt `scoring_store.SECOND_RATER_DIR` in ein leeres temporäres Verzeichnis und entfernt
    `SCORING_RATER` aus der Umgebung: kein Test sieht `data/evaluation/second_rater/` oder einen R2-Modus der Shell.
  - `closed_book_file` lenkt `catalogue.CLOSED_BOOK_FILE` in eine temporäre Datei: kein Test liest
    `data/evaluation/closed_book_screen.csv`.
- Beim Import setzt `conftest.py` `RAGAS_DO_NOT_TRACK=true`.
- Helfer in `conftest.py` für Testdaten: `build_corpus`, Fixtures `corpus_files`/`corpus` und `pilot`,
  `write_catalogue`, `valid_rows`, `write_plan_for`, `fresh_plan_for`, `write_screen_for`, `write_scoring_set`,
  `write_control_set`, `log_scaffold`.
- Einfrieren in Tests: Tests, die einen eingefrorenen Katalog brauchen, setzen per `monkeypatch`
  `freeze.QUESTIONS_FILE` und `freeze.GROUND_TRUTH_FILE` auf ihre temporären Dateien (z. B. `tests/test_freeze.py`);
  den echten Freeze-Datensatz nie löschen, um eine Prüfung zu umgehen.
- Korpus-Integrationstests (`tests/test_corpus_integration.py`) werden übersprungen, solange (1) kein Snapshot in
  `data/raw/e2e_docs_snapshot/` liegt (`docs.json` fehlt), (2) `data/processed/sections.jsonl` fehlt (nicht
  vorverarbeitet) oder (3) die Vektordatei einer Strategie fehlt (nicht eingebettet). In CI greifen alle drei.
