# 0034. Bewertung in der App

## Status

Angenommen (17.10.2026; ergänzt [ADR 0032](0032-blinde-rubrik-bewertung.md))

## Kontext

- Die blinde Bewertung (ADR 0032) lief über ein Markdown-Lesepaket und eine CSV, die von Hand gefüllt wird; das ist
  bei 144 Antworten fehleranfällig (Tippfehler, falsche Zeile) und mühsam.
- Die App hat schon eine Seite für den Fragenkatalog, die nie Chunks oder Ergebnisse zeigt (ADR 0027).
- Für eine Oberfläche braucht die App Antworten und Passagen je Code als Daten; ohne Schlüssel ist das Lesepaket die
  einzige blinde Quelle, und Markdown zu parsen wäre brüchig.

## Entscheidung

Wir werden die Bewertung als zweite Seite „Scoring“ der App anbieten (Start wie bisher über
`app/catalogue_editor.py`). `evaluate_answers.py --mode scaffold` schreibt zusätzlich `scoring_items.jsonl`: je Code
Frage, Referenzantwort, Antwort und die Passagen in Rangfolge, ohne Strategie und ohne Chunk-IDs. Die Seite liest nur
diese Datei und den Bewertungsbogen und schreibt nur den Bogen; den Schlüssel öffnet sie nie. Sobald `scores.csv`
existiert, ist der Bogen in der App schreibgeschützt.

## Konsequenzen

- Gut: Bewertung ohne Tippfehler im CSV, mit Fortschritt und Rubrik-Ankern; der Bogen bleibt die Primärquelle und
  `summarise` unverändert.
- Gut: Die Katalogseite behält ihre Zusicherung aus ADR 0027; Antworten und Passagen stehen nur auf der Bewertungsseite.
- Neutral: Lesepaket und Bogen bleiben für die Zweitbewertung ohne App erhalten.
- Schlecht: Eine weitere abgeleitete Datei, die zu Bogen und Schlüssel passen muss; die App prüft, dass die Codes
  übereinstimmen. Geht sie verloren, schreibt ein erneutes `scaffold` mit gleichem Schlüssel nur Lesepaket und
  Einträge neu und lässt den Bogen mit den Bewertungen unverändert (Hinweis aus dem Abschluss-Review).
