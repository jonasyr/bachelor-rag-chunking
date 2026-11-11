# 0049. Schreibhilfen im Katalog-Editor

## Status

Angenommen (29.10.2026; ergänzt [ADR 0031](0031-stichprobenplan-und-ki-durchsicht.md); Entwurf:
[Spec](../superpowers/specs/2026-10-29-catalogue-guidance-design.md)); Vorbereitungsblätter für alle Blöcke laut
[Nachtrag 09.11.2026](#nachtrag-09112026-vorbereitungsblätter-für-jeden-block); Typ-Eignung im Blatt laut
[Nachtrag 10.11.2026](#nachtrag-10112026-typ-eignung-im-vorbereitungsblatt)

## Kontext

- Die Ausgangsabschnitte sind zufällig gezogen (ADR 0031); Jonas kennt die e2e-Doku nicht und muss für jede Frage
  wissen, wo derselbe Inhalt noch steht. Viele Inhalte stehen mehrfach im Korpus (z. B. die Anbieter-Tabelle in
  `D036#ai-sdk-providers` und `D037#use-a-subscription-or-api-key`).
- Übersehene relevante Abschnitte sind das größte gemessene Risiko der Annotation (Pilot: Recall@5 bis 0,07, ADR 0031).
  Die KI-Durchsicht nach jedem Block findet sie erst nach dem Schreiben.
- KI darf Hilfsmittel sein, nicht Autorin der Fragen (Exposé „manuell kuratiert“, ADR 0017, KI-Richtlinie der IU).
  Ein gerankter Vorschlag relevanter Abschnitte wäre ein Retrieval-Verfahren vor der Annotation (ADR 0027).
- Der Editor soll auch vom Handy erreichbar sein; ADR 0031 bindet ihn an `localhost`.

## Entscheidung

Wir werden dem Editor fünf Hilfen geben, die weder Frage noch Antwort, Typ oder Relevanzurteil festlegen:

1. **Wörtliche Doppelungen**: Der Editor zeigt mechanisch alle Abschnitte, deren eigener Text mit dem Ausgangsabschnitt
   eine Wortfolge von mindestens `config.CATALOGUE_DUPLICATE_MIN_WORDS` Wörtern teilt; Folgen in mehr als
   `config.CATALOGUE_DUPLICATE_MAX_SECTIONS` Abschnitten gelten als Vorlage (Config-Codeblock, Linktext), ebenso
   Folgen ganz in TypeScript-/JavaScript-Beispielblöcken (`config.CATALOGUE_DUPLICATE_SKIP_FENCES`); Shell-Befehle
   zählen weiter.
2. **Inhaltliche Überschneidungen**: Claude erstellt einmal für alle Plan- und Reserveabschnitte
   `data/evaluation/catalogue_overlap.csv` durch Lesen und Suchen im Korpus (nicht über Chunks oder Retrieval), je
   Zeile mit einer neutralen Notiz, was beide Abschnitte gemeinsam haben, nie eine Frageidee. Die Liste hängt nur am
   Abschnitt, wird versioniert, von `catalogue.py check` geprüft (Format, bekannte IDs) und beim Einfrieren mitgehasht.
3. **Leitfragen je Klasse** (`config.CATALOGUE_CLASS_GUIDE`), für jeden Abschnitt gleich.
4. **Typvorschlag** aus dem Wortlaut der fertigen Frage nach festen Regeln (`config.QUESTION_TYPE_HINTS`); der Typ
   startet leer und wird erst durch Jonas' Klick gesetzt. Speichern ist gesperrt, solange eine Prüfung nicht erfüllt
   oder die Quote des Typs voll ist.
5. **Vorbereitungsblatt** für Block 1 (`data/evaluation/catalogue_prep_block1.md`, Vorläufer von 1 und 2), versioniert
   mit Block 1.

Jeder Treffer aus 1 und 2 übernimmt Jonas nur per Klick in die Annotation. Die KI-Durchsicht nach jedem Block bleibt.

Wir werden den Editor zusätzlich über Tailscale Serve im eigenen Tailnet erreichbar machen (nur Geräte von Jonas, kein
Funnel); der Editor selbst bindet weiter an `localhost`. Das ersetzt den Satz „der Editor läuft nur auf `localhost`“
aus ADR 0031 in diesem Sinn.

## Konsequenzen

- Gut: Doppelungen und Überschneidungen sind sichtbar, bevor eine Frage gespeichert wird; die größte Fehlerquelle der
  Annotation wird zweifach (mechanisch und durch Lesen) abgedeckt.
- Gut: Alle KI-Hilfen sind Dateien im Repo; die KI-Offenlegung kann sie zählen (Zeilen der Überschneidungsliste,
  übernommene Abschnitte).
- Neutral: Eine Doppelung in mehr als acht Abschnitten fehlt im mechanischen Teil; die Überschneidungsliste deckt
  Inhalte ab, nicht Vorlagen.
- Schlecht: Die Überschneidungsliste ist eine KI-Vorauswahl; sie kann Abschnitte übersehen. Die Suche im Editor und die
  Durchsicht nach jedem Block bleiben deshalb Pflicht.

## Nachtrag 09.11.2026: Vorbereitungsblätter für jeden Block

Von Jonas entschieden. Punkt 5 gilt nicht nur für Block 1: Claude legt vor jedem Block ein Vorbereitungsblatt
`data/evaluation/catalogue_prep_block<N>.md` an, versioniert mit dem Block. Es entsteht mechanisch: je Satz des
Ausgangsabschnitts (ohne Codeblöcke), ob eine Folge von fünf Wörtern auch im eigenen Text eines anderen Abschnitts steht
(ohne umschließende und enthaltene Abschnitte), für Begriffe in Backticks die anderen Abschnitte mit diesem Begriff
(gelistet bis zehn Treffer), dazu die Zeilen aus `catalogue_overlap.csv` und die Klassenregel. Es enthält keine Frage,
keine Antwort, keinen Typ und kein Relevanzurteil. „ONLY HERE“ bedeutet nur „kein wörtlicher Treffer“; anders
formulierte Stellen mit gleichem Inhalt deckt die Überschneidungsliste ab, die Suche im Editor und die Durchsicht nach
jedem Block bleiben Pflicht. Anlass: In Block 1 brachen mehrere Fragen die Klassenregel erst in der Durchsicht, weil
Teile der Antwort wörtlich in weiteren Abschnitten standen.

## Nachtrag 10.11.2026: Typ-Eignung im Vorbereitungsblatt

Von Jonas entschieden. Nach 16 Fragen fehlen vor allem `conceptual`-Fragen (1 von 12), und die Ausgangsabschnitte
sind gezogen, nicht wählbar (ADR 0031). Ab Block 3 nennt das Vorbereitungsblatt deshalb je Slot die Fragetypen, die der
Text des Abschnitts trägt, jeweils mit der Stelle, auf die sich der Typ stützt, und ob sie nur dort steht (sonst bricht
die Klassenregel), sowie die Typen, die an der Klasse scheitern (z. B. `comparative` unter `paraphrase`, wenn der
zweite Gegenstand ein Wort des Seitentitels ist). Das ersetzt für die Typ-Eignung den Satz „Es enthält … keinen Typ“
des Nachtrags vom 09.11.2026; Frage, Antwort und Relevanzurteil bleiben ausgeschlossen, und den Typ wählt weiter Jonas
im Editor. Die Typziele je Block stehen im [Plan](../plan.md#zeitplan). Tabellenzeilen zählen im mechanischen Teil ab
Block 3 je als ein Satz. Schlecht: Der Vorschlag lenkt die Fragen stärker als die bisherigen Hilfen; er wird wie die
übrigen Hilfen offengelegt.
