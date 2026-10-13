# Dokumentation

Code der Bachelorarbeit „Einfluss von Chunking-Strategien auf die Retrieval- und Antwortqualität eines
RAG-Systems für technische Projektdokumentation“. Jede Tatsache hat genau ein Zuhause; andere Seiten verlinken dorthin.

## Anleitungen (how-to)

| Seite | Wofür |
|---|---|
| [how-to/set-up.md](how-to/set-up.md) | Einrichten: Abhängigkeiten, API-Schlüssel, pre-commit |
| [how-to/create-corpus-snapshot.md](how-to/create-corpus-snapshot.md) | Vue.js-Snapshot erstellen und dokumentieren |
| [how-to/run-the-experiment.md](how-to/run-the-experiment.md) | Reihenfolge der Pipeline, Prüfliste vor jedem Evaluationslauf |
| [how-to/deliver-results-to-thesis.md](how-to/deliver-results-to-thesis.md) | Tabellen und Abbildungen in die Arbeit (PaperLab) übernehmen |

## Nachschlagen (reference)

| Seite | Inhalt |
|---|---|
| [reference/corpus.md](reference/corpus.md) | Korpusbereiche, Schema von `corpus_manifest.csv` |
| [reference/data-formats.md](reference/data-formats.md) | Formate aller Datenartefakte (JSONL, CSV) |
| [reference/question-catalogue.md](reference/question-catalogue.md) | Fragenkatalog: Umfang, Typen, Felder |
| [reference/evaluation.md](reference/evaluation.md) | Metriken, Rubrik, Triangulation, Kosten, Statistik, Abbildungen |
| [reference/prompts.md](reference/prompts.md) | Prompt-Vorlagen und konstante Parameter |
| [reference/literature.md](reference/literature.md) | Literaturbasis (15 Quellen) |
| [reference/experiment-record.md](reference/experiment-record.md) | Snapshot und Modellversionen (bei der Umsetzung ausfüllen) |
| [reference/tooling.md](reference/tooling.md) | Tech-Stack, Repository-Struktur, Skript-Optionen, Qualitätswerkzeuge |
| [corpus_manifest.csv](corpus_manifest.csv) | Korpusmanifest (52 Dateien, erzeugt von `src/preprocess.py`) |

## Hintergrund (explanation)

- [explanation/research-design.md](explanation/research-design.md): Forschungsfrage, Hypothesen, Forschungslücke,
  warum diese Strategien, Architektur, Validität, Prompt-Gestaltung

## Entscheidungen und Plan

- [adr/](adr/README.md): Entscheidungen D1–D18 und ADR 0019, je eine Datei
- [plan.md](plan.md): Zeitplan und offene Entscheidungen
- [Exposee.md](Exposee.md): Lesekopie des Exposés; Original (LaTeX) im privaten PaperLab-Repo

Text, Gliederung und IU-Form der Arbeit liegen im privaten Repo PaperLab, das dieses Repo als Submodul `code/`
einbindet; dort prüft `./paperlab check` Format und Stilregeln.
