# Evaluation

> Seitentyp: Nachschlagen (reference). Stand: 19.10.2026. Übersicht: [Dokumentation](../README.md).

Parameterwerte (`TOP_K`, Überlappungsschwellen, Rubrik): [Konfiguration](configuration.md).

## Relevanz eines Chunks

Ein abgerufener Chunk *c* ist für Frage *q* relevant, wenn seine Token-Spanne die Spanne eines Abschnitts aus
`relevant_section_ids` derselben Seite um mindestens *m* Tokens überlappt (Spannen `[start, end)` im gemeinsamen
Token-Raum von `src/tokens.py`; `src/relevance.py`).

| Regel | Schwelle *m* | Verwendung | Entscheidung |
|---|---|---|---|
| Hauptregel | `RELEVANCE_MIN_OVERLAP` (jede Überlappung) | `is_relevant` in `retrieved_results*.csv`, alle Hauptwerte | [ADR 0019](../adr/0019-korpus-ausschnitt.md) |
| Sensitivität | min(`SENSITIVITY_MIN_OVERLAP`, Länge von *c*), mindestens 1 | Wiederholung der Retrieval-Auswertung; kurze Chunks, die ganz im Abschnitt liegen, bleiben relevant | [ADR 0026](../adr/0026-c3-vergleichbarkeit.md) |

Welche Abschnitte relevant sind, legt die Annotation fest: blind vor jedem Retrieval
([ADR 0027](../adr/0027-blinde-annotation.md)), H1-Abschnitte nur nach
[ADR 0022](../adr/0022-h1-abschnitte-in-ground-truth.md).

## Retrieval-Evaluation

Beantwortet: Findet das System die richtigen Dokumentstellen? Metriken nach
[ADR 0012](../adr/0012-retrieval-metriken.md), k = `TOP_K` ([ADR 0014](../adr/0014-temperatur-und-topk.md)).

Bezeichnungen je Frage *q*: *S_q* = annotierte relevante Abschnitte; *c_1 … c_k* = die k abgerufenen Chunks nach Rang;
rel(*c_i*) = 1, wenn *c_i* relevant ist (oben), sonst 0.

| Metrik | Definition je Frage | Einheit |
|---|---|---|
| **Hit@k** | 1, wenn mindestens ein *c_i* relevant ist, sonst 0 | Chunks |
| **MRR** (Reciprocal Rank) | 1 / Rang des ersten relevanten Chunks; 0, wenn keiner relevant ist | Chunks |
| **Precision@k** | Σ rel(*c_i*) / k — Anteil relevanter Chunks unter den Top-k | Chunks |
| **Recall@k** | Anteil der Abschnitte in *S_q*, die mindestens ein *c_i* überlappt | Abschnitte |

Berichtet wird je Strategie und Relevanzregel das Mittel über alle Fragen (MRR = mittlerer Reciprocal Rank),
zusätzlich je Fragetyp (`type`) und je Konstruktionsklasse (`difficulty`,
[ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md)); die Werte je Frage stehen in
`retrieval_scores*.csv` (`src/evaluate_retrieval.py`). Precision@k zählt Chunks, Recall@k zählt Abschnitte; deshalb
können mehrere relevante Chunks denselben Abschnitt decken.

