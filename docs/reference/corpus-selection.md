# Korpusauswahl (Lückentext-Probe und Closed-Book-Fragen)

*[Doku-Index](../README.md) · Referenz · Verwandt: [ADR 0038](../adr/0038-korpus-e2e.md), [Korpus](corpus.md), [Vorregistrierung](../../data/corpus_probe/preregistration.md)*

Stand: 22.10.2026 (Messung 17.–19.10.2026). Entscheidung: [ADR 0038](../adr/0038-korpus-e2e.md).

Einmalige Diagnose, mit der der Korpus gewählt wurde; kein Teil des Experiments. Frage: Welche Dokumentation kennt
das Antwortmodell (`config.LLM_MODEL` = `gpt-6-luna`, Wissensstand 18.05.2026) noch nicht?

## Vorgehen

1. **Kandidaten.** Zwei unabhängige Recherchen (Bibliotheken und Frameworks; CLIs, Infrastruktur und Protokolle) über
   rund 2.500 GitHub-Repositories, die ab dem 01.06.2026 angelegt wurden; dazu Vue.js (bisheriger Korpus) und Angular
   (vom Betreuer vorgeschlagen) als bekannte Vergleiche. Ausschlusskriterien, Messung und Gewichte standen fest, bevor
   die neuen Kandidaten gemessen wurden: [`data/corpus_probe/preregistration.md`](../../data/corpus_probe/preregistration.md).
   Vue, Blume und e2e waren schon vorher gemessen und werden nach denselben Regeln gewertet.
