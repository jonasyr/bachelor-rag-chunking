# Ground Truth und Projektleitfaden für die Bachelorarbeit

> Zentrales Arbeits-, Entscheidungs- und Referenzdokument für die gesamte Bearbeitung.
> Stand: Juni 2026. Bearbeitungszeitraum der Arbeit: ca. Juli–Dezember 2026.

---

## 0. Wie dieses Dokument zu lesen ist

Dieses Dokument ist die verbindliche Orientierung von Beginn bis Abgabe. Es fasst zusammen, **was final entschieden ist**, **was sich gegenüber der ursprünglichen Baseline geändert hat**, **in welcher Reihenfolge gearbeitet wird** und **wie die Arbeit technisch und wissenschaftlich umgesetzt wird**.

**Prioritätsregel bei Widersprüchen:**

1. Finales Exposé und spätere Präzisierungen im Chat (höchste Priorität)
2. Konkret bestätigte Entscheidungen aus dem Chatverlauf
3. Ursprüngliche Projekt-Baseline
4. Allgemeine Best Practices

Wo die ursprüngliche Baseline und das Exposé sich unterscheiden, gilt das Exposé. Die wichtigsten Abweichungen sind in Abschnitt 3 explizit aufgeführt.

---

## 1. Finale Projektdefinition (verbindlich)

### Titel
**Einfluss von Chunking-Strategien auf die Retrieval- und Antwortqualität eines Retrieval-Augmented-Generation-Systems für technische Projektdokumentation**

### Hauptforschungsfrage
**Wie beeinflussen unterschiedliche Chunking-Strategien die Retrieval- und Antwortqualität eines Retrieval-Augmented-Generation-Systems bei der Beantwortung projektspezifischer Fragen auf Basis technischer Open-Source-Dokumentation?**

### Unterfragen
1. Welche Chunking-Strategien eignen sich für die Aufbereitung technischer Projektdokumentation im Kontext eines RAG-Systems?
2. Wie unterscheiden sich die Strategien hinsichtlich der Retrieval-Qualität (Recall@k, Precision@k, MRR)?
3. Wie wirken sie sich auf die Antwortqualität aus (Korrektheit, Vollständigkeit, Quellenbezug, Halluzinationsfreiheit)?
4. Welche Trade-offs ergeben sich zwischen Chunk-Größe, Kontextabdeckung, Redundanz, Retrieval-Präzision, Kosten und Antwortqualität?
5. Welche Empfehlungen lassen sich für die Gestaltung von RAG-Systemen auf technischer Dokumentation ableiten?

### Ziel in einem Satz
Konzeption, Implementierung und Evaluation einer RAG-Pipeline für technische Open-Source-Dokumentation, bei der ausschließlich die Chunking-Strategie variiert wird, um deren Einfluss auf Retrieval- und Antwortqualität isoliert zu bestimmen und daraus praktische Empfehlungen abzuleiten.

### Dozenten-taugliche Kurzbeschreibung
Die Arbeit vergleicht drei Chunking-Strategien für ein RAG-System auf Basis der Vue.js-Dokumentation. Dazu wird ein Dokumentationssnapshot fixiert, ein Fragenkatalog mit Referenzantworten und relevanten Quellen kuratiert und eine RAG-Pipeline mit konstantem Modell-, Embedding- und Retrieval-Setup implementiert. Bewertet werden Retrieval-Qualität (Recall@k, Precision@k, MRR) und Antwortqualität (referenzbasierte Rubrik), ergänzt um eine automatisierte Sekundärbewertung und eine Effizienzbetrachtung.

---

## 2. Verbindliche Entscheidungen (Decision Log)

