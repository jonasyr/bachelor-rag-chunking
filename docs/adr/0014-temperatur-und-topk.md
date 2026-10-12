# ADR 0014: Temperatur 0 und top-k 5 konstant

- **Status:** angenommen (D14, verbindlich)
- **Quelle:** Baseline; Verhältnis zur Baseline: übernommen
- **Details:** [Ground-Truth-Leitfaden](../Ground_Truth_Projektleitfaden.md), §8

## Kontext

Reproduzierbarkeit und interne Validität.

## Entscheidung

`LLM_TEMPERATURE = 0.0`, `TOP_K = 5` in `src/config.py`, für alle Strategien gleich.

## Folgen

top-k wird nicht variiert, sonst entstünde eine zweite unabhängige Variable.
