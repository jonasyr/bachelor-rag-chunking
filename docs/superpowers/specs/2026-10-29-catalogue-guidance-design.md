# Entwurf: Schreibhilfen im Katalog-Editor (29.10.2026)

## Absicht

Jonas sitzt im Editor vor einem zufällig gezogenen Abschnitt einer Doku, die er nicht kennt, und weiß nicht, wo er
anfangen soll, welcher Typ passt und ob derselbe Inhalt noch anderswo steht. Die größte gemessene Gefahr der
Annotation sind übersehene relevante Abschnitte (ADR 0031, Pilot: Recall@5 bis 0,07). Ziel: Er liest, schreibt Frage
und Antwort, und alles andere nimmt ihm der Editor ab, ohne dass eine KI Frage, Antwort, Typ oder Relevanzurteil
festlegt.

## Ziele

- Pro Slot sieht Jonas, ohne zu suchen, welche anderen Abschnitte denselben Text oder Inhalt haben, und übernimmt sie
  mit einem Klick.
- Leitfragen je Konstruktionsklasse helfen gegen das leere Blatt.
- Der Typ ist nicht vorbelegt; der Editor leitet einen Vorschlag regelbasiert aus der geschriebenen Frage ab und zeigt
  die offenen Quoten.
- Speichern ist erst möglich, wenn Typ gewählt und alle Prüfungen erfüllt sind.
- Auf Laptop, Desktop und Handy (Tailscale) ein ruhiger, klarer Ablauf ohne Reibung; jeder Platz genutzt.

## Nicht-Ziele und Anti-Ziele

- Keine von einer KI geschriebenen Fragen, Antworten oder inhaltlichen Hinweise zum Abschnitt (ADR 0031).
- Kein gerankter, semantischer oder Embedding-basierter Vorschlag relevanter Abschnitte im Editor: das wäre ein
  Retrieval-Verfahren vor der Annotation (ADR 0027).
- Kein API-Aufruf im Editor (wie bisher, ADR 0040).
- Anti-Ziel: Eine Hilfe, die je nach Frage andere Inhalte anbietet und damit die Frage lenkt. Alle Hilfen hängen am
  Abschnitt oder an der Klasse, nur der Typvorschlag an der fertigen Frage.

## Bausteine

### 1. Wörtliche Doppelungen (mechanisch, live)

`catalogue.py` erhält eine Funktion, die für einen Abschnitt alle anderen Abschnitte liefert, deren eigener Text (ohne
Unterabschnitte, wie bei `find`) eine Wortfolge von mindestens `config.CATALOGUE_DUPLICATE_MIN_WORDS` Wörtern mit ihm
teilt (Wörter normalisiert: Kleinschreibung, `[a-z0-9]+`), je Treffer mit einem Ausschnitt der längsten geteilten
Stelle. Vorfahren und Nachkommen des Abschnitts zählen nicht (ein umschließender Abschnitt fügt keinen Text hinzu,
ADR 0029). Deterministisch, ohne Modell, zwischengespeichert pro Korpus.

### 2. Inhaltliche Überschneidungen (KI, vorab, versioniert)

Neue Datei `data/evaluation/catalogue_overlap.csv`: `section_id, related_section_id, note`. Claude erstellt sie einmal
für alle Abschnitte des Plans (Slots und Reserve), indem es den Korpus liest und sucht (nicht über Chunks oder
Retrieval). `note` sagt in einem kurzen Satz, was beide Abschnitte gemeinsam haben, nicht, wonach man fragen soll.
Die Liste hängt nur am Abschnitt. Sie wird wie die Durchsicht offengelegt und mit dem Freeze gehasht. Zeilen, die schon
als wörtliche Doppelung erscheinen, dürfen fehlen.

### 3. Kasten „Also covered elsewhere“

Zeigt die Treffer aus 1 und 2 zusammen, pro Abschnitt: Überschriftenpfad, Herkunft (`same text` / `related`), die
geteilte Stelle oder `note`, ausklappbarer Abschnittstext, Knopf „Add“. Bereits hinzugefügte sind markiert. Leer:
„No other section shares text with this one“ plus Hinweis auf die Suche. Darunter die Regel in einem Satz: jeder
Abschnitt, der einen nötigen Teil der Antwort enthält, ist relevant.

### 4. Leitfragen je Klasse

`config.CATALOGUE_CLASS_GUIDE`: pro Klasse die Regel in einem Satz und 2–3 inhaltsfreie Leitfragen (Englisch, wie
die App). Angezeigt oben im Formular, einklappbar, standardmäßig offen.

### 5. Typ ohne Vorgabe, Vorschlag aus der Frage

