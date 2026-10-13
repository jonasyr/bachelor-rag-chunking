# 0020. Kodierte Playground-URLs beim Preprocessing kürzen

## Status

Angenommen (13.10.2026; ergänzt [ADR 0019](0019-korpus-ausschnitt.md))

## Kontext

- Der Korpus verlinkt Beispiele im Vue Playground und im Template Explorer, z. B.
  `[Try it in the Playground](https://play.vuejs.org/#eNp9…)`. Der Teil nach `#` enthält den kompletten Beispielcode
  komprimiert und kodiert; er ist für Menschen und Embeddings bedeutungslos.
- Auf Commit `b75d188` belegen diese URLs 21.862 von 139.500 Tokens (15,7 %), eine einzelne URL bis zu 886 Tokens.
- Größenbasierte Chunks (C1, C2) würden dadurch teilweise mit Zeichenrauschen gefüllt, C3 bräuchte für eine einzige URL
  einen harten Schnitt; Embeddings und die gemessenen Kosten ([ADR 0008](0008-kosten-als-variable.md)) würden verzerrt.

## Entscheidung

Wir werden in Link-Zielen außerhalb von Code den kodierten Teil (`#…`) von URLs auf `play.vuejs.org`, `sfc.vuejs.org`,
`explorer.vuejs.org` und `template-explorer.vuejs.org` entfernen; Linktext und Adresse bleiben erhalten.

## Konsequenzen

- Gut: Der Korpus schrumpft auf 117.594 Tokens ohne inhaltlichen Verlust; der Hinweis, dass ein Live-Beispiel
  existiert, bleibt im Text.
- Gut: Die Bereinigung gilt für alle Strategien gleich; nur das Chunking variiert weiterhin ([ADR 0006](0006-nur-chunking-variiert.md)).
- Neutral: Der Bereinigungsschritt wird in der Methodik zusammen mit den übrigen Regeln aus [ADR 0019](0019-korpus-ausschnitt.md) beschrieben.
- Schlecht: Der Beispielcode hinter den Links ist nicht Teil des Korpus; Fragen dürfen sich nicht nur auf ihn stützen.
