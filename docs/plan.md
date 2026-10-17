# Plan und offene Entscheidungen

> Projektstand, kein Diátaxis-Typ. Übersicht: [Dokumentation](README.md).

## Stand

Stand 14.10.2026: Korpus festgelegt (Guide, API-Referenz, Style Guide;
[ADR 0025](adr/0025-korpus-guide-api-styleguide.md)); Kontrolle K1 und faire Sensitivitätsregel beschlossen
([ADR 0026](adr/0026-c3-vergleichbarkeit.md)). Umgesetzt und getestet: `snapshot.py`, `ingest.py`, `preprocess.py`,
`chunking.py`, `embed.py`, `retrieve.py` (inkl. `--control` für K1), Fragenkatalog-Werkzeuge `catalogue.py` und
`freeze.py` ([ADR 0029](adr/0029-fragetypen-und-konstruktionsklassen.md), [ADR 0030](adr/0030-einfrieren-des-fragenkatalogs.md)), Stichprobenplan, Editor
`app/catalogue_editor.py` und protokollierte KI-Durchsicht ([ADR 0031](adr/0031-stichprobenplan-und-ki-durchsicht.md)).
Stand 16.10.2026: `evaluate_retrieval.py` (Haupt- und Sensitivitätsregel, K1 mit `--control`) und `evaluate_answers.py`
(blinde Rubrik-Bewertung, [ADR 0032](adr/0032-blinde-rubrik-bewertung.md)) umgesetzt und getestet.
Stand 17.10.2026: Antwortmodell `gpt-6-luna` gepinnt (Effort `none`, Temperatur 0,
[ADR 0033](adr/0033-antwortmodell.md)); `generate.py` umgesetzt und getestet (ohne echten API-Aufruf). Damit ist kein
Schritt der Pipeline mehr Platzhalter. Nächster Schritt: Stichprobenplan ziehen, dann 48 Fragen
in sechs Blöcken zu 8 schreiben und annotieren ([Fragenkatalog erstellen](how-to/build-the-question-catalogue.md)),
Einfrieren bis 06.11.2026 (Meilenstein 09.11.).

## Zeitplan (13.10.–24.12.2026)

Neu geplant am 13.10.2026: Pipeline und Fragenkatalog zuerst, dann Experimente, dann Schreiben. Abgabe 24.12.2026
([ADR 0004](adr/0004-zeitraum-und-abgabe.md)).

