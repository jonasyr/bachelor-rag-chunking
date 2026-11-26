# Plan und offene Entscheidungen

*[Doku-Index](README.md) · Planung · Verwandt: [Experiment durchführen](how-to/run-the-experiment.md), [Fragenkatalog erstellen](how-to/build-the-question-catalogue.md), [ADRs](adr/README.md)*

## Stand

Stand 26.11.2026. **Erledigt:** Korpus e2e, Pipeline mit K1 und K0, Auswertung (`src/analyse.py`), RAGAS-Lauf und
Zweitbewertung sind umgesetzt und getestet; Pilot e2e, Probelauf und Generalprobe des Hauptlaufs sind bestanden
([Experiment-Protokoll](reference/experiment-record.md)); Generierung und RAGAS setzen nach einem Abbruch fort
([ADR 0050](adr/0050-journal-und-fortsetzen-der-api-schritte.md)); Doku-Audits vom 22.10. (PR #41–#43) und 26.10. (PR #44–#46); Korpus-Snapshot
und Chunk-Vektoren versioniert, damit sich Retrieval und Auswertung ohne API nachrechnen lassen
([ADR 0048](adr/0048-korpus-und-chunk-vektoren-versioniert.md)).
**Hauptlauf** (Branch `run/hauptlauf`): Schritte 0–5 erledigt (Ziehung der Zweitbewertung, Retrieval, Antworten, Retrieval-Metriken, Bewertungsbogen; Kernpunkte am 26.11. eingefroren). Die Bewertung ist hybrid ([ADR 0051](adr/0051-hybride-bewertung.md)): Jonas bewertet 24 Fragen, das Sprachmodell alle Antworten, die Wiederholung entfällt. **Nächster Schritt:** Ziehung der 12 Zusatzfragen (`src/hybrid.py --mode draw`), dann Jonas' 72 Antworten; parallel K0 im Sprachmodell-Bewerter und das Zusammenführen ([Backlog](#backlog), Punkt 3). **Größtes Risiko:** Die Schreibphase beginnt nach der Bewertung; Zusammenführen und Analyse müssen bis Anfang Dezember stehen. Der
Hauptkatalog ist am 16.11. eingefroren, 48 von 48 Fragen (Block 1 am 09.11., Block 2 bis 4 am 11.11., Block 5 am 12.11., Block 6 am 16.11.; Sprünge `content-elsewhere` in S15 und S37), alle Typquoten erfüllt; Closed-Book 35 retrieval-abhängig nach der Gesamtdurchsicht (Runde 9, 16.11.; mindestens 32, [ADR 0040](adr/0040-closed-book-pruefung.md)) ([Typverteilung](#zeitplan)); das Einfrieren ist am 06.11. auf den 13.11. und am 16.11. vom 13.11. auf den 16.11. verschoben, C4 entfällt
([Zeitplan](#zeitplan)).

## Zeitplan

Neu geplant am 13.10.2026: Pipeline und Fragenkatalog zuerst, dann Experimente, dann Schreiben. Abgabe 24.12.2026
([ADR 0004](adr/0004-zeitraum-und-abgabe.md)). Einzelheiten zu erledigten Phasen: [Verlauf](#verlauf).

| Zeitraum | Phase | Schwerpunkte | Ergebnis | Status |
|----------|-------|--------------|----------|--------|
| 13.–19.10. | Korpus | Snapshot, `ingest.py`, `preprocess.py`, Korpusmanifest; Wechsel zu e2e ([ADR 0038](adr/0038-korpus-e2e.md)) | `documents.jsonl`, `corpus_manifest.csv`, Token-Zahl im Experiment-Protokoll | erledigt 18.10. |
| 20.10.–02.11. | Pipeline | Chunking C1–C3 und K1, Embedding, Chroma, Retrieval, Generierung, Kontrolle K0 ([ADR 0041](adr/0041-kontrolle-k0.md)); Pilot auf e2e als Vortest von Prompt und Rubrik | lauffähige Pipeline, Modellversionen dokumentiert | erledigt 20.10. |
| 23.10.–16.11. | Fragenkatalog | 48 Fragen in sechs Blöcken zu 8, ab 06.11. ein Block je Tag, nach jedem Block KI-Durchsicht ([ADR 0031](adr/0031-stichprobenplan-und-ki-durchsicht.md)) und Closed-Book-Prüfung ([ADR 0040](adr/0040-closed-book-pruefung.md)); Referenzantworten, `relevant_section_ids` (blind, [ADR 0027](adr/0027-blinde-annotation.md)); Ablauf: [Fragenkatalog erstellen](how-to/build-the-question-catalogue.md) | `questions.csv`, `ground_truth.csv`, `closed_book_screen.csv` | erledigt 16.11. (48/48) |
| 03.–09.11. | Auswertungsskripte | Statistik, Tabellen und Abbildungen ([ADR 0044](adr/0044-statistische-auswertung.md)), RAGAS-Lauf ([ADR 0047](adr/0047-ragas-als-triangulation.md)), Zweitbewertung und Übereinstimmung ([ADR 0046](adr/0046-zweitbewertung.md)) | `analyse.py`, `ragas_eval.py`, `second_rater.py` getestet | erledigt 22.10. |
| **16.11.** | **Meilenstein** | **Ground Truth eingefroren** ([ADR 0017](adr/0017-fragenkatalog.md)): am 06.11. vom 09.11. auf den 13.11., am 16.11. vom 13.11. auf den 16.11. verschoben; C4 entfällt damit ([ADR 0028](adr/0028-c4-bedingung.md#nachtrag-06112026-c4-entfällt)) | Commit-Hash im Experiment-Protokoll ([Fragenkatalog](reference/experiment-record.md#fragenkatalog-eingefroren-16112026)) | erledigt 16.11. |
| 17.–18.11. | Experimente | direkt nach dem Einfrieren und vor jeder eigenen Bewertung die Ziehung der Zweitbewertung ([ADR 0046](adr/0046-zweitbewertung.md)); volle Läufe C1–C3, Kontrolle K1 (nur Retrieval), Sensitivitätsprüfung ([ADR 0026](adr/0026-c3-vergleichbarkeit.md)), Kontrolle K0 (im selben Generierungslauf); Ergebnisse nach jedem Schritt committen ([ADR 0045](adr/0045-retrieval-ergebnisse-versioniert.md)) | `retrieved_results.csv`, `retrieved_results_control.csv` (K1), `generated_answers.csv`, `generated_answers_control.csv` (K0) | erledigt 17.11. |
| 19.11.–Anfang 12. | Bewertung und Analyse | Kernpunkte eingefroren 26.11.; hybride Bewertung ([ADR 0051](adr/0051-hybride-bewertung.md)): Jonas 72 Antworten (24 Fragen × C1–C3), das Sprachmodell alle 144 und K0; Übereinstimmung auf 72 Antworten; RAGAS nach `summarise`; Statistik, Tabellen, Abbildungen ([Experiment durchführen](how-to/run-the-experiment.md)) | `scores.csv`, `scores_control.csv`, `ragas_scores.csv`, `output/tables/` (mit `agreement_llm.tex`), `output/figures/` | läuft |
| 26.11.–13.12. | Schreibphase | Methodik, Implementierung, Ergebnisse, Diskussion, Fazit | Rohfassung komplett | offen |
| 14.–20.12. | Überarbeitung | Sprache, Argumentation, roter Faden, `./paperlab check` | Endfassung | offen |
| 21.–23.12. | Puffer | Korrektorat, Formatierung, Zitation, `./paperlab final` | Abgabe-PDF | offen |
| 24.12. | Abgabe | Einreichung | | offen |

> **Risiko Schreibphase:** Für das Schreiben bleiben knapp drei Wochen. Kapitel ohne Ergebnisabhängigkeit
> (Einleitung, Grundlagen, Methodik) ab Anfang November parallel zum Fragenkatalog entwerfen.

> **Risiko Fragenkatalog (erledigt 16.11.):** Am 06.11. lag eine Frage vor; das Einfrieren rutschte vom 13.11. auf
> den 16.11., weil Block 6 noch fehlte. Eingefroren mit 48 Fragen, ohne Kürzung.

> **Typverteilung Restkatalog** (11.11.2026, nach 16 Fragen: 8 `factual`, 4 `procedural`, 2 `conceptual`,
> 1 `comparative`, 1 `limitation`): Es fehlen 10 `conceptual`, 5 `comparative`, 5 `limitation`, 8 `procedural` und
> 4 `factual` (Quoten: [ADR 0029](adr/0029-fragetypen-und-konstruktionsklassen.md)).
> Die Abschnitte sind gezogen und nicht wählbar ([ADR 0031](adr/0031-stichprobenplan-und-ki-durchsicht.md)); gesteuert
> wird über die Frage, die ein Abschnitt trägt, nie über einen künstlichen Typ. Das Vorbereitungsblatt prüft dazu je
> Slot die Typ-Eignung ([ADR 0049](adr/0049-schreibhilfen-im-editor.md#nachtrag-10112026-typ-eignung-im-vorbereitungsblatt)).
> Ziel je Block (conceptual/comparative/limitation/procedural/factual): Block 3 4/1/1/2/0 (nach Prüfung der
> Abschnitte; ein zweites `comparative` trägt kein Slot), erreicht 3/1/2/2/0 (S22 als `limitation`); danach Block 4
> 2/2/1/2/1, erreicht 1/2/1/1/3 (S25 nach drei Durchsichtsrunden als `factual`, S31 als `factual`); danach fehlen
> 6/2/2/5/1, Ziel Block 5 2/1/1/3/1 (das dritte `conceptual` trägt in Block 5 kein Slot sauber,
> [Vorbereitungsblatt](../data/evaluation/catalogue_prep_block5.md)), erreicht 2/1/1/3/1 (S37 nach dem Sprung auf
> D051#outbound-connections als `factual`); danach fehlen 4/1/1/2/0, Ziel Block 6 4/1/1/2/0, erreicht 4/1/1/2/0. Weicht ein Block ab, wandert der Rest in den nächsten; die
> Ziele für Block 5 und 6 werden mit dem jeweiligen Vorbereitungsblatt geprüft ([Block 6](../data/evaluation/catalogue_prep_block6.md)).

> **Puffer-Regel:** Rutscht der Meilenstein, entfallen zuerst C4 (am 06.11. angewandt, [ADR 0028](adr/0028-c4-bedingung.md#nachtrag-06112026-c4-entfällt))
> und RAGAS-Feinheiten, nicht die Schreibphase; der RAGAS-Lauf selbst ist fest ([ADR 0047](adr/0047-ragas-als-triangulation.md)).

Der ursprüngliche Phasenplan (Juni 2026, Abgabe 15.12.) steht in der Git-Historie.

## Backlog

Offene Arbeit nach Priorität; erledigte Punkte wandern in den [Verlauf](#verlauf).

1. **Übungsbewertung Pilot.** Wer: Jonas. Frist: vor der Bewertung des Hauptlaufs (19.11.). Fertig, wenn die 9
   Antworten in `data/pilot/e2e_jonas/` bewertet sind und der Vergleich mit der Agentenbewertung im
   [Experiment-Protokoll](reference/experiment-record.md#pilot-e2e-1920102026) steht.
2. **Zweite bewertende Person finden** ([ADR 0046](adr/0046-zweitbewertung.md)): entschieden am 17.11.2026, keine
   Person; es gilt die hybride Bewertung (Punkt 3). Sagt sie doch zu, gilt zusätzlich der R2-Weg.
3. **Hybride Bewertung** ([ADR 0051](adr/0051-hybride-bewertung.md)). Wer: Claude, Jonas gibt frei. (a) ADR,
   Ziehung der Zusatzfragen und Ablauf: dieser PR. (b) Folge-PR: K0 in `llm_rater.py`, Zusammenführen der Werte mit
   Quelle je Zeile, `analyse.py` mit gemischtem Satz, beiden Sensitivitätsanalysen und Übereinstimmung auf 72 Antworten,
   Tests, Experiment-Protokoll. Frist: vor dem Ende von Jonas' Bewertung. Fertig, wenn beide PRs gemergt sind. Die
   Wiederholung des früheren Ersatzverfahrens entfällt; ihr Code bleibt für Pilot-Sets.
4. **Probe-Bewertung R2 auf dem Pilot** (optional). Wer: Jonas. Frist: vor der Ziehung im Hauptlauf. Fertig, wenn der
   R2-Satz in `data/pilot/e2e/` bewertet und mit `second_rater.py --mode close` abgeschlossen ist
   ([Experiment durchführen](how-to/run-the-experiment.md#zweitbewertung)).
5. **Hauptlauf dokumentieren.** Wer: Claude. Frist: beim Hauptlauf (17.–18.11.). Fertig, wenn Python-Version,
   Commit, `system_fingerprint`, Sitzungen und Abbrüche aus den Laufeinträgen im
   [Experiment-Protokoll](reference/experiment-record.md) stehen ([ADR 0033](adr/0033-antwortmodell.md),
   [ADR 0050](adr/0050-journal-und-fortsetzen-der-api-schritte.md)).
6. **Lizenzen der Korpusproben.** Wer: Claude prüft, Jonas entscheidet. Frist: vor der DOI-Veröffentlichung. Fertig,
   wenn jedes Zitat aus `data/corpus_probe/` eine Lizenz hat, die die Weitergabe erlaubt, oder entfernt ist
   (Lizenzspalte in der [Korpusauswahl](reference/corpus-selection.md)).
7. **Ergebnisse-Seite in der App.** Wer: Claude. Frist: nach dem Hauptlauf, nur falls Zeit bleibt. Fertig, wenn eine
   eigene Spezifikation (Brainstorming) vorliegt und umgesetzt ist; ersetzt das frühere Demo-Dashboard. Die Auswertung
   für die Arbeit bleibt `src/analyse.py`.
8. **Thesis-Aufgaben** (Anhang B verweisen usw.): PaperLab `docs/HANDOFF.md`.
9. **Beispiele im Fragenkatalog.** Wer: Jonas. Frist: nach Block 1. Fertig, wenn die Tabelle der Fragetypen in
    [Fragenkatalog](reference/question-catalogue.md) je Typ eine echte e2e-Frage statt des Platzhalters zeigt.

## Offene Entscheidungen

- **Zweitannotation der Relevanz** (`relevant_section_ids`): Vorschlag 10–12 Fragen, blind; ob und in welchem Umfang, nach dem Einfrieren entscheiden,
  falls Zeit bleibt ([ADR 0046](adr/0046-zweitbewertung.md)).

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
- 06.11.2026: Zeitplan neu getaktet: Fragenkatalog mit 1 von 48 Fragen, Einfrieren auf den 13.11. verschoben,
  Experimente 14.–15.11., Bewertung ab 16.11.; die Schreibphase bleibt. C4 entfällt nach der Puffer-Regel
  ([ADR 0028](adr/0028-c4-bedingung.md#nachtrag-06112026-c4-entfällt)).
- 16.11.2026: Einfrieren vom 13.11. auf den 16.11. verschoben, weil Block 6 (S41–S48) noch fehlte; Experimente
  17.–18.11., Bewertung und Analyse 19.–25.11. (drei Tage kürzer); die Schreibphase bleibt (Puffer-Regel).
- 16.11.2026: Fragenkatalog eingefroren (48 Fragen, 35 retrieval-abhängig) nach der Gesamtdurchsicht (Runde 9);
  Freeze-Datensatz und Hashes im [Experiment-Protokoll](reference/experiment-record.md#fragenkatalog-eingefroren-16112026).
- 16.11.2026: Generalprobe des Hauptlaufs mit Störungen und zwei Code-Durchsichten; Generierung und RAGAS journalisieren
  jede API-Antwort und setzen nach einem Abbruch fort, Laufeinträge nennen Commit und Umgebung
  ([ADR 0050](adr/0050-journal-und-fortsetzen-der-api-schritte.md),
  [Generalprobe](reference/experiment-record.md#generalprobe-hauptlauf-16112026)).
- 17.11.2026: Hauptlauf Schritte 0–4 (Ziehung, Retrieval, Generierung, Retrieval-Metriken, Scaffold); keine zweite
  bewertende Person, Ersatzverfahren ausgelöst
  ([ADR 0046](adr/0046-zweitbewertung.md#nachtrag-17112026-ersatzverfahren-ausgelöst)).
