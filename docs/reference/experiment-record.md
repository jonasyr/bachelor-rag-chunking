# Experiment-Protokoll

> Seitentyp: Nachschlagen (reference). Stand: 20.10.2026. Übersicht: [Dokumentation](../README.md).

Messwerte aller Läufe (Chunking, Embedding, Stichprobenplan, Pilot e2e, Pilotproben, Vortest) mit Datum; wird mit jedem Lauf
fortgeschrieben und ist die Quelle für das Methodik- und Implementierungskapitel. Ausschnitt und Umfang des Korpus:
[Korpus](corpus.md) ([ADR 0038](../adr/0038-korpus-e2e.md)); Parameter: [Konfiguration](configuration.md). Der erste
Teil gilt für den aktuellen e2e-Korpus, der zweite ([Historie](#historie-vuejs-korpus-bis-18102026)) für den
Vue.js-Korpus bis 18.10.2026.

## Snapshot (e2e)

| Feld | Wert |
|---|---|
| Repository | `tester-army/e2e` (https://github.com/tester-army/e2e), Ordner `docs/` |
| Commit | `ef977f4856da009cac26d78d2e9bb14e5991ee41` (Commit-Datum 17.10.2026; [ADR 0038](../adr/0038-korpus-e2e.md)) |
| Datum des Snapshots | 18.10.2026 ([`corpus_snapshot.txt`](../corpus_snapshot.txt): Commit, Daten, SHA-256 je Datei) |
| Dateien | 62: 60 Seiten (`*.mdx`, genau die Navigation) und `docs.json`, `snippets/model-provider.jsx` |
| Umfang | Tokens und Abschnitte: [Korpus](corpus.md#quelle-und-ausschnitt); je Bereich: [Korpus](corpus.md#bereiche) |
| K1-Fenster | 375 Tokens: 667 C3-Chunks, Mittel 375,38 → 375 ([ADR 0026](../adr/0026-c3-vergleichbarkeit.md)) |

## Chunking (e2e)

Lauf am 18.10.2026 (`src/chunking.py`).

| Strategie | Chunks | Tokens min / Mittel / max | Median |
|---|---:|---|---:|
| C1 | 529 | 6 / 473 / 500 | 500 |
| C2 | 642 | 102 / 481 / 500 | 500 |
| C3 | 667 | 50 / 375 / 800 | 283 |
| K1 (Kontrolle, [ADR 0026](../adr/0026-c3-vergleichbarkeit.md)) | 697 | 3 / 359 / 375 | 375 |

## Embedding (e2e)

Lauf am 18.10.2026 (`src/embed.py`, `text-embedding-3-large`, 3072 Dimensionen, SDK 2.44.0, Chroma 1.5.9; Protokoll
`data/processed/embedding_runs.jsonl`, enthält nur die e2e-Läufe). Die Vue-Vektoren, der alte Chroma-Index und das
Vue-Protokoll liegen lokal unter `data/processed/archive_vue_2026-10-18/` (nicht versioniert). K1 hat einen
Eingabe-Token weniger als die Korpussumme: Wie beim Vue-Lauf trennt ein fester Fensterschnitt ein Token-Paar, das beim
erneuten Kodieren verschmilzt; Spannen und Relevanz bleiben unberührt.

| Strategie | Vektoren | Eingabe-Tokens | Kosten (USD) | Vektordatei | Modellstand-Prüfung (Kosinus) |
|---|---:|---:|---:|---:|---:|
| C1 | 529 | 250.380 | 0,0325 | 11,5 MB | –¹ |
| C2 | 642 | 308.580 | 0,0401 | 14,0 MB | 0,99999 |
| C3 | 667 | 250.380 | 0,0325 | 17,7 MB | 0,99996 |
| K1 | 697 | 250.379 | 0,0325 | 13,8 MB | 0,99994 |
| Summe | 2.535 | 1.059.719 | 0,1378 (+ 0,0010 Prüfung = 0,1387) | 56,9 MB | alle ≥ 0,999 |

¹ C1 wurde zuerst eingebettet; es gab keine gespeicherte Vektordatei zum Vergleich (die Vue-Dateien sind archiviert).
Die Prüfungen bei C2, C3 und K1 vergleichen mit den an diesem Tag gespeicherten e2e-Vektoren.
Kosten- und Größensummen aus den ungerundeten Werten in `embedding_runs.jsonl` bzw. den Dateigrößen.

## Stichprobenplan (e2e)

| Feld | Wert |
|---|---|
| Gezogen | 19.10.2026 (Commit `a73674b`), `uv run python src/catalogue.py plan`, Seed `20261014` ([ADR 0039](../adr/0039-stichprobenplan-e2e.md)) |
| Datei | `data/evaluation/catalogue_plan.csv`, 48 Slots und 48 Reserveabschnitte, SHA-256 `0e348c317fe1a202a0a48a54ea7eed64f045be37aa01ce2f3c45580321dff8c9` |
| Slots je Bereich | nach Tokenanteil, mindestens 1: [Korpus](corpus.md#bereiche) |
| Vue-Plan | unverändert archiviert unter `data/evaluation/archive_vue/catalogue_plan.csv` (gezogen 15.10.2026, Commit `4b22a45`; nie benutzt; SHA-256 `5af20883e71b5deb9325bb559ee24a895821f454e767623c404d77218ff52d9c`) |

## Antwortmodell: Prüfaufruf (17.10.2026)

Ein Aufruf mit den Einstellungen des Hauptlaufs (Pilotfrage H01 des Vue-Sets `hard`, top-5 von C1 auf dem Vue-Korpus,
nicht gespeichert) bestätigte, dass die API `temperature = 0`, `seed` und Effort `none` zusammen annimmt: `finish_reason
= "stop"`, 2.649 Prompt- und 140 Antwort-Tokens, abgerechnet 0,00034 USD. Gemeldet wurden nur das Modell `gpt-6-luna`
und kein `system_fingerprint`; die Modellliste der API führt für GPT-6 keine datierten Varianten (`gpt-5.6-luna`,
`gpt-6-astra`, `gpt-6-luna`, `gpt-6-sol`, `gpt-6.1-sol`). Erstellungszeitpunkte laut `GET /v1/models`: `gpt-6-luna`
14.09.2026, 17:15:02 UTC; `gpt-6-sol` 14.09.2026, 17:12:17 UTC. Folgerung: [ADR 0033](../adr/0033-antwortmodell.md).

## Modellversionen

| Komponente | Version | Datum der ersten Nutzung |
|---|---|---|
| LLM | `gpt-6-luna` (Modellobjekt erstellt 14.09.2026, 17:15:02 UTC; Wissensstand 18.05.2026), Effort `none`, Temperatur 0, `seed` 20261017, höchstens 1.024 Ausgabe-Tokens ([ADR 0033](../adr/0033-antwortmodell.md)) | 17.10.2026 (Prüfaufruf) |
| Embedding-Modell | `text-embedding-3-large`, 3.072 Dimensionen ([ADR 0023](../adr/0023-embedding-modell.md)) | 13.10.2026 |
| OpenAI Python SDK | 2.44.0 | 13.10.2026 |
| ChromaDB | 1.5.9 | 13.10.2026 |
| tiktoken | 0.13.0 | 13.10.2026 |

## Pilot e2e (19./20.10.2026)

Vortest der ganzen Pipeline auf dem e2e-Korpus vor dem Fragenkatalog (Schritt 5 in [plan.md](../plan.md#stand)); zählt
nicht zur Auswertung. Set `data/pilot/e2e/`, 16 Fragen `E01`–`E16`, je 4 der Klassen single, multi-section, detail,
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
C2; paraphrase: C3 1,00 gegen 0,75). Ohne Treffer in den Top 5: E03 bei C3, E04 bei C3 und K1, E10 bei C2 und K1, E13 bei C1, C2 und K1.

**Generierung** (`generate.py --set data/pilot/e2e`, 19.10.2026): 48 Antworten C1–C3 und 16 K0-Antworten in einem Lauf,
105.207 Prompt- und 4.622 Antwort-Tokens, 0,0128 USD (C1 0,0045, C2 0,0045, C3 0,0032, K0 0,0006). `model_reported`
`gpt-6-luna`, Modellobjekt erstellt 14.09.2026 17:15:02 UTC (vor und nach dem Lauf gleich), kein `system_fingerprint`.

**Bewertung**: Kernpunkte E01–E03 von Jonas geprüft und eingefroren, E04–E16 von einem Agenten aus den Referenzantworten
(ohne Blick auf die Antworten); ein Agent bewertete alle Antworten regelbasiert und blind als Entwicklungshilfe
(`scores.csv`, `scores_control.csv` im Set). Mittel über die vier gemeinsamen Kriterien
(`config.CONTROL_CRITERIA`, `evaluate_answers.py --mode summarise --control`):

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

**Offen**: Jonas' Übungsbewertung der ersten 3 Fragen (9 Antworten, Set `data/pilot/e2e_jonas/`, Kernpunkte
eingefroren) und ihr Vergleich mit der Agentenbewertung.

**Folgerungen** (Empfehlungen, Entscheidung bei Jonas):
- Der Korpus erfüllt den Zweck von [ADR 0038](../adr/0038-korpus-e2e.md): K0 liegt weit unter C1–C3, das Retrieval
  trägt den größten Teil der Antwortqualität; H2 ist damit auswertbar.
- Die Antwortbewertung liegt nahe an der Obergrenze (Mittel 1,7–1,9); Unterschiede zwischen den Strategien zeigen sich
  vor allem in den Retrieval-Metriken und bei single- und multi-section-Fragen. Die harten Klassen des Katalogs
  ([ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md)) bleiben nötig.
- Selbst Fragen außerhalb des Plans trifft das Modell ohne Kontext zu rund einem Viertel; die Grenze von höchstens 16
  bekannten Katalogfragen ist erreichbar, aber nicht großzügig. Die Prüfung nach jedem Block lohnt sich.
- Unklar in den Regeln: ob `direct` „ja“ ist, wenn die (falsche) Kernaussage der Antwort vorn steht. Der Agent wertete
  „nein“, wenn der Kernpunkt fehlt oder falsch ist, „ja“, wenn er nur teilweise vorn steht. Vor der echten Bewertung
  in [Evaluation](evaluation.md#regelbasierte-bewertung) präzisieren.
- Teilantworten mit Hinweis „die Passagen enthalten den Rest nicht“ (E04, E13) wertete der Agent als Antwort, nicht als
  `declines`; die Regel deckt das, sollte aber im Hilfetext stehen.

## Historie: Vue.js-Korpus (bis 18.10.2026)

Alle Abschnitte dieses Teils gelten für den Vue.js-Korpus ([ADR 0025](../adr/0025-korpus-guide-api-styleguide.md),
ersetzt durch [ADR 0038](../adr/0038-korpus-e2e.md)); sie sind abgeschlossen und werden nicht fortgeschrieben.
Vue-Chunks, -Vektoren, Chroma-Index und Embedding-Protokoll liegen lokal unter `data/processed/archive_vue_2026-10-18/`
(nicht versioniert). Die Vue-Dateien `documents.jsonl` und `sections.jsonl` sind nicht archiviert; sie lassen sich aus
dem Vue-Commit `40aa88a` mit dem Code vor dem e2e-Wechsel (Stand `4115ffc`) neu erzeugen. Bis dahin sind die
Recall@5-Werte der Vue-Pilotproben nicht aus dem Archiv nachrechenbar. Die Pilot-Sets unter `data/pilot/` tragen Vue-IDs
und lassen sich auf den aktuellen e2e-Daten unter `data/processed/` nicht wiederholen.

### Snapshot (Vue.js, bis 18.10.2026)

| Feld | Wert |
|---|---|
| Repository | `vuejs/docs` (https://github.com/vuejs/docs) |
| Commit | `40aa88af0094f7bab4aaf786e55c748a6a251d88` (Commit-Datum 15.09.2026; [ADR 0025](../adr/0025-korpus-guide-api-styleguide.md)) |
| Datum des Snapshots | 14.10.2026 (Datensatz in der Git-Historie: `git show 4115ffc:docs/corpus_snapshot.txt`, mit Commit, Daten, Bereichen, Ausschlüssen, SHA-256 je Datei; die aktuelle [`corpus_snapshot.txt`](../corpus_snapshot.txt) enthält den e2e-Datensatz) |
| Pfade, Dateien, Tokens, Abschnitte | 79 Dateien (Guide 52, API 22, Style Guide 5), 165.723 Tokens, 813 Abschnitte; Details in der Git-Historie von `docs/reference/corpus.md` |

### Chunking (Vue.js)

| Strategie | Chunks | Tokens min / Mittel / max | Median |
|---|---:|---|---:|
| C1 | 369 | 17 / 449 / 500 | 500 |
| C2 | 435 | 108 / 463 / 500 | 500 |
| C3 | 718 | 50 / 231 / 799 | 190 |
| K1 (Kontrolle, [ADR 0026](../adr/0026-c3-vergleichbarkeit.md)) | 758 | 3 / 219 / 231 | 231 |

K1-Fenster = kaufmännisch gerundetes Mittel der C3-Chunklängen (230,8 → 231). C3 ohne Obergrenze: 706 Segmente,
davon 12 über 800 Tokens, längstes 1.467 (Obergrenze nach [ADR 0021](../adr/0021-c3-grenzen.md), begründet in
[ADR 0026](../adr/0026-c3-vergleichbarkeit.md)).

### Embedding (Vue.js)

Lauf am 14.10.2026 (`src/embed.py`; Protokoll lokal archiviert:
`data/processed/archive_vue_2026-10-18/embedding_runs.jsonl`). Die von OpenAI abgerechneten Tokens stimmen für alle vier
Strategien exakt mit der eigenen Zählung der gesendeten Texte überein (`src/tokens.py`). Bei K1 ist ein Chunk
(`K1_D057_0015`) 231 Token-Positionen lang, sein Text kodiert aber zu 230 Tokens: Der feste Fensterschnitt trennt ein
Token-Paar, das der Tokenizer beim erneuten Kodieren zusammenführt. Spannen und Relevanz bleiben davon unberührt.

| Strategie | Vektoren | Eingabe-Tokens | Kosten (USD) | Vektordatei | Modellstand-Prüfung (Kosinus) |
|---|---:|---:|---:|---:|---:|
| C1 | 369 | 165.723 | 0,0215 | 8,5 MB | 0,99991¹ |
| C2 | 435 | 201.323 | 0,0262 | 10,0 MB | 0,99987 |
| C3 | 718 | 165.723 | 0,0215 | 18,9 MB | 0,99987 |
| K1 | 758 | 165.722 | 0,0215 | 14,3 MB | 0,99963 |
| Summe | 2.280 | 698.491 | 0,0908 (+ 0,0013 Prüfung = 0,0921) | 51,8 MB | alle ≥ 0,999 |

¹ Die Prüfung vergleicht mit den jeweils schon gespeicherten übrigen Vektordateien: bei C1 (zuerst eingebettet) mit
den Vektoren vom 13.10.2026 (alter Korpus), bei C2, C3 und K1 teils schon mit den neuen vom 14.10.2026.
Kosten- und Größensummen aus den ungerundeten Werten im archivierten `embedding_runs.jsonl` bzw. den Dateigrößen.

Die Modellstand-Prüfung von K1 (0,99963) liegt unter dem am 13.10.2026 gemessenen Wert für gleiche Texte
(≥ 0,99996), aber deutlich über dem Schwellwert 0,999 und weit über der Ähnlichkeit verschiedener Chunks (≤ 0,84).

### Korpuserweiterung (14.10.2026): Prüfungen

Umstellung nach [ADR 0025](../adr/0025-korpus-guide-api-styleguide.md) und
[ADR 0026](../adr/0026-c3-vergleichbarkeit.md); Spezifikation und Plan:
`docs/superpowers/specs/2026-10-14-corpus-extension-design.md`, `docs/superpowers/plans/2026-10-14-corpus-extension.md`.

| Prüfung | Ergebnis |
|---|---|
| V1 Guide-Bereinigung unverändert | Der alte Guide (`b75d188`, neu geholt und gegen den alten Prüfsummen-Datensatz verifiziert) ergibt mit dem neuen Code Byte für Byte dieselben `documents.jsonl`, `sections.jsonl` und dasselbe Manifest. |
| V2 nur geänderte Guide-Dateien weichen ab | 47 von 52 Guide-Seiten unverändert; geändert (Tokens alt → neu): `transition-group` 823 → 834, `slots` 3.657 → 3.740, `component-basics` 3.666 → 3.583, `lifecycle` 447 → 530, `render-function` 4.511 → 4.517. Bei `teleport.md` entfiel upstream nur ein Werbelink, den die Bereinigung schon vorher entfernte. |
| V3 Dateiliste unabhängig geprüft | 79 lokale Dateien = GitHub-Baum des Commits ohne die Ausschlüsse (79). |
| V4 API-Sonderfälle von Hand gelesen | Titel `<script setup>` und `Composition API: Dependency Injection`; Überschriften `\<script setup>`, `PropType\<T>`; die `v-text`-Zeile endet sauber mit `` `<span>…</span>`). `` |
| V5 Chunk-Invarianten | Alle Prüfungen von `chunking.py` für C1–C3 und K1 bestanden; K1-Größe gleich der Regel. |
| V6 Tokens | abgerechnet = gesendete Texte für alle vier Strategien (siehe Embedding). |
| V7 Reproduzierbarkeit | Zweiter Probenlauf ohne API-Aufruf, alle vier Ergebnisdateien Byte für Byte gleich. |
| V8 Pilot-Ground-Truth | 33 annotierte Abschnitte über Pfad und Anker abgebildet; Titel, Ebene und Text unverändert, keine Annotation geändert; unabhängig von einem zweiten Prüfer nachgerechnet. |

Gefunden und behoben dabei: Die Integrationsprüfung entdeckte in zwei API-Seiten eingerückte Überschriften
(`  ### Function Signature`), die als Text durchgerutscht wären; drei Abschnitte wurden erst mit der CommonMark-Regel
(bis zu drei Leerzeichen Einrückung) erkannt.

### Pilotproben auf dem erweiterten Korpus (14.10.2026)

Gleiche Fragen und Annotationen wie in den Proben unten (IDs abgebildet, V8); `scripts/difficulty_probe.py`,
jetzt mit der Kontrolle K1. Keine API-Kosten (gespeicherte Fragevektoren). Kontext@5 = Mittel über die Fragen der
summierten Tokens der fünf Treffer ([Evaluation](evaluation.md#effizienzkosten-abhängige-variable)).

Probe 1 (8 einfache Fragen):

| Strategie | Hit@5 | MRR | Precision@5 | Recall@5 | Kontext@5 |
|---|---:|---:|---:|---:|---:|
| C1 | 1,00 | 0,88 | 0,23 | 1,00 | 2.406 |
| C2 | 1,00 | 0,76 | 0,28 | 1,00 | 2.441 |
| C3 | 1,00 | 0,94 | 0,23 | 1,00 | 1.302 |
| K1 | 1,00 | 0,94 | 0,38 | 1,00 | 1.082 |

Probe 2 (16 schwere Fragen), Annotation blind, also vor jedem Retrieval festgelegt (`data/pilot/hard/`; Hauptwerte nach
[ADR 0027](../adr/0027-blinde-annotation.md)):

| Strategie | Hit@5 | MRR | Precision@5 | Recall@5 | Kontext@5 |
|---|---:|---:|---:|---:|---:|
| C1 | 1,00 | 0,68 | 0,29 | 0,95 | 2.388 |
| C2 | 0,81 | 0,61 | 0,31 | 0,76 | 2.402 |
| C3 | 0,94 | 0,66 | 0,24 | 0,85 | 1.263 |
| K1 | 0,94 | 0,59 | 0,33 | 0,82 | 1.129 |

Nach Fragenart (MRR / Recall@5, blind):

| Art | C1 | C2 | C3 | K1 |
|---|---|---|---|---|
| multi-section (n = 5) | 0,87 / 0,83 | 0,85 / 0,83 | 0,67 / 0,73 | 0,50 / 0,63 |
| detail (n = 4) | 0,88 / 1,00 | 0,62 / 0,75 | 0,75 / 1,00 | 0,62 / 0,75 |
| paraphrase (n = 7) | 0,43 / 1,00 | 0,44 / 0,71 | 0,60 / 0,86 | 0,63 / 1,00 |

Post-hoc-Sensitivität, **keine Evidenz** ([ADR 0027](../adr/0027-blinde-annotation.md); Annotation nach Sicht der
Ergebnisse um drei Abschnitte ergänzt, siehe Probe 2 im vorherigen Stand; `data/pilot/hard_posthoc/`): C1 1,00 / 0,76 /
0,34 / 0,92, C2 0,81 / 0,66 / 0,36 / 0,73, C3 1,00 / 0,69 / 0,28 / 0,89, K1 0,94 / 0,67 / 0,36 / 0,80 (Hit@5 / MRR / P@5
/ R@5). Sie zeigt nur, wie stark eine unvollständige Annotation die Werte verschiebt.

Befund (Pilot, blinde Annotation, n klein, keine Signifikanz):

- Der größere Korpus macht das Retrieval schwerer: Gegenüber dem alten Korpus sinken in Probe 2 Hit@5 und Recall@5
  vor allem bei C2 (0,94 → 0,81 bzw. 0,89 → 0,76); Guide- und API-Seiten konkurrieren um dieselben Plätze.
- Die Kontrolle wirkt wie vorgesehen und zeigt kein einheitliches Bild: Bei Mehrabschnitts- und Detailfragen liegt C3
  vor K1 (Recall@5 0,73 gegen 0,63 bzw. 1,00 gegen 0,75), bei Paraphrasen liegt K1 vorn (1,00 gegen 0,86). Ein Teil
  des C3-Verhaltens geht also auf die Größe zurück, ein Teil auf die Struktur; ob das trägt, zeigt erst der Katalog.
- Kontext je Antwort: C3 und K1 liefern dem Sprachmodell nur etwa halb so viele Tokens wie C1/C2.

Zur Annotation: Blinde Annotationen sind die Hauptwerte, nachträgliche Ergänzungen nur Sensitivität (Begründung:
[ADR 0027](../adr/0027-blinde-annotation.md), ausgelöst durch das Codex-Review von PR #6). Die blinde Fassung wurde aus
der ursprünglichen Datei Byte für Byte wiederhergestellt; ihre SHA-256 (`f9ddb34b…7e860`) ist gleich der im ersten
API-Lauf protokollierten (`data/pilot/hard/runs.jsonl`, erste Zeile). Sie liegt mit alten IDs in
`data/pilot/hard/history/ground_truth_b75d188.csv` und wurde wie die übrigen Pilotdateien über Pfad und Anker
abgebildet. Regeln für den echten Fragenkatalog, auch die Folgerungen aus beiden Proben:
[Fragenkatalog](question-catalogue.md#regeln-für-annotation-und-aufbau).

### Vortest Generierung und Bewertung (Pilot `hard`, 17./18.10.2026)

Vortest von Prompt und Bewertungskette auf dem Pilot-Set `data/pilot/hard/` (Vue-Fragen, Vue-Chunks; nicht Teil des
Fragenkatalogs). Protokoll: `data/pilot/hard/runs.jsonl` (letzte drei Zeilen).

Generierung am 17.10.2026 (`src/generate.py`): 48 Antworten (16 Fragen × C1–C3), Modell `gpt-6-luna`, Effort `none`,
Temperatur 0, `seed` 20261017, höchstens 1.024 Ausgabe-Tokens; gemeldet (`model_reported`) `gpt-6-luna`,
`model_created` 14.09.2026, 17:15:02 UTC, `system_fingerprint` leer (`null`). Der Lauf enthält keine K0-Antworten
(K0 kam am 19.10.2026 hinzu).

| Strategie | Prompt-Tokens | Antwort-Tokens | Kosten (USD) |
|---|---:|---:|---:|
| C1 | 40.332 | 1.249 | 0,0047 |
| C2 | 40.579 | 1.226 | 0,0047 |
| C3 | 22.279 | 1.314 | 0,0029 |
| Summe | 103.190 | 3.789 | 0,0122 |

Bewertungsgerüst am 17.10.2026 (`src/evaluate_answers.py --mode scaffold --set data/pilot/hard --limit 8`): 24 Codes,
die ersten acht Fragen (H01–H08) × C1–C3. Kernpunkte eingefroren am 18.10.2026 (Eintrag `key_points`): 12 Kernpunkte zu
den acht Fragen in `key_points.csv`. Bewertet ist noch nichts (`scoring_sheet.csv` leer, keine `scoring_checks.csv`).

### Vorheriger Stand (13.10.2026, `b75d188`, nur Guide)

Ersetzt durch [ADR 0025](../adr/0025-korpus-guide-api-styleguide.md); die beiden Proben unten liefen auf diesem Stand.

#### Snapshot

| Feld | Wert |
|---|---|
| Repository | `vuejs/docs` (https://github.com/vuejs/docs) |
| Commit | `b75d188ab16bf83bd1f364a77dfd2315be8f3fa4` (Commit-Datum 31.07.2026) |
| Datum des Snapshots | 13.10.2026 (Datensatz in der Git-Historie: `git show fe371c1:docs/corpus_snapshot.txt`) |
| Verwendete Pfade | `src/guide/` ([ADR 0019](../adr/0019-korpus-ausschnitt.md)); Dateiliste: `git show fe371c1:docs/corpus_manifest.csv` |
| Anzahl Dateien | 52 |
| Gesamtumfang (Tokens) | 117.594 nach Preprocessing (`cl100k_base`); 560 Abschnitte (H1–H3) |

#### Chunking

| Strategie | Chunks | Tokens min / Mittel / max |
|---|---:|---|
| C1 | 260 | 11 / 452 / 500 |
| C2 | 305 | 108 / 469 / 500 |
| C3 | 493 | 50 / 239 / 799 |

#### Embedding

Einmaliger Lauf am 13.10.2026 (`src/embed.py`; Protokoll lokal archiviert:
`data/processed/archive_vue_2026-10-18/embedding_runs.jsonl`, Zeilen vom 13.10.2026). Die von OpenAI abgerechneten
Tokens stimmen exakt mit der eigenen Zählung (`cl100k_base`, `src/tokens.py`) überein. Weitere Läufe am selben Tag
nutzten die gespeicherten Referenzvektoren ohne API-Aufruf
([ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)).

| Strategie | Vektoren | Eingabe-Tokens | Kosten (USD) | Vektordatei |
|---|---:|---:|---:|---:|
| C1 | 260 | 117.594 | 0,0153 | 6,0 MB |
| C2 | 305 | 142.894 | 0,0186 | 7,0 MB |
| C3 | 493 | 117.594 | 0,0153 | 13,0 MB |
| Summe | 1.058 | 378.082 | 0,0492 | 26,0 MB |

Dateigrößen gemessen am 13.10.2026; die Vektordateien wurden am 14.10.2026 überschrieben.

Prüfung: Für je 25 zufällig gewählte Chunk-Vektoren je Strategie stimmt Chromas Top-5 mit der exakten
Kosinus-Rangfolge überein, der Chunk selbst steht auf Rang 1 (75/75); Vektornormen 0,9994–1,0007.

Wiederholungsmessung (13.10.2026, 2.706 Tokens, 0,00035 USD): je drei Chunks pro Strategie erneut eingebettet;
Kosinus zum gespeicherten Vektor ≥ 0,99996 (7 von 9 bitgleich), ähnlichster anderer Chunk ≤ 0,84. Daraus der
Schwellwert 0,999 der Modellstand-Prüfung ([ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)).

#### Schwierigkeitsprobe 1: einfache Fragen (Pilot, 14.10.2026, alter Korpus)

Zweck: prüfen, ob das Retrieval auf dem Korpus schwer genug ist, um die Strategien zu unterscheiden (kein
Deckeneffekt). Acht Pilotfragen in `data/pilot/` (alle fünf Fragetypen, fünf Korpusbereiche, je ein relevanter
Abschnitt); sie sind **nicht** Teil des Fragenkatalogs. Auswertung: `scripts/difficulty_probe.py`; Kosten 0,0004 USD.

| Strategie | Hit@5 | MRR | Precision@5 | Recall@5 |
|---|---:|---:|---:|---:|
| C1 | 1,00 | 0,94 | 0,23 | 1,00 |
| C2 | 1,00 | 0,79 | 0,30 | 1,00 |
| C3 | 1,00 | 0,94 | 0,23 | 1,00 |

Befund: Bei einfachen Fragen mit genau einem passenden Abschnitt finden alle Strategien die Antwort (Hit@5 und
Recall@5 = 1,00, Deckeneffekt); Unterschiede zeigen sich nur in Rang und Präzision (MRR, Precision@5). Folgerung für den
Fragenkatalog: [Fragenkatalog](question-catalogue.md#regeln-für-annotation-und-aufbau).

#### Schwierigkeitsprobe 2: schwere Fragen (Pilot, 14.10.2026, alter Korpus)

Zweck: prüfen, ob der Deckeneffekt aus Probe 1 an den Fragen oder am Korpus liegt, bevor über eine Erweiterung des
Korpus (ADR 0019) entschieden wird. 16 bewusst schwere Pilotfragen in `data/pilot/hard/`, **nicht** Teil des
Fragenkatalogs, drei Arten (Feld `notes`):

- **multi-section** (5): Die Antwort braucht zwei oder drei Abschnitte, teils auf verschiedenen Seiten.
- **detail** (4): Die Antwort ist ein einzelnes Detail in einem kurzen Abschnitt (Version, Option, Konvention).
- **paraphrase** (7): Die Frage beschreibt ein Symptom ohne die Begriffe der Überschrift.

Auswertung: `uv run python scripts/difficulty_probe.py data/pilot/hard`; Kosten 0,0004 USD (391 Frage-Tokens plus
2.706 Tokens Modellstand-Prüfung, Kosinus 0,99996). Metriken: [Evaluation](evaluation.md#retrieval-evaluation).

Werte mit der blinden Annotation (vor dem Retrieval festgelegt; Hauptwerte):

| Strategie | Hit@5 | MRR | Precision@5 | Recall@5 |
|---|---:|---:|---:|---:|
| C1 | 1,00 | 0,74 | 0,30 | 0,97 |
| C2 | 0,94 | 0,67 | 0,35 | 0,89 |
| C3 | 0,94 | 0,72 | 0,24 | 0,85 |

Nach Fragenart (MRR / Recall@5, blind):

| Art | C1 | C2 | C3 |
|---|---|---|---|
| multi-section (n = 5) | 0,87 / 0,90 | 0,85 / 0,83 | 0,67 / 0,73 |
| detail (n = 4) | 0,88 / 1,00 | 0,71 / 1,00 | 0,88 / 1,00 |
| paraphrase (n = 7) | 0,58 / 1,00 | 0,52 / 0,86 | 0,67 / 0,86 |

Annotation nachträglich ergänzt (nur Sensitivität, keine Evidenz; [ADR 0027](../adr/0027-blinde-annotation.md)):
Die Durchsicht aller Chunks, die vor
dem ersten relevanten Treffer rangierten, ergab drei Abschnitte, die eine richtige (Teil-)Antwort enthalten, aber
fehlten: `D046#cross-request-state-pollution` (H04), `D027#dom-update-timing` (H10, `nextTick()` als Alternative) und
`D033#how-reactivity-works-in-vue` (H16, nennt den Verlust der Reaktivität beim Destrukturieren wörtlich). Regel: Ein
Abschnitt ist relevant, wenn er eine richtige Antwort oder Teilantwort enthält; nicht ergänzt wurden daher
`D004#potential-dangers` (allgemein, ohne `v-html`) und `D034` (veraltete Reactivity Transform). Werte nach der
Ergänzung: C1 1,00 / 0,83 / 0,35 / 0,94, C2 0,94 / 0,72 / 0,40 / 0,85, C3 1,00 / 0,75 / 0,28 / 0,89
(Hit@5 / MRR / P@5 / R@5). Beide Läufe stehen in `data/pilot/hard/runs.jsonl` (verschiedene SHA-256 der Ground Truth).

Befund:

- Der Deckeneffekt liegt an den Fragen, nicht am Korpus: Auf demselben Korpus trennen schwere Fragen die Strategien
  (blind: MRR 0,67–0,74, Recall@5 0,85–0,97 statt 0,79–0,94 und 1,00 in Probe 1). Hit@5 bleibt nahe 1 und taugt allein nicht
  zur Unterscheidung.
- Fragen mit mehreren Abschnitten sind für C3 am schwersten (Recall@5 0,73): Strukturtreue Chunks sind kleiner und
  zahlreicher, sodass fünf Plätze seltener alle Teilantworten abdecken.
- C2 verfehlt bei H11 (`v-model.lazy`, 72-Token-Abschnitt) als einzige Strategie jeden relevanten Chunk.
- n = 16 ist zu klein für Signifikanzaussagen; die Werte zeigen nur, dass der Katalog die Strategien trennen kann.

Folgerung für den Fragenkatalog (fester Anteil schwerer Fragen, Annotation über den ganzen Korpus):
[Fragenkatalog](question-catalogue.md#regeln-für-annotation-und-aufbau); für die Auswertung (MRR und Recall@5 neben
Hit@5): [Evaluation](evaluation.md#retrieval-evaluation). Die Lücken oben fand erst die
Durchsicht nach dem Retrieval.

Zwischenfall: Der erste Lauf brach ab, weil Chroma für eine C3-Frage einen echten Top-5-Treffer (`C3_D034_0006`, Kosinus
0,325) nicht lieferte; die Prüfung gegen die exakte NumPy-Rangfolge
([ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)) verhinderte ein falsches Ergebnis. Nicht reproduzierbar:
12 neue Prozesse gegen den Index, 10 Neuaufbauten mit Abfrage im getrennten Prozess und 1.200 leicht verrauschte
Anfragen ergaben keine Abweichung; alle Vektoren waren erreichbar. Chroma schreibt die Indexdateien beim Lesen neu,
sodass der Zustand des Abbruchs nicht erhalten ist. Die Kosten des abgebrochenen Laufs (gleiche Größenordnung, rund
0,0004 USD) sind nicht protokolliert, weil `retrieve.py` erst am Ende in `runs.jsonl` schreibt.
