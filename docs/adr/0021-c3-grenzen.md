# 0021. C3: Untergrenze 50 Tokens, Verschmelzen vor dem Teilen

## Status

Angenommen (13.10.2026; konkretisiert [ADR 0005](0005-drei-chunking-strategien.md))

## Kontext

- ADR 0005 legt für C3 Abschnitte unter H2/H3 mit höchstens 800 Tokens fest und verlangt, Unter- und Obergrenze sowie die
  Absatz-Unterteilung zu dokumentieren; eine Untergrenze war offen.
- Auf dem bereinigten Korpus ergeben die H1–H3-Überschriften 560 Segmente; 77 davon haben weniger als 50 Tokens, meist
  eine H2 direkt gefolgt von einer H3 oder eine einzeilige Einleitung. Als eigene Chunks wären sie nahezu inhaltsleer,
  belegten top-k-Plätze und blähten die Chunk-Zahl von C3 auf.
- Eine Verschmelzung nur bei Einhaltung der Obergrenze ließ Überschriften wie „# Watchers“ (4 Tokens) allein stehen,
  sobald der folgende Abschnitt zu lang war.

## Entscheidung

Wir werden C3 in drei Schritten bilden: (1) Segmente zwischen H1–H3-Überschriften; (2) ein Segment unter 50 Tokens
(`C3_MIN_TOKENS`) wird immer mit dem folgenden verschmolzen, ein kurzes letztes Segment mit dem vorherigen; (3) ein
Segment über 800 Tokens (`C3_MAX_TOKENS`) wird am letzten passenden Absatzende geteilt, sodass kein Rest unter 50 Tokens
entsteht; Absätze in Codeblöcken werden nicht getrennt; ohne passendes Absatzende wird hart geschnitten.

## Konsequenzen

- Gut: Alle 493 C3-Chunks liegen zwischen 50 und 799 Tokens; jede Überschrift steht bei ihrem Inhalt.
- Gut: Chunk-Texte bleiben exakte Ausschnitte des Dokuments; die Relevanz über Token-Überlappung bleibt gültig.
- Neutral: Untergrenze, Obergrenze und Teilungsregel werden im Methodikkapitel genannt.
- Schlecht: Ein Chunk kann mehrere kurze Abschnitte umfassen und ist damit nicht immer genau ein Abschnitt.

## Nachtrag (14.10.2026): Begründung der Obergrenze 800

- Die Eingabegrenze des Embedding-Modells (8.192 Tokens) ist ein technisches Maximum, keine Empfehlung. Längere Chunks verdünnen den Vektor eines Chunks (Smith & Troynikov, 2024) und gäben C3 bei festem `top_k` mehr Kontext als C1/C2 ([ADR 0006](0006-nur-chunking-variiert.md)).
- Gemessen auf dem Korpus nach [ADR 0025](0025-korpus-guide-api-styleguide.md): Ohne Obergrenze wäre der längste Chunk 1.467 Tokens lang; die Grenze 800 teilt 12 von 706 Segmenten. Sie wirkt also nur auf wenige lange Abschnitte.
- Größeneffekte gegenüber C1/C2 kontrolliert [ADR 0026](0026-c3-vergleichbarkeit.md).
