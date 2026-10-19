# 0041. Kontrolle K0: Erzeugung und Bewertung

## Status

Angenommen (19.10.2026; setzt die Kontrolle K0 aus [ADR 0038](0038-korpus-e2e.md) um; Prompt aus
[ADR 0040](0040-closed-book-pruefung.md); ergänzt [ADR 0033](0033-antwortmodell.md) und
[ADR 0035](0035-regelbasierte-bewertung.md))

## Kontext

- ADR 0038 verlangt eine Kontrolle K0: dieselben Fragen ohne Retrieval, bewertet wie die Strategien, nicht in
  `config.STRATEGY_IDS`. Sie zeigt, wie viel das Retrieval überhaupt beiträgt.
- Das Modell gibt es nur als Alias; Antworten werden einmal in einem Lauf erzeugt (ADR 0033).
- Die Bewertung ist blind und zeigt zu jeder Antwort die Passagen, die das Modell sah (ADR 0032, 0035). K0 sah keine
  Passagen: im Paket wäre K0 sofort erkennbar, und `grounded` ergäbe stets 0.

## Entscheidung

Wir werden die K0-Antworten im selben `generate.py`-Lauf wie C1–C3 mit dem Closed-Book-Prompt erzeugen und in
`generated_answers_control.csv` ablegen; scheitert eine Antwort, wird keine Datei geschrieben.
Wir werden K0 als eigenen Bewertungssatz erst nach C1–C3 bewerten: `evaluate_answers.py --mode scaffold --control`
verweigert, solange `scores.csv` fehlt. K0 nutzt die eingefrorenen Kernpunkte und die Regeln von ADR 0035 ohne
`grounded`; `declines` heißt „sagt, dass es die Antwort nicht weiß“, Halluzination bezieht sich auf die Referenz.
Wir werden K0 mit C1–C3 über Korrektheit, Vollständigkeit, Halluzinationsfreiheit und Verständlichkeit vergleichen
(`config.CONTROL_CRITERIA`), insgesamt, je Fragetyp und Klasse und getrennt nach dem Closed-Book-Urteil (ADR 0040).

## Konsequenzen

- Positiv: K0 und C1–C3 stammen vom selben Modellstand; die Differenz zeigt den Beitrag des Retrievals, auch getrennt
  für retrieval-abhängige und bekannte Fragen.
- Negativ: K0 wird nicht blind bewertet (ohne Passagen erkennbar); der Quellenbezug fehlt im Vergleich. Beides steht
  als Grenze in der Arbeit.
- Neutral: Das blinde Paket und `scores.csv` von C1–C3 bleiben unverändert; die Reihenfolge verhindert, dass das
  Wissen um die K0-Antworten die Bewertung der Strategien färbt.
