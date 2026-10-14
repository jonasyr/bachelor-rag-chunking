# Korpus (Vue.js)

> Seitentyp: Nachschlagen (reference). Stand: 14.10.2026, festgelegt in [ADR 0025](../adr/0025-korpus-guide-api-styleguide.md) (Regeln aus [ADR 0019](../adr/0019-korpus-ausschnitt.md)). Übersicht: [Dokumentation](../README.md).

## Quelle und Ausschnitt

| Feld | Wert |
|---|---|
| Repository | `vuejs/docs` (offizielle Vue-3-Dokumentation) |
| Commit | `40aa88af0094f7bab4aaf786e55c748a6a251d88` (15.09.2026) |
| Snapshot | 14.10.2026; Datensatz [`docs/corpus_snapshot.txt`](../corpus_snapshot.txt) (Format: [Datenformate](data-formats.md#korpus)) |
| Pfade | `src/guide/`, `src/api/`, `src/style-guide/` (alle `*.md`, rekursiv) |
| Ausgeschlossen (`config.VUE_DOCS_EXCLUDED`) | `api/index.md` (generiertes Inhaltsverzeichnis), `api/component-instance.md`, `api/options-{composition,lifecycle,misc,rendering,state}.md` (nur Options API) |
| Dateien | 79 (Guide 52, API 22, Style Guide 5) |
| API-Stil | nur Composition API; `<div class="options-api">`-Blöcke werden beim Preprocessing entfernt |
| Playground-Links | kodierter Beispielzustand nach `#` entfernt, Link bleibt ([ADR 0020](../adr/0020-playground-urls-kuerzen.md)) |
| Token-Kodierung | `config.TOKEN_ENCODING` = `cl100k_base` (`tiktoken` 0.13.0); alle Parameter: [Konfiguration](configuration.md#korpus) |
| Umfang | 165.723 Tokens nach dem Preprocessing (Guide 117.694, API 42.488, Style Guide 5.541), 813 Abschnitte (H1–H3); gemessen beim Snapshot vom 14.10.2026, Chunking und Embedding im [Experiment-Protokoll](experiment-record.md) |

Bereiche in `src/guide/` (Dateien): `essentials` (13), `components` (8), `extras` (8), `scaling-up` (6),
`built-ins` (5), `best-practices` (4), `reusability` (3), `typescript` (3), Einstiegsseiten direkt in `guide/` (2).
Im Manifest heißen die beiden anderen Bereiche „API Reference“ und „Style Guide“.

Nicht aufgenommen: Tutorial (interaktive Schritte, wiederholt den Guide), Beispiele (nur Code) und Projektseiten
(about, ecosystem, partners usw.); Begründung in [ADR 0025](../adr/0025-korpus-guide-api-styleguide.md).

## Bereinigung (Auszug)

Neben den Regeln aus [ADR 0019](../adr/0019-korpus-ausschnitt.md) und [ADR 0020](../adr/0020-playground-urls-kuerzen.md)
gelten für die API-Seiten ([ADR 0025](../adr/0025-korpus-guide-api-styleguide.md)):

- Escapte spitze Klammern (`\<script setup>`, `PropType\<T>`) sind Text, kein HTML. Im bereinigten Text bleibt
  das Escape wie in der Quelle stehen; der Abschnittstitel (`title` in `sections.jsonl`, Manifest) zeigt `<`.
  Ein escapter Backslash vor einem echten Tag (`\\<b>`) bricht weiterhin ab.
- `<br>` in einer Zeile wird ein Leerzeichen (`Composition API: Dependency Injection`).
- `<span v-pre>` um Inline-Code wird entpackt, auch wenn der Code selbst Tags enthält.
- ATX-Überschriften dürfen bis zu drei Leerzeichen eingerückt sein (CommonMark; die API rückt sie in
  Listenpunkten ein); im bereinigten Text steht die Überschrift ohne Einrückung.

## Abschnitte und Relevanz

- **`section_id`** = `{doc_id}#{anchor}`, wobei `anchor` der explizite VitePress-Anker `{#…}` einer H1-, H2- oder
  H3-Überschrift ist (z. B. `D049#reactive`). Alle H1–H3-Überschriften im Ausschnitt tragen einen solchen Anker;
  `sections.jsonl` enthält 79 H1-, 467 H2- und 267 H3-Abschnitte.
- **H1-Abschnitte** umfassen jeweils die ganze Seite. Für `relevant_section_ids` gilt
  [ADR 0022](../adr/0022-h1-abschnitte-in-ground-truth.md): H2/H3-Abschnitte annotieren, einen
  H1-Abschnitt nur, wenn wirklich die ganze Seite die Antwort ist.
- **Relevanz eines Chunks** (Hauptregel und Sensitivitätsregel): [Evaluation](evaluation.md#relevanz-eines-chunks).

## Korpusmanifest (`corpus_manifest.csv`)

Eine Zeile je Datei des Ausschnitts; `tokens` nach dem Preprocessing. Drei echte Zeilen:

| file_id | path | title | section | tokens | included |
|---------|------|-------|---------|-------:|----------|
| D015 | api/reactivity-core.md | Reactivity API: Core | API Reference | 4181 | yes |
| D035 | guide/components/props.md | Props | Components | 3754 | yes |
| D049 | guide/essentials/reactivity-fundamentals.md | Reactivity Fundamentals | Essentials | 3063 | yes |
