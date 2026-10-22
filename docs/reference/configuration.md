# Konfiguration (`src/config.py`)

*[Doku-Index](../README.md) · Referenz · Verwandt: [Datenformate](data-formats.md), [Evaluation](evaluation.md), [Werkzeuge](tooling.md)*

Alle Parameter des Experiments stehen ausschließlich in [`src/config.py`](../../src/config.py); **die Datei ist
maßgeblich**, diese Seite beschreibt sie. Weicht ein Wert hier ab, gilt `config.py` und diese Seite ist zu
korrigieren. Andere Seiten dürfen einen Wert nur zusammen mit seinem Schlüssel (`config.X`) nennen und verlinken
hierher. Abschnitte und Reihenfolge der Zeilen wie in `config.py`; Pfade relativ zur Repo-Wurzel (`ROOT`). Spalte
„Entscheidung“: die ADR, unter der der Wert steht (dahinter die ADR, die ihn zuletzt geändert oder ergänzt hat);
setzt erst ein Design-Dokument die Zahl, folgt ein Link „Spec“ darauf. Umgebungsvariablen (`OPENAI_API_KEY`,
`SCORING_RATER`, `PAPERLAB_FONTS`, `RAGAS_DO_NOT_TRACK`) stehen nicht hier, sondern in
[Werkzeuge](tooling.md#umgebungsvariablen).

## Pfade

Formate aller Dateien: [Datenformate](data-formats.md).

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `ROOT` | `Path`, Repo-Wurzel | Basis aller Pfade | – |
| `DATA_RAW` | `data/raw/e2e_docs_snapshot` | Rohdateien des Snapshots | [ADR 0019](../adr/0019-korpus-ausschnitt.md), [ADR 0038](../adr/0038-korpus-e2e.md) |
| `DATA_PROCESSED` | `data/processed` | Zwischenstände (Dokumente, Abschnitte, Chunks, Vektoren) | – |
| `DATA_EVAL` | `data/evaluation` | Fragen, Ground Truth, Ergebnisse | – |
| `PILOT_DIR` | `data/pilot` | Pilotproben, nicht der Fragenkatalog (`scripts/difficulty_probe.py`) | – |
| `PILOT_RUNS_FILE_NAME` | `"runs.jsonl"` | Laufprotokoll je Pilot-Set; die übrigen Pilotdateien tragen die Namen der Evaluationsartefakte | – |
| `CHROMA_DIR` | `chroma_db` | Chroma-Index (lokal, persistent) | – |
| `DOCS_DIR` | `docs` | Dokumentation | – |
| `DOCUMENTS_FILE` | `data/processed/documents.jsonl` | Dokumente nach Ingest/Preprocessing | – |
| `SNAPSHOT_INFO_FILE` | `docs/corpus_snapshot.txt` | Snapshot-Datensatz: Commit, Daten, SHA-256 je Datei | [ADR 0038](../adr/0038-korpus-e2e.md), [Spec](../superpowers/specs/2026-10-18-e2e-snapshot-design.md) |
| `SECTIONS_FILE` | `data/processed/sections.jsonl` | H1–H3-Abschnitte mit Token-Spannen | [ADR 0019](../adr/0019-korpus-ausschnitt.md), [ADR 0022](../adr/0022-h1-abschnitte-in-ground-truth.md) |
| `SECTION_INDEX_FILE` | `data/processed/section_index.md` | Abschnitts-Nachschlageliste für die Annotation (`catalogue.py sections`) | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `CORPUS_MANIFEST_FILE` | `docs/corpus_manifest.csv` | Korpusmanifest | – |
| `CHUNKS_C1_FILE`, `CHUNKS_C2_FILE`, `CHUNKS_C3_FILE` | `data/processed/chunks_c1.jsonl`, `chunks_c2.jsonl`, `chunks_c3.jsonl` | Chunks je Strategie | [ADR 0005](../adr/0005-drei-chunking-strategien.md) |
| `QUESTIONS_FILE` | `data/evaluation/questions.csv` | Fragenkatalog | [ADR 0017](../adr/0017-fragenkatalog.md) |
| `GROUND_TRUTH_FILE` | `data/evaluation/ground_truth.csv` | Referenzantworten und relevante Abschnitte | [ADR 0017](../adr/0017-fragenkatalog.md) |
| `CATALOGUE_FREEZE_FILE` | `data/evaluation/catalogue_freeze.json` | Freeze-Datensatz des Katalogs (Datum, Anzahlen, SHA-256) | [ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md) |
| `CATALOGUE_PLAN_FILE` | `data/evaluation/catalogue_plan.csv` | Stichprobenplan der Slots | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `CATALOGUE_REVIEW_FILE` | `data/evaluation/catalogue_review.csv` | Vorschläge und Entscheidungen der KI-Durchsicht | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `CLOSED_BOOK_FILE` | `data/evaluation/closed_book_screen.csv` | Antworten ohne Kontext und Urteile | [ADR 0040](../adr/0040-closed-book-pruefung.md) |
| `RETRIEVED_RESULTS_FILE` | `data/evaluation/retrieved_results.csv` | Top-k je Frage und Strategie | – |
| `CONTROL_RETRIEVED_FILE` | `data/evaluation/retrieved_results_control.csv` | Top-k der Kontrolle K1 | [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |
| `GENERATED_ANSWERS_FILE` | `data/evaluation/generated_answers.csv` | generierte Antworten (nie überschrieben) | [ADR 0033](../adr/0033-antwortmodell.md) |
| `GENERATED_ANSWERS_CONTROL_FILE` | `data/evaluation/generated_answers_control.csv` | Antworten der Kontrolle K0 (nie überschrieben) | [ADR 0041](../adr/0041-kontrolle-k0.md) |
| `GENERATION_RUNS_FILE` | `data/evaluation/generation_runs.jsonl` | Laufprotokoll der Antwort-, Bewertungs-, RAGAS- und Zweitbewertungsschritte und der Closed-Book-Prüfung ([Schritte](data-formats.md#laufprotokoll)) | [ADR 0008](../adr/0008-kosten-als-variable.md), [ADR 0033](../adr/0033-antwortmodell.md) |
| `SCORES_FILE` | `data/evaluation/scores.csv` | Rubrik-Bewertungen mit Strategie (abgeleitet aus Bogen und Schlüssel) | [ADR 0013](../adr/0013-antwort-rubrik.md) |
| `SCORING_SHEET_FILE` | `data/evaluation/scoring_sheet.csv` | Bewertungsbogen der blinden Bewertung | [ADR 0032](../adr/0032-blinde-rubrik-bewertung.md) |
| `SCORING_PACKET_FILE` | `data/evaluation/scoring_packet.md` | Lesepaket der blinden Bewertung | [ADR 0032](../adr/0032-blinde-rubrik-bewertung.md) |
| `SCORING_KEY_FILE` | `data/evaluation/scoring_key.csv` | Schlüssel Code → Strategie | [ADR 0032](../adr/0032-blinde-rubrik-bewertung.md) |
| `SCORING_ITEMS_FILE` | `data/evaluation/scoring_items.jsonl` | blinde Einträge der Bewertungsseite | [ADR 0034](../adr/0034-bewertung-in-der-app.md) |
| `KEY_POINTS_FILE` | `data/evaluation/key_points.csv` | Kernpunkte je Frage, vor der Bewertung eingefroren | [ADR 0035](../adr/0035-regelbasierte-bewertung.md) |
| `SCORING_CHECKS_FILE` | `data/evaluation/scoring_checks.csv` | Antworten auf die Prüffragen je Code | [ADR 0035](../adr/0035-regelbasierte-bewertung.md) |
| `SCORING_ITEMS_CONTROL_FILE`, `SCORING_SHEET_CONTROL_FILE`, `SCORING_CHECKS_CONTROL_FILE`, `SCORES_CONTROL_FILE` | `data/evaluation/scoring_items_control.jsonl`, `…/scoring_sheet_control.csv`, `…/scoring_checks_control.csv`, `…/scores_control.csv` | Bewertungssatz der Kontrolle K0 | [ADR 0041](../adr/0041-kontrolle-k0.md) |
| `RETRIEVAL_SCORES_FILE` | `data/evaluation/retrieval_scores.csv` | Retrieval-Metriken je Frage, Strategie und Relevanzregel | [ADR 0012](../adr/0012-retrieval-metriken.md) |
| `CONTROL_RETRIEVAL_SCORES_FILE` | `data/evaluation/retrieval_scores_control.csv` | dasselbe für die Kontrolle K1 | [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |

## Korpus

Umfang und Bereinigung des Korpus: [Korpus](corpus.md).

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `CORPUS_REPO_URL` | `"https://github.com/tester-army/e2e.git"` | Quell-Repository | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_COMMIT` | `"ef977f4856da009cac26d78d2e9bb14e5991ee41"` | fester Commit (17.10.2026) | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_ROOT` | `"docs"` | Dokumentationswurzel im Repository; der Snapshot spiegelt sie unter `DATA_RAW` | – |
| `CORPUS_PAGE_SUFFIX` | `".mdx"` | Seitendateien unter `CORPUS_ROOT`; ihre Menge muss den Seiten der Navigation entsprechen | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_NAV_FILE` | `"docs.json"` | Navigation (Tabs, Gruppen, Seiten); liefert die Bereiche | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_PROVIDER_SNIPPET` | `"snippets/model-provider.jsx"` | Daten der Komponente `<ModelProvider>` (Anbieterliste) | [ADR 0038](../adr/0038-korpus-e2e.md), [Spec](../superpowers/specs/2026-10-18-e2e-snapshot-design.md) |
| `CORPUS_SUPPORT_FILES` | `(CORPUS_NAV_FILE, CORPUS_PROVIDER_SNIPPET)` | mit den Seiten kopiert und im Snapshot-Datensatz geprüft | – |
| `CORPUS_AREAS` | Tupel der 15 Navigationsgruppen in Reihenfolge (Get started … Engine contract, Examples) | Bereiche; `ingest.py` bricht ab, wenn die Navigation abweicht | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `TOKEN_ENCODING` | `"cl100k_base"` | Token-Kodierung (`tiktoken` 0.13.0, gepinnt in `pyproject.toml`) | [ADR 0019](../adr/0019-korpus-ausschnitt.md) |
| `SECTION_MAX_LEVEL` | `3` | H1–H3 werden Abschnitte (`sections.jsonl`, C3-Grenzen) | [ADR 0019](../adr/0019-korpus-ausschnitt.md), [ADR 0021](../adr/0021-c3-grenzen.md), [ADR 0022](../adr/0022-h1-abschnitte-in-ground-truth.md) |

## Chunking

Begründung der Strategien: [Forschungsdesign](../explanation/research-design.md#chunking-strategien). Die Kontrollen
haben eigene `CONTROL_*`-Zuordnungen, damit sie nie in die Schleifen über `STRATEGY_IDS` geraten.

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `C1_CHUNK_SIZE` | `500` | C1: Fenstergröße in Tokens | [ADR 0005](../adr/0005-drei-chunking-strategien.md) |
| `C1_OVERLAP` | `0` | C1: ohne Overlap | [ADR 0005](../adr/0005-drei-chunking-strategien.md) |
| `C2_CHUNK_SIZE` | `500` | C2: Fenstergröße in Tokens | [ADR 0005](../adr/0005-drei-chunking-strategien.md), [ADR 0010](../adr/0010-starke-baseline.md) |
| `C2_OVERLAP` | `100` | C2: Overlap in Tokens | [ADR 0005](../adr/0005-drei-chunking-strategien.md), [ADR 0010](../adr/0010-starke-baseline.md) |
| `C3_MAX_TOKENS` | `800` | C3: harte Obergrenze je Chunk; zu lange Abschnitte werden an Absätzen geteilt | [ADR 0005](../adr/0005-drei-chunking-strategien.md), [ADR 0021](../adr/0021-c3-grenzen.md) |
| `C3_MIN_TOKENS` | `50` | C3: Untergrenze; kürzere Segmente verschmelzen zuerst mit einem Nachbarn | [ADR 0021](../adr/0021-c3-grenzen.md) |
| `K1_CHUNK_SIZE` | `375` | Kontrolle K1: Fenstergröße = kaufmännisch gerundetes Mittel der C3-Chunklängen (gemessen 18.10.2026 auf `ef977f4`); `chunking.py` bricht ab, wenn der Wert nicht mehr der Regel entspricht | [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |
| `K1_OVERLAP` | `0` | K1: ohne Overlap | [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |
| `CONTROL_STRATEGIES` | `{"K1": "fixed_375_no_overlap"}` (aus `K1_CHUNK_SIZE` gebildet) | Schlüssel und `strategy`-Wert der Kontrolle; nur Retrieval, keine Generierung | [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |
| `CONTROL_ANSWER_STRATEGIES` | `{"K0": "closed_book"}` | Kontrolle K0: Antworten ohne Retrieval (Closed-Book-Prompt); nicht in `STRATEGY_IDS` | [ADR 0041](../adr/0041-kontrolle-k0.md) |
| `STRATEGY_IDS` | `{"C1": "fixed_500_no_overlap", "C2": "fixed_500_overlap_100", "C3": "structure_h2h3"}` | Schlüssel und `strategy`-Werte des Experiments (C1–C3); K1 gehört nicht hinein | [ADR 0005](../adr/0005-drei-chunking-strategien.md) |
| `CHUNK_FILES` | `{"C1": CHUNKS_C1_FILE, "C2": …, "C3": …}` | Chunk-Datei je Strategie | – |
| `EMBEDDING_FILES` | `{"C1": data/processed/embeddings_c1.npz, …c2, …c3}` | gespeicherte Referenzvektoren je Strategie | [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `QUERY_EMBEDDINGS_FILE` | `data/evaluation/query_embeddings.npz` | gespeicherte Fragevektoren | [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `EMBEDDING_RUNS_FILE` | `data/processed/embedding_runs.jsonl` | Laufprotokoll von `embed.py`, `retrieve.py` und `evaluate_retrieval.py` ([Schritte](data-formats.md#laufprotokoll)) | [ADR 0008](../adr/0008-kosten-als-variable.md), [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `CHROMA_COLLECTIONS` | `{"C1": "rag_c1", "C2": "rag_c2", "C3": "rag_c3"}` | Chroma-Collection je Strategie | [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `CONTROL_CHUNK_FILES` | `{"K1": data/processed/chunks_k1.jsonl}` | Chunk-Datei der Kontrolle | [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |
| `CONTROL_EMBEDDING_FILES` | `{"K1": data/processed/embeddings_k1.npz}` | Vektordatei der Kontrolle | [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |
| `CONTROL_COLLECTIONS` | `{"K1": "rag_k1"}` | Chroma-Collection der Kontrolle | [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |

## Retrieval

Metriken und Relevanzregel: [Evaluation](evaluation.md).

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `TOP_K` | `5` | abgerufene Chunks je Frage; konstant, nie variieren | [ADR 0014](../adr/0014-temperatur-und-topk.md) |
| `SCORE_TOLERANCE` | `1e-5` | erlaubte Abweichung zwischen Chromas Score und exaktem NumPy-Kosinus (float32) | [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `HNSW_MIN_BREADTH` | `100` | HNSW `ef_search` und `ef_construction` = max(Collection-Größe, Wert); ≥ Größe heißt erschöpfende Suche (100 = Chroma-Standard) | [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `CHROMA_SPACE` | `"cosine"` | Distanzmaß; Ähnlichkeit = 1 − Distanz | [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `CANARY_MIN_COSINE` | `0.999` | Schwelle der Modellstand-Prüfung; darunter Abbruch (gemessen 13.10.2026: gleiches Modell ≥ 0,99996, verschiedene Chunks ≤ 0,84) | [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `CANARY_PROBE_POSITIONS` | `(0.0, 0.5, 1.0)` | relative Positionen der erneut eingebetteten Texte je Vektordatei (erster, mittlerer, letzter) | [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `ID_SEPARATOR` | `";"` | Trennzeichen mehrerer IDs in einem Feld von `ground_truth.csv` und in `sources` von `generated_answers*.csv` | – |
| `RELEVANCE_MIN_OVERLAP` | `1` | Hauptregel: Chunk relevant bei mindestens so vielen Tokens Überlappung mit einem relevanten Abschnitt (jede Überlappung) | [ADR 0019](../adr/0019-korpus-ausschnitt.md) |
| `SENSITIVITY_MIN_OVERLAP` | `100` | Sensitivitätsprüfung: benötigt werden min(100, Chunk-Länge) Tokens, mindestens 1 (`relevance.is_relevant`); von `evaluate_retrieval.py` als Regel `sensitivity` ausgewertet | [ADR 0019](../adr/0019-korpus-ausschnitt.md), [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |

## Fragenkatalog

Regeln des Katalogs: [Fragenkatalog](question-catalogue.md).

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `QUESTION_TYPES` | `{"factual": 12, "procedural": 12, "conceptual": 12, "comparative": 6, "limitation": 6}` | erlaubte Werte von `type` mit Quote | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `QUESTION_CLASSES` | `{"single": 12, "multi-section": 12, "detail": 12, "paraphrase": 12}` | erlaubte Werte von `difficulty` (Konstruktionsklasse) mit Quote; Summe 48 | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `AREA_MIN_QUESTIONS` | 15 Bereiche, gleich den Slots ([Korpus](corpus.md#bereiche)) | Mindestzahl Fragen mit einem relevanten Abschnitt im Bereich | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md), [ADR 0039](../adr/0039-stichprobenplan-e2e.md) |
| `DETAIL_MAX_ANSWER_WORDS` | `30` | `detail`: Referenzantwort höchstens so viele Wörter | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `MULTI_SECTION_MIN_SECTIONS` | `2` | `multi-section`: mindestens so viele unabhängige relevante Abschnitte (ein Abschnitt innerhalb eines anderen angegebenen zählt nicht) | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `SINGLE_CLASS_SECTIONS` | `1` | `single`, `detail`, `paraphrase`: genau so viele relevante Abschnitte | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `CATALOGUE_REPORT_MIN_PAGES` | `2` | Bericht von `check`: Anzahl der `multi-section`-Fragen mit Abschnitten auf mindestens so vielen Seiten (nur Anzeige, keine Regel) | – |
| `CATALOGUE_EXCERPT_CHARS` | `60` | `catalogue.py find`: Zeichen Kontext vor und nach einem Treffer (nie über den Abschnitt hinaus) | – |
| `CATALOGUE_HEADING_SEPARATOR` | `" › "` | Trenner im Überschriftenpfad (`section_index.md`, `find`, `show`) | – |
| `CORPUS_SITE_URL` | `"https://e2e.tester.army/docs"` | Editor, formatierte Ansicht: seitenrelative Links der Doku zeigen auf die öffentliche Seite | – |
| `CATALOGUE_SEED` | `20261014` | Seed des Stichprobenplans (Tag der Entscheidung; nie angepasst) | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `CATALOGUE_AREA_SLOTS` | 15 Bereiche nach Tokenanteil, mindestens 1 ([Korpus](corpus.md#bereiche)) | Slots je Bereich (Summe 48) | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md), [ADR 0039](../adr/0039-stichprobenplan-e2e.md) |
| `CATALOGUE_RESERVE` | gleich `CATALOGUE_AREA_SLOTS` | Reserveabschnitte je Bereich für Sprünge | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md), [ADR 0039](../adr/0039-stichprobenplan-e2e.md) |
| `CATALOGUE_SKIP_REASONS` | `("code-or-links", "too-short", "duplicate-topic", "no-answerable-content")` | erlaubte Gründe für einen Sprung | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `CATALOGUE_SKIP_MIN_TOKENS` | `50` | `too-short` nur für Abschnitte unter so vielen Tokens | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `CATALOGUE_PLAN_STATUSES` | `("open", "used", "skipped", "reserve")` | Werte von `status` in `catalogue_plan.csv` | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `CATALOGUE_SLOT_FORMAT` | `"S{:02d}"` | Format der Slot-IDs im Plan (S01 … S48) | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `CATALOGUE_REVIEW_KINDS`, `CATALOGUE_REVIEW_DECISIONS` | `("missing_section", "wording", "fact", "class")`, `("open", "accepted", "rejected")` | Arten und Entscheidungen der KI-Durchsicht | [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md) |
| `CLOSED_BOOK_VERDICTS` | `("", "hit", "miss")` | Urteil: offen, trifft den Kernpunkt, trifft ihn nicht | [ADR 0040](../adr/0040-closed-book-pruefung.md) |
| `CLOSED_BOOK_MIN_DEPENDENT_SHARE` | `Fraction(2, 3)` | Mindestanteil retrieval-abhängiger Fragen (auf ganze Fragen aufgerundet: 32 von 48); `catalogue.py freeze` verweigert darunter | [ADR 0038](../adr/0038-korpus-e2e.md), [ADR 0040](../adr/0040-closed-book-pruefung.md) |
| `QUESTION_ID_PATTERN`, `QUESTION_ID_FORMAT` | `r"Q\d+"`, `"Q{:03d}"` | Muster vorhandener und Format neuer Frage-IDs (Editor) | – |
| `CATALOGUE_WORD_PATTERN` | `r"[a-z0-9]+"` | Wörter für den Paraphrase-Vergleich (nach Kleinschreibung) | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `CATALOGUE_CAMEL_BOUNDARY` | `r"(?<=[a-z0-9])(?=[A-Z])"` | camelCase-Grenze; Bezeichner zählen auch mit ihren Teilen | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `CATALOGUE_FOLD_MIN_LENGTH` | `4` | ab dieser Länge auch ohne `s`/`es`, mit `ies` → `y` | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `CATALOGUE_PREFIX_MIN`, `CATALOGUE_PREFIX_SLACK` | `4`, `3` | gleicher Anfang von mindestens max(4, kürzere Länge − 3) Zeichen gilt als gleiches Wort | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) |
| `CATALOGUE_STOPWORDS` | Tupel englischer Funktions- und Fragewörter plus `e2e` (Produktname) | beim Vergleich ignoriert | [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md), [ADR 0039](../adr/0039-stichprobenplan-e2e.md) |

## LLM und Embedding

Konstante Einstellungen der Antwortgenerierung: [Prompts](prompts.md).

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `EMBEDDING_MODEL` | `"text-embedding-3-large"` | Embedding-Modell (nur als Alias angeboten, daher Vektoren einmal speichern); auch für Response Relevancy in RAGAS ([ADR 0047](../adr/0047-ragas-als-triangulation.md)) | [ADR 0023](../adr/0023-embedding-modell.md), [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md) |
| `EMBEDDING_DIMENSIONS` | `3072` | Vektordimension (Modellstandard) | [ADR 0023](../adr/0023-embedding-modell.md) |
| `EMBEDDING_BATCH_SIZE` | `100` | Texte je API-Anfrage (API-Grenze: ≤ 2.048 Eingaben, ≤ 300.000 Tokens) | – |
| `EMBEDDING_PRICE_PER_MTOK` | `0.13` | USD je 1 Mio. Eingabe-Tokens (OpenAI-Modellseite, abgerufen 13.10.2026); Grundlage von `cost_usd` | [ADR 0008](../adr/0008-kosten-als-variable.md), [ADR 0023](../adr/0023-embedding-modell.md) |
| `LLM_MODEL` | `"gpt-6-luna"` | Antwortmodell, gepinnt 17.10.2026 (nur als Alias angeboten, daher Antworten einmal erzeugen) | [ADR 0016](../adr/0016-modell-neutralitaet.md), [ADR 0033](../adr/0033-antwortmodell.md) |
| `LLM_REASONING_EFFORT` | `"none"` | einzige Stufe, bei der die API eine Temperatur annimmt | [ADR 0033](../adr/0033-antwortmodell.md) |
| `LLM_TEMPERATURE` | `0.0` | konstant für Reproduzierbarkeit | [ADR 0014](../adr/0014-temperatur-und-topk.md) |
| `LLM_SEED` | `20261017` | fester `seed` jeder Anfrage (OpenAI: Beta, nur „best effort“); fest, nie getunt | [ADR 0033](../adr/0033-antwortmodell.md) |
| `LLM_MAX_TOKENS` | `1024` | Obergrenze der Antwortlänge (`max_completion_tokens`); eine dort abgeschnittene Antwort bricht den Lauf ab | [ADR 0033](../adr/0033-antwortmodell.md) |
| `LLM_PRICE_INPUT_PER_MTOK`, `LLM_PRICE_OUTPUT_PER_MTOK` | `0.10`, `0.50` | USD je 1 Mio. Ein- bzw. Ausgabe-Tokens (OpenAI-Modellseite, abgerufen 17.10.2026); Grundlage von `cost_usd` | [ADR 0008](../adr/0008-kosten-als-variable.md), [ADR 0033](../adr/0033-antwortmodell.md) |

### RAGAS

Richter und Einstellungen sind für alle vier Metriken gleich und gepinnt ([ADR 0047](../adr/0047-ragas-als-triangulation.md));
Verfahren: [Evaluation](evaluation.md#triangulation), Dateien: [Datenformate](data-formats.md#ragas). In `config.py`
stehen die Schlüssel im Block „LLM / Embedding“ zwischen den Preisen des Antwortmodells und den Prompts.

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `RAGAS_JUDGE_MODEL` | `"gpt-6-sol"` | Richtermodell, nicht das Antwortmodell | [ADR 0047](../adr/0047-ragas-als-triangulation.md), [Spec](../superpowers/specs/2026-10-21-ragas-design.md) |
| `RAGAS_REASONING_EFFORT` | `"none"` | einzige Stufe, bei der die API eine Temperatur annimmt | [ADR 0033](../adr/0033-antwortmodell.md), [ADR 0047](../adr/0047-ragas-als-triangulation.md) |
| `RAGAS_TEMPERATURE` | `0.0` | Temperatur der Richteraufrufe (RAGAS 0.4.3 würde 1,0 senden, siehe [Werkzeuge](tooling.md#ragas-pins)) | [ADR 0047](../adr/0047-ragas-als-triangulation.md), [Spec](../superpowers/specs/2026-10-21-ragas-design.md) |
| `RAGAS_SEED` | `20261021` | fester `seed` jeder Richteranfrage (nur „best effort“); fest, nie getunt | [ADR 0047](../adr/0047-ragas-als-triangulation.md), [Spec](../superpowers/specs/2026-10-21-ragas-design.md) |
| `RAGAS_STRICTNESS` | `1` | Zahl der Fragen, die Response Relevancy je Antwort erzeugt; bei Temperatur 0 wiederholt jede weitere denselben Prompt | [ADR 0047](../adr/0047-ragas-als-triangulation.md), [Spec](../superpowers/specs/2026-10-21-ragas-design.md) |
| `RAGAS_METRICS` | `("faithfulness", "response_relevancy", "context_precision", "context_recall")` | die vier Metriken = Spalten von `ragas_scores.csv` (Context Precision und Recall mit Referenz) | [ADR 0047](../adr/0047-ragas-als-triangulation.md), [Spec](../superpowers/specs/2026-10-21-ragas-design.md) |
| `RAGAS_DECIMALS` | `6` | Nachkommastellen der Werte in `ragas_scores*.csv` | [ADR 0047](../adr/0047-ragas-als-triangulation.md), [Spec](../superpowers/specs/2026-10-21-ragas-design.md) |
| `RAGAS_SCORES_FILE` | `data/evaluation/ragas_scores.csv` | Ergebnisdatei des Hauptlaufs | [ADR 0047](../adr/0047-ragas-als-triangulation.md) |
| `RAGAS_REPEAT_FILE_NAME` | `"ragas_scores_repeat.csv"` | Name der Wiederholungsdatei neben der Ergebnisdatei (`--repeat`, nur Pilot-Sets) | [ADR 0047](../adr/0047-ragas-als-triangulation.md) |
| `RAGAS_JUDGE_PRICE_INPUT_PER_MTOK`, `RAGAS_JUDGE_PRICE_OUTPUT_PER_MTOK` | `2.0`, `10.0` | USD je 1 Mio. Ein- bzw. Ausgabe-Tokens des Richters (abgerufen 17.10.2026); Grundlage von `judge_cost_usd` | [ADR 0008](../adr/0008-kosten-als-variable.md), [ADR 0033](../adr/0033-antwortmodell.md) |
| `RAGAS_TIMEOUT_S` | `120` | Zeitgrenze je Anfrage in Sekunden | [ADR 0047](../adr/0047-ragas-als-triangulation.md) |
| `RAGAS_MAX_RETRIES` | `5` | Wiederholungen je Anfrage im SDK | [ADR 0047](../adr/0047-ragas-als-triangulation.md) |
| `RAGAS_CONCURRENCY` | `8` | gleichzeitige Bewertungsaufträge (eine Antwort mit einer Metrik) | [ADR 0047](../adr/0047-ragas-als-triangulation.md) |
| `RAGAS_DO_NOT_TRACK` | `True` | unterbindet das Senden der RAGAS-Telemetrie ([Umgebungsvariablen](tooling.md#umgebungsvariablen)) | [ADR 0047](../adr/0047-ragas-als-triangulation.md) |
| `RAGAS_MAX_TOKENS` | `4096` | `max_completion_tokens` eines Richteraufrufs; eine abgeschnittene Ausgabe ist ein Fehler | [ADR 0047](../adr/0047-ragas-als-triangulation.md) |
| `RAGAS_NAN_REASONS` | Text je Metrik | feste Begründung, wenn RAGAS 0.4.3 ein NaN ohne eigenen Grund liefert (Faithfulness, Context Recall, Context Precision; Response Relevancy hat keinen Eintrag) | [ADR 0047](../adr/0047-ragas-als-triangulation.md), [Spec](../superpowers/specs/2026-10-21-ragas-design.md) |

### Prompts

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `SYSTEM_PROMPT`, `USER_PROMPT_TEMPLATE`, `CONTEXT_SEPARATOR` | Texte | Prompt der Generierung: die beiden Texte wörtlich wie in [Prompts](prompts.md) (ein Test vergleicht sie), `CONTEXT_SEPARATOR` (`"\n---\n"`) wie dort beschrieben | [ADR 0006](../adr/0006-nur-chunking-variiert.md) |
| `CLOSED_BOOK_SYSTEM_PROMPT`, `CLOSED_BOOK_USER_TEMPLATE` | Texte | Prompt der Closed-Book-Prüfung und von K0, wörtlich wie in [Prompts](prompts.md#closed-book-prompt-prüfung-und-k0) | [ADR 0040](../adr/0040-closed-book-pruefung.md) |

## Evaluation

Rubrik und Statistik: [Evaluation](evaluation.md). Die Dateinamen der Tabellen und Abbildungen
(`report_tables.TABLE_NAMES`, `report_figures.FIGURE_NAMES`) stehen nicht in `config.py`: Sie sind Namen von
Artefakten, keine Parameter des Experiments, und sind in [Datenformate](data-formats.md#auswertung-output)
beschrieben.

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `RUBRIC_CRITERIA` | `["correctness", "completeness", "groundedness", "no_hallucination", "clarity"]` | Rubrik-Kriterien = Spalten in `scores.csv` | [ADR 0013](../adr/0013-antwort-rubrik.md) |
| `CONTROL_CRITERIA` | `["correctness", "completeness", "no_hallucination", "clarity"]` | Kriterien, die K0 und C1–C3 teilen (ohne Quellenbezug) | [ADR 0041](../adr/0041-kontrolle-k0.md) |
| `RUBRIC_MAX_SCORE` | `2` | Höchstwert je Kriterium (Skala 0–2) | [ADR 0013](../adr/0013-antwort-rubrik.md) |
| `KEY_POINTS_MAX` | `4` | höchstens so viele Kernpunkte je Frage; Punkt 1 = Kernaussage | [ADR 0035](../adr/0035-regelbasierte-bewertung.md) |
| `RUBRIC_COMPLETENESS_PARTIAL` | `0.5` | Anteil enthaltener Kernpunkte für Vollständigkeit 1 | [ADR 0035](../adr/0035-regelbasierte-bewertung.md) |
| `RUBRIC_RULES_VERSION` | `"2026-10-20"` | Version der Regeln in `src/scoring_rules.py`; steht in jeder Zeile von `scoring_checks.csv` | [ADR 0035](../adr/0035-regelbasierte-bewertung.md), [ADR 0037](../adr/0037-praezisierte-pruefregeln-und-vorbefuellte-kernpunkte.md), [ADR 0043](../adr/0043-praezisierung-direct-und-teilantworten.md) |
| `SCORING_METHOD` | `"rules"` | Kennzeichen eines Scaffolds, das nur regelbasiert bewertet werden darf (`scoring` im `scaffold`-Eintrag) | [ADR 0036](../adr/0036-regelbasierte-bewertung-verpflichtend.md) |
| `SCORING_SEED` | `20261016` | Reihenfolge der verblindeten Antworten je Frage; fest, nie angepasst | [ADR 0032](../adr/0032-blinde-rubrik-bewertung.md) |
| `OUTPUT_DIR` | `output` | Ausgabe der Auswertung (Tabellen, Abbildungen, `analysis.json`) | [ADR 0044](../adr/0044-statistische-auswertung.md), [Spec](../superpowers/specs/2026-10-20-analysis-design.md) |
| `TABLES_DIR` | `output/tables` | Tabellen der Auswertung | [ADR 0044](../adr/0044-statistische-auswertung.md), [Spec](../superpowers/specs/2026-10-20-analysis-design.md) |
| `FIGURES_DIR` | `output/figures` | Abbildungen der Auswertung | [ADR 0044](../adr/0044-statistische-auswertung.md), [Spec](../superpowers/specs/2026-10-20-analysis-design.md) |
| `ANALYSIS_FILE` | `output/analysis.json` | Kennzahlen und Testergebnisse der Auswertung | [ADR 0044](../adr/0044-statistische-auswertung.md), [Spec](../superpowers/specs/2026-10-20-analysis-design.md) |
| `ANALYSIS_ALPHA` | `0.05` | Signifikanzniveau der konfirmatorischen Tests (Holm-korrigiert) | [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `ANALYSIS_DIFF_DECIMALS` | `12` | Rundung der Differenzen im Wilcoxon-Test, damit gleiche Differenzen gebrochener Metriken trotz Gleitkommafehler eine Bindungsgruppe bilden | [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `ANALYSIS_PRIMARY` | `{"recall": "R@5", "reciprocal_rank": "MRR", "total_score": "Gesamtwert"}` | konfirmatorische Metriken: Spalte → Anzeigename | [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `ANALYSIS_RULE` | `"main"` | Relevanzregel der Retrieval-Metriken in der Auswertung | [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `REPORT_DECIMALS` | `2` | Nachkommastellen von Werten, Kennzahlen, Teststatistiken und Effektstärken in den Tabellen | [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `REPORT_P_DECIMALS` | `3` | Nachkommastellen der p-Werte; kleinere erscheinen als `<0,001` | [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `REPORT_COST_DECIMALS` | `5` | Nachkommastellen der Kosten (USD) in der Effizienztabelle | [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `BYTES_PER_MB` | `1000000` | Indexgröße in MB (dezimal) | [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `JSON_DECIMALS` | `6` | Rundung der Gleitkommazahlen in `analysis.json` | [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `FIGURE_WIDTH_CM`, `FIGURE_HEIGHT_CM` | `17.0`, `6.5` | Abbildungen in Endgröße (Breite des Satzspiegels; Standardhöhe, Panels und Heatmap wachsen mit ihren Zeilen) | [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `FIGURE_FONT_SIZE` | `9` | Schriftgröße der Abbildungen | [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `FIGURE_DPI` | `300` | Auflösung der Abbildungen | [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `FIGURE_FONT_FILE` | `"arial282/Arial282-Regular.ttf"` | Arial unter `PAPERLAB_FONTS` ([Umgebungsvariablen](tooling.md#umgebungsvariablen)) oder `fonts/` von PaperLab (eine Schrift in der Arbeit, Prüfung `schrift`); fehlt sie, DejaVu Sans mit Hinweis | [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `FIGURE_COLORS` | `C1` `#184F95`, `C2` `#B8461A`, `C3` `#11866A`, `K1` `#52514E`, `K0` `#8E8C87` | Farben der Strategien: Klassenfarben FigBlue und FigOrange, dritter Farbton auf Farbsehschwäche geprüft (alle Paare ΔE ≥ 10), Kontrollen grau | [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `FIGURE_HATCHES`, `FIGURE_MARKERS` | Schraffur: `K1` `///`, `K0` `xxx`, C1–C3 ohne; Marker: `C1` `o`, `C2` `s`, `C3` `D`, `K0` `^` (K1 erscheint nur als Balken) | Farbe nie alleiniger Informationsträger | [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `FIGURE_INK`, `FIGURE_MUTED`, `FIGURE_GRID` | `#0B0B0B`, `#52514E`, `#E4E3DF` | Text, Achsen, Gitterlinien | [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `FIGURE_SEQUENTIAL` | `#F2F7FE` → `#CDE2FB` → `#184F95` | einfarbige Skala der Heatmap und Zähltabelle | [ADR 0044](../adr/0044-statistische-auswertung.md) |
| `FIGURE_HISTOGRAM_BINS` | `20` | Klassen der Chunk-Längen-Histogramme | [ADR 0044](../adr/0044-statistische-auswertung.md) |

## Korpusauswahl

Einmalige Diagnose, kein Teil des Experiments; Verfahren: [Korpusauswahl](corpus-selection.md).

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `CORPUS_PROBE_DIR` | `data/corpus_probe` | Kandidaten, Seitenstatistik, Ergebnisse, klassifizierte Fehltreffer, Wertung | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_PROBE_SEED` | `20261018` | Reihenfolge der Kandidatensätze je Seite; fest, nie angepasst | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_PROBE_PER_PAGE` | `12` | höchstens so viele Proben je Seite | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_PROBE_SPAN_CHARS` | `(2, 40)` | Länge eines maskierbaren Inline-Code-Ausdrucks (Zeichen) | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_PROBE_SENTENCE_CHARS` | `(40, 400)` | Länge eines verwendbaren Prosasatzes (Zeichen) | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_PROBE_CONTEXT_CHARS` | `6000` | Abschnittstext im Open-Book-Lauf (Zeichen) | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_PROBE_WORKERS` | `8` | parallele API-Anfragen | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_PROBE_GUESS_CHARS` | `120` | gespeicherter Anfang der Closed-Book-Antwort in `misses/<name>.json` | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_PROBE_WEIGHTS` | Unbekanntheit 35, Sauberkeit 15, Struktur 15, Qualität 15, Stabilität 10, Passung 10 | vorab festgelegte Gewichte der Wertung (Stufen 0–4 in `summarise.py`) | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_PROBE_SENSITIVITY` | fünf Gewichtungen | Rangfolge je Gewichtung als Sensitivität | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_PROBE_MIN_TOKENS` | `80000` | untere Größengrenze (Ausschlusskriterium 5) für die Sensitivität | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_PROBE_TOP` | `5` | Kandidaten je Gewichtung in `summary.json` | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_PROBE_AI_RATING`, `CORPUS_PROBE_FEW_STARS` | `low` 4 … `high` 1; `100` | Stufe „Passung“ nach KI-Textanteil, minus 1 unter 100 GitHub-Sternen | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_QUESTIONS_PER_CORPUS` | `20` | Closed-Book-Diagnosefragen je Korpus, eine je gezogenem Abschnitt | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_QUESTIONS_MIN_WORDS` | `60` | Prosawörter (ab 3 Buchstaben, außerhalb von Code), die ein gezogener Abschnitt braucht | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_QUESTIONS_PER_PAGE` | `2` | höchstens so viele gezogene Abschnitte je Seite | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_QUESTIONS_SECTION_CHARS` | `5000` | Abschnittstext für Fragenschreiber und Open-Book-Lauf (Zeichen) | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CORPUS_QUESTIONS_JUDGE_SEEDS` | `{1: 7, 2: 8}` | Reihenfolge der verblindeten Antworten je Urteilslauf (1: fünf Korpora, 2: Angular) | [ADR 0038](../adr/0038-korpus-e2e.md) |

## Zweitbewertung

[ADR 0046](../adr/0046-zweitbewertung.md); Verfahren: [Evaluation](evaluation.md#zweitbewertung), Dateien:
[Datenformate](data-formats.md#zweitbewertung).

| Schlüssel | Wert/Typ | Bedeutung | Entscheidung |
|---|---|---|---|
| `AGREEMENT_BOOTSTRAP_REPS` | `2000` | Bootstrap-Wiederholungen über Fragen für die Intervalle | [ADR 0046](../adr/0046-zweitbewertung.md), [Spec](../superpowers/specs/2026-10-22-second-rater-design.md) |
| `AGREEMENT_CI_LEVEL` | `0.95` | Niveau des Perzentil-Intervalls | [ADR 0046](../adr/0046-zweitbewertung.md) |
| `AGREEMENT_SEED` | `20261022` | Seed des Bootstraps; fest, nie getunt | [ADR 0046](../adr/0046-zweitbewertung.md), [Spec](../superpowers/specs/2026-10-22-second-rater-design.md) |
| `SECOND_RATER_QUESTIONS` | `12` | gezogene Fragen im Hauptkatalog (× C1–C3 = 36 Antworten) | [ADR 0046](../adr/0046-zweitbewertung.md) |
| `SECOND_RATER_DISAGREEMENTS_FILE_NAME` | `"second_rater_disagreements.csv"` | Abweichungsliste in `output/` | [ADR 0046](../adr/0046-zweitbewertung.md), [Spec](../superpowers/specs/2026-10-22-second-rater-design.md) |
| `SECOND_RATER_SEED` | `20261022` | Seed der geschichteten Ziehung; fest, nie getunt | [ADR 0046](../adr/0046-zweitbewertung.md) |
| `SECOND_RATER_MAX_DRAWS` | `100000` | Versuche, bis eine Ziehung beide Schichtungen trifft; sonst Abbruch | [ADR 0046](../adr/0046-zweitbewertung.md) |
| `SECOND_RATER_PSEUDONYM` | `"R2"` | einziger Name der zweiten Person in Dateien, Einträgen und Ausgaben | [ADR 0046](../adr/0046-zweitbewertung.md) (Nachtrag Datenschutz) |
| `SECOND_RATER_DIR_NAME`, `SECOND_RATER_DIR` | `"second_rater"`, `data/evaluation/second_rater` | Ordner des R2-Satzes (im Pilot-Set `DIR/second_rater`) | [ADR 0046](../adr/0046-zweitbewertung.md) |
| `SECOND_RATER_SAMPLE_FILE` | `data/evaluation/second_rater_sample.csv` | gezogene Fragen | [ADR 0046](../adr/0046-zweitbewertung.md) |
| `SECOND_RATER_ENV` | `"SCORING_RATER"` | Umgebungsvariable für den R2-Modus der App; nur Wert `R2` erlaubt, sonst Abbruch ([Umgebungsvariablen](tooling.md#umgebungsvariablen)) | [ADR 0046](../adr/0046-zweitbewertung.md), [Spec](../superpowers/specs/2026-10-22-second-rater-design.md) |
