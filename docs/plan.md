# Plan und offene Entscheidungen

> Projektstand, kein Diátaxis-Typ. Übersicht: [Dokumentation](README.md).

## Zeitplan (13.10.–24.12.2026)

Neu geplant am 13.10.2026: Pipeline und Fragenkatalog zuerst, dann Experimente, dann Schreiben. Abgabe 24.12.2026
([ADR 0004](adr/0004-zeitraum-und-abgabe.md)); Korpus: [ADR 0025](adr/0025-korpus-guide-api-styleguide.md) (Guide, API-Referenz, Style Guide; Stand 14.10.2026), Vergleichbarkeit von C3: [ADR 0026](adr/0026-c3-vergleichbarkeit.md).

| Zeitraum | Phase | Schwerpunkte | Ergebnis |
|----------|-------|--------------|----------|
| 13.–19.10. | Korpus | Snapshot, `ingest.py`, `preprocess.py` (test-first), Korpusmanifest; am 14.10. auf Guide + API + Style Guide erweitert (erledigt) | `documents.jsonl`, `corpus_manifest.csv`, Token-Zahl im Experiment-Protokoll |
| 20.10.–02.11. | Pipeline | Chunking C1–C3, Embedding, Chroma, Retrieval, Generierung; Modelle und SDK pinnen; Prototyp mit einer Frage | lauffähige Pipeline, Modellversionen dokumentiert |
| 20.10.–08.11. | Fragenkatalog (parallel) | 40 Fragen, Referenzantworten, `relevant_section_ids`; Pilot mit 5 Fragen gegen den Prototyp | `questions.csv`, `ground_truth.csv` |
| 03.–09.11. | Auswertungsskripte | Relevanz per Token-Überlappung, Recall/Precision/MRR/Hit@5, RAGAS, Kostenerfassung, Kontext-Tokens je Antwort | `evaluate_retrieval.py`, `evaluate_answers.py` getestet |
| **09.11.** | **Meilenstein** | **Ground Truth eingefroren** ([ADR 0017](adr/0017-fragenkatalog.md)) | Commit-Hash im Experiment-Protokoll |
| 10.–16.11. | Experimente | volle Läufe C1–C3, Kontrolle K1 (nur Retrieval), Sensitivitätsprüfung (≥ min(100, Chunk-Länge) Tokens Überlappung) | `retrieved_results.csv`, `generated_answers.csv` |
| 17.–25.11. | Bewertung und Analyse | manuelle Rubrik (120 Antworten), RAGAS-Abgleich, Statistik, Abbildungen | `scores.csv`, `output/tables/`, `output/figures/` |
| 26.11.–13.12. | Schreibphase | Methodik, Implementierung, Ergebnisse, Diskussion, Fazit (Grundlagen siehe Hinweis) | Rohfassung komplett |
| 14.–20.12. | Überarbeitung | Sprache, Argumentation, roter Faden, `./paperlab check` | Endfassung |
| 21.–23.12. | Puffer | Korrektorat, Formatierung, Zitation, `./paperlab final` | Abgabe-PDF |
| 24.12. | Abgabe | Einreichung | |

> **Risiko Schreibphase:** Für das Schreiben bleiben knapp drei Wochen. Kapitel ohne Ergebnisabhängigkeit
> (Einleitung, Grundlagen, Methodik) ab Anfang November parallel zur Pipeline entwerfen.

> Der Fragenkatalog wird regelmäßig unterschätzt — bewusst Zeit einplanen.

> **Puffer-Regel:** Rutscht der Meilenstein 09.11., zuerst C4 und RAGAS-Feinheiten streichen, nicht die Schreibphase.

Der ursprüngliche Phasenplan (Juni 2026, Abgabe 15.12.) steht in der Git-Historie.


## Offene Entscheidungen / vor Beginn zu bestätigen

- **Exposé-Umfang:** Aktuelle Fassung ist näher an „Betreuungsanfrage" (2–3 Seiten). Die IU-Formvorgabe nennt 5 Seiten ±10 %. Falls das Exposé als reguläre IU-Abgabe zählt, Theorie und Methodik entsprechend ausbauen (jeder Unterabschnitt ≥ ½ Seite).
- **Modell-/Versionswahl:** konkretes GPT-Modell und SDK-/API-Version zum Implementierungszeitpunkt fixieren und dokumentieren. Entschieden: Embedding-Modell sowie SDK- und Chroma-Version ([ADR 0023](adr/0023-embedding-modell.md)); offen: GPT-Modell.
- **Embedding-Sprache:** Korpus ist englisch; Fragen/Referenzantworten englisch halten (Konsistenz mit Embedding-Raum).
- **Zweitbewertung:** Verfügbarkeit einer zweiten bewertenden Person klären (stärkt Konstruktvalidität).
- **Fragenkatalog-Werkzeuge (vereinbart 14.10.2026):** Abschnitts-Nachschlageliste und Abdeckungsprüfung (Fragetypen, Bereiche inkl. API, zu leichte Fragen) als nächster Schritt; Werte für `type` und `difficulty` noch festzulegen.
- **C4 (semantisch):** nur einplanen, wenn der Meilenstein 09.11. (Ground Truth eingefroren) planmäßig erreicht ist.
