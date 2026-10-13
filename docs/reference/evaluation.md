# Evaluation

> Seitentyp: Nachschlagen (reference). Stand: aus dem Projektleitfaden (Juni 2026, aktualisiert 13.10.2026). Übersicht: [Dokumentation](../README.md).


## Retrieval-Evaluation
Beantwortet: Findet das System die richtigen Dokumentstellen?

- **Recall@k** = |R_q ∩ T_{q,k}| / |R_q| — Anteil der gefundenen relevanten Stellen unter Top-k
- **Hit@k** = 1, wenn mindestens eine relevante Quelle in Top-k, sonst 0 (vereinfachte, gut nutzbare Variante)
- **Precision@k** = |R_q ∩ T_{q,k}| / k — Anteil relevanter unter den Top-k
- **MRR** = (1/|Q|) · Σ 1/rank_q — Position des ersten relevanten Treffers

(R_q = relevante Stellen für Frage q; T_{q,k} = Top-k abgerufene Stellen.)

## Antwort-Evaluation (Rubrik 0–2)
| Kriterium | 0 | 1 | 2 |
|-----------|---|---|---|
| Korrektheit | falsch | teilweise korrekt | korrekt |
| Vollständigkeit | wesentliche Punkte fehlen | teilweise vollständig | vollständig |
| Quellenbezug | nicht belegt | teilweise belegt | klar durch Quellen gedeckt |
| Halluzinationsfreiheit | falsche/unbelegte Aussagen | kleine unbelegte Ergänzungen | keine Halluzinationen |
| Verständlichkeit | unklar | verständlich mit Schwächen | klar und präzise |

**Gesamtscore:** Q = (K + V + G + H + L) / 5, Wertebereich 0–2; optional Q_norm = (Q/2)·100.
**Gewichtung:** alle Kriterien gleich gewichtet, da keine priorisierte Domäne (Medizin/Recht/Sicherheit) untersucht wird — leichter zu begründen als komplexe Gewichtungen.

## Triangulation (verbindlich)
- **Primär:** referenzbasierte manuelle Bewertung (eigene Ground Truth, nicht zirkulär, verteidigbar).
- **Sekundär:** automatisiertes Framework (RAGAS) mit Metriken wie Faithfulness und Kontextrelevanz (skalierbar, reproduzierbar).
- **Validitätsindikator:** Übereinstimmung zwischen manueller und automatisierter Bewertung wird ausgewertet. Übereinstimmung → Robustheit; Abweichung → eigener Befund zur Metrik-Zuverlässigkeit.
- RAGAS ist **nie alleinige Grundlage** (LLM-as-a-judge hat bekannte Zuverlässigkeitsgrenzen).

## Effizienz/Kosten (abhängige Variable)
Pro Strategie erfassen: Chunk-Anzahl, Indexgröße, Token-Verbrauch (Prompt + Completion). Qualitätsunterschiede werden den Kosten gegenübergestellt („X % bessere Retrieval-Qualität bei Y× Kosten").

## Arbeitsdefinition Halluzination
Eine Halluzination liegt vor, wenn die Antwort Informationen enthält, die weder durch die Kontextpassagen noch durch die Referenzantwort gedeckt sind oder diesen widersprechen. Bewertung 2/1/0 wie in der Rubrik.

## Zweitbewertung (empfohlen)
10–20 % der Antworten unabhängig durch eine zweite Person bewerten lassen. Einfache Übereinstimmung = gleiche Bewertungen / alle Bewertungen, oder durchschnittliche absolute Abweichung bei 0–2-Skala. Cohen's Kappa optional.

## Statistische Auswertung
Deskriptiv ausreichend: Mittelwert, Median, Standardabweichung, Boxplot, Vergleich nach Fragetyp, Korrelation Retrieval vs. Antwortscore. Optional Signifikanztests: Friedman-Test (mehrere verbundene Gruppen), Wilcoxon Signed-Rank (paarweise) — nur bei Sicherheit im Umgang damit.


## Visualisierungen

| Visualisierung | Zweck |
|----------------|-------|
| Balkendiagramm Recall@5 je Strategie | Retrieval-Vergleich |
| Balkendiagramm MRR je Strategie | Rankingqualität |
| Boxplot Antwortscore je Strategie | Verteilung der Antwortqualität |
| Heatmap Frage × Strategie | Wo funktioniert welche Strategie? |
| Scatterplot Retrieval-Score vs. Antwortscore | Entkopplung Retrieval/Antwort (H2) |
| Bar Chart Fragetypen | Zusammensetzung des Katalogs |
| Chunk-Längen-Histogramm | Unterschiede der Strategien |
| Kosten-/Tokenvergleich | Effizienzbetrachtung (D8) |
