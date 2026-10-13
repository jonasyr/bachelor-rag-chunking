# Datenartefakte und Formate

> Seitentyp: Nachschlagen (reference). Stand: aus dem Projektleitfaden (Juni 2026, aktualisiert 13.10.2026). Übersicht: [Dokumentation](../README.md).


**`documents.jsonl`**
```json
{"doc_id":"D001","path":"guide/essentials/reactivity-fundamentals.md","title":"Reactivity Fundamentals","text":"...","tokens":1700}
```

**`chunks_c1.jsonl`** (analog c2/c3)
```json
{"chunk_id":"C1_D001_0001","doc_id":"D001","strategy":"fixed_500_no_overlap","text":"...","start_token":0,"end_token":500}
```

**`questions.csv`**
```
question_id,question,type,difficulty,notes
Q001,"What is the difference between ref and reactive in Vue?",conceptual,medium,
```

**`ground_truth.csv`**
```
question_id,expected_answer,relevant_doc_ids,relevant_section_ids
Q001,"ref wraps any value in a reactive object with a .value property; reactive makes an object deeply reactive but only works on objects.",D001,"D001#ref-vs-reactive"
```

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
