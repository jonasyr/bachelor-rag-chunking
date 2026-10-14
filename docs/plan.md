# Plan und offene Entscheidungen

> Projektstand, kein Diátaxis-Typ. Übersicht: [Dokumentation](README.md).

## Stand

Stand 14.10.2026: Korpus festgelegt (Guide, API-Referenz, Style Guide;
[ADR 0025](adr/0025-korpus-guide-api-styleguide.md)); Kontrolle K1 und faire Sensitivitätsregel beschlossen
([ADR 0026](adr/0026-c3-vergleichbarkeit.md)). Umgesetzt und getestet: `snapshot.py`, `ingest.py`, `preprocess.py`,
`chunking.py`, `embed.py`, `retrieve.py` (inkl. `--control` für K1). Noch Platzhalter: `generate.py`,
`evaluate_retrieval.py`, `evaluate_answers.py`. Nächster Schritt: Werkzeuge für den Fragenkatalog (siehe
[Offene Entscheidungen](#offene-entscheidungen--vor-beginn-zu-bestätigen)).

## Zeitplan (13.10.–24.12.2026)

Neu geplant am 13.10.2026: Pipeline und Fragenkatalog zuerst, dann Experimente, dann Schreiben. Abgabe 24.12.2026
([ADR 0004](adr/0004-zeitraum-und-abgabe.md)).

| Zeitraum | Phase | Schwerpunkte | Ergebnis |
|----------|-------|--------------|----------|
| 13.–19.10. | Korpus | Snapshot, `ingest.py`, `preprocess.py` (test-first), Korpusmanifest; am 14.10. auf Guide + API + Style Guide erweitert (erledigt) | `documents.jsonl`, `corpus_manifest.csv`, Token-Zahl im Experiment-Protokoll |
| 20.10.–02.11. | Pipeline | Chunking C1–C3 und K1, Embedding, Chroma, Retrieval; Embedding-Modell, SDK und Chroma gepinnt (erledigt 13.–14.10.); offen: Generierung, GPT-Modell pinnen, Prototyp mit einer Frage | lauffähige Pipeline, Modellversionen dokumentiert |
| 20.10.–08.11. | Fragenkatalog (parallel) | 40 Fragen, Referenzantworten, `relevant_section_ids` (blind annotiert, [ADR 0027](adr/0027-blinde-annotation.md)); Vortest von Prompt und Rubrik: 5 Pilotfragen (nicht aus dem Katalog) über die ganze Kette inkl. Generierung und Bewertung, sobald der Prototyp steht; ergänzt die Retrieval-Pilotproben mit 8 und 16 Fragen vom 14.10. ([Experiment-Protokoll](reference/experiment-record.md)) und hält den Katalog unberührt ([ADR 0027](adr/0027-blinde-annotation.md)) | `questions.csv`, `ground_truth.csv` |
| 03.–09.11. | Auswertungsskripte | Relevanz per Token-Überlappung (erledigt in `retrieve.py`/`relevance.py`); Recall/Precision/MRR/Hit@5, RAGAS, Kostenerfassung, Kontext-Tokens je Antwort | `evaluate_retrieval.py`, `evaluate_answers.py` getestet |
| **09.11.** | **Meilenstein** | **Ground Truth eingefroren** ([ADR 0017](adr/0017-fragenkatalog.md)) | Commit-Hash im Experiment-Protokoll |
| 10.–16.11. | Experimente | volle Läufe C1–C3, Kontrolle K1 (nur Retrieval), Sensitivitätsprüfung ([ADR 0026](adr/0026-c3-vergleichbarkeit.md)) | `retrieved_results.csv`, `retrieved_results_control.csv` (K1), `generated_answers.csv` |
| 17.–25.11. | Bewertung und Analyse | manuelle Rubrik (120 Antworten), RAGAS-Abgleich, Statistik, Abbildungen | `scores.csv`, `output/tables/`, `output/figures/` |
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

- **Modell-/Versionswahl:** konkretes GPT-Modell und SDK-/API-Version zum Implementierungszeitpunkt fixieren und dokumentieren. Entschieden: Embedding-Modell sowie SDK- und Chroma-Version ([ADR 0023](adr/0023-embedding-modell.md)); offen: GPT-Modell.
- **Embedding-Sprache:** Korpus ist englisch; Fragen/Referenzantworten englisch halten (Konsistenz mit Embedding-Raum).
- **Zweitbewertung:** Verfügbarkeit einer zweiten bewertenden Person klären (stärkt Konstruktvalidität).
- **Fragenkatalog-Werkzeuge (vereinbart 14.10.2026):** Abschnitts-Nachschlageliste und Abdeckungsprüfung (Fragetypen, Bereiche inkl. API, zu leichte Fragen) als nächster Schritt; Werte für `type` und `difficulty` noch festzulegen.
- **C4 (semantisch):** entschieden: nur, wenn der Meilenstein 09.11. (Ground Truth eingefroren) planmäßig erreicht ist
  ([ADR 0028](adr/0028-c4-bedingung.md)).
