# Datenartefakte und Formate

> Seitentyp: Nachschlagen (reference). Stand: 20.10.2026. Übersicht: [Dokumentation](../README.md).

Dateinamen und Pfade kommen aus [`src/config.py`](../../src/config.py) ([Konfiguration](configuration.md)); welche
Dateien versioniert sind: [Versioniert und ignoriert](#versioniert-und-ignoriert). Korpus-Beispiele und der
`embed.py`-Eintrag sind echte Datensätze auf `ef977f4` ([Korpus](corpus.md)). Katalog- und Ergebnisbeispiele nutzen
echte e2e-IDs aus `sections.jsonl` mit Platzhaltern (`…`) für Texte; ihre Zahlen zeigen nur die Form, denn einen Lauf
des Hauptexperiments gibt es noch nicht ([Plan](../plan.md#stand)). Der `retrieve.py`-Eintrag stammt aus einem
historischen Pilot-Set ([Pilot-Sets](#pilot-sets)). Texte gekürzt (`...`), Prüfsummen gekürzt
(`…`).

## Korpus

**`docs/corpus_snapshot.txt`** (geschrieben von `snapshot.py`): Kopfzeilen `schlüssel: wert`, eine Leerzeile, dann je
Datei `SHA-256  pfad` (zwei Leerzeichen; Pfad relativ zu `docs/`, sortiert; Seiten und die beiden mitkopierten
Dateien `docs.json` und `snippets/model-provider.jsx`).

```
repository: https://github.com/tester-army/e2e.git
commit: ef977f4856da009cac26d78d2e9bb14e5991ee41
commit_date: 2026-10-17T16:12:13+02:00
snapshot_date: 2026-10-18
root: docs
files: 62

2b64177a…f8671c8  agent-steps.mdx
```

**`data/raw/e2e_docs_snapshot/`** (`config.DATA_RAW`, geschrieben von `snapshot.py`): die Seiten (`*.mdx`) und die
beiden mitkopierten Dateien mit denselben relativen Pfaden wie unter `docs/` im Repository; `snapshot.py` leert den
Ordner vorher (bis auf Dateien, die mit `.` beginnen, z. B. `.gitkeep`).

**`docs/corpus_manifest.csv`** (geschrieben von `preprocess.py`): Spalten und Beispielzeilen in
[Korpus](corpus.md#korpusmanifest-corpus_manifestcsv).

**`documents.jsonl`** (`area` = Gruppe der Navigation, [Korpus](corpus.md#bereiche); `text` nach `ingest.py` das
rohe MDX, nach `preprocess.py` das umgewandelte Markdown)
```json
{"doc_id":"D031","path":"migrate/detox.mdx","title":"From Detox","area":"Migrate","text":"# From Detox\n\nUse your existing app build and testIDs with s...","tokens":2409}
```

- `doc_id` = Position der Seite in der nach Pfad sortierten Seitenliste (`D001` = `agent-steps.mdx`, `D002` =
  `agents.mdx`, …). Jede Änderung der Seitenmenge nummeriert die folgenden Seiten um; Annotationen eines anderen
  Korpusstands werden über Pfad und Anker umgeschrieben, nie von Hand (so am 14.10.2026 mit
  `scripts/remap_pilot.py`, [ADR 0025](../adr/0025-korpus-guide-api-styleguide.md); das Skript gilt nur für den
  Vue-Korpus).
- `preprocess.py` schreibt `documents.jsonl` an Ort und Stelle neu und bricht ab, wenn die Datei schon umgewandelt
  ist; vor einem zweiten Lauf erst `ingest.py` ausführen.

**`sections.jsonl`** (ein Eintrag je H1–H3-Abschnitt; Spanne in Tokens des bereinigten `text`, Ende exklusiv; ein
Abschnitt reicht bis zur nächsten Überschrift gleicher oder höherer Ebene; [ADR 0019](../adr/0019-korpus-ausschnitt.md),
Anker nach [ADR 0042](../adr/0042-mdx-umwandlung.md))
```json
{"section_id":"D013#let-the-agent-use-the-app","doc_id":"D013","anchor":"let-the-agent-use-the-app","title":"Let the agent use the app","level":2,"start_token":639,"end_token":710}
```

`chunking.py` bricht ab, wenn `sections.jsonl` nicht zum Text in `documents.jsonl` passt (etwa nach `ingest.py` ohne
anschließendes `preprocess.py`).

## Chunks

**`chunks_c1.jsonl`** (analog `chunks_c2.jsonl`, `chunks_c3.jsonl`)
```json
{"chunk_id":"C1_D001_0001","doc_id":"D001","strategy":"fixed_500_no_overlap","text":"...","start_token":0,"end_token":500}
```

- `chunk_id` = `{Strategie}_{doc_id}_{laufende Nummer, vierstellig}`; `strategy` = Wert aus `config.STRATEGY_IDS`.
- `text` ist genau der Ausschnitt `[start_token, end_token)` des Dokumenttexts.
- `start_token`/`end_token` von Chunks und Abschnitten zählen beide über `src/tokens.py` (`cl100k_base`) und sind
  daher direkt vergleichbar ([ADR 0019](../adr/0019-korpus-ausschnitt.md), [ADR 0021](../adr/0021-c3-grenzen.md)).

**`chunks_k1.jsonl`** (Kontrolle K1, [ADR 0026](../adr/0026-c3-vergleichbarkeit.md)): gleiches Schema, `chunk_id`
`K1_…`, `strategy` aus `config.CONTROL_STRATEGIES` (`fixed_<K1_CHUNK_SIZE>_no_overlap`).

## Vektoren

**`embeddings_c1.npz`** (analog c2/c3 und `embeddings_k1.npz`; `data/processed/`;
[ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)): Arrays `model` (Embedding-Modell), `ids` (Chunk-IDs in
Dateireihenfolge), `texts` (Chunk-Texte), `vectors` (float32, n × `EMBEDDING_DIMENSIONS`). Wiederverwendet nur, wenn
Modell, IDs und Texte unverändert sind; sonst bricht der Lauf ab, bis die Datei bewusst gelöscht wird.

**`query_embeddings.npz`** (`data/evaluation/` bzw. je Pilot-Set): Arrays `model`, `ids` (Frage-IDs), `texts`
(Fragen), `vectors`.

**`chroma_db/`** (`config.CHROMA_DIR`, Chroma-Index): je Strategie eine Collection aus `config.CHROMA_COLLECTIONS`
(`rag_c1`–`rag_c3`) bzw. `config.CONTROL_COLLECTIONS` (`rag_k1`), die `embed.py` aus den Vektoren der `.npz`-Datei
aufbaut; Metadaten je Chunk `doc_id`, `start_token`, `end_token`. `retrieve.py` bricht ab, wenn eine Collection nicht
so viele Einträge hat wie die Chunk-Datei.

## Laufprotokoll

**`embedding_runs.jsonl`** (`data/processed/`; ein Eintrag je Lauf von `embed.py` oder `retrieve.py`; Kosten nach
[ADR 0008](../adr/0008-kosten-als-variable.md)). Pilot-Sets nutzen dasselbe Format in `runs.jsonl`.

- `input_tokens`/`cost_usd`: nur die eigenen Texte des Schritts (Chunks einer Strategie bzw. Fragen).
- `canary_*`: Modellstand-Prüfung getrennt davon (`canary_min_cosine` = niedrigste Kosinus-Ähnlichkeit, `null` wenn
  keine Prüfung nötig war), damit sie die Kosten einer Strategie nicht verfälscht.
- `api_called`: `false`, wenn gespeicherte Vektoren wiederverwendet wurden.

`embed.py` (eine Zeile je Strategie; Lauf C2 vom 18.10.2026, alle Läufe im
[Experiment-Protokoll](experiment-record.md#embedding-e2e)):
```json
{"date":"2026-10-18","model":"text-embedding-3-large","openai_sdk":"2.44.0","chromadb":"1.5.9","step":"embed","strategy":"C2","dimensions":3072,"vectors":642,"vector_bytes":7888896,"inputs_sha256":{"chunks_c2.jsonl":"5c65075b…"},"canary_min_cosine":0.9999860525131226,"input_tokens":308580,"cost_usd":0.0401154,"canary_input_tokens":1499,"canary_cost_usd":0.00019487,"api_called":true}
```

`retrieve.py` (eine Zeile je Lauf; `strategy` listet alle Strategien des Laufs, `vectors`/`dimensions` beziehen sich
auf die Fragen, `inputs_sha256` belegt alle Eingaben, u. a. die Ground Truth nach
[ADR 0017](../adr/0017-fragenkatalog.md); seit 17.10.2026 zusätzlich `outputs_sha256` mit der Prüfsumme der
geschriebenen Ergebnisdatei, gegen die `generate.py` prüft (Pflicht für den Hauptlauf; ältere Pilot-Einträge
ohne sie werden nur an den Eingaben geprüft) ([ADR 0033](../adr/0033-antwortmodell.md)); Beispiel:
erster Lauf des Pilot-Sets `hard` vom 14.10.2026 auf dem Vue-Korpus, noch ohne `outputs_sha256`):
```json
{"date":"2026-10-14","model":"text-embedding-3-large","openai_sdk":"2.44.0","chromadb":"1.5.9","step":"retrieve","strategy":"C1,C2,C3","dimensions":3072,"vectors":16,"inputs_sha256":{"questions.csv":"6f4a2e9f…","ground_truth.csv":"f9ddb34b…","sections.jsonl":"…","query_embeddings.npz":"…","chunks_c1.jsonl":"…","chunks_c2.jsonl":"…","chunks_c3.jsonl":"…","embeddings_c1.npz":"…","embeddings_c2.npz":"…","embeddings_c3.npz":"…"},"canary_min_cosine":0.9999592304229736,"input_tokens":391,"cost_usd":5.083e-05,"canary_input_tokens":2706,"canary_cost_usd":0.00035178,"api_called":true}
```

Ein Lauf mit `--control` steht mit `"strategy":"K1"` und den K1-Dateien in `inputs_sha256` im Protokoll.

`evaluate_retrieval.py` (lokaler Schritt ohne API, geschrieben von `run_log.append_step_run`; ein Eintrag je Lauf in
`embedding_runs.jsonl`, mit `--set DIR` in der `runs.jsonl` des Sets): `date`, `step` (`evaluate_retrieval`),
`strategy` (`C1,C2,C3` bzw. `K1` mit `--control`), `inputs_sha256` (`retrieved_results*.csv`, Fragen, Ground Truth,
`sections.jsonl`, Chunk-Dateien) und `outputs_sha256` mit `retrieval_scores*.csv`. `analyse.py` prüft die Datei gegen
diesen Eintrag.

**`generation_runs.jsonl`** (`data/evaluation/`; Pilot-Sets schreiben dieselben Einträge in ihre `runs.jsonl`;
[ADR 0033](../adr/0033-antwortmodell.md)). Jeder Eintrag beginnt mit `date`; die Einträge mit API-Aufrufen tragen
danach die gepinnten Einstellungen und enden mit `prompt_tokens`, `completion_tokens`, `cost_usd`.

| `step` | `strategy` | geschrieben von | weitere Felder |
|---|---|---|---|
| `generate` | `C1,C2,C3` | `generate.py`, nur nach einem erfolgreichen Lauf; ein abgebrochener Lauf schreibt nichts | siehe unten |
| `scaffold` | `C1,C2,C3` | `evaluate_answers.py --mode scaffold`, nur bei neu erzeugtem Bogen | `scoring`, `codes` (Zahl der Codes), `outputs_sha256` mit `scoring_items.jsonl` |
| `scaffold` | `K0` | `evaluate_answers.py --mode scaffold --control` ([ADR 0041](../adr/0041-kontrolle-k0.md)) | `scoring`, `codes` (Zahl der K0-Codes), `outputs_sha256` mit `scoring_items_control.jsonl` |
| `key_points` | `C1,C2,C3` | Einfrieren der Kernpunkte auf der Bewertungsseite (siehe `key_points.csv`) | `outputs_sha256` mit `key_points.csv` und `scoring_items.jsonl` |
| `summarise` | `C1,C2,C3` | `evaluate_answers.py --mode summarise` (auch mit `--set`; Pilot-Sets von vor diesem Eintrag haben ihn nicht, `analyse.py --set` wertet sie mit Hinweis aus, [ADR 0044](../adr/0044-statistische-auswertung.md)) | `inputs_sha256` (Bogen, Schlüssel, `scoring_checks.csv`, `key_points.csv`), `outputs_sha256` mit `scores.csv` |
| `summarise_control` | `K0` | `evaluate_answers.py --mode summarise --control` | `inputs_sha256` (Bogen, Prüfungen und Kernpunkte von K0, `scores.csv`), `outputs_sha256` mit `scores_control.csv` |
| `ragas` | `C1,C2,C3` | `ragas_eval.py` ([ADR 0047](../adr/0047-ragas-als-triangulation.md)), nur nach einem erfolgreichen Lauf | siehe unten |
| `ragas_repeat` | `C1,C2,C3` | `ragas_eval.py --repeat` (nur Pilot-Sets), nur nach einem erfolgreichen Lauf | wie `ragas`, `outputs_sha256` mit `ragas_scores_repeat.csv` |
| `closed_book_screen` | (kein Feld) | `catalogue.py screen` ([ADR 0040](../adr/0040-closed-book-pruefung.md)) | siehe unten |

`scoring` = `config.SCORING_METHOD` (`rules`): das Scaffold ist nur regelbasiert zu bewerten
([ADR 0036](../adr/0036-regelbasierte-bewertung-verpflichtend.md)); ältere Einträge haben das Feld nicht.

```json
{"date":"…","step":"scaffold","strategy":"C1,C2,C3","scoring":"rules","codes":…,"outputs_sha256":{"scoring_items.jsonl":"…"}}
```

Felder des Eintrags `generate`:

- `model`, `reasoning_effort`, `temperature`, `seed`, `max_completion_tokens`: die gepinnten Einstellungen; `model_reported`:
  das Modell, das die API für alle Antworten des Laufs gemeldet hat; `model_created`: Erstellungszeitpunkt des
  Modellobjekts (ISO 8601, UTC), vor und nach dem Lauf gleich; `system_fingerprint`: die gemeldete
  Backend-Konfiguration (`null`, wenn die API keine meldet).
- `openai_sdk`, `date`, `step` (`generate`), `strategy` (`C1,C2,C3`), `answers` (Zahl der Antworten C1–C3),
  `control_answers` (Zahl der K0-Antworten, [ADR 0041](../adr/0041-kontrolle-k0.md)).
- `inputs_sha256`: `retrieved_results.csv`, Fragen, Ground Truth und Chunk-Dateien; `outputs_sha256`:
  `generated_answers.csv` und `generated_answers_control.csv`.
- `prompt_tokens`, `completion_tokens`, `cost_usd` für den Lauf, `by_strategy` dieselben drei je Strategie und für K0
  ([ADR 0008](../adr/0008-kosten-als-variable.md)).

Der Eintrag wird geprüft, bevor ein späterer Schritt auf ihm aufbaut: `evaluate_answers.py --mode scaffold` vergleicht
`questions.csv`, `ground_truth.csv`, die drei Chunk-Dateien und `generated_answers.csv`,
`evaluate_answers.py --mode scaffold --control` vergleicht `questions.csv`, `ground_truth.csv` und
`generated_answers_control.csv` mit den aktuellen Dateien. `retrieved_results.csv` prüft `generate.py` schon vor dem
Lauf gegen den `retrieve.py`-Eintrag; im `generate`-Eintrag ist die Prüfsumme nur aufgezeichnet.

Bisher gibt es keinen `generate`-Lauf des Hauptexperiments. Der einzige echte Eintrag steht im historischen Pilot-Set
`data/pilot/hard/runs.jsonl` (17.10.2026, vor K0: ohne `control_answers`, ohne `generated_answers_control.csv` in
`outputs_sha256`, `by_strategy` ohne K0). Form des Eintrags (Zahlen nur zur Form):

```json
{"date":"…","model":"gpt-6-luna","reasoning_effort":"none","temperature":0.0,"seed":20261017,"max_completion_tokens":1024,"openai_sdk":"2.44.0","step":"generate","strategy":"C1,C2,C3","model_reported":"…","model_created":"…","system_fingerprint":"…","answers":144,"control_answers":48,"inputs_sha256":{"retrieved_results.csv":"…","questions.csv":"…","ground_truth.csv":"…","chunks_c1.jsonl":"…","chunks_c2.jsonl":"…","chunks_c3.jsonl":"…"},"outputs_sha256":{"generated_answers.csv":"…","generated_answers_control.csv":"…"},"by_strategy":{"C1":{"prompt_tokens":0,"completion_tokens":0,"cost_usd":0.0},"C2":{"…":"…"},"C3":{"…":"…"},"K0":{"…":"…"}},"prompt_tokens":0,"completion_tokens":0,"cost_usd":0.0}
```

Felder der Einträge `ragas` und `ragas_repeat` (`run_log.ragas_record`, Reihenfolge wie geschrieben; Pilot-Beispiel in
[Experiment-Protokoll](experiment-record.md#ragas-pilot-e2e-21102026)):

- `date`, `judge_model`, `embedding_model`, `reasoning_effort`, `temperature`, `seed`, `strictness`: die gepinnten
  Einstellungen aus `config.py` ([Konfiguration](configuration.md#ragas)); `ragas_version`, `openai_sdk`: installierte
  Versionen.
- `step` (`ragas` oder `ragas_repeat`), `strategy` (`C1,C2,C3`), `rows` (Zahl der Zeilen der Ergebnisdatei).
- `model_reported`: das Modell, das die API für alle Richteraufrufe gemeldet hat; `model_created`: Erstellungszeitpunkt
  des Modellobjekts (ISO 8601, UTC), vor und nach dem Lauf gleich; `system_fingerprint`: die gemeldete
  Backend-Konfiguration (`null`, wenn die API keine meldet). Meldet die API mehrere Modelle oder Fingerabdrücke, bricht
  der Lauf ohne Schreiben ab ([ADR 0033](../adr/0033-antwortmodell.md)).
- `nan_counts`: je Metrik die Zahl der Zeilen mit leerer Zelle (Gründe in `nan_reasons` der Ergebnisdatei).
- `inputs_sha256`: `generated_answers.csv`, `retrieved_results.csv`, Fragen, Ground Truth und die drei Chunk-Dateien;
  auf dem Hauptkatalog zusätzlich `scores.csv` (RAGAS läuft erst nach `summarise`). `outputs_sha256`: die
  Ergebnisdatei des Schritts.
- `judge_prompt_tokens`, `judge_completion_tokens`, `embedding_tokens` (die Embeddings der Response Relevancy, nur sie
  gehen an das Embedding-Modell); `judge_cost_usd` (nach `RAGAS_JUDGE_PRICE_*`), `embedding_cost_usd`
  (nach `EMBEDDING_PRICE_PER_MTOK`) und `cost_usd` (Summe) in USD.

`ragas_eval.py --repeat` verlangt, dass der `ragas`-Eintrag zur aktuellen `ragas_scores.csv` passt; `analyse.py` prüft
beide Dateien gegen ihren Eintrag (`analysis_data._load_ragas`).

Der Eintrag `closed_book_screen` hat die gepinnten Einstellungen und `openai_sdk` wie `generate`, dann `answers` (Zahl
der abgerechneten Antworten dieses Aufrufs), `model_reported` und `system_fingerprint` als **sortierte Listen** aller
gemeldeten Werte (fehlender Fingerprint als `""`), `outputs_sha256` mit `closed_book_screen.csv`; er hat weder
`strategy` noch `inputs_sha256`. `screen` schreibt ihn, sobald mindestens eine Antwort abgerechnet wurde, auch nach
einem Abbruch (API-Fehler, abgeschnittene oder leere Antwort).

```json
{"date":"…","model":"gpt-6-luna","reasoning_effort":"none","temperature":0.0,"seed":20261017,"max_completion_tokens":1024,"openai_sdk":"2.44.0","step":"closed_book_screen","answers":…,"model_reported":["…"],"system_fingerprint":["…"],"outputs_sha256":{"closed_book_screen.csv":"…"},"prompt_tokens":…,"completion_tokens":…,"cost_usd":…}
```

## Fragen und Ground Truth

**`questions.csv`**
```
question_id,question,type,difficulty,notes
Q001,"How do I …?",procedural,single,
```

`type` und `difficulty` nehmen nur die Werte aus [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) an (`config.QUESTION_TYPES`,
`config.QUESTION_CLASSES`); die Pilot-Sets sind davon ausgenommen.

**`ground_truth.csv`**
```
question_id,expected_answer,relevant_doc_ids,relevant_section_ids
Q001,"…",D013,D013#install-the-skill
```

Mehrere IDs in `relevant_doc_ids` bzw. `relevant_section_ids` werden durch `config.ID_SEPARATOR` (`;`) getrennt.

`retrieve.py` prüft beide Dateien vor jedem Lauf und bricht bei Verstößen ab:

- Datei vorhanden und nicht leer; Kopfzeilen exakt wie oben, jede Zeile mit genau dieser Feldanzahl, keine doppelte
  `question_id`.
- Pflichtfelder nicht leer: in `questions.csv` alle außer `notes`, in `ground_truth.csv` alle.
- Jede Frage hat eine Ground-Truth-Zeile und umgekehrt; jede Frage hat mindestens eine `relevant_section_id`, und alle
  existieren in `sections.jsonl`; keine Abschnitts-ID steht in einer Zeile doppelt.
- `relevant_doc_ids` liegen im Korpus, keine steht in einer Zeile doppelt, und sie sind genau die Dokumente der
  `relevant_section_ids`.
- Nur für den Hauptkatalog: Der Freeze-Datensatz existiert und die Prüfsummen von `questions.csv`, `ground_truth.csv`,
  `sections.jsonl` und `documents.jsonl` passen ([ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md)).

**`section_index.md`** (`data/processed/`, geschrieben von `catalogue.py sections`): Überschrift `# Section index`,
eine Zeile mit Herkunft und Zahl der Abschnitte („Generated by … do not edit. 571 sections.“), dann eine
Markdown-Tabelle mit einer Zeile je Abschnitt in der Reihenfolge von `sections.jsonl`:
```
| section_id | area | path | heading path | tokens |
|---|---|---|---|---:|
| `D001#agent-steps` | Deep dive | agent-steps.mdx | How agent steps work | 1176 |
```
`area` ist der Bereich der Seite (Gruppe der Navigation, Feld `area` in `documents.jsonl`; [Korpus](corpus.md#bereiche));
`heading path` verbindet die Überschriften mit `config.CATALOGUE_HEADING_SEPARATOR` (` › `).

**`catalogue_freeze.json`** (`data/evaluation/`, geschrieben von `catalogue.py freeze`; [ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md)):
```
{
  "date": "…",
  "questions": 48,
  "types": {"factual": 12, "procedural": 12, "conceptual": 12, "comparative": 6, "limitation": 6},
  "classes": {"single": 12, "multi-section": 12, "detail": 12, "paraphrase": 12},
  "closed_book": {"dependent": 40, "known": 8},
  "sha256": {"questions.csv": "…", "ground_truth.csv": "…", "sections.jsonl": "…", "documents.jsonl": "…",
             "catalogue_plan.csv": "…", "catalogue_review.csv": "…", "closed_book_screen.csv": "…"}
}
```

Plan-, Durchsichts- und Closed-Book-Datei werden nur aufgezeichnet, und nur, sofern sie vorhanden sind; die Sperre in
`retrieve.py` prüft die vier übrigen Dateien. `closed_book` = Zahl der retrieval-abhängigen (`miss`) und
-unabhängigen (`hit`) Fragen.

**`catalogue_plan.csv`** (`data/evaluation/`, einmal geschrieben von `catalogue.py plan`, danach ändert
der Editor nur Status, Sprunggrund und Frage-ID sowie bei einem Sprung Slot und Klasse der nachrückenden Reservezeile; [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md), [ADR 0039](../adr/0039-stichprobenplan-e2e.md)): eine Zeile je gezogenem Abschnitt, je Bereich erst die Slots, dann
die Reserve in Ziehungsreihenfolge. Der unbenutzte Vue-Plan liegt unverändert in
`data/evaluation/archive_vue/catalogue_plan.csv` ([Experiment-Protokoll](experiment-record.md#stichprobenplan-e2e)).
```
area,draw,section_id,slot_id,class,status,skip_reason,question_id
Get started,1,D013#install-the-skill,S01,single,used,,Q001
Get started,2,D037#use-a-subscription-or-api-key,S02,multi-section,skipped,code-or-links,
Get started,3,D014#assertions,S02,multi-section,open,,
Get started,4,D037#add-an-agent-step,,,reserve,,
```
`status` ∈ `config.CATALOGUE_PLAN_STATUSES` (`open`, `used`, `skipped`, `reserve`); `skip_reason` ∈
`config.CATALOGUE_SKIP_REASONS`. `check` vergleicht den Plan mit einer frischen Ziehung und meldet jede andere
Abweichung als Fehler.

**`catalogue_review.csv`** (`data/evaluation/`; Claude hängt Zeilen mit `decision = open` an, die
Entscheidung trifft Jonas im Editor; [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md)):
```
round,question_id,kind,suggestion,section_id,decision,reason,date
1,Q001,missing_section,…,D006#install-the-skill,accepted,,…
1,Q002,wording,…,,rejected,…,…
```
`kind` ∈ `config.CATALOGUE_REVIEW_KINDS`, `decision` ∈ `config.CATALOGUE_REVIEW_DECISIONS`; `section_id` nur bei
`missing_section`, `reason` Pflicht bei `rejected`.

**`closed_book_screen.csv`** (`data/evaluation/`, nur für den Hauptkatalog; `catalogue.py screen` schreibt Antworten,
Jonas die Urteile im Editor; [ADR 0040](../adr/0040-closed-book-pruefung.md)): eine Zeile je Katalogfrage, sortiert
nach ID.
```
question_id,question_sha256,reference_sha256,answer,model,core_point,note,date
Q001,5d1f…,a90c…,…,gpt-6-luna,miss,,…
```
`question_sha256` = SHA-256 des Fragetexts, zu dem die Antwort gehört (geänderte Frage: `screen` fragt neu, das Urteil
wird geleert); `reference_sha256` = SHA-256 der Referenzantwort, zu der das Urteil gehört (geänderte Referenz: Urteil
offen). `model` = das von der API gemeldete Modell. `core_point` ∈ `config.CLOSED_BOOK_VERDICTS`: leer = offen,
`hit` = trifft den Kernpunkt (Frage retrieval-unabhängig), `miss` = trifft ihn nicht oder nur teilweise.

## Ergebnisse

**`retrieved_results.csv`** (`retrieve.py` läuft über alle Strategien C1–C3 und schreibt die Datei vollständig neu,
sortiert nach `question_id`, Strategie und Rang; [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)).
`score` = Kosinus-Ähnlichkeit mit sechs Nachkommastellen; `is_relevant` = `1`/`0` nach der Hauptregel
([Evaluation](evaluation.md#relevanz-eines-chunks)).
```
question_id,strategy,rank,chunk_id,score,is_relevant
Q001,C1,1,C1_D013_0001,0.840000,1
```

**`retrieved_results_control.csv`** (`retrieve.py --control`): gleiche Spalten, `strategy` immer `K1`.

**`retrieval_scores.csv`** (`evaluate_retrieval.py`, wird vollständig neu geschrieben; `retrieval_scores_control.csv`
mit `--control` für K1): eine Zeile je Frage, Strategie und Relevanzregel (`rule` = `main` oder `sensitivity`,
[Evaluation](evaluation.md#relevanz-eines-chunks)), sortiert nach `question_id`, Strategie, Regel. `hit` = `1`/`0`;
`reciprocal_rank`, `precision`, `recall` mit sechs Nachkommastellen; `context_tokens` = summierte Länge der k
abgerufenen Chunks (Kontext@k).
```
question_id,strategy,rule,hit,reciprocal_rank,precision,recall,context_tokens
Q001,C1,main,1,0.333333,0.600000,1.000000,610
```

**`generated_answers.csv`** (`generate.py`, alle Strategien C1–C3 in einem Lauf, sortiert nach `question_id` und
Strategie; wird nie überschrieben, [ADR 0033](../adr/0033-antwortmodell.md)). `answer` = Text der API unverändert;
`sources` = die top-k Chunk-IDs in Rangfolge, getrennt durch `;` (genau die Passagen des Prompts);
`prompt_tokens`/`completion_tokens` = Abrechnung der API (`usage`).
```
question_id,strategy,answer,sources,prompt_tokens,completion_tokens
Q001,C1,"...",C1_D013_0001;…,1200,180
```

**`generated_answers_control.csv`** (Kontrolle K0, im selben Lauf von `generate.py` mit dem Closed-Book-Prompt; Format
wie `generated_answers.csv`, `strategy` = `K0`, `sources` leer; wird nie überschrieben;
[ADR 0041](../adr/0041-kontrolle-k0.md)).

Blinde Bewertung ([ADR 0032](../adr/0032-blinde-rubrik-bewertung.md)): `evaluate_answers.py --mode scaffold` schreibt
aus `generated_answers.csv` vier Dateien (Lesepaket, Bogen, Schlüssel, `scoring_items.jsonl`), je Frage die drei
Antworten in der mit `config.SCORING_SEED` gemischten Reihenfolge unter den Codes `<question_id>-A`, `-B`, `-C`; Bogen
und Schlüssel werden nie überschrieben (liegen beide vor, stimmt der Schlüssel und sind die neuen Einträge byte-gleich
zur Prüfsumme im Laufprotokoll, schreibt ein erneuter Aufruf nur Lesepaket und `scoring_items.jsonl` neu).

**`scoring_packet.md`** (Lesepaket, nur Lesekopie; bewertet wird in der App über die Prüffragen): Hinweis, dann je
Frage `## Q001` mit Frage und Referenzantwort, je Code `### Q001-A` mit der Antwort und den Passagen, die das Modell
sah (`[Excerpt N]`, getrennt durch `---`, ohne Chunk-IDs), jeweils in einem eigenen Code-Block, dessen Zaun länger ist
als jede Backtick-Folge im Text.

**`scoring_sheet.csv`** (Bewertungsbogen: Kriterien ganze Zahlen 0–2, `notes` frei). Die Bewertungsseite schreibt die
Werte, abgeleitet aus den Prüffragen in `scoring_checks.csv`; `--mode summarise` lehnt jeden Wert ab, der von dieser
Ableitung abweicht ([ADR 0035](../adr/0035-regelbasierte-bewertung.md),
[ADR 0036](../adr/0036-regelbasierte-bewertung-verpflichtend.md)). Von Hand eingetragene Werte gelten nur für ein
Scaffold vor ADR 0036 ohne Kernpunkte und Prüffragen.
```
code,question_id,correctness,completeness,groundedness,no_hallucination,clarity,notes
Q001-A,Q001,2,1,2,2,2,…
```

**`scoring_key.csv`** (Schlüssel; erst `--mode summarise` entblindet mit ihm; ein erneutes `--mode scaffold` liest ihn
nur, um ihn maschinell mit dem berechneten zu vergleichen)
```
code,question_id,strategy
Q001-A,Q001,C3
```

**`scoring_items.jsonl`** (Daten der Bewertungsseite, [ADR 0034](../adr/0034-bewertung-in-der-app.md)): eine Zeile je
Code in der Reihenfolge des Lesepakets mit `code`, `question_id`, `question`, `reference_answer`, `answer` und
`excerpts` (Texte der Passagen in Rangfolge, ohne Chunk-IDs); keine Strategie.

**`key_points.csv`** (Kernpunkte je Frage, von Jonas vor der Bewertung geschrieben und eingefroren,
[ADR 0035](../adr/0035-regelbasierte-bewertung.md)): eine Zeile je Punkt, `point` ab 1 ohne Lücken
(1 = Kernaussage), höchstens `config.KEY_POINTS_MAX` je Frage, `text` einzeilig. Das Einfrieren schreibt einen
Eintrag `{"date":"…","step":"key_points","strategy":"C1,C2,C3","outputs_sha256":{"key_points.csv":"…","scoring_items.jsonl":"…"}}`
ins Laufprotokoll; er gilt nur für das Scaffold mit dieser `scoring_items.jsonl`. Nach einem neuen Scaffold werden die
Kernpunkte erneut eingefroren; das Einfrieren verweigert, solange eine `scoring_checks.csv` eines früheren Scaffolds
vorliegt.
```
question_id,point,text
Q001,1,"…"
```

**`scoring_checks.csv`** (Antworten auf die Prüffragen je bewertetem Code, in der Reihenfolge des Bogens,
[ADR 0035](../adr/0035-regelbasierte-bewertung.md)): `rules_version` = `config.RUBRIC_RULES_VERSION` (Zeilen mit
einer anderen Version lehnt `--mode summarise` ab); `points` = Markierungen der Kernpunkte in Punktreihenfolge, durch
`;` getrennt; übrige Spalten und Optionen nach [Evaluation](evaluation.md#regelbasierte-bewertung).
```
code,rules_version,points,declines,core_wrong,other_error,grounded,hallucination,answers_question,direct,wordy
Q001-A,2026-10-20,covered;missing,no,no,no,all,none,yes,yes,no
```

**`scores.csv`** (abgeleitet von `--mode summarise` aus Bogen und Schlüssel, wird neu geschrieben; sortiert nach
`question_id` und Strategie; Kriterien-Spalten = `config.RUBRIC_CRITERIA`, `total_score` = Mittel der Kriterien mit
einer Nachkommastelle, nach [Evaluation](evaluation.md#antwort-evaluation-rubrik-02))
```
question_id,strategy,correctness,completeness,groundedness,no_hallucination,clarity,total_score
Q001,C1,2,2,2,2,2,2.0
```

**Kontrolle K0** ([ADR 0041](../adr/0041-kontrolle-k0.md), [Evaluation](evaluation.md#kontrolle-k0)):
`evaluate_answers.py --mode scaffold --control` schreibt erst nach `scores.csv` für deren Fragen
`scoring_items_control.jsonl` (Einträge wie `scoring_items.jsonl`, Code `Q001-K0`, `excerpts` leer; versioniert, da es
kein Wiederherstellen gibt) und `scoring_sheet_control.csv`
(`code,question_id,correctness,completeness,no_hallucination,clarity,notes`); die Bewertungsseite schreibt
`scoring_checks_control.csv` (Kopf von `scoring_checks.csv` ohne `grounded`) und die abgeleiteten Werte in den Bogen.
`--mode summarise --control` schreibt `scores_control.csv` (Gesamtwert = Mittel der vier Kriterien mit zwei
Nachkommastellen):
```
question_id,strategy,correctness,completeness,no_hallucination,clarity,total_score
Q001,K0,1,0,2,2,1.25
```

**`ragas_scores.csv`** (`ragas_eval.py`, [ADR 0047](../adr/0047-ragas-als-triangulation.md); schreibt die Datei einmal
und nie über eine vorhandene; Pilot-Sets: `ragas_scores.csv` im Set-Ordner): eine Zeile je Frage und Strategie
C1–C3 (K0 bekommt kein RAGAS), sortiert nach `question_id`, dann Strategie in der Reihenfolge `config.STRATEGY_IDS`. Die
Spalten sind `config.RAGAS_METRICS` in dieser Reihenfolge, Werte von 0 bis 1 mit `config.RAGAS_DECIMALS` = 6
Nachkommastellen. Eine Metrik, die selbst NaN meldet (Verfahren: [Evaluation](evaluation.md#triangulation)), steht als
**leere Zelle**; `nan_reasons` nennt dann je leerer Zelle `<Metrik>: <Grund>`, mehrere durch `; ` getrennt, sonst leer.
Ein leerer Wert ohne Grund, ein Wert außerhalb 0–1 oder eine fehlende Zeile bricht den Lauf ohne Schreiben ab.
```
question_id,strategy,faithfulness,response_relevancy,context_precision,context_recall,nan_reasons
E01,C1,1.000000,0.776339,0.833333,1.000000,
```

**`ragas_scores_repeat.csv`** (`ragas_eval.py --repeat`, nur Pilot-Sets): gleiche Spalten, Zeilen und Sortierung; der
zweite Lauf über dieselben Antworten, nur für die Stabilität der Werte. Er steht unter dem Schritt `ragas_repeat` im
Laufprotokoll ([Laufprotokoll](#laufprotokoll)), das `ragas`-Protokoll bleibt das der ersten Datei.

## Auswertung (`output/`)

`analyse.py` ([ADR 0044](../adr/0044-statistische-auswertung.md)) schreibt jedes Mal alle Dateien neu; Ordner und
Namen: `config.OUTPUT_DIR`, `TABLES_DIR`, `FIGURES_DIR`, `ANALYSIS_FILE`. Ein Pilot-Set (`--set DIR`) schreibt
dieselbe Struktur nach `DIR/output/`, nie nach `output/`.

| Pfad | Inhalt |
|---|---|
| `output/tables/*.tex` | zwölf Tabellen nach den IU-Regeln (`table`-Umgebung mit kurzem Titel ohne Schlusspunkt, Label `tab:<Name>`, darunter `\source{Eigene Darstellung. …}` mit den Anmerkungen; Ausrichtung aus der Klasse; negative Werte mit typografischem Minus): `retrieval`, `retrieval_sensitivity`, `answers`, `tests` (nur die konfirmatorischen Tests), `tests_descriptive` (W und r der Maße ohne Test), `control_k0`, `correlation`, `efficiency`, `breakdown`, `ragas` (Mittel der vier RAGAS-Metriken je Strategie, Kendalls W), `ragas_effects` (paarweise r, Median-Differenz und n′), `ragas_agreement` (Spearmans ρ mit dem regelbasierten Gegenstück, [Evaluation](evaluation.md#triangulation)) (`report_tables.TABLE_NAMES`) |
| `output/figures/*.pdf` | acht Abbildungen in Endgröße: `recall`, `mrr`, `answers_distribution`, `heatmap`, `scatter_retrieval_answer`, `catalogue_composition`, `chunk_lengths`, `cost` (`report_figures.FIGURE_NAMES`, Inhalte: [Evaluation](evaluation.md#visualisierungen)) |
| `output/analysis.json` | alle Kennzahlen und Testergebnisse, sortierte Schlüssel, Gleitkommazahlen auf `config.JSON_DECIMALS` gerundet |

Oberste Schlüssel von `analysis.json`: `n_questions`, `alpha`, `retrieval` (Mittel je Relevanzregel `main` und
`sensitivity` und Strategie, einschließlich K1), `answers` (`means` je Strategie und Kriterium, einschließlich K0),
`confirmatory` (Friedman-Test, Holm-korrigierte p, Kendalls W und paarweise Wilcoxon-Tests je Metrik aus
`config.ANALYSIS_PRIMARY`), `descriptive_effects` (Effektstärken ohne p-Werte, getrennt nach Regel und `answers`),
`control_k0` (K0 gegen C1–C3, `null` ohne K0-Bewertung), `correlation` (Spearmans ρ je Strategie und `pooled`, dieses ohne `p`),
`efficiency` (Chunks, Längen, Kontext-Tokens, Indexgröße, Embedding- und Generierungskosten je Strategie),
`breakdown` (Fragetyp, Konstruktionsklasse und Closed-Book-Urteil), `ragas` (`means`, `nan_counts` und `effects` je Metrik, jeweils je Strategie; Kendalls W und r über die Fragen mit Wert in
allen Strategien, ohne p-Werte), `ragas_agreement` (Schlüssel `<Metrik>~<Gegenstück>`, je Strategie und `pooled` mit `rho`,
`n`, `testable`, ohne `p`; `rho` ist `null`, wenn eine Seite konstant ist), `ragas_stability` (je Metrik `n`,
`mean_abs_diff`, `rho`, `share_equal`; nur wenn `ragas_scores_repeat.csv` vorliegt, also bei Pilot-Sets) und
`notes` (entfallene Teile, Hinweise). Fehlt `ragas_scores.csv`, ist `ragas` `null`, `ragas_agreement` `null` und die
beiden Tabellen entfallen mit Hinweis.

## Pilot-Sets

Pilotproben (`scripts/difficulty_probe.py`) liegen in `config.PILOT_DIR` = `data/pilot/`; sie sind **nicht** Teil des
Fragenkatalogs. Aktuell ist das Set `e2e` (IDs `E01`–`E16`, nur Abschnitte außerhalb des Stichprobenplans) mit der
Übungskopie `e2e_jonas` (die ersten 3 Fragen; [Experiment-Protokoll](experiment-record.md#pilot-e2e-1920102026)).
Historisch sind die drei Vue-Sets: Sie entstanden vor [ADR 0038](../adr/0038-korpus-e2e.md), ihre Abschnitts- und
Chunk-IDs gibt es im e2e-Korpus nicht, sie lassen sich darauf nicht neu ausführen und bleiben als Aufzeichnung
erhalten. Ein Set ist ein Ordner mit den
Dateien der Evaluation unter denselben Namen und Formaten (Schritte mit `--set DIR`, `evaluate_answers.py` dazu
`--limit N` für die ersten N Fragen); das Laufprotokoll heißt `config.PILOT_RUNS_FILE_NAME` = `runs.jsonl` und hat
das Format von `embedding_runs.jsonl` und `generation_runs.jsonl`. Eine Closed-Book-Prüfung gibt es für Pilot-Sets
nicht. Welche Dateien versioniert sind: [Versioniert und ignoriert](#versioniert-und-ignoriert).

| Set | Fragen | vorhandene Dateien |
|---|---|---|
| `data/pilot/e2e/` | Pilot e2e: 16 Fragen `E01`–`E16` (je 4 `single`, `multi-section`, `detail`, `paraphrase`; `notes` = `pilot <Klasse>`), nur Abschnitte außerhalb des Stichprobenplans | `questions.csv`, `ground_truth.csv`, `query_embeddings.npz`, `retrieved_results.csv`, `retrieved_results_control.csv`, `generated_answers.csv`, `generated_answers_control.csv`, `key_points.csv`, `scoring_sheet.csv`, `scoring_key.csv`, `scoring_checks.csv`, `scoring_packet.md`, `scoring_items.jsonl`, `scores.csv`, `scoring_items_control.jsonl`, `scoring_sheet_control.csv`, `scoring_checks_control.csv`, `scores_control.csv`, `ragas_scores.csv`, `ragas_scores_repeat.csv`; `runs.jsonl` mit `retrieve`, `generate` (mit K0), `scaffold` (C1–C3 und `K0`), `key_points`, `ragas`, `ragas_repeat` |
| `data/pilot/e2e_jonas/` | Übungskopie: die ersten 3 Fragen von `e2e` (9 Antworten, gleiche Codes), Kernpunkte von Jonas | `questions.csv`, `ground_truth.csv`, `generated_answers*.csv`, `key_points.csv`, `scoring_sheet.csv`, `scoring_key.csv`, `scoring_packet.md`, `scoring_items.jsonl`; `runs.jsonl` (Kopie aus `e2e`, dazu `scaffold` mit `--limit 3` und `key_points`) |
| `data/pilot/` | Probe 1 (Vue, historisch): 8 Fragen `P01`–`P08` (`difficulty`: 3 `easy`, 4 `medium`, 1 `hard`; `notes` = `pilot`) | `questions.csv`, `ground_truth.csv`, `query_embeddings.npz`, `retrieved_results.csv`, `retrieved_results_control.csv`, `runs.jsonl` (nur `retrieve`) |
| `data/pilot/hard/` | Probe 2: 16 schwere Fragen `H01`–`H16` (`notes` = `pilot <Art>`: `multi-section`, `detail`, `paraphrase`), Annotation blind vor jedem Retrieval (Hauptwerte; [ADR 0027](../adr/0027-blinde-annotation.md)) | wie `data/pilot/`, dazu `generated_answers.csv`, `scoring_sheet.csv`, `scoring_key.csv`, `scoring_packet.md`, `scoring_items.jsonl`, `key_points.csv`; `runs.jsonl` mit `retrieve`, `generate` (17.10.2026), `scaffold` (ohne `scoring`) und `key_points` (18.10.2026) |
| `data/pilot/hard_posthoc/` | dieselben Fragen mit nachträglich ergänzter Annotation; nur Sensitivität, keine Evidenz ([ADR 0027](../adr/0027-blinde-annotation.md)) | wie `data/pilot/` |
| `data/pilot/hard/history/` | `ground_truth_b75d188.csv`: blinde Annotation mit den IDs des älteren Vue-Korpus (`b75d188`) | |

Ergebnisse der Proben: [Experiment-Protokoll](experiment-record.md#pilotproben-auf-dem-erweiterten-korpus-14102026).

## Versioniert und ignoriert

Einzige vollständige Liste der Datenartefakte nach `.gitignore`; alles, was hier nicht als ignoriert steht, ist
versioniert, sobald es existiert. Ignoriert sind Dateien, die sich aus versionierten Daten neu erzeugen lassen;
versioniert sind Primärdaten, die kein Lauf exakt wiederholt (Antworten, [ADR 0033](../adr/0033-antwortmodell.md);
Fragevektoren und Retrieval-Ergebnisse des Hauptlaufs, [ADR 0045](../adr/0045-retrieval-ergebnisse-versioniert.md)),
und alles, was Jonas schreibt oder entscheidet.

| Pfad | Inhalt | Status |
|---|---|---|
| `docs/corpus_snapshot.txt`, `docs/corpus_manifest.csv` | Snapshot-Datensatz, Korpusmanifest | versioniert |
| `data/raw/e2e_docs_snapshot/` | Rohseiten des Snapshots | ignoriert; nur `.gitkeep` versioniert |
| übrige Ordner in `data/raw/` (z. B. `vue_docs_snapshot/`) | alter Vue-Snapshot, nur lokal | ignoriert (`data/raw/*`) |
| `data/processed/` | `documents.jsonl`, `sections.jsonl`, `section_index.md`, `chunks_*.jsonl`, `embeddings_*.npz` | ignoriert; versioniert nur `.gitkeep` und das Laufprotokoll `embedding_runs.jsonl` ([ADR 0045](../adr/0045-retrieval-ergebnisse-versioniert.md)) |
| `data/processed/archive_vue_2026-10-18/` | Vue-Chunks, -Vektoren, -Laufprotokoll und alter Chroma-Index, nur lokal ([Experiment-Protokoll](experiment-record.md#embedding-e2e)) | ignoriert |
| `chroma_db/` (auch `*.chroma`) | Chroma-Index; entsteht beim ersten `embed.py` | ignoriert (ganzer Ordner, kein `.gitkeep`) |
| `data/evaluation/questions.csv`, `ground_truth.csv`, `catalogue_plan.csv`, `catalogue_review.csv`, `closed_book_screen.csv`, `catalogue_freeze.json` | Fragenkatalog und seine Aufzeichnungen | versioniert |
| `data/evaluation/archive_vue/catalogue_plan.csv` | unbenutzter Vue-Plan ([ADR 0039](../adr/0039-stichprobenplan-e2e.md)) | versioniert |
| `data/evaluation/query_embeddings.npz`, `retrieved_results.csv`, `retrieved_results_control.csv`, `retrieval_scores.csv`, `retrieval_scores_control.csv` | Fragevektoren und Retrieval-Ergebnisse des Hauptlaufs | versioniert ([ADR 0045](../adr/0045-retrieval-ergebnisse-versioniert.md)) |
| `data/evaluation/generated_answers.csv`, `generated_answers_control.csv`, `generation_runs.jsonl` | Antworten C1–C3 und K0, Laufprotokoll | versioniert |
| `data/evaluation/scoring_sheet.csv`, `scoring_key.csv`, `key_points.csv`, `scoring_checks.csv` | Primärdaten der Bewertung C1–C3 | versioniert |
| `data/evaluation/ragas_scores.csv` | RAGAS-Werte der Antworten C1–C3, einmal erzeugt (die Pilot-Dateien `ragas_scores*.csv` sind ebenfalls versioniert) ([ADR 0047](../adr/0047-ragas-als-triangulation.md)) | versioniert |
| `data/evaluation/scoring_items_control.jsonl`, `scoring_sheet_control.csv`, `scoring_checks_control.csv` | Bewertung K0 | versioniert |
| `data/evaluation/scoring_packet.md`, `scoring_items.jsonl`, `scores.csv`, `scores_control.csv` | Lesepaket, Daten der Bewertungsseite (vom Scaffold wiederherstellbar), entblindete Werte | ignoriert |
| `data/pilot/**/query_embeddings.npz`, `scoring_packet.md`, `scoring_items.jsonl`, `scores.csv`, `scores_control.csv` | dieselben Dateien in den Pilot-Sets | ignoriert; alle übrigen Pilotdateien versioniert |
| `data/pilot/**/output/` | Auswertung eines Pilot-Sets (`analyse.py --set`) | ignoriert |
| `output/tables/*.tex`, `output/analysis.json` | Tabellen und Kennzahlen der Auswertung | versioniert (nicht in `.gitignore`) |
| `output/figures/*.pdf` | Abbildungen der Auswertung | versioniert (Ausnahme von `*.pdf`) |
| `data/corpus_probe/docs/`, `probes/`, `sources/`, `questions/*-sections.json` | nachgebaute Seiten, Proben mit Abschnittstext, Klone der Kandidaten | ignoriert; übrige Dateien in `data/corpus_probe/` versioniert ([Korpusauswahl](corpus-selection.md#dateien-und-befehle)) |
| `*.pdf` | erzeugte Dokumente | ignoriert, außer `output/figures/*.pdf` (siehe oben) |
| `.env`, `.venv/`, `venv/`, `env/`, `__pycache__/`, `*.py[cod]`, `*.pyo`, `.vscode/`, `.ipynb_checkpoints/`, `.DS_Store` | Geheimnisse, Umgebung, Editor | ignoriert |

Die Vue-Verarbeitungsdateien, die nicht im Archivordner liegen (`documents.jsonl`, `sections.jsonl`), entstehen neu
aus `vuejs/docs` auf Commit `40aa88a` mit dem Code vor ADR 0038
([Experiment-Protokoll](experiment-record.md#snapshot-vuejs-bis-18102026)).
