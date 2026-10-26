# 0035. Regelbasierte Rubrik-Bewertung mit Kernpunkten

## Status

Angenommen (17.10.2026; operationalisiert die Stufen von [ADR 0013](0013-antwort-rubrik.md); ergänzt
[ADR 0032](0032-blinde-rubrik-bewertung.md) und [ADR 0034](0034-bewertung-in-der-app.md)); der Intra-Rater-Folgeschritt unten entfällt, ersetzt durch die Zweitbewertung
nach [ADR 0046](0046-zweitbewertung.md), die Intra-Rater-Wiederholung nur noch als deren Ersatzverfahren (Jonas,
22.10.2026); verpflichtend für neue Scaffolds: [ADR 0036](0036-regelbasierte-bewertung-verpflichtend.md); für K0 ergänzt
durch [ADR 0041](0041-kontrolle-k0.md) (Regeln ohne `grounded`). Die Regeln wurden zweimal angepasst, nicht einmal wie
unten vorgesehen: nach dem Pilot-Set `hard` durch
[ADR 0037](0037-praezisierte-pruefregeln-und-vorbefuellte-kernpunkte.md) (Version `2026-10-18`) und nach dem Pilot e2e
durch [ADR 0043](0043-praezisierung-direct-und-teilantworten.md) (Version `2026-10-20`); der Hauptlauf nutzt
`config.RUBRIC_RULES_VERSION` = `2026-10-20`

## Kontext

- Die Rubrik (ADR 0013) beschreibt die Stufen mit Adjektiven („teilweise korrekt“). Dieselbe Person kann dieselbe
  Antwort an zwei Tagen verschieden einstufen; das schwächt die primäre Bewertung (ADR 0007).
- Ein LLM als Bewerter wäre wiederholbar, aber nicht valide geprüft; RAGAS bleibt sekundär (ADR 0007).

## Entscheidung

Wir werden die fünf Kriterien aus Prüffragen mit festen Antwortoptionen nach festen Regeln ableiten:

- Je Frage schreibt Jonas vor der Bewertung 1–4 Kernpunkte (`key_points.csv`, Punkt 1 = Kernaussage) und friert sie
  mit einem Protokolleintrag (Prüfsumme) ein; danach sind sie unveränderlich, jede Speicherung prüft die Prüfsumme.
- Je Antwort werden die Kernpunkte als „enthalten/fehlt“ markiert und acht Prüffragen beantwortet; die Werte folgen
  aus der Regeltabelle in [Evaluation](../reference/evaluation.md#regelbasierte-bewertung) (`src/scoring_rules.py`,
  Version `config.RUBRIC_RULES_VERSION`). Ein manuelles Überschreiben gibt es nicht.
- Eine Antwort, die erklärt, der Kontext enthalte die Antwort nicht, erhält Korrektheit 1, Vollständigkeit 0,
  Quellenbezug 2 und Halluzinationsfreiheit 2.
- Die Antworten auf die Prüffragen stehen in `scoring_checks.csv`; `--mode summarise` prüft jede Zeile des Bogens gegen
  sie.
- Die Regeln werden nach dem Pilot-Set `hard` einmal angepasst und dann für den Hauptlauf eingefroren.

## Konsequenzen

- Jeder Wert ist auf beobachtbare Prüfantworten zurückführbar; die Methodik kann die Regeln vollständig angeben.
- Ermessen bleibt in den Prüffragen selbst (z. B. „klein“ vs. „wesentlich“); die Intra-Rater-Übereinstimmung wird
  nach dem Pilot an einer Stichprobe gemessen (Folgeschritt).
- Kernpunkte sind Teil der Ground Truth: nur Jonas schreibt sie, vor jeder Bewertung (Geist von ADR 0017).
