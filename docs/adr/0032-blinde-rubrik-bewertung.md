# 0032. Blinde Rubrik-Bewertung der Antworten

## Status

Angenommen (16.10.2026; ergänzt [ADR 0013](0013-antwort-rubrik.md); in der App umgesetzt: [ADR 0034](0034-bewertung-in-der-app.md))

## Kontext

- Die Rubrik-Bewertung (ADR 0013) ist die primäre Antwortbewertung (ADR 0007) und wird von derselben Person
  vergeben, die die Hypothesen aufgestellt hat (ADR 0009). Wer beim Bewerten sieht, welche Strategie eine Antwort
  erzeugt hat, kann unbewusst die erwartete Strategie besser bewerten (Erwartungseffekt).
- `scores.csv` enthält die Strategie je Zeile; Chunk-IDs (`C1_…`) in `sources` verraten sie ebenfalls.
- Für Quellenbezug und Halluzinationsfreiheit braucht die bewertende Person die Kontextpassagen, die das Modell
  gesehen hat. Länge und Zuschnitt der Passagen (C3 beginnt an Überschriften, C1 schneidet mitten im Text) lassen die
  Strategie teilweise erahnen; das lässt sich nicht verbergen, ohne die Bewertung dieser Kriterien unmöglich zu machen.

## Entscheidung

Wir werden die Antworten blind bewerten:

- `evaluate_answers.py --mode scaffold` schreibt aus `generated_answers.csv` drei Dateien: ein Lesepaket
  (`scoring_packet.md`) mit Frage, Referenzantwort und je Antwort einem neutralen Code (`Q001-A`, `Q001-B`, …) samt
  den Passagen ohne Chunk-IDs, einen Bewertungsbogen (`scoring_sheet.csv`, eine Zeile je Code) und einen Schlüssel
  (`scoring_key.csv`, Code → Strategie).
- Die Reihenfolge der drei Antworten je Frage ist mit `config.SCORING_SEED` gemischt, fest und reproduzierbar.
- Der Schlüssel wird erst geöffnet, wenn jede Zeile bewertet ist: `--mode summarise` prüft den Bogen gegen den
  Schlüssel und schreibt erst dann `scores.csv` mit Strategie und `total_score`.
- Bogen und Schlüssel werden nie überschrieben; eine neue Runde braucht ein bewusstes Verschieben der Dateien.

## Konsequenzen

- Die Methodik kann eine blinde Bewertung der Strategie angeben; verbleibende Hinweise (Passagenzuschnitt) werden als
  Einschränkung genannt.
- Dieselben drei Dateien eignen sich für die empfohlene Zweitbewertung (Evaluation, „Zweitbewertung“): Paket und
  leerer Bogen gehen an die zweite Person, der Schlüssel nicht.
- `scores.csv` ist ein abgeleitetes Artefakt; die Primärdaten der Bewertung sind Bogen und Schlüssel.
