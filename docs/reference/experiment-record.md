# Experiment-Protokoll

> Seitentyp: Nachschlagen (reference). Übersicht: [Dokumentation](../README.md).

Wird bei der Umsetzung ausgefüllt und ist die Quelle für das Methodik- und Implementierungskapitel. Ausschnitt:
[Korpus](corpus.md) ([ADR 0019](../adr/0019-korpus-ausschnitt.md)).

## Snapshot

| Feld | Wert |
|---|---|
| Repository | `vuejs/docs` (https://github.com/vuejs/docs) |
| Commit | `b75d188ab16bf83bd1f364a77dfd2315be8f3fa4` (Commit-Datum 31.07.2026) |
| Datum des Snapshots | 13.10.2026 ([`corpus_snapshot.txt`](../corpus_snapshot.txt): Commit, Daten, SHA-256 je Datei) |
| Verwendete Pfade | siehe `docs/corpus_manifest.csv` |
| Anzahl Dateien | 52 |
| Gesamtumfang (Tokens) | 117.594 nach Preprocessing (`cl100k_base`); 560 Abschnitte (H1–H3) |

## Chunking

| Strategie | Chunks | Tokens min / Mittel / max |
|---|---:|---|
| C1 | 260 | 11 / 452 / 500 |
| C2 | 305 | 108 / 469 / 500 |
| C3 | 493 | 50 / 239 / 799 |

## Embedding

Einmaliger Lauf am 13.10.2026 (`src/embed.py`; Protokoll `data/processed/embedding_runs.jsonl`). Die von OpenAI
abgerechneten Tokens stimmen exakt mit der eigenen Zählung (`cl100k_base`, `src/tokens.py`) überein. Ein zweiter Lauf
nutzte die gespeicherten Referenzvektoren ohne API-Aufruf ([ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)).

| Strategie | Vektoren | Eingabe-Tokens | Kosten (USD) | Vektordatei |
|---|---:|---:|---:|---:|
| C1 | 260 | 117.594 | 0,0153 | 6,0 MB |
| C2 | 305 | 142.894 | 0,0186 | 7,0 MB |
| C3 | 493 | 117.594 | 0,0153 | 13,0 MB |
| Summe | 1.058 | 378.082 | 0,0492 | 26,0 MB |

Prüfung: Für je 25 zufällig gewählte Chunk-Vektoren je Strategie stimmt Chromas Top-5 mit der exakten
Kosinus-Rangfolge überein, der Chunk selbst steht auf Rang 1 (75/75); Vektornormen 0,9994–1,0007.

Wiederholungsmessung (13.10.2026, 2.706 Tokens, 0,00035 USD): je drei Chunks pro Strategie erneut eingebettet;
Kosinus zum gespeicherten Vektor ≥ 0,99996 (7 von 9 bitgleich), ähnlichster anderer Chunk ≤ 0,84. Daraus der
Schwellwert 0,999 der Modellstand-Prüfung ([ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md)).

## Schwierigkeitsprobe 1: einfache Fragen (Pilot, 14.10.2026)

Zweck: prüfen, ob das Retrieval auf dem Korpus schwer genug ist, um die Strategien zu unterscheiden (kein
Deckeneffekt). Acht Pilotfragen in `data/pilot/` (alle fünf Fragetypen, fünf Korpusbereiche, je ein relevanter
Abschnitt); sie sind **nicht** Teil des Fragenkatalogs. Auswertung: `scripts/difficulty_probe.py`; Kosten 0,0004 USD.

| Strategie | Hit@5 | MRR | Precision@5 | Recall@5 |
|---|---:|---:|---:|---:|
| C1 | 1,00 | 0,94 | 0,23 | 1,00 |
| C2 | 1,00 | 0,79 | 0,30 | 1,00 |
| C3 | 1,00 | 0,94 | 0,23 | 1,00 |

Befund: Bei einfachen Fragen mit genau einem passenden Abschnitt finden alle Strategien die Antwort (Hit@5 und
Recall@5 = 1,00, Deckeneffekt); Unterschiede zeigen sich nur in Rang und Präzision (MRR, Precision@5). Folgerung für den
Fragenkatalog: anspruchsvollere Fragen (mehrere Abschnitte oder Seiten, Detailfragen, Fragen ohne wörtliche Nähe zur
Überschrift) und MRR/Precision@5 als zentrale Kennzahlen.

## Schwierigkeitsprobe 2: schwere Fragen (Pilot, 14.10.2026)

Zweck: prüfen, ob der Deckeneffekt aus Probe 1 an den Fragen oder am Korpus liegt, bevor über eine Erweiterung des
Korpus (ADR 0019) entschieden wird. 16 bewusst schwere Pilotfragen in `data/pilot/hard/`, **nicht** Teil des
Fragenkatalogs, drei Arten (Feld `notes`):

- **multi-section** (5): Die Antwort braucht zwei oder drei Abschnitte, teils auf verschiedenen Seiten.
- **detail** (4): Die Antwort ist ein einzelnes Detail in einem kurzen Abschnitt (Version, Option, Konvention).
- **paraphrase** (7): Die Frage beschreibt ein Symptom ohne die Begriffe der Überschrift.

Auswertung: `uv run python scripts/difficulty_probe.py data/pilot/hard`; Kosten 0,0004 USD (391 Frage-Tokens plus
2.706 Tokens Modellstand-Prüfung, Kosinus 0,99996). Recall@5 = Anteil der relevanten Abschnitte einer Frage, die ein
Top-5-Chunk überlappt.

| Strategie | Hit@5 | MRR | Precision@5 | Recall@5 |
|---|---:|---:|---:|---:|
| C1 | 1,00 | 0,83 | 0,35 | 0,94 |
| C2 | 0,94 | 0,72 | 0,40 | 0,85 |
| C3 | 1,00 | 0,75 | 0,28 | 0,89 |

Nach Fragenart (MRR / Recall@5):

| Art | C1 | C2 | C3 |
|---|---|---|---|
| multi-section (n = 5) | 1,00 / 0,90 | 1,00 / 0,83 | 0,67 / 0,73 |
| detail (n = 4) | 0,88 / 1,00 | 0,71 / 1,00 | 0,88 / 1,00 |
| paraphrase (n = 7) | 0,68 / 0,93 | 0,52 / 0,79 | 0,74 / 0,93 |

Annotation nachträglich korrigiert (offengelegt, weil nach Sicht der Ergebnisse): Die Durchsicht aller Chunks, die vor
dem ersten relevanten Treffer rangierten, ergab drei Abschnitte, die eine richtige (Teil-)Antwort enthalten, aber
fehlten: `D046#cross-request-state-pollution` (H04), `D027#dom-update-timing` (H10, `nextTick()` als Alternative) und
`D033#how-reactivity-works-in-vue` (H16, nennt den Verlust der Reaktivität beim Destrukturieren wörtlich). Regel: Ein
Abschnitt ist relevant, wenn er eine richtige Antwort oder Teilantwort enthält; nicht ergänzt wurden daher
`D004#potential-dangers` (allgemein, ohne `v-html`) und `D034` (veraltete Reactivity Transform). Werte vor der Korrektur:
C1 1,00 / 0,74 / 0,30 / 0,97, C2 0,94 / 0,67 / 0,35 / 0,89, C3 0,94 / 0,72 / 0,24 / 0,85 (Hit@5 / MRR / P@5 / R@5).
Beide Läufe stehen in `data/pilot/hard/runs.jsonl` (verschiedene SHA-256 der Ground Truth).

Befund:

- Der Deckeneffekt liegt an den Fragen, nicht am Korpus: Auf demselben Korpus trennen schwere Fragen die Strategien
  (MRR 0,72–0,83, Recall@5 0,85–0,94 statt 0,79–0,94 und 1,00 in Probe 1). Hit@5 bleibt nahe 1 und taugt allein nicht
  zur Unterscheidung.
- Fragen mit mehreren Abschnitten sind für C3 am schwersten (Recall@5 0,73): Strukturtreue Chunks sind kleiner und
  zahlreicher, sodass fünf Plätze seltener alle Teilantworten abdecken.
- C2 verfehlt bei H11 (`v-model.lazy`, 72-Token-Abschnitt) als einzige Strategie jeden relevanten Chunk.
- n = 16 ist zu klein für Signifikanzaussagen; die Werte zeigen nur, dass der Katalog die Strategien trennen kann.

Folgerung für den Fragenkatalog: einen festen Anteil schwerer Fragen (mehrere Abschnitte, Paraphrase, Detail) vorsehen;
Relevanz-Annotation über den ganzen Korpus suchen, nicht nur auf der naheliegenden Seite (die Lücken oben fand erst die
Durchsicht); MRR und Recall@5 neben Hit@5 berichten.

Zwischenfall: Der erste Lauf brach ab, weil Chroma für eine C3-Frage einen echten Top-5-Treffer (`C3_D034_0006`,
Kosinus 0,325) nicht lieferte; die Prüfung gegen die exakte NumPy-Rangfolge ([ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md))
verhinderte ein falsches Ergebnis. Nicht reproduzierbar: 12 neue Prozesse gegen den Index, 10 Neuaufbauten mit Abfrage im
getrennten Prozess und 1.200 leicht verrauschte Anfragen ergaben keine Abweichung; alle Vektoren waren erreichbar.
Chroma schreibt die Indexdateien beim Lesen neu, sodass der Zustand des Abbruchs nicht erhalten ist. Die Kosten des
abgebrochenen Laufs (gleiche Größenordnung, rund 0,0004 USD) sind nicht protokolliert, weil `retrieve.py` erst am Ende
in `runs.jsonl` schreibt.

## Modellversionen (bei der Umsetzung eintragen)

| Komponente | Version | Datum der ersten Nutzung |
|---|---|---|
| LLM | | |
| Embedding-Modell | `text-embedding-3-large`, 3.072 Dimensionen ([ADR 0023](../adr/0023-embedding-modell.md)) | 13.10.2026 |
| OpenAI Python SDK | 2.44.0 | 13.10.2026 |
| ChromaDB | 1.5.9 | 13.10.2026 |
| tiktoken | 0.13.0 | 13.10.2026 |
