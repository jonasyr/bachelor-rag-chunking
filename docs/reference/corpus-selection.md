# Korpusauswahl (Lückentext-Probe)

> Seitentyp: Nachschlagen (reference). Stand: 18.10.2026. Entscheidung: [ADR 0038](../adr/0038-korpus-enroute.md).
> Übersicht: [Dokumentation](../README.md).

Einmalige Diagnose, mit der der Korpus gewählt wurde; kein Teil des Experiments. Frage: Welche Dokumentation kennt
das Antwortmodell (`config.LLM_MODEL` = `gpt-6-luna`, Wissensstand 18.05.2026) noch nicht?

## Vorgehen

1. **Kandidaten.** Zwei unabhängige Recherchen (Bibliotheken und Frameworks; CLIs, Infrastruktur und Protokolle) über
   rund 2.500 GitHub-Repositories, die nach dem 01.06.2026 angelegt wurden; dazu Vue.js (bisheriger Korpus) und Angular
   (vom Betreuer vorgeschlagen) als bekannte Vergleiche. Ausschlusskriterien, Messung und Gewichte standen fest, bevor
   die neuen Kandidaten gemessen wurden: [`data/corpus_probe/preregistration.md`](../../data/corpus_probe/preregistration.md).
   Vue, Blume und e2e waren schon vorher gemessen und werden nach denselben Regeln gewertet.
2. **Seiten** (`to_docs.py`): alle `.md`/`.mdx`-Dateien des Docs-Ordners auf dem gepinnten Commit, ohne Übersetzungen,
   Changelogs und die in `candidates.csv` genannten Ausschlüsse; Titel aus dem Frontmatter, MDX-`import`/`export`
   entfernt. Vue: `data/processed/documents.jsonl` des Snapshots `40aa88a` nach dem Preprocessing.
3. **Proben** (`build_probes.py`): je Prosasatz (40–400 Zeichen, außerhalb von Code, Tabellen, HTML und Hinweisboxen)
   wird ein Inline-Code-Ausdruck (2–40 Zeichen) maskiert; höchstens 12 Proben je Seite, Seed 20261018
   (`config.CORPUS_PROBE_*`). Proben, deren Ausdruck im Seiten- oder Abschnittstitel steht, entfallen (`run_probes.py`).
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
   bewertete Qualität, Passung, Eignung für den Chunking-Vergleich, Fragenpotenzial und Aufbereitungsaufwand (je 0–4).

Prompt der Klassifikation (je Korpus; Eingabe `misses/<name>.json` ohne `category`):

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

## Ergebnis

24 Korpora, 14.547 Proben, davon 5.419 eindeutig gestellt und 2.088 closed-book verfehlt; Kosten rund 1 USD.
Vollständige Werte: [`data/corpus_probe/summary.json`](../../data/corpus_probe/summary.json).

| Korpus | Wertung | Wissenslücke (95-%-KI) | Seiten | Tokens (≈) |
|---|---|---|---|---|
| Enroute | 81,2 | 50,4 % (42,1–58,6) | 53 | 81.395 |
| xy | 73,8 | 31,7 % (25,8–37,5) | 81 | 159.453 |
| django-ox | 71,2 | 41,5 % (30,8–52,1) | 21 | 135.132 |
| Social SDK | 71,2 | 40,7 % (34,6–46,9) | 63 | 173.668 |
| Strands Box | 70,0 | 38,6 % (29,1–48,1) | 40 | 164.627 |
| Angular (bekannt) | 55,0 | 12,8 % (9,7–15,9) | 256 | 508.000 |
| Vue.js (bekannt) | 65,0 | 7,0 % (4,8–9,2) | 79 | 177.951 |

