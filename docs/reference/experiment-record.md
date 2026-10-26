# Experiment-Protokoll

*[Doku-Index](../README.md) · Referenz · Verwandt: [Korpus](corpus.md), [Datenformate](data-formats.md), [Vue-Historie](experiment-record-vue.md)*

Stand: 22.10.2026. Gemessene Werte aller Läufe auf dem e2e-Korpus mit Datum; wird mit jedem Lauf fortgeschrieben und
ist die Quelle für das Methodik- und Implementierungskapitel. Ausschnitt und Umfang des Korpus: [Korpus](corpus.md)
([ADR 0038](../adr/0038-korpus-e2e.md)); Parameter: [Konfiguration](configuration.md). Die abgeschlossenen Werte des
Vue.js-Korpus (bis 18.10.2026) stehen in [Experiment-Protokoll: Vue.js](experiment-record-vue.md). Dateigrößen in
MB = 10⁶ Byte.

## Snapshot (e2e)

| Feld | Wert |
|---|---|
| Repository | `tester-army/e2e` (https://github.com/tester-army/e2e), Ordner `docs/` |
| Commit | `ef977f4856da009cac26d78d2e9bb14e5991ee41` (Commit-Datum 17.10.2026; [ADR 0038](../adr/0038-korpus-e2e.md)) |
| Datum des Snapshots | 18.10.2026 ([`corpus_snapshot.txt`](../corpus_snapshot.txt): Commit, Daten, SHA-256 je Datei) |
| Dateien, Tokens, Abschnitte | [Korpus](corpus.md#quelle-und-ausschnitt); je Bereich: [Korpus](corpus.md#bereiche) |
| K1-Fenster | 375 Tokens: 667 C3-Chunks, Mittel 375,38 → 375 ([ADR 0026](../adr/0026-c3-vergleichbarkeit.md)) |

## Modellversionen

| Komponente | Version | Datum der ersten Nutzung |
|---|---|---|
| LLM | `gpt-6-luna` (Modellobjekt erstellt 14.09.2026, 17:15:02 UTC; Wissensstand 18.05.2026), Effort `none`, Temperatur 0, `seed` 20261017, höchstens 1.024 Ausgabe-Tokens ([ADR 0033](../adr/0033-antwortmodell.md)) | 17.10.2026 ([Prüfaufruf](experiment-record-vue.md#antwortmodell-prüfaufruf-17102026), Vue-Korpus) |
| RAGAS-Richter | `gpt-6-sol` (Modellobjekt erstellt 14.09.2026, 17:12:17 UTC), Temperatur 0, Effort `none`, `seed` 20261021 ([ADR 0047](../adr/0047-ragas-als-triangulation.md)) | 21.10.2026 ([RAGAS-Pilot](#ragas-pilot-e2e-21102026)) |
| Embedding-Modell | `text-embedding-3-large`, 3.072 Dimensionen ([ADR 0023](../adr/0023-embedding-modell.md)) | 13.10.2026 |
| OpenAI Python SDK | 2.44.0 | 13.10.2026 |
| ChromaDB | 1.5.9 | 13.10.2026 |
| tiktoken | 0.13.0 | 13.10.2026 |
| `ragas` / `langchain-community` | 0.4.3 / 0.4.1 ([Pins](tooling.md#ragas-pins)) | 21.10.2026 |

Die Pakete dieser Tabelle und `scipy` sind in `pyproject.toml` exakt gepinnt (`==`); die übrigen haben dort nur
Untergrenzen (`>=`). Alle installierten Stände hält `uv.lock` fest.

## Chunking (e2e)

Lauf am 18.10.2026 (`src/chunking.py`). Die Vektordateien sind versioniert ([ADR 0048](../adr/0048-korpus-und-chunk-vektoren-versioniert.md)); die Chunk-Dateien entstehen aus dem Snapshot
bitgleich neu, ihre SHA-256 stehen als `inputs_sha256` im versionierten `data/processed/embedding_runs.jsonl`, so
lassen sich neu erzeugte Dateien gegen die eingebetteten prüfen.

| Strategie | Chunks | Tokens min / Mittel / max | Median |
|---|---:|---|---:|
| C1 | 529 | 6 / 473 / 500 | 500 |
| C2 | 642 | 102 / 481 / 500 | 500 |
| C3 | 667 | 50 / 375 / 800 | 283 |
| K1 (Kontrolle, [ADR 0026](../adr/0026-c3-vergleichbarkeit.md)) | 697 | 3 / 359 / 375 | 375 |

## Embedding (e2e)

Lauf am 18.10.2026 (`src/embed.py`, Modell und Pakete: [Modellversionen](#modellversionen); Protokoll
`data/processed/embedding_runs.jsonl`, enthält nur die e2e-Läufe; Vue-Läufe:
[Vue-Historie](experiment-record-vue.md#embedding-vuejs)). K1 hat einen
Eingabe-Token weniger als die Korpussumme: Wie beim Vue-Lauf trennt ein fester Fensterschnitt ein Token-Paar, das beim
erneuten Kodieren verschmilzt; Spannen und Relevanz bleiben unberührt.

| Strategie | Vektoren | Eingabe-Tokens | Kosten (USD) | Dateigröße `.npz`² | Modellstand-Prüfung (Kosinus) |
|---|---:|---:|---:|---:|---:|
| C1 | 529 | 250.380 | 0,0325 | 11,5 MB | –¹ |
| C2 | 642 | 308.580 | 0,0401 | 14,0 MB | 0,99999 |
| C3 | 667 | 250.380 | 0,0325 | 17,7 MB | 0,99996 |
| K1 | 697 | 250.379 | 0,0325 | 13,8 MB | 0,99994 |
| Summe | 2.535 | 1.059.719 | 0,1378 (+ 0,0010 Prüfung = 0,1387) | 56,9 MB | alle ≥ 0,999 |

¹ C1 wurde zuerst eingebettet; es gab keine gespeicherte Vektordatei zum Vergleich (die Vue-Dateien sind archiviert).
Die Prüfungen bei C2, C3 und K1 vergleichen mit den an diesem Tag gespeicherten e2e-Vektoren.
Kosten- und Größensummen aus den ungerundeten Werten in `embedding_runs.jsonl` bzw. den Dateigrößen.
² Größe der Datei mit Vektoren, IDs und Texten. Die Indexgröße in `efficiency.tex` ist dagegen `vector_bytes` aus
`embedding_runs.jsonl`, nur die float32-Vektoren (C1 529 × 3.072 × 4 B = 6,50 MB).

## Stichprobenplan (e2e)

| Feld | Wert |
|---|---|
| Gezogen | 19.10.2026 (Commit `a73674b`), `uv run python src/catalogue.py plan`, Seed `20261014` ([ADR 0039](../adr/0039-stichprobenplan-e2e.md)) |
| Datei | `data/evaluation/catalogue_plan.csv`, 48 Slots und 48 Reserveabschnitte, SHA-256 `0e348c317fe1a202a0a48a54ea7eed64f045be37aa01ce2f3c45580321dff8c9` |
| Slots je Bereich | nach Tokenanteil, mindestens 1: [Korpus](corpus.md#bereiche) |
| Vue-Plan | unverändert archiviert unter `data/evaluation/archive_vue/catalogue_plan.csv` (gezogen 15.10.2026, Commit `4b22a45`; nie benutzt; SHA-256 `5af20883e71b5deb9325bb559ee24a895821f454e767623c404d77218ff52d9c`) |

## Pilot e2e (19./20.10.2026)

Vortest der ganzen Pipeline auf dem e2e-Korpus vor dem [Fragenkatalog](question-catalogue.md); zählt nicht zur
Auswertung. Set `data/pilot/e2e/`, 16 Fragen `E01`–`E16`, je 4 der Klassen single, multi-section, detail,
paraphrase, alle fünf Fragetypen, 11 Bereiche, 18 Seiten. Fragen, Referenzantworten und Annotation schrieb ein Agent,
nur zu innersten H2/H3-Abschnitten, die weder Slot noch Reserve im [Stichprobenplan](#stichprobenplan-e2e) sind
(377 von 473 Kandidaten); keine annotierte Stelle liegt im Plan, so bleibt die blinde Annotation des Katalogs
gewahrt. Jede Zeile besteht die Klassenregeln (`catalogue.class_findings`).

**Retrieval** (`scripts/difficulty_probe.py data/pilot/e2e`, 19.10.2026; Fragevektoren 460 Tokens, 0,00006 USD,
Modellstand-Prüfung Kosinus 0,99994):

| Strategie | Hit@5 | MRR | P@5 | R@5 |
|---|---:|---:|---:|---:|
| C1 | 0,94 | 0,69 | 0,26 | 0,91 |
| C2 | 0,88 | 0,65 | 0,28 | 0,80 |
| C3 | 0,88 | 0,61 | 0,21 | 0,83 |
| K1 | 0,81 | 0,59 | 0,28 | 0,77 |

Kein Deckeneffekt; die Strategien trennen sich je Klasse unterschiedlich (single: C3 Hit@5 0,50 gegen 1,00 bei C1 und
C2; paraphrase: C3 1,00 gegen 0,75). Ohne Treffer in den Top 5: E03 bei C3, E04 bei C3 und K1, E10 bei C2 und K1,
E13 bei C1, C2 und K1.

**Generierung** (`generate.py --set data/pilot/e2e`, 19.10.2026): 48 Antworten C1–C3 und 16 K0-Antworten in einem Lauf,
105.207 Prompt- und 4.622 Antwort-Tokens, 0,0128 USD (C1 0,0045, C2 0,0045, C3 0,0032, K0 0,0006). `model_reported`
`gpt-6-luna`, Modellobjekt erstellt 14.09.2026 17:15:02 UTC (vor und nach dem Lauf gleich), kein `system_fingerprint`.

**Bewertung**: Kernpunkte E01–E03 von Jonas geprüft und eingefroren, E04–E16 von einem Agenten aus den Referenzantworten
(ohne Blick auf die Antworten); ein Agent bewertete alle Antworten regelbasiert und blind als Entwicklungshilfe
(`scores.csv`, `scores_control.csv`, nur lokal; nachrechenbar aus `scoring_sheet*.csv` und `scoring_key.csv`). Mittel über die vier gemeinsamen Kriterien
(`config.CONTROL_CRITERIA`, `evaluate_answers.py --mode summarise --control`; Regeln:
[Evaluation](evaluation.md#regelbasierte-bewertung), Regelversion `2026-10-18`):

| | Gesamt | Korrektheit | Vollständigkeit | Halluzinationsfreiheit | Verständlichkeit |
|---|---:|---:|---:|---:|---:|
| K0 | 0,92 | 0,94 | 0,38 | 0,38 | 2,00 |
| C1 | 1,84 | 1,88 | 1,69 | 1,88 | 1,94 |
| C2 | 1,80 | 1,81 | 1,62 | 1,88 | 1,88 |
| C3 | 1,72 | 1,75 | 1,50 | 1,75 | 1,88 |

Mit allen fünf Kriterien (C1–C3): C1 1,86, C2 1,82, C3 1,76; 34 der 48 Antworten erreichen überall 2. Die Abzüge sitzen
in wenigen Fragen: E06 (alle drei Strategien beantworten den Bitrise-Teil mit dem Abschnitt eines anderen
CI-Dienstes), E04 und E13 (Teilantworten bei allen drei), E05 (C1, C3), E03 (C3), E10 (C2), E16 (C3, unvollständig).

**Closed-Book-Probelauf**: Die K0-Antworten nutzen den Prompt der Closed-Book-Prüfung ([ADR 0040](../adr/0040-closed-book-pruefung.md)).
Sie treffen den Kernpunkt bei 5 von 16 Fragen (E06, E11, E13, E15, E16); E06 trifft nur Punkt 1 und ist im Übrigen
falsch, E13 und E16 nur bei großzügiger Lesart: streng 2–4 von 16. K0 lehnt nie ab, sondern antwortet sicher und oft
falsch (Korrektheit 0 bei 8 von 16).

**Befund** (Pilot, n = 16, keine ADR): K0 liegt weit unter C1–C3, das Retrieval trägt also den größten Teil der
Antwortqualität (Zweck von [ADR 0038](../adr/0038-korpus-e2e.md)); die Antwortbewertung liegt nahe der Obergrenze
(Mittel 1,7–1,9), Unterschiede zeigen sich vor allem im Retrieval und bei single- und multi-section-Fragen, die harten Klassen
([ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md)) bleiben also nötig; H2 ist auswertbar. Ohne Kontext
trifft das Modell auch Fragen außerhalb des Plans zu rund einem Viertel; die Grenze von höchstens 16 bekannten
Katalogfragen ist erreichbar, aber knapp, daher die Prüfung nach jedem Block. Die Regelfragen des Pilots (`direct` bei falscher
Kernaussage, Teilantworten mit Hinweis wie bei E04 und E13) klärt
[ADR 0043](../adr/0043-praezisierung-direct-und-teilantworten.md) (Regelversion `2026-10-20`); der Pilot ist unter
`2026-10-18` bewertet.

**Offen**: Jonas' Übungsbewertung der ersten 3 Fragen (9 Antworten, Set `data/pilot/e2e_jonas/`, Kernpunkte
eingefroren) und ihr Vergleich mit der Agentenbewertung.

## Probelauf Hauptlauf (21.10.2026)

Befehlsfolge aus [Experiment durchführen](../how-to/run-the-experiment.md#hauptlauf-auf-einen-blick) in einer
Wegwerfkopie des Repos, ohne API-Schlüssel (jeder API-Aufruf wäre gescheitert), die 16 Pilotfragen als Hauptkatalog,
der Freeze-Datensatz direkt geschrieben (die strenge Prüfung von `catalogue.py freeze` decken die Tests ab).

- `retrieve.py` und `retrieve.py --control` liefen aus den gespeicherten Fragevektoren ohne API-Aufruf; beide
  Ergebnisdateien sind byteweise gleich mit denen des Pilots (`scripts/difficulty_probe.py`).
- `generate.py` verweigert das Überschreiben vorhandener Antworten (ADR 0033); für die weiteren Schritte standen die
  Pilotantworten mit ihrem `generate`-Eintrag.
- `evaluate_retrieval.py` (beide), `evaluate_answers.py --mode scaffold` (48 verblindete Antworten) liefen durch;
  `--mode scaffold --control` bricht vor `scores.csv` ab, `analyse.py` vor dem `summarise`-Eintrag (beides gewollt).
  Die Bewertung selbst ist Handarbeit und war nicht Teil des Probelaufs; `analyse.py` ist auf dem Pilot-Set erprobt.
- Gefunden und behoben: Fehlte ein Laufeintrag, nannten die Meldungen `src/summarise.py` statt
  `evaluate_answers.py --mode summarise` (`run_log.step_command`).

## RAGAS-Pilot e2e (21.10.2026)

Zwei Läufe von `ragas_eval.py --set data/pilot/e2e` (und `--repeat`) über die 48 Antworten C1–C3 des Pilots e2e
(16 Fragen); Verfahren: [Evaluation](evaluation.md#triangulation), Dateien: [Datenformate](data-formats.md#ragas).
Richter und Pakete: [Modellversionen](#modellversionen); Strictness 1, kein Fingerabdruck gemeldet. Der Pilot zählt
nicht zur Auswertung; die Werte sind Erprobung.

| Lauf | Zeilen | NaN | Richter-Tokens (Eingabe / Ausgabe) | Embedding-Tokens | Kosten (USD) |
|---|---:|---:|---:|---:|---:|
| `ragas` | 48 | 0 | 779.606 / 46.299 | 2.471 | 2,02 |
| `ragas_repeat` | 48 | 0 | 779.722 / 46.777 | 2.486 | 2,03 |
| zusammen | 96 | 0 | 1.559.328 / 93.076 | 4.957 | 4,05 |

Kein Wert fehlt; die Embeddings kosten je Lauf unter 0,001 USD, der Rest ist der Richter.

**Mittel je Strategie** (Lauf `ragas`, 16 Fragen je Strategie):

| Strategie | Faithfulness | Response Relevancy | Context Precision | Context Recall |
|---|---:|---:|---:|---:|
| C1 | 0,98 | 0,73 | 0,76 | 0,97 |
| C2 | 0,94 | 0,72 | 0,78 | 0,85 |
| C3 | 0,96 | 0,71 | 0,75 | 0,83 |

**Übereinstimmung** mit dem Gegenstück (Spearmans ρ je Antwort; `ragas_agreement`):

| Paar | gesamt (n = 48) | C1 | C2 | C3 |
|---|---:|---:|---:|---:|
| Faithfulness ~ Quellenbezug | 0,43 | −0,07 | 0,62 | 0,62 |
| Faithfulness ~ Halluzinationsfreiheit | 0,35 | −0,07 | 0,62 | 0,36 |
| Response Relevancy ~ Frage beantwortet | nicht bestimmbar | nicht bestimmbar | nicht bestimmbar | nicht bestimmbar |
| Context Precision ~ P@5 | 0,11 | −0,21 | 0,10 | 0,41 |
| Context Recall ~ R@5 | 0,90 | 0,73 | 0,90 | 1,00 |

Bei Response Relevancy ~ Frage beantwortet ist eine Seite konstant (alle Antworten bestehen die Prüffrage), ρ ist dann
nicht definiert. **Befund** (ungeprüft, keine ADR): Context Precision stimmt kaum mit P@5 überein, Context Recall eng
mit R@5; RAGAS beurteilt die Relevanz eines Chunks mit dem LLM, P@5 per Tokenüberlappung
([Evaluation](evaluation.md#relevanz-eines-chunks)).

**Stabilität** (Lauf 2 gegen Lauf 1, je Metrik 48 Paare; `ragas_stability`; mittlere absolute Differenz mit drei
Nachkommastellen, weil sie sonst auf 0,00 oder 0,01 fällt):

| Metrik | gleiche Werte | mittlere abs. Differenz | ρ |
|---|---:|---:|---:|
| Faithfulness | 0,90 | 0,013 | 0,80 |
| Response Relevancy | 0,60 | 0,018 | 0,88 |
| Context Precision | 0,94 | 0,007 | 0,98 |
| Context Recall | 1,00 | 0,000 | 1,00 |

Trotz Temperatur 0 und festem `seed` sind die Werte nicht bitgleich wiederholbar; am wenigsten stabil ist Response
Relevancy. Folgerung: [ADR 0047](../adr/0047-ragas-als-triangulation.md).

Gefunden beim Aufbau: RAGAS 0.4.3 sendet an `gpt-6-sol` Temperatur 1,0 (behoben durch die Unterklasse), und seine
Telemetrie sendet an einen Server (abgeschaltet), siehe [RAGAS-Pins](tooling.md#ragas-pins) und
[Umgebungsvariablen](tooling.md#umgebungsvariablen).



## Zweitbewertung: Probe auf dem Pilot e2e (22.10.2026)

Verfahren: [ADR 0046](../adr/0046-zweitbewertung.md),
[Experiment durchführen](../how-to/run-the-experiment.md#zweitbewertung). `second_rater.py --mode draw --set
data/pilot/e2e --questions 4` zog mit Seed 20261022 (`config.SECOND_RATER_SEED`) E04 (single), E08 (multi-section),
E09 (detail) und E15 (paraphrase) in `second_rater_sample.csv` (SHA-256 `a7776306…7c292d7a`, Laufeintrag
`second_rater_draw`). `--mode export` legte den Satz der zweiten Person in `data/pilot/e2e/second_rater/` an: 12 Codes
(4 Fragen × C1–C3), 13 Kernpunkte, Bogen leer. Bewertet und mit `--mode close` abgeschlossen ist noch nichts.

## Pilot-Sets

Vorhandene Dateien und gelaufene Schritte je e2e-Set, Stand 22.10.2026 (`git ls-files data/pilot/<set>`, `runs.jsonl`);
Zweck und Format eines Sets: [Datenformate](data-formats.md#pilot-sets), Vue-Sets:
[Vue-Historie](experiment-record-vue.md#vue-pilot-sets-dateien-und-laufschritte). Was versioniert ist, regelt
[Versioniert und ignoriert](data-formats.md#versioniert-und-ignoriert).

| Set | versionierte Dateien | nur lokal | Laufschritte (`runs.jsonl`) |
|---|---|---|---|
| `data/pilot/e2e/` | `questions.csv`, `ground_truth.csv`, `retrieved_results.csv`, `retrieved_results_control.csv`, `retrieval_scores.csv`, `retrieval_scores_control.csv`, `generated_answers.csv`, `generated_answers_control.csv`, `key_points.csv`, `scoring_sheet.csv`, `scoring_key.csv`, `scoring_checks.csv`, `scoring_items_control.jsonl`, `scoring_sheet_control.csv`, `scoring_checks_control.csv`, `ragas_scores.csv`, `ragas_scores_repeat.csv`, `second_rater_sample.csv`, `second_rater/` (`key_points.csv`, `scoring_items.jsonl`, `scoring_sheet.csv`, `runs.jsonl`), `runs.jsonl` | `query_embeddings.npz`, `scoring_items.jsonl`, `scoring_packet.md`, `scores.csv`, `scores_control.csv`, `output/` | 19.10.: `retrieve` (C1–C3, K1), `generate` (mit K0), `scaffold` (48 Codes), `key_points`, `scaffold` K0 (16 Codes); 20.10.: `evaluate_retrieval` (C1–C3, K1); 21.10.: `ragas`, `ragas_repeat`; 22.10.: `second_rater_draw`, `second_rater_export` (`second_rater/runs.jsonl`: `scaffold` 12 Codes, `key_points`) |
| `data/pilot/e2e_jonas/` | Übungskopie von `e2e` (alle 16 Fragen und 48 Antworten): `questions.csv`, `ground_truth.csv`, `generated_answers.csv`, `generated_answers_control.csv`, `key_points.csv` (E01–E03), `scoring_sheet.csv` (9 Zeilen, leer), `scoring_key.csv`, `runs.jsonl` | `scoring_items.jsonl`, `scoring_packet.md` | aus `e2e` übernommen: `retrieve`, `generate`, `scaffold` (48 Codes); 19.10.: `scaffold` mit `--limit 3` (9 Codes), `key_points` |
