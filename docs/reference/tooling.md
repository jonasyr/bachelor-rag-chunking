# Werkzeuge und Repository

> Seitentyp: Nachschlagen (reference). Übersicht: [Dokumentation](../README.md).

## Tech-Stack

Entscheidung und Folgen: [ADR 0015](../adr/0015-tech-stack.md), Modellwahl: [ADR 0016](../adr/0016-modell-neutralitaet.md).
Konstante Parameter (Temperatur, top-k): [ADR 0014](../adr/0014-temperatur-und-topk.md) und `src/config.py`.


| Zweck | Werkzeug |
|-------|----------|
| Sprache | Python ≥ 3.11 |
| Paketverwaltung | **uv** + `pyproject.toml` (inkl. `uv.lock` für reproduzierbare Installs) |
| Dokumentverarbeitung | Python-Markdown, `pathlib`, `regex` |
| Token-Zählung | `tiktoken` 0.13.0 (gepinnt), Kodierung `cl100k_base`, gekapselt in `src/tokens.py` ([ADR 0019](../adr/0019-korpus-ausschnitt.md)) |
| Embeddings | OpenAI API, `text-embedding-3-large` (3.072 Dimensionen; SDK 2.44.0; [ADR 0023](../adr/0023-embedding-modell.md)) |
| Vector Store | Chroma 1.5.9 (lokal, persistent; Kosinus, exakte Suche geprüft; [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)) |
| LLM | festes GPT-Modell über OpenAI API |
| Datenanalyse | Pandas |
| Diagramme | Matplotlib / Plotly |
| App/Dashboard | Streamlit |
| Evaluation | eigene Skripte + optional RAGAS |

## Repository-Struktur

```
bachelor-rag-chunking/
├── README.md
├── pyproject.toml
├── uv.lock
├── .env.example
├── data/
│   ├── raw/
│   │   └── vue_docs_snapshot/
│   ├── processed/
│   │   ├── documents.jsonl
│   │   ├── chunks_c1.jsonl
│   │   ├── chunks_c2.jsonl
│   │   └── chunks_c3.jsonl
│   └── evaluation/
│       ├── questions.csv
│       ├── ground_truth.csv
│       ├── retrieved_results.csv
│       ├── generated_answers.csv
│       └── scores.csv
├── src/
│   ├── snapshot.py
│   ├── tokens.py
│   ├── ingest.py
│   ├── preprocess.py
│   ├── chunking.py
│   ├── embedding_client.py
│   ├── vector_index.py
│   ├── relevance.py
│   ├── run_log.py
│   ├── embed.py
│   ├── retrieve.py
│   ├── generate.py
│   ├── evaluate_retrieval.py
│   ├── evaluate_answers.py
│   └── config.py
├── tests/                        (pytest; Integrationstests laufen, sobald der Snapshot existiert)
├── notebooks/
│   └── analysis.ipynb
├── app/
│   └── streamlit_app.py
└── docs/
    ├── README.md                 (Index der Dokumentation)
    ├── explanation/  reference/  how-to/   (Diátaxis)
    ├── plan.md                   (Zeitplan, offene Entscheidungen)
    ├── adr/                      (Entscheidungen D1–D24)
    ├── Exposee.md                (Lesekopie, Original in PaperLab)
    └── corpus_manifest.csv
```

Rohdaten (`data/raw/vue_docs_snapshot/`), Zwischenstände (`data/processed/`) und der Vektorspeicher (`chroma_db/`)
sind gitignored; die Ordner bleiben über `.gitkeep` erhalten. Formate: [Datenartefakte](data-formats.md).

## Skripte und Optionen

Alle Schritte in `src/` laufen aus der Repo-Wurzel (`uv run python src/<schritt>.py`, Optionen mit `--help`).
Umgesetzt: `snapshot.py`, `ingest.py`, `preprocess.py`, `chunking.py`, `embed.py`, `retrieve.py` (Tests in `tests/`, `uv run pytest`); die übrigen Schritte sind Gerüste (`raise NotImplementedError`).

| Skript | Optionen |
|---|---|
| `snapshot.py`, `ingest.py`, `preprocess.py` | keine |
| `chunking.py`, `embed.py` | `--strategy C1\|C2\|C3\|K1\|all` (Standard `all` = C1–C3, dann die Kontrolle K1; [ADR 0026](../adr/0026-c3-vergleichbarkeit.md)) |
| `generate.py` | `--strategy C1\|C2\|C3\|all` (nur das Experiment; K1 wird nicht generiert) |
| `retrieve.py` | ohne Option alle Strategien C1–C3 ([ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)); `--control` nur die Kontrolle K1 |
| `evaluate_retrieval.py` | `--k` (Standard `TOP_K` = 5) |
| `evaluate_answers.py` | `--mode scaffold\|summarise` (Pflicht) |
| `scripts/difficulty_probe.py` | Pilot-Fragenset als Ordner (Standard `data/pilot`, z. B. `data/pilot/hard`); läuft auch die Kontrolle K1 |
| `scripts/remap_pilot.py` | einmalig: `ALT_ORDNER PILOT_ORDNER …` bildet die Pilot-Ground-Truth über Pfad und Anker auf neue IDs ab ([ADR 0025](../adr/0025-korpus-guide-api-styleguide.md)) |

## Qualitätswerkzeuge

| Werkzeug | Was | Wo |
|---|---|---|
| ruff | Lint (E, F, W, I, B, UP; F401 bis zur Implementierung aus) und Formatierung, Zeilenlänge 100 | `pyproject.toml` `[tool.ruff]` |
| pre-commit | ruff, große Dateien (> 5 MB), private Schlüssel, Merge-Konflikte, YAML/TOML, Zeilenenden | `.pre-commit-config.yaml` |
| pytest | Unit-Tests aller umgesetzten Schritte; Korpus-Integrationstests werden ohne Snapshot übersprungen (z. B. in CI) | `tests/`, `pyproject.toml` `[tool.pytest.ini_options]` |
| Pyright (Editor) | Typprüfung mit uv-venv und `src/` als Importpfad | `pyproject.toml` `[tool.pyright]` |
| GitHub Actions | `uv sync`, alle pre-commit-Hooks, `compileall` für `src/` und `app/`, `pytest` | `.github/workflows/ci.yml` |
