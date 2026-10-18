# 0019. Korpus-Ausschnitt: ganzes `src/guide/`, nur Composition API

## Status

Angenommen (13.10.2026); Ausschnitt und Commit ersetzt durch [ADR 0025](0025-korpus-guide-api-styleguide.md) (14.10.2026) und den Korpus Enroute ([ADR 0038](0038-korpus-enroute.md), 18.10.2026), übrige Regeln gelten weiter; Abschnitte um H1 ergänzt durch [ADR 0022](0022-h1-abschnitte-in-ground-truth.md); Sensitivitätsregel (Mindestüberlappung) geändert durch [ADR 0026](0026-c3-vergleichbarkeit.md) (ursprünglich: konkretisiert [ADR 0001](0001-korpus-vuejs.md), ersetzt den Vorschlag der vier Unterordner in [Korpus](../reference/corpus.md))

## Kontext

- [ADR 0001](0001-korpus-vuejs.md) legt Vue.js als Korpus fest, lässt aber Ausschnitt und Commit offen ([Plan](../plan.md)).
- Der bisherige Vorschlag (vier Unterordner `essentials`, `components`, `reusability`, `best-practices`) umfasst auf dem gewählten Commit nur 28 Dateien und verfehlt damit den selbst gesetzten Rahmen von 50–100 Dateien.
- `src/guide/` auf Commit `b75d188ab16bf83bd1f364a77dfd2315be8f3fa4` (31.07.2026) enthält 52 Markdown-Dateien in neun Bereichen.
- Die Seiten enthalten parallele `options-api`- und `composition-api`-Blöcke (172 bzw. 169). Beide Varianten beschreiben weitgehend denselben Inhalt und würden beim Retrieval als Beinahe-Duplikate konkurrieren.
- Alle H2/H3-Überschriften (514 im Rohtext, 282 H2 und 232 H3) tragen explizite VitePress-Anker (`{#…}`); damit lassen sich Abschnitte ohne eigene Slug-Erzeugung eindeutig benennen.
- Referenzquellen und Relevanzurteile müssen vor der Evaluation feststehen und mechanisch prüfbar sein ([ADR 0017](0017-fragenkatalog.md), [ADR 0012](0012-retrieval-metriken.md)).

## Entscheidung

Wir werden als Korpus alle Markdown-Dateien unter `src/guide/` aus `vuejs/docs` auf Commit `b75d188ab16bf83bd1f364a77dfd2315be8f3fa4` verwenden.
Wir werden nur Composition-API-Inhalte behalten und `options-api`-Blöcke beim Preprocessing entfernen.
Wir werden Abschnitte als `section_id = {doc_id}#{anchor}` aus den expliziten `{#…}`-Ankern der H2/H3-Überschriften benennen.
Wir werden einen Chunk als relevant werten, wenn seine Token-Spanne die Token-Spanne eines annotierten relevanten Abschnitts überlappt (jede Überlappung); als Sensitivitätsprüfung wiederholen wir die Retrieval-Auswertung mit einer Mindestüberlappung von 100 Tokens.
Wir werden Tokens mit `tiktoken` (Version 0.13.0) und der Kodierung `cl100k_base` zählen.
Alle Werte stehen in [`src/config.py`](../../src/config.py).

## Konsequenzen

- Gut: 52 Dateien liegen im angestrebten Rahmen; „ganzer Guide“ ist ohne Auswahlwillkür begründbar und reproduzierbar.
- Gut: Mehr Bereiche (u. a. `scaling-up`, `typescript`, `built-ins`) stützen die fünf Fragetypen, besonders vergleichende und Einschränkungs-/Fehlerfragen.
- Gut: Ohne Options-API-Duplikate bleiben Precision@k und MRR aussagekräftig.
- Gut: Anker und Überlappungsregel machen `relevant_section_ids` und `is_relevant` objektiv und automatisch berechenbar.
- Schlecht: Etwa doppelt so viele Tokens wie die vier Unterordner; mehr Chunks und Embedding-Kosten (absolut gering) sowie mehr Aufwand bei der Ground Truth.
- Schlecht: „Jede Überlappung“ ist großzügig und begünstigt C2 bei Precision@k; die Sensitivitätsprüfung macht diesen Effekt sichtbar und wird in der Arbeit diskutiert.
- Neutral: Das Entfernen der Options-API-Blöcke ist ein Eingriff in den Korpus und wird in der Methodik als Bereinigungsschritt dokumentiert.
- Neutral: Die exakte Token-Zahl nach dem Preprocessing steht im [Korpusmanifest](../corpus_manifest.csv) und im [Experiment-Protokoll](../reference/experiment-record.md); der Plan vom 13.08.2026 nannte rund 106k Tokens, eine grobe Vorabmessung ergab bis zu 150k (abhängig von der Bereinigung).
