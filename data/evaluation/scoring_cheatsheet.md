# Spickzettel Bewertung (Hauptlauf)

KI-Hilfe (Claude), erstellt am 17.11.2026. Das Blatt fasst nur die geltenden Regeln zusammen:
[Evaluation](../../docs/reference/evaluation.md#regelbasierte-bewertung), ADR 0035, 0037, 0041, 0043, Regelversion
`2026-10-20` (`config.RUBRIC_RULES_VERSION`); Umfang nach ADR 0051 (hybride Bewertung, 26.11.2026). Es enthält keine Frage, keine Antwort und keinen Kernpunkt und führt
keine neue Regel ein; bei einem Widerspruch gilt die Evaluation-Seite. Jede bewertende Person bekommt dasselbe Blatt.

## Ablauf in der App

1. `uv run streamlit run app/catalogue_editor.py --server.address localhost`, Seite „Scoring“.
2. Set „Main catalogue“ (C1–C3, blind). K0 bewertet nur das Sprachmodell (ADR 0051).
3. Schritt „Key points“: 48 Fragen, dann einfrieren. Schritt „Score“: die App bietet nur die 72 Antworten deiner 24
   Fragen an (siehe unten); die Excerpts stehen untereinander, die Prüffragen bleiben beim Scrollen sichtbar.
4. Pausieren ist jederzeit möglich; gespeichert ist, was mit „Save and next“ bestätigt wurde.

## Teil 1: Kernpunkte (einmal je Frage, vor dem Bewerten)

Sichtbar sind nur Frage und Referenzantwort. Bis zu 4 Felder, aus der Referenz vorbefüllt.

- **Core point (Punkt 1)** = die direkte Antwort auf die Frage.
- **Weiter teilen**, wo eine Antwort einen Teil richtig und den anderen falsch oder gar nicht haben kann.
- **Ein Nebensatz, der zählen soll**, wird ein eigener Punkt; sonst muss er nicht in der Antwort stehen.
- **Eine Einschränkung in Klammern** (z. B. eine Versionsangabe) braucht keinen eigenen Punkt; sie muss später
  nicht in der Antwort stehen.
- **Nur aus der Referenzantwort**: nichts hinzufügen, was dort nicht steht.
- **Lückenlos von oben**: Punkt 1 zuerst, kein leeres Feld zwischen zwei Punkten. Höchstens 4 Punkte; was darüber
  hinausgeht, bleibt im letzten Punkt.
- **Einfrieren** erst, wenn alle 48 gespeichert und noch einmal durchgesehen sind. Danach unveränderlich, auch für
  K0 und die Zweitbewertung.

Was die Zahl der Punkte bewirkt (Vollständigkeit 1 ab der Hälfte enthaltener Punkte):

| Punkte | Vollständigkeit 2 | 1 | 0 |
|---|---|---|---|
| 1 | 1 enthalten | – | 0 |
| 2 | 2 | 1 | 0 |
| 3 | 3 | 2 | 0–1 |
| 4 | 4 | 2–3 | 0–1 |

## Teil 2: Bewerten (je Antwort)

Sichtbar: Frage, Referenz, die Antwort und die fünf Passagen, die das Modell gesehen hat (Reiter 1–5). Strategie
und Chunk-IDs sind verborgen; die drei Antworten einer Frage stehen unter neutralen Codes in gemischter Reihenfolge.

Reihenfolge im Formular:

### `declines`: „Does the answer say the excerpts do not contain the answer, and give none?“

- `yes` nur, wenn die Antwort ablehnt **und keine** Antwort gibt.
- **Teilantwort** mit dem Hinweis, der Rest stehe nicht in den Passagen: `no`; die fehlenden Teile sind fehlende
  Kernpunkte (ADR 0043).
- Bei `yes` fallen Kernpunkte, `core_wrong`, `other_error`, `grounded` und `hallucination` weg. Ergebnis fest:
  Korrektheit 1, Vollständigkeit 0, Quellenbezug 2, Halluzinationsfreiheit 2; Verständlichkeit nach ihren drei
  Fragen.

### Kernpunkte: `covered` / `missing`

- `covered`: dieselbe Bedeutung steht in der Antwort, auch in anderen Worten.
- **Nur teilweise = `missing`.**
- Die Klammer-Einschränkung muss nicht enthalten sein.
- Gemessen wird gegen den Kernpunkt, nicht gegen die Passagen.

### Facts

**`core_wrong`: „Does it state the core point wrongly or contradict it?“**
Kernaussage falsch wiedergegeben oder widersprochen: `yes` → Korrektheit 0 (geht allem anderen vor).

**`other_error`: „Is any other statement factually wrong?“**
Irgendeine andere Aussage sachlich falsch: `yes` → Korrektheit 1.

### Sources

**`grounded`: „How many of its statements are backed by the excerpts?“** – `all` / `some` / `none`
- Maßstab sind **nur die fünf Passagen**, nicht die Referenz und nicht dein Wissen.
- Eine **wahre** Aussage, die die Passagen nicht belegen, zählt als **nicht belegt**.

**`hallucination`: „Does it contain anything that neither the excerpts nor the reference cover?“** – `none` /
`minor` / `substantive`
- Halluzination = was **weder Passagen noch Referenz** decken, oder was ihnen widerspricht.
- Zählt **auch, wenn es wahr ist**.
- `minor` = ändert die Antwort nicht; `substantive` = ändert sie oder widerspricht.
- Ein **erfundener Beispielname** zur Veranschaulichung ist **keine** Halluzination.

### Clarity

**`answers_question`: „Does it address what was asked?“** – `no` → Verständlichkeit 0.

**`direct`: „Does the core point come in the first two sentences?“**
- Bezogen auf die **Kernaussage der Antwort**, nicht die der Referenz.
- `yes` auch, wenn sie **falsch** ist (das zählt unter Facts) und auch, wenn ein zweiter Teil der Frage später
  beantwortet wird (ADR 0043).

**`wordy`: „Is it repetitive, padded or confusing?“**

### Notes

Passt eine Regel nicht, kommt das in „Notes“. Werte werden nie von Hand überschrieben.

## Ableitung der Werte (macht die App)

| Kriterium | 2 | 1 | 0 |
|---|---|---|---|
| Korrektheit | nichts falsch | `other_error` = yes oder `declines` = yes | `core_wrong` = yes |
| Vollständigkeit | alle Kernpunkte | ≥ Hälfte | weniger |
| Quellenbezug | `grounded` = all | some | none |
| Halluzinationsfreiheit | `hallucination` = none | minor | substantive |
| Verständlichkeit | `answers_question` yes, `direct` yes, `wordy` no | `answers_question` yes, sonst | `answers_question` no |

## Typische Grenzfälle

| Fall | Entscheidung |
|---|---|
| Wahre Aussage, steht weder in Passagen noch Referenz | `grounded` höchstens `some`, `hallucination` `minor` (oder `substantive`, wenn sie die Antwort ändert) |
| Steht in der Referenz, nicht in den Passagen | keine Halluzination, aber nicht belegt (`grounded`) |
| Steht in den Passagen, nicht in der Referenz | belegt, keine Halluzination |
| Teilantwort + „der Rest steht nicht in den Passagen“ | `declines` = no, fehlende Teile = `missing` |
| Kernaussage falsch, aber im ersten Satz | `core_wrong` = yes, `direct` = yes |
| Kernpunkt nur halb getroffen | `missing` |
| Versionsangabe in Klammern fehlt | trotzdem `covered` |
| Beispielname wie `my-app` erfunden | keine Halluzination |

## K0 (eigener Satz, nach C1–C3)

Nur zur Information: Seit ADR 0051 bewertet K0 das Sprachmodell mit diesen Regeln, nicht du.

- Dieselben eingefrorenen Kernpunkte; **kein `grounded`**, keine Passagen.
- `declines`: „Does the answer say it does not know the answer, and give none?“ (Teilantwort + „Rest unbekannt“ =
  `no`).
- `hallucination`: „Does it contain anything the reference does not cover?“ – Maßstab ist **nur die Referenz**.
- Nicht blind: die Strategie ist bekannt.

## Welche Fragen (ADR 0051, hybride Bewertung)

- **Nur diese 24 Fragen**, je alle drei Antworten (72 insgesamt), in beliebiger Reihenfolge über „Jump to“; die
  App zeigt nur sie an (seit PR #73):
  - Stichprobe: Q001, Q004, Q006, Q008, Q009, Q010, Q011, Q015, Q017, Q036, Q038, Q042
  - Zusatzfragen: Q005, Q012, Q014, Q020, Q024, Q027, Q029, Q030, Q033, Q035, Q040, Q045
- Die übrigen 24 Fragen und alle K0-Antworten bewertet das Sprachmodell; sie nicht bewerten.
- Keine Wiederholung, kein `mark`, keine 14 Tage.
- Kein `summarise` von Hand: das Zusammenführen (`src/hybrid.py --mode summarise`) folgt nach allen 72 Antworten.

## Nie

- `scoring_key.csv` öffnen oder Strategien erraten wollen.
- Kernpunkte nach dem Einfrieren ändern oder `key_points.csv` von Hand bearbeiten.
- Fragen außerhalb deiner 24 bewerten.
- Werte überschreiben; stattdessen „Notes“.
- Empfehlung, keine Regel: Ergebnisse (Retrieval-Metriken, RAGAS) erst nach der eigenen Bewertung ansehen.
