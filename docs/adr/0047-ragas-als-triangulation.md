# 0047. RAGAS als feste Triangulation

## Status

Angenommen (21.10.2026; konkretisiert [ADR 0007](0007-triangulation.md); ändert „optional RAGAS“ in
[ADR 0015](0015-tech-stack.md)); Richtermodell und Metriken von Jonas entschieden. Umgesetzt 21.10.2026; die
Kosten liegen nach dem Pilot bei 2,02 USD je 48 Antworten, nicht im Cent-Bereich
([Experiment-Protokoll](../reference/experiment-record.md#ragas-pilot-e2e-21102026)).

## Kontext

- [ADR 0007](0007-triangulation.md) sieht RAGAS als sekundäre Bewertung vor und die Übereinstimmung mit der manuellen
  Bewertung als Validitätsindikator; spätere Seiten nannten RAGAS „optional“ ([ADR 0015](0015-tech-stack.md),
  [Evaluation](../reference/evaluation.md#triangulation), [Plan](../plan.md)).
- Ein Modell, das seine eigenen Antworten bewertet, bevorzugt sie tendenziell (Zheng et al., 2023); die Antworten
  stammen von `gpt-6-luna` ([ADR 0033](0033-antwortmodell.md)).
- LLM-Ausgaben sind auch bei `temperature = 0` und festem `seed` nur nach Möglichkeit wiederholbar
  ([ADR 0033](0033-antwortmodell.md)), und ein LLM als Bewerter ist nicht valide geprüft
  ([ADR 0035](0035-regelbasierte-bewertung.md)); die Arbeit darf daher nicht allein auf seinen Urteilen aufbauen.
- Im Lockfile steht `ragas` 0.4.3, in `pyproject.toml` nur `ragas>=0.1.0`.

## Entscheidung

Wir werden RAGAS auf allen 144 Antworten C1–C3 laufen lassen, mit vier Metriken: Faithfulness, Response Relevancy,
Context Precision und Context Recall, beide mit Referenz (die eingefrorenen Referenzantworten aus `ground_truth.csv`).
Wir werden `gpt-6-sol` als Richtermodell nutzen, nicht das Antwortmodell, mit `temperature = 0` und festem `seed`;
Richtermodell, RAGAS-Version (exakt gepinnt) und alle Parameter stehen in `src/config.py`.
Wir werden RAGAS erst laufen lassen, wenn die regelbasierte Bewertung C1–C3 mit `summarise` abgeschlossen ist; seine
Werte fließen nie in Fragen, Referenzen, Kernpunkte, Relevanzurteile oder `scores.csv` zurück
([ADR 0017](0017-fragenkatalog.md)).
Wir werden den Lauf wie die Antworten einmal ausführen, die Rohwerte je Antwort speichern und nie überschreiben, mit
Laufeintrag (Modell, Version, Prüfsummen von Antworten, Retrieval-Ergebnissen und Ground Truth, Tokens, Kosten).
Wir werden RAGAS beschreibend berichten (Mittel je Strategie, Effektstärken wie die Nebenmetriken in
[ADR 0044](0044-statistische-auswertung.md), keine p-Werte) und die Übereinstimmung mit dem jeweiligen Gegenstück
angeben (Spearmans ρ je Antwort): Faithfulness mit Quellenbezug und Halluzinationsfreiheit, Response Relevancy mit
der Prüffrage `answers_question`, Context Precision und Context Recall mit P@5 und R@5 der Hauptregel.
K0 bekommt kein RAGAS (ohne Kontext entfallen drei der vier Metriken).

## Konsequenzen

- Positiv: Die Arbeit hat eine zweite, automatische Sicht neben der regelbasierten Bewertung, mit einem anderen
  Modell als dem Antwortmodell; eine Abweichung ist selbst ein Befund zur Zuverlässigkeit der Metriken.
- Negativ: Ein weiteres Modell und eine weitere Abhängigkeit sind zu pinnen und zu dokumentieren; die Werte sind nicht
  bitgleich wiederholbar und dürfen deshalb nur sekundär sein. Code dafür ist noch umzusetzen.
- Neutral: Die Kosten liegen nach den Pilotkosten im Cent-Bereich; sie werden wie die übrigen Kosten protokolliert.

## Literatur

- Es, S., James, J., Espinosa-Anke, L., & Schockaert, S. (2024). RAGAS: Automated evaluation of retrieval augmented
  generation. *Proceedings of the 18th Conference of the European Chapter of the Association for Computational
  Linguistics: System Demonstrations*, 150–158.
- Zheng, L., Chiang, W.-L., Sheng, Y., et al. (2023). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena.
  *Advances in Neural Information Processing Systems 36* (Datasets and Benchmarks Track).
