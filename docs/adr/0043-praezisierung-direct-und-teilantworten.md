# 0043. Präzisierte Prüfregeln: `direct` bei falscher Kernaussage, Teilantworten

## Status

Angenommen (20.10.2026; ergänzt [ADR 0035](0035-regelbasierte-bewertung.md) und
[ADR 0037](0037-praezisierte-pruefregeln-und-vorbefuellte-kernpunkte.md); Anlass: [Pilot e2e](../reference/experiment-record.md#pilot-e2e-1920102026))

## Kontext

- Im Pilot auf e2e wendete der bewertende Agent `direct` uneinheitlich an: bei C1–C3 „nein“, wenn die Antwort mit einer
  falschen Kernaussage beginnt, bei K0 „ja“. Die Prüffrage „Steht die Kernaussage in den ersten zwei Sätzen?“ lässt
  beides zu: Kernaussage der Referenz oder Kernaussage der Antwort.
- Liest man sie als Kernaussage der Referenz, verliert eine falsche Antwort zweimal, unter Korrektheit (`core_wrong`)
  und unter Verständlichkeit; die Kriterien wären nicht mehr unabhängig.
- Einige Antworten beantworten einen Teil der Frage und sagen, der Rest stehe nicht in den Passagen. `declines` verlangt
  „und gibt keine“; der Hilfetext der App sagte dazu nichts.

## Entscheidung

Wir werden `direct` auf die Kernaussage der Antwort beziehen: `yes`, wenn sie in den ersten zwei Sätzen steht, auch wenn
sie falsch ist; ob sie stimmt, prüfen `core_wrong`, `other_error` und `hallucination`.
Wir werden eine Teilantwort mit dem Hinweis, der Rest stehe nicht in den Passagen (bei K0: sei unbekannt), nicht als
Ablehnung werten: `declines` = `no`, die fehlenden Teile zählen als fehlende Kernpunkte.
Wir werden beides in [Evaluation](../reference/evaluation.md#regelbasierte-bewertung) und im Hilfetext der
Bewertungsseite festhalten und `config.RUBRIC_RULES_VERSION` auf `2026-10-20` setzen; die Ableitung der Werte bleibt.

## Konsequenzen

- Positiv: Verständlichkeit misst nur den Aufbau der Antwort; eine falsche Antwort verliert einmal, unter Korrektheit.
  Zwei Bewerter kommen bei denselben Fällen zum selben Ergebnis.
- Negativ: Prüfungen unter der alten Version (Pilot-Sets) passen nicht mehr zur aktuellen; `--mode summarise` lehnt sie
  ab. Die Pilot-Sets sind schon ausgewertet und zählen nicht.
- Neutral: Der Hauptkatalog ist noch nicht bewertet; alle echten Bewertungen laufen unter `2026-10-20`.
