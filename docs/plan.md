# Plan und offene Entscheidungen

*[Doku-Index](README.md) · Planung · Verwandt: [Experiment durchführen](how-to/run-the-experiment.md), [Fragenkatalog erstellen](how-to/build-the-question-catalogue.md), [ADRs](adr/README.md)*

## Stand

Stand 26.10.2026. **Erledigt:** Korpus e2e, Pipeline mit K1 und K0, Auswertung (`src/analyse.py`), RAGAS-Lauf und
Zweitbewertung sind umgesetzt und getestet; Pilot e2e und Probelauf des Hauptlaufs sind bestanden
([Experiment-Protokoll](reference/experiment-record.md)); Doku-Audits vom 22.10. (PR #41–#43) und 26.10. (PR #44–#46); Korpus-Snapshot
und Chunk-Vektoren versioniert, damit sich Retrieval und Auswertung ohne API nachrechnen lassen
([ADR 0048](adr/0048-korpus-und-chunk-vektoren-versioniert.md)).
**Nächster Schritt:** Fragenkatalog, drei Blöcke je Woche ab 23.10. ([Backlog](#backlog) Punkt 1). **Größtes Risiko:**
Der Hauptkatalog hat 0 von 48 Fragen; Einfrieren geplant am 06.11., spätestens 09.11. ([Zeitplan](#zeitplan)).

## Zeitplan

Neu geplant am 13.10.2026: Pipeline und Fragenkatalog zuerst, dann Experimente, dann Schreiben. Abgabe 24.12.2026
([ADR 0004](adr/0004-zeitraum-und-abgabe.md)). Einzelheiten zu erledigten Phasen: [Verlauf](#verlauf).

| Zeitraum | Phase | Schwerpunkte | Ergebnis | Status |
|----------|-------|--------------|----------|--------|
| 13.–19.10. | Korpus | Snapshot, `ingest.py`, `preprocess.py`, Korpusmanifest; Wechsel zu e2e ([ADR 0038](adr/0038-korpus-e2e.md)) | `documents.jsonl`, `corpus_manifest.csv`, Token-Zahl im Experiment-Protokoll | erledigt 18.10. |
| 20.10.–02.11. | Pipeline | Chunking C1–C3 und K1, Embedding, Chroma, Retrieval, Generierung, Kontrolle K0 ([ADR 0041](adr/0041-kontrolle-k0.md)); Pilot auf e2e als Vortest von Prompt und Rubrik | lauffähige Pipeline, Modellversionen dokumentiert | erledigt 20.10. |
| 23.10.–06.11. | Fragenkatalog | 48 Fragen in sechs Blöcken zu 8, drei Blöcke je Woche ab 23.10., nach jedem Block KI-Durchsicht ([ADR 0031](adr/0031-stichprobenplan-und-ki-durchsicht.md)) und Closed-Book-Prüfung ([ADR 0040](adr/0040-closed-book-pruefung.md)); Referenzantworten, `relevant_section_ids` (blind, [ADR 0027](adr/0027-blinde-annotation.md)); Ablauf: [Fragenkatalog erstellen](how-to/build-the-question-catalogue.md) | `questions.csv`, `ground_truth.csv`, `closed_book_screen.csv` | offen (0/48) |
| 03.–09.11. | Auswertungsskripte | Statistik, Tabellen und Abbildungen ([ADR 0044](adr/0044-statistische-auswertung.md)), RAGAS-Lauf ([ADR 0047](adr/0047-ragas-als-triangulation.md)), Zweitbewertung und Übereinstimmung ([ADR 0046](adr/0046-zweitbewertung.md)) | `analyse.py`, `ragas_eval.py`, `second_rater.py` getestet | erledigt 22.10. |
| **09.11.** | **Meilenstein** | **Ground Truth eingefroren** ([ADR 0017](adr/0017-fragenkatalog.md)): geplant am 06.11., spätestens 09.11.; am selben Tag fällt die C4-Entscheidung ([ADR 0028](adr/0028-c4-bedingung.md#nachtrag-22102026-c4-nur-deskriptiv)) | Commit-Hash im Experiment-Protokoll | offen |
| 10.–16.11. | Experimente | direkt nach dem Einfrieren und vor jeder eigenen Bewertung die Ziehung der Zweitbewertung ([ADR 0046](adr/0046-zweitbewertung.md)); volle Läufe C1–C3, Kontrolle K1 (nur Retrieval), Sensitivitätsprüfung ([ADR 0026](adr/0026-c3-vergleichbarkeit.md)), Kontrolle K0 (im selben Generierungslauf); Ergebnisse nach jedem Schritt committen ([ADR 0045](adr/0045-retrieval-ergebnisse-versioniert.md)) | `retrieved_results.csv`, `retrieved_results_control.csv` (K1), `generated_answers.csv`, `generated_answers_control.csv` (K0) | offen |
| 17.–25.11. | Bewertung und Analyse | regelbasierte Rubrik-Bewertung (144 Antworten: 48 Fragen × C1–C3), danach 48 Antworten K0; Zweitbewertung von 36 Antworten; RAGAS nach `summarise`; Statistik, Tabellen, Abbildungen ([Experiment durchführen](how-to/run-the-experiment.md)) | `scores.csv`, `scores_control.csv`, `ragas_scores.csv`, `output/tables/` (mit `agreement.tex`), `output/figures/` | offen |
| 26.11.–13.12. | Schreibphase | Methodik, Implementierung, Ergebnisse, Diskussion, Fazit | Rohfassung komplett | offen |
| 14.–20.12. | Überarbeitung | Sprache, Argumentation, roter Faden, `./paperlab check` | Endfassung | offen |
| 21.–23.12. | Puffer | Korrektorat, Formatierung, Zitation, `./paperlab final` | Abgabe-PDF | offen |
| 24.12. | Abgabe | Einreichung | | offen |

> **Risiko Schreibphase:** Für das Schreiben bleiben knapp drei Wochen. Kapitel ohne Ergebnisabhängigkeit
> (Einleitung, Grundlagen, Methodik) ab Anfang November parallel zum Fragenkatalog entwerfen.

> **Risiko Fragenkatalog:** Er wird regelmäßig unterschätzt. Am 22.10. lag noch kein Block vor; für das Einfrieren am
> 06.11. sind drei Blöcke je Woche nötig.

> **Puffer-Regel:** Rutscht der Meilenstein 09.11., entfallen zuerst C4 ([ADR 0028](adr/0028-c4-bedingung.md#nachtrag-22102026-c4-nur-deskriptiv))
> und RAGAS-Feinheiten, nicht die Schreibphase; der RAGAS-Lauf selbst ist fest ([ADR 0047](adr/0047-ragas-als-triangulation.md)).

Der ursprüngliche Phasenplan (Juni 2026, Abgabe 15.12.) steht in der Git-Historie.

## Backlog

Offene Arbeit nach Priorität; erledigte Punkte wandern in den [Verlauf](#verlauf).

1. **Fragenkatalog** (kritischer Pfad). Wer: Jonas. Frist: Einfrieren 06.11., spätestens 09.11. Fertig, wenn 48
   Fragen mit Referenzantworten und Relevanz eingefroren sind und der Freeze-Datensatz committet ist
   ([Fragenkatalog erstellen](how-to/build-the-question-catalogue.md)).
2. **Übungsbewertung Pilot.** Wer: Jonas. Frist: vor der Bewertung des Hauptlaufs (17.11.). Fertig, wenn die 9
   Antworten in `data/pilot/e2e_jonas/` bewertet sind und der Vergleich mit der Agentenbewertung im
   [Experiment-Protokoll](reference/experiment-record.md#pilot-e2e-1920102026) steht.
3. **Zweite bewertende Person finden** ([ADR 0046](adr/0046-zweitbewertung.md)). Wer: Jonas. Frist: Mitte November.
   Fertig, wenn eine Person mündlich zugestimmt hat (Vermerk außerhalb des Repos, in Dateien nur das Pseudonym `R2`);
   sonst gilt das Ersatzverfahren (Punkt 4).
4. **Ersatzverfahren der Zweitbewertung** ([ADR 0046](adr/0046-zweitbewertung.md)). Wer: Jonas entscheidet, ob es
   gebraucht wird; Claude setzt die Intra-Rater-Wiederholung und die LLM-Gegenprobe um. Frist: Mitte November. Fertig,
   wenn feststeht, ob es gebraucht wird, und es im Bedarfsfall umgesetzt und getestet ist.
5. **Probe-Bewertung R2 auf dem Pilot** (optional). Wer: Jonas. Frist: vor der Ziehung im Hauptlauf. Fertig, wenn der
   R2-Satz in `data/pilot/e2e/` bewertet und mit `second_rater.py --mode close` abgeschlossen ist
   ([Experiment durchführen](how-to/run-the-experiment.md#zweitbewertung)).
6. **Hauptlauf dokumentieren.** Wer: Claude. Frist: beim Hauptlauf (10.–16.11.). Fertig, wenn Python-Version und
   `system_fingerprint` im [Experiment-Protokoll](reference/experiment-record.md) stehen
   ([ADR 0033](adr/0033-antwortmodell.md)).
7. **Lizenzen der Korpusproben.** Wer: Claude prüft, Jonas entscheidet. Frist: vor der DOI-Veröffentlichung. Fertig,
   wenn jedes Zitat aus `data/corpus_probe/` eine Lizenz hat, die die Weitergabe erlaubt, oder entfernt ist
   (Lizenzspalte in der [Korpusauswahl](reference/corpus-selection.md)).
8. **Volltext Pesl et al. (2026) lesen.** Wer: Jonas. Frist: vor dem Methodik- und Verwandte-Arbeiten-Kapitel (Anfang
   November). Fertig, wenn feststeht, ob die Studie auch die Antwortqualität misst, und
   [Forschungsdesign](explanation/research-design.md#verwandte-arbeiten) und
   [Literaturbasis](reference/literature.md) das nennen.
9. **Ergebnisse-Seite in der App.** Wer: Claude. Frist: nach dem Hauptlauf, nur falls Zeit bleibt. Fertig, wenn eine
   eigene Spezifikation (Brainstorming) vorliegt und umgesetzt ist; ersetzt das frühere Demo-Dashboard. Die Auswertung
   für die Arbeit bleibt `src/analyse.py`.
10. **Thesis-Aufgaben** (Anhang B verweisen usw.): PaperLab `docs/HANDOFF.md`.
11. **Beispiele im Fragenkatalog.** Wer: Jonas. Frist: nach Block 1. Fertig, wenn die Tabelle der Fragetypen in
    [Fragenkatalog](reference/question-catalogue.md) je Typ eine echte e2e-Frage statt des Platzhalters zeigt.

## Offene Entscheidungen

- **Zweitannotation der Relevanz** (`relevant_section_ids`): Vorschlag 10–12 Fragen, blind; ob und in welchem Umfang, nach dem Einfrieren entscheiden,
  falls Zeit bleibt ([ADR 0046](adr/0046-zweitbewertung.md)).
- **C4 (semantisch):** läuft nur, wenn der Meilenstein 09.11. planmäßig erreicht ist; Entscheidung am 09.11.
  ([ADR 0028](adr/0028-c4-bedingung.md#nachtrag-22102026-c4-nur-deskriptiv)).

Entschiedenes mit Begründung: [ADRs](adr/README.md).

## Verlauf

- 13.10.2026: Codex-Review-Stellvertreter, Lizenzhinweise; Snapshot bis Retrieval auf Vue.js umgesetzt und getestet
  (PR #1–#5).
- 14.10.2026: Korpus Vue.js auf Guide, API-Referenz und Style Guide erweitert
  ([ADR 0025](adr/0025-korpus-guide-api-styleguide.md), später ersetzt durch [ADR 0038](adr/0038-korpus-e2e.md));
  Kontrolle K1 ([ADR 0026](adr/0026-c3-vergleichbarkeit.md)); Katalogwerkzeuge und Einfrieren
  ([ADR 0029](adr/0029-fragetypen-und-konstruktionsklassen.md), [ADR 0030](adr/0030-einfrieren-des-fragenkatalogs.md))
  (PR #6–#8).
- 15.10.2026: Stichprobenplan (Vue.js, inzwischen archiviert), Editor und protokollierte KI-Durchsicht
  ([ADR 0031](adr/0031-stichprobenplan-und-ki-durchsicht.md)) (PR #9–#11).
- 16.10.2026: `evaluate_retrieval.py` und `evaluate_answers.py` (blinde Bewertung,
  [ADR 0032](adr/0032-blinde-rubrik-bewertung.md)); Editor auf iOS Safari (PR #12, #13).
- 17.10.2026: Antwortmodell `gpt-6-luna` ([ADR 0033](adr/0033-antwortmodell.md)), `generate.py`; Bewertung in der App,
  regelbasiert ([ADR 0034](adr/0034-bewertung-in-der-app.md)–[0036](adr/0036-regelbasierte-bewertung-verpflichtend.md))
  (PR #14–#19).
- 18.10.2026: Pilot `data/pilot/hard` (Vue.js) von einem Agenten als Entwicklungshilfe bewertet (zählt nicht); daraus
  präzisierte Prüfregeln ([ADR 0037](adr/0037-praezisierte-pruefregeln-und-vorbefuellte-kernpunkte.md)). Das
  Antwortmodell kennt Vue.js ([Korpusauswahl](reference/corpus-selection.md)): Korpuswechsel zu e2e beschlossen
  ([ADR 0038](adr/0038-korpus-e2e.md)); Snapshot, Preprocessing, Chunks und Embeddings auf e2e (PR #20–#23).
- 19.10.2026: Stichprobenplan auf e2e, Closed-Book-Prüfung, Kontrolle K0
  ([ADR 0039](adr/0039-stichprobenplan-e2e.md)–[0041](adr/0041-kontrolle-k0.md)); die Regeln der MDX-Umwandlung
  nachträglich festgehalten ([ADR 0042](adr/0042-mdx-umwandlung.md)); Doku-Audit nach dem Korpuswechsel (PR #24–#27).
- 20.10.2026: Pilot `data/pilot/e2e` (16 Fragen außerhalb des Stichprobenplans, ganze Pipeline mit K0;
  [Experiment-Protokoll](reference/experiment-record.md#pilot-e2e-1920102026)); Regel zu `direct` und Teilantworten
  präzisiert ([ADR 0043](adr/0043-praezisierung-direct-und-teilantworten.md)); Auswertungsskripte (`analyse.py`):
  Testplan, Tabellen und Abbildungen ([ADR 0044](adr/0044-statistische-auswertung.md)) (PR #28–#30).
- 21.10.2026: Backlog angelegt; Ground-Truth-Prüfung weist doppelte `relevant_doc_ids` ab
  ([Datenformate](reference/data-formats.md)); Tabellen nach IU-Regeln; Probelauf des Hauptlaufs
  ([Experiment-Protokoll](reference/experiment-record.md#probelauf-hauptlauf-21102026)); Retrieval-Ergebnisse
  versioniert ([ADR 0045](adr/0045-retrieval-ergebnisse-versioniert.md)); Zweitbewertung
  ([ADR 0046](adr/0046-zweitbewertung.md)) und RAGAS als feste Triangulation
  ([ADR 0047](adr/0047-ragas-als-triangulation.md)) entschieden; RAGAS-Lauf (`src/ragas_eval.py`) umgesetzt und auf
  dem Pilot e2e erprobt, zwei Läufe, 4,05 USD
  ([Experiment-Protokoll](reference/experiment-record.md#ragas-pilot-e2e-21102026)) (PR #31–#37).
- 22.10.2026: Kapitel 4 gestrafft, Tests und RAGAS-Effekte als Anhangstabellen (PR #38); Nachträge aus dem
  Methodik-Faktenblatt zu ADR 0009, 0013, 0035 und 0046 (PR #39); Zweitbewertung umgesetzt (Ziehung, R2-Modus der App,
  Abschluss, Übereinstimmung als Anhangstabelle; Nachtrag zum Maß der geordneten Prüffragen in ADR 0046) mit
  Nachtrag zu ADR 0033 (PR #40). Doku-Audit; Entscheidungen von Jonas: die Tests von R@5, MRR und Gesamtwert sind
  konfirmatorisch, alle übrigen p-Werte explorativ ([ADR 0044](adr/0044-statistische-auswertung.md#nachtrag-22102026-konfirmatorische-tests)); C4 nur beschreibend ([ADR 0028](adr/0028-c4-bedingung.md#nachtrag-22102026-c4-nur-deskriptiv)); Forschungslücke Säule 2 auf
  Prosa-Entwicklerdokumentation eingegrenzt, Pesl et al. (2026) als nächste verwandte Arbeit ([ADR 0011](adr/0011-forschungsluecke.md#nachtrag-22102026-zweite-säule-eingeengt)); Ziehung und Bootstrap der
  Zweitbewertung und Mischung der Bewertung mit `random`/NumPy akzeptiert, weil die gespeicherten Artefakte gelten ([ADR 0046](adr/0046-zweitbewertung.md#nachtrag-22102026-zufallszahlen)); Notebook-Gerüst und `plotly` entfallen;
  Lizenzspalte für die Korpusproben; Vue-Archiv `embedding_runs.jsonl` und die Hauptlauf-Ausgaben
  `analysis.json` und `second_rater_disagreements.csv` werden versioniert; eigene Bewertung erst nach dem
  Abschluss der Zweitbewertung pushen; Fragenkatalog mit drei Blöcken je Woche ab 23.10., Einfrieren 06.11.;
  Code-Befunde in einem eigenen PR (am 23.10.); Doku-Audit (PR #41).
- 23.10.2026: Code-Befunde des Audits (PR #42): Schlüssel von K1 und K0 nur aus `config`, Ausgabeordner der Pilot-Sets
  aus `config`, `difficulty_probe.py` verlangt das Set, RAGAS-Block als eigener Abschnitt in `config.py`, Testtabelle
  „konfirmatorisch“, Notebook-Gerüst und `plotly` entfernt, Regelversion im Einfrier-Eintrag
  ([ADR 0035](adr/0035-regelbasierte-bewertung.md)), `catalogue.py check` meldet H1-Abschnitte ohne Begründung
  ([ADR 0022](adr/0022-h1-abschnitte-in-ground-truth.md)); `jupyter` und `ipykernel` entfernt (PR #43).
- 26.10.2026: Doku-Audit; Entscheidungen von Jonas: Korpus-Snapshot und Chunk-Vektoren versioniert, damit
  Begutachtende und ein zweiter Rechner Retrieval und Auswertung ohne API nachrechnen
  ([ADR 0048](adr/0048-korpus-und-chunk-vektoren-versioniert.md), PR #45); der Hauptlauf läuft auf dem Branch
  `run/hauptlauf`; Taiwo (2026) belegt die Forschungslücke nicht mehr
  ([ADR 0011](adr/0011-forschungsluecke.md#nachtrag-26102026-taiwo-kein-beleg-der-lücke)); Pesl et al. (2026)
  vorläufig bis zur Volltextprüfung; Nachträge zur NaN-Regel von RAGAS
  ([ADR 0047](adr/0047-ragas-als-triangulation.md#nachtrag-26102026-fehlende-werte)) und zur Holm-Familie
  ([ADR 0044](adr/0044-statistische-auswertung.md#nachtrag-26102026-holm-über-die-testbaren-metriken));
  toter Code und Platzhalter-App entfernt (PR #44); Doku-Audit (PR #46).
