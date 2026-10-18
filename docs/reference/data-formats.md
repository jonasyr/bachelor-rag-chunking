# Datenartefakte und Formate

> Seitentyp: Nachschlagen (reference). Stand: 17.10.2026. Übersicht: [Dokumentation](../README.md).

Dateinamen und Pfade kommen aus [`src/config.py`](../../src/config.py) ([Konfiguration](configuration.md)); welche
Dateien versioniert sind: [Werkzeuge und Repository](tooling.md#versioniert-und-ignoriert). Die Korpus-Beispiele sind echte
Datensätze auf `ef977f4` ([Korpus](corpus.md)); Katalog- und Ergebnisbeispiele stammen noch aus dem Vue-Korpus und
werden mit dem neuen Pilot ersetzt ([Plan](../plan.md#stand)). Texte gekürzt (`...`), Prüfsummen gekürzt (`…`).

## Korpus

**`docs/corpus_snapshot.txt`** (versioniert, geschrieben von `snapshot.py`): Kopfzeilen `schlüssel: wert`, eine
Leerzeile, dann je Datei `SHA-256  pfad` (zwei Leerzeichen; Pfad relativ zu `docs/`, sortiert; Seiten und die
beiden mitkopierten Dateien `docs.json` und `snippets/model-provider.jsx`).

```
repository: https://github.com/tester-army/e2e.git
commit: ef977f4856da009cac26d78d2e9bb14e5991ee41
commit_date: 2026-10-17T16:12:13+02:00
snapshot_date: 2026-10-18
root: docs
files: 62

2b64177a…f8671c8  agent-steps.mdx
```

**`docs/corpus_manifest.csv`** (versioniert, geschrieben von `preprocess.py`): Spalten und Beispielzeilen in
[Korpus](corpus.md#korpusmanifest-corpus_manifestcsv).

**`documents.jsonl`** (`area` = Gruppe der Navigation, [Korpus](corpus.md#bereiche); `text` nach `ingest.py` das
rohe MDX, nach `preprocess.py` das umgewandelte Markdown)
```json
{"doc_id":"D031","path":"migrate/detox.mdx","title":"From Detox","area":"Migrate","text":"# From Detox\n\nUse your existing app build and testIDs with s...","tokens":2409}
```

**`sections.jsonl`** (ein Eintrag je H1–H3-Abschnitt; Spanne in Tokens des bereinigten `text`, Ende exklusiv; ein
Abschnitt reicht bis zur nächsten Überschrift gleicher oder höherer Ebene; [ADR 0019](../adr/0019-korpus-ausschnitt.md))
```json
{"section_id":"D013#let-the-agent-use-the-app","doc_id":"D013","anchor":"let-the-agent-use-the-app","title":"Let the agent use the app","level":2,"start_token":639,"end_token":710}
```

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

## Laufprotokoll

**`embedding_runs.jsonl`** (`data/processed/`; ein Eintrag je Lauf von `embed.py` oder `retrieve.py`; Kosten nach
[ADR 0008](../adr/0008-kosten-als-variable.md)). Pilot-Sets nutzen dasselbe Format in `runs.jsonl`.

- `input_tokens`/`cost_usd`: nur die eigenen Texte des Schritts (Chunks einer Strategie bzw. Fragen).
- `canary_*`: Modellstand-Prüfung getrennt davon (`canary_min_cosine` = niedrigste Kosinus-Ähnlichkeit, `null` wenn
  keine Prüfung nötig war), damit sie die Kosten einer Strategie nicht verfälscht.
- `api_called`: `false`, wenn gespeicherte Vektoren wiederverwendet wurden.

`embed.py` (eine Zeile je Strategie; Lauf C1 vom 14.10.2026):
```json
{"date":"2026-10-14","model":"text-embedding-3-large","openai_sdk":"2.44.0","chromadb":"1.5.9","step":"embed","strategy":"C1","dimensions":3072,"vectors":369,"vector_bytes":4534272,"inputs_sha256":{"chunks_c1.jsonl":"6d8ca599…"},"canary_min_cosine":0.9999061226844788,"input_tokens":165723,"cost_usd":0.02154399,"canary_input_tokens":2706,"canary_cost_usd":0.00035178,"api_called":true}
```

`retrieve.py` (eine Zeile je Lauf; `strategy` listet alle Strategien des Laufs, `vectors`/`dimensions` beziehen sich
auf die Fragen, `inputs_sha256` belegt alle Eingaben, u. a. die Ground Truth nach
[ADR 0017](../adr/0017-fragenkatalog.md); seit 17.10.2026 zusätzlich `outputs_sha256` mit der Prüfsumme der
geschriebenen Ergebnisdatei, gegen die `generate.py` prüft (Pflicht für den Hauptlauf; ältere Pilot-Einträge
ohne sie werden nur an den Eingaben geprüft) ([ADR 0033](../adr/0033-antwortmodell.md)); Beispiel:
erster Lauf des Pilot-Sets `hard`, noch ohne `outputs_sha256`):
```json
{"date":"2026-10-14","model":"text-embedding-3-large","openai_sdk":"2.44.0","chromadb":"1.5.9","step":"retrieve","strategy":"C1,C2,C3","dimensions":3072,"vectors":16,"inputs_sha256":{"questions.csv":"6f4a2e9f…","ground_truth.csv":"f9ddb34b…","sections.jsonl":"…","query_embeddings.npz":"…","chunks_c1.jsonl":"…","chunks_c2.jsonl":"…","chunks_c3.jsonl":"…","embeddings_c1.npz":"…","embeddings_c2.npz":"…","embeddings_c3.npz":"…"},"canary_min_cosine":0.9999592304229736,"input_tokens":391,"cost_usd":5.083e-05,"canary_input_tokens":2706,"canary_cost_usd":0.00035178,"api_called":true}
```

Ein Lauf mit `--control` steht mit `"strategy":"K1"` und den K1-Dateien in `inputs_sha256` im Protokoll.

**`generation_runs.jsonl`** (`data/evaluation/`, versioniert; ein Eintrag je erfolgreichem Lauf von `generate.py`, dazu je
neu erzeugter blinder Bewertung ein Eintrag `{"step":"scaffold","strategy":"C1,C2,C3","scoring":"rules","codes":…,"outputs_sha256":{"scoring_items.jsonl":"…"}}`
(`scoring` = `config.SCORING_METHOD`: nur regelbasiert zu bewerten, [ADR 0036](../adr/0036-regelbasierte-bewertung-verpflichtend.md); ältere Einträge ohne das Feld), je
Einfrieren der Kernpunkte ein Eintrag `"step":"key_points"` (siehe `key_points.csv`);
[ADR 0033](../adr/0033-antwortmodell.md)). Pilot-Sets schreiben dieselben Einträge in ihre `runs.jsonl`. Ein
abgebrochener Lauf schreibt keinen Eintrag. Felder (noch kein echter Lauf, Werte daher nur zur Form):

- `model`, `reasoning_effort`, `temperature`, `seed`, `max_completion_tokens`: die gepinnten Einstellungen; `model_reported`:
  das Modell, das die API für alle Antworten des Laufs gemeldet hat; `model_created`: Erstellungszeitpunkt des
  Modellobjekts (ISO 8601, UTC), vor und nach dem Lauf gleich; `system_fingerprint`: die gemeldete
  Backend-Konfiguration (`null`, wenn die API keine meldet).
- `openai_sdk`, `date`, `step` (`generate`), `strategy` (`C1,C2,C3`), `answers` (Zahl der Antworten).
- `inputs_sha256`: Ergebnisdatei des Retrievals, Fragen, Ground Truth und Chunk-Dateien; `outputs_sha256`:
  `generated_answers.csv`. `evaluate_answers.py --mode scaffold` prüft beide gegen die aktuellen Dateien.
- `prompt_tokens`, `completion_tokens`, `cost_usd` für den Lauf, `by_strategy` dieselben drei je Strategie
  ([ADR 0008](../adr/0008-kosten-als-variable.md)).

```json
{"date":"…","model":"gpt-6-luna","reasoning_effort":"none","temperature":0.0,"seed":20261017,"max_completion_tokens":1024,"openai_sdk":"2.44.0","step":"generate","strategy":"C1,C2,C3","model_reported":"…","model_created":"…","system_fingerprint":"…","answers":144,"inputs_sha256":{"retrieved_results.csv":"…","questions.csv":"…","ground_truth.csv":"…","chunks_c1.jsonl":"…","chunks_c2.jsonl":"…","chunks_c3.jsonl":"…"},"outputs_sha256":{"generated_answers.csv":"…"},"by_strategy":{"C1":{"prompt_tokens":0,"completion_tokens":0,"cost_usd":0.0},"C2":{"…":"…"},"C3":{"…":"…"}},"prompt_tokens":0,"completion_tokens":0,"cost_usd":0.0}
```

## Fragen und Ground Truth

**`questions.csv`**
```
question_id,question,type,difficulty,notes
Q001,"What is the difference between ref and reactive in Vue?",comparative,multi-section,
```

`type` und `difficulty` nehmen nur die Werte aus [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) an (`config.QUESTION_TYPES`,
`config.QUESTION_CLASSES`); die Pilot-Sets sind davon ausgenommen.

**`ground_truth.csv`**
```
question_id,expected_answer,relevant_doc_ids,relevant_section_ids
Q001,"ref wraps any value in a reactive object with a .value property; reactive makes an object deeply reactive but only works on objects.",D049,"D049#reactive"
```

Mehrere IDs in `relevant_doc_ids` bzw. `relevant_section_ids` werden durch `config.ID_SEPARATOR` (`;`) getrennt.

`retrieve.py` prüft beide Dateien vor jedem Lauf und bricht bei Verstößen ab:

- Datei vorhanden und nicht leer; Kopfzeilen exakt wie oben, jede Zeile mit genau dieser Feldanzahl, keine doppelte
  `question_id`.
- Pflichtfelder nicht leer: in `questions.csv` alle außer `notes`, in `ground_truth.csv` alle.
- Jede Frage hat eine Ground-Truth-Zeile und umgekehrt; jede Frage hat mindestens eine `relevant_section_id`, und alle
  existieren in `sections.jsonl`; keine ID steht in einer Zeile doppelt.
- `relevant_doc_ids` liegen im Korpus und sind genau die Dokumente der `relevant_section_ids`.
- Nur für den Hauptkatalog: Der Freeze-Datensatz existiert und die Prüfsummen von `questions.csv`, `ground_truth.csv`,
  `sections.jsonl` und `documents.jsonl` passen ([ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md)).

**`section_index.md`** (`data/processed/`, nicht versioniert, geschrieben von `catalogue.py sections`): Markdown-Tabelle,
eine Zeile je Abschnitt in der Reihenfolge von `sections.jsonl`:
```
| section_id | area | path | heading path | tokens |
|---|---|---|---|---:|
| `D001#createapp` | api | api/application.md | Application API › createApp() | 164 |
```
`area` ist der Bereich der Seite (Gruppe der Navigation, Feld `area` in `documents.jsonl`; [Korpus](corpus.md#bereiche)).

**`catalogue_freeze.json`** (`data/evaluation/`, versioniert, geschrieben von `catalogue.py freeze`; [ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md)):
```
{
  "date": "2026-11-09",
  "questions": 48,
  "types": {"factual": 12, "procedural": 12, "conceptual": 12, "comparative": 6, "limitation": 6},
  "classes": {"single": 12, "multi-section": 12, "detail": 12, "paraphrase": 12},
  "sha256": {"questions.csv": "…", "ground_truth.csv": "…", "sections.jsonl": "…", "documents.jsonl": "…",
             "catalogue_plan.csv": "…", "catalogue_review.csv": "…"}
}
```

Plan- und Durchsichtsdatei werden nur aufgezeichnet; die Sperre in `retrieve.py` prüft die vier übrigen Dateien.

**`catalogue_plan.csv`** (`data/evaluation/`, versioniert, einmal geschrieben von `catalogue.py plan`, danach ändert
der Editor nur Status, Sprunggrund und Frage-ID sowie bei einem Sprung Slot und Klasse der nachrückenden Reservezeile; [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md)): eine Zeile je gezogenem Abschnitt, je Bereich erst die Slots, dann
die Reserve in Ziehungsreihenfolge.
```
area,draw,section_id,slot_id,class,status,skip_reason,question_id
api,1,D009#onmounted,S01,single,used,,Q001
api,2,D012#createrenderer,S02,multi-section,skipped,code-or-links,
api,13,D020#script,S02,multi-section,open,,
api,14,D003#v-bind,,,reserve,,
```
`status` ∈ `config.CATALOGUE_PLAN_STATUSES` (`open`, `used`, `skipped`, `reserve`); `skip_reason` ∈
`config.CATALOGUE_SKIP_REASONS`. `check` vergleicht den Plan mit einer frischen Ziehung und meldet jede andere
Abweichung als Fehler.

**`catalogue_review.csv`** (`data/evaluation/`, versioniert; Claude hängt Zeilen mit `decision = open` an, die
Entscheidung trifft Jonas im Editor; [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md)):
```
round,question_id,kind,suggestion,section_id,decision,reason,date
1,Q001,missing_section,onUnmounted shows the same callback timing.,D009#onunmounted,accepted,,2026-10-20
1,Q002,wording,Name the hook instead of "it".,,rejected,the slot asks for a paraphrase,2026-10-20
```
`kind` ∈ `config.CATALOGUE_REVIEW_KINDS`, `decision` ∈ `config.CATALOGUE_REVIEW_DECISIONS`; `section_id` nur bei
`missing_section`, `reason` Pflicht bei `rejected`.

## Ergebnisse

**`retrieved_results.csv`** (`retrieve.py` läuft über alle Strategien C1–C3 und schreibt die Datei vollständig neu;
[ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)). `score` = Kosinus-Ähnlichkeit mit sechs
Nachkommastellen; `is_relevant` = `1`/`0` nach der Hauptregel ([Evaluation](evaluation.md#relevanz-eines-chunks)).
```
question_id,strategy,rank,chunk_id,score,is_relevant
Q001,C1,1,C1_D049_0004,0.840000,1
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
Q001,C1,"...",C1_D049_0004,1200,180
```

Blinde Bewertung ([ADR 0032](../adr/0032-blinde-rubrik-bewertung.md)): `evaluate_answers.py --mode scaffold` schreibt
aus `generated_answers.csv` drei Dateien, je Frage die drei Antworten in der mit `config.SCORING_SEED` gemischten
Reihenfolge unter den Codes `<question_id>-A`, `-B`, `-C`; Bogen und Schlüssel werden nie überschrieben (liegen beide
vor, stimmt der Schlüssel und sind die neuen Einträge byte-gleich zur Prüfsumme im Laufprotokoll, schreibt ein
erneuter Aufruf nur Lesepaket und `scoring_items.jsonl` neu).

**`scoring_packet.md`** (Lesepaket, nur Lesekopie; bewertet wird in der App über die Prüffragen): Hinweis, dann je Frage `## Q001` mit Frage und Referenzantwort, je Code
`### Q001-A` mit der Antwort und den Passagen, die das Modell sah (`[Excerpt N]`, getrennt durch `---`, ohne
Chunk-IDs), beide in einem Code-Block, dessen Zaun länger ist als jede Backtick-Folge im Text.

**`scoring_sheet.csv`** (Bewertungsbogen, von Hand gefüllt: Kriterien ganze Zahlen 0–2, `notes` frei)
```
code,question_id,correctness,completeness,groundedness,no_hallucination,clarity,notes
Q001-A,Q001,2,1,2,2,2,lists only one of the two hooks
```

**`scoring_key.csv`** (Schlüssel; erst `--mode summarise` liest ihn)
```
code,question_id,strategy
Q001-A,Q001,C3
```

**`scoring_items.jsonl`** (Daten der Bewertungsseite, [ADR 0034](../adr/0034-bewertung-in-der-app.md); nicht
versioniert): eine Zeile je Code in der Reihenfolge des Lesepakets mit `code`, `question_id`, `question`,
`reference_answer`, `answer` und `excerpts` (Texte der Passagen in Rangfolge, ohne Chunk-IDs); keine Strategie.

**`key_points.csv`** (Kernpunkte je Frage, von Jonas vor der Bewertung geschrieben und eingefroren,
[ADR 0035](../adr/0035-regelbasierte-bewertung.md); versioniert): eine Zeile je Punkt, `point` ab 1 ohne Lücken
(1 = Kernaussage), höchstens `config.KEY_POINTS_MAX` je Frage, `text` einzeilig. Das Einfrieren schreibt einen
Eintrag `{"step":"key_points","strategy":"C1,C2,C3","outputs_sha256":{"key_points.csv":"…","scoring_items.jsonl":"…"}}`
ins Laufprotokoll; er gilt nur für das Scaffold mit dieser `scoring_items.jsonl`. Nach einem neuen Scaffold werden die
Kernpunkte erneut eingefroren (eine `scoring_checks.csv` des alten Scaffolds vorher beiseitelegen).
```
question_id,point,text
Q001,1,"ref() wraps any value, reactive() only objects"
```

**`scoring_checks.csv`** (Antworten auf die Prüffragen je bewertetem Code, in der Reihenfolge des Bogens,
[ADR 0035](../adr/0035-regelbasierte-bewertung.md); versioniert): `points` = Markierungen der Kernpunkte in
Punktreihenfolge, durch `;` getrennt; übrige Spalten und Optionen nach
[Evaluation](evaluation.md#regelbasierte-bewertung).
```
code,rules_version,points,declines,core_wrong,other_error,grounded,hallucination,answers_question,direct,wordy
Q001-A,2026-10-17,covered;missing,no,no,no,all,none,yes,yes,no
```

**`scores.csv`** (abgeleitet von `--mode summarise` aus Bogen und Schlüssel, wird neu geschrieben; sortiert nach
`question_id` und Strategie; Kriterien-Spalten = `config.RUBRIC_CRITERIA`, `total_score` = Mittel der Kriterien mit
einer Nachkommastelle, nach [Evaluation](evaluation.md#antwort-evaluation-rubrik-02))
```
question_id,strategy,correctness,completeness,groundedness,no_hallucination,clarity,total_score
Q001,C1,2,2,2,2,2,2.0
```

## Pilot-Sets

Pilotproben (`scripts/difficulty_probe.py`) liegen in `config.PILOT_DIR` = `data/pilot/`; sie sind **nicht** Teil des
Fragenkatalogs. Jedes Set ist ein Ordner mit den Dateien der Evaluation unter denselben Namen und Formaten:

| Datei | Inhalt | Versioniert |
|---|---|---|
| `questions.csv` | Pilotfragen (IDs `P01`… bzw. `H01`…; `notes` = `pilot <Art>`, Art z. B. `multi-section`, `detail`, `paraphrase`) | ja |
| `ground_truth.csv` | Relevanz-Annotation | ja |
| `query_embeddings.npz` | gespeicherte Fragevektoren | nein |
| `retrieved_results.csv` | Top-5 für C1–C3 | ja |
| `retrieved_results_control.csv` | Top-5 für K1 | ja |
| `generated_answers.csv` | Antworten C1–C3 (`generate.py --set`) | ja |
| `scoring_sheet.csv`, `scoring_key.csv` | blinde Bewertung (`evaluate_answers.py --set`, ggf. nur die ersten N Fragen mit `--limit`) | ja |
| `key_points.csv`, `scoring_checks.csv` | Kernpunkte und Prüffragen der regelbasierten Bewertung ([ADR 0035](../adr/0035-regelbasierte-bewertung.md)) | ja |
| `scoring_packet.md`, `scoring_items.jsonl`, `scores.csv` | Lesepaket, Daten der Bewertungsseite, entblindete Bewertung | nein |
| `runs.jsonl` (`config.PILOT_RUNS_FILE_NAME`) | Laufprotokoll im Format von `embedding_runs.jsonl` und `generation_runs.jsonl` | ja |

| Set | Inhalt |
|---|---|
| `data/pilot/` | Probe 1: 8 einfache Fragen |
| `data/pilot/hard/` | Probe 2: 16 schwere Fragen, Annotation blind vor jedem Retrieval (Hauptwerte; [ADR 0027](../adr/0027-blinde-annotation.md)) |
| `data/pilot/hard_posthoc/` | dieselben Fragen mit nachträglich ergänzter Annotation; nur Sensitivität, keine Evidenz ([ADR 0027](../adr/0027-blinde-annotation.md)) |
| `data/pilot/hard/history/` | `ground_truth_b75d188.csv`: blinde Annotation mit den IDs des alten Korpus (`b75d188`) |

Ergebnisse der Proben: [Experiment-Protokoll](experiment-record.md#pilotproben-auf-dem-erweiterten-korpus-14102026).
