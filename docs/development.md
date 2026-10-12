# Entwicklung

## Einrichtung

```bash
uv sync                      # Python >= 3.11, Abhängigkeiten aus pyproject.toml/uv.lock, inkl. Gruppe dev
cp .env.example .env         # OPENAI_API_KEY eintragen; .env ist gitignored und wird nie committet
uv tool install pre-commit && pre-commit install   # einmal je Klon
```

Skripte laufen aus der Repo-Wurzel, z. B. `uv run python src/chunking.py --strategy C1`
(Optionen je Skript mit `--help`). Alle Parameter stehen in `src/config.py` und nur dort.

## Pipeline

Reihenfolge und Befehle: [README](../README.md#pipeline-run-in-order). Stand 13.10.2026: alle Schritte in `src/`
sind Gerüste (`raise NotImplementedError`). `ingest.py` und `preprocess.py` haben keine Optionen; `chunking.py`,
`embed.py`, `retrieve.py`, `generate.py` nehmen `--strategy C1|C2|C3|all`, `evaluate_retrieval.py` nimmt `--k`,
`evaluate_answers.py` verlangt `--mode scaffold|summarise`.

Datenablage: Rohdaten `data/raw/vue_docs_snapshot/` und Zwischenstände `data/processed/` sind gitignored (die
Ordner bleiben über `.gitkeep` erhalten), Bewertungsdateien liegen in `data/evaluation/`, der Vektorspeicher in
`chroma_db/` (gitignored). Formate: Leitfaden §10.

## Qualität

| Werkzeug | Was | Wo |
|---|---|---|
| ruff | Lint (E, F, W, I, B, UP; F401 bis zur Implementierung aus) und Formatierung, Zeilenlänge 100 | `pyproject.toml` `[tool.ruff]` |
| pre-commit | ruff, große Dateien (> 5 MB), private Schlüssel, Merge-Konflikte, YAML/TOML, Zeilenenden | `.pre-commit-config.yaml` |
| GitHub Actions | `uv sync`, alle pre-commit-Hooks, `compileall` für `src/` und `app/`, `pytest`, sobald `tests/` existiert | `.github/workflows/ci.yml` |

## Anbindung an die Bachelorarbeit (PaperLab)

Das private Repo PaperLab bindet dieses Repo als Git-Submodul ein:
`scientific-papers/thesis/thesis-semester-7-rag-chunking_jonas/code/`. Die Arbeit zitiert den dort festgehaltenen
Commit. Ablauf für Änderungen: hier committen und pushen, danach in PaperLab den Submodul-Zeiger committen.

Vereinbarung für Ergebnisse, die in der Arbeit erscheinen: LaTeX-Tabellen nach `output/tables/*.tex`, Abbildungen
nach `output/figures/*.pdf`. Die Arbeit bindet sie direkt ein (`\input{code/output/tables/…}`), ohne Kopie;
PaperLab meldet ein veraltetes PDF, wenn dort etwas neuer ist. Der Ordner `output/` und ein Pfad in
`src/config.py` entstehen mit der ersten Auswertung.

## Pläne

Implementierungspläne liegen unter `docs/superpowers/plans/` und werden versioniert (seit 13.10.2026 nicht mehr
gitignored).
