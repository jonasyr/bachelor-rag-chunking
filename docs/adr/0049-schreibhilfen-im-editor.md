# 0049. Schreibhilfen im Katalog-Editor

## Status

Angenommen (29.10.2026; ergänzt [ADR 0031](0031-stichprobenplan-und-ki-durchsicht.md); Entwurf:
[Spec](../superpowers/specs/2026-10-29-catalogue-guidance-design.md))

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
