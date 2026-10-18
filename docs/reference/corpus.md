# Korpus (e2e)

> Seitentyp: Nachschlagen (reference). Stand: 18.10.2026, festgelegt in [ADR 0038](../adr/0038-korpus-e2e.md) (Regeln aus [ADR 0019](../adr/0019-korpus-ausschnitt.md)). Übersicht: [Dokumentation](../README.md).

Bis 18.10.2026 war der Korpus die Vue.js-Dokumentation ([ADR 0025](../adr/0025-korpus-guide-api-styleguide.md),
abgelöst durch [ADR 0038](../adr/0038-korpus-e2e.md)); ihre Zahlen stehen weiter im
[Experiment-Protokoll](experiment-record.md), ihre Bereinigungsregeln in der Git-Historie von `src/preprocess.py`.
Warum e2e: [Korpusauswahl](corpus-selection.md).

## Quelle und Ausschnitt

| Feld | Wert |
|---|---|
| Repository | `tester-army/e2e` (https://github.com/tester-army/e2e), Ordner `docs/` (Mintlify, MDX) |
| Commit | `ef977f4856da009cac26d78d2e9bb14e5991ee41` (17.10.2026) |
| Lizenz | Apache License 2.0, © TesterArmy, Inc. ([Lizenzhinweise im README](../../README.md#license)) |
| Snapshot | 18.10.2026; Datensatz [`docs/corpus_snapshot.txt`](../corpus_snapshot.txt) (Format: [Datenformate](data-formats.md#korpus)) |
| Seiten | alle 60 `*.mdx` unter `docs/`; die Menge muss genau den Seiten der Navigation (`docs.json`) entsprechen, sonst brechen Snapshot und Ingest ab |
| Mitkopiert | `docs.json` (Navigation, liefert die Bereiche) und `snippets/model-provider.jsx` (Daten der Anbieterliste) |
| Nicht im Korpus | Bilder, Videos, `examples/` (Beispielprojekte, nur Code), Styles und Skripte der Website |
| Token-Kodierung | `config.TOKEN_ENCODING` = `cl100k_base` (`tiktoken` 0.13.0); alle Parameter: [Konfiguration](configuration.md#korpus) |
| Umfang | 250.380 Tokens nach dem Preprocessing, 571 Abschnitte (60 H1, 347 H2, 164 H3); kleinste Seite 378, größte 21.507 Tokens (`reference/engine.mdx`); gemessen 18.10.2026 |

## Bereiche

Ein Bereich ist eine Gruppe der Navigation; Seiten, die direkt unter einem Tab stehen (Examples), bilden einen
Bereich mit dem Namen des Tabs (`config.CORPUS_AREAS`, Feld `area` in `documents.jsonl`, Spalte `section` im Manifest).

| Tab | Bereich | Seiten | Tokens | Slots |
|---|---|---:|---:|---:|
| Documentation | Get started | 5 | 12.558 | 2 |
| | Platforms | 3 | 10.908 | 2 |
| | Features | 6 | 11.473 | 2 |
| | Models and agents | 3 | 11.962 | 2 |
| | Run in CI | 6 | 10.114 | 2 |
| | Hosted browsers and devices | 7 | 10.940 | 2 |
| | Extend | 3 | 6.703 | 1 |
| | Deep dive | 5 | 15.059 | 3 |
| | Migrate | 5 | 19.210 | 4 |
| Reference | Test API | 5 | 37.134 | 7 |
| | Project | 8 | 61.029 | 12 |
| | Web | 1 | 11.033 | 2 |
| | Mobile | 1 | 10.203 | 2 |
| | Engine contract | 1 | 21.507 | 4 |
| Examples | Examples | 1 | 547 | 1 |

Slots, Reserve und Mindestzahl je Bereich sind gleich (nach Tokenanteil, mindestens 1;
[ADR 0039](../adr/0039-stichprobenplan-e2e.md)).

## Aufbereitung (MDX → Markdown)

`src/mdx.py` wandelt jede Seite in Markdown um, `src/preprocess.py` zeichnet danach die Abschnitte auf. Ziel: jeder
Text, den eine Leserin oder ein Leser der Website sieht, bleibt erhalten ([ADR 0038](../adr/0038-korpus-e2e.md)).
Code in Fences bleibt unverändert bis auf Info-String, Einrückung und Leerzeichen am Zeilenende.

| Eingabe | Ausgabe |
|---|---|
| Frontmatter | `# {title}`, Leerzeile, `description` als erster Absatz; `sidebarTitle`, `icon` und Bild-Metadaten entfallen |
| `import …` | entfällt |
| `export const NAME = \`…\`` (Agent-Prompt) | Text des Prompts, angezeigt an der Stelle des `<Prompt>` |
| `<SetupPrompt>` mit `<Prompt …/>` | Zeile `**Agent prompt**`, dann der Prompt als ```` ```text ````-Block |
| `<Note>`, `<Warning>`, `<Tip>` | Zeile `**Note**` usw., dann der Inhalt |
| `<Accordion title>`, `<Tab title>` | Zeile `**Titel**`, dann der Inhalt |
| `<Steps>`/`<Step title>` | Zeile `**N. Titel**` (N zählt ab 1 je Block), dann der Inhalt |
| `<AccordionGroup>`, `<Tabs>`, `<CodeGroup>`, `<CardGroup>`, `<ShowMore>`, `<Video>` | Hülle entfällt, Inhalt bleibt (bei `CodeGroup` alle Varianten) |
| `<Card title href>Text</Card>` | Listenpunkt `- [Titel](href): Text` |
| `<VideoCard title subtitle …/>` | Listenpunkt `- **Titel**: Untertitel` |
| `<video …/>` (Bildunterschrift bleibt), `<a id/>`, `<span id/>` | entfällt |
| `<ModelProvider show="select"/>` | Tabelle aller 51 Anbieter (Anbieter mit Link, Gruppe, Pakete, Variablen, Import, Modell, Hinweis) |
| `<ModelProvider show="install\|env\|config\|model"/>` | was die Seite ohne Auswahl zeigt (erster Anbieter, npm): Zeile `**Install · Vercel AI Gateway**` usw. und der Codeblock |
| Fence-Info `ts title="a.ts" expandable`, `bash npm` | Zeile `**a.ts**` bzw. `**npm**` vor dem Block, der Block behält nur die Sprache; eingerückte Fences werden ausgerückt |
| unbekannte Komponente, JSX-Ausdruck, HTML-Tag außerhalb von Code | Abbruch mit Seite und Zeile |

Eine Seite der Navigation, die keine dieser Regeln braucht, bleibt bis auf den Kopf unverändert. Die Aufbereitung
ist rein regelbasiert und deterministisch; Tests je Regel in `tests/test_mdx.py`.

## Abschnitte und Relevanz

- **`section_id`** = `{doc_id}#{anchor}`. H2/H3-Anker sind die Anker der Website: Linkziele und Backticks weg,
  Kleinschreibung, jede Folge anderer Zeichen als `a-z0-9` wird `-`, `-` an den Rändern entfällt
  (`` `.env` files `` → `env-files`, `agent.act` → `agent-act`). Geprüft am 18.10.2026 an allen 503 abrufbaren
  H2/H3 der Live-Seite; nur `/docs/mcp` liefert dort Mintlifys MCP-Endpunkt statt der Seite.
- **H1-Anker** = Slug des Seitenpfads ohne Endung (`reference/config` → `reference-config`): Die Website hat keinen
  H1-Anker, und der Titel `E2EConfig` kollidiert mit einer H3 derselben Seite.
- **H1-Abschnitte** umfassen jeweils die ganze Seite. Für `relevant_section_ids` gilt
  [ADR 0022](../adr/0022-h1-abschnitte-in-ground-truth.md): H2/H3-Abschnitte annotieren, einen
  H1-Abschnitt nur, wenn wirklich die ganze Seite die Antwort ist.
- **Relevanz eines Chunks** (Hauptregel und Sensitivitätsregel): [Evaluation](evaluation.md#relevanz-eines-chunks).

## Korpusmanifest (`corpus_manifest.csv`)

Eine Zeile je Seite; `section` = Bereich, `tokens` nach dem Preprocessing. Drei echte Zeilen:

| file_id | path | title | section | tokens | included |
|---------|------|-------|---------|-------:|----------|
| D036 | models.mdx | Models | Models and agents | 7383 | yes |
| D037 | quickstart.mdx | Quickstart | Get started | 6914 | yes |
| D045 | reference/expect.mdx | expect | Test API | 10332 | yes |
