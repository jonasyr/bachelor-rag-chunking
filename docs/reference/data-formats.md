# Datenartefakte und Formate

> Seitentyp: Nachschlagen (reference). Stand: 14.10.2026. Übersicht: [Dokumentation](../README.md).

Dateinamen und Pfade kommen aus [`src/config.py`](../../src/config.py) ([Konfiguration](configuration.md)); welche
Dateien versioniert sind: [Werkzeuge und Repository](tooling.md#versioniert-und-ignoriert). Beispiele sind echte
Datensätze des Korpus auf `40aa88a` ([Korpus](corpus.md)), Texte gekürzt (`...`), Prüfsummen gekürzt (`…`).

## Korpus

**`docs/corpus_snapshot.txt`** (versioniert, geschrieben von `snapshot.py`): Kopfzeilen `schlüssel: wert`, eine
Leerzeile, dann je Datei `SHA-256  pfad` (zwei Leerzeichen; Pfad relativ zu `src/`, sortiert).

```
repository: https://github.com/vuejs/docs.git
commit: 40aa88af0094f7bab4aaf786e55c748a6a251d88
commit_date: 2026-09-15T14:47:19+02:00
snapshot_date: 2026-10-14
areas: api, guide, style-guide
excluded: api/component-instance.md, api/index.md, …
files: 79

fd649a62…ea62234e8  api/application.md
```

**`docs/corpus_manifest.csv`** (versioniert, geschrieben von `preprocess.py`): Spalten und Beispielzeilen in
[Korpus](corpus.md#korpusmanifest-corpus_manifestcsv).

**`documents.jsonl`**
```json
{"doc_id":"D049","path":"guide/essentials/reactivity-fundamentals.md","title":"Reactivity Fundamentals","text":"...","tokens":3063}
```

**`sections.jsonl`** (ein Eintrag je H1–H3-Abschnitt; Spanne in Tokens des bereinigten `text`, Ende exklusiv; ein
Abschnitt reicht bis zur nächsten Überschrift gleicher oder höherer Ebene; [ADR 0019](../adr/0019-korpus-ausschnitt.md))
```json
{"section_id":"D049#declaring-reactive-state-1","doc_id":"D049","anchor":"declaring-reactive-state-1","title":"Declaring Reactive State","level":2,"start_token":60,"end_token":1567}
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
[ADR 0017](../adr/0017-fragenkatalog.md); Beispiel: erster Lauf des Pilot-Sets `hard`):
```json
{"date":"2026-10-14","model":"text-embedding-3-large","openai_sdk":"2.44.0","chromadb":"1.5.9","step":"retrieve","strategy":"C1,C2,C3","dimensions":3072,"vectors":16,"inputs_sha256":{"questions.csv":"6f4a2e9f…","ground_truth.csv":"f9ddb34b…","sections.jsonl":"…","query_embeddings.npz":"…","chunks_c1.jsonl":"…","chunks_c2.jsonl":"…","chunks_c3.jsonl":"…","embeddings_c1.npz":"…","embeddings_c2.npz":"…","embeddings_c3.npz":"…"},"canary_min_cosine":0.9999592304229736,"input_tokens":391,"cost_usd":5.083e-05,"canary_input_tokens":2706,"canary_cost_usd":0.00035178,"api_called":true}
```

Ein Lauf mit `--control` steht mit `"strategy":"K1"` und den K1-Dateien in `inputs_sha256` im Protokoll.

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
`area` ist das erste Pfadsegment (`api`, `guide`, `style-guide`).

**`catalogue_freeze.json`** (`data/evaluation/`, versioniert, geschrieben von `catalogue.py freeze`; [ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md)):
```
{
  "date": "2026-11-09",
  "questions": 48,
  "types": {"factual": 12, "procedural": 12, "conceptual": 12, "comparative": 6, "limitation": 6},
  "classes": {"single": 12, "multi-section": 12, "detail": 12, "paraphrase": 12},
  "sha256": {"questions.csv": "…", "ground_truth.csv": "…", "sections.jsonl": "…", "documents.jsonl": "…"}
}
```

## Ergebnisse

**`retrieved_results.csv`** (`retrieve.py` läuft über alle Strategien C1–C3 und schreibt die Datei vollständig neu;
[ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)). `score` = Kosinus-Ähnlichkeit mit sechs
Nachkommastellen; `is_relevant` = `1`/`0` nach der Hauptregel ([Evaluation](evaluation.md#relevanz-eines-chunks)).
```
question_id,strategy,rank,chunk_id,score,is_relevant
Q001,C1,1,C1_D049_0004,0.840000,1
```

**`retrieved_results_control.csv`** (`retrieve.py --control`): gleiche Spalten, `strategy` immer `K1`.

**`generated_answers.csv`** (Schema festgelegt, `generate.py` noch nicht umgesetzt)
```
question_id,strategy,answer,sources,prompt_tokens,completion_tokens
Q001,C1,"...",C1_D049_0004,1200,180
```

**`scores.csv`** (Schema festgelegt, `evaluate_answers.py` noch nicht umgesetzt; Kriterien-Spalten =
`config.RUBRIC_CRITERIA`, `total_score` nach [Evaluation](evaluation.md#antwort-evaluation-rubrik-02))
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
| `runs.jsonl` (`config.PILOT_RUNS_FILE_NAME`) | Laufprotokoll im Format von `embedding_runs.jsonl` | ja |

| Set | Inhalt |
|---|---|
| `data/pilot/` | Probe 1: 8 einfache Fragen |
| `data/pilot/hard/` | Probe 2: 16 schwere Fragen, Annotation blind vor jedem Retrieval (Hauptwerte; [ADR 0027](../adr/0027-blinde-annotation.md)) |
| `data/pilot/hard_posthoc/` | dieselben Fragen mit nachträglich ergänzter Annotation; nur Sensitivität, keine Evidenz ([ADR 0027](../adr/0027-blinde-annotation.md)) |
| `data/pilot/hard/history/` | `ground_truth_b75d188.csv`: blinde Annotation mit den IDs des alten Korpus (`b75d188`) |

Ergebnisse der Proben: [Experiment-Protokoll](experiment-record.md#pilotproben-auf-dem-erweiterten-korpus-14102026).
