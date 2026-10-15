# Konfiguration (`src/config.py`)

> Seitentyp: Nachschlagen (reference). Stand: 14.10.2026. Übersicht: [Dokumentation](../README.md).

Alle Parameter des Experiments stehen ausschließlich in [`src/config.py`](../../src/config.py); **die Datei ist
maßgeblich**, diese Seite beschreibt sie. Weicht ein Wert hier ab, gilt `config.py` und diese Seite ist zu
korrigieren. Andere Seiten der Dokumentation nennen Parameterwerte nicht, sondern verlinken hierher. Gruppen und
Reihenfolge wie in `config.py`; Pfade relativ zur Repo-Wurzel (`ROOT`).

## Pfade

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `ROOT` | `Path`, Repo-Wurzel | Basis aller Pfade | – |
| `DATA_RAW` | `data/raw/vue_docs_snapshot` | Rohdateien des Snapshots | [ADR 0019](../adr/0019-korpus-ausschnitt.md) |
| `DATA_PROCESSED` | `data/processed` | Zwischenstände (Dokumente, Abschnitte, Chunks, Vektoren) | – |
| `DATA_EVAL` | `data/evaluation` | Fragen, Ground Truth, Ergebnisse | – |
| `PILOT_DIR` | `data/pilot` | Pilotproben, nicht der Fragenkatalog (`scripts/difficulty_probe.py`) | [ADR 0027](../adr/0027-blinde-annotation.md) |
| `PILOT_RUNS_FILE_NAME` | `"runs.jsonl"` | Laufprotokoll je Pilot-Set; die übrigen Pilotdateien tragen die Namen der Evaluationsartefakte | – |
| `CHROMA_DIR` | `chroma_db` | Chroma-Index (lokal, persistent) | [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `DOCS_DIR` | `docs` | Dokumentation | – |
| `DOCUMENTS_FILE` | `data/processed/documents.jsonl` | Dokumente nach Ingest/Preprocessing | – |
| `SNAPSHOT_INFO_FILE` | `docs/corpus_snapshot.txt` | Snapshot-Datensatz (versioniert): Commit, Daten, SHA-256 je Datei | [ADR 0019](../adr/0019-korpus-ausschnitt.md) |
| `SECTIONS_FILE` | `data/processed/sections.jsonl` | H1–H3-Abschnitte mit Token-Spannen | [ADR 0019](../adr/0019-korpus-ausschnitt.md) |
| `SECTION_INDEX_FILE` | `data/processed/section_index.md` | Abschnitts-Nachschlageliste für die Annotation (`catalogue.py sections`) | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `CORPUS_MANIFEST_FILE` | `docs/corpus_manifest.csv` | Korpusmanifest (versioniert) | – |
| `CHUNKS_C1_FILE`, `CHUNKS_C2_FILE`, `CHUNKS_C3_FILE` | `data/processed/chunks_c1.jsonl`, `chunks_c2.jsonl`, `chunks_c3.jsonl` | Chunks je Strategie | [ADR 0005](../adr/0005-drei-chunking-strategien.md) |
| `QUESTIONS_FILE` | `data/evaluation/questions.csv` | Fragenkatalog | [ADR 0017](../adr/0017-fragenkatalog.md) |
| `GROUND_TRUTH_FILE` | `data/evaluation/ground_truth.csv` | Referenzantworten und relevante Abschnitte | [ADR 0017](../adr/0017-fragenkatalog.md) |
| `CATALOGUE_PLAN_FILE` | `data/evaluation/catalogue_plan.csv` | Stichprobenplan der Slots | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `CATALOGUE_REVIEW_FILE` | `data/evaluation/catalogue_review.csv` | Vorschläge und Entscheidungen der KI-Durchsicht | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `CATALOGUE_FREEZE_FILE` | `data/evaluation/catalogue_freeze.json` | Freeze-Datensatz des Katalogs (Datum, Anzahlen, SHA-256) | [ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md) |
| `RETRIEVED_RESULTS_FILE` | `data/evaluation/retrieved_results.csv` | Top-k je Frage und Strategie | – |
| `CONTROL_RETRIEVED_FILE` | `data/evaluation/retrieved_results_control.csv` | Top-k der Kontrolle K1 | [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |
| `GENERATED_ANSWERS_FILE` | `data/evaluation/generated_answers.csv` | generierte Antworten | – |
| `SCORES_FILE` | `data/evaluation/scores.csv` | Rubrik-Bewertungen | [ADR 0013](../adr/0013-antwort-rubrik.md) |

Formate aller Dateien: [Datenartefakte und Formate](data-formats.md).

## Korpus

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `VUE_DOCS_REPO_URL` | `"https://github.com/vuejs/docs.git"` | Quell-Repository | [ADR 0001](../adr/0001-korpus-vuejs.md) |
| `VUE_DOCS_COMMIT` | `"40aa88af0094f7bab4aaf786e55c748a6a251d88"` | fester Commit (15.09.2026) | [ADR 0025](../adr/0025-korpus-guide-api-styleguide.md) |
| `VUE_DOCS_ROOT` | `"src"` | Dokumentationswurzel im Repository | – |
| `VUE_DOCS_AREAS` | `("api", "guide", "style-guide")` | Bereiche unter `VUE_DOCS_ROOT`; der Snapshot spiegelt sie unter `DATA_RAW` | [ADR 0025](../adr/0025-korpus-guide-api-styleguide.md) |
| `VUE_DOCS_EXCLUDED` | Tupel aus 7 Pfaden: `api/component-instance.md`, `api/index.md`, `api/options-composition.md`, `api/options-lifecycle.md`, `api/options-misc.md`, `api/options-rendering.md`, `api/options-state.md` | ausgeschlossene Seiten (nur Options API, generierter API-Index); jede muss am Commit existieren | [ADR 0025](../adr/0025-korpus-guide-api-styleguide.md) |
| `TOKEN_ENCODING` | `"cl100k_base"` | Token-Kodierung (`tiktoken` 0.13.0, gepinnt in `pyproject.toml`) | [ADR 0019](../adr/0019-korpus-ausschnitt.md) |
| `SECTION_MAX_LEVEL` | `3` | H1–H3 werden Abschnitte (`sections.jsonl`, C3-Grenzen) | [ADR 0019](../adr/0019-korpus-ausschnitt.md), [ADR 0021](../adr/0021-c3-grenzen.md) |

Umfang und Bereinigung des Korpus: [Korpus](corpus.md).

## Chunking

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `C1_CHUNK_SIZE` | `500` | C1: Fenstergröße in Tokens | [ADR 0005](../adr/0005-drei-chunking-strategien.md) |
| `C1_OVERLAP` | `0` | C1: ohne Overlap | [ADR 0005](../adr/0005-drei-chunking-strategien.md) |
| `C2_CHUNK_SIZE` | `500` | C2: Fenstergröße in Tokens | [ADR 0005](../adr/0005-drei-chunking-strategien.md), [ADR 0010](../adr/0010-starke-baseline.md) |
| `C2_OVERLAP` | `100` | C2: Overlap in Tokens | [ADR 0005](../adr/0005-drei-chunking-strategien.md), [ADR 0010](../adr/0010-starke-baseline.md) |
| `C3_MAX_TOKENS` | `800` | C3: harte Obergrenze je Chunk; zu lange Abschnitte werden an Absätzen geteilt | [ADR 0021](../adr/0021-c3-grenzen.md), [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |
| `C3_MIN_TOKENS` | `50` | C3: Untergrenze; kürzere Segmente verschmelzen zuerst mit einem Nachbarn | [ADR 0021](../adr/0021-c3-grenzen.md) |
| `K1_CHUNK_SIZE` | `231` | Kontrolle K1: Fenstergröße = kaufmännisch gerundetes Mittel der C3-Chunklängen (gemessen 14.10.2026 auf `40aa88a`); `chunking.py` bricht ab, wenn der Wert nicht mehr der Regel entspricht | [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |
| `K1_OVERLAP` | `0` | K1: ohne Overlap | [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |
| `CONTROL_STRATEGIES` | `{"K1": "fixed_231_no_overlap"}` (aus `K1_CHUNK_SIZE` gebildet) | Schlüssel und `strategy`-Wert der Kontrolle; nur Retrieval, keine Generierung | [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |
| `STRATEGY_IDS` | `{"C1": "fixed_500_no_overlap", "C2": "fixed_500_overlap_100", "C3": "structure_h2h3"}` | Schlüssel und `strategy`-Werte des Experiments (C1–C3); K1 gehört nicht hinein | [ADR 0005](../adr/0005-drei-chunking-strategien.md) |
| `CHUNK_FILES` | `{"C1": CHUNKS_C1_FILE, "C2": …, "C3": …}` | Chunk-Datei je Strategie | – |
| `EMBEDDING_FILES` | `{"C1": data/processed/embeddings_c1.npz, …c2, …c3}` | gespeicherte Referenzvektoren je Strategie | [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `QUERY_EMBEDDINGS_FILE` | `data/evaluation/query_embeddings.npz` | gespeicherte Fragevektoren | [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `EMBEDDING_RUNS_FILE` | `data/processed/embedding_runs.jsonl` | Laufprotokoll von `embed.py` und `retrieve.py` (Modell, Versionen, Tokens, Kosten) | [ADR 0008](../adr/0008-kosten-als-variable.md), [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `CHROMA_COLLECTIONS` | `{"C1": "rag_c1", "C2": "rag_c2", "C3": "rag_c3"}` | Chroma-Collection je Strategie | [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `CONTROL_CHUNK_FILES` | `{"K1": data/processed/chunks_k1.jsonl}` | Chunk-Datei der Kontrolle | [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |
| `CONTROL_EMBEDDING_FILES` | `{"K1": data/processed/embeddings_k1.npz}` | Vektordatei der Kontrolle | [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |
| `CONTROL_COLLECTIONS` | `{"K1": "rag_k1"}` | Chroma-Collection der Kontrolle | [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |

Die Kontrolle hat eigene `CONTROL_*`-Zuordnungen, damit sie nie in die Schleifen über `STRATEGY_IDS` gerät.

## Retrieval

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `TOP_K` | `5` | abgerufene Chunks je Frage; konstant, nie variieren | [ADR 0014](../adr/0014-temperatur-und-topk.md) |
| `SCORE_TOLERANCE` | `1e-5` | erlaubte Abweichung zwischen Chromas Score und exaktem NumPy-Kosinus (float32) | [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `HNSW_MIN_BREADTH` | `100` | HNSW `ef_search` und `ef_construction` = max(Collection-Größe, Wert); ≥ Größe heißt erschöpfende Suche (100 = Chroma-Standard) | [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `CHROMA_SPACE` | `"cosine"` | Distanzmaß; Ähnlichkeit = 1 − Distanz | [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `CANARY_MIN_COSINE` | `0.999` | Schwelle der Modellstand-Prüfung; darunter Abbruch (gemessen 13.10.2026: gleiches Modell ≥ 0,99996, verschiedene Chunks ≤ 0,84) | [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `CANARY_PROBE_POSITIONS` | `(0.0, 0.5, 1.0)` | relative Positionen der erneut eingebetteten Texte je Vektordatei (erster, mittlerer, letzter) | [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `ID_SEPARATOR` | `";"` | Trennzeichen mehrerer IDs in einem Feld von `ground_truth.csv` | – |
| `RELEVANCE_MIN_OVERLAP` | `1` | Hauptregel: Chunk relevant bei mindestens so vielen Tokens Überlappung mit einem relevanten Abschnitt (jede Überlappung) | [ADR 0019](../adr/0019-korpus-ausschnitt.md) |
| `SENSITIVITY_MIN_OVERLAP` | `100` | Sensitivitätsprüfung: benötigt werden min(100, Chunk-Länge) Tokens, mindestens 1 (`relevance.is_relevant`); noch nicht in einem Auswertungsskript verwendet | [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |

Metriken und Relevanzregel: [Evaluation](evaluation.md).

## Fragenkatalog

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `QUESTION_TYPES` | `{"factual": 12, "procedural": 12, "conceptual": 12, "comparative": 6, "limitation": 6}` | erlaubte Werte von `type` mit Quote | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `QUESTION_CLASSES` | `{"single": 12, "multi-section": 12, "detail": 12, "paraphrase": 12}` | erlaubte Werte von `difficulty` (Konstruktionsklasse) mit Quote; Summe 48 | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `AREA_MIN_QUESTIONS` | `{"api": 12, "style-guide": 3}` | Mindestzahl Fragen mit einem relevanten Abschnitt im Bereich | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `DETAIL_MAX_ANSWER_WORDS` | `30` | `detail`: Referenzantwort höchstens so viele Wörter | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `MULTI_SECTION_MIN_SECTIONS` | `2` | `multi-section`: mindestens so viele unabhängige relevante Abschnitte (ein Abschnitt innerhalb eines anderen angegebenen zählt nicht) | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `SINGLE_CLASS_SECTIONS` | `1` | `single`, `detail`, `paraphrase`: genau so viele relevante Abschnitte | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `CATALOGUE_REPORT_MIN_PAGES` | `2` | Bericht von `check`: Anzahl der `multi-section`-Fragen mit Abschnitten auf mindestens so vielen Seiten (nur Anzeige, keine Regel) | – |
| `CATALOGUE_EXCERPT_CHARS` | `60` | `catalogue.py find`: Zeichen Kontext je Seite eines Treffers (nie über den Abschnitt hinaus) | – |
| `CATALOGUE_HEADING_SEPARATOR` | `" › "` | Trenner im Überschriftenpfad (`section_index.md`, `find`, `show`) | – |
| `CATALOGUE_WORD_PATTERN` | `r"[a-z0-9]+"` | Wörter für den Paraphrase-Vergleich (nach Kleinschreibung) | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `CATALOGUE_CAMEL_BOUNDARY` | `r"(?<=[a-z0-9])(?=[A-Z])"` | camelCase-Grenze; Bezeichner zählen auch mit ihren Teilen | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `CATALOGUE_FOLD_MIN_LENGTH` | `4` | ab dieser Länge auch ohne `s`/`es`, mit `ies` → `y` | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `CATALOGUE_PREFIX_MIN`, `CATALOGUE_PREFIX_SLACK` | `4`, `3` | gleicher Anfang von mindestens max(4, kürzere Länge − 3) Zeichen gilt als gleiches Wort | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `CATALOGUE_SEED` | `20261014` | Seed des Stichprobenplans (Tag der Entscheidung; nie angepasst) | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `CATALOGUE_AREA_SLOTS` | `{"api": 12, "style-guide": 3, "guide": 33}` | Slots je Bereich (Summe 48) | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `CATALOGUE_RESERVE` | `{"api": 12, "style-guide": 3, "guide": 33}` | Reserveabschnitte je Bereich für Sprünge | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `CATALOGUE_SKIP_REASONS` | `("code-or-links", "too-short", "duplicate-topic", "no-answerable-content")` | erlaubte Gründe für einen Sprung | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `CATALOGUE_SKIP_MIN_TOKENS` | `50` | `too-short` nur für Abschnitte unter so vielen Tokens | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `CATALOGUE_SLOT_FORMAT` | `"S{:02d}"` | Format der Slot-IDs im Plan (S01 … S48) | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `CATALOGUE_PLAN_STATUSES` | `("open", "used", "skipped", "reserve")` | Werte von `status` in `catalogue_plan.csv` | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `CATALOGUE_REVIEW_KINDS`, `CATALOGUE_REVIEW_DECISIONS` | `("missing_section", "wording", "fact", "class")`, `("open", "accepted", "rejected")` | Arten und Entscheidungen der KI-Durchsicht | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `QUESTION_ID_PATTERN`, `QUESTION_ID_FORMAT` | `r"Q\d+"`, `"Q{:03d}"` | Muster vorhandener und Format neuer Frage-IDs (Editor) | – |
| `CATALOGUE_STOPWORDS` | Tupel englischer Funktions- und Fragewörter plus `v` (Präfix der Direktiven) und `vue` | beim Vergleich ignoriert | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |

## LLM und Embedding

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `EMBEDDING_MODEL` | `"text-embedding-3-large"` | Embedding-Modell (nur als Alias angeboten, daher Vektoren einmal speichern) | [ADR 0023](../adr/0023-embedding-modell.md), [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `EMBEDDING_DIMENSIONS` | `3072` | Vektordimension (Modellstandard) | [ADR 0023](../adr/0023-embedding-modell.md) |
| `EMBEDDING_BATCH_SIZE` | `100` | Texte je API-Anfrage (API-Grenze: ≤ 2.048 Eingaben, ≤ 300.000 Tokens) | [ADR 0023](../adr/0023-embedding-modell.md) |
| `EMBEDDING_PRICE_PER_MTOK` | `0.13` | USD je 1 Mio. Eingabe-Tokens (OpenAI-Modellseite, abgerufen 13.10.2026); Grundlage von `cost_usd` | [ADR 0008](../adr/0008-kosten-als-variable.md), [ADR 0023](../adr/0023-embedding-modell.md) |
| `LLM_MODEL` | `"gpt-4o"` | **Platzhalter**; exakter Snapshot wird bei der Umsetzung von `generate.py` gepinnt | [ADR 0016](../adr/0016-modell-neutralitaet.md) |
| `LLM_TEMPERATURE` | `0.0` | konstant für Reproduzierbarkeit | [ADR 0014](../adr/0014-temperatur-und-topk.md) |
| `LLM_MAX_TOKENS` | `1024` | Obergrenze der Antwortlänge | – |

## Evaluation

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `RUBRIC_CRITERIA` | `["correctness", "completeness", "groundedness", "no_hallucination", "clarity"]` | Rubrik-Kriterien = Spalten in `scores.csv` | [ADR 0013](../adr/0013-antwort-rubrik.md) |
| `RUBRIC_MAX_SCORE` | `2` | Höchstwert je Kriterium (Skala 0–2) | [ADR 0013](../adr/0013-antwort-rubrik.md) |
