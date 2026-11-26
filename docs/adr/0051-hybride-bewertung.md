# 0051. Hybride Bewertung: Jonas bewertet 24 Fragen, das Sprachmodell alle Antworten

## Status

Vorgeschlagen (26.11.2026; Umfang, Aufteilung und Wegfall der Wiederholung von Jonas entschieden am 25.11.2026,
Schichtung der Ziehung, Vergleichsbasis von K0 und die zweite Sensitivitätsanalyse sind Vorschläge von Claude); ändert
[ADR 0007](0007-triangulation.md) (primär manuelle Bewertung), [ADR 0035](0035-regelbasierte-bewertung.md) (wer die
Prüffragen beantwortet), [ADR 0041](0041-kontrolle-k0.md) (wer K0 bewertet), [ADR 0044](0044-statistische-auswertung.md)
(Instrument des Gesamtwerts) und [ADR 0046](0046-zweitbewertung.md) (Ersatzverfahren, Nachtrag 17.11.2026)

## Kontext

- Der Hauptlauf hat 144 Antworten C1–C3 und 48 Antworten K0. Alle regelbasiert von Hand zu bewerten kostet nach der
  Schätzung von ADR 0046 (1,5–2 h je 36 Antworten) etwa 8,5–11 Stunden, mit der Intra-Rater-Wiederholung des
  Ersatzverfahrens (ADR 0046, Nachtrag 17.11.2026) etwa 10–13 Stunden. Bis zur Abgabe am 24.12.2026 bleiben neben dem
  Schreiben, dem eigentlichen Engpass, nur wenige Stunden.
- Die LLM-Gegenprobe (`src/llm_rater.py`) beantwortet dieselben Prüffragen mit Jonas' eingefrorenen Kernpunkten, blind
  und regelbasiert, für alle 144 Antworten unter 1 USD. Bisher ist sie nur Triangulation; die Werte der Arbeit
  sollten Jonas' Bewertung aller 144 Antworten sein (ADR 0046).
- Alle konfirmatorischen Tests sind nach Frage gepaart (Friedman, Wilcoxon; ADR 0044). Bewertet dieselbe Instanz alle
  drei Antworten einer Frage, geht ein Unterschied zwischen den Bewertern nicht in den Vergleich der Strategien
  innerhalb dieser Frage ein.
- Die Stichprobe der Zweitbewertung (`second_rater_sample.csv`, 12 Fragen) wurde vor jeder eigenen Bewertung
  geschichtet nach Fragetyp und Konstruktionsklasse gezogen (ADR 0046); eine zweite Person gibt es nicht.
- Erwogen wurden: alles selbst bewerten (Methode unverändert, Zeit fehlt), das Sprachmodell bewertet alles und Jonas
  nur 36 Antworten zur Prüfung (größte Abweichung vom Exposé, menschliche Bewertung nur noch als Stichprobe) und die
  hier gewählte Aufteilung nach ganzen Fragen.

## Entscheidung

Wir werden die Antworten hybrid nach ganzen Fragen bewerten:

- **Jonas** bewertet 24 Fragen × C1–C3 = 72 Antworten, blind und regelbasiert wie bisher (ADR 0032, 0035, 0043):
  die 12 Fragen von `second_rater_sample.csv` und 12 weitere. Die 12 weiteren werden vor jeder eigenen Bewertung
  einer dieser Fragen aus den übrigen 36 Fragen mit festem Seed gezogen (`src/hybrid.py --mode draw`,
  `config.HYBRID_SEED`, `config.HYBRID_EXTRA_QUESTIONS`), geschichtet nach Fragetyp und Konstruktionsklasse wie in
  ADR 0046, und als `hybrid_extra_sample.csv` mit Laufeintrag `hybrid_draw` festgehalten und committet. Beide
  Ziehungen zusammen bilden die Anteile des Katalogs genau ab (je 6 Fragen procedural, factual, conceptual, je 3
  comparative und limitation, je 6 Fragen jeder Konstruktionsklasse).
