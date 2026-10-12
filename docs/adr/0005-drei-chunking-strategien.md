# ADR 0005: Drei Chunking-Strategien C1–C3, C4 optional

- **Status:** angenommen (D5, verbindlich)
- **Quelle:** Exposé/Baseline; Verhältnis zur Baseline: übernommen
- **Details:** [Ground-Truth-Leitfaden](../Ground_Truth_Projektleitfaden.md), §6

## Kontext

Verglichen werden soll, wie die Zerlegung der Dokumente die Ergebnisse beeinflusst.

## Entscheidung

C1: fixed-size 500 Tokens ohne Overlap. C2: fixed-size 500 Tokens, Overlap 100. C3: strukturbasiert an Markdown-Überschriften H2/H3, höchstens 800 Tokens, große Abschnitte nach Absätzen unterteilt. C4 (semantisch) nur, wenn die Phasen 1–4 planmäßig laufen.

## Folgen

Parameter stehen ausschließlich in `src/config.py`. Lange Vue-Abschnitte (z. B. „Reactivity Fundamentals“) machen die Unterteilungsregel von C3 wichtig; sie ist im Methodikkapitel zu dokumentieren.
