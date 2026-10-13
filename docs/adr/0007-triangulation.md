# 0007. Evaluation als Triangulation: manuell primär, RAGAS sekundär

## Status

Angenommen (D7 im Leitfaden; Quelle: Chat, verschärft die Baseline, in der RAGAS nur optional war)

## Kontext

- Die manuelle, referenzbasierte Bewertung beruht auf einer eigenen Ground Truth, ist nicht zirkulär und verteidigbar ([Leitfaden §12.3](../reference/evaluation.md#triangulation-verbindlich)).
- Ein automatisiertes Framework wie RAGAS ist skalierbar und reproduzierbar, LLM-as-a-Judge hat aber bekannte Zuverlässigkeitsgrenzen (Leitfaden §12.3).
- Eine rein automatische Bewertung ohne menschliche Kontrolle liegt außerhalb des Scopes (Leitfaden §3).

## Entscheidung

Wir werden primär manuell und referenzbasiert bewerten und sekundär mit RAGAS (Faithfulness, Kontextrelevanz).
Wir werden die Übereinstimmung beider Bewertungen als Validitätsindikator auswerten und berichten.

## Konsequenzen

- Gut: Übereinstimmung spricht für Robustheit der Ergebnisse; eine Abweichung ist ein eigener Befund zur Zuverlässigkeit der Metrik (Leitfaden §12.3).
- Schlecht: Die manuelle Bewertung kostet Zeit, eine Zweitbewertung von 10–20 % der Antworten wird empfohlen (Leitfaden §12.6).
- Neutral: RAGAS ist nie alleinige Grundlage.
