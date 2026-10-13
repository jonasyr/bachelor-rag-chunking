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

## Schwierigkeitsprobe (Pilot, 14.10.2026)

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

## Modellversionen (bei der Umsetzung eintragen)

| Komponente | Version | Datum der ersten Nutzung |
|---|---|---|
| LLM | | |
| Embedding-Modell | `text-embedding-3-large`, 3.072 Dimensionen ([ADR 0023](../adr/0023-embedding-modell.md)) | 13.10.2026 |
| OpenAI Python SDK | 2.44.0 | 13.10.2026 |
| ChromaDB | 1.5.9 | 13.10.2026 |
| tiktoken | 0.13.0 | 13.10.2026 |