Typauswahl startet leer („Choose a type“). Regeln in `config.QUESTION_TYPE_HINTS` (Anfang der Frage → Typ, z. B.
„how do i“/„how can i“ → `procedural`, „what is the difference“/„… vs …“ → `comparative`, „why“ → `conceptual`,
„can't/cannot/limit/not support“ → `limitation`, „what/which“ → `factual`; erste passende Regel gewinnt). Unter der
Auswahl: „Looks like procedural (‘How do I’)“ mit Knopf, und je Typ die noch offenen Plätze der Quote. Jonas
bestätigt oder wählt anders; nichts wird ohne Klick gesetzt.

### 6. Speichern nur, wenn alles erfüllt ist

Der Knopf ist gesperrt, solange Frage, Antwort oder Typ fehlen oder eine Prüfung „Not met“ ist; der Grund steht
direkt am Knopf. `catalogue_store` validiert weiterhin selbst.

### 7. Layout und Ablauf

Desktop/Laptop (zwei Spalten): links Abschnitt (füllt die Höhe, scrollt innen), darunter „Also covered elsewhere“ und
die Suche; rechts von oben nach unten Klasse und Leitfragen, Frage, Typ, Antwort, Notizen, relevante Abschnitte,
Prüfungen, Speichern, Überspringen. Handy (unter 640 px): eine Spalte in Arbeitsreihenfolge: Klasse und Leitfragen,
Abschnitt (begrenzte Höhe), Also covered elsewhere, Formular, Suche. Touch-Ziele ≥ 44 px, kein horizontales Scrollen
der Seite. Geprüft mit Playwright bei 320, 768 und 1280 px, dazu Impeccable `audit` und `polish`.

## Methodische Absicherung

Neues ADR 0049 (ergänzt 0031): Vorbereitungsliste, Leitfragen, regelbasierter Typvorschlag, Doppelungsanzeige,
Zugriff über Tailscale (nur Tailnet; der Editor bindet weiter an `localhost`). Jede KI-Hilfe ist eine Datei im Repo
und wird in der KI-Offenlegung gezählt. `data/evaluation/catalogue_prep_block1.md` (Vorgänger dieser Liste) wird mit
Block 1 versioniert.

## Festlegungen nach der Bauprüfung (Claudes Entscheidungen)

- **Speichern gesperrt**, wenn Frage, Antwort oder Typ fehlen, eine Prüfung „Not met“ ist oder die Quote des gewählten
  Typs voll ist (die bearbeitete Frage selbst zählt nicht mit). Der erste Grund steht am Knopf.
- **Doppelungen** werden nur für den Ausgangsabschnitt des Slots berechnet, gegen alle Abschnitte des Korpus, bei
  Bedarf und zwischengespeichert je Korpus (`st.cache_resource`). Vorfahren und Nachkommen des Ausgangsabschnitts
  fallen weg. Treffer, die schon in der Liste stehen oder in einem gelisteten Abschnitt liegen bzw. ihn enthalten,
  werden markiert, nicht versteckt. Höchstens 10 sichtbar, der Rest hinter „Show all“. Schwelle 8 Wörter.
- **`catalogue_overlap.csv`** gilt gerichtet (nur für `section_id`, keine Spiegelung). Fehlt die Datei, zeigt der
  Kasten nur die wörtlichen Doppelungen; liegt sie vor, wird sie beim Freeze mitgehasht. Unbekannte Abschnitts-IDs
  sperren den Editor wie bisher (`unknown_sections`). Eine vollständige Abdeckung des Plans wird nicht geprüft. Die
  echte Datei erstellt Claude im selben PR als eigene Aufgabe.
- **Typregeln**: Kleinschreibung, typografische Apostrophe vereinheitlicht; geordnete reguläre Ausdrücke, irgendwo in
  der Frage: zuerst `comparative` (difference, versus, vs, compared, instead of), dann `limitation` (can't, cannot,
  not support, limit, fail, unsupported), dann `procedural` (how do/can/should i, how to), dann `conceptual` (why,
  purpose, when should), zuletzt `factual` (beginnt mit what/which/where/when/who/does/is/are). Kein Treffer: kein
  Vorschlag. Der Knopf nennt die gefundene Wendung.
- **Gespeicherte Fragen** zeigen ihren gespeicherten Typ; nur neue starten leer.
- **Umfang**: Umbau in `app/catalogue_page.py` (Hilfsfunktionen dürfen in ein neues Modul), CSS über `ui_theme.py`.
  Tailscale ist nur ADR-Text.

## Dem Bauenden überlassen

Schwellenwert der Wortfolge (Vorschlag 8), genaue Ausschnittlänge, Formulierung der Leitfragen und Hinweise, Wahl der
Streamlit-Elemente, CSS. Tests mit `AppTest` wie bisher; der Editor bleibt ohne Netz und API.
