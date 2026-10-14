# Evaluation

> Seitentyp: Nachschlagen (reference). Stand: 14.10.2026. Übersicht: [Dokumentation](../README.md).

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
([ADR 0027](../adr/0027-blinde-annotation.md)), H1-Abschnitte nur nach [ADR 0022](../adr/0022-h1-abschnitte-in-ground-truth.md).

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

Berichtet wird je Strategie das Mittel über alle Fragen (MRR = mittlerer Reciprocal Rank), zusätzlich je Fragetyp.
Precision@k zählt Chunks, Recall@k zählt Abschnitte; deshalb können mehrere relevante Chunks denselben Abschnitt decken.

## Kontrolle K1

K1 (größengleiche Kontrolle, [ADR 0026](../adr/0026-c3-vergleichbarkeit.md)) durchläuft Chunking, Embedding und
Retrieval, aber keine Antwortgenerierung. Für K1 werden dieselben Retrieval-Metriken berechnet
(`retrieved_results_control.csv`) und als Kontrollanalyse berichtet, nicht als vierte Strategie. Lesart: Schlägt C3
C1 und K1 ebenso, liegt der Effekt in der Größe; schlägt C3 auch K1, in der Struktur.

## Antwort-Evaluation (Rubrik 0–2)
| Kriterium | 0 | 1 | 2 |
|-----------|---|---|---|
| Korrektheit | falsch | teilweise korrekt | korrekt |
| Vollständigkeit | wesentliche Punkte fehlen | teilweise vollständig | vollständig |
| Quellenbezug | nicht belegt | teilweise belegt | klar durch Quellen gedeckt |
| Halluzinationsfreiheit | falsche/unbelegte Aussagen | kleine unbelegte Ergänzungen | keine Halluzinationen |
| Verständlichkeit | unklar | verständlich mit Schwächen | klar und präzise |

Kriterien in `scores.csv`: `config.RUBRIC_CRITERIA` ([ADR 0013](../adr/0013-antwort-rubrik.md)).

**Gesamtscore:** Q = (K + V + G + H + L) / 5 (Spalte `total_score`), Wertebereich 0–2; optional Q_norm = (Q/2)·100.
**Gewichtung:** alle Kriterien gleich gewichtet, da keine priorisierte Domäne (Medizin/Recht/Sicherheit) untersucht wird — leichter zu begründen als komplexe Gewichtungen.

## Triangulation (verbindlich)

Entscheidung: [ADR 0007](../adr/0007-triangulation.md).

- **Primär:** referenzbasierte manuelle Bewertung (eigene Ground Truth, nicht zirkulär, verteidigbar).
- **Sekundär:** automatisiertes Framework (RAGAS) mit Metriken wie Faithfulness und Kontextrelevanz (skalierbar, reproduzierbar).
- **Validitätsindikator:** Übereinstimmung zwischen manueller und automatisierter Bewertung wird ausgewertet. Übereinstimmung → Robustheit; Abweichung → eigener Befund zur Metrik-Zuverlässigkeit.
- RAGAS ist **nie alleinige Grundlage** (LLM-as-a-judge hat bekannte Zuverlässigkeitsgrenzen).

## Effizienz/Kosten (abhängige Variable)

Nach [ADR 0008](../adr/0008-kosten-als-variable.md) und [ADR 0026](../adr/0026-c3-vergleichbarkeit.md), je Strategie
(und für K1 ohne Generierung):

| Kennzahl | Definition | Quelle |
|---|---|---|
| Chunk-Anzahl | Zeilen in `chunks_*.jsonl` | Chunk-Dateien |
| Chunk-Länge | Median und Mittel von `end_token − start_token` | Chunk-Dateien |
| Kontext-Tokens je Antwort (Kontext@k) | Mittel über die Fragen der summierten Längen der k abgerufenen Chunks | `retrieved_results*.csv` + Chunk-Dateien |
| Indexgröße | Bytes der gespeicherten Vektoren (`vector_bytes` = n × Dimensionen × 4) | `embedding_runs.jsonl` |
| Embedding-Tokens und -Kosten | `input_tokens`, `cost_usd` (Modellstand-Prüfung getrennt) | `embedding_runs.jsonl` |
| Generierungs-Tokens | `prompt_tokens` + `completion_tokens` | `generated_answers.csv` |

Qualitätsunterschiede werden den Kosten gegenübergestellt („X % bessere Retrieval-Qualität bei Y× Kosten").

## Arbeitsdefinition Halluzination
Eine Halluzination liegt vor, wenn die Antwort Informationen enthält, die weder durch die Kontextpassagen noch durch die Referenzantwort gedeckt sind oder diesen widersprechen. Bewertung 2/1/0 wie in der Rubrik.

## Zweitbewertung (empfohlen)
10–20 % der Antworten unabhängig durch eine zweite Person bewerten lassen. Einfache Übereinstimmung = gleiche Bewertungen / alle Bewertungen, oder durchschnittliche absolute Abweichung bei 0–2-Skala. Cohen's Kappa optional.

## Statistische Auswertung
Deskriptiv ausreichend: Mittelwert, Median, Standardabweichung, Boxplot, Vergleich nach Fragetyp, Korrelation Retrieval vs. Antwortscore. Optional Signifikanztests: Friedman-Test (mehrere verbundene Gruppen), Wilcoxon Signed-Rank (paarweise) — nur bei Sicherheit im Umgang damit.


## Visualisierungen

| Visualisierung | Zweck |
|----------------|-------|
| Balkendiagramm Recall@k je Strategie (K1 als Kontrolle) | Retrieval-Vergleich |
| Balkendiagramm MRR je Strategie (K1 als Kontrolle) | Rankingqualität |
| Boxplot Antwortscore je Strategie | Verteilung der Antwortqualität |
| Heatmap Frage × Strategie | Wo funktioniert welche Strategie? |
| Scatterplot Retrieval-Score vs. Antwortscore | Entkopplung Retrieval/Antwort (H2, [ADR 0009](../adr/0009-hypothesen.md)) |
| Bar Chart Fragetypen | Zusammensetzung des Katalogs |
| Chunk-Längen-Histogramm | Unterschiede der Strategien |
| Kosten-/Tokenvergleich | Effizienzbetrachtung ([ADR 0008](../adr/0008-kosten-als-variable.md)) |
