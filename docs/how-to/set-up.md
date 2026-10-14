# Einrichten

> Seitentyp: Anleitung (how-to). Übersicht: [Dokumentation](../README.md).

1. Abhängigkeiten installieren (Python ≥ 3.11, aus `pyproject.toml`/`uv.lock`, inkl. Gruppe `dev`):
   `uv sync`
2. API-Schlüssel hinterlegen: `cp .env.example .env`, dann `OPENAI_API_KEY` eintragen. `.env` ist gitignored und
   wird nie committet. Der Schlüssel wird erst geladen, wenn ein Schritt die OpenAI-API aufruft (Embedding, Retrieval
   mit neuen Frage-Embeddings, Generierung). Die Offline-Schritte (`snapshot.py`, `ingest.py`, `preprocess.py`,
   `chunking.py`) und die Tests brauchen keinen Schlüssel.
3. Prüfungen vor jedem Commit einschalten (einmal je Klon): `uv tool install pre-commit && pre-commit install`
4. Prüfen, dass alles läuft: `uv run python src/chunking.py --help` und `uv run pytest`

Optionen der Skripte und Werkzeuge: [Werkzeuge und Repository](../reference/tooling.md). Pläne für größere
Arbeitsschritte unter `docs/superpowers/plans/` ablegen und committen.
