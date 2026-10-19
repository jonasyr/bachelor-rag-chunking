# 0038. Korpus: e2e-Dokumentation statt Vue.js; Closed-Book-Prüfung und Kontrolle K0

## Status

Angenommen (18.10.2026; ersetzt [ADR 0025](0025-korpus-guide-api-styleguide.md) und den Vue-spezifischen Ausschnitt
von [ADR 0019](0019-korpus-ausschnitt.md); Umsetzung in eigenen Pull Requests, Stand in [plan.md](../plan.md#stand); wer den Kernpunkt beurteilt:
[ADR 0040](0040-closed-book-pruefung.md))

## Kontext

- Das Antwortmodell kennt Vue.js aus dem Training. Im Pilot `data/pilot/hard` erreichten fast alle Antworten die
  Höchstwerte, auch bei schwachem Retrieval ([ADR 0037](0037-praezisierte-pruefregeln-und-vorbefuellte-kernpunkte.md));
  ohne Retrieval beantwortete das Modell 14 der 16 Pilotfragen vollständig. Antwortqualität misst so vor allem
  Modellwissen, nicht Retrieval, und ein Effekt des Chunkings kann kaum sichtbar werden.
- Die angemeldete Forschungsfrage nennt „technische Projektdokumentation“, kein bestimmtes Projekt; Vue.js stand nur
  im Exposé als Beispiel. Fragenkatalog und Ground Truth waren noch leer, gezogen war nur der Stichprobenplan.
- Messung ([Korpusauswahl](../reference/corpus-selection.md)), Kriterien und Gewichte vorab festgelegt
  ([`preregistration.md`](../../data/corpus_probe/preregistration.md)):
  - Lückentext-Probe über 24 Dokumentationen (14.547 Proben): Wissenslücke Vue 7,0 %, Angular 12,8 % (vom Betreuer
    vorgeschlagen), alle 22 nach dem Wissensstand des Modells veröffentlichten Projekte 20–50 %.
  - Closed-Book-Prüfung auf Fragenebene (je 20 realistische Fragen, blind beurteilt): ohne Dokumentation richtig
    beantwortet Vue 15/20, Angular 10/20, xy 3/20, e2e 1/20, TanStack Charts 1/20, Enroute 0/20; mit dem Abschnitt
    118 von 120 richtig.
- Kandidaten der Spitzengruppe: Enroute (höchste Wertung 81,2, Lücke 50,4 %, sauberstes Markdown, aber 81.000 Tokens,
  ein Maintainer, drei Commits) und e2e (`tester-army/e2e`, KI-gestützter End-to-End-Testläufer, Apache-2.0, angelegt
  22.07.2026; Wertung 67,5, Lücke 36,5 %, KI 29,8–43,1 %; 11.100 Sterne, 56 Mitwirkende). Qualitative Durchsicht e2e
  3/3/4/4/2 (Qualität, Passung, Chunking, Fragenpotenzial, Aufbereitung): klare Trennung Anleitung / Referenz, mehrere
  „Limits“-Abschnitte und Fehlercode-Katalog, dichte Querverweise; Aufwand durch Mintlify-MDX.
- Vorgabe: möglichst viel Inhalt in der Wissensbasis. e2e hat rund 228.000 Tokens auf 61 Seiten (Enroute rund 81.000,
  der Vue-Korpus 166.000); mehr Ablenker machen das Retrieval realistischer.
- Vergleich (vollständig mit allen 24 Kandidaten, Durchsicht und Entscheidungsweg:
  [Korpusauswahl](../reference/corpus-selection.md#ergebnis)):

  | | Vue.js | Angular | e2e | Enroute | TanStack Charts | xy |
  |---|---|---|---|---|---|---|
  | Wissenslücke (Lückentext) | 7,0 % | 12,8 % | 36,5 % | 50,4 % | 29,7 % | 31,7 % |
  | Closed-Book ohne Doku richtig | 15/20 | 10/20 | 1/20 | 0/20 | 1/20 | 3/20 |
  | Tokens (≈) | 177.951 | 508.000 | 228.266 | 81.395 | 219.823 | 159.453 |
  | Sterne / Mitwirkende | bekannt | bekannt | 11.109 / 56 | 258 / 1 | 842 / 10 | 1.879 / 17 |
  | Wertung (0–100) | – | – | 67,5 | 81,2 | 66,2 | 73,8 |
  | Qualitativ (0–4 ×5) | – | – | 3/3/4/4/2 | 4/4/4/3/4 | 3/2/3/3/4 | 3/3/2/2/1 |

- Zwei Korpora zu verbinden, um mehr Text zu haben, würde zwei Projekte mischen; Fragen und Retrieval wären nicht mehr
  über eine Dokumentation definiert.

## Entscheidung

Wir werden als Korpus den Ordner `docs/` aus `tester-army/e2e` auf Commit `ef977f4856da009cac26d78d2e9bb14e5991ee41`
(17.10.2026, gemessener Stand) verwenden. Bereiche, Ausschlüsse und Bereinigung legt der Snapshot-Schritt fest; die
Bereinigung wandelt MDX-Komponenten in Markdown um, statt Inhalt zu verwerfen (Hinweise, Akkordeons, Tabs und Schritte
behalten ihren Text, Code-Gruppen alle Varianten, Datenkomponenten werden zu Tabellen); nur Navigation, Videos und
Einrichtungs-Prompts für Coding-Agenten entfallen. Die übrigen Regeln von ADR 0019 (eine Fassung, alle Überschriften
mit Ankern, Ausnahmen genau eine Datei) gelten weiter. Enroute bleibt Reserve, falls e2e im ersten Katalogblock
scheitert.

Wir werden jede Katalogfrage vor dem Einfrieren closed-book prüfen: Das Antwortmodell beantwortet sie ohne Kontext;
eine Frage, deren Kernpunkt es dabei richtig trifft, zählt als retrieval-unabhängig und wird markiert. Mindestens zwei
Drittel der Fragen müssen retrieval-abhängig sein. Wer den Kernpunkt beurteilt und wie das geprüft wird, legt der
Schritt Fragenkatalog fest.

Wir werden als Kontrolle K0 dieselben Fragen ohne Retrieval beantworten lassen und wie die Strategien bewerten; K0 ist
keine Chunking-Strategie und steht nicht in `config.STRATEGY_IDS`.

## Konsequenzen

- Gut: Antworten hängen vom Retrieval ab (95 % der Diagnosefragen); ein Effekt des Chunkings kann sichtbar werden, und
  K0 zeigt, wie viel das Retrieval überhaupt beiträgt.
- Gut: großer, real genutzter Korpus; breite Verteilung der Abschnittslängen (Median 94 Wörter, 14 Abschnitte über
  800) trennt die Strategien.
- Gut: Die Auswahl ist belegt und reproduzierbar (Skripte `scripts/corpus_probe/`, Daten `data/corpus_probe/`).
- Schlecht: MDX-Bereinigung mit getesteten Regeln (rund ein Tag); die Dokumentation ändert sich täglich, der Snapshot
  bleibt fest. Referenzseiten sind sehr lang (bis rund 13.000 Wörter).
- Schlecht: Snapshot, Preprocessing, Chunking, Embeddings, K1 und Stichprobenplan werden neu gebaut; die Vue-Pilotdaten
  zählen nur noch als Entwicklungsgeschichte.
- Neutral: Das Fachgebiet (Testen mit Sprachmodell-Agenten) ist dem Modell vertraut; die Closed-Book-Prüfung zeigt,
  dass es die Dokumentation trotzdem nicht kennt (1/20, meist „weiß ich nicht“).
- Neutral: Lückentext-Probe, Fragen und Urteile der Diagnose stammen von Agenten, nicht von einer Person; 20 Fragen je
  Korpus geben breite Intervalle. Die Closed-Book-Prüfung jeder Katalogfrage bestätigt das Ergebnis.
- Neutral: Der Betreuer erfährt den Wechsel mit diesen Zahlen; Angular (10/20 ohne Dokumentation richtig) zeigt, warum
  ein bekanntes Framework keine Lösung ist.