| Zeitraum | Phase | Schwerpunkte | Ergebnis |
|----------|-------|--------------|----------|
| 13.–19.10. | Korpus | Snapshot, `ingest.py`, `preprocess.py` (test-first), Korpusmanifest; am 14.10. auf Guide + API + Style Guide erweitert (erledigt) | `documents.jsonl`, `corpus_manifest.csv`, Token-Zahl im Experiment-Protokoll |
| 20.10.–02.11. | Pipeline | Chunking C1–C3 und K1, Embedding, Chroma, Retrieval; Embedding-Modell, SDK und Chroma gepinnt (erledigt 13.–14.10.); Generierung und GPT-Modell erledigt 17.10.; offen: Prototyp mit einer Frage | lauffähige Pipeline, Modellversionen dokumentiert |
| 20.10.–08.11. | Fragenkatalog (parallel) | 48 Fragen in sechs Blöcken zu 8 (zwei je Woche ab 20.10., Einfrieren 06.11.; Stichprobenplan und KI-Durchsicht nach jedem Block, [ADR 0031](adr/0031-stichprobenplan-und-ki-durchsicht.md)), Referenzantworten, `relevant_section_ids` (blind annotiert, [ADR 0027](adr/0027-blinde-annotation.md)); Vortest von Prompt und Rubrik: 5 Pilotfragen (nicht aus dem Katalog) über die ganze Kette inkl. Generierung und Bewertung, sobald der Prototyp steht; ergänzt die Retrieval-Pilotproben mit 8 und 16 Fragen vom 14.10. ([Experiment-Protokoll](reference/experiment-record.md)) und hält den Katalog unberührt ([ADR 0027](adr/0027-blinde-annotation.md)) | `questions.csv`, `ground_truth.csv` |
| 03.–09.11. | Auswertungsskripte | Relevanz per Token-Überlappung (erledigt in `retrieve.py`/`relevance.py`); Recall/Precision/MRR/Hit@5, RAGAS, Kostenerfassung, Kontext-Tokens je Antwort | `evaluate_retrieval.py`, `evaluate_answers.py` getestet |
| **09.11.** | **Meilenstein** | **Ground Truth eingefroren** ([ADR 0017](adr/0017-fragenkatalog.md)) | Commit-Hash im Experiment-Protokoll |
| 10.–16.11. | Experimente | volle Läufe C1–C3, Kontrolle K1 (nur Retrieval), Sensitivitätsprüfung ([ADR 0026](adr/0026-c3-vergleichbarkeit.md)) | `retrieved_results.csv`, `retrieved_results_control.csv` (K1), `generated_answers.csv` |
| 17.–25.11. | Bewertung und Analyse | manuelle Rubrik (144 Antworten: 48 Fragen × C1–C3), RAGAS-Abgleich, Statistik, Abbildungen | `scores.csv`, `output/tables/`, `output/figures/` |
| 26.11.–13.12. | Schreibphase | Methodik, Implementierung, Ergebnisse, Diskussion, Fazit (Grundlagen siehe Hinweis) | Rohfassung komplett |
| 14.–20.12. | Überarbeitung | Sprache, Argumentation, roter Faden, `./paperlab check` | Endfassung |
| 21.–23.12. | Puffer | Korrektorat, Formatierung, Zitation, `./paperlab final` | Abgabe-PDF |
| 24.12. | Abgabe | Einreichung | |

> **Risiko Schreibphase:** Für das Schreiben bleiben knapp drei Wochen. Kapitel ohne Ergebnisabhängigkeit
> (Einleitung, Grundlagen, Methodik) ab Anfang November parallel zur Pipeline entwerfen.

> Der Fragenkatalog wird regelmäßig unterschätzt — bewusst Zeit einplanen.

> **Puffer-Regel:** Rutscht der Meilenstein 09.11., zuerst C4 ([ADR 0028](adr/0028-c4-bedingung.md)) und
> RAGAS-Feinheiten streichen, nicht die Schreibphase.

Der ursprüngliche Phasenplan (Juni 2026, Abgabe 15.12.) steht in der Git-Historie.


## Offene Entscheidungen / vor Beginn zu bestätigen

- **Modell-/Versionswahl:** konkretes GPT-Modell und SDK-/API-Version zum Implementierungszeitpunkt fixieren und dokumentieren. Entschieden: Embedding-Modell sowie SDK- und Chroma-Version ([ADR 0023](adr/0023-embedding-modell.md)), GPT-Modell `gpt-6-luna` ([ADR 0033](adr/0033-antwortmodell.md)).
- **Embedding-Sprache:** Korpus ist englisch; Fragen/Referenzantworten englisch halten (Konsistenz mit Embedding-Raum).
- **Zweitbewertung:** Verfügbarkeit einer zweiten bewertenden Person klären (stärkt Konstruktvalidität). Eine
  Zweitannotation der Relevanz (10–12 Fragen, blind, Übereinstimmungsmaß) ist vorgemerkt: später, falls Zeit bleibt.
- **Fragenkatalog:** entschieden: 48 Fragen, Typen und Konstruktionsklassen mit Quoten und Bereichsuntergrenzen ([ADR 0029](adr/0029-fragetypen-und-konstruktionsklassen.md)), Einfrieren als Sperre vor dem Retrieval ([ADR 0030](adr/0030-einfrieren-des-fragenkatalogs.md)).
- **C4 (semantisch):** entschieden: nur, wenn der Meilenstein 09.11. (Ground Truth eingefroren) planmäßig erreicht ist
  ([ADR 0028](adr/0028-c4-bedingung.md)).
