# Datenartefakte und Formate

> Seitentyp: Nachschlagen (reference). Stand: aus dem Projektleitfaden (Juni 2026, aktualisiert 13.10.2026). Übersicht: [Dokumentation](../README.md).


**`documents.jsonl`**
```json
{"doc_id":"D027","path":"guide/essentials/reactivity-fundamentals.md","title":"Reactivity Fundamentals","text":"...","tokens":3063}
```

**`chunks_c1.jsonl`** (analog c2/c3)
```json
{"chunk_id":"C1_D001_0001","doc_id":"D001","strategy":"fixed_500_no_overlap","text":"...","start_token":0,"end_token":500}
```

**`sections.jsonl`** (ein Eintrag je H1–H3-Abschnitt; Spanne in Tokens des bereinigten `text`, Ende exklusiv; ein Abschnitt reicht bis zur nächsten Überschrift gleicher oder höherer Ebene; [ADR 0019](../adr/0019-korpus-ausschnitt.md))
```json
{"section_id":"D027#declaring-reactive-state-1","doc_id":"D027","anchor":"declaring-reactive-state-1","title":"Declaring Reactive State","level":2,"start_token":60,"end_token":1567}
```

**`embeddings_c1.npz`** (analog c2/c3; `data/processed/`, nicht versioniert; [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md))
Arrays `model` (Embedding-Modell), `ids` (Chunk-IDs in Dateireihenfolge), `texts` (Chunk-Texte), `vectors` (float32, n × 3.072).
Wiederverwendet wird die Datei nur, wenn Modell, IDs und Texte unverändert sind.

**`query_embeddings.npz`** (`data/evaluation/`, nicht versioniert): Arrays `model`, `ids` (Frage-IDs), `texts` (Fragen), `vectors`.

`retrieve.py --strategy` ersetzt in `retrieved_results.csv` nur die Zeilen der gewählten Strategien.

**`embedding_runs.jsonl`** (ein Eintrag je Lauf von `embed.py` oder `retrieve.py`; Kosten nach [ADR 0008](../adr/0008-kosten-als-variable.md); `canary_min_cosine` = Ergebnis der Modellstand-Prüfung, `null` wenn keine nötig war)
```json
{"date":"2026-10-13","model":"text-embedding-3-large","openai_sdk":"2.44.0","chromadb":"1.5.9","step":"embed","strategy":"C1","dimensions":3072,"vectors":260,"vector_bytes":3194880,"inputs_sha256":{"chunks_c1.jsonl":"…"},"input_tokens":117594,"cost_usd":0.01528722,"api_called":true,"canary_min_cosine":null}
```

`start_token`/`end_token` von Chunks und Abschnitten zählen beide über `src/tokens.py` (`cl100k_base`) und sind daher direkt vergleichbar.

**`questions.csv`**
```
question_id,question,type,difficulty,notes
Q001,"What is the difference between ref and reactive in Vue?",conceptual,medium,
```

**`ground_truth.csv`**
```
question_id,expected_answer,relevant_doc_ids,relevant_section_ids
Q001,"ref wraps any value in a reactive object with a .value property; reactive makes an object deeply reactive but only works on objects.",D027,"D027#reactive"
```

Mehrere IDs in `relevant_doc_ids` bzw. `relevant_section_ids` werden durch `;` getrennt (`config.ID_SEPARATOR`).

**`retrieved_results.csv`**
```
question_id,strategy,rank,chunk_id,score,is_relevant
Q001,C1,1,C1_D001_0001,0.84,1
```

**`generated_answers.csv`**
```
question_id,strategy,answer,sources,prompt_tokens,completion_tokens
Q001,C1,"...",C1_D001_0001,1200,180
```

**`scores.csv`**
```
question_id,strategy,correctness,completeness,groundedness,no_hallucination,clarity,total_score
Q001,C1,2,2,2,2,2,2.0
```

> Jede Zwischenstufe speichern. Das ist die Grundlage für Reproduzierbarkeit und für die spätere Auswertung.