Alle 22 neuen Projekte liegen bei 20–50 %; kein Intervall überschneidet sich mit dem von Vue, mit dem von Angular
nur das von nub (20,2 %, KI 15,4–25,1) knapp. Enroute liegt in 4
von 5 Gewichtungen vorn (sonst Dritter). Qualitative Durchsicht (Qualität, Passung, Chunking, Fragen, Aufbereitung):
Enroute 4/4/4/3/4 (saubere Trennung Tutorial / How-to / Konzepte / Referenz / Interna, reines Markdown, eigene Seite
zu Grenzen), Strands Box 3/4/4/4/4 (größer, Nutzerteil „wird überarbeitet“), e2e 3/3/3/3/0, xy 3/3/2/2/1,
django-ox 2/3/2/3/3, Social SDK 3/3/2/2/1.

## Grenzen

- Die Probe misst Einzelfakten, nicht ganze Fragen; die Closed-Book-Prüfung jeder Katalogfrage bestätigt das auf
  Fragenebene ([ADR 0038](../adr/0038-korpus-enroute.md)).
- Die Fehltreffer klassifizierten Agenten, nicht eine Person; Strukturkennzahlen beruhen auf Pfad- und
  Musterheuristiken, Tokens sind Zeichen / 4.
- Die Stichprobe der aufgezeichneten Läufe hing von Pythons Hash-Seed ab (Reihenfolge einer Menge vor dem Mischen).
  `build_probes.py` sortiert inzwischen und zieht deterministisch eine neue Stichprobe; `--recorded` baut dagegen genau
  die aufgezeichneten Proben samt maskiertem Abschnittstext aus `results/` und den Seiten wieder auf. Geprüft
  (18.10.2026): Für alle 23 geklonten Kandidaten ergeben gepinnter Commit, `to_docs.py` und `--recorded` dieselben
  Seiten, dieselbe Seitenstatistik und dieselben Proben wie die aufgezeichneten Läufe, für Vue aus
  `documents.jsonl` des Snapshots `40aa88a`. Die Antworten selbst sind nicht bitgenau wiederholbar (Modell nur als
  Alias, `seed` nur „best effort“, [ADR 0033](../adr/0033-antwortmodell.md)); belegt sind die Werte durch die
  abgelegten Ergebnisse.
- Blume wurde vor der Erweiterung des Changelog-Filters gelesen und enthält die Seite `advanced/changelog.mdx` (eine
  Anleitung zur Changelog-Funktion, kein Changelog); `skip_changelogs` = `no` hält das fest.

## Dateien und Befehle

Skripte in `scripts/corpus_probe/`, Daten in `config.CORPUS_PROBE_DIR` = `data/corpus_probe/`:

| Datei | Inhalt |
|---|---|
| `candidates.csv` | `name`, `repo` (`local` = Vue-Snapshot), `docs_path`, `commit`, `commit_date`, `product` (Name im Prompt), `drops`, `skip_changelogs` (`yes` = Changelog-Dateien auslassen), `commits30` (Docs-Commits in 30 Tagen), `stars`, `ai` (Anteil KI-geschriebenen Texts, Einschätzung), `new` (nach dem 31.05.2026 veröffentlicht) |
| `stats.json` | Seitenstatistik je Korpus (Tokens je Seite, H2–H4 je Seite, JSX-Zeilen, Codeblöcke, Frontmatter-Titel, Ebenensprünge, Referenzanteil) |
| `results/<name>.jsonl` | eine Zeile je Probe: Satz, Ausdruck, beide Antworten, `closed_ok`, `open_ok` |
| `misses/<name>.json` | eindeutig gestellte closed-book-Fehltreffer mit `category`; `id` = Zeile in `results/` (ab 0) |
| `summary.json` | Messwerte, Stufen und Wertung je Korpus, Rangfolgen der Gewichtungen |

`docs/`, `probes/` und `sources/` sind Zwischenstände (ganze Seiten) und nicht versioniert. Ein Korpus neu messen:
`scripts/corpus_probe/probe_corpus.sh <name>` (ruft die OpenAI-API; `--recorded` wiederholt die aufgezeichneten
Proben statt eine neue Stichprobe zu ziehen), dann klassifizieren und
`uv run python scripts/corpus_probe/summarise.py`.
