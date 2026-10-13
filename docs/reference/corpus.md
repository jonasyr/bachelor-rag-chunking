# Korpus (Vue.js)

> Seitentyp: Nachschlagen (reference). Stand: 13.10.2026, festgelegt in [ADR 0019](../adr/0019-korpus-ausschnitt.md). Übersicht: [Dokumentation](../README.md).

## Quelle und Ausschnitt

| Feld | Wert |
|---|---|
| Repository | `vuejs/docs` (offizielle Vue-3-Dokumentation) |
| Commit | `b75d188ab16bf83bd1f364a77dfd2315be8f3fa4` (31.07.2026) |
| Pfad | ganzes `src/guide/` (alle `*.md`, rekursiv) |
| Dateien | 52 |
| API-Stil | nur Composition API; `<div class="options-api">`-Blöcke werden beim Preprocessing entfernt |
| Playground-Links | kodierter Beispielzustand nach `#` entfernt, Link bleibt ([ADR 0020](../adr/0020-playground-urls-kuerzen.md)) |
| Token-Kodierung | `cl100k_base` (`tiktoken` 0.13.0) |
| Umfang | 117.594 Tokens nach dem Preprocessing, 560 Abschnitte (H1–H3); Protokoll: [Experiment-Protokoll](experiment-record.md) |

Bereiche in `src/guide/` (Dateien): `essentials` (13), `components` (8), `extras` (8), `scaling-up` (6),
`built-ins` (5), `best-practices` (4), `reusability` (3), `typescript` (3), Einstiegsseiten direkt in `guide/` (2).

## Abschnitte und Relevanz

- **`section_id`** = `{doc_id}#{anchor}`, wobei `anchor` der explizite VitePress-Anker `{#…}` einer H2/H3-Überschrift
  ist (z. B. `D027#reactive`). Alle H1–H3-Überschriften im Ausschnitt tragen einen solchen Anker; `sections.jsonl`
  enthält 52 H1-, 279 H2- und 229 H3-Abschnitte.
- **H1-Abschnitte** umfassen jeweils die ganze Seite. In `relevant_section_ids` werden H2/H3-Abschnitte annotiert; ein
  H1-Abschnitt nur, wenn wirklich die ganze Seite die Antwort ist (sonst wäre bei jeder Überlappung jeder Chunk der
  Seite relevant).
- **Relevanz eines Chunks:** relevant, wenn seine Token-Spanne die Token-Spanne eines Abschnitts aus
  `relevant_section_ids` überlappt (jede Überlappung). Sensitivitätsprüfung: Mindestüberlappung 100 Tokens.
- Werte dazu stehen in [`src/config.py`](../../src/config.py).

## Korpusmanifest (`corpus_manifest.csv`)

Eine Zeile je Datei des Ausschnitts; `tokens` nach dem Preprocessing. Zwei echte Zeilen:

| file_id | path | title | section | tokens | included |
|---------|------|-------|---------|-------:|----------|
| D013 | guide/components/props.md | Props | Components | 3754 | yes |
| D027 | guide/essentials/reactivity-fundamentals.md | Reactivity Fundamentals | Essentials | 3063 | yes |
