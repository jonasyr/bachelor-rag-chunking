# 0044. Statistische Auswertung und Abbildungen

## Status

Angenommen (20.10.2026; vor dem Hauptlauf festgelegt; ergänzt [ADR 0008](0008-kosten-als-variable.md),
[ADR 0012](0012-retrieval-metriken.md) und [ADR 0013](0013-antwort-rubrik.md) sowie [ADR 0015](0015-tech-stack.md) (SciPy); ändert die Auswertungsart von
[ADR 0009](0009-hypothesen.md)). Präzisiert am 22.10.2026: [konfirmatorische
Tests](#nachtrag-22102026-konfirmatorische-tests) (Jonas); die dort genannte Tabellennotiz von `tests.tex` ist
korrigiert (PR #42). Präzisiert am 26.10.2026: [Holm über die testbaren
Metriken](#nachtrag-26102026-holm-über-die-testbaren-metriken) (Jonas)

## Kontext

- Verglichen werden drei Chunking-Strategien an denselben Fragen (verbundene Stichproben, n = 48); die Werte sind nicht
  normalverteilt und stark gebunden (Antwortwerte in Schritten von 0,2, die meisten bei 2; R@5 oft 0 oder 1).
- Viele Metriken (Hit@5, MRR, P@5, R@5, fünf Kriterien, zwei Relevanzregeln) würden ohne festen Testplan viele Tests
  und damit Zufallsbefunde erzeugen; einzelne Fragetypen oder Klassen haben nur wenige Fragen.
- K0 ist eine Kontrolle ohne Retrieval ([ADR 0041](0041-kontrolle-k0.md)), kein Teil des Strategievergleichs.
- Die Arbeit wird nach den IU-Regeln gesetzt; PaperLab prüft Abbildungen auf Schrift, Ausrichtung und Abstände.

## Entscheidung

Wir werden drei primäre Metriken konfirmatorisch testen: R@5 und MRR (Hauptregel) und den Gesamtwert der Antworten
(`config.ANALYSIS_PRIMARY`). Je Metrik ein Friedman-Test über C1–C3, Holm-Korrektur über die drei p-Werte; nur für
Metriken mit Holm-korrigiertem p < `config.ANALYSIS_ALPHA` (0,05) paarweise Wilcoxon-Tests (C1–C2, C1–C3, C2–C3),
Holm-Korrektur über alle diese Paare. Effektstärken: Kendalls W (aus dem bindungskorrigierten Friedman-Wert,
W = χ² / (n (k − 1)), voll gebundene Fragen zählen in n) und r = |z| / √n′ mit n′ = Zahl der Differenzen ungleich 0;
die Richtung zeigt die Median-Differenz.
Wir werden den Wilcoxon-Test zweiseitig mit Normalapproximation, Bindungskorrektur und ohne Stetigkeitskorrektur
rechnen, Nulldifferenzen verwerfen (`zero_method="wilcox"`) und Differenzen auf `config.ANALYSIS_DIFF_DECIMALS` Stellen
runden, damit gleiche Differenzen trotz Gleitkommafehler eine Bindung bilden; ein Paar mit nur einer Differenz
ungleich 0 gilt als testbar, sein Ergebnis wird mit n′ berichtet.
Wir werden alle übrigen Metriken, die Sensitivitätsregel, K0 gegen C1–C3 und die Aufteilung nach Fragetyp,
Konstruktionsklasse und Closed-Book-Urteil nur beschreibend berichten (Mittel, Median, Effektstärken, keine p-Werte);
der Zusammenhang von Retrieval und Antwort (H2) wird mit Spearmans ρ je Strategie und gepoolt berichtet (gepoolt ohne p-Wert, weil jede Frage dreifach eingeht). Alle
p-Werte gelten als explorativ.
Wir werden die Abbildungen in Endgröße nach den PaperLab-Regeln erzeugen (17 cm, Arial, kein Titel im Bild,
deutsche Zahlen, Klassenfarben FigBlue und FigOrange, dritter Farbton auf Farbsehschwäche geprüft, Kontrollen grau und
schraffiert, Werte in Heatmaps beschriftet) und Verteilungen wegen der Bindungen als Punktdiagramme statt Boxplots
zeigen.

## Konsequenzen

- Positiv: Der Testplan steht vor dem Hauptlauf fest; die Fehlerrate der konfirmatorischen Aussagen ist kontrolliert,
  und die Arbeit kann Unterschiede zwischen den Strategien belegen oder ausschließen.
- Negativ: Bei n = 48 und vielen Bindungen ist die Teststärke begrenzt; kleine Unterschiede bleiben unentdeckt.
  Unterschiede in Nebenmetriken lassen sich nur beschreiben.
- Neutral: `scipy` ist neu und auf 1.17.1 gepinnt (die einzige Version, die für alle von `requires-python` erlaubten
  Interpreter auflöst). Pilot-Sets werden ohne Laufeintrag `summarise` ausgewertet, weil ihre Bewertungen unter einer
  älteren Regelversion entstanden ([ADR 0043](0043-praezisierung-direct-und-teilantworten.md)).

## Nachtrag 22.10.2026: konfirmatorische Tests

Von Jonas entschieden; präzisiert die Entscheidung oben, ändert den Testplan nicht.

- Die Tests von R@5, MRR und Gesamtwert (`config.ANALYSIS_PRIMARY`) sind konfirmatorisch: der Plan stand vor dem
  Hauptlauf fest, die Fehlerrate ist mit Holm kontrolliert. Für diese drei Metriken ersetzt das „deskriptiv, nicht
  inferenzstatistisch“ aus [ADR 0009](0009-hypothesen.md).
- „Alle p-Werte gelten als explorativ“ meint alle übrigen p-Werte, etwa die der H2-Korrelationen (Spearmans ρ je
  Strategie).
- Die Konsequenz „belegen oder ausschließen“ gilt in diesem Sinn: für die drei primären Metriken, im Rahmen der
  begrenzten Teststärke (Negativ-Konsequenz oben).
- Die Tabellennotiz von `tests.tex` (`src/report_tables.py`) sagt noch „Explorativ“; sie wird im nächsten Code-PR
  korrigiert ([Backlog](../plan.md#backlog)).

## Nachtrag 26.10.2026: Holm über die testbaren Metriken

Von Jonas bestätigt (Doku-Audit); präzisiert „Holm-Korrektur über die drei p-Werte“ so, wie `src/stats.py` es seit
20.10.2026 umsetzt. Die Holm-Familie der Omnibus-Tests sind die
primären Metriken, deren Friedman-Test einen p-Wert hat. Eine Metrik, die über C1–C3 konstant ist, hat keinen p-Wert,
fällt aus der Familie und wird als nicht testbar berichtet; die übrigen werden über die verbleibenden p-Werte
korrigiert (`stats.confirmatory`; [Evaluation](../reference/evaluation.md#statistische-auswertung)). Für die Paare gilt
dasselbe: Holm über alle testbaren Paare.
