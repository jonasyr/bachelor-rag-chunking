# Plan und offene Entscheidungen

> Projektstand, kein Diátaxis-Typ. Übersicht: [Dokumentation](README.md).

## Zeitplan (Juli–Dezember 2026)

| Zeitraum | Phase | Schwerpunkte |
|----------|-------|--------------|
| 01.–14.07. | Vorbereitung | Thema/Scope final, Arbeitsumgebung, Repository |
| 06.–27.07. | Literaturrecherche | Theoriebasis RAG/Chunking/Evaluation |
| 20.–31.07. | Forschungsfrage schärfen | Hypothesen, Abstimmung Betreuung |
| 01.–14.08. | Methodik vorbereiten | Design, Pipeline-Architektur, Evaluationsschema, Rubrik |
| 11.–24.08. | Snapshot/Korpus | Vue-Snapshot, Bereinigung, Korpusmanifest |
| 24.08.–07.09. | Datenerhebung | Fragenkatalog, Referenzantworten, Annotation |
| 07.–28.09. | Implementierung | Preprocessing, Chunking, Embedding, Retrieval, Generierung |
| 28.09.–12.10. | Datenauswertung | Experimente, Retrieval-Metriken, Antwortbewertung |
| 12.–26.10. | Analyse/Visualisierung | deskriptiv, Korrelation, Abbildungen |
| 26.10.–23.11. | Schreibphase | Theorie, Methodik, Implementierung, Ergebnisse, Diskussion |
| 23.11.–07.12. | Überarbeitung | Sprache, Argumentation, roter Faden |
| 07.–14.12. | Korrektur/Puffer | Korrektorat, Formatierung, Zitation, Reserve |
| 15.12. | Abgabe | Finalisierung und Einreichung |

> Der Fragenkatalog (Phase Datenerhebung) wird regelmäßig unterschätzt — bewusst Zeit einplanen.

> **Planungsstand Juni 2026.** Abgabe ist der 24.12.2026 (ADR 0004). Stand 13.10.2026: Pipeline in `src/` noch als Gerüst (`NotImplementedError`), Korpus-Ausschnitt offen (unten). Der Plan ist entsprechend zu verschieben.


## Offene Entscheidungen / vor Beginn zu bestätigen

- **Exposé-Umfang:** Aktuelle Fassung ist näher an „Betreuungsanfrage" (2–3 Seiten). Die IU-Formvorgabe nennt 5 Seiten ±10 %. Falls das Exposé als reguläre IU-Abgabe zählt, Theorie und Methodik entsprechend ausbauen (jeder Unterabschnitt ≥ ½ Seite).
- **Exakter Vue-Korpus-Ausschnitt (offen, Stand 13.10.2026):** Vorschlag aus einem Plan vom 13.08.2026 (`docs/superpowers/plans/2026-08-13-corpus-snapshot.md`, liegt vermutlich auf dem PC und ist noch nicht im Repo): ganzes `src/guide/` aus `vuejs/docs` auf Commit `b75d188ab16bf83bd1f364a77dfd2315be8f3fa4` (52 Dateien, ca. 106k Tokens), nur Composition-API-Inhalte (`options-api`-Blöcke entfernt), `section_id` = `{doc_id}#{anchor}` aus expliziten `{#…}`-Ankern, relevant = jede Überlappung von Token-Spannen (Sensitivitätsprüfung ab 100 Tokens), Token-Kodierung `cl100k_base` (tiktoken 0.13.0). Abweichung von §5.2 (vier Unterordner, 50–100 Dateien). Nach Bestätigung als ADR festhalten und §5 anpassen.
- **Modell-/Versionswahl:** konkretes GPT-Modell, Embedding-Modell (`-large` vs. `-small`), SDK-/API-Version zum Implementierungszeitpunkt fixieren und dokumentieren.
- **Embedding-Sprache:** Korpus ist englisch; Fragen/Referenzantworten englisch halten (Konsistenz mit Embedding-Raum).
- **Zweitbewertung:** Verfügbarkeit einer zweiten bewertenden Person klären (stärkt Konstruktvalidität).
- **C4 (semantisch):** nur einplanen, wenn Phasen 1–4 planmäßig laufen.
