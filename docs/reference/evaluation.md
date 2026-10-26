# Evaluation

*[Doku-Index](../README.md) · Referenz · Verwandt: [Datenformate](data-formats.md#auswertung-output), [Forschungsdesign](../explanation/research-design.md#warum-die-evaluation-so-angelegt-ist), [Experiment durchführen](../how-to/run-the-experiment.md)*

Stand: 26.10.2026. Diese Seite beschreibt die Maße; Ablauf und Befehle stehen in
[Experiment durchführen](../how-to/run-the-experiment.md), Parameterwerte (`TOP_K`, Überlappungsschwellen, Rubrik) in
[Konfiguration](configuration.md).

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

Bezeichnungen je Frage *q*:

- S_q: die annotierten relevanten Abschnitte; c₁ … c_k: die k abgerufenen Chunks nach Rang.
- rel_s(c) = 1, wenn Chunk c den Abschnitt s ∈ S_q um mindestens die Schwelle *m* der gewählten Regel überlappt, sonst 0;
  rel(c) = 1, wenn rel_s(c) = 1 für mindestens ein s ∈ S_q. Alle vier Metriken hängen über *m* von der Relevanzregel ab.

| Metrik | Definition je Frage | zählt |
|---|---|---|
| **Hit@k** | 1, wenn ∃ i ≤ k: rel(cᵢ) = 1, sonst 0 | Chunks |
| **MRR** (Reciprocal Rank) | RR = 1 / min{i ≤ k : rel(cᵢ) = 1}, 0 ohne relevanten Chunk; MRR = Mittel von RR | Chunks |
| **Precision@k** | (1/k) · Σᵢ₌₁ᵏ rel(cᵢ) | Chunks |
| **Recall@k** | \|{s ∈ S_q : ∃ i ≤ k: rel_s(cᵢ) = 1}\| / \|S_q\| | Abschnitte |

Berichtet wird je Strategie und Relevanzregel das Mittel über alle Fragen, zusätzlich je Fragetyp (`type`) und je
Konstruktionsklasse (`difficulty`, [ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md)); die Werte je Frage
stehen in `retrieval_scores*.csv` (`src/evaluate_retrieval.py`). Mehrere relevante Chunks können denselben Abschnitt
decken; deshalb sind P@k (Chunks) und R@k (Abschnitte) nicht direkt vergleichbar.

MRR, P@5 und R@5 werden immer neben Hit@5 berichtet (Befund dazu auf dem Vue-Korpus, 14.10.2026:
[Experiment-Protokoll Vue](experiment-record-vue.md#pilotproben-auf-dem-erweiterten-korpus-14102026)).

## Kontrolle K1

K1 (größengleiche Kontrolle, [ADR 0026](../adr/0026-c3-vergleichbarkeit.md)) durchläuft Chunking, Embedding und
Retrieval, aber keine Antwortgenerierung. Für K1 werden dieselben Retrieval-Metriken berechnet
(`retrieved_results_control.csv`, `evaluate_retrieval.py --control`) und als Kontrollanalyse berichtet, nicht als
vierte Strategie. Lesart: [Forschungsdesign](../explanation/research-design.md#chunking-strategien).

## Antwort-Evaluation (Rubrik 0–2)

Kurzfassung der Stufen ([ADR 0013](../adr/0013-antwort-rubrik.md)); verbindlich vergeben werden die Werte nach der
Ableitungstabelle unter [Regelbasierte Bewertung](#regelbasierte-bewertung).

| Kriterium | 0 | 1 | 2 |
|-----------|---|---|---|
| Korrektheit | falsch | teilweise korrekt | korrekt |
| Vollständigkeit | wesentliche Punkte fehlen | teilweise vollständig | vollständig |
| Quellenbezug | nicht belegt | teilweise belegt | klar durch Quellen gedeckt |
| Halluzinationsfreiheit | falsche/unbelegte Aussagen | kleine unbelegte Ergänzungen | keine Halluzinationen |
| Verständlichkeit | unklar | verständlich mit Schwächen | klar und präzise |

Kriterien in `scores.csv`: `config.RUBRIC_CRITERIA`.

**Gesamtscore:** Mittel der fünf Kriterien (`correctness`, `completeness`, `groundedness`, `no_hallucination`,
`clarity`), Spalte `total_score`, Wertebereich 0–2; alle Kriterien gleich gewichtet (ADR 0013).

## Regelbasierte Bewertung

Regeln nach [ADR 0035](../adr/0035-regelbasierte-bewertung.md) (`src/scoring_rules.py`, Version
`config.RUBRIC_RULES_VERSION`). Vor der Bewertung schreibt Jonas je Frage 1–`config.KEY_POINTS_MAX` Kernpunkte (Punkt 1 =
Kernaussage, die direkte Antwort auf die Frage) und friert sie ein. Die App befüllt sie aus der Referenzantwort vor:
getrennt an Semikolon und an Satzenden vor einem Großbuchstaben, Teile über `KEY_POINTS_MAX` hinaus bleiben im letzten
Punkt (`scoring_rules.split_reference`); Jonas prüft und teilt weiter
([ADR 0037](../adr/0037-praezisierte-pruefregeln-und-vorbefuellte-kernpunkte.md)). Je Antwort werden dann diese
Prüffragen beantwortet:

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

Die Hilfetexte des Bewertungsformulars (`POINT_HELP`, `HELP` in `app/scoring_page.py`) geben diese Prüffragen
wortgleich wieder; wer eine Prüffrage ändert, ändert beide (kein Test prüft das).

Ableitung der Werte, verbindlich ([ADR 0035](../adr/0035-regelbasierte-bewertung.md)):

| Kriterium | 2 | 1 | 0 |
|---|---|---|---|
| Korrektheit | nichts falsch | `other_error` = yes oder `declines` = yes | `core_wrong` = yes |
| Vollständigkeit | alle Kernpunkte enthalten | Anteil enthaltener ≥ `config.RUBRIC_COMPLETENESS_PARTIAL` | sonst |
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
wird ein eigener Kernpunkt. Ein manuelles Überschreiben gibt es nicht; passt eine Regel nicht, wird das in `notes`
vermerkt.

Die Antworten stehen in `scoring_checks.csv` ([Datenformate](data-formats.md#bewertung)). `--mode summarise` prüft,
dass die Kernpunkte die eingefrorenen des aktuellen Scaffolds sind, die Prüfantworten in der Reihenfolge des Bogens
stehen und unter der aktuellen `RUBRIC_RULES_VERSION` gegeben wurden, jede Zeile so viele Kernpunkte markiert, wie ihre
Frage hat, und jede Zeile des Bogens den abgeleiteten Werten entspricht. Auf dem Hauptkatalog brechen Scaffold und
Summarise zudem ab, wenn der Freeze-Datensatz eine andere Regelversion hält (`freeze.require_rules_version`): der
Hauptlauf wird nach den Regeln bewertet, die beim Einfrieren galten.

## Blinde Bewertung

Die Bewertung von C1–C3 sieht die Strategie nicht; die drei Antworten einer Frage stehen unter neutralen Codes in
gemischter Reihenfolge (`config.SCORING_SEED`), die Zuordnung liegt in einem Schlüssel, den erst die Auswertung liest
([ADR 0032](../adr/0032-blinde-rubrik-bewertung.md); Dateien: [Datenformate](data-formats.md#bewertung)).

## Kontrolle K0

K0 beantwortet dieselben Fragen ohne Retrieval mit dem Closed-Book-Prompt
([Prompts](prompts.md#closed-book-prompt-prüfung-und-k0)) und wird nach C1–C3 als eigener Satz bewertet
([ADR 0041](../adr/0041-kontrolle-k0.md)): dieselben eingefrorenen Kernpunkte und Prüffragen ohne `grounded`. `declines`
fragt, ob die Antwort sagt, dass sie die Antwort nicht weiß, und keine gibt (eine Teilantwort mit dem Hinweis, der Rest
sei unbekannt, ist keine Ablehnung, [ADR 0043](../adr/0043-praezisierung-direct-und-teilantworten.md));
`hallucination`, ob sie etwas enthält, das die Referenz nicht deckt. Abgeleitet werden Korrektheit, Vollständigkeit,
Halluzinationsfreiheit und Verständlichkeit nach den Regeln oben (`config.CONTROL_CRITERIA`); der Gesamtwert ist ihr
Mittelwert. Der Vergleich mit C1–C3 nutzt dieselben vier Kriterien (die Gesamtwerte von C1–C3 werden dafür auf diesen
vier neu gemittelt), über alle Fragen, je Fragetyp, je Konstruktionsklasse und getrennt nach dem Closed-Book-Urteil
(retrieval-abhängig, bekannt, nicht beurteilt; [ADR 0040](../adr/0040-closed-book-pruefung.md); `src/control_k0.py`).
Je Strategie stehen die mittlere Differenz je Kriterium sowie r und Median-Differenz des Gesamtwerts über vier
Kriterien gegen K0. K0 wird nicht blind bewertet. Begründung:
[Forschungsdesign](../explanation/research-design.md#warum-closed-book-prüfung-und-k0).

## Zweitbewertung

Entscheidung: [ADR 0046](../adr/0046-zweitbewertung.md); Ablauf und Befehle:
[Experiment durchführen](../how-to/run-the-experiment.md#zweitbewertung); Dateien:
[Datenformate](data-formats.md#zweitbewertung).

- **Stichprobe:** `config.SECOND_RATER_QUESTIONS` Fragen, mit festem Seed (`config.SECOND_RATER_SEED`) geschichtet
  nach Fragetyp und Konstruktionsklasse, proportional zum Katalog (bei 12 Fragen: je Klasse 3; factual, procedural, conceptual je 3; comparative und
  limitation zusammen 3, also 2 + 1, der Seed entscheidet). Die Ziehung kennt keine Ergebnisse: Sie zieht nur
  aus `questions.csv` und prüft lediglich, ob Bogen oder Prüfantworten schon Werte enthalten.
- **Satz:** R2 bewertet die Antworten C1–C3 dieser Fragen unter denselben Codes in derselben Reihenfolge, mit Jonas'
  eingefrorenen Kernpunkten und nach denselben Regeln.
- **Maße** (`src/agreement.py`, `src/stats.py`): je Prüffrage, für die Kernpunkt-Markierungen (gepoolt) und je
  Kriterium die einfache Übereinstimmung, Gwets AC1 (Ja/Nein-Prüffragen, Kernpunkte) bzw. AC2 mit ordinalen Gewichten
  (`grounded` none < some < all, `hallucination` substantive < minor < none, Kriterien 0–2) und Krippendorffs α
  (ordinal), jeweils mit Perzentil-Bootstrap-Intervall über die Fragen als Cluster (`config.AGREEMENT_*`); wie viele
  Wiederholungen entfallen, steht in der Anmerkung der Tabelle. Ist α nicht bestimmbar (nur eine Kategorie), steht
  „nicht bestimmbar“. Warum kein Cohens Kappa: ADR 0046.
- **Bericht:** Tabelle `agreement.tex` (Anhang B) mit den Bezeichnungen Ablehnung (`declines`), Kernaussage falsch
  (`core_wrong`), Anderer Fehler (`other_error`), Durch Passagen gestützt (`grounded`), Halluzination
  (`hallucination`), Frage beantwortet (`answers_question`), Direkt (`direct`), Wortreich (`wordy`); dazu
  `output/second_rater_disagreements.csv` zum Besprechen. Die Werte der Arbeit bleiben Jonas' Bewertung.
- **In `analyse.py`:** Fehlt die Zweitbewertung oder ist sie nicht abgeschlossen, entfallen Tabelle und CSV mit Hinweis
  (Dateien eines früheren Laufs werden entfernt); passen ihre Dateien nicht mehr zum Abschlusseintrag oder weichen
  Items und Kernpunkte von Jonas' Satz ab, bricht `analyse.py` ab.
- **Ersatzverfahren** ohne zweite Person bis Mitte November (Intra-Rater und Sprachmodell, ADR 0046): noch nicht
  umgesetzt.

## Triangulation

Grundlage der Antwort-Evaluation ist die regelbasierte, referenzbasierte Bewertung oben
([ADR 0007](../adr/0007-triangulation.md)). RAGAS kommt als feste zweite, automatische Sicht hinzu
([ADR 0047](../adr/0047-ragas-als-triangulation.md)): Faithfulness, Response Relevancy, Context Precision und Context
Recall (beide mit Referenz) auf allen Antworten C1–C3, Richtermodell `config.RAGAS_JUDGE_MODEL` (nicht das
Antwortmodell), erst nach `summarise`, einmal ausgeführt und gespeichert. Es ist nie alleinige Grundlage und fließt
nie zurück ([ADR 0017](../adr/0017-fragenkatalog.md)); berichtet werden Mittel je Strategie und die Übereinstimmung
(Spearmans ρ) mit dem Gegenstück: Faithfulness mit Quellenbezug und Halluzinationsfreiheit, Response Relevancy mit
`answers_question`, Context Precision und Recall mit P@5 und R@5. Begründung:
[Forschungsdesign](../explanation/research-design.md#warum-die-evaluation-so-angelegt-ist).

**Eingaben** (`src/ragas_eval.py`, Optionen: [Werkzeuge](tooling.md#skripte-und-optionen), Dateien:
[Datenformate](data-formats.md#ragas)): Je Frage und Strategie C1–C3 bekommt der Richter die Frage, die
gespeicherte Antwort, die Chunk-Texte aus `sources` der Antwortzeile in dieser Reihenfolge (genau das, was das
Antwortmodell sah) und die eingefrorene Referenz. K0 hat keinen Kontext und wird nicht bewertet. Vor dem ersten Aufruf
wird geprüft, dass der Katalog eingefroren ist, die Antworten vom letzten `generate`-Lauf stammen und auf dem
Hauptkatalog `summarise` gelaufen ist.

- **Richter:** `RAGAS_JUDGE_MODEL`, `RAGAS_TEMPERATURE`, `RAGAS_REASONING_EFFORT`, `RAGAS_SEED`
  ([Konfiguration](configuration.md#ragas)); Response Relevancy vergleicht mit `config.EMBEDDING_MODEL`. RAGAS 0.4.3
  hält jedes Modell von gpt-5 bis gpt-19 für ein Reasoning-Modell und würde die Temperatur auf 1,0 setzen; eine dünne
  Unterklasse in `src/ragas_client.py` behält die konfigurierte Temperatur, aber nur bei `reasoning_effort` `none`,
  sonst gilt die Abbildung von RAGAS ([Pins](tooling.md#ragas-pins)).
- **Strictness:** Response Relevancy erzeugt aus der Antwort `RAGAS_STRICTNESS` Fragen und vergleicht deren Embeddings
  mit der echten Frage; Wert und Grund: [ADR 0047, Nachtrag](../adr/0047-ragas-als-triangulation.md#nachtrag-21102026-strictness-1).
- **NaN:** Meldet eine Metrik selbst NaN, ist das gültig: leere Zelle, der Grund in `nan_reasons`, gezählt und im Lauf
  berichtet. Liefert RAGAS 0.4.3 ein NaN ohne Grund, steht der feste Grund je Metrik aus `config.RAGAS_NAN_REASONS`
  (keine Aussagen oder Urteile bei Faithfulness, keine Klassifikationen bei Context Recall, NaN als mittlere Präzision
  bei Context Precision). Response Relevancy liefert 0,0 statt NaN, ein NaN dort wäre unerwartet, hat keinen Grund und
  bricht den Lauf. Ebenso brechen ein Wert außerhalb 0–1, ein Fehler des Richters, eine abgeschnittene Ausgabe
  (`RAGAS_MAX_TOKENS`) und ein wechselndes Modell oder mehrere System-Fingerabdrücke ab; dann wird nichts geschrieben.
  Mittel gelten über die Fragen mit Wert, Effektstärken über die Fragen mit Wert in allen Strategien
  ([ADR 0047, Nachtrag](../adr/0047-ragas-als-triangulation.md#nachtrag-26102026-fehlende-werte)).
- **Übereinstimmung** (`ragas_agreement`): Spearmans ρ je Antwort zwischen Metrik und Gegenstück, je Strategie und über
  alle Strategien (`gesamt`, jede Frage dreifach), beschreibend ohne p-Werte; eine Frage ohne RAGAS-Wert entfällt im
  Paar, ist eine Seite konstant, steht „nicht bestimmbar“ (in keiner Gruppe bestimmbar: eine Zeile für das ganze Paar).
- **Effekte** (`ragas_effects`): je Metrik paarweise r und Median-Differenz wie in der Statistik; neben jedem r steht
  n′, die Zahl der Fragen mit Differenz ungleich 0 ([ADR 0044](../adr/0044-statistische-auswertung.md)).
- **Stabilität:** Auf Pilot-Sets läuft `--repeat` ein zweites Mal; `ragas_stability` in `analysis.json` vergleicht
  beide Läufe je Metrik (Anteil gleicher Werte, mittlere absolute Differenz, ρ). Befund des Pilots:
  [Experiment-Protokoll](experiment-record.md#ragas-pilot-e2e-21102026). Der Hauptlauf läuft einmal.

## Effizienz/Kosten (abhängige Variable)

Nach [ADR 0008](../adr/0008-kosten-als-variable.md) und [ADR 0026](../adr/0026-c3-vergleichbarkeit.md), je Strategie;
für K1 ohne Generierung, für K0 ([ADR 0041](../adr/0041-kontrolle-k0.md)) nur die Generierungs-Tokens (kein Chunking,
kein Retrieval):

| Kennzahl | Definition | Quelle |
|---|---|---|
| Chunk-Anzahl | Zeilen in `chunks_*.jsonl` | Chunk-Dateien |
| Chunk-Länge | Median und Mittel von `end_token − start_token` | Chunk-Dateien |
| Kontext-Tokens je Antwort (Kontext@k) | Mittel über die Fragen der summierten Längen der k abgerufenen Chunks | Spalte `context_tokens` in `retrieval_scores*.csv` (aus `retrieved_results*.csv` und den Chunk-Dateien) |
| Indexgröße | Bytes der gespeicherten Vektoren (`vector_bytes` = n × Dimensionen × 4); in `efficiency.tex` in MB (dezimal) | `embedding_runs.jsonl` |
| Embedding-Tokens und -Kosten | `input_tokens`, `cost_usd` (Modellstand-Prüfung getrennt) | `embedding_runs.jsonl` |
| Generierungs-Tokens | `prompt_tokens` + `completion_tokens` je Antwort; Summen und Kosten je Strategie und K0 unter `by_strategy` im Laufprotokoll | `generated_answers.csv`, `generated_answers_control.csv` (K0), `generation_runs.jsonl` |

Die Kosten stehen neben den Qualitätswerten (Tabelle `efficiency.tex`, Abbildung `cost.pdf`, Generierung und Embedding
getrennt), ohne Verhältniszahl ([ADR 0008](../adr/0008-kosten-als-variable.md),
[ADR 0044](../adr/0044-statistische-auswertung.md)). Kosten und Tokens je Antwort in `efficiency.tex` sind die
Summen des Laufs geteilt durch die Zahl der Fragen.

## Statistische Auswertung

Entscheidung: [ADR 0044](../adr/0044-statistische-auswertung.md); `src/analyse.py` liest nur Ergebnisdateien mit
aktuellem Laufeintrag und schreibt `output/` ([Datenformate](data-formats.md#auswertung-output)). Rechnung in
`src/stats.py`, Tabellen in `src/report_tables.py`, Abbildungen in `src/report_figures.py`.

**Konfirmatorisch** sind nur die Tests der drei primären Metriken (`config.ANALYSIS_PRIMARY`): Der Plan stand vor dem
Hauptlauf fest, die Fehlerrate ist mit Holm kontrolliert
([ADR 0044, Nachtrag](../adr/0044-statistische-auswertung.md#nachtrag-22102026-konfirmatorische-tests)). Alle übrigen
p-Werte (H2-Korrelationen) sind explorativ.

| Schritt | Verfahren |
|---|---|
| Metriken | R@5, MRR (Hauptregel `config.ANALYSIS_RULE`) und Gesamtwert der Antworten |
| Omnibus | Friedman-Test über C1–C3 je Metrik, Holm-Korrektur über die p-Werte der testbaren Metriken (eine konstante Metrik hat kein p und fällt aus der Familie; [ADR 0044, Nachtrag](../adr/0044-statistische-auswertung.md#nachtrag-26102026-holm-über-die-testbaren-metriken)), Niveau `config.ANALYSIS_ALPHA` |
| Paare | nur für Metriken mit korrigiertem p < α Wilcoxon-Tests C1–C2, C1–C3, C2–C3: zweiseitig, Normalapproximation, Bindungskorrektur, ohne Stetigkeitskorrektur, Nulldifferenzen verworfen, Differenzen auf `config.ANALYSIS_DIFF_DECIMALS` Stellen gerundet; ein Paar mit einer Differenz ungleich 0 ist testbar; Holm über alle diese Paare |
| Effektstärken | Kendalls W = χ²_F / (n (k − 1)) aus dem bindungskorrigierten Friedman-Wert (voll gebundene Fragen zählen in n) und r = \|z\| / √n′ (n′ = Differenzen ungleich 0); die Richtung zeigt die Median-Differenz |

**Beschreibend** (Mittel, Median, Effektstärken, keine p-Werte): nach der Hauptregel Hit@5, P@5 und Kontext@5, nach
der Sensitivitätsregel alle Retrieval-Metriken, die fünf Kriterien der Rubrik, K0 gegen C1–C3 über
`config.CONTROL_CRITERIA` und die Aufteilung nach Fragetyp, Konstruktionsklasse und Closed-Book-Urteil (je Strategie,
mit R@5 und Gesamtwert).

**Zusammenhang Retrieval und Antwort** (H2, [ADR 0009](../adr/0009-hypothesen.md)): Spearmans ρ zwischen R@5 bzw. MRR
und dem Gesamtwert, je Strategie und gepoolt (gepoolt nur ρ: jede Frage geht dreifach ein); „nicht bestimmbar“ bei
weniger als drei Fragen oder einer konstanten Seite.

Teile ohne Eingabedaten entfallen mit einem Hinweis in `notes` von `analysis.json`
([Datenformate](data-formats.md#auswertung-output)). Die Mittel der Einzelschritte (`evaluate_retrieval.py`,
`evaluate_answers.py --mode summarise`) bleiben Konsolenausgabe.

**Wo steht was** (Tabellen in `output/tables/`, Schlüssel in `output/analysis.json`):

| Maß | Tabelle | Schlüssel |
|---|---|---|
| Retrieval-Mittel, Hauptregel (mit K1) | `retrieval.tex` | `retrieval.main` |
| Retrieval-Mittel, Sensitivitätsregel | `retrieval_sensitivity.tex` | `retrieval.sensitivity` |
| Antwort-Mittel je Kriterium | `answers.tex` | `answers.means` |
| Konfirmatorische Tests | `tests.tex` | `confirmatory` |
| Effektstärken ohne Test, Hauptregel und Kriterien | `tests_descriptive.tex` | `descriptive_effects.main`, `descriptive_effects.answers` |
| Effektstärken ohne Test, Sensitivitätsregel | keine (nur JSON) | `descriptive_effects.sensitivity` |
| K0 gegen C1–C3 | `control_k0.tex` | `control_k0` |
| H2-Korrelation | `correlation.tex` | `correlation` |
| Aufteilung nach Gruppen | `breakdown.tex` | `breakdown` |
| Effizienz und Kosten | `efficiency.tex` | `efficiency` |
| RAGAS-Mittel und Kendalls W | `ragas.tex` | `ragas` |
| RAGAS paarweise r, Median-Differenz, n′ | `ragas_effects.tex` | `ragas.effects` |
| RAGAS gegen regelbasierte Bewertung | `ragas_agreement.tex` | `ragas_agreement` |
| Zweitbewertung | `agreement.tex` | `agreement` |

## Visualisierungen

Umgesetzt in `src/report_figures.py` ([ADR 0044](../adr/0044-statistische-auswertung.md)); `src/analyse.py` schreibt
die acht PDFs nach `output/figures/`:

| Datei | Zeigt | Zweck |
|---|---|---|
| `recall.pdf` | Balken R@5 je Strategie, K1 als schraffierte Kontrolle | Retrieval-Vergleich |
| `mrr.pdf` | Balken MRR je Strategie, K1 schraffiert | Rankingqualität |
| `answers_distribution.pdf` | Punktdiagramm des Gesamtwerts je Frage und Strategie mit Median und Mittel (statt Boxplot: die Werte sind stark gebunden); K0 über vier Kriterien als Kontrolle, sofern bewertet | Verteilung der Antwortqualität |
| `heatmap.pdf` | Gesamtwert je Frage × Strategie, einfarbige Skala, Werte in den Zellen | Wo funktioniert welche Strategie? |
| `scatter_retrieval_answer.pdf` | R@5 gegen Gesamtwert, ein Panel je Strategie (Small Multiples), Markerfläche = Zahl der Fragen, ρ im Panel | Entkopplung Retrieval/Antwort (H2) |
| `catalogue_composition.pdf` | Zähltabelle der Fragen nach Fragetyp × Konstruktionsklasse | Zusammensetzung des Katalogs |
| `chunk_lengths.pdf` | Histogramm der Chunk-Längen je Strategie und K1 (schraffiert), gemeinsame Klassen, Median markiert | Unterschiede der Strategien |
| `cost.pdf` | Generierungskosten je 1.000 Antworten (C1–C3, K0) neben den einmaligen Embedding-Kosten je Strategie (inkl. K1) | Effizienzbetrachtung ([ADR 0008](../adr/0008-kosten-als-variable.md)) |

Gestaltung nach den PaperLab-Regeln (Werte in `config.FIGURE_*`): Endgröße, Einbinden ohne Skalieren; volle Breite
17 cm, die Heatmap 0,6 und die Zähltabelle 0,75 davon. Arial (eingebettet; sonst DejaVu Sans mit Hinweis in `notes`),
kein Titel im Bild (Titel über `\caption`), deutsche Dezimalkommas, Klassenfarben FigBlue und FigOrange plus ein auf
Farbsehschwäche geprüfter dritter Farbton, Kontrollen grau und schraffiert, Werte der Heatmap beschriftet. Die PDFs
sind byte-reproduzierbar.