- **Das Sprachmodell** (`config.LLM_RATER_MODEL`, wie in ADR 0046 Nachtrag 17.11.2026: dieselben Prüffragen, Jonas'
  eingefrorene Kernpunkte, blind, Temperatur 0, einmalig mit Journal) bewertet alle 144 Antworten C1–C3 und alle 48
  Antworten K0, K0 mit den Regeln von ADR 0041 (ohne `grounded`, Halluzination gegen die Referenz).
- **Werte der Arbeit:** für Jonas' 24 Fragen seine Werte, für die übrigen 24 Fragen die des Sprachmodells; jede Zeile
  nennt ihre Quelle (Bewerter als Schicht). Darauf laufen die konfirmatorischen Tests des Gesamtwerts und die
  beschreibenden Auswertungen von ADR 0044 unverändert.
- **Sensitivitätsanalysen:** dieselben Tests und Kennzahlen (a) nur auf Jonas' 24 Fragen und (b) auf allen 48 Fragen
  nur mit den Werten des Sprachmodells. Beide sind beschreibend; konfirmatorisch bleibt der gemischte Satz.
- **K0** wird nur vom Sprachmodell bewertet. Der Vergleich K0 gegen C1–C3 (ADR 0041) nutzt deshalb auf beiden Seiten
  die Werte des Sprachmodells, damit er nicht zwei Instrumente vergleicht.
- **Übereinstimmung** Mensch–Sprachmodell auf Jonas' 72 Antworten, mit den Maßen von ADR 0046 (einfache
  Übereinstimmung, Gwets AC1 bzw. AC2, Krippendorffs α, Bootstrap-Intervall über Fragen), je Prüffrage und je
  Kriterium. Sie wird als Übereinstimmung mit einem automatischen Bewerter berichtet, nicht als
  Inter-Rater-Reliabilität (Zheng et al., 2023).
- **Die Intra-Rater-Wiederholung entfällt** (`second_rater.py --mode mark`, `--mode repeat`, `--mode close --repeat`
  werden im Hauptlauf nicht genutzt).
- Die Arbeit benennt die Abweichung vom Exposé („referenzbasierte manuelle Bewertung als primäres Verfahren“) und vom
  vor dem Hauptlauf festgelegten Testplan (ADR 0044: der Gesamtwert misst jetzt mit einem gemischten Instrument) offen,
  mit Begründung, in Methodik und Limitationen.

## Konsequenzen

- Positiv: Jonas' Aufwand sinkt auf etwa 3,5–4,5 Stunden; die Hälfte der Fragen bleibt menschlich bewertet, die
  Übereinstimmung wird auf 72 statt 36 Antworten gemessen. Weil Bewerter und Frage zusammenfallen, berührt ein
  Bewerterunterschied den Strategievergleich innerhalb einer Frage nicht.
- Negativ: Der primäre Gesamtwert stammt zur Hälfte von einem Sprachmodell, dessen Gültigkeit nur über die
  Übereinstimmung belegt ist; bekannte Verzerrungen (ähnliche Modellfamilie wie das Antwortmodell, Bevorzugung längerer
  Antworten; Zheng et al., 2023) bleiben möglich. Zwischen den Fragen kann sich der Bewerter auswirken, etwa auf Mittel
  je Fragetyp. Eine Intra-Rater-Messung gibt es nicht.
- Neutral: Noch umzusetzen (Folge-PR): K0 in `llm_rater.py`, das Zusammenführen der Werte mit Quelle je Zeile,
  Auswertung und Tabellen in `analyse.py`. Bis dahin bewertet Jonas nur seine 24 Fragen; `--mode summarise` setzt
  heute noch alle 144 Antworten voraus. Der Code der Wiederholung bleibt für Pilot-Sets bestehen.

## Literatur

- Zheng, L., Chiang, W.-L., Sheng, Y., et al. (2023). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena.
  *Advances in Neural Information Processing Systems 36* (Datasets and Benchmarks Track).
