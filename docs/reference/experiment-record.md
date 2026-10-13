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

## Modellversionen (bei der Umsetzung eintragen)

| Komponente | Version | Datum der ersten Nutzung |
|---|---|---|
| LLM | | |
| Embedding-Modell | | |
| OpenAI Python SDK | | |
| ChromaDB | | |
| tiktoken | 0.13.0 | 13.10.2026 |
