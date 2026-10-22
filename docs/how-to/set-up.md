# Einrichten

*[Doku-Index](../README.md) · Anleitung · Verwandt: [Werkzeuge](../reference/tooling.md), [Korpus-Snapshot erstellen](create-corpus-snapshot.md), [Experiment durchführen](run-the-experiment.md)*

0. Voraussetzungen: `git` und [uv](https://docs.astral.sh/uv/). Repo klonen und hineinwechseln. Wer mit PaperLab
   arbeitet, klont dort mit `git clone --recurse-submodules`; dieses Repo liegt dann als Submodul `code/` im Ordner der
   Arbeit.
1. Abhängigkeiten installieren (Python ≥ 3.11, aus `pyproject.toml`/`uv.lock`, inkl. Gruppe `dev`):
   `uv sync`
2. API-Schlüssel hinterlegen: `cp .env.example .env`, dann `OPENAI_API_KEY` eintragen. `.env` ist gitignored und
   wird nie committet. Der Schlüssel wird erst geladen, wenn ein Schritt die OpenAI-API aufruft; welche Schritte das
   sind: [Umgebungsvariablen](../reference/tooling.md#umgebungsvariablen). Ohne Schlüssel laufen die Tests und die
   Korpusschritte; `snapshot.py` braucht aber Netz (`git fetch`), und die Tests laden beim ersten Lauf die
   `tiktoken`-Kodierung.
3. Prüfungen vor jedem Commit einschalten (einmal je Klon): `uv tool install pre-commit && pre-commit install`
4. Prüfen, dass alles läuft: `uv run python src/chunking.py --help` und `uv run pytest`. Nicht jedes Skript kennt
   `--help` ([Skripte und Optionen](../reference/tooling.md#skripte-und-optionen)).
5. Nur ohne PaperLab-Checkout und nur für die Abbildungen der Auswertung: `PAPERLAB_FONTS` auf einen Ordner mit Arial
   setzen ([Umgebungsvariablen](../reference/tooling.md#umgebungsvariablen)).
