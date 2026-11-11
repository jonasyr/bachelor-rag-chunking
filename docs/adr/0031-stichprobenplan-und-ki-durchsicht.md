# 0031. Zufälliger Stichprobenplan und protokollierte KI-Durchsicht des Fragenkatalogs

## Status

Angenommen (14.10.2026; ergänzt [ADR 0029](0029-fragetypen-und-konstruktionsklassen.md); erweitert
[ADR 0030](0030-einfrieren-des-fragenkatalogs.md); Slotzahlen ersetzt durch [ADR 0039](0039-stichprobenplan-e2e.md);
ergänzt durch [ADR 0040](0040-closed-book-pruefung.md) (Closed-Book-Prüfung nach jedem Block) und
[ADR 0049](0049-schreibhilfen-im-editor.md) (Schreibhilfen, Zugriff über Tailscale)); Sprunggrund `content-elsewhere`
laut [Nachtrag 11.11.2026](#nachtrag-11112026-sprunggrund-content-elsewhere); Zahlen im Kontext:
Vue-Korpus `40aa88a` ([ADR 0025](0025-korpus-guide-api-styleguide.md)); aktuelle Werte in
[Korpus](../reference/corpus.md)

## Kontext

- Ohne Vorgabe wählt die verfassende Person Themen aus dem Gedächtnis; das bevorzugt bekannte Themen und kann
  Strategien begünstigen. Eine reproduzierbare Zufallsauswahl der Ausgangsabschnitte macht den Katalog zu einer
  Stichprobe der Dokumentation.
- 644 innerste H2/H3-Abschnitte (Guide 431, API 183, Style Guide 30), Median 190 Tokens, 30 unter 50 Tokens. Gleiche
  Gewichte je Abschnitt würden kleine Abschnitte überbetonen, an deren Grenzen C3-Chunks genau liegen.
- Python garantiert nur den Strom von `random()` über Versionen, NumPy keine festen `Generator`-Ströme; ein
  SHA-256-Hash ist überall gleich.
- Exposé („manuell kuratierter Fragenkatalog“), ADR 0017 (Eigenleistung) und die KI-Richtlinie der IU (KI ersetzt
  keine Datenerhebung, die menschlich zu leisten ist; Verantwortung bei den Studierenden; Offenlegung empfohlen)
  erlauben KI als Hilfsmittel, nicht als Autorin der Fragen.
- Pilotprobe: nachträglich ergänzte Abschnitte verschoben Recall@5 um bis zu 0,07; übersehene Abschnitte sind das
  größte gemessene Risiko der Annotation.

## Entscheidung

Wir werden je Slot einen Ausgangsabschnitt nach Textlänge ziehen: eine Tokenposition im Bereich über SHA-256 von
„{Seed}:{Bereich}:{k}“, gezogen wird der innerste H2/H3-Abschnitt an dieser Stelle, ohne Wiederholung. Seed
`20261014` (Tag der Entscheidung), 12 Slots API, 3 Style Guide, 33 Guide und ebenso viele Reserveabschnitte je Bereich;
die 48 Konstruktionsklassen werden mit demselben Seed gemischt und den Slots zugeordnet. Den Fragetyp wählt Jonas.
Wir werden den Plan einmal schreiben (`data/evaluation/catalogue_plan.csv`, versioniert) und nie überschreiben.
Wir werden einen Ausgangsabschnitt nur mit einem festen Grund überspringen (nur Code oder Links, unter 50 Tokens, gleiches
Thema wie ein früherer Slot, keine beantwortbaren Inhalte); den Slot übernimmt der nächste Reserveabschnitt desselben
Bereichs. Jeder Sprung wird protokolliert und in der Arbeit berichtet.
Wir werden nach jedem Block eine KI-Durchsicht (Claude) durchführen, die nur Fragen, Annotation und Korpustext liest
und Vorschläge (übersehene Abschnitte, Formulierung, Fakten, Klasse) als offene Zeilen in
`data/evaluation/catalogue_review.csv` schreibt; Jonas nimmt jeden Vorschlag an oder lehnt ihn mit Grund ab. Fragen,
Referenzantworten und Relevanzurteile schreibt nur Jonas.
Wir werden einfrieren nur, wenn kein Vorschlag offen ist; der Freeze-Datensatz enthält die Prüfsummen von Plan und
Durchsicht.
Wir werden bei jeder Prüfung den Plan mit einer frischen Ziehung vergleichen (die Ziehung ist deterministisch): Nur Status,
Sprunggrund, Frage-ID und die Übernahme von Reserveabschnitten in Ziehungsreihenfolge dürfen abweichen. „Unter 50 Tokens“
wird nur für Abschnitte unter `config.CATALOGUE_SKIP_MIN_TOKENS` angenommen.
Wir werden die handgeschriebenen Dateien atomar schreiben (temporäre Datei, dann Ersetzen) und Zeilen mit falscher
Feldzahl oder doppelter Frage-ID als Fehler ablehnen; der Editor läuft nur auf `localhost`.

## Konsequenzen

- Gut: Themen sind eine reproduzierbare Zufallsstichprobe; die Auswahl ist nachprüfbar und nicht von Vorlieben oder
  Pilotwissen geprägt.
- Gut: Die KI-Unterstützung ist vollständig protokolliert und für die KI-Offenlegung zählbar (Vorschläge, angenommen,
  abgelehnt je Art).
- Gut: Ein von Hand veränderter Plan (andere Abschnitte oder Klassen) fällt bei der Prüfung auf; der Freeze ist
  dann gesperrt.
- Neutral: Ein ungeeigneter Abschnitt kostet einen protokollierten Sprung; ist eine Reserve erschöpft, braucht eine
  größere Reserve ein neues ADR.
- Schlecht: Zufällige Abschnitte erfordern mehr Einarbeitung je Frage als frei gewählte Themen.

## Nachtrag 11.11.2026: Sprunggrund `content-elsewhere`

Von Jonas entschieden. Die vier festen Gründe decken einen Fall nicht ab, der in Block 2 auftrat: Der Abschnitt hat
beantwortbaren Inhalt, aber jede Aussage, die eine Frage nutzen könnte, steht auch in einem anderen Abschnitt. Nach der
Duplikatregel (jeder Abschnitt mit einem nötigen Teil der Antwort ist relevant) kann er dann weder `single` noch `detail`
oder `paraphrase` tragen. Anlass war `D054#what-can-still-leak` (Slot S15, `single`): Seine Lücken stehen in
`D051#where-redaction-stops`, `D051#site-check`, `D051#cache-trust`, `D051#artifacts`, `D051#redaction` und
`D041#recording`, seine Ratschläge in `D006#what-the-agent-does`, `D051#policy-denials` und
`D051#screenshots-after-a-secret-fill`; nur „Keep secrets out of your app's output“ steht allein dort.

Wir werden deshalb einen fünften festen Grund `content-elsewhere` zulassen („jeder Inhalt steht auch woanders“). Er gilt
nur, wenn die Durchsicht die anderen Abschnitte je Aussage in `catalogue_review.csv` nennt (Zeile der Art `class`) und
Jonas sie annimmt; „schwer zu schreiben“ bleibt kein Grund. Den Slot übernimmt wie bei jedem Sprung der nächste
Reserveabschnitt des Bereichs in Ziehungsreihenfolge, für S15 `D005#run-a-script-before-the-page`. Der Sprung wird
wie jeder andere in der Arbeit berichtet. Schlecht: Der Grund verlangt ein Urteil statt einer Zählung, wie
`duplicate-topic`; die Belegpflicht in der Durchsicht macht ihn nachprüfbar.
