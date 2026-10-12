# ADR 0016: Modell-Neutralität

- **Status:** angenommen (D16, verbindlich)
- **Quelle:** Baseline; Verhältnis zur Baseline: übernommen
- **Details:** [Ground-Truth-Leitfaden](../Ground_Truth_Projektleitfaden.md), §8, §19

## Kontext

Im Exposé und in der Arbeit wird neutral formuliert; konkrete Versionsnummern werden erst bei der tatsächlichen Implementierung festgeschrieben (Leitfaden §8).

## Entscheidung

Es wird ein festes GPT-Modell über die OpenAI API verwendet. Modell, SDK- und API-Version werden zum Implementierungszeitpunkt fixiert, mit Datum dokumentiert und während der Evaluation konstant gehalten.

## Folgen

`LLM_MODEL` in `src/config.py` ist bis dahin ein Platzhalter; Versionen werden in `docs/methodology.md` eingetragen.
