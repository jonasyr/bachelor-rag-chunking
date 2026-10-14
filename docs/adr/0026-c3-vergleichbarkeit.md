# 0026. C3-Vergleichbarkeit: Größenkontrolle K1 und faire Sensitivitätsregel

## Status

Angenommen (14.10.2026; ergänzt [ADR 0005](0005-drei-chunking-strategien.md), [ADR 0019](0019-korpus-ausschnitt.md) und [ADR 0021](0021-c3-grenzen.md))

## Kontext

- C3 unterscheidet sich von C1/C2 in Struktur und Größe: auf dem Korpus nach [ADR 0025](0025-korpus-guide-api-styleguide.md) Median 190 gegen 500 Tokens; bei top 5 erhält das Sprachmodell mit C3 nur etwa halb so viel Kontext. Ohne Kontrolle ist nicht trennbar, ob ein Unterschied aus der Struktur oder aus der Größe kommt.
- Kleinere Chunks erhöhen die Precision bei etwa gleichem Recall (Smith & Troynikov, 2024, mit `text-embedding-3-large` und fünf abgerufenen Chunks); die beste Größe hängt vom Fragetyp ab (Bhat et al., 2025).
- Die geplante Sensitivitätsprüfung (Mindestüberlappung 100 Tokens) hätte jeden Chunk unter 100 Tokens grundsätzlich ausgeschlossen, auch einen vollständig im relevanten Abschnitt liegenden; das benachteiligt C3 systematisch.
- Die Entscheidung fällt vor dem Einfrieren der Ground Truth ([ADR 0017](0017-fragenkatalog.md)). Zwei Pilotproben existieren und sind im [Experiment-Protokoll](../reference/experiment-record.md) offengelegt; die Begründung stützt sich auf das Design-Argument und die Literatur, nicht auf Pilotwerte.

## Entscheidung

Wir werden eine größengleiche Kontrolle K1 bilden: Fixed-size ohne Overlap mit der kaufmännisch gerundeten (0,5 aufwärts) mittleren C3-Chunklänge als Fenstergröße, festgelegt in `config.K1_CHUNK_SIZE` (derzeit 231) und von `chunking.py` gegen die Regel geprüft. K1 ist nicht Teil von `STRATEGY_IDS`, durchläuft Chunking, Embedding und Retrieval, aber keine Antwortgenerierung.
Wir werden in der Sensitivitätsprüfung einen Chunk als relevant werten, wenn er einen relevanten Abschnitt um mindestens min(100, Chunk-Länge) Tokens überlappt; die Hauptregel (jede Überlappung) bleibt.
Wir werden für jede Strategie Chunk-Anzahl, Median und Mittel der Chunk-Länge sowie die Kontext-Tokens je Antwort berichten.

## Konsequenzen

- Gut: Struktur- und Größeneffekt werden trennbar: Schlägt C3 C1, aber K1 ebenso, liegt der Effekt in der Größe; schlägt C3 auch K1, in der Struktur.
- Gut: Die Sensitivitätsprüfung benachteiligt kleine Chunks nicht mehr konstruktionsbedingt.
- Neutral: K1 kostet 0,0215 USD Embedding; keine Generierungskosten.
- Schlecht: Eine vierte Retrieval-Reihe vergrößert die Auswertung; sie wird als Kontrollanalyse berichtet, nicht als vierte Strategie.
