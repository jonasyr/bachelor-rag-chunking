# 0038. Korpus: Enroute-Dokumentation statt Vue.js; Closed-Book-Prüfung und Kontrolle K0

## Status

Angenommen (18.10.2026; ersetzt [ADR 0025](0025-korpus-guide-api-styleguide.md) und den Vue-spezifischen Ausschnitt
von [ADR 0019](0019-korpus-ausschnitt.md); Umsetzung in eigenen Pull Requests, Stand in [plan.md](../plan.md#stand))

## Kontext

- Das Antwortmodell kennt Vue.js aus dem Training. Drei Befunde: Im Pilot `data/pilot/hard` erreichten fast alle
  Antworten die Höchstwerte, auch bei schwachem Retrieval ([ADR 0037](0037-praezisierte-pruefregeln-und-vorbefuellte-kernpunkte.md));
  ohne jedes Retrieval beantwortete das Modell 14 der 16 Pilotfragen vollständig; im Lückentext-Test fehlt ihm nur
  7,0 % des dokumentierten Vue-Wissens (95-%-KI 4,8–9,2 %). Antwortqualität misst so vor allem Modellwissen, nicht
  Retrieval, und ein Effekt des Chunkings kann kaum sichtbar werden.
- Die angemeldete Forschungsfrage nennt „technische Projektdokumentation“, kein bestimmtes Projekt; Vue.js stand nur
  im Exposé als Beispiel. Fragenkatalog und Ground Truth waren noch leer, gezogen war nur der Stichprobenplan.
- Kandidatensuche und Messung: [Korpusauswahl](../reference/corpus-selection.md). 24 Dokumentationen (Vue, Angular und
  22 nach dem Wissensstand des Modells veröffentlichte Projekte), 14.547 Lückentext-Proben. Kriterien und Gewichte
  wurden vor der Messung der neuen Kandidaten festgelegt ([`preregistration.md`](../../data/corpus_probe/preregistration.md)).
- Ergebnis: Wissenslücke Vue 7,0 %, Angular 12,8 % (vom Betreuer vorgeschlagen; gleiches Problem), alle neuen
  Projekte 20–50 %. Enroute (`enroute-sh/enroute`, Git auf Objektspeicher, Apache-2.0, erste Version v0.1.0 am 10.09.2026) hat
  die höchste Lücke (50,4 %, KI 42,1–58,6 %) und die höchste Gesamtwertung (81,2 von 100), liegt in 4 von 5
  Gewichtungen vorn und war in der qualitativen Durchsicht die sauberste Dokumentation (reines Markdown, Trennung
  Tutorial / How-to / Konzepte / Referenz / Interna, eigene Seite zu Grenzen). Zweiter in der Durchsicht: Strands Box
  (`strands-agents/box`).
- Zwei Korpora zu verbinden, um mehr Text zu haben, würde zwei Projekte mischen; Fragen und Retrieval wären nicht mehr
  über eine Dokumentation definiert.

## Entscheidung

Wir werden als Korpus den Ordner `docs/` aus `enroute-sh/enroute` auf Commit
`bc0dc6efce9cbbce9a5368e594a9b28f18a12d40` (14.10.2026, Release v0.3.0) verwenden; Bereiche, Ausschlüsse und Bereinigung legt der
Snapshot-Schritt fest, die übrigen Regeln von ADR 0019 (eine Fassung, alle Überschriften mit Ankern, Ausnahmen genau
eine Datei) gelten weiter. Strands Box bleibt Reserve, falls Enroute im ersten Katalogblock scheitert.

Wir werden jede Katalogfrage vor dem Einfrieren closed-book prüfen: Das Antwortmodell beantwortet sie ohne Kontext;
eine Frage, deren Kernpunkt es dabei richtig trifft, zählt als retrieval-unabhängig und wird markiert. Mindestens zwei
Drittel der Fragen müssen retrieval-abhängig sein. Wer den Kernpunkt beurteilt und wie das geprüft wird, legt der
Schritt Fragenkatalog fest.

Wir werden als Kontrolle K0 dieselben Fragen ohne Retrieval beantworten lassen und wie die Strategien bewerten; K0 ist
keine Chunking-Strategie und steht nicht in `config.STRATEGY_IDS`.

## Konsequenzen

- Gut: Antworten hängen vom Retrieval ab; ein Effekt des Chunkings kann sichtbar werden, und K0 zeigt, wie viel das
  Retrieval überhaupt beiträgt.
- Gut: Die Auswahl ist belegt und reproduzierbar (Skripte `scripts/corpus_probe/`, Daten `data/corpus_probe/`).
- Schlecht: Enroute ist klein (53 Seiten, rund 81.000 Tokens, rund 150–160 Chunks je Strategie); weniger Ablenker im
  Retrieval können absolute Werte heben. Der Vergleich der Strategien bleibt gültig, weil alle denselben Korpus
  nutzen; das steht in den Limitationen.
- Schlecht: Snapshot, Preprocessing, Chunking, Embeddings, K1 und Stichprobenplan werden neu gebaut; die Vue-Pilotdaten
  zählen nur noch als Entwicklungsgeschichte.
- Neutral: Das Repository veröffentlicht je Release einen einzigen Commit (v0.1.0, v0.2.0, v0.3.0) eines einzelnen
  Maintainers (258 Sterne, 9 Forks am 18.10.2026). Das macht den Snapshot stabil und eindeutig pinnbar, belegt aber
  wenig Nutzung; die Arbeit nennt das bei der Korpuswahl.
- Neutral: Der Lückentext-Test misst Einzelfakten, nicht ganze Fragen; die Closed-Book-Prüfung bestätigt das je Frage.
  Die Fehltreffer wurden von Agenten klassifiziert, nicht von einer Person.
- Neutral: Der Betreuer erfährt den Wechsel mit diesen Zahlen; Angulars Wert zeigt, warum ein bekanntes Framework
  keine Lösung ist.
