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

`retrieve.py` läuft immer über alle Strategien und schreibt `retrieved_results.csv` vollständig neu
([ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)).

**`embedding_runs.jsonl`** (ein Eintrag je Lauf von `embed.py` oder `retrieve.py`; Kosten nach [ADR 0008](../adr/0008-kosten-als-variable.md))

- `input_tokens`/`cost_usd`: nur die eigenen Texte des Schritts (Chunks einer Strategie bzw. Fragen).
- `canary_*`: Modellstand-Prüfung getrennt davon (`canary_min_cosine` = niedrigste Kosinus-Ähnlichkeit, `null` wenn
  keine Prüfung nötig war), damit sie die Kosten einer Strategie nicht verfälscht.

`embed.py` (eine Zeile je Strategie):
```json
{"date":"2026-10-13","model":"text-embedding-3-large","openai_sdk":"2.44.0","chromadb":"1.5.9","step":"embed","strategy":"C1","dimensions":3072,"vectors":260,"vector_bytes":3194880,"inputs_sha256":{"chunks_c1.jsonl":"…"},"canary_min_cosine":null,"input_tokens":117594,"cost_usd":0.01528722,"canary_input_tokens":0,"canary_cost_usd":0.0,"api_called":true}
```

`retrieve.py` (eine Zeile je Lauf; `strategy` listet alle Strategien, `vectors`/`dimensions` beziehen sich auf die
Fragen, `inputs_sha256` belegt alle Eingaben, u. a. die eingefrorene Ground Truth nach ADR 0017):
```json
{"date":"…","model":"text-embedding-3-large","openai_sdk":"2.44.0","chromadb":"1.5.9","step":"retrieve","strategy":"C1,C2,C3","dimensions":3072,"vectors":40,"inputs_sha256":{"questions.csv":"…","ground_truth.csv":"…","sections.jsonl":"…","query_embeddings.npz":"…","chunks_c1.jsonl":"…","chunks_c2.jsonl":"…","chunks_c3.jsonl":"…","embeddings_c1.npz":"…","embeddings_c2.npz":"…","embeddings_c3.npz":"…"},"canary_min_cosine":0.99999,"input_tokens":600,"cost_usd":0.000078,"canary_input_tokens":2700,"canary_cost_usd":0.000351,"api_called":true}
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

`retrieve.py` prüft beide Dateien vor jedem Lauf und bricht bei Verstößen ab:

- Kopfzeilen exakt wie oben, jede Zeile mit genau dieser Feldanzahl, keine doppelte `question_id`.
- Pflichtfelder nicht leer: in `questions.csv` alle außer `notes`, in `ground_truth.csv` alle.
- Jede Frage hat eine Ground-Truth-Zeile und umgekehrt; alle `relevant_section_ids` existieren in `sections.jsonl`.
- `relevant_doc_ids` sind genau die Dokumente der `relevant_section_ids`.

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
