# ADR 0015: Tech-Stack

- **Status:** angenommen (D15, verbindlich)
- **Quelle:** Baseline; Verhältnis zur Baseline: übernommen
- **Details:** [Ground-Truth-Leitfaden](../Ground_Truth_Projektleitfaden.md), §8

## Kontext

Die Pipeline soll mit verbreiteten, gut dokumentierten Werkzeugen gebaut werden.

## Entscheidung

Python, OpenAI API (LLM und Embeddings), Chroma, tiktoken, Pandas, Matplotlib/Plotly, Streamlit, optional RAGAS; Abhängigkeiten über uv und `pyproject.toml`.

## Folgen

Details im Leitfaden §8; Entwicklungswerkzeuge in `docs/development.md`.
