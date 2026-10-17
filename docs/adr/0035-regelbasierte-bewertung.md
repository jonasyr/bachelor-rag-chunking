# 0035. Regelbasierte Rubrik-Bewertung mit Kernpunkten

## Status

Angenommen (17.10.2026; ergänzt [ADR 0013](0013-antwort-rubrik.md), [ADR 0032](0032-blinde-rubrik-bewertung.md) und
[ADR 0034](0034-bewertung-in-der-app.md))

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
