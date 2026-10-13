# 0015. Tech-Stack

## Status

Angenommen (D15 im Leitfaden; Quelle: Baseline, übernommen)

## Kontext

- Der Leitfaden nennt für die Werkzeugwahl keinen Grund; sie ist aus der Baseline übernommen ([Leitfaden §8](../reference/tooling.md#tech-stack)).
- Die Pipeline braucht je Strategie einen eigenen Vektorindex sowie Embeddings, Token-Zählung, Auswertung und Diagramme (Leitfaden §7).

## Entscheidung

Wir werden Python (≥ 3.11), die OpenAI API (LLM und Embeddings), Chroma (lokal, persistent), tiktoken, Pandas, Matplotlib/Plotly, Streamlit und optional RAGAS einsetzen.
Wir werden Abhängigkeiten mit uv über `pyproject.toml` und `uv.lock` verwalten.

## Konsequenzen

- Gut: `uv.lock` macht Installationen reproduzierbar (Leitfaden §8).
- Neutral: LLM und Embeddings laufen über die OpenAI API; Modell- und Versionswahl regelt [ADR 0016](0016-modell-neutralitaet.md).
- Neutral: Entwicklungswerkzeuge stehen in [`docs/reference/tooling.md`](../reference/tooling.md).
