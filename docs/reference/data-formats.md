# Datenartefakte und Formate

*[Doku-Index](../README.md) · Referenz · Verwandt: [Konfiguration](configuration.md), [Evaluation](evaluation.md), [Experiment-Protokoll](experiment-record.md)*

Dateinamen und Pfade kommen aus [`src/config.py`](../../src/config.py) ([Konfiguration](configuration.md)); welche
Dateien versioniert sind und wo jedes Format steht: [Versioniert und ignoriert](#versioniert-und-ignoriert).

Herkunft der Beispiele: Korpus-Beispiele und der `embed.py`-Eintrag sind echte Datensätze auf `ef977f4`
([Korpus](corpus.md)); der `retrieve.py`- und der `generate.py`-Eintrag sowie die Zeile von `ragas_scores.csv` sind
echt und stammen aus dem Pilot-Set `e2e` ([Pilot-Sets](#pilot-sets)). Katalog- und übrige Ergebnisbeispiele nutzen
echte e2e-IDs aus `sections.jsonl` mit Platzhaltern (`…`) für Texte; ihre Zahlen zeigen nur die Form, denn einen Lauf
des Hauptexperiments gibt es noch nicht ([Plan](../plan.md#stand)). Texte gekürzt (`...`), Prüfsummen gekürzt (`…`);
JSON-Zeilen kompakt dargestellt (die Dateien haben ein Leerzeichen nach `:` und `,`).

## Konventionen

- CSV: UTF-8, Zeilenende LF, immer mit Kopfzeile, Anführungszeichen nur wo nötig (Python-Modul `csv`).
  `atomic_csv.write_csv` schreibt über eine temporäre Datei im selben Ordner und ersetzt die alte in einem Schritt.
- JSONL: ein JSON-Objekt je Zeile, UTF-8 ohne ASCII-Escapes. Laufprotokolle werden nur angehängt (einzige Ausnahme:
  ein erneuter Export der Zweitbewertung beginnt `second_rater/runs.jsonl` neu, [Zweitbewertung](#zweitbewertung)).

## Korpus

**`docs/corpus_snapshot.txt`** (geschrieben von `snapshot.py`): Kopfzeilen `schlüssel: wert`, eine Leerzeile, dann je
Datei `SHA-256  pfad` (zwei Leerzeichen; Pfad relativ zum Dokumentationsordner `docs/` des e2e-Repositorys,
`config.CORPUS_ROOT`; sortiert; Seiten und die beiden mitkopierten Dateien `docs.json` und
`snippets/model-provider.jsx`). Eine vorhandene Datei schreibt `snapshot.py` nie neu: es prüft Commit und Prüfsummen
gegen sie und bricht bei einer Abweichung ab.

```text
repository: https://github.com/tester-army/e2e.git
commit: ef977f4856da009cac26d78d2e9bb14e5991ee41
commit_date: 2026-10-17T16:12:13+02:00
snapshot_date: 2026-10-18
root: docs
files: 62

2b64177a…f8671c8  agent-steps.mdx
```

**`data/raw/e2e_docs_snapshot/`** (`config.DATA_RAW`, geschrieben von `snapshot.py`): die Seiten (`*.mdx`) und die
beiden mitkopierten Dateien mit denselben relativen Pfaden wie unter `docs/` im e2e-Repository; `snapshot.py` leert
den Ordner vorher (bis auf Dateien, die mit `.` beginnen, z. B. `.gitkeep`).

**`docs/corpus_manifest.csv`** (geschrieben von `preprocess.py`): Spalten und Beispielzeilen in
[Korpus](corpus.md#korpusmanifest-corpus_manifestcsv).

**`documents.jsonl`** (`area` = Gruppe der Navigation, [Korpus](corpus.md#bereiche); `text` nach `ingest.py` das
rohe MDX, nach `preprocess.py` das umgewandelte Markdown)
```json
{"doc_id":"D031","path":"migrate/detox.mdx","title":"From Detox","area":"Migrate","text":"# From Detox\n\nUse your existing app build and testIDs with s...","tokens":2409}
```

- `doc_id` = Position der Seite in der nach Pfad sortierten Seitenliste (`D001` = `agent-steps.mdx`, `D002` =
  `agents.mdx`, …). Jede Änderung der Seitenmenge nummeriert die folgenden Seiten um; Annotationen eines anderen
  Korpusstands werden dann über Pfad und Anker umgeschrieben, nie von Hand (einziger Fall bisher, auf dem Vue-Korpus:
  [Experiment-Protokoll Vue](experiment-record-vue.md#korpuserweiterung-14102026-prüfungen)).
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

## Fragen und Ground Truth

**`questions.csv`** (der Editor schreibt sie sortiert nach `question_id`)
```csv
question_id,question,type,difficulty,notes
Q001,"How do I …?",procedural,single,
```

`type` und `difficulty` nehmen nur die Werte aus [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md) an (`config.QUESTION_TYPES`,
`config.QUESTION_CLASSES`); die Pilot-Sets sind davon ausgenommen: `data/pilot/` hat `difficulty` `easy`/`medium`/`hard`
(3/4/1) und `notes` = `pilot`, `hard` und `e2e` tragen in `difficulty` die Klasse bzw. `hard` und in `notes`
`pilot <Klasse>`.

**`ground_truth.csv`** (sortiert nach `question_id`)
```csv
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
```markdown
| section_id | area | path | heading path | tokens |
|---|---|---|---|---:|
| `D001#agent-steps` | Deep dive | agent-steps.mdx | How agent steps work | 1176 |
```
`area` ist der Bereich der Seite (Feld `area` in `documents.jsonl`); `heading path` verbindet die Überschriften mit
`config.CATALOGUE_HEADING_SEPARATOR` (` › `); `tokens` = `end_token − start_token` des Abschnitts.

**`catalogue_freeze.json`** (`data/evaluation/`, geschrieben von `catalogue.py freeze`; [ADR 0030](../adr/0030-einfrieren-des-fragenkatalogs.md)):
```json
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

Plan-, Durchsichts- und Closed-Book-Datei werden nur aufgezeichnet, und nur, sofern sie vorhanden sind; die Sperre
(`freeze.require_frozen`, in jedem Schritt ab `retrieve.py`) prüft die vier übrigen Dateien. `closed_book` = Zahl der
retrieval-abhängigen (`miss`) und -unabhängigen (`hit`) Fragen.

**`catalogue_plan.csv`** (`data/evaluation/`, einmal geschrieben von `catalogue.py plan`, danach ändert
der Editor nur Status, Sprunggrund und Frage-ID sowie bei einem Sprung Slot und Klasse der nachrückenden Reservezeile;
[ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md), [ADR 0039](../adr/0039-stichprobenplan-e2e.md)): eine
Zeile je gezogenem Abschnitt, je Bereich erst die Slots, dann die Reserve in Ziehungsreihenfolge. Der unbenutzte
Vue-Plan liegt unverändert in `data/evaluation/archive_vue/catalogue_plan.csv`
([Experiment-Protokoll](experiment-record.md#stichprobenplan-e2e)).
```csv
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
```csv
round,question_id,kind,suggestion,section_id,decision,reason,date
1,Q001,missing_section,…,D006#install-the-skill,accepted,,…
1,Q002,wording,…,,rejected,…,…
```
`round` = Durchsichtsrunde (ganze Zahl), `date` = Tag der Entscheidung; `kind` ∈ `config.CATALOGUE_REVIEW_KINDS`,
`decision` ∈ `config.CATALOGUE_REVIEW_DECISIONS`; `section_id` nur bei `missing_section`, `reason` Pflicht bei
`rejected`.

**`closed_book_screen.csv`** (`data/evaluation/`, nur für den Hauptkatalog; `catalogue.py screen` schreibt Antworten,
Jonas die Urteile im Editor; [ADR 0040](../adr/0040-closed-book-pruefung.md)): eine Zeile je Katalogfrage, sortiert
nach ID.
```csv
question_id,question_sha256,reference_sha256,answer,model,core_point,note,date
Q001,5d1f…,a90c…,…,gpt-6-luna,miss,,…
```
`question_sha256` = SHA-256 des Fragetexts, zu dem die Antwort gehört (geänderte Frage: `screen` fragt neu, das Urteil
wird geleert); `reference_sha256` = SHA-256 der Referenzantwort, zu der das Urteil gehört (geänderte Referenz: Urteil
offen). `answer` ohne führende und folgende Leerzeichen; `model` = das von der API gemeldete Modell. `core_point` ∈
`config.CLOSED_BOOK_VERDICTS`: leer = offen, `hit` = trifft den Kernpunkt (Frage retrieval-unabhängig), `miss` = trifft
ihn nicht oder nur teilweise; `note` = freie Notiz, `date` = Tag des Urteils.

## Retrieval-Ergebnisse

**`retrieved_results.csv`** (`retrieve.py` läuft über alle Strategien C1–C3 und schreibt die Datei vollständig neu,
sortiert nach `question_id`, Strategie und Rang; [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)).
`score` = Kosinus-Ähnlichkeit mit sechs Nachkommastellen; `is_relevant` = `1`/`0` nach der Hauptregel
([Evaluation](evaluation.md#relevanz-eines-chunks)).
```csv
question_id,strategy,rank,chunk_id,score,is_relevant
Q001,C1,1,C1_D013_0001,0.840000,1
```

**`retrieved_results_control.csv`** (`retrieve.py --control`): gleiche Spalten, `strategy` immer `K1`.

**`retrieval_scores.csv`** (`evaluate_retrieval.py`, wird vollständig neu geschrieben; `retrieval_scores_control.csv`
mit `--control` für K1): eine Zeile je Frage, Strategie und Relevanzregel (`rule` = `main` oder `sensitivity`,
[Evaluation](evaluation.md#relevanz-eines-chunks)), sortiert nach `question_id`, Strategie, Regel. `hit` = `1`/`0`;
`reciprocal_rank`, `precision`, `recall` mit sechs Nachkommastellen; `context_tokens` = summierte Länge der k
abgerufenen Chunks (Kontext@k).
```csv
question_id,strategy,rule,hit,reciprocal_rank,precision,recall,context_tokens
Q001,C1,main,1,0.333333,0.600000,1.000000,610
```

## Antworten

**`generated_answers.csv`** (`generate.py`, alle Strategien C1–C3 in einem Lauf, sortiert nach `question_id` und
Strategie; wird nie überschrieben, [ADR 0033](../adr/0033-antwortmodell.md)). `answer` = Text der API unverändert;
`sources` = die top-k Chunk-IDs in Rangfolge, getrennt durch `config.ID_SEPARATOR` (`;`; genau die Passagen des
Prompts); `prompt_tokens`/`completion_tokens` = Abrechnung der API (`usage`).
```csv
question_id,strategy,answer,sources,prompt_tokens,completion_tokens
Q001,C1,"...",C1_D013_0001;…,1200,180
```

**`generated_answers_control.csv`** (Kontrolle K0, im selben Lauf von `generate.py` mit dem Closed-Book-Prompt; Format
wie `generated_answers.csv`, `strategy` = `K0`, `sources` leer; wird nie überschrieben;
[ADR 0041](../adr/0041-kontrolle-k0.md)).

## Bewertung

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
```csv
code,question_id,correctness,completeness,groundedness,no_hallucination,clarity,notes
Q001-A,Q001,2,1,2,2,2,…
```

**`scoring_key.csv`** (Schlüssel; erst `--mode summarise` entblindet mit ihm; ein erneutes `--mode scaffold` liest ihn
nur, um ihn maschinell mit dem berechneten zu vergleichen)
```csv
code,question_id,strategy
Q001-A,Q001,C3
```

**`scoring_items.jsonl`** (Daten der Bewertungsseite, [ADR 0034](../adr/0034-bewertung-in-der-app.md)): eine Zeile je
Code in der Reihenfolge des Lesepakets mit `code`, `question_id`, `question`, `reference_answer`, `answer` und
`excerpts` (Texte der Passagen in Rangfolge, ohne Chunk-IDs); keine Strategie.

**`key_points.csv`** (Kernpunkte je Frage, von Jonas vor der Bewertung geschrieben und eingefroren,
[ADR 0035](../adr/0035-regelbasierte-bewertung.md)): eine Zeile je Punkt, sortiert nach `question_id` und `point`;
`point` ab 1 ohne Lücken (1 = Kernaussage), höchstens `config.KEY_POINTS_MAX` je Frage, `text` einzeilig. Das
Einfrieren schreibt den Eintrag `key_points` ins Laufprotokoll ([Laufprotokoll](#laufprotokoll)); er gilt nur für das
Scaffold mit dieser `scoring_items.jsonl`. Nach einem neuen Scaffold werden die Kernpunkte erneut eingefroren; das
Einfrieren verweigert, solange eine `scoring_checks.csv` eines früheren Scaffolds vorliegt.
```csv
question_id,point,text
Q001,1,"…"
```

**`scoring_checks.csv`** (Antworten auf die Prüffragen je bewertetem Code, in der Reihenfolge des Bogens,
[ADR 0035](../adr/0035-regelbasierte-bewertung.md)): `rules_version` = `config.RUBRIC_RULES_VERSION` (Zeilen mit
einer anderen Version lehnt `--mode summarise` ab); `points` = Markierungen der Kernpunkte in Punktreihenfolge, durch
`;` getrennt; übrige Spalten und Optionen nach [Evaluation](evaluation.md#regelbasierte-bewertung).
```csv
code,rules_version,points,declines,core_wrong,other_error,grounded,hallucination,answers_question,direct,wordy
Q001-A,2026-10-20,covered;missing,no,no,no,all,none,yes,yes,no
```

**`scores.csv`** (abgeleitet von `--mode summarise` aus Bogen und Schlüssel, wird neu geschrieben; sortiert nach
`question_id` und Strategie; Kriterien-Spalten = `config.RUBRIC_CRITERIA`, `total_score` = Mittel der Kriterien mit
einer Nachkommastelle, nach [Evaluation](evaluation.md#antwort-evaluation-rubrik-02))
```csv
question_id,strategy,correctness,completeness,groundedness,no_hallucination,clarity,total_score
Q001,C1,2,2,2,2,2,2.0
```

### Kontrolle K0

[ADR 0041](../adr/0041-kontrolle-k0.md), Verfahren: [Evaluation](evaluation.md#kontrolle-k0).
`evaluate_answers.py --mode scaffold --control` schreibt erst nach `scores.csv`, für deren Fragen, die ersten beiden
Dateien; die Bewertungsseite schreibt die Prüfungen und die abgeleiteten Werte in den Bogen.

**`scoring_items_control.jsonl`**: Einträge wie `scoring_items.jsonl`, Code `<question_id>-K0` (z. B. `Q001-K0`),
`excerpts` leer; versioniert, da es kein Wiederherstellen gibt.

**`scoring_sheet_control.csv`** (Kriterien = `config.CONTROL_CRITERIA`, ohne `groundedness`)
```csv
code,question_id,correctness,completeness,no_hallucination,clarity,notes
Q001-K0,Q001,1,0,2,2,…
```

**`scoring_checks_control.csv`**: Kopf von `scoring_checks.csv` ohne `grounded`.

**`scores_control.csv`** (`--mode summarise --control`; Gesamtwert = Mittel der vier Kriterien mit zwei
Nachkommastellen)
```csv
question_id,strategy,correctness,completeness,no_hallucination,clarity,total_score
Q001,K0,1,0,2,2,1.25
```

## RAGAS

**`ragas_scores.csv`** (`ragas_eval.py`, [ADR 0047](../adr/0047-ragas-als-triangulation.md); schreibt die Datei einmal
und nie über eine vorhandene; Pilot-Sets: `ragas_scores.csv` im Set-Ordner): eine Zeile je Frage und Strategie
C1–C3 (K0 bekommt kein RAGAS), sortiert nach `question_id`, dann Strategie in der Reihenfolge `config.STRATEGY_IDS`. Die
Spalten sind `config.RAGAS_METRICS` in dieser Reihenfolge, Werte von 0 bis 1 mit `config.RAGAS_DECIMALS` = 6
Nachkommastellen. Eine Metrik, die selbst NaN meldet (Verfahren: [Evaluation](evaluation.md#triangulation)), steht als
**leere Zelle**; `nan_reasons` nennt dann je leerer Zelle `<Metrik>: <Grund>`, mehrere durch `; ` getrennt, sonst leer.
Ein leerer Wert ohne Grund, ein Wert außerhalb 0–1 oder eine fehlende Zeile bricht den Lauf ohne Schreiben ab.
```csv
question_id,strategy,faithfulness,response_relevancy,context_precision,context_recall,nan_reasons
E01,C1,1.000000,0.776339,0.833333,1.000000,
```

**`ragas_scores_repeat.csv`** (`ragas_eval.py --repeat`, nur Pilot-Sets): gleiche Spalten, Zeilen und Sortierung; der
zweite Lauf über dieselben Antworten, nur für die Stabilität der Werte. Er steht unter dem Schritt `ragas_repeat` im
[Laufprotokoll](#laufprotokoll), der Eintrag `ragas` bleibt der der ersten Datei.

## Zweitbewertung

[ADR 0046](../adr/0046-zweitbewertung.md), Verfahren: [Evaluation](evaluation.md#zweitbewertung). Im Pilot-Set liegen
die Dateien im Set-Ordner (`DIR/second_rater_sample.csv`, `DIR/second_rater/`, Einträge in `DIR/runs.jsonl`).

**`second_rater_sample.csv`** (`data/evaluation/`, `second_rater.py --mode draw`): die gezogenen Fragen, sortiert nach
`question_id`.
```csv
question_id,type,difficulty
Q004,factual,detail
```

**`second_rater/`** (`data/evaluation/second_rater/`, `--mode export`): der Bewertungssatz der zweiten Person (nur das
Pseudonym R2): `scoring_items.jsonl` (die Zeilen der gezogenen Fragen aus Jonas' Item-Datei, unverändert),
`key_points.csv` (die eingefrorenen Kernpunkte dieser Fragen), `scoring_sheet.csv` (Format wie oben, anfangs je Code
eine Zeile ohne Werte), `runs.jsonl` (Einträge `scaffold` und `key_points` für die App, danach `second_rater_close`;
ein erneuter Export beginnt die Datei neu); die App schreibt `scoring_checks.csv` dazu. Kein Schlüssel, keine
Prüfantworten von Jonas.

**`second_rater_disagreements.csv`** (`output/`, im Set `DIR/output/`; `analyse.py`, nur mit abgeschlossener
Zweitbewertung, sonst löscht `analyse.py` eine ältere Datei): je abweichender Prüffrage, Kernpunkt-Markierung oder
Kriterium eine Zeile, ohne Strategie.
```csv
code,question_id,field,first,second
Q004-B,Q004,direct,yes,no
```

## Laufprotokoll

Jeder Schritt mit Ergebnisdatei hängt einen Eintrag (eine JSON-Zeile) an ein Laufprotokoll an; ein späterer Schritt
prüft mit `run_log.require_run`, dass er auf genau den Dateien des letzten passenden Eintrags (gleicher `step` und
`strategy`) aufbaut. Drei Dateien:

- **`embedding_runs.jsonl`** (`data/processed/`, `config.EMBEDDING_RUNS_FILE`; Kosten nach
  [ADR 0008](../adr/0008-kosten-als-variable.md)): Schritte `embed`, `retrieve`, `evaluate_retrieval`.
- **`generation_runs.jsonl`** (`data/evaluation/`, `config.GENERATION_RUNS_FILE`;
  [ADR 0033](../adr/0033-antwortmodell.md)): alle übrigen Schritte außer `second_rater_close`.
- **`second_rater/runs.jsonl`** (`config.PILOT_RUNS_FILE_NAME` im R2-Ordner): `scaffold`, `key_points` und
  `second_rater_close` des R2-Satzes.

Pilot-Sets schreiben die Einträge der ersten beiden Dateien in ihre `DIR/runs.jsonl` ([Pilot-Sets](#pilot-sets)).
Jeder Eintrag beginnt mit `date`; Einträge mit API-Aufrufen tragen danach die gepinnten Einstellungen und enden mit
Tokens und `cost_usd`. Die übrigen lokalen Schritte ohne API schreibt `run_log.append_step_run`: `date`, `step`, `strategy`, `inputs_sha256`,
`outputs_sha256`, dann die eigenen Felder; `scaffold` und `key_points` tragen nur `date`, `step`, `strategy`, ihre
Felder und `outputs_sha256`.

| `step` | Datei | `strategy` | geschrieben von | eigene Felder | geprüft von |
|---|---|---|---|---|---|
| `embed` | `embedding_runs.jsonl` | eine Strategie (`C1` … `K1`) | `embed.py`, ein Eintrag je Strategie | `model`, `openai_sdk`, `chromadb`, `dimensions`, `vectors`, `vector_bytes`, `inputs_sha256` (Chunk-Datei), `canary_*`, `input_tokens`, `cost_usd`, `api_called` | `analyse.py` liest den letzten Eintrag je Strategie (Indexgröße, Embedding-Kosten), ohne Prüfsummen |
| `retrieve` | `embedding_runs.jsonl` | `C1,C2,C3` bzw. `K1` (`--control`) | `retrieve.py`; Pilot-Sets über `scripts/difficulty_probe.py` | wie `embed`, `vectors`/`dimensions` der Fragen, `inputs_sha256` (Fragen, Ground Truth nach [ADR 0017](../adr/0017-fragenkatalog.md), Abschnitte, Vektor- und Chunk-Dateien), seit 17.10.2026 `outputs_sha256` | `generate.py` (Ergebnisdatei, Fragen, Ground Truth, Chunk-Dateien; ältere Pilot-Einträge ohne `outputs_sha256` nur an den Eingaben) |
| `evaluate_retrieval` | `embedding_runs.jsonl` | `C1,C2,C3` bzw. `K1` | `evaluate_retrieval.py` | `inputs_sha256` (`retrieved_results*.csv`, Fragen, Ground Truth, `sections.jsonl`, Chunk-Dateien), `outputs_sha256` (`retrieval_scores*.csv`) | `analyse.py` |
| `generate` | `generation_runs.jsonl` | `C1,C2,C3` | `generate.py`, nur nach einem erfolgreichen Lauf | siehe unten | `evaluate_answers.py --mode scaffold` (Fragen, Ground Truth, Chunk-Dateien, `generated_answers.csv`), `--mode scaffold --control` (Fragen, Ground Truth, `generated_answers_control.csv`), `ragas_eval.py`, `analyse.py` (nur die Antwortdateien, für die Kosten) |
| `scaffold` | `generation_runs.jsonl` | `C1,C2,C3` | `evaluate_answers.py --mode scaffold`, nur bei neu erzeugtem Bogen | `scoring` (`config.SCORING_METHOD`, [ADR 0036](../adr/0036-regelbasierte-bewertung-verpflichtend.md); ältere Einträge ohne), `codes` (Zahl), `outputs_sha256` (`scoring_items.jsonl`) | erneutes `--mode scaffold`, `--mode summarise` (`scoring`), Bewertungsseite beim Einfrieren der Kernpunkte |
| `scaffold` | `generation_runs.jsonl` | `K0` | `evaluate_answers.py --mode scaffold --control` ([ADR 0041](../adr/0041-kontrolle-k0.md)) | wie oben, `outputs_sha256` (`scoring_items_control.jsonl`) | – |
| `key_points` | `generation_runs.jsonl` | `C1,C2,C3` | Bewertungsseite beim Einfrieren | `outputs_sha256` (`key_points.csv`, `scoring_items.jsonl`) | Bewertungsseite, `--mode summarise`, K0-Scaffold und `--control`-Summarise, `second_rater.py --mode export` |
| `summarise` | `generation_runs.jsonl` | `C1,C2,C3` | `evaluate_answers.py --mode summarise` (auch mit `--set`) | `inputs_sha256` (Bogen, Schlüssel und, sofern vorhanden, `scoring_checks.csv`, `key_points.csv`), `outputs_sha256` (`scores.csv`) | `ragas_eval.py` (Hauptkatalog), `analyse.py` (Pilot-Sets ohne Eintrag mit Hinweis, [ADR 0044](../adr/0044-statistische-auswertung.md)) |
| `summarise_control` | `generation_runs.jsonl` | `K0` | `evaluate_answers.py --mode summarise --control` | `inputs_sha256` (Bogen und Prüfungen von K0, die eingefrorene `key_points.csv` von C1–C3, `scores.csv`), `outputs_sha256` (`scores_control.csv`) | `analyse.py` |
| `ragas` | `generation_runs.jsonl` | `C1,C2,C3` | `ragas_eval.py` ([ADR 0047](../adr/0047-ragas-als-triangulation.md)), nur nach einem erfolgreichen Lauf | siehe unten | `ragas_eval.py --repeat`, `analyse.py` |
| `ragas_repeat` | `generation_runs.jsonl` | `C1,C2,C3` | `ragas_eval.py --repeat` (nur Pilot-Sets) | wie `ragas`, `outputs_sha256` (`ragas_scores_repeat.csv`) | `analyse.py` |
| `second_rater_draw` | `generation_runs.jsonl` | `C1,C2,C3` | `second_rater.py --mode draw` ([ADR 0046](../adr/0046-zweitbewertung.md)) | `inputs_sha256` (`questions.csv`), `outputs_sha256` (`second_rater_sample.csv`), `seed`, `questions` (Zahl) | `second_rater.py --mode export` |
| `second_rater_export` | `generation_runs.jsonl` | `C1,C2,C3` | `second_rater.py --mode export` | `inputs_sha256` (Ziehung, `scoring_items.jsonl`, `key_points.csv`), `outputs_sha256` (Items und Kernpunkte im R2-Ordner) | – |
| `second_rater_close` | `second_rater/runs.jsonl` | `C1,C2,C3` | `second_rater.py --mode close` | `inputs_sha256` (Items, Kernpunkte), `outputs_sha256` (`scoring_checks.csv`, `scoring_sheet.csv`), `rater` (`R2`), `rules_version` | `analyse.py`; danach verweigern Export und Close, die App zeigt den Satz schreibgeschützt |
| `closed_book_screen` | `generation_runs.jsonl` | (kein Feld) | `catalogue.py screen` ([ADR 0040](../adr/0040-closed-book-pruefung.md)) | siehe unten | – |

Die R2-Einträge `scaffold` und `key_points` schreibt `--mode export` in derselben Form wie oben; `--mode close` prüft
den `scaffold`-Eintrag gegen die exportierte Item-Datei.

**`embed`**, Lauf C2 vom 18.10.2026 (alle Läufe im [Experiment-Protokoll](experiment-record.md#embedding-e2e)).
`input_tokens`/`cost_usd` zählen nur die eigenen Texte des Schritts (Chunks einer Strategie bzw. Fragen); `canary_*`
ist die Modellstand-Prüfung getrennt davon (`canary_min_cosine` = niedrigste Kosinus-Ähnlichkeit, `null`, wenn keine
Prüfung nötig war), damit sie die Kosten einer Strategie nicht verfälscht; `api_called` ist `false`, wenn gespeicherte
Vektoren wiederverwendet wurden.
```json
{"date":"2026-10-18","model":"text-embedding-3-large","openai_sdk":"2.44.0","chromadb":"1.5.9","step":"embed","strategy":"C2","dimensions":3072,"vectors":642,"vector_bytes":7888896,"inputs_sha256":{"chunks_c2.jsonl":"5c65075b…"},"canary_min_cosine":0.9999860525131226,"input_tokens":308580,"cost_usd":0.0401154,"canary_input_tokens":1499,"canary_cost_usd":0.00019487,"api_called":true}
```

**`retrieve`**, erster Lauf des Pilot-Sets `e2e` vom 19.10.2026 ([ADR 0033](../adr/0033-antwortmodell.md) für
`outputs_sha256`, Pflicht für den Hauptlauf):
```json
{"date":"2026-10-19","model":"text-embedding-3-large","openai_sdk":"2.44.0","chromadb":"1.5.9","step":"retrieve","strategy":"C1,C2,C3","dimensions":3072,"vectors":16,"inputs_sha256":{"questions.csv":"65971a0a…","ground_truth.csv":"094d0f81…","sections.jsonl":"e2e72242…","query_embeddings.npz":"8d8c6de0…","chunks_c1.jsonl":"74138039…","chunks_c2.jsonl":"5c65075b…","chunks_c3.jsonl":"bce0598f…","embeddings_c1.npz":"68b72f7f…","embeddings_c2.npz":"8f9243e1…","embeddings_c3.npz":"a3b849d9…"},"canary_min_cosine":0.9999375343322754,"outputs_sha256":{"retrieved_results.csv":"a9a95978…"},"input_tokens":460,"cost_usd":5.98e-05,"canary_input_tokens":3388,"canary_cost_usd":0.00044044,"api_called":true}
```

**`generate`**:

- `model`, `reasoning_effort`, `temperature`, `seed`, `max_completion_tokens`: die gepinnten Einstellungen; `model_reported`:
  das Modell, das die API für alle Antworten des Laufs gemeldet hat; `model_created`: Erstellungszeitpunkt des
  Modellobjekts (ISO 8601, UTC), vor und nach dem Lauf gleich; `system_fingerprint`: die gemeldete
  Backend-Konfiguration (`null`, wenn die API keine meldet).
- `openai_sdk`, `date`, `step` (`generate`), `strategy` (`C1,C2,C3`), `answers` (Zahl der Antworten C1–C3),
  `control_answers` (Zahl der K0-Antworten, [ADR 0041](../adr/0041-kontrolle-k0.md)).
- `inputs_sha256`: `retrieved_results.csv`, Fragen, Ground Truth und Chunk-Dateien; `outputs_sha256`:
  `generated_answers.csv` und `generated_answers_control.csv`. `retrieved_results.csv` prüft `generate.py` schon vor
  dem Lauf gegen den `retrieve`-Eintrag; hier ist die Prüfsumme nur aufgezeichnet.
- `prompt_tokens`, `completion_tokens`, `cost_usd` für den Lauf, `by_strategy` dieselben drei je Strategie und für K0
  ([ADR 0008](../adr/0008-kosten-als-variable.md)).

Einen `generate`-Lauf des Hauptexperiments gibt es noch nicht. Beispiel: Lauf des Pilot-Sets `e2e` vom 19.10.2026.
Der ältere Eintrag in `data/pilot/hard/runs.jsonl` (17.10.2026) hat noch die Form vor K0: ohne `control_answers`,
ohne `generated_answers_control.csv`, `by_strategy` ohne K0.
```json
{"date":"2026-10-19","model":"gpt-6-luna","reasoning_effort":"none","temperature":0.0,"seed":20261017,"max_completion_tokens":1024,"openai_sdk":"2.44.0","step":"generate","strategy":"C1,C2,C3","model_reported":"gpt-6-luna","model_created":"2026-09-14T17:15:02+00:00","system_fingerprint":null,"answers":48,"control_answers":16,"inputs_sha256":{"retrieved_results.csv":"a9a95978…","questions.csv":"65971a0a…","ground_truth.csv":"094d0f81…","chunks_c1.jsonl":"74138039…","chunks_c2.jsonl":"5c65075b…","chunks_c3.jsonl":"bce0598f…"},"outputs_sha256":{"generated_answers.csv":"da18da97…","generated_answers_control.csv":"a2131251…"},"by_strategy":{"C1":{"prompt_tokens":38542,"completion_tokens":1271,"cost_usd":0.0044897},"C2":{"prompt_tokens":38954,"completion_tokens":1194,"cost_usd":0.0044924},"C3":{"prompt_tokens":26500,"completion_tokens":1138,"cost_usd":0.003219},"K0":{"prompt_tokens":1211,"completion_tokens":1019,"cost_usd":0.0006306}},"prompt_tokens":105207,"completion_tokens":4622,"cost_usd":0.0128317}
```

**`scaffold`** (Form):
```json
{"date":"…","step":"scaffold","strategy":"C1,C2,C3","scoring":"rules","codes":…,"outputs_sha256":{"scoring_items.jsonl":"…"}}
```

**`ragas`** und **`ragas_repeat`** (`run_log.ragas_record`, Felder in der Reihenfolge, in der sie geschrieben werden;
Pilot-Beispiel im [Experiment-Protokoll](experiment-record.md#ragas-pilot-e2e-21102026)):

- `date`, `judge_model`, `embedding_model`, `reasoning_effort`, `temperature`, `seed`, `strictness`: die gepinnten
  Einstellungen aus `config.py` ([Konfiguration](configuration.md#ragas)); `ragas_version`, `openai_sdk`: installierte
  Versionen.
- `step` (`ragas` oder `ragas_repeat`), `strategy` (`C1,C2,C3`).
- `model_reported`: das Modell, das die API für alle Richteraufrufe gemeldet hat; `model_created`: Erstellungszeitpunkt
  des Modellobjekts (ISO 8601, UTC), vor und nach dem Lauf gleich; `system_fingerprint`: die gemeldete
  Backend-Konfiguration (`null`, wenn die API keine meldet). Meldet die API mehrere Modelle oder Fingerabdrücke, bricht
  der Lauf ohne Schreiben ab ([ADR 0033](../adr/0033-antwortmodell.md)).
- `rows` (Zahl der Zeilen der Ergebnisdatei); `nan_counts`: je Metrik die Zahl der Zeilen mit leerer Zelle (Gründe in
  `nan_reasons` der Ergebnisdatei).
- `inputs_sha256`: `generated_answers.csv`, `retrieved_results.csv`, Fragen, Ground Truth und die drei Chunk-Dateien;
  auf dem Hauptkatalog zusätzlich `scores.csv` (RAGAS läuft erst nach `summarise`).
- `judge_prompt_tokens`, `judge_completion_tokens`, `embedding_tokens` (die Embeddings der Response Relevancy, nur sie
  gehen an das Embedding-Modell); `judge_cost_usd` (nach `RAGAS_JUDGE_PRICE_*`), `embedding_cost_usd`
  (nach `EMBEDDING_PRICE_PER_MTOK`) und `cost_usd` (Summe) in USD.
- zuletzt `outputs_sha256`: die Ergebnisdatei des Schritts.

`ragas_eval.py --repeat` verlangt, dass der `ragas`-Eintrag zur aktuellen `ragas_scores.csv` passt; `analyse.py` prüft
beide Dateien gegen ihren Eintrag (`analysis_data._load_ragas`).

**`closed_book_screen`** hat die gepinnten Einstellungen und `openai_sdk` wie `generate`, dann `answers` (Zahl
der abgerechneten Antworten dieses Aufrufs), `model_reported` und `system_fingerprint` als **sortierte Listen** aller
gemeldeten Werte (fehlender Fingerprint als `""`), `outputs_sha256` mit `closed_book_screen.csv`; er hat weder
`strategy` noch `inputs_sha256`. `screen` schreibt ihn, sobald mindestens eine Antwort abgerechnet wurde, auch nach
einem Abbruch (API-Fehler, abgeschnittene oder leere Antwort).
```json
{"date":"…","model":"gpt-6-luna","reasoning_effort":"none","temperature":0.0,"seed":20261017,"max_completion_tokens":1024,"openai_sdk":"2.44.0","step":"closed_book_screen","answers":…,"model_reported":["…"],"system_fingerprint":["…"],"outputs_sha256":{"closed_book_screen.csv":"…"},"prompt_tokens":…,"completion_tokens":…,"cost_usd":…}
```

## Auswertung (`output/`)

`analyse.py` ([ADR 0044](../adr/0044-statistische-auswertung.md)) schreibt bei jedem Lauf alle Dateien neu; Ordner und
Namen: `config.OUTPUT_DIR`, `TABLES_DIR`, `FIGURES_DIR`, `ANALYSIS_FILE`; die Dateinamen der Tabellen und Abbildungen
stehen in `report_tables.TABLE_NAMES` und `report_figures.FIGURE_NAMES`. Ein Pilot-Set (`--set DIR`) schreibt
dieselbe Struktur nach `DIR/output/`, nie nach `output/`. Was entfällt, nennt `notes` in `analysis.json`; eine
entfallene Tabelle löscht `analyse.py` aus einem früheren Lauf, eine entfallene Abbildung `chunk_lengths.pdf` nicht.

**Tabellen** (`output/tables/<Name>.tex`): je eine `table`-Umgebung nach den IU-Regeln mit kurzem Titel ohne
Schlusspunkt, Label `tab:<Name>`, darunter `\source{Eigene Darstellung. …}` mit den Anmerkungen; Ausrichtung aus der
Klasse; negative Werte mit typografischem Minus.

| Name | Inhalt | entfällt wenn |
|---|---|---|
| `retrieval` | Retrieval-Metriken je Strategie (Hauptregel) | – |
| `retrieval_sensitivity` | dieselben nach der Sensitivitätsregel | – |
| `answers` | Rubrik-Kriterien und Gesamtwert je Strategie | – |
| `tests` | nur die konfirmatorischen Tests | – |
| `tests_descriptive` | W und r der Maße ohne Test | – |
| `control_k0` | K0 gegen C1–C3 | keine K0-Bewertung |
| `correlation` | Rangkorrelation zwischen Retrieval- und Antwortqualität (H2) | – |
| `efficiency` | Chunks, Längen, Kontext-Tokens, Indexgröße, Kosten | Chunk-Dateien oder `embed`-Einträge fehlen |
| `breakdown` | nach Fragetyp, Konstruktionsklasse und Closed-Book-Urteil | – |
| `ragas` | Mittel der vier RAGAS-Metriken je Strategie, Kendalls W | `ragas_scores.csv` fehlt |
| `ragas_effects` | paarweise r, Median-Differenz und n′ | `ragas_scores.csv` fehlt |
| `ragas_agreement` | Spearmans ρ mit dem regelbasierten Gegenstück ([Evaluation](evaluation.md#triangulation)) | `ragas_scores.csv` fehlt |
| `agreement` | Erst- gegen Zweitbewertung ([Evaluation](evaluation.md#zweitbewertung)) | keine abgeschlossene Zweitbewertung |

**Abbildungen** (`output/figures/<Name>.pdf`, in Endgröße; Inhalte: [Evaluation](evaluation.md#visualisierungen)):

| Name | Inhalt | entfällt wenn |
|---|---|---|
| `recall` | Recall@5 je Strategie | – |
| `mrr` | MRR je Strategie | – |
| `answers_distribution` | Verteilung der Gesamtwerte | – |
| `heatmap` | Gesamtwert je Frage und Strategie | – |
| `scatter_retrieval_answer` | Retrieval gegen Antwortqualität | – |
| `catalogue_composition` | Zusammensetzung des Katalogs | – |
| `chunk_lengths` | Histogramme der Chunk-Längen | Chunk-Dateien fehlen (eine ältere Datei bleibt liegen) |
| `cost` | Kosten je Strategie | – (ohne `embed`-Einträge nur die Generierungskosten) |

**`output/analysis.json`**: alle Kennzahlen und Testergebnisse, sortierte Schlüssel, zwei Leerzeichen Einzug,
Gleitkommazahlen auf `config.JSON_DECIMALS` gerundet. Oberste Schlüssel:

- `n_questions`, `alpha`.
- `retrieval`: Mittel je Relevanzregel (`main`, `sensitivity`) und Strategie, einschließlich K1.
- `answers`: `means` je Strategie und Kriterium, einschließlich K0.
- `confirmatory`: Friedman-Test, Holm-korrigierte p, Kendalls W und paarweise Wilcoxon-Tests je Metrik aus
  `config.ANALYSIS_PRIMARY`.
- `descriptive_effects`: Effektstärken ohne p-Werte, getrennt nach Regel und `answers`.
- `control_k0`: K0 gegen C1–C3; `null` ohne K0-Bewertung.
- `correlation`: Spearmans ρ je Strategie und `pooled` (dieses ohne `p`).
- `efficiency`: Chunks, Längen, Kontext-Tokens, Indexgröße, Embedding- und Generierungskosten je Strategie; `null`,
  wenn Chunk-Dateien oder `embed`-Einträge fehlen.
- `breakdown`: nach Fragetyp, Konstruktionsklasse und Closed-Book-Urteil.
- `ragas`: `means` und `nan_counts` je Strategie und Metrik; `effects` je Metrik mit `label`, `kendalls_w`, `n` und
  `pairs` (paarweise r), über die Fragen mit Wert in allen Strategien, ohne p-Werte.
- `ragas_agreement`: Schlüssel `<Metrik>~<Gegenstück>`, je Strategie und `pooled` mit `rho`, `n`, `testable`, ohne
  `p`; `rho` ist `null`, wenn eine Seite konstant ist.
- `ragas_stability`: je Metrik `n`, `mean_abs_diff`, `rho`, `share_equal`; nur wenn `ragas_scores_repeat.csv`
  vorliegt, also bei Pilot-Sets.
- `agreement`: `rows` (je Prüffrage, Kernpunkte und Kriterium mit `group`, `label`, `n`, `agreement`, `measure`, `ac`,
  `ac_ci`, `alpha`, `alpha_ci`, `dropped`), `n_codes`, `n_questions`, `reps`, `level` (Niveau der Intervalle,
  `config.AGREEMENT_CI_LEVEL`); `null` ohne abgeschlossene Zweitbewertung.
- `notes`: entfallene Teile, Hinweise.

Fehlt `ragas_scores.csv`, sind `ragas` und `ragas_agreement` `null`, und die drei Tabellen `ragas`, `ragas_effects`,
`ragas_agreement` entfallen mit Hinweis.

`second_rater_disagreements.csv` liegt ebenfalls in `output/` ([Zweitbewertung](#zweitbewertung)).

## Pilot-Sets

Pilotproben liegen in `config.PILOT_DIR` = `data/pilot/`; sie sind **nicht** Teil des Fragenkatalogs. Ein Set ist ein
Ordner mit den Dateien der Evaluation unter denselben Namen und Formaten. Das Retrieval eines Sets läuft über
`scripts/difficulty_probe.py DIR` (schreibt auch K1); die übrigen Schritte nehmen `--set DIR`, `evaluate_answers.py`
dazu `--limit N` für die ersten N Fragen. Das Laufprotokoll heißt `config.PILOT_RUNS_FILE_NAME` = `runs.jsonl` und
hat die Einträge von `embedding_runs.jsonl` und `generation_runs.jsonl` ([Laufprotokoll](#laufprotokoll)); die
Auswertung liegt in `DIR/output/`. Eine Closed-Book-Prüfung gibt es für Pilot-Sets nicht.

| Set | Zweck | IDs | Korpus |
|---|---|---|---|
| `data/pilot/e2e/` | aktueller Vortest der ganzen Pipeline; nur Abschnitte außerhalb des Stichprobenplans | `E01`–`E16` | e2e |
| `data/pilot/e2e_jonas/` | Übungskopie von `e2e` (alle Fragen und Antworten); bewertet mit `--limit 3` (9 Codes, dieselben wie in `e2e`) | `E01`–`E16` | e2e |
| `data/pilot/` | Probe 1, historisch | `P01`–`P08` | Vue |
| `data/pilot/hard/` | Probe 2, historisch; blinde Annotation ([ADR 0027](../adr/0027-blinde-annotation.md)) | `H01`–`H16` | Vue |
| `data/pilot/hard_posthoc/` | dieselben Fragen mit nachträglich ergänzter Annotation, nur Sensitivität | `H01`–`H16` | Vue |
| `data/pilot/hard/history/` | `ground_truth_b75d188.csv`: blinde Annotation mit den IDs des älteren Vue-Korpus | `H01`–`H16` | Vue (`b75d188`) |

Die Vue-Sets entstanden vor [ADR 0038](../adr/0038-korpus-e2e.md); ihre Abschnitts- und Chunk-IDs gibt es im
e2e-Korpus nicht, sie lassen sich darauf nicht neu ausführen und bleiben als Aufzeichnung erhalten. Vorhandene Dateien
und gelaufene Schritte je Set: [Experiment-Protokoll](experiment-record.md#pilot-sets); Ergebnisse:
[Pilot e2e](experiment-record.md#pilot-e2e-1920102026), Vue-Proben im
[Experiment-Protokoll Vue](experiment-record-vue.md#pilotproben-auf-dem-erweiterten-korpus-14102026).

## Versioniert und ignoriert

Einzige vollständige Liste der Datenartefakte nach `.gitignore`; alles, was hier nicht als ignoriert steht, ist
versioniert, sobald es existiert. Ignoriert sind Dateien, die sich aus versionierten Daten neu erzeugen lassen;
versioniert sind Primärdaten, die kein Lauf exakt wiederholt (Antworten, [ADR 0033](../adr/0033-antwortmodell.md);
Fragevektoren und Retrieval-Ergebnisse des Hauptlaufs, [ADR 0045](../adr/0045-retrieval-ergebnisse-versioniert.md)),
und alles, was Jonas schreibt oder entscheidet.

| Pfad | Inhalt | Format | Status |
|---|---|---|---|
| `docs/corpus_snapshot.txt`, `docs/corpus_manifest.csv` | Snapshot-Datensatz, Korpusmanifest | [Korpus](#korpus) | versioniert |
| `data/raw/e2e_docs_snapshot/` | Rohseiten des Snapshots | [Korpus](#korpus) | ignoriert; nur `.gitkeep` versioniert |
| übrige Ordner in `data/raw/` (z. B. `vue_docs_snapshot/`) | alter Vue-Snapshot, nur lokal | – | ignoriert (`data/raw/*`) |
| `data/processed/` | `documents.jsonl`, `sections.jsonl`, `section_index.md`, `chunks_*.jsonl`, `embeddings_*.npz` | [Korpus](#korpus), [Fragen](#fragen-und-ground-truth), [Chunks](#chunks), [Vektoren](#vektoren) | ignoriert; versioniert nur `.gitkeep` und das Laufprotokoll `embedding_runs.jsonl` ([ADR 0045](../adr/0045-retrieval-ergebnisse-versioniert.md)) |
| `data/processed/archive_vue_2026-10-18/` | Vue-Chunks, -Vektoren, -Laufprotokoll und alter Chroma-Index ([Experiment-Protokoll Vue](experiment-record-vue.md#embedding-vuejs)) | [Laufprotokoll](#laufprotokoll) | ignoriert; versioniert nur `embedding_runs.jsonl` (Kosten der Vue-Läufe) |
| `chroma_db/` (auch `*.chroma`) | Chroma-Index; entsteht beim ersten `embed.py` | [Vektoren](#vektoren) | ignoriert (ganzer Ordner, kein `.gitkeep`) |
| `data/evaluation/questions.csv`, `ground_truth.csv`, `catalogue_plan.csv`, `catalogue_review.csv`, `closed_book_screen.csv`, `catalogue_freeze.json` | Fragenkatalog und seine Aufzeichnungen | [Fragen](#fragen-und-ground-truth) | versioniert |
| `data/evaluation/archive_vue/catalogue_plan.csv` | unbenutzter Vue-Plan ([ADR 0039](../adr/0039-stichprobenplan-e2e.md)) | [Fragen](#fragen-und-ground-truth) | versioniert |
| `data/evaluation/query_embeddings.npz`, `retrieved_results.csv`, `retrieved_results_control.csv`, `retrieval_scores.csv`, `retrieval_scores_control.csv` | Fragevektoren und Retrieval-Ergebnisse des Hauptlaufs | [Vektoren](#vektoren), [Retrieval](#retrieval-ergebnisse) | versioniert ([ADR 0045](../adr/0045-retrieval-ergebnisse-versioniert.md)) |
| `data/evaluation/generated_answers.csv`, `generated_answers_control.csv`, `generation_runs.jsonl` | Antworten C1–C3 und K0, Laufprotokoll | [Antworten](#antworten), [Laufprotokoll](#laufprotokoll) | versioniert |
| `data/evaluation/scoring_sheet.csv`, `scoring_key.csv`, `key_points.csv`, `scoring_checks.csv` | Primärdaten der Bewertung C1–C3 | [Bewertung](#bewertung) | versioniert |
| `data/evaluation/scoring_items_control.jsonl`, `scoring_sheet_control.csv`, `scoring_checks_control.csv` | Bewertung K0 | [Kontrolle K0](#kontrolle-k0) | versioniert |
| `data/evaluation/scoring_packet.md`, `scoring_items.jsonl`, `scores.csv`, `scores_control.csv` | Lesepaket, Daten der Bewertungsseite (vom Scaffold wiederherstellbar), entblindete Werte | [Bewertung](#bewertung) | ignoriert |
| `data/evaluation/ragas_scores.csv` | RAGAS-Werte der Antworten C1–C3, einmal erzeugt ([ADR 0047](../adr/0047-ragas-als-triangulation.md)) | [RAGAS](#ragas) | versioniert |
| `data/evaluation/second_rater_sample.csv`, `data/evaluation/second_rater/` (alle Dateien) | Zweitbewertung (die Items von R2 sind nach dem Bewerten nicht mehr neu erzeugbar) | [Zweitbewertung](#zweitbewertung) | versioniert |
| `data/pilot/**/` | Dateien der Pilot-Sets, auch `ragas_scores*.csv`, `second_rater_sample.csv`, `second_rater/` | [Pilot-Sets](#pilot-sets) | versioniert, außer den drei folgenden Zeilen |
| `data/pilot/**/query_embeddings.npz`, `scoring_packet.md`, `scoring_items.jsonl`, `scores.csv`, `scores_control.csv` | dieselben Dateien wie im Hauptlauf | [Vektoren](#vektoren), [Bewertung](#bewertung) | ignoriert, außer `data/pilot/**/second_rater/scoring_items.jsonl` |
| `data/pilot/**/output/` | Auswertung eines Pilot-Sets (`analyse.py --set`), auch `second_rater_disagreements.csv` | [Auswertung](#auswertung-output) | ignoriert |
| `output/tables/*.tex`, `output/analysis.json`, `output/second_rater_disagreements.csv` | Tabellen, Kennzahlen und Abweichungsliste der Auswertung | [Auswertung](#auswertung-output), [Zweitbewertung](#zweitbewertung) | versioniert (nicht in `.gitignore`) |
| `output/figures/*.pdf` | Abbildungen der Auswertung | [Auswertung](#auswertung-output) | versioniert (Ausnahme von `*.pdf`) |
| `data/corpus_probe/docs/`, `probes/`, `sources/`, `questions/*-sections.json` | nachgebaute Seiten, Proben mit Abschnittstext, Klone der Kandidaten | [Korpusauswahl](corpus-selection.md#dateien-und-befehle) | ignoriert; übrige Dateien in `data/corpus_probe/` versioniert |
| `*.pdf` | erzeugte Dokumente | – | ignoriert, außer `output/figures/*.pdf` (siehe oben) |
| `.env`, `.venv/`, `venv/`, `env/`, `__pycache__/`, `*.py[cod]`, `*.pyo`, `.vscode/`, `.ipynb_checkpoints/`, `.DS_Store` | Geheimnisse, Umgebung, Editor | – | ignoriert |

Die Vue-Verarbeitungsdateien, die nicht im Archivordner liegen (`documents.jsonl`, `sections.jsonl`), entstehen neu
aus `vuejs/docs` auf Commit `40aa88a` mit dem Code vor ADR 0038
([Experiment-Protokoll Vue](experiment-record-vue.md#snapshot-vuejs-bis-18102026)).
