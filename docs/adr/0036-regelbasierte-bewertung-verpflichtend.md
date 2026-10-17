# 0036. Regelbasierte Bewertung verpflichtend für neue Scaffolds

## Status

Angenommen (17.10.2026; präzisiert [ADR 0035](0035-regelbasierte-bewertung.md))

## Kontext

- ADR 0035 macht die Regeln zur operativen Bewertung, aber `--mode summarise` nahm weiter einen von Hand mit 0–2
  gefüllten Bogen an, solange weder Kernpunkte eingefroren noch Prüffragen gespeichert waren; das Lesepaket forderte
  sogar dazu auf.
- Damit hätte ein Lauf die Regeln umgehen können, ohne dass es auffällt.

## Entscheidung

Wir werden jedes neue Scaffold als regelbasiert kennzeichnen (`"scoring":"rules"` im `scaffold`-Eintrag,
`config.SCORING_METHOD`). Für ein solches Scaffold entblindet `--mode summarise` nur mit eingefrorenen Kernpunkten und
`scoring_checks.csv`; von Hand eingetragene Werte werden abgewiesen. Das Lesepaket ist nur noch Lesekopie und verweist
auf die Prüffragen. Die Zweitbewertung läuft mit denselben Prüffragen in der App auf einer Kopie des Sets.

## Konsequenzen

- Jeder Wert eines neuen Laufs ist aus Prüfantworten abgeleitet; ein Umgehen der Regeln fällt bei `summarise` auf.
- Scaffolds ohne Kennzeichnung (vor dieser Entscheidung, z. B. `data/pilot/hard`) behalten ihr bisheriges Verhalten,
  solange dort keine Kernpunkte eingefroren sind; mit dem Einfrieren gelten auch dort die Regeln.
- Die Zweitbewertung misst die Übereinstimmung je Prüffrage und je Kriterium, nicht nur je Gesamtwert.
