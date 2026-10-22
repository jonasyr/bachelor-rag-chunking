# 0029. Fragetypen, Konstruktionsklassen und Quoten des Fragenkatalogs

## Status

Angenommen (14.10.2026; präzisiert [ADR 0017](0017-fragenkatalog.md); ergänzt durch
[ADR 0031](0031-stichprobenplan-und-ki-durchsicht.md) (Stichprobenplan, KI-Durchsicht); Bereichsuntergrenzen ersetzt und
Stoppwörter angepasst (`e2e` statt `v` und `vue`) durch [ADR 0039](0039-stichprobenplan-e2e.md)); Zahlen im Kontext:
Vue-Korpus `40aa88a` ([ADR 0025](0025-korpus-guide-api-styleguide.md)); aktuelle Werte in
[Korpus](../reference/corpus.md). Korrektur zum Kontext: das Verhältnis 2:2:2:1:1 der Fragetypen steht nicht in ADR
0017, sondern in der Tabelle von Leitfaden §11 (10/10/10/5/5)

## Kontext

- ADR 0017 legt etwa 40 Fragen (30–60) in fünf Typen im Verhältnis 2:2:2:1:1 fest; das Exposé nennt „etwa 40 Fragen“.
  H3 ([ADR 0009](0009-hypothesen.md)) braucht neben dem Typ die Unterscheidung abschnittsübergreifender Fragen.
- Pilotprobe 2 ([Experiment-Protokoll](../reference/experiment-record-vue.md#pilotproben-auf-dem-erweiterten-korpus-14102026)):
  Einfache Fragen erreichen bei allen Strategien Hit@5 = 1,0 (Deckeneffekt); die Konstruktion der Frage
  (mehrere Abschnitte, Detail, Paraphrase) trennt C3 und K1.
- Eine subjektive Schwierigkeit (leicht/mittel/schwer) ist nicht prüfbar; eine Konstruktionsklasse lässt sich gegen die
  eigene Annotation prüfen, ohne Retrieval-Ergebnisse ([ADR 0027](0027-blinde-annotation.md)).
- Messungen auf dem Korpus nach [ADR 0025](0025-korpus-guide-api-styleguide.md): H2/H3-Abschnitte Median 211 Tokens
  (p25 120, p75 356); die relevanten Abschnitte der Pilot-Detailfragen sind 22–546 Tokens lang, „Detail“ ist also eine
  Eigenschaft der Antwort, nicht der Abschnittslänge.
- Ein Wortvergleich nur über Pluralendungen übersieht Ableitungen (`watch`/`Watchers`, `mounted`/`Mounting`,
  `reactive`/`Reactivity`); eine solche Frage wäre keine Paraphrase (Review zu Aufgabe 3, 14.10.2026). Mit dem
  Präfixvergleich unten würden 5 der 7 Pilot-Paraphrasen die Regel verletzen.
- Korpusanteile (ADR 0025): Guide 71 %, API 26 %, Style Guide 3 % der Tokens.
- Umfang: Der Standardfehler eines Mittelwerts sinkt mit √n. 48 statt 40 Fragen senken ihn um etwa 9 %; mit 12 Fragen
  je Klasse sind bei gepaartem Vergleich (gepaarter t-Test, 80 % Power, zweiseitig α = 0,05) nur große Effekte
  (d ≈ 0,89) erkennbar, über alle 48 Fragen d ≈ 0,41 (bei 40: 0,45). Mehraufwand gegenüber 40: etwa 8 Stunden
  Fragen und Annotation, 24 Antworten mehr zu bewerten.

## Entscheidung

Wir werden 48 Fragen erstellen: `type` ∈ {`factual`, `procedural`, `conceptual`, `comparative`, `limitation`} mit
12/12/12/6/6 Fragen und `difficulty` als Konstruktionsklasse ∈ {`single`, `multi-section`, `detail`, `paraphrase`}
mit je 12 Fragen.
Wir werden die Klassen so definieren: `single` genau ein relevanter Abschnitt, dessen Hauptinhalt die Antwort ist;
`multi-section` mindestens zwei relevante Abschnitte, die alle nötig sind (ein Abschnitt innerhalb eines anderen
angegebenen zählt nicht mit, er fügt keinen Text hinzu); `detail` genau ein Abschnitt, die Antwort
ist ein einzelnes Faktum (Referenzantwort höchstens 30 Wörter); `paraphrase` genau ein Abschnitt, die Frage teilt kein
Inhaltswort mit dem Titel des Abschnitts oder dem Titel seiner Seite (H1).
Wir werden Wörter so vergleichen: Kleinschreibung, Wörter `[a-z0-9]+`, ohne Stoppwörter (`config.CATALOGUE_STOPWORDS`);
camelCase-Bezeichner zählen zusätzlich mit ihren Teilen (`defineProps` → `define`, `props`). Zwei Wörter gelten als
gleich, wenn sich ihre Pluralformen überschneiden (Wörter ab vier Zeichen auch ohne `s`/`es` und mit `ies` → `y`) oder
wenn sie einen gemeinsamen Anfang von mindestens max(4, Länge des kürzeren Wortes − 3) Zeichen haben. Die Regel meldet
im Zweifel eine Überlappung.
Wir werden mindestens 12 Fragen mit einem relevanten Abschnitt in der API-Referenz und mindestens 3 im Style Guide
verlangen; eine Frage zählt für jeden Bereich, den sie berührt.
Werte und Grenzen stehen in [`src/config.py`](../../src/config.py); `src/catalogue.py check` prüft sie.

## Konsequenzen

- Gut: H3 lässt sich nach Typ und nach Konstruktion auswerten; die Klassen stehen vor jedem Retrieval fest und werden
  maschinell geprüft.
- Gut: Der Deckeneffekt einfacher Fragen bleibt sichtbar (`single` als Referenzgruppe), statt den Katalog zu prägen.
- Neutral: 48 statt „etwa 40“ Fragen; die Arbeit nennt die Abweichung vom Exposé und ihren Grund.
- Schlecht: Je Klasse sind nur große Effekte erkennbar; Ergebnisse je Klasse bleiben explorativ (ADR 0009).
- Schlecht: Der Wortvergleich ist bewusst grob und meldet eher zu viel (z. B. `server`/`service`); Paraphrasen
  brauchen dadurch mehr Umformulierung. Ob ein Detail nur einen kleinen Teil des Abschnitts ausmacht, bleibt ein
  Urteil; die Prüfung zeigt Abschnitts- und Antwortlänge an.
