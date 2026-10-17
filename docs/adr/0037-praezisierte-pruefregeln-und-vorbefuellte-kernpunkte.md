# 0037. Präzisierte Prüfregeln und vorbefüllte Kernpunkte

## Status

Angenommen (18.10.2026; präzisiert [ADR 0035](0035-regelbasierte-bewertung.md))

## Kontext

- Im Pilot `data/pilot/hard` (H01–H08, 24 Antworten) bewertete ein unabhängiger Agent die Antworten mit den Prüffragen
  von ADR 0035 als Entwicklungshilfe; die Werte zählen nicht. 20 von 24 Antworten erhielten überall 2; alle vier Abzüge
  gingen auf Regelfälle zurück, nicht auf schwache Antworten: eine fehlende Versionsangabe in Klammern oder ein
  Nebensatz („unless …“) machte den einzigen Kernpunkt „missing“ (Vollständigkeit 0 bei Korrektheit 2), ein wahrer
  Zusatz kostete Quellenbezug und Halluzinationsfreiheit.
- Offen waren außerdem: ob eine Umformulierung als enthalten zählt, ob ein erfundener Beispielname eine Halluzination
  ist und was „direkt“ bei zweiteiligen Fragen heißt.
- Die Kernpunkte entsprachen fast wörtlich den Teilsätzen der Referenzantwort; sie von Hand abzuschreiben kostet Zeit
  ohne Erkenntnisgewinn.

## Entscheidung

Wir werden die Prüffragen so anwenden (`config.RUBRIC_RULES_VERSION` = `2026-10-18`; die Ableitung der Werte bleibt):

1. Ein Kernpunkt ist enthalten, wenn seine Bedeutung in der Antwort steht, auch in anderen Worten. Eine Einschränkung
   in Klammern (z. B. eine Versionsangabe) muss nicht enthalten sein; ein Nebensatz, der zählen soll, wird ein eigener
   Kernpunkt.
2. Nur teilweise enthalten zählt weiter als fehlend.
3. Eine wahre Aussage, die weder Passagen noch Referenz decken, zählt als nicht belegt und als Halluzination (`minor`,
   wenn sie die Antwort nicht ändert), wie in der Arbeitsdefinition.
4. Ein erfundener Beispielname zur Veranschaulichung ist keine Halluzination.
5. `direct` = yes, wenn die Kernaussage in den ersten zwei Sätzen steht, auch wenn ein zweiter Teil der Frage später
   beantwortet wird.

Die Kernpunkte werden in der App aus der Referenzantwort vorbefüllt (getrennt an Semikolon und Satzende, höchstens
`config.KEY_POINTS_MAX`, `scoring_rules.split_reference`); Jonas prüft sie, teilt weiter und speichert. Gespeichert
und eingefroren wird nur, was er bestätigt.

## Konsequenzen

- Vollständigkeit misst die Aussagen, nicht die Wortwahl oder Versionshinweise; weniger Abzüge aus Regelfällen.
- Die Kernpunkte bleiben Jonas' Entscheidung (Grundwahrheit), kosten aber je Frage nur eine Prüfung.
- Zeilen von `scoring_checks.csv` mit der älteren Regelversion weist `--mode summarise` ab; der Pilot war mit der alten
  Version nicht von Jonas bewertet, es geht nichts verloren.
- Der Pilot zeigte zudem kaum Unterschiede der Antwortqualität zwischen den Strategien bei unterschiedlichem
  Retrieval; das ist eine Beobachtung für die Auswertung, keine Regeländerung.