| # | Entscheidung | Status | Quelle | Verhältnis zur Baseline |
|---|--------------|--------|--------|--------------------------|
| D1 | **Dokumentkorpus: Vue.js-Dokumentation** (`vuejs/docs`, Markdown) | verbindlich | Chat | **ersetzt FastAPI** |
| D2 | Zitierstil: **biblatex + biber, APA 7, `\parencite`** | verbindlich | Chat | konkretisiert |
| D3 | **Kein Praxispartner** (Peano o. Ä. nicht einbinden) | verbindlich | Chat | ergänzt |
| D4 | Bearbeitungszeitraum: **Juli–Dezember 2026** | verbindlich | Chat | konkretisiert (Baseline hatte nur Wochenraster) |
| D5 | **Drei Chunking-Strategien**: C1 fixed ohne Overlap, C2 fixed mit Overlap, C3 strukturbasiert (Markdown-Überschriften). C4 semantisch nur optional | verbindlich | Exposé/Baseline | übernommen |
| D6 | **Nur Chunking variiert**, alle übrigen Pipeline-Komponenten konstant | verbindlich | Exposé | übernommen |
| D7 | **Evaluation als Triangulation**: manuelle referenzbasierte Bewertung **primär**, automatisiertes Framework (RAGAS) **sekundär**, Übereinstimmung beider als **Validitätsindikator** | verbindlich | Chat | **verschärft** (Baseline: RAGAS nur „optional") |
| D8 | **Kosten/Effizienz als eigene abhängige Variable** (Chunk-Anzahl, Indexgröße, Token-Verbrauch) | verbindlich | Chat | ergänzt |
| D9 | **Drei geschärfte Hypothesen H1–H3** (siehe 4.3), explorativ | verbindlich | Chat | **ersetzt** alte H1–H3 der Baseline |
| D10 | **Fixed-size + Overlap = starke Baseline**, kein Strohmann (belegt durch Qu et al. 2025) | verbindlich | Chat | ergänzt |
| D11 | Forschungslücke = **entwicklerorientierte Open-Source-Softwaredokumentation**; bestehende kontrollierte Vergleiche liegen in fachfremden Domänen | verbindlich | Chat | ergänzt |
| D12 | Retrieval-Metriken: **Recall@k, Precision@k, MRR** (+ Hit@k vereinfacht) | verbindlich | Exposé/Baseline | übernommen |
| D13 | Antwort-Rubrik: **0–2-Skala, 5 Kriterien, gleich gewichtet** | verbindlich | Exposé/Baseline | übernommen |
| D14 | Parameter-Baseline: **temperature = 0, top-k = 5** | verbindlich | Baseline | übernommen |
| D15 | Tech-Stack: **Python, OpenAI API (LLM + Embeddings), Chroma, tiktoken, Pandas, Matplotlib/Plotly, Streamlit, optional RAGAS** | verbindlich | Baseline | übernommen |
| D16 | **Modell-Neutralität**: festes GPT-Modell über OpenAI API, exakte Version zum Implementierungszeitpunkt dokumentiert und konstant gehalten | verbindlich | Baseline | übernommen (siehe Hinweis 3 & 19) |
| D17 | Fragenkatalog: **ca. 40 Fragen** mit Referenzantworten und annotierten Quellen | verbindlich | Exposé/Baseline | übernommen |
| D18 | Literaturbasis: **15 verifizierte Quellen** (Abschnitt 18) | verbindlich | Chat | konkretisiert |

---

## 3. Was sich gegenüber der ursprünglichen Baseline geändert hat

Dieser Abschnitt ist bewusst explizit, damit keine veralteten Baseline-Punkte versehentlich übernommen werden.

### Geändert / ersetzt
- **Korpus FastAPI → Vue.js.** Grund: Abgrenzung. Ein Praktiker-Blogbeitrag (Mai 2026) hat ein nahezu identisches Setup (FastAPI/Supabase/Stripe, eingefrorenes QA-Set, eine Variable pro Experiment, RAGAS, überschriftenbasiertes Chunking) bereits umgesetzt. Vue.js grenzt Korpus und Domäne klar ab und behält die Fragetyp-Vielfalt.
- **Alle FastAPI-spezifischen Beispiele entfallen** (Path Parameters, Dependency Injection, Pydantic) und werden durch Vue-Beispiele ersetzt (Reaktivität, Composition API, Komponenten, Props, Composables; siehe Abschnitt 11).
- **Repository-Pfad** `data/raw/fastapi_docs_snapshot/` → `data/raw/vue_docs_snapshot/`.
- **Hypothesen** der Baseline (alte H1–H3) → durch geschärfte H1–H3 ersetzt (Abschnitt 4.3), die die nicht-offensichtlichen Dimensionen betonen.
- **RAGAS-Rolle** von „optional/Zusatz" → fester Bestandteil der **Triangulation** mit explizitem Übereinstimmungsabgleich.

### Konkretisiert / ergänzt
- **Kosten/Effizienz** wird zur eigenständigen abhängigen Variable.
- **Fixed-size + Overlap** wird ausdrücklich als leistungsfähige Baseline positioniert (belegt durch Qu et al. 2025), wodurch die Arbeit gegen den Vorwurf der Trivialität abgesichert ist.
- **Forschungslücke** wird domänenspezifisch geschärft (fachfremde Vergleiche existieren; Softwaredokumentation ist die Lücke).
- **Zeitplan** auf konkrete Kalenderdaten Juli–Dezember 2026 gelegt.

### Bewusst nicht Teil der Arbeit (Scope-Schutz, unverändert)
Bester LLM-/Embedding-Vergleich; RAG vs. kein RAG als Hauptfrage; Fine-Tuning; lokale LLMs; rein automatische Bewertung ohne menschliche Kontrolle; private Firmendaten; multimodale Dokumente/PDFs mit Diagrammen.

---

## 4. Wissenschaftlicher Rahmen

### 4.1 Problem und Ansatz
Technische Dokumentation enthält umfangreiches projektspezifisches Wissen, das über viele Dateien verteilt ist. LLMs beantworten Fragen, verfügen aber ohne Kontext nicht zuverlässig über projektspezifisches Wissen und neigen zu unbelegten Aussagen. RAG ruft relevante Dokumentstellen zur Laufzeit ab und stellt sie als Kontext bereit. Die Qualität hängt maßgeblich von der **Segmentierung (Chunking)** ab.

### 4.2 Forschungslücke und Abgrenzung (drei Säulen)
1. **Anderer Korpus:** Vue.js statt der bereits informell untersuchten FastAPI/Supabase/Stripe-Doku.
2. **Andere Domäne:** entwicklerorientierte Frontend-Framework-Dokumentation; kontrollierte Chunking-Vergleiche existieren bislang vor allem fachfremd (Unternehmensdokumente, klinische Entscheidungsunterstützung).
3. **Striktere Methodik:** referenzbasierte manuelle Bewertung als Primärverfahren, Fragetyp-Differenzierung, Reproduzierbarkeit über Snapshot.

### 4.3 Hypothesen (verbindlich, explorativ)
- **H1 — Starke Baseline:** Strukturbasiertes Chunking erzielt gegenüber größenbasiertem Chunking **ohne** Overlap eine höhere Retrieval-Qualität, übertrifft größenbasiertes Chunking **mit** Overlap jedoch **nicht durchgängig**, da der Overlap den Verlust an Segmentgrenzen weitgehend kompensiert.
- **H2 — Entkopplung Retrieval/Antwort:** Unterschiede in der Retrieval-Qualität übertragen sich **nur teilweise** auf die Antwortqualität, da das Sprachmodell moderate Retrieval-Defizite ausgleicht.
- **H3 — Fragetyp-Interaktion:** Die relative Eignung der Strategien **variiert nach Fragetyp**; strukturbasiertes Chunking begünstigt konzeptuelle, abschnittsübergreifende Fragen, während größenbasierte Verfahren für eng umgrenzte faktische Fragen ausreichen.

### 4.4 Warum das Thema nicht trivial ist
Die Annahme „strukturiert schlägt naiv offensichtlich" ist empirisch nicht gesichert: Qu, Bao & Tu (2025) zeigen, dass semantisch/strukturell motiviertes Chunking größenbasiertes Chunking **nicht konsistent** übertrifft und der Mehraufwand oft nicht gerechtfertigt ist. Der eigentliche Erkenntnisgewinn liegt nicht in „wer gewinnt", sondern in **Effektgröße, Kosten, Metrik-Abhängigkeit, der Retrieval-Antwort-Entkopplung und der Fragetyp-Interaktion**.

### 4.5 Verwandte Arbeiten (Hinweis)
Der erwähnte Praktiker-Blogbeitrag (Mai 2026) ist **keine zitierfähige wissenschaftliche Quelle**, sollte aber im Kapitel „Verwandte Arbeiten" kurz als informeller Vorläufer eingeordnet werden — das wirkt souveräner, als ihn auszulassen, und unterstreicht die Abgrenzung (peer-review-fähige Methodik, anderer Korpus, deutschsprachige wissenschaftliche Arbeit).

---

## 5. Dokumentkorpus (Vue.js)

### 5.1 Begründung der Wahl
Vue.js bietet entwicklerorientierte, didaktisch hochwertige Dokumentation mit konzeptueller und prozeduraler Tiefe, liegt im Quellrepository durchgängig als **Markdown** vor (VitePress) und ist öffentlich und stabil. Damit ist sie sauber snapshot- und parsebar und erlaubt viele Fragetypen.

### 5.2 Quelle und Struktur
- **Repository:** `vuejs/docs` (offizielle Vue-3-Dokumentation), Inhalte unter `src/`.
- **Relevante Bereiche (Vorschlag für die Begrenzung):**
  - `src/guide/essentials/` — Template-Syntax, Reaktivität, Computed, Lifecycle, Watcher, Komponenten-Grundlagen (faktische + prozedurale Fragen)
  - `src/guide/components/` — Props, Events, v-model, Slots, Provide/Inject (prozedurale + konzeptuelle Fragen)
  - `src/guide/reusability/` — Composables, Custom Directives, Plugins (konzeptuelle Fragen)
  - `src/guide/best-practices/` — Performance, Security, Accessibility (anspruchsvollere Fragen)
  - optional Teile von `src/api/` für Referenz-/Faktenfragen
- **Umfang:** bewusst begrenzt auf ca. **50–100 Markdown-Dateien/Seiten**. Ziel ist eine sauber kontrollierbare Datenbasis, nicht maximale Menge.

### 5.3 Snapshot-Strategie (Reproduzierbarkeit)
1. Repository klonen.
2. Konkreten Commit auswählen und **Commit-Hash dokumentieren**.
3. Relevante Markdown-Dateien in separaten Ordner kopieren.
4. Optional als ZIP archivieren, **Prüfsumme** erzeugen.
5. Im Anhang/Repository dokumentieren.

**Snapshot-Steckbrief (Vorlage):**
```
Projekt: Vue.js (vuejs/docs)
Quelle: offizielles GitHub-Repository
Commit: <commit-hash>
Datum des Snapshots: <Datum>
Verwendete Pfade:
- src/guide/essentials/
- src/guide/components/
- src/guide/reusability/
- src/guide/best-practices/
Dateiformat: Markdown
Anzahl Dateien: <n>
Gesamtumfang: <n> Tokens / Wörter
```

### 5.4 Korpusmanifest (`corpus_manifest.csv`)
| file_id | path | title | section | tokens | included |
|---------|------|-------|---------|-------:|----------|
| D001 | guide/essentials/reactivity-fundamentals.md | Reactivity Fundamentals | Essentials | 1700 | yes |
| D002 | guide/components/props.md | Props | Components | 1500 | yes |

---

## 6. Chunking-Strategien

| ID | Strategie | Parameter | Vorteil | Nachteil |
|----|-----------|-----------|---------|----------|
| **C1** | Fixed-size ohne Overlap | 500 Tokens, Overlap 0 | einfach, reproduzierbar, Baseline | Kontextbruch an Grenzen |
| **C2** | Fixed-size mit Overlap | 500 Tokens, Overlap 100 | bessere Abdeckung, **starke Baseline** | mehr Chunks, mehr Redundanz, höhere Kosten |
| **C3** | Strukturbasiert | Abschnitt unter H2/H3, max. 800 Tokens, große Abschnitte nach Absätzen unterteilen | erhält semantische Einheiten | uneinheitliche Chunkgrößen (auf Vue relevant: lange Abschnitte) |
| C4 | Semantisch (optional) | Trennung nach semantischer Ähnlichkeit | theoretisch spannend | Mehraufwand, weitere Modellabhängigkeit, nur falls Zeit |

**Konstant halten (nur Chunking variiert):** Korpus/Snapshot, Sprache (Englisch), Embedding-Modell, LLM, Temperatur (0), top-k (5), Prompt, Fragenset, Bewertungsrubrik, Vector Store, Retrieval-Art (Dense), Antwortformat.

> Hinweis zu C3 auf Vue: Manche Abschnitte (z. B. „Reactivity Fundamentals") sind lang und erzeugen große Chunks; die Untergrenze/Obergrenze und die Absatz-Unterteilung sind daher sauber zu dokumentieren.

---

## 7. RAG-Pipeline-Architektur

```
Documentation Snapshot (Vue.js)
        ↓
Preprocessing (Markdown Cleaning)
        ↓
Chunking Strategy  → C1 / C2 / C3
        ↓
Embedding (OpenAI Embeddings)
        ↓
Vector Store (Chroma, ein Index pro Strategie)
        ↓
Question → Retriever (Top-k = 5)
        ↓
Prompt Assembly (Question + Context, identisch für alle Strategien)
        ↓
LLM Answer (Answer + Sources)
        ↓
Evaluation (Retrieval-Metriken + Antwort-Rubrik + Effizienz)
```

---

## 8. Technische Umsetzung / Tech-Stack

| Zweck | Werkzeug |
|-------|----------|
| Sprache | Python |
| Dokumentverarbeitung | Python-Markdown, `pathlib`, `regex` |
| Token-Zählung | `tiktoken` |
| Embeddings | OpenAI API (`text-embedding-3-large` Standard; `text-embedding-3-small` bei Kosten-/Geschwindigkeitsfokus) |
| Vector Store | Chroma (lokal, persistent) |
| LLM | festes GPT-Modell über OpenAI API |
| Datenanalyse | Pandas |
| Diagramme | Matplotlib / Plotly |
| App/Dashboard | Streamlit |
| Evaluation | eigene Skripte + optional RAGAS |

**Baseline-Parameter:** temperature = 0, top-k = 5 (konstant halten; top-k nicht zusätzlich variieren, sonst zweite unabhängige Variable).

> **Modell-Hinweis (wichtig):** Im Exposé und in der Arbeit neutral formulieren: „Es wird ein festes GPT-Modell über die OpenAI API verwendet; das konkrete Modell wird zum Implementierungszeitpunkt dokumentiert und während der Evaluation konstant gehalten." Konkrete Versionsnummern (Modell, SDK, API) erst bei der tatsächlichen Implementierung festschreiben und im Methodik-/Implementierungskapitel dokumentieren (Datum der Abfragen, Modellversion, SDK-Version).

---

## 9. Repository-Struktur

```
bachelor-rag-chunking/
├── README.md
├── requirements.txt
├── .env.example
├── data/
│   ├── raw/
│   │   └── vue_docs_snapshot/
│   ├── processed/
│   │   ├── documents.jsonl
│   │   ├── chunks_c1.jsonl
│   │   ├── chunks_c2.jsonl
│   │   └── chunks_c3.jsonl
│   └── evaluation/
│       ├── questions.csv
│       ├── ground_truth.csv
│       ├── retrieved_results.csv
│       ├── generated_answers.csv
│       └── scores.csv
├── src/
│   ├── ingest.py
│   ├── preprocess.py
│   ├── chunking.py
│   ├── embed.py
│   ├── retrieve.py
│   ├── generate.py
│   ├── evaluate_retrieval.py
│   ├── evaluate_answers.py
│   └── config.py
├── notebooks/
│   └── analysis.ipynb
├── app/
│   └── streamlit_app.py
└── docs/
    ├── methodology.md
    ├── prompts.md
    └── corpus_manifest.csv
```

---

## 10. Datenartefakte und Formate

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
question_id,question,type,difficulty
Q001,"What is the difference between ref and reactive in Vue?",conceptual,medium
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

---

## 11. Fragenkatalog (Ground Truth)

**Umfang:** ca. 40 Fragen (Minimum 30, optimal 40–50, nicht über 60). Der Fragenkatalog ist eine der wichtigsten Eigenleistungen und dauert länger als gedacht — früh beginnen.

**Fragetypen und Beispiele (Vue.js, englisch):**

| Typ | Anzahl | Beispiel |
|-----|------:|----------|
| Faktisch | 10 | Which lifecycle hooks are available in the Composition API? |
| Prozedural | 10 | How do you define props in a component using `<script setup>`? |
| Konzeptuell | 10 | What is a composable in Vue and what problem does it solve? |
| Vergleichend | 5 | What is the difference between the Options API and the Composition API? |
| Einschränkung/Fehler | 5 | What happens if a child component mutates a prop directly? |

**Ground-Truth-Felder pro Frage:** `question_id`, `question`, `question_type`, `expected_answer`, `relevant_doc_ids`, `relevant_section_ids`, `difficulty`, `notes`.

> **Wichtig:** Referenzantworten und relevante Quellen müssen **vor** der Evaluation feststehen, um nachträgliche, ergebnisorientierte Anpassungen auszuschließen.

---

## 12. Evaluation

### 12.1 Retrieval-Evaluation
Beantwortet: Findet das System die richtigen Dokumentstellen?

- **Recall@k** = |R_q ∩ T_{q,k}| / |R_q| — Anteil der gefundenen relevanten Stellen unter Top-k
- **Hit@k** = 1, wenn mindestens eine relevante Quelle in Top-k, sonst 0 (vereinfachte, gut nutzbare Variante)
- **Precision@k** = |R_q ∩ T_{q,k}| / k — Anteil relevanter unter den Top-k
- **MRR** = (1/|Q|) · Σ 1/rank_q — Position des ersten relevanten Treffers

(R_q = relevante Stellen für Frage q; T_{q,k} = Top-k abgerufene Stellen.)

### 12.2 Antwort-Evaluation (Rubrik 0–2)
| Kriterium | 0 | 1 | 2 |
|-----------|---|---|---|
| Korrektheit | falsch | teilweise korrekt | korrekt |
| Vollständigkeit | wesentliche Punkte fehlen | teilweise vollständig | vollständig |
| Quellenbezug | nicht belegt | teilweise belegt | klar durch Quellen gedeckt |
| Halluzinationsfreiheit | falsche/unbelegte Aussagen | kleine unbelegte Ergänzungen | keine Halluzinationen |
| Verständlichkeit | unklar | verständlich mit Schwächen | klar und präzise |

**Gesamtscore:** Q = (K + V + G + H + L) / 5, Wertebereich 0–2; optional Q_norm = (Q/2)·100.
**Gewichtung:** alle Kriterien gleich gewichtet, da keine priorisierte Domäne (Medizin/Recht/Sicherheit) untersucht wird — leichter zu begründen als komplexe Gewichtungen.

### 12.3 Triangulation (verbindlich)
- **Primär:** referenzbasierte manuelle Bewertung (eigene Ground Truth, nicht zirkulär, verteidigbar).
- **Sekundär:** automatisiertes Framework (RAGAS) mit Metriken wie Faithfulness und Kontextrelevanz (skalierbar, reproduzierbar).
- **Validitätsindikator:** Übereinstimmung zwischen manueller und automatisierter Bewertung wird ausgewertet. Übereinstimmung → Robustheit; Abweichung → eigener Befund zur Metrik-Zuverlässigkeit.
- RAGAS ist **nie alleinige Grundlage** (LLM-as-a-judge hat bekannte Zuverlässigkeitsgrenzen).

### 12.4 Effizienz/Kosten (abhängige Variable)
Pro Strategie erfassen: Chunk-Anzahl, Indexgröße, Token-Verbrauch (Prompt + Completion). Qualitätsunterschiede werden den Kosten gegenübergestellt („X % bessere Retrieval-Qualität bei Y× Kosten").

### 12.5 Arbeitsdefinition Halluzination
Eine Halluzination liegt vor, wenn die Antwort Informationen enthält, die weder durch die Kontextpassagen noch durch die Referenzantwort gedeckt sind oder diesen widersprechen. Bewertung 2/1/0 wie in der Rubrik.

### 12.6 Zweitbewertung (empfohlen)
10–20 % der Antworten unabhängig durch eine zweite Person bewerten lassen. Einfache Übereinstimmung = gleiche Bewertungen / alle Bewertungen, oder durchschnittliche absolute Abweichung bei 0–2-Skala. Cohen's Kappa optional.

### 12.7 Statistische Auswertung
Deskriptiv ausreichend: Mittelwert, Median, Standardabweichung, Boxplot, Vergleich nach Fragetyp, Korrelation Retrieval vs. Antwortscore. Optional Signifikanztests: Friedman-Test (mehrere verbundene Gruppen), Wilcoxon Signed-Rank (paarweise) — nur bei Sicherheit im Umgang damit.

---

## 13. Validität und Grenzen

- **Interne Validität:** Misst die Arbeit wirklich den Chunking-Einfluss? Absicherung über Konstanthaltung aller anderen Parameter, gleicher Korpus/Fragen/Prompts/Modelle, temperature 0.
- **Externe Validität:** begrenzt — ein Korpus (Vue.js), Ergebnisse liefern Hinweise, keine universelle Aussage.
- **Konstruktvalidität:** etablierte Metriken, transparente Rubrik, Bewertungsbeispiele zeigen, optional Zweitbewertung.
- **Reliabilität:** temperature 0, Rohdaten speichern, Modellversion dokumentieren, Snapshot verwenden, Prompts veröffentlichen.

---

## 14. Visualisierungen

| Visualisierung | Zweck |
|----------------|-------|
| Balkendiagramm Recall@5 je Strategie | Retrieval-Vergleich |
| Balkendiagramm MRR je Strategie | Rankingqualität |
| Boxplot Antwortscore je Strategie | Verteilung der Antwortqualität |
| Heatmap Frage × Strategie | Wo funktioniert welche Strategie? |
| Scatterplot Retrieval-Score vs. Antwortscore | Entkopplung Retrieval/Antwort (H2) |
| Bar Chart Fragetypen | Zusammensetzung des Katalogs |
| Chunk-Längen-Histogramm | Unterschiede der Strategien |
| Kosten-/Tokenvergleich | Effizienzbetrachtung (D8) |

---

## 15. Arbeitsreihenfolge (Phasenplan)

**Phase 1 – Vorbereitung:** Thema/Forschungsfrage finalisieren, Korpus (Vue.js) festlegen, Snapshot erstellen, Literaturbasis aufbauen.
**Phase 2 – Korpus und Ground Truth:** Dokumente sichten, relevante Bereiche wählen, bereinigen, Fragenkatalog erstellen, Referenzantworten formulieren, relevante Stellen annotieren.
**Phase 3 – Implementierung:** Preprocessing, Chunking C1/C2/C3, Embeddings, Vektorindizes pro Strategie, Retrieval, Antwortgenerierung, Datenspeicherung.
**Phase 4 – Evaluation:** Retrieval-Metriken berechnen, Antworten generieren und nach Rubrik bewerten, RAGAS-Sekundärbewertung, Übereinstimmung prüfen, Effizienz erfassen, Visualisierungen.
**Phase 5 – Schreiben:** Einleitung, Grundlagen, Verwandte Arbeiten, Methodik, Implementierung, Evaluation, Diskussion, Fazit.

**Minimaler Prototyp zuerst:** Markdown laden → C1/C2/C3 erzeugen → embedden → Chroma-Index pro Strategie → eine Frage abfragen → Top-5 anzeigen → Antwort generieren. Erst wenn das läuft, die große Evaluation.

---

## 16. Zeitplan (Juli–Dezember 2026)

| Zeitraum | Phase | Schwerpunkte |
|----------|-------|--------------|
| 01.–14.07. | Vorbereitung | Thema/Scope final, Arbeitsumgebung, Repository |
| 06.–27.07. | Literaturrecherche | Theoriebasis RAG/Chunking/Evaluation |
| 20.–31.07. | Forschungsfrage schärfen | Hypothesen, Abstimmung Betreuung |
| 01.–14.08. | Methodik vorbereiten | Design, Pipeline-Architektur, Evaluationsschema, Rubrik |
| 11.–24.08. | Snapshot/Korpus | Vue-Snapshot, Bereinigung, Korpusmanifest |
| 24.08.–07.09. | Datenerhebung | Fragenkatalog, Referenzantworten, Annotation |
| 07.–28.09. | Implementierung | Preprocessing, Chunking, Embedding, Retrieval, Generierung |
| 28.09.–12.10. | Datenauswertung | Experimente, Retrieval-Metriken, Antwortbewertung |
| 12.–26.10. | Analyse/Visualisierung | deskriptiv, Korrelation, Abbildungen |
| 26.10.–23.11. | Schreibphase | Theorie, Methodik, Implementierung, Ergebnisse, Diskussion |
| 23.11.–07.12. | Überarbeitung | Sprache, Argumentation, roter Faden |
| 07.–14.12. | Korrektur/Puffer | Korrektorat, Formatierung, Zitation, Reserve |
| 15.12. | Abgabe | Finalisierung und Einreichung |

> Der Fragenkatalog (Phase Datenerhebung) wird regelmäßig unterschätzt — bewusst Zeit einplanen.

---

## 17. Vom Projekt zur Bachelorarbeit (Schreibleitfaden)

**Kapitelstruktur (IU-konform, 6 Hauptkapitel):**
1. **Einleitung** — Problemstellung, Ziel, Forschungsfrage, Aufbau
2. **Theoretische Fundierung** — LLMs/Embeddings, RAG/Dense Retrieval, Chunking, Evaluation; Forschungslücke
3. **Methodik und Forschungsdesign** — Design, Korpus/Snapshot, Fragenkatalog/Ground Truth, Evaluationsverfahren (Triangulation)
4. **Präsentation und Analyse der Forschungsergebnisse** — Retrieval-Ergebnisse, Antwortbewertung, Zusammenhang Retrieval/Antwort, Effizienz (keine Interpretation im Ergebnisteil)
5. **Diskussion und Handlungsempfehlungen** — Interpretation, Einordnung in Literatur, Trade-offs, Empfehlungen, Validität
6. **Fazit und Limitationen** — Beantwortung der Forschungsfrage, Ausblick

**Wiederverwendung:** Textbausteine aus dem Exposé (Einleitung, Theorie, Methodik) dürfen in die Arbeit übernommen werden. Die Ergebnis-/Diskussionskapitel entstehen neu aus den Auswertungsdaten.

**Implementierungskapitel** (kann in Kapitel 3 oder als eigener Abschnitt vor der Evaluation stehen): Systemarchitektur, Preprocessing, Chunking, Embedding, Vector Store, Retrieval, Prompting, Antwortgenerierung, Datenspeicherung.

---

## 18. Literaturbasis (15 verifizierte Quellen)

Alle Quellen sind in `literatur.bib` enthalten und im Exposé zitiert. APA 7 / biblatex / biber.

| BibTeX-Key | Rolle in der Argumentation | Typ |
|------------|----------------------------|-----|
| `lewis2020rag` | RAG-Grundlagenpaper | NeurIPS |
| `gao2023ragsurvey` | RAG-Survey, Pipeline-Komponenten | Preprint |
| `yu2025ragevalsurvey` | Evaluation auf Komponentenebene | Springer |
| `es2024ragas` | RAGAS, sekundäre automatisierte Evaluation | EACL-Demo |
| `karpukhin2020dpr` | Dense Retrieval | EMNLP |
| `manning2008ir` | IR-Metriken: Precision, Recall, MRR | Buch |
| `reimers2019sbert` | Satz-Embeddings / semantische Ähnlichkeit | EMNLP-IJCNLP |
| `devlin2019bert` | Kontextuelle Repräsentationen (Transformer) | NAACL |
| `hladena2025chunksize` | Einfluss der Chunk-Größe | Springer |
| `jimenoyepes2024chunking` | strukturbasiertes/element-basiertes Chunking | Preprint |
| `finardi2024chronicles` | Retriever/Chunk/Generator als Einheit | Preprint |
| `ji2023hallucination` | Halluzinationen in NLG | ACM CSUR |
| `taiwo2026chunking` | Chunking-Vergleich (Öl & Gas) – domänenfremde Lücke | Preprint |
| `gomezcabello2025chunking` | Chunking-Vergleich (klinisch) – domänenfremde Lücke | Bioengineering |
| `qu2025semanticchunking` | semantisch/struktur ≠ konsistent besser → starke Baseline, „nicht trivial" | NAACL Findings |

> Nicht zitierfähig, aber in „Verwandte Arbeiten" zu erwähnen: der Praktiker-Blogbeitrag (Mai 2026) mit nahezu identischem Setup auf FastAPI/Supabase/Stripe.

---

## 19. Offene Entscheidungen / vor Beginn zu bestätigen

- **Exposé-Umfang:** Aktuelle Fassung ist näher an „Betreuungsanfrage" (2–3 Seiten). Die IU-Formvorgabe nennt 5 Seiten ±10 %. Falls das Exposé als reguläre IU-Abgabe zählt, Theorie und Methodik entsprechend ausbauen (jeder Unterabschnitt ≥ ½ Seite).
- **Exakter Vue-Korpus-Ausschnitt:** finale Auswahl der `src/guide/`-Bereiche und Seitenzahl festlegen (Ziel 50–100 Dateien).
- **Modell-/Versionswahl:** konkretes GPT-Modell, Embedding-Modell (`-large` vs. `-small`), SDK-/API-Version zum Implementierungszeitpunkt fixieren und dokumentieren.
- **Embedding-Sprache:** Korpus ist englisch; Fragen/Referenzantworten englisch halten (Konsistenz mit Embedding-Raum).
- **Zweitbewertung:** Verfügbarkeit einer zweiten bewertenden Person klären (stärkt Konstruktvalidität).
- **C4 (semantisch):** nur einplanen, wenn Phasen 1–4 planmäßig laufen.

---

## 20. Schreibstil- und Formregeln (IU)

- APA 7 (IU-Zitierleitfaden), nur tatsächlich zitierte Quellen, alphabetisch, hängender Einzug.
- Wissenschaftlich, sachlich, objektiv, präzise; keine Ich-/Wir-/„man"-Formen, keine Umgangssprache, keine Floskeln, keine Ausrufezeichen, keine wertenden Aussagen.
- Passive/neutrale Formulierungen bevorzugen, klarer roter Faden (Problem → Forschungsfrage → Theorie → Methodik → Ergebnisse → Diskussion).
- Maximal 3 Gliederungsebenen (1 / 1.1 / 1.1.1), jede Untergliederung mindestens zwei Unterpunkte.
- **(Unter-)Überschrift nur, wenn darunter mindestens ca. eine halbe Seite Text folgt** — sonst keine eigene Überschrift, Inhalt in Fließtext integrieren.
- Hauptteil 40 Textseiten ±10 % (36–44); Abbildungs-/Tabellenverzeichnis ab 3 Abbildungen/Tabellen; Quellenangabe direkt unter Abbildungen/Tabellen (10 pt).
- Ergebnisteil ohne Interpretation; Interpretation in Diskussion.

---

*Ende des Ground-Truth-Dokuments. Bei jeder Abweichung im Projektverlauf gilt: Änderung hier eintragen, damit dieses Dokument die einzige verbindliche Referenz bleibt.*
