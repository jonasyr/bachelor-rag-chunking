# Dokumentation

*Doku-Index · Verwandt: [Repo-README](../README.md), [Plan](plan.md#stand), [ADRs](adr/README.md)*

Code der Bachelorarbeit „Einfluss von Chunking-Strategien auf die Retrieval- und Antwortqualität eines
RAG-Systems für technische Projektdokumentation“. Jede Tatsache hat genau ein Zuhause; andere Seiten verlinken dorthin.
Bei Widersprüchen gelten die [ADRs](adr/README.md), danach die Seiten unter „Nachschlagen“. Projektstand:
[plan.md](plan.md#stand).

## Einstieg

- Neu im Projekt: [Repo-README](../README.md) → [Forschungsdesign](explanation/research-design.md) →
  [Experiment durchführen](how-to/run-the-experiment.md) → [Evaluation](reference/evaluation.md).
- Ergebnisse prüfen (Begutachtung): [Ergebnisse nachvollziehen](how-to/reproduce-the-results.md).
- Mitarbeit am Code: [Einrichten](how-to/set-up.md) → [Werkzeuge](reference/tooling.md) →
  [Konfiguration](reference/configuration.md) und [Datenformate](reference/data-formats.md); Regeln für Branches,
  Reviews und Befunde: [AGENTS.md](../AGENTS.md).

## Anleitungen (how-to)

| Seite | Wofür |
|---|---|
| [how-to/set-up.md](how-to/set-up.md) | Einrichten: Voraussetzungen, Abhängigkeiten, API-Schlüssel, pre-commit |
| [how-to/create-corpus-snapshot.md](how-to/create-corpus-snapshot.md) | e2e-Snapshot erstellen, aufbereiten, Manifest erzeugen |
| [how-to/build-the-question-catalogue.md](how-to/build-the-question-catalogue.md) | Fragenkatalog schreiben, annotieren, Closed-Book-Prüfung, prüfen und einfrieren |
| [how-to/run-the-experiment.md](how-to/run-the-experiment.md) | Vorbereitung (Chunking, Embeddings) und Hauptlauf in Reihenfolge auf dem Branch `run/hauptlauf`: Retrieval, Antworten, Bewertung, Zweitbewertung, RAGAS, Auswertung; Prüfliste |
| [how-to/deliver-results-to-thesis.md](how-to/deliver-results-to-thesis.md) | Ergebnisse aus `output/` per Pull Request und Submodul-Zeiger an die Arbeit (PaperLab) übergeben |
| [how-to/work-on-two-machines.md](how-to/work-on-two-machines.md) | Laptop und PC: einen Rechner einrichten, wechseln, was nur auf einem Rechner läuft |
| [how-to/reproduce-the-results.md](how-to/reproduce-the-results.md) | Für Begutachtende: Korpus, Index, Retrieval und Auswertung ohne API-Schlüssel nachrechnen und vergleichen |

## Nachschlagen (reference)

| Seite | Inhalt |
|---|---|
| [reference/configuration.md](reference/configuration.md) | Alle Schlüssel aus `src/config.py` nach Bereich: Wert, Bedeutung, ADR |
| [reference/corpus.md](reference/corpus.md) | Korpus e2e: Quelle, Bereiche, MDX-Aufbereitung, Abschnitte, Manifest |
| [reference/corpus-selection.md](reference/corpus-selection.md) | Korpusauswahl: Vorgehen, Ergebnis, Grenzen, Dateien und Befehle |
| [reference/data-formats.md](reference/data-formats.md) | Formate aller Datenartefakte, Laufprotokoll, Auswertung, Pilot-Sets; versioniert und ignoriert |
| [reference/question-catalogue.md](reference/question-catalogue.md) | Fragenkatalog: Umfang, Typen, Konstruktionsklassen, Regeln für Annotation und Aufbau |
| [reference/evaluation.md](reference/evaluation.md) | Metriken, Kontrollen K1 und K0, Rubrik, regelbasierte und blinde Bewertung, Triangulation mit RAGAS, Zweitbewertung, Kosten, Statistik, Abbildungen |
| [reference/prompts.md](reference/prompts.md) | Prompt-Vorlagen (mit Kontext; Closed-Book für Prüfung und K0) und Parameter |
| [reference/literature.md](reference/literature.md) | Literaturbasis, technische Webquellen, Methodenquellen der Bewertung |
| [reference/experiment-record.md](reference/experiment-record.md) | Gemessene Zahlen der e2e-Läufe: Snapshot, Chunking, Embedding, Pilot, Probelauf, RAGAS-Pilot, Modellversionen |
| [reference/experiment-record-vue.md](reference/experiment-record-vue.md) | Historie: gemessene Zahlen des Vue.js-Korpus bis 18.10.2026 |
| [reference/tooling.md](reference/tooling.md) | Tech-Stack, Repository-Struktur, Skript-Optionen, Umgebungsvariablen, Qualitätswerkzeuge, Tests |
| [corpus_manifest.csv](corpus_manifest.csv) | Korpusmanifest (eine Zeile je Seite, erzeugt von `src/preprocess.py`) |
| [corpus_snapshot.txt](corpus_snapshot.txt) | Snapshot-Protokoll: Commit, Daten, SHA-256 je Datei (erzeugt von `src/snapshot.py`) |

## Hintergrund (explanation)

- [explanation/research-design.md](explanation/research-design.md): Forschungsfrage, Rahmen und Forschungslücke,
  Wahl des Korpus, Chunking-Strategien, warum nur das Chunking variiert, Closed-Book-Prüfung und K0, Anlage der
  Evaluation, Architektur, Validität und Grenzen, Prompt-Gestaltung

## Entscheidungen und Plan

- [adr/README.md](adr/README.md): Index der Entscheidungen (ADR 0001 ff.; 0001–0018 = D1–D18 des früheren
  Leitfadens), je eine Datei
- [plan.md](plan.md): Stand, Zeitplan, Backlog, offene Entscheidungen, Verlauf
- [superpowers/README.md](superpowers/README.md): datierte Entwürfe (`specs/`) und Umsetzungspläne (`plans/`);
  Momentaufnahmen, werden nicht nachgepflegt

Das Exposé (final, bei der IU angemeldet), Text, Gliederung und IU-Form der Arbeit liegen im privaten Repo PaperLab,
das dieses Repo als Submodul `code/` einbindet; dort prüft `./paperlab check` Format und Stilregeln.