MRR und Recall@5 werden immer neben Hit@5 berichtet; Hit@5 allein unterscheidet die Strategien kaum (Pilotproben:
[Experiment-Protokoll](experiment-record.md#pilotproben-auf-dem-erweiterten-korpus-14102026)).

## Kontrolle K1

K1 (größengleiche Kontrolle, [ADR 0026](../adr/0026-c3-vergleichbarkeit.md)) durchläuft Chunking, Embedding und
Retrieval, aber keine Antwortgenerierung. Für K1 werden dieselben Retrieval-Metriken berechnet
(`retrieved_results_control.csv`, `evaluate_retrieval.py --control`) und als Kontrollanalyse berichtet, nicht als
vierte Strategie. Lesart: [Forschungsdesign](../explanation/research-design.md#chunking-strategien).

## Antwort-Evaluation (Rubrik 0–2)

| Kriterium | 0 | 1 | 2 |
|-----------|---|---|---|
| Korrektheit | falsch | teilweise korrekt | korrekt |
| Vollständigkeit | wesentliche Punkte fehlen | teilweise vollständig | vollständig |
| Quellenbezug | nicht belegt | teilweise belegt | klar durch Quellen gedeckt |
| Halluzinationsfreiheit | falsche/unbelegte Aussagen | kleine unbelegte Ergänzungen | keine Halluzinationen |
| Verständlichkeit | unklar | verständlich mit Schwächen | klar und präzise |

Kriterien in `scores.csv`: `config.RUBRIC_CRITERIA` ([ADR 0013](../adr/0013-antwort-rubrik.md)).

**Gesamtscore:** Mittel der fünf Kriterien (`correctness`, `completeness`, `groundedness`, `no_hallucination`,
`clarity`), Spalte `total_score`, Wertebereich 0–2; alle Kriterien gleich gewichtet
([ADR 0013](../adr/0013-antwort-rubrik.md)).

## Regelbasierte Bewertung

Die Tabelle oben fasst die Stufen zusammen; vergeben werden die Werte nach den folgenden Regeln
([ADR 0035](../adr/0035-regelbasierte-bewertung.md), `src/scoring_rules.py`, Version `config.RUBRIC_RULES_VERSION`). Vor
der Bewertung schreibt Jonas je Frage 1–`config.KEY_POINTS_MAX` Kernpunkte (Punkt 1 = Kernaussage, die direkte Antwort
auf die Frage) und friert sie ein; die App befüllt sie aus der Referenzantwort vor (getrennt an Semikolon und Satzende),
Jonas prüft und teilt weiter ([ADR 0037](../adr/0037-praezisierte-pruefregeln-und-vorbefuellte-kernpunkte.md)). Je
Antwort werden dann diese Prüffragen beantwortet:

| Prüffrage | Frage | Optionen |
|---|---|---|
| Kernpunkt *n* (Spalte `points`: je Kernpunkt ein Eintrag, durch `;` getrennt) | Steht Kernpunkt *n* mit derselben Bedeutung in der Antwort, auch in anderen Worten? (nur teilweise = fehlt; eine Einschränkung in Klammern muss nicht enthalten sein) | `covered`, `missing` |
| `declines` | Sagt die Antwort, dass die Passagen die Antwort nicht enthalten, und gibt keine? (eine Teilantwort mit dem Hinweis, der Rest stehe nicht in den Passagen, ist keine Ablehnung: `no`, die fehlenden Teile sind fehlende Kernpunkte) | `yes`, `no` |
| `core_wrong` | Gibt die Antwort die Kernaussage falsch wieder oder widerspricht ihr? | `yes`, `no` |
| `other_error` | Ist eine andere Aussage sachlich falsch? | `yes`, `no` |
| `grounded` | Wie viele Aussagen der Antwort sind durch die Passagen belegt? | `all`, `some`, `none` |
| `hallucination` | Enthält die Antwort etwas, das weder Passagen noch Referenz decken? (`minor` = ändert die Antwort nicht, `substantive` = ändert sie oder widerspricht) | `none`, `minor`, `substantive` |
| `answers_question` | Geht die Antwort auf das Gefragte ein? | `yes`, `no` |
| `direct` | Steht die Kernaussage der Antwort in den ersten zwei Sätzen? (auch wenn sie falsch ist, das zählt unter Korrektheit, und auch wenn ein zweiter Teil der Frage später folgt; [ADR 0043](../adr/0043-praezisierung-direct-und-teilantworten.md)) | `yes`, `no` |
| `wordy` | Ist die Antwort wiederholend, aufgebläht oder verwirrend? | `yes`, `no` |

| Kriterium | 2 | 1 | 0 |
|---|---|---|---|
| Korrektheit | nichts falsch | `other_error` = yes oder `declines` = yes | `core_wrong` = yes |
| Vollständigkeit | alle Kernpunkte enthalten | Anteil enthaltener ≥ `config.RUBRIC_COMPLETENESS_PARTIAL` (0,5) | sonst |
| Quellenbezug | `grounded` = all | `grounded` = some | `grounded` = none |
| Halluzinationsfreiheit | `hallucination` = none | `hallucination` = minor | `hallucination` = substantive |
| Verständlichkeit | `answers_question` = yes, `direct` = yes, `wordy` = no | `answers_question` = yes, sonst | `answers_question` = no |

Korrektheit wird in dieser Reihenfolge geprüft: `core_wrong` = yes ergibt 0, sonst `other_error` oder `declines` 1,
sonst 2. Bei `declines` = yes werden Kernpunkte, `core_wrong`, `other_error`, `grounded` und `hallucination` nicht
gefragt und als `missing`/`no`/`no`/`all`/`none` gespeichert: Korrektheit 1, Vollständigkeit 0, Quellenbezug 2,
Halluzinationsfreiheit 2, Verständlichkeit nach ihren Prüffragen. Als Halluzination zählt, was weder die
Kontextpassagen noch die Referenzantwort decken oder was ihnen widerspricht. Eine wahre Aussage, die weder Passagen noch
Referenz decken, zählt als nicht belegt (`grounded`) und als Halluzination (`minor`, wenn sie die Antwort nicht
ändert); ein erfundener Beispielname zur Veranschaulichung ist keine Halluzination. Ein Nebensatz, der zählen soll,
wird ein eigener Kernpunkt. Ein manuelles Überschreiben gibt es nicht; passt
eine Regel nicht, wird das in `notes` vermerkt. Die Antworten stehen in `scoring_checks.csv`
([Datenformate](data-formats.md)); `--mode summarise` prüft, dass die Kernpunkte die eingefrorenen sind, jede
Zeile so viele Kernpunkte markiert, wie ihre Frage hat, und jede Zeile des Bogens den abgeleiteten Werten entspricht.

## Kontrolle K0

K0 beantwortet dieselben Fragen ohne Retrieval mit dem Closed-Book-Prompt
([Prompts](prompts.md#closed-book-prompt-prüfung-und-k0)) und wird nach C1–C3 als eigener Satz bewertet
([ADR 0041](../adr/0041-kontrolle-k0.md)): dieselben eingefrorenen Kernpunkte und Prüffragen ohne `grounded`. `declines`
fragt, ob die Antwort sagt, dass sie die Antwort nicht weiß, und keine gibt; `hallucination`, ob sie etwas enthält, das
die Referenz nicht deckt. Abgeleitet werden Korrektheit, Vollständigkeit, Halluzinationsfreiheit und Verständlichkeit
nach den Regeln oben (`config.CONTROL_CRITERIA`); der Gesamtwert ist ihr Mittelwert. Der Vergleich mit C1–C3 nutzt
dieselben vier Kriterien (die Gesamtwerte von C1–C3 werden dafür auf diesen vier neu gemittelt), über alle Fragen, je
Fragetyp, je Konstruktionsklasse und getrennt nach dem Closed-Book-Urteil (retrieval-abhängig / bekannt,
[ADR 0040](../adr/0040-closed-book-pruefung.md); `src/control_k0.py`). K0 wird nicht blind bewertet. Begründung:
[Forschungsdesign](../explanation/research-design.md#warum-closed-book-prüfung-und-k0).

## Blinde Bewertung

Die Bewertung von C1–C3 sieht die Strategie nicht; die drei Antworten einer Frage stehen unter neutralen Codes in
gemischter Reihenfolge (`config.SCORING_SEED`), die Zuordnung liegt in einem Schlüssel, den erst die Auswertung liest
([ADR 0032](../adr/0032-blinde-rubrik-bewertung.md); Dateien: [Datenformate](data-formats.md)).

## Triangulation (optional)

Grundlage der Antwort-Evaluation ist die regelbasierte, referenzbasierte Bewertung oben
([ADR 0007](../adr/0007-triangulation.md)). Ein automatisiertes Framework (RAGAS, in `pyproject.toml` deklariert)
kommt optional hinzu, und erst nachdem die regelbasierte Bewertung abgeschlossen ist
([ADR 0015](../adr/0015-tech-stack.md), [Plan](../plan.md)); Code dafür gibt es noch nicht. Wird es eingesetzt, ist es
nie alleinige Grundlage, und seine Übereinstimmung mit der regelbasierten Bewertung wird berichtet. Begründung:
[Forschungsdesign](../explanation/research-design.md#warum-die-evaluation-so-angelegt-ist).

## Effizienz/Kosten (abhängige Variable)

Nach [ADR 0008](../adr/0008-kosten-als-variable.md) und [ADR 0026](../adr/0026-c3-vergleichbarkeit.md), je Strategie;
für K1 ohne Generierung, für K0 ([ADR 0041](../adr/0041-kontrolle-k0.md)) nur die Generierungs-Tokens (kein Chunking,
kein Retrieval):

| Kennzahl | Definition | Quelle |
|---|---|---|
| Chunk-Anzahl | Zeilen in `chunks_*.jsonl` | Chunk-Dateien |
| Chunk-Länge | Median und Mittel von `end_token − start_token` | Chunk-Dateien |
| Kontext-Tokens je Antwort (Kontext@k) | Mittel über die Fragen der summierten Längen der k abgerufenen Chunks | Spalte `context_tokens` in `retrieval_scores*.csv` (aus `retrieved_results*.csv` und den Chunk-Dateien) |
| Indexgröße | Bytes der gespeicherten Vektoren (`vector_bytes` = n × Dimensionen × 4) | `embedding_runs.jsonl` |
| Embedding-Tokens und -Kosten | `input_tokens`, `cost_usd` (Modellstand-Prüfung getrennt) | `embedding_runs.jsonl` |
| Generierungs-Tokens | `prompt_tokens` + `completion_tokens` je Antwort; Summen und Kosten je Strategie und K0 unter `by_strategy` im Laufprotokoll | `generated_answers.csv`, `generated_answers_control.csv` (K0), `generation_runs.jsonl` |

Geplant (noch nicht umgesetzt): Qualitätsunterschiede den Kosten gegenüberstellen
([ADR 0008](../adr/0008-kosten-als-variable.md)).

## Zweitbewertung (empfohlen)

Mit denselben Prüffragen in der App, ohne Schlüssel ([ADR 0032](../adr/0032-blinde-rubrik-bewertung.md),
[ADR 0036](../adr/0036-regelbasierte-bewertung-verpflichtend.md)): eine Kopie des Sets als Ordner unter `data/pilot/`
(z. B. `data/pilot/zweitbewertung`) mit `scoring_items.jsonl`, `key_points.csv` (die eingefrorenen Kernpunkte),
`runs.jsonl` (mit dem `scaffold`- und `key_points`-Eintrag) und leerem `scoring_sheet.csv`, ohne `scoring_key.csv` und
ohne `scoring_checks.csv`; die zweite Person bewertet dort 10–20 % der Antworten unabhängig. Einfache Übereinstimmung
je Prüffrage und je Kriterium = gleiche Antworten / alle Antworten, oder durchschnittliche absolute Abweichung bei der
0–2-Skala. Cohen's Kappa optional.

## Statistische Auswertung

Umgesetzt: `evaluate_retrieval.py` gibt die Mittel der Retrieval-Metriken aus; `evaluate_answers.py --mode summarise`
(mit `--control` für K0 gegen C1–C3) gibt Mittel, Median und Standardabweichung des Gesamtwerts und das Mittel je
Kriterium aus, jeweils je Strategie über alle Fragen, je Fragetyp und je Konstruktionsklasse (siehe oben).

Geplant für die Phase „Bewertung und Analyse" ([Plan](../plan.md)), noch nicht umgesetzt: Boxplots, Korrelation von
Retrieval- und Antwortwerten, optional Signifikanztests (Friedman-Test für mehrere verbundene Gruppen, Wilcoxon
Signed-Rank paarweise).

## Visualisierungen (geplant)

Noch nicht umgesetzt; Grundlage der Abbildungen in der Arbeit.

| Visualisierung | Zweck |
|----------------|-------|
| Balkendiagramm Recall@k je Strategie (K1 als Kontrolle) | Retrieval-Vergleich |
| Balkendiagramm MRR je Strategie (K1 als Kontrolle) | Rankingqualität |
| Boxplot Antwortscore je Strategie | Verteilung der Antwortqualität |
| Heatmap Frage × Strategie | Wo funktioniert welche Strategie? |
| Scatterplot Retrieval-Score vs. Antwortscore | Entkopplung Retrieval/Antwort (H2, [ADR 0009](../adr/0009-hypothesen.md)) |
| Balkendiagramm Fragetypen und Konstruktionsklassen | Zusammensetzung des Katalogs |
| Chunk-Längen-Histogramm | Unterschiede der Strategien |
| Kosten-/Tokenvergleich | Effizienzbetrachtung ([ADR 0008](../adr/0008-kosten-als-variable.md)) |