2. **Seiten** (`to_docs.py`): alle `.md`/`.mdx`-Dateien des Docs-Ordners auf dem gepinnten Commit, ohne Übersetzungen,
   Changelogs und die in `candidates.csv` genannten Ausschlüsse; Titel aus dem Frontmatter, MDX-`import`/`export`
   entfernt. Vue: `data/processed/documents.jsonl` des Snapshots `40aa88a` nach dem Preprocessing (heute liegt dort
   e2e, siehe [Dateien und Befehle](#dateien-und-befehle)).
3. **Proben** (`build_probes.py`): je Prosasatz (40–400 Zeichen, außerhalb von Code, Tabellen, HTML und Hinweisboxen)
   wird jeder Inline-Code-Ausdruck (2–40 Zeichen) einzeln maskiert, je Ausdruck eine Probe; doppelte Ausdrücke,
   triviale Literale (`true`, `false`, `null`, `undefined`) und Ausdrücke, die im Satz sichtbar bleiben, entfallen.
   Codeblöcke erkennt nur der Zaun ```` ``` ```` (nicht `~~~`). Höchstens 12 Proben je Seite, Seed 20261018
   (`config.CORPUS_PROBE_*`). Proben, deren Ausdruck nach Normalisierung (Schritt 4) als Teilzeichenkette im
   normalisierten Seiten- oder Abschnittstitel vorkommt, entfallen (`run_probes.py`).
4. **Läufe** (`run_probes.py`): Das Antwortmodell mit den Einstellungen des Experiments (`llm_client`) ergänzt jeden
   Ausdruck einmal nur aus Satz, Seiten- und Abschnittstitel (closed-book) und einmal zusätzlich mit dem maskierten
   Abschnittstext (open-book, höchstens 6.000 Zeichen). Treffer = gleicher Ausdruck nach Normalisierung (erste Zeile,
   ohne Backticks, Anführungszeichen, Leerraum, Schlusspunkt und `()`, Kleinschreibung).
5. **Klassifikation.** Eindeutig gestellt ist eine Probe, die open-book stimmt. Jeden closed-book-Fehltreffer unter
   ihnen ordnete ein unabhängiger Agent mit demselben Prompt für alle Korpora ein (unten). Wissenslücke = `fact` /
   eindeutig gestellte Proben, mit 95-%-Konfidenzintervall (Normalapproximation).
6. **Wertung** (`summarise.py`): sechs Kriterien je 0–4 aus Messwerten, gewichtet 35/15/15/15/10/10 (Unbekanntheit,
   Markdown-Sauberkeit, Struktur, Dokumentationsqualität, Stabilität, Passung; `config.CORPUS_PROBE_WEIGHTS`),
   Stufen in `summarise.py`; dazu fünf Gewichtungen als Sensitivität (`config.CORPUS_PROBE_SENSITIVITY`).
7. **Qualitative Durchsicht.** Ein unabhängiger Agent las je mindestens sechs Seiten der sechs besten Kandidaten und
   bewertete Qualität, Passung, Eignung für den Chunking-Vergleich, Fragenpotenzial und Aufbereitungsaufwand (je 0–4);
   ein zweiter Agent später ebenso e2e und TanStack Charts (mindestens acht Seiten).
8. **Closed-Book-Fragen** (`question_probe.py`) für Vue, Angular, Enroute, e2e, TanStack Charts und xy: je 20
   Abschnitte (H2/H3, mindestens 60 Prosawörter, höchstens 2 je Seite, ohne Beispiele, Changelogs und Blog; Seed
   `config.CORPUS_PROBE_SEED` = 20261018, übrige Werte `config.CORPUS_QUESTIONS_*`). Ein Agent schrieb je Abschnitt
   eine realistische Frage mit Referenzantwort (je Korpus 4 × faktisch, prozedural, konzeptuell, Grenze, Vergleich;
   Prompt unten). Das Antwortmodell beantwortete jede Frage ohne Kontext und mit dem Abschnitt; ein weiterer Agent
   beurteilte alle Antworten blind (gemischt, ohne Angabe der Bedingung): `correct`, `partial`, `wrong`, `abstain`.
   Retrieval-abhängig = Anteil der mit Abschnitt `correct` beantworteten Fragen, die ohne Abschnitt nicht `correct`
   sind (Nenner: nur die mit Abschnitt richtigen; Wilson-Intervall, `question_probe.summary`). Die Fragen sind Diagnose,
   kein Teil des Fragenkatalogs. Urteilslauf 1: die fünf Korpora gemeinsam, Lauf 2: Angular allein (auf Wunsch für die
   Mail an den Betreuer nachgereicht); Seeds in `config.CORPUS_QUESTIONS_JUDGE_SEEDS`, beide Reihenfolgen aus den
   abgelegten Antworten reproduzierbar.

Prompt der Lückentext-Läufe (`run_probes.py`, wörtlich; Nutzernachricht = `HEAD` + `CONTEXT` (nur open-book) +
`TAIL`, `{context}` = Fenster des maskierten Abschnittstexts):

```python
SYSTEM = "You are an expert on {product}."
HEAD = (
    'The following sentence is from the official {product} documentation, page "{page}", '
    'section "{section}". One code term was replaced by [MASK].\n\nSentence: {sentence}\n\n'
)
CONTEXT = "Section text (the term is masked there too):\n{context}\n\n"
TAIL = "Reply with the masked code term only, without backticks or explanation."
```

Prompt der Klassifikation (je Korpus; Eingabe `misses/<name>.json` mit leerem `category`):

```text
Classify each probe into exactly one category, judging ONLY from the sentence, answer and guess (do not rely on your
own knowledge of the project):
- `fact`: the true term is a specific thing the documentation teaches (an API/function/option/config key/CLI
  flag/command/directive/hook/default value/package name of the project), the sentence pins it down, and the guess is
  a different thing (wrong).
- `example_name`: the true term is a local/sample name from example code (variable, component, file name in an
  example) that the docs do not teach as part of the project's API.
- `equivalent`: the guess means the same as the answer but differs in form (case, prefix, quotes, `()`, plural, path
  form).
- `ambiguous`: several terms would make the sentence true, or the guess is a valid reading.
```

Prompt des Fragenschreibers (Kern; je Korpus gleich, Eingabe `questions/<name>-sections.json`):

```text
For EVERY section write exactly one question and a reference answer:
- The question is what a real developer using that project might ask. It is answerable from that section alone, and
  it tests what this documentation specifically says (product-specific behaviour, API, option, default, procedure,
  concept, limitation), not general programming knowledge.
- Never ask about names that only occur in example code, and never ask about the documentation itself.
- The question must not give away its answer. Name the product naturally in the question.
- Vary the type: use each of factual, procedural, conceptual, limitation, comparative 4 times, assigning by section
  fit.
- The reference answer is 1-2 sentences: the core point, taken only from the section text, specific enough that a
  judge can tell a correct answer from a plausible but wrong one.
```

Prompt des Urteils (Eingabe `judge-input.json`: Frage, Referenz, Antwort):

```text
Judge each answer ONLY against the reference; do not use your own knowledge of the projects:
- `correct`: the answer states the reference's core point (wording may differ; extra detail is fine as long as it
  does not contradict the reference).
- `partial`: some of the core point is there, but an essential part is missing or vague.
- `wrong`: it contradicts the reference or states a different mechanism, value or procedure.
- `abstain`: it says it does not know, or gives only generic advice without committing to the specific point.
Be strict and consistent. A plausible but generic answer that does not hit the specific documented point is `abstain`
if it hedges, or `wrong` if it asserts something else.
```

Antwort-Prompt (`question_probe.py`): System „You are an expert on {product}.“, Nutzer „Question about {product}:
{question}“, open-book zusätzlich die Kopfzeile `Documentation section "{section}" (page "{page}"):` und der
Abschnittstext (gekürzt auf `config.CORPUS_QUESTIONS_SECTION_CHARS` = 5.000 Zeichen), dann „Answer in 1-3 sentences.
If you do not know, say so instead of guessing.“

## Ergebnis

24 Korpora, 14.547 Proben, davon 5.419 eindeutig gestellt und 2.088 closed-book verfehlt; Kosten rund 1 USD (Lückentext)
und rund 0,01 USD (Closed-Book-Fragen). Vollständige Werte: [`data/corpus_probe/summary.json`](../../data/corpus_probe/summary.json).

### Alle Kandidaten

Rangfolge nach der vorab festgelegten Wertung (0–100). Stufen U/S/St/Q/Sb/P (je 0–4) = Unbekanntheit, Markdown-Sauberkeit,
Struktur, Dokumentationsqualität, Stabilität, Passung. Tokens = Zeichen / 4 nach `to_docs.py` (so auch in ADR 0038); die
Pipeline zählt dagegen tiktoken-Tokens nach dem Preprocessing (Vue 177.951 hier gegen 165.723 im
[Experiment-Protokoll: Vue.js](experiment-record-vue.md#snapshot-vuejs-bis-18102026), e2e 228.266 gegen 250.380 in
[Korpus](corpus.md#quelle-und-ausschnitt)). Seiten = alle `.md`/`.mdx` nach `to_docs.py` (e2e 61: die 60 Seiten der
Navigation und `docs/images/examples/README.md`). Sterne = GitHub-Sterne aus `candidates.csv` (Messzeitpunkt; die
[Spitzengruppe](#spitzengruppe-im-vergleich) zeigt den Stand von `gh api` am 18.10.2026), Commits = Docs-Commits in den
30 Tagen vor der Messung (Stand 17./18.10.2026). Lizenzen: [Lizenzen](#lizenzen). CB = Closed-Book-Fragen ohne
Dokumentation richtig (nur für sechs Korpora gemessen). Vue und Angular sind bekannte Vergleiche, keine Kandidaten
(Ausschlusskriterium 1). Sightmap (#16) ist durch Kriterium 5 ausgeschlossen (79.174 < 80.000 Tokens) und wurde
irrtümlich mitgewertet: `summarise.py` wendet die Token-Grenze nur auf den Pool der Sensitivität an. Ohne Sightmap
rücken die Plätze 17–24 um einen auf; die Sensitivität (ohnehin ohne Sightmap) und die Wahl ändern sich nicht.

| # | Projekt (Beschreibung im Prompt) | Quelle | Wertung | Wissenslücke % (95-%-Konfidenzintervall) | U/S/St/Q/Sb/P | Seiten | Tokens | Sterne | Commits | CB |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Enroute (git on object storage) | `enroute-sh/enroute` | 81,2 | 50,4 (42,1–58,6) | 4/2/3/2/4/4 | 53 | 81.395 | 253 | 2 | 0/20 |
| 2 | xy (a Python charting library by Reflex) | `reflex-dev/xy` | 73,8 | 31,7 (25,8–37,5) | 3/2/3/3/4/3 | 81 | 159.453 | 1.878 | 5 | 3/20 |
| 3 | django-ox (a Django background task library) | `oxpull/django-ox` | 71,2 | 41,5 (30,8–52,1) | 4/3/3/1/2/2 | 21 | 135.132 | 89 | 53 | – |
| 4 | Social SDK (a TypeScript SDK for social platforms) | `opencoredev/social-sdk` | 71,2 | 40,7 (34,6–46,9) | 4/2/2/3/2/2 | 63 | 173.668 | 677 | 49 | – |
| 5 | Strands Box (a sandbox for AI agents) | `strands-agents/box` | 70,0 | 38,6 (29,1–48,1) | 3/2/4/1/4/3 | 40 | 164.627 | 431 | 5 | – |
| 6 | e2e (an end-to-end testing framework) | `tester-army/e2e` | 67,5 | 36,5 (29,8–43,1) | 3/1/4/4/0/3 | 61 | 228.266 | 11.079 | 376 | 1/20 |
| 7 | TanStack Charts (a charting library) | `TanStack/charts` | 66,2 | 29,7 (24,8–34,6) | 2/3/3/3/3/3 | 90 | 219.823 | 842 | 28 | 1/20 |
| 8 | Vela (a charting engine by LuxAlgo) | `LuxAlgo/Vela` | 65,0 | 31,7 (22,8–40,7) | 3/2/3/2/2/3 | 35 | 106.951 | 1.184 | 44 | – |
| 9 | Vue.js | Vue-Snapshot `40aa88a` | 65,0 | 7,0 (4,8–9,2) | 0/4/4/4/4/4 | 79 | 177.951 | – | 0 | 15/20 |
| 10 | better-drizzle (a Drizzle ORM extension library) | `almeidazs/better-drizzle` | 62,5 | 31,4 (26,5–36,3) | 3/1/3/3/1/3 | 80 | 141.910 | 373 | 85 | – |
| 11 | Angular Native (Angular for native mobile apps) | `ng-native/ng-native` | 61,2 | 31,2 (27,4–35,0) | 3/3/2/3/0/2 | 141 | 227.912 | 553 | 320 | – |
| 12 | microcharts (a small charts library for React) | `ganapativs/microcharts` | 60,0 | 32,9 (25,9–40,0) | 3/0/4/1/4/2 | 131 | 159.130 | 201 | 0 | – |
| 13 | Lattice (a PHP admin UI framework) | `lattice-php/lattice` | 58,8 | 28,5 (24,1–32,9) | 2/2/2/3/4/2 | 106 | 145.227 | 63 | 0 | – |
| 14 | Nimbus (a documentation framework by Cloudflare) | `cloudflare/nimbus` | 56,2 | 39,1 (30,0–48,2) | 3/0/2/4/0/3 | 70 | 86.794 | 1.428 | 188 | – |
| 15 | gori (a terminal HTTP intercepting proxy) | `hahwul/gori` | 56,2 | 37,1 (28,6–45,6) | 3/2/2/2/0/3 | 46 | 247.971 | 123 | 271 | – |
| 16 | Sightmap (a site map format and CLI), **ausgeschlossen (Kriterium 5)** | `sightmap/sightmap` | 56,2 | 32,1 (22,2–42,1) | 3/0/3/3/3/0 | 38 | 79.174 | 60 | 19 | – |
| 17 | Blume (a documentation site framework) | `haydenbleasel/blume` | 55,0 | 26,6 (21,6–31,5) | 2/2/2/4/0/3 | 65 | 158.850 | 1.790 | 288 | – |
| 18 | Angular | `angular/angular` | 55,0 | 12,8 (9,7–15,9) | 1/4/2/3/1/4 | 256 | 508.000 | 101.075 | 96 | 10/20 |
| 19 | pgContext (a Postgres retrieval extension) | `Evokoa/pgContext` | 53,8 | 35,5 (28,3–42,7) | 3/2/1/1/4/1 | 66 | 179.407 | 265 | 0 | – |
| 20 | Shipyard (a coding-agent orchestration tool) | `cosscom/shipyard` | 53,8 | 26,3 (18,8–33,8) | 2/2/4/3/0/1 | 46 | 151.311 | 316 | 362 | – |
| 21 | nub (a JavaScript runtime and package script CLI) | `nubjs/nub` | 53,8 | 20,2 (15,4–25,1) | 2/2/2/3/3/1 | 47 | 114.918 | 4.396 | 15 | – |
| 22 | Decionis agent-safe-pipeline (a gateway for AI agents) | `decionis/agent-safe-pipeline` | 51,2 | 28,7 (20,9–36,5) | 2/2/3/2/2/1 | 64 | 154.947 | 688 | 58 | – |
| 23 | Zuke (a typed build automation tool for Deno) | `zuke-build/zuke` | 50,0 | 32,0 (23,8–40,2) | 3/2/2/1/2/0 | 42 | 175.086 | 46 | 53 | – |
| 24 | NVX (a virtual machine monitor) | `microsoft/nvx` | 43,8 | 29,0 (17,7–40,3) | 2/2/2/1/0/3 | 45 | 138.779 | 407 | 475 | – |

Die 22 neuen Projekte liegen bei 20,2–50,4 % (nub bis Enroute); kein Intervall überschneidet sich mit dem von Vue,
mit dem von Angular nur das von nub (20,2 %, Konfidenzintervall 15,4–25,1) knapp. Die Wertung allein hätte Enroute
gewählt: vorn in 4 von 5 Gewichtungen (sonst Dritter). Rangfolgen der Sensitivität (beste fünf, nur neue Projekte
ab 80.000 Tokens):

| Gewichtung | Rangfolge |
|---|---|
| preregistered | enroute > xy > djangoox > socialsdk > strandsbox |
| equal | enroute > xy > strandsbox > tscharts > djangoox |
| unknown50 | enroute > djangoox > socialsdk > xy > strandsbox |
| no_stability_fit | e2e > socialsdk > enroute > djangoox > xy |
| quality_heavy | enroute > e2e > xy > socialsdk > tscharts |

### Qualitative Durchsicht

Je 0–4 für Qualität / Passung / Chunking-Eignung / Fragenpotenzial / Aufbereitung (4 = reines Markdown). Erste
Durchsicht: die sechs besten der Wertung; zweite: e2e und TanStack Charts, nachdem die Nutzung der Spitzengruppe in
Frage stand.

| Korpus | Bewertung | Befund |
|---|---|---|
| Enroute | 4/4/4/3/4 | saubere Trennung Tutorial / How-to / Konzepte / Referenz / Interna; reines Markdown; Ketten Konzept → Referenz → Interna für abschnittsübergreifende Fragen; eigene Seite zu Grenzen |
| Strands Box | 3/4/4/4/4 | größer (~270 Chunks); Nutzer- und Designseiten zum selben Thema; Hinweis „wird überarbeitet“ im Nutzerteil |
| e2e (1. Durchsicht) | 3/3/3/3/0 | viele MDX-Komponenten; API ähnelt Playwright und ist teils erratbar |
| e2e (2. Durchsicht) | 3/3/4/4/2 | Anleitung (9 Gruppen) und Referenz (16 Seiten) getrennt; H2–H4 konsistent; Abschnitte Median 94 Wörter (p10 24, p90 323), 14 über 800; mehrere „Limits“-Abschnitte (cache, decision-models, web, mobile, lightpanda, testmu) und Fehlercode-Katalog; dichte Querverweise (core-concepts → cache → reference/agent → reference/errors); Referenzseiten sehr lang (engine 12.900, config 9.300, cli 9.000 Wörter); Prosa einheitlich, vermutlich von Agenten geschrieben und kuratiert (AGENTS.md verlangt Doku-Update je Verhaltensänderung); weniger als 5 % Beinahe-Duplikate |
| TanStack Charts | 3/2/3/3/4 | concepts / guides / reference getrennt, aber 583 H2 gegen 31 H3; rund 20 fast gleiche Framework-Seiten (~22 %); überwiegend KI-geschriebene Prosa; Alpha-Stabilitätsseite veraltet (CHANGELOG schon 1.1.0); Docs folgen unveröffentlichtem `main` |
| xy | 3/3/2/2/1 | 22 Diagrammseiten nach derselben Vorlage; 186 ausführbare Demo-Blöcke |
| django-ox | 2/3/2/3/3 | 21 sehr große Seiten, Abschnitte bis 7.000 Wörter; Werbe- und Benchmark-Seiten |
| Social SDK | 3/3/2/2/1 | generierte Fähigkeitsmatrix (~19 % des Korpus); fast gleiche Integrationsseiten |

### Spitzengruppe im Vergleich

GitHub-Daten vom 18.10.2026 (`gh api`).

| | e2e (gewählt) | Enroute (Reserve) | TanStack Charts | xy | Strands Box |
|---|---|---|---|---|---|
| Repository | `tester-army/e2e` | `enroute-sh/enroute` | `TanStack/charts` | `reflex-dev/xy` | `strands-agents/box` |
| Art | KI-gestützter End-to-End-Testläufer (TypeScript) | Git auf Objektspeicher | Diagrammbibliothek | Python-Diagrammbibliothek | Sandbox für KI-Agenten |
| Angelegt | 22.07.2026 | 24.08.2026 | 28.07.2026 | 09.07.2026 | 02.10.2026 |
| Letztes Release (18.10.) | e2e@0.21.2 (16.10.) | v0.3.0 (14.10.) | v1.1.0 (09.10.) | v0.0.8 (13.10.) | v0.1.0 (07.10.) |
| Sterne / Forks | 11.109 / 558 | 258 / 9 | 842 / 53 | 1.879 / 76 | 432 / 25 |
| Mitwirkende / Commits | 56 / 851 | 1 / 3 (je Release ein Commit) | 10 / 467 | 17 / 461 | 6 / 14 |
| Seiten / Tokens | 61 / 228.266 | 53 / 81.395 | 90 / 219.823 | 81 / 159.453 | 40 / 164.627 |
| Wissenslücke (Lückentext) | 36,5 % | 50,4 % | 29,7 % | 31,7 % | 38,6 % |
| Closed-Book ohne Doku richtig | 1/20 | 0/20 | 1/20 | 3/20 | – |
| Wertung | 67,5 | 81,2 | 66,2 | 73,8 | 70,0 |
| Qualitativ | 3/3/4/4/2 | 4/4/4/3/4 | 3/2/3/3/4 | 3/3/2/2/1 | 3/4/4/4/4 |
| Format | Mintlify-MDX | Markdown | Markdown | Markdown mit Demo-Blöcken | Markdown |

### Closed-Book-Fragen

Je 20 Fragen (Schritt 8), Daten in `questions/<name>.json`:

| Korpus | ohne Doku richtig | mit Abschnitt richtig | retrieval-abhängig, Anteil der mit Abschnitt richtigen (95-%-Konfidenzintervall) |
|---|---|---|---|
| Vue.js | 15 | 20 | 25 % (11–47) |
| Angular | 10 (nie „weiß nicht“) | 20 | 50 % (30–70) |
| xy | 3 | 20 | 85 % (64–95) |
| TanStack Charts | 1 | 19 | 95 % = 18/19 (75–99) |
| e2e | 1 (13 × „weiß nicht“) | 19 | 95 % = 18/19 (75–99) |
| Enroute | 0 (15 × „weiß nicht“) | 20 | 100 % (84–100) |

Auf Fragenebene trennen sich die bekannten Frameworks klar von den neuen Projekten; Enroute, e2e und TanStack Charts
sind bei 20 Fragen nicht unterscheidbar.

### Entscheidungsweg

1. Pilot `data/pilot/hard` (Vue): Antwortqualität an der Obergrenze; ohne Retrieval 14 von 16 Pilotfragen
   vollständig beantwortet (Beobachtung im Pilot, kein abgelegtes Artefakt; [ADR 0038](../adr/0038-korpus-e2e.md),
   Kontext).
2. Lückentext-Probe über 24 Dokumentationen: Vue und Angular bekannt, die neuen Projekte 20,2–50,4 % Lücke; die Wertung
   wählte Enroute (Bericht an Jonas, 18.10.2026).
3. Einwand: Enroute hat einen Maintainer und drei Commits; gesucht war ein ähnlich geeignetes, real genutztes Projekt.
4. [Closed-Book-Fragen](#closed-book-fragen) für die Spitzengruppe und Vue, auf Wunsch für die Mail an den Betreuer
   auch Angular: Vue 15/20, Angular 10/20, die neuen Projekte 0–3/20.
5. Gewählt: e2e, Enroute bleibt Reserve; Begründung: [ADR 0038](../adr/0038-korpus-e2e.md).

### MDX-Probe (e2e)

Probelauf mit sieben Regeln am 18.10.2026 (nicht der spätere Preprocessing-Code): Navigationskarten (`Card`,
`CardGroup`, 104/43) und Einbettungen (`Video`, `SetupPrompt`) entfernt; `Note`/`Warning`/`Tip` als Text; Titel von
`Accordion`/`Tab`/`Step` als fette Zeile, Inhalt bleibt; `CodeGroup` (70) ausgepackt. Danach rund 50 Tags außerhalb
von Code, fast alle Platzhalter (`<NAME>`) oder TypeScript-Generics im Text. Einziger Inhaltsverlust wäre
`<ModelProvider>` (8 Einbindungen): Datenliste von 51 Modellanbietern (Name, Paket, Import, Umgebungsvariablen)
in `snippets/model-provider.jsx`; das Preprocessing gibt sie als Tabelle aus ([Korpus](corpus.md#aufbereitung-mdx--markdown)).

## Lizenzen

`data/corpus_probe/` zitiert einzelne Sätze der 24 Dokumentationen (`results/`, `misses/`, `questions/`). Lizenz je
Dokumentation, geprüft am 22.10.2026 am gepinnten Commit aus `candidates.csv` (`gh api repos/<repo>/license?ref=<commit>`):
Keiner der Docs-Ordner hat eine eigene Lizenzdatei, es gilt die des Repositorys; Fußzeilen der Docs-Websites sind nur
bei Angular geprüft. Alle Lizenzen erlauben die Weitergabe mit Urheber- und Lizenzhinweis. Reihenfolge wie
[Alle Kandidaten](#alle-kandidaten).

| # | Projekt | Lizenz (SPDX) | Quelle |
|---|---|---|---|
| 1 | Enroute | Apache-2.0 | [`LICENSE`](https://github.com/enroute-sh/enroute/blob/bc0dc6efce9cbbce9a5368e594a9b28f18a12d40/LICENSE) |
| 2 | xy | Apache-2.0 | [`LICENSE`](https://github.com/reflex-dev/xy/blob/7a75a983c3d9ea203495a879dbfd427df7fd0913/LICENSE) |
| 3 | django-ox | BSD-3-Clause | [`LICENSE`](https://github.com/oxpull/django-ox/blob/8429abcd6c48e0647f7963a333f7350248864268/LICENSE) |
| 4 | Social SDK | MIT | [`LICENSE`](https://github.com/opencoredev/social-sdk/blob/af61377586735dc51f6737a62c6d4ab2e05dd1b4/LICENSE) |
| 5 | Strands Box | Apache-2.0 | [`LICENSE`](https://github.com/strands-agents/box/blob/069c39cfd29f830aaadd2a1af362753a57c7b202/LICENSE) |
| 6 | e2e | Apache-2.0 | [`LICENSE`](https://github.com/tester-army/e2e/blob/ef977f4856da009cac26d78d2e9bb14e5991ee41/LICENSE) |
| 7 | TanStack Charts | MIT | [`LICENSE`](https://github.com/TanStack/charts/blob/f8f8ed7a326471e61faa0129688679f3eca9e388/LICENSE) |
| 8 | Vela | Apache-2.0 | [`LICENSE`](https://github.com/LuxAlgo/Vela/blob/850fa1f431e2065e9b0074c4b0555a48a2999eaf/LICENSE) |
| 9 | Vue.js | CC-BY-4.0 | [`LICENSE`](https://github.com/vuejs/docs/blob/40aa88af0094f7bab4aaf786e55c748a6a251d88/LICENSE) (Inhalte außer Bildern) |
| 10 | better-drizzle | Apache-2.0 | [`LICENSE`](https://github.com/almeidazs/better-drizzle/blob/0174cbd718d4ad4f79864078b9e4bae6b43c20b2/LICENSE) |
| 11 | Angular Native | MIT | [`LICENSE`](https://github.com/ng-native/ng-native/blob/1ec3d699517a2b2a60da825f5c0a53454bb36d14/LICENSE) |
| 12 | microcharts | MIT | [`LICENSE`](https://github.com/ganapativs/microcharts/blob/378d4fe2207bc1e1c8e7bd3b2957765fe005505c/LICENSE) |
| 13 | Lattice | MIT | [`LICENSE.md`](https://github.com/lattice-php/lattice/blob/9c83c070a1ac9e99927d588c93e0ceab68387976/LICENSE.md) |
| 14 | Nimbus | MIT | [`LICENSE`](https://github.com/cloudflare/nimbus/blob/0474e07d662796c1b5fe4ced400e8d10637664b3/LICENSE) |
| 15 | gori | Apache-2.0 | [`LICENSE`](https://github.com/hahwul/gori/blob/bd2142ebc2b92621b3b048f96016f336a6f86aae/LICENSE) |
| 16 | Sightmap | MIT | [`LICENSE`](https://github.com/sightmap/sightmap/blob/e229565648f34a9af4a8deca79d5afe23cd8ac6c/LICENSE) |
| 17 | Blume | MIT | [`LICENSE`](https://github.com/haydenbleasel/blume/blob/8d84df343070bcc23b7982ba70493679bd714a96/LICENSE) |
| 18 | Angular | CC-BY-4.0 | Fußzeile von angular.dev ([`footer.component.html`](https://github.com/angular/angular/blob/5d69bf4f4ae8f99c46d0d6481ec0709cb4be69d9/adev/src/app/core/layout/footer/footer.component.html)); der Code steht unter MIT ([`LICENSE`](https://github.com/angular/angular/blob/5d69bf4f4ae8f99c46d0d6481ec0709cb4be69d9/LICENSE)) |
| 19 | pgContext | Apache-2.0 | [`LICENSE`](https://github.com/Evokoa/pgContext/blob/aa91710e69bd6882a37f1c859d2f56d0e8a30ab9/LICENSE) |
| 20 | Shipyard | MIT | [`LICENSE`](https://github.com/cosscom/shipyard/blob/2928a430dbc12b22ffb955f4e3a4a0f6499842dc/LICENSE) |
| 21 | nub | MIT | [`LICENSE`](https://github.com/nubjs/nub/blob/02466954c428871e91f4de5733e713c498f80720/LICENSE) |
| 22 | Decionis agent-safe-pipeline | Apache-2.0 | [`LICENSE`](https://github.com/decionis/agent-safe-pipeline/blob/fc08a17c0542e68eeaa42d11c3df6b29710eef49/LICENSE) (Text der Apache License 2.0; GitHub meldet `NOASSERTION`) |
| 23 | Zuke | MIT | [`LICENSE`](https://github.com/zuke-build/zuke/blob/010554576b560180eaf8c4f0f6597de75c28d775/LICENSE) |
| 24 | NVX | MIT | [`LICENSE`](https://github.com/microsoft/nvx/blob/e67a06f4015a0d5d50f5c8e0070a781035785b60/LICENSE) |

## Grenzen

- Die Lückentext-Probe misst Einzelfakten; die Closed-Book-Fragen (20 je Korpus, breite Intervalle) und später die
  Prüfung jeder Katalogfrage bestätigen das auf Fragenebene ([ADR 0038](../adr/0038-korpus-e2e.md)).
- Die [Vorregistrierung](../../data/corpus_probe/preregistration.md) trägt das Datum 18.10.2026 und wurde lokal vor
  der Messung der neuen Kandidaten festgelegt, aber erst zusammen mit den Ergebnissen und ADR 0038 versioniert (Commit
  `4115ffc`); die Git-Historie belegt die Reihenfolge daher nicht.
- Die Fehltreffer klassifizierten Agenten, nicht eine Person; Strukturkennzahlen beruhen auf Pfad- und
  Musterheuristiken, Tokens sind Zeichen / 4.
- Die Stichprobe der aufgezeichneten Läufe hing von Pythons Hash-Seed ab (Reihenfolge einer Menge vor dem Mischen).
  `build_probes.py` sortiert inzwischen und zieht deterministisch eine neue Stichprobe; `--recorded` baut dagegen genau
  die aufgezeichneten Proben samt maskiertem Abschnittstext aus `results/` und den Seiten wieder auf. Geprüft
  (18.10.2026): Für alle 23 geklonten Kandidaten ergeben gepinnter Commit, `to_docs.py` und `--recorded` dieselben
  Seiten, dieselbe Seitenstatistik und dieselben Proben wie die aufgezeichneten Läufe, für Vue aus
  `documents.jsonl` des Snapshots `40aa88a` (damals noch in `data/processed/`; heute muss der Vue-Korpus dafür neu
  erzeugt werden, siehe [Dateien und Befehle](#dateien-und-befehle)). Die Antworten selbst sind nicht bitgenau
  wiederholbar (Modell nur als Alias, `seed` nur „best effort“, [ADR 0033](../adr/0033-antwortmodell.md)); belegt sind
  die Werte durch die abgelegten Ergebnisse.
- Drei Abweichungen der aufgezeichneten Läufe, in der Codex-Prüfung von PR #21 gefunden; `build_probes.py`,
  `run_probes.py` und `question_probe.py` sind seither korrigiert, `--recorded` wiederholt den alten Stand:
  - Code-Ausdrücke: Das Muster filterte die Länge innerhalb des regulären Ausdrucks, sodass bei benachbarten
    Ein-Zeichen-Ausdrücken (`` `+`/`×` ``) Prosa zwischen zwei Ausdrücken als Ausdruck galt (z. B. Vela,
    `results/vela.jsonl` Zeile 80). Betroffen sind laut ursprünglicher Auswertung 0–46 Proben je Korpus, davon
    höchstens 5 eindeutig gestellt; ohne sie ändere sich keine Wissenslücke um mehr als 0,4 Prozentpunkte (Vue,
    Angular, e2e, Enroute: unverändert). Nachprüfung 19.10.2026: bis 0,45 Prozentpunkte (Heuristik: Ausdruck beginnt
    oder endet mit Leerraum).
  - Open-Book-Kontext: Es wurden die ersten 6.000 Zeichen des Abschnitts gezeigt, auch wenn der Satz später stand;
    solche Proben fallen aus dem Nenner. Betroffen sind laut ursprünglicher Auswertung 0–23 Proben je Korpus (Vue 0,
    Enroute 0, e2e 3). Nachprüfung 19.10.2026 (Satz beginnt nach Zeichen 6.000): Enroute 0, e2e 2 sicher, 5 nicht
    zuzuordnen. Neu: ein Fenster um den Satz.
  - Modellkennung: Die Läufe speicherten nicht, welche Modellversion die API meldete; `gpt-6-luna` ist ein Alias.
    Alle Läufe fanden am 17./18.10.2026 statt. Neu: `model` sowie `closed_fingerprint` und `open_fingerprint` (die
    von der API gemeldete `system_fingerprint` je Lauf) je Ergebniszeile, `model` auch je Closed-Book-Frage; ein Lauf
    mit mehreren Modellen bricht ab.
- Abweichungen von der Vorregistrierung (Operationalisierung in `summarise.ratings`):
  - Struktur: dort auch die Streuung der Seitenlängen; umgesetzt nur Median H2–H4 je Seite (Stufen 3/5/6/8), minus 1
    bei mehr als 0,1 Ebenensprüngen je Seite (`page_iqr` steht in `summary.json`, geht aber nicht in die Wertung ein).
  - Dokumentationsqualität: dort Trennung Anleitung / Referenz, konsistente Überschriftenhierarchie,
    Frontmatter-Titel, Codebeispiele, wenig generierter Text; umgesetzt als Mittel aus Codeblöcken je 10.000 Tokens
    (Stufen 5/10/20/30), Frontmatter-Titeln (Anteil ≥ 0,9 → 4, sonst 0) und Referenzanteil nach Pfad (0,15–0,6 → 4,
    0,05–0,8 → 2, sonst 0). Hierarchie und generierter Text gehen nicht ein (Ebenensprünge zählen bei Struktur).
  - Stabilität: dort Docs-Commits in 30 Tagen und Release-Tags zum Pinnen; umgesetzt nur `commits30` (4 minus Stufe
    11/31/61/151).
  - Passung: dort real genutztes Projekt, kein Marketing, nicht überwiegend KI-geschrieben; umgesetzt als Stufe des
    geschätzten KI-Anteils (`ai`, `config.CORPUS_PROBE_AI_RATING`), minus 1 unter 100 Sternen
    (`config.CORPUS_PROBE_FEW_STARS`). Marketing wurde nur in der qualitativen Durchsicht beurteilt.
  - Messung: dort „höchstens 12 Prosasätze mit je einem maskierten Ausdruck“ je Seite; umgesetzt höchstens 12 Proben
    je Seite, ein Satz kann mehrere Proben liefern (Schritt 3).
  - Ausschlusskriterium 5 (80.000–300.000 Tokens) gilt in `summarise.py` nur für den Pool der Sensitivität und nur mit
    der Untergrenze (Sightmap, siehe [Alle Kandidaten](#alle-kandidaten)).

  Die Wertung wurde nachträglich nicht geändert. Die Entscheidung für e2e stützt sich
  vor allem auf die Closed-Book-Fragen und den Umfang, nicht auf die Rangfolge der Wertung.
- Blume wurde vor der Erweiterung des Changelog-Filters gelesen und enthält die Seite `advanced/changelog.mdx` (eine
  Anleitung zur Changelog-Funktion, kein Changelog); `skip_changelogs` = `no` hält das fest.

## Dateien und Befehle

Skripte in `scripts/corpus_probe/`, Daten in `config.CORPUS_PROBE_DIR` = `data/corpus_probe/`:

| Datei | Inhalt |
|---|---|
| `candidates.csv` | `name`, `repo` (`local` = Vue-Snapshot), `docs_path`, `commit`, `commit_date`, `product` (Name im Prompt), `drops`, `skip_changelogs` (`yes` = Changelog-Dateien auslassen), `commits30` (Docs-Commits in 30 Tagen), `stars`, `ai` (grobe Einschätzung des KI-geschriebenen Textanteils: `low`, `medium`, `medium-high`, `high`; kein Messwert), `new` (nach dem 31.05.2026 veröffentlicht) |
| `stats.json` | Seitenstatistik je Korpus (Tokens je Seite, H2–H4 je Seite, JSX-Zeilen, Codeblöcke, Frontmatter-Titel, Ebenensprünge, Referenzanteil) |
| `results/<name>.jsonl` | eine Zeile je Probe: `doc_id`, `path`, `page`, `section`, `sentence` (maskiert), `answer` (Ausdruck), `kind`, `area`, `closed`, `open`, `closed_ok`, `open_ok`; neue Läufe zusätzlich `model`, `closed_fingerprint`, `open_fingerprint` |
| `misses/<name>.json` | eindeutig gestellte closed-book-Fehltreffer: `id` (Zeile in `results/`, ab 0), `page`, `section`, `sentence`, `answer`, `closed_book_guess` (die ersten `config.CORPUS_PROBE_GUESS_CHARS` Zeichen der Closed-Book-Antwort), `category` |
| `summary.json` | Messwerte, Stufen und Wertung je Korpus, Rangfolgen der Gewichtungen |
| `questions/<name>.json` | Closed-Book-Fragen: `id`, `path`, `section`, `type`, `question`, `reference`, `closed`, `open`, `closed_verdict`, `open_verdict`, `judge_batch`; neue Läufe zusätzlich `model` |

`docs/`, `probes/`, `sources/` und `questions/*-sections.json` sind Zwischenstände (ganze Seiten oder Abschnitte) und
nicht versioniert; die Dateien des Urteilslaufs (`questions/judge-input.json`, `judge-key.json`, `judge-output.json`)
sind nicht abgelegt. Die Vue-Zeile liest `data/processed/documents.jsonl`; dort liegt seit
[ADR 0038](../adr/0038-korpus-e2e.md) der e2e-Korpus, und ein Lauf unter dem Namen `vue` würde still e2e messen. Für
die Vue-Zeile zuerst den Vue-Korpus neu erzeugen: Code-Stand `4115ffc` (pinnt `vuejs/docs` auf `40aa88a`), dort
`snapshot.py`, `ingest.py`, `preprocess.py`. Ein Korpus neu messen:
`scripts/corpus_probe/probe_corpus.sh <name>` (ruft die OpenAI-API; `--recorded` wiederholt die aufgezeichneten
Proben statt eine neue Stichprobe zu ziehen), dann klassifizieren (ein Agent trägt mit dem Prompt oben `category` in
`misses/<name>.json` ein) und
`uv run python scripts/corpus_probe/summarise.py`. Closed-Book-Fragen: `question_probe.py sample NAME…`, Fragen
schreiben lassen, `answer NAME…` (API), `blind BATCH NAME…`, urteilen lassen, `unblind`, `summary`.
