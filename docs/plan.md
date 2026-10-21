# Plan und offene Entscheidungen

> Projektstand, kein Diátaxis-Typ. Übersicht: [Dokumentation](README.md).

## Stand

Stand 20.10.2026: Die Schritte 1–4 des Korpuswechsels zu e2e ([ADR 0038](adr/0038-korpus-e2e.md)) sind erledigt:
(1) Entscheidung und Messung ([Korpusauswahl](reference/corpus-selection.md)); (2) Snapshot und Preprocessing
([Korpus](reference/corpus.md), [ADR 0042](adr/0042-mdx-umwandlung.md)); (3) Chunk-Dateien und Embeddings
([Experiment-Protokoll](reference/experiment-record.md#embedding-e2e)); (4) Katalogwerkzeuge: (4a) Quoten je Bereich
und Stichprobenplan ([ADR 0039](adr/0039-stichprobenplan-e2e.md)), (4b) Closed-Book-Prüfung im Editor
([ADR 0040](adr/0040-closed-book-pruefung.md)), (4c) Kontrolle K0 ohne Retrieval
([ADR 0041](adr/0041-kontrolle-k0.md)). Alle Schritte der Pipeline sind umgesetzt und getestet, ebenso die Auswertungsskripte (`src/analyse.py`, erledigt
20.10.2026, [ADR 0044](adr/0044-statistische-auswertung.md)); echte Läufe auf dem Katalog stehen aus. (5) Pilot auf e2e erledigt 20.10.2026 ([Experiment-Protokoll](reference/experiment-record.md#pilot-e2e-1920102026);
offen nur Jonas' Übungsbewertung von 3 Fragen); die Regel zu `direct` ist präzisiert
([ADR 0043](adr/0043-praezisierung-direct-und-teilantworten.md)). Stand 21.10.2026: Der Hauptkatalog hat noch 0 von 48
Fragen. Nächster Schritt: 48 Fragen in sechs Blöcken zu 8 schreiben und annotieren
([Fragenkatalog erstellen](how-to/build-the-question-catalogue.md)); weitere Punkte im [Backlog](#backlog).
Frühere Stände: [Verlauf](#verlauf).

## Zeitplan (13.10.–24.12.2026)

Neu geplant am 13.10.2026: Pipeline und Fragenkatalog zuerst, dann Experimente, dann Schreiben. Abgabe 24.12.2026
([ADR 0004](adr/0004-zeitraum-und-abgabe.md)).

| Zeitraum | Phase | Schwerpunkte | Ergebnis |
|----------|-------|--------------|----------|
| 13.–19.10. | Korpus | **erledigt 18.10.:** Snapshot, `ingest.py`, `preprocess.py` (test-first), Korpusmanifest; am 18.10. Wechsel zu e2e beschlossen ([ADR 0038](adr/0038-korpus-e2e.md)) und Snapshot und Neuaufbau auf e2e abgeschlossen | `documents.jsonl`, `corpus_manifest.csv`, Token-Zahl im Experiment-Protokoll |
| 20.10.–02.11. | Pipeline | **erledigt:** Chunking C1–C3 und K1, Embedding, Chroma, Retrieval (13.10., auf e2e neu am 18.10.); Embedding-Modell, SDK und Chroma gepinnt (13.–14.10.); Generierung und GPT-Modell (17.10.); Kontrolle K0 (19.10.). Der Prototyp mit einer Frage ist durch die Pilotläufe auf Vue.js abgedeckt und wird auf e2e durch Schritt (5) ersetzt | lauffähige Pipeline, Modellversionen dokumentiert |
| 20.10.–08.11. | Fragenkatalog (parallel) | Vorab Schritt (5): Pilot auf e2e (nicht aus dem Katalog) als Vortest von Prompt und Rubrik, **erledigt** 20.10.; der Vortest auf dem Vue-Set `hard` ist erledigt (18.10., zählt nicht). Dann 48 Fragen in sechs Blöcken zu 8 (zwei je Woche ab 20.10., Einfrieren 06.11.; Stichprobenplan gezogen 19.10. ([ADR 0039](adr/0039-stichprobenplan-e2e.md)), KI-Durchsicht ([ADR 0031](adr/0031-stichprobenplan-und-ki-durchsicht.md)) und Closed-Book-Prüfung ([ADR 0040](adr/0040-closed-book-pruefung.md)) nach jedem Block), Referenzantworten, `relevant_section_ids` (blind annotiert, [ADR 0027](adr/0027-blinde-annotation.md)) | `questions.csv`, `ground_truth.csv`, `closed_book_screen.csv` |
| 03.–09.11. | Auswertungsskripte | **erledigt 16.–17.10. und 20.10.:** Statistik, Tabellen und Abbildungen (`analyse.py`, `stats.py`, `report_tables.py`, `report_figures.py`, [ADR 0044](adr/0044-statistische-auswertung.md)); zuvor Relevanz per Token-Überlappung (`retrieve.py`/`relevance.py`); Recall/Precision/MRR/Hit@5, Kostenerfassung, Kontext-Tokens je Antwort (16.10.); regelbasierte Bewertung in der App (17.10., [ADR 0035](adr/0035-regelbasierte-bewertung.md)). RAGAS fest nach der regelbasierten Bewertung ([ADR 0047](adr/0047-ragas-als-triangulation.md)) | `evaluate_retrieval.py`, `evaluate_answers.py`, `analyse.py` getestet |
| **09.11.** | **Meilenstein** | **Ground Truth eingefroren** ([ADR 0017](adr/0017-fragenkatalog.md)) | Commit-Hash im Experiment-Protokoll |
| 10.–16.11. | Experimente | volle Läufe C1–C3, Kontrolle K1 (nur Retrieval), Sensitivitätsprüfung ([ADR 0026](adr/0026-c3-vergleichbarkeit.md)), Kontrolle K0 (ohne Retrieval, im selben Generierungslauf, [ADR 0041](adr/0041-kontrolle-k0.md)) | `retrieved_results.csv`, `retrieved_results_control.csv` (K1), `generated_answers.csv`, `generated_answers_control.csv` (K0) |
| 17.–25.11. | Bewertung und Analyse | regelbasierte Rubrik-Bewertung (144 Antworten: 48 Fragen × C1–C3), danach 48 Antworten K0; Zweitbewertung von 36 Antworten ([ADR 0046](adr/0046-zweitbewertung.md)); RAGAS-Abgleich ([ADR 0047](adr/0047-ragas-als-triangulation.md)); Statistik, Abbildungen | `scores.csv`, `scores_control.csv`, `output/tables/`, `output/figures/` |
| 26.11.–13.12. | Schreibphase | Methodik, Implementierung, Ergebnisse, Diskussion, Fazit (Grundlagen siehe Hinweis) | Rohfassung komplett |
| 14.–20.12. | Überarbeitung | Sprache, Argumentation, roter Faden, `./paperlab check` | Endfassung |
| 21.–23.12. | Puffer | Korrektorat, Formatierung, Zitation, `./paperlab final` | Abgabe-PDF |
| 24.12. | Abgabe | Einreichung | |

> **Risiko Schreibphase:** Für das Schreiben bleiben knapp drei Wochen. Kapitel ohne Ergebnisabhängigkeit
> (Einleitung, Grundlagen, Methodik) ab Anfang November parallel zur Pipeline entwerfen.

> Der Fragenkatalog wird regelmäßig unterschätzt — bewusst Zeit einplanen.

> **Puffer-Regel:** Rutscht der Meilenstein 09.11., zuerst C4 ([ADR 0028](adr/0028-c4-bedingung.md)) und
> RAGAS-Feinheiten streichen, nicht die Schreibphase.

Vorschlag (Claude, 19.10.): Die Zeilen „Pipeline“ und „Auswertungsskripte“ sind vor ihrem Zeitraum erledigt. Die
frei gewordene Zeit vom 20.10. bis etwa 23.10. für Schritt (5) nutzen und die Fragenblöcke danach dichter legen (drei
je Woche statt zwei), damit das Einfrieren am 06.11. bleibt; den Zeitraum 03.–09.11. für das Analyse-Notebook und die
Skripte für `output/tables/` und `output/figures/` sowie für Einleitung, Grundlagen und Methodik nutzen. Jonas'
Daten in der Tabelle bleiben bis zu seiner Entscheidung unverändert.

Der ursprüngliche Phasenplan (Juni 2026, Abgabe 15.12.) steht in der Git-Historie.

## Backlog

Offene Arbeit nach Priorität (Punkt 1 ist die Katalogzeile des Zeitplans); erledigte Punkte wandern in den [Verlauf](#verlauf).

1. **Fragenkatalog** (kritischer Pfad): 48 Fragen in sechs Blöcken zu 8, nach jedem Block KI-Durchsicht und
   Closed-Book-Prüfung; Einfrieren bis 06.11. ([Fragenkatalog erstellen](how-to/build-the-question-catalogue.md)).
2. **Übungsbewertung Pilot**: Jonas bewertet die 9 Antworten in `data/pilot/e2e_jonas/`; danach Vergleich mit der
   Agentenbewertung im [Experiment-Protokoll](reference/experiment-record.md#pilot-e2e-1920102026).
3. **Zweitbewertung** ([ADR 0046](adr/0046-zweitbewertung.md)): zweite Person finden (bis Mitte November, sonst
   Ersatz nach ADR 0046); Ziehung der 12 Fragen und Übereinstimmungsrechnung umsetzen, Ziehung nach dem Einfrieren.
4. **RAGAS** ([ADR 0047](adr/0047-ragas-als-triangulation.md)): Code und Pilot erledigt 21.10.
   ([Experiment-Protokoll](reference/experiment-record.md#ragas-pilot-e2e-21102026)); Hauptlauf nach `summarise`.
5. **Demo-Dashboard** (niedrige Priorität): Ergebnisse interaktiv zeigen, nur falls Zeit bleibt.

## Offene Entscheidungen

- **Zweitannotation der Relevanz:** 10–12 Fragen, blind; nach dem Einfrieren entscheiden, falls Zeit bleibt
  ([ADR 0046](adr/0046-zweitbewertung.md)).
- **C4 (semantisch):** läuft nur, wenn der Meilenstein 09.11. (Ground Truth eingefroren) planmäßig erreicht ist
  ([ADR 0028](adr/0028-c4-bedingung.md)).

Entschieden (Begründung in den ADRs): Embedding-Modell, SDK und Chroma ([ADR 0023](adr/0023-embedding-modell.md)),
Antwortmodell ([ADR 0033](adr/0033-antwortmodell.md)); Fragenkatalog mit 48 Fragen, Typen und Konstruktionsklassen
([ADR 0029](adr/0029-fragetypen-und-konstruktionsklassen.md)), Quoten je Bereich und Stichprobenplan auf e2e
([ADR 0039](adr/0039-stichprobenplan-e2e.md)), Closed-Book-Prüfung ([ADR 0040](adr/0040-closed-book-pruefung.md)),
Einfrieren vor dem Retrieval ([ADR 0030](adr/0030-einfrieren-des-fragenkatalogs.md)); Kontrolle K0
([ADR 0041](adr/0041-kontrolle-k0.md)); Zweitbewertung ([ADR 0046](adr/0046-zweitbewertung.md)); RAGAS fest nach der regelbasierten Bewertung
([ADR 0047](adr/0047-ragas-als-triangulation.md)).

## Verlauf

- 13.10.2026: Snapshot bis Retrieval auf Vue.js umgesetzt und getestet.
- 14.10.2026: Korpus Vue.js auf Guide, API-Referenz und Style Guide erweitert
  ([ADR 0025](adr/0025-korpus-guide-api-styleguide.md), später ersetzt durch [ADR 0038](adr/0038-korpus-e2e.md));
  Kontrolle K1 ([ADR 0026](adr/0026-c3-vergleichbarkeit.md)); Katalogwerkzeuge und Einfrieren
  ([ADR 0029](adr/0029-fragetypen-und-konstruktionsklassen.md), [ADR 0030](adr/0030-einfrieren-des-fragenkatalogs.md)).
- 15.10.2026: Stichprobenplan (Vue.js, inzwischen archiviert), Editor und protokollierte KI-Durchsicht
  ([ADR 0031](adr/0031-stichprobenplan-und-ki-durchsicht.md)).
- 16.10.2026: `evaluate_retrieval.py` und `evaluate_answers.py` (blinde Bewertung,
  [ADR 0032](adr/0032-blinde-rubrik-bewertung.md)).
- 17.10.2026: Antwortmodell `gpt-6-luna` ([ADR 0033](adr/0033-antwortmodell.md)), `generate.py`; Bewertung in der App,
  regelbasiert ([ADR 0034](adr/0034-bewertung-in-der-app.md)–[0036](adr/0036-regelbasierte-bewertung-verpflichtend.md)).
- 18.10.2026: Pilot `data/pilot/hard` (Vue.js) von einem Agenten als Entwicklungshilfe bewertet (zählt nicht); daraus
  präzisierte Prüfregeln ([ADR 0037](adr/0037-praezisierte-pruefregeln-und-vorbefuellte-kernpunkte.md)). Das
  Antwortmodell kennt Vue.js ([Korpusauswahl](reference/corpus-selection.md)): Korpuswechsel zu e2e beschlossen
  ([ADR 0038](adr/0038-korpus-e2e.md)); Snapshot, Preprocessing, Chunks und Embeddings auf e2e.
- 19.10.2026: Stichprobenplan auf e2e, Closed-Book-Prüfung, Kontrolle K0
  ([ADR 0039](adr/0039-stichprobenplan-e2e.md)–[0041](adr/0041-kontrolle-k0.md)); die Regeln der MDX-Umwandlung
  nachträglich festgehalten ([ADR 0042](adr/0042-mdx-umwandlung.md)).
- 19./20.10.2026: Pilot `data/pilot/e2e` (16 Fragen außerhalb des Stichprobenplans, ganze Pipeline mit K0;
  [Experiment-Protokoll](reference/experiment-record.md#pilot-e2e-1920102026)).
- 20.10.2026: Auswertungsskripte (`analyse.py`): Testplan, Tabellen und Abbildungen
  ([ADR 0044](adr/0044-statistische-auswertung.md)).
- 21.10.2026: Backlog angelegt; Ground-Truth-Prüfung weist doppelte `relevant_doc_ids` ab
  ([Datenformate](reference/data-formats.md)).
- 21.10.2026: Zweitbewertung ([ADR 0046](adr/0046-zweitbewertung.md)) und RAGAS als feste Triangulation
  ([ADR 0047](adr/0047-ragas-als-triangulation.md)) entschieden.
- 21.10.2026: RAGAS-Lauf (`src/ragas_eval.py`) umgesetzt und auf dem Pilot e2e erprobt, zwei Läufe, 4,05 USD
  ([Experiment-Protokoll](reference/experiment-record.md#ragas-pilot-e2e-21102026)).
