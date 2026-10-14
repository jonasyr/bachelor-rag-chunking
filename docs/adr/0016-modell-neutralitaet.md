# 0016. Modell-Neutralität

## Status

Angenommen (D16 im Leitfaden; Quelle: Baseline, übernommen); Embedding-Modell sowie SDK- und Chroma-Version entschieden in [ADR 0023](0023-embedding-modell.md)

## Kontext

- Im Exposé und in der Arbeit wird neutral formuliert; konkrete Versionsnummern (Modell, SDK, API) werden erst bei der tatsächlichen Implementierung festgeschrieben ([Leitfaden §8](../reference/tooling.md)).
- Zur Reliabilität gehört, die Modellversion zu dokumentieren (Leitfaden §13).
- Modell, Embedding-Modell (`-large` oder `-small`) und SDK-/API-Version sind noch offen ([Leitfaden §19](../plan.md)).

## Entscheidung

Wir werden ein festes GPT-Modell über die OpenAI API verwenden.
Wir werden Modell, SDK- und API-Version zum Implementierungszeitpunkt fixieren, mit Datum dokumentieren und während der Evaluation konstant halten.

## Konsequenzen

- Neutral: `LLM_MODEL` in [`src/config.py`](../../src/config.py) ist bis dahin ein Platzhalter.
- Neutral: Die fixierten Versionen werden in [`docs/reference/experiment-record.md`](../reference/experiment-record.md) und im Methodik-/Implementierungskapitel eingetragen.
