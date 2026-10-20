# Dokumentation

Code der Bachelorarbeit „Einfluss von Chunking-Strategien auf die Retrieval- und Antwortqualität eines
RAG-Systems für technische Projektdokumentation“. Jede Tatsache hat genau ein Zuhause; andere Seiten verlinken dorthin.
Bei Widersprüchen gelten die [ADRs](adr/README.md), danach die Seiten unter „Nachschlagen“. Projektstand:
[plan.md](plan.md#stand).

## Anleitungen (how-to)

| Seite | Wofür |
|---|---|
| [how-to/set-up.md](how-to/set-up.md) | Einrichten: Abhängigkeiten, API-Schlüssel (nur für API-Schritte), pre-commit |
| [how-to/create-corpus-snapshot.md](how-to/create-corpus-snapshot.md) | e2e-Snapshot erstellen, aufbereiten, Manifest erzeugen |
| [how-to/build-the-question-catalogue.md](how-to/build-the-question-catalogue.md) | Fragenkatalog schreiben, annotieren, Closed-Book-Prüfung, prüfen und einfrieren |
| [how-to/run-the-experiment.md](how-to/run-the-experiment.md) | Schritte der Pipeline (C1–C3, Kontrollen K1 und K0), Prüfliste vor jedem Evaluationslauf |
| [how-to/deliver-results-to-thesis.md](how-to/deliver-results-to-thesis.md) | Tabellen und Abbildungen per Pull Request und Submodul-Zeiger in die Arbeit (PaperLab) übernehmen |

## Nachschlagen (reference)

| Seite | Inhalt |
|---|---|
| [reference/configuration.md](reference/configuration.md) | Alle Schlüssel aus `src/config.py`: Wert oder Typ, Bedeutung, ADR |
| [reference/corpus.md](reference/corpus.md) | Korpus e2e: Commit, Bereiche, MDX-Aufbereitung, Anker, Schema von `corpus_manifest.csv` |
| [reference/corpus-selection.md](reference/corpus-selection.md) | Korpusauswahl: Lückentext-Probe über 24 Dokumentationen, Closed-Book-Fragen, Kriterien, Ergebnis, Dateien |
| [reference/data-formats.md](reference/data-formats.md) | Formate aller Datenartefakte (JSONL, CSV); welche Dateien versioniert und welche ignoriert sind |
| [reference/question-catalogue.md](reference/question-catalogue.md) | Fragenkatalog: Umfang, Typen, Konstruktionsklassen, Felder, Regeln für Annotation und Closed-Book-Prüfung |
| [reference/evaluation.md](reference/evaluation.md) | Metriken, Kontrollen K1 und K0, Rubrik, regelbasierte und blinde Bewertung, Triangulation (optional), Kosten, Statistik, Abbildungen |
| [reference/prompts.md](reference/prompts.md) | Prompt-Vorlagen (mit Kontext; Closed-Book für Prüfung und K0) und konstante Parameter |
| [reference/literature.md](reference/literature.md) | Literaturbasis (15 Quellen) und technische Webquellen |
| [reference/experiment-record.md](reference/experiment-record.md) | Laufprotokoll: Snapshot, Chunking, Embedding, Stichprobenplan, Pilotproben, Modellversionen (gemessene Zahlen) |
| [reference/tooling.md](reference/tooling.md) | Tech-Stack, Repository-Struktur, Skript-Optionen, Qualitätswerkzeuge |
| [corpus_manifest.csv](corpus_manifest.csv) | Korpusmanifest (60 Seiten, erzeugt von `src/preprocess.py`) |
| [corpus_snapshot.txt](corpus_snapshot.txt) | Snapshot-Protokoll: Commit, Daten, SHA-256 je Datei (erzeugt von `src/snapshot.py`) |

## Hintergrund (explanation)

- [explanation/research-design.md](explanation/research-design.md): angemeldete Forschungsfrage, Unterfragen,
  Hypothesen, Forschungslücke, Wahl des Korpus, warum diese Strategien und die Kontrolle K1, warum nur das Chunking
  variiert, Anlage der Evaluation, warum Closed-Book-Prüfung und K0, Architektur, Validität und Grenzen,
  Prompt-Gestaltung

## Entscheidungen und Plan

- [adr/](adr/README.md): Entscheidungen ADR 0001–0043 (0001–0018 = D1–D18 des früheren Leitfadens), je eine Datei
- [plan.md](plan.md): Projektstand, Zeitplan und offene Entscheidungen
- `superpowers/` (`specs/`, `plans/`): datierte Entwürfe und Umsetzungspläne einzelner Arbeitsschritte; Momentaufnahmen,
  werden nicht nachgepflegt

Das Exposé (final, bei der IU angemeldet), Text, Gliederung und IU-Form der Arbeit liegen im privaten Repo PaperLab,
das dieses Repo als Submodul `code/` einbindet; dort prüft `./paperlab check` Format und Stilregeln.
