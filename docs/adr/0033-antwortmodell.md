# 0033. Antwortmodell und einmalige Generierung

## Status

Angenommen (17.10.2026; konkretisiert [ADR 0016](0016-modell-neutralitaet.md), setzt [ADR 0014](0014-temperatur-und-topk.md) um)

## Kontext

- ADR 0014 verlangt Temperatur 0 für alle Strategien. Die aktuellen GPT-Modelle sind Reasoning-Modelle; sie nehmen
  `temperature` nur bei `reasoning_effort = "none"` an, und diese Stufe bieten nur GPT-6 Sol und GPT-6 Luna, nicht
  GPT-6.1 Sol und GPT-6 Astra (`openai2026latestmodel`, `openai2026reasoning`).
- Kandidaten (Stand 17.10.2026): `gpt-6-luna` (0,10/0,50 USD je 1 Mio. Ein-/Ausgabe-Tokens, Wissensstand Mai 2026,
  von OpenAI als Nachfolger von GPT-4o und GPT-4.1 genannt, `openai2026gpt6luna`), `gpt-6-sol` (2/10 USD, bereits
  durch GPT-6.1 Sol abgelöst) und `gpt-4.1-2025-04-14` (2/8 USD, datierter Snapshot, wird am 14.01.2027 abgeschaltet,
  drei Wochen nach der Abgabe, `openai2026deprecations`). Die GPT-5-Snapshots werden schon am 11.12.2026 abgeschaltet.
- `gpt-6-luna` gibt es nur als Alias ohne datierten Snapshot; das Modell hinter dem Namen kann sich ändern. Dasselbe
  Problem löst ADR 0024 für die Vektoren.
- Temperatur 0 kostet bei Faktenfragen keine Qualität (keine signifikante Wirkung zwischen 0,0 und 1,0,
  `renze2024temperature`), macht die Ausgabe aber nicht vollständig deterministisch (Genauigkeitsschwankungen bis
  15 % über wiederholte Läufe, `atil2024nondeterminism`).
- Verdecktes Reasoning könnte schwache Kontexte teilweise ausgleichen und so die Unterschiede zwischen den Strategien
  verkleinern, die die Arbeit messen will; zudem hilft es bei störenden Passagen nicht verlässlich
  (`lee2026noisybench`, nur Abstract geprüft). Ein Modell, das direkt aus den Passagen antwortet, zeigt deutlicher,
  was das Chunking liefert.
- Ein erster Aufruf am 17.10.2026 meldete als Modell nur `gpt-6-luna` und keinen `system_fingerprint`; die
  Modellliste der API führt keine datierten Varianten. Einziger Versionshinweis ist der Erstellungszeitpunkt des
  Modellobjekts (`GET /v1/models/gpt-6-luna`: 14.09.2026, 17:15:02 UTC); ob er sich bei einer Änderung hinter dem
  Alias ändert, dokumentiert OpenAI nicht.
- 144 Antworten (48 Fragen × 3 Strategien) mit rund 2.500 Prompt-Tokens kosten mit `gpt-6-luna` etwa 0,05 USD.

## Entscheidung

Wir werden die Antworten mit `gpt-6-luna` erzeugen, mit `reasoning_effort = "none"`, `temperature = 0` und
`max_completion_tokens = 1024` und einem festen `seed` (`config.LLM_*`), für alle Strategien gleich. Der `seed` ist
laut OpenAI eine Beta-Funktion, die Determinismus nur nach Möglichkeit herstellt (Hinweis aus dem Codex-Review von
PR #14); er ersetzt das einmalige Speichern nicht.

Wir werden alle Antworten in einem Lauf über C1–C3 erzeugen und speichern; `generated_answers.csv` wird nie
überschrieben, eine Neuerzeugung erfordert das bewusste Löschen der Datei. Der Lauf schreibt nichts, wenn eine
Antwort nicht mit `finish_reason = "stop"` endet (z. B. abgeschnitten) oder leer ist oder die API innerhalb des Laufs
verschiedene Modelle oder verschiedene `system_fingerprint`-Werte (Backend-Konfiguration) meldet; Letzteres nach dem
Codex-Review von PR #14, weil sonst Strategien auf verschiedenen Backends laufen könnten. Zeigt der Pilotlauf, dass
OpenAI den Fingerabdruck auch ohne Modelländerung laufend wechselt, wird diese Regel in einer neuen ADR überprüft. Das Laufprotokoll hält das von der API gemeldete Modell, die Prüfsummen der Ein- und
Ausgaben, SDK-Version, Tokens und Kosten je Strategie fest.

Wir werden den Erstellungszeitpunkt des Modellobjekts vor der ersten und nach der letzten Antwort abfragen (kostenlos),
im Laufprotokoll festhalten und den Lauf ohne Schreiben abbrechen, wenn er sich unterscheidet. In der Arbeit wird das
Modell als „`gpt-6-luna` (Modellobjekt erstellt 14.09.2026, Wissensstand 18.05.2026), aufgerufen am <Datum> mit
SDK <Version>“ angegeben.

Wir werden jeden Schritt nur auf den Dateien des letzten Laufs seines Vorgängers aufsetzen lassen (Hinweis aus dem
Codex-Review von PR #14): `generate.py` prüft vor dem ersten API-Aufruf, dass Fragen, Ground Truth und Chunk-Dateien
die Prüfsummen des letzten Retrieval-Laufs über C1–C3 haben und die Ergebnisdatei dessen Ausgabe ist;
`evaluate_answers.py --mode scaffold` prüft dasselbe gegen den letzten Generierungslauf, damit das Lesepaket genau die
Passagen zeigt, die das Modell gesehen hat. Retrieval-Einträge der Pilot-Sets vor dem 17.10.2026 haben keine
Ausgabe-Prüfsumme und werden nur an ihren Eingaben geprüft; für den Hauptlauf ist die Ausgabe-Prüfsumme Pflicht.

Wechsel auf `gpt-6-sol` (ebenfalls `"none"`) nur, wenn die Antworten der Pilotfragen dafür zu schwach sind, und nur
vor dem Hauptlauf.

## Konsequenzen

- Gut: Temperatur 0 bleibt möglich (ADR 0014); das Modell ist bis über die Verteidigung hinaus verfügbar.
- Gut: Die Antworten der Bewertung stammen nachweislich aus einem Modellstand und lassen sich mit dem gemeldeten
  Modellnamen genau angeben.
- Gut: Veraltete Retrieval-Ergebnisse oder nachträglich neu erzeugte Chunk-Dateien können weder in die Generierung
  noch in die Bewertung gelangen.
- Schlecht: Modell- und Fingerabdruck-Prüfung greifen bei `gpt-6-luna` derzeit nicht, weil die API weder eine
  Version noch einen Fingerabdruck meldet; der Erstellungszeitpunkt ist ein Hinweis, kein Beweis.
- Schlecht: Ohne datierten Snapshot lässt sich ein Lauf nach einer Modelländerung nicht exakt wiederholen; die
  gespeicherten Antworten sind die Primärdaten und daher versioniert (`generated_answers.csv`, mit
  `generation_runs.jsonl`).
- Neutral: Die Ergebnisse gelten für einen Generator, der direkt antwortet; mit einem Reasoning-Modell könnten die
  Unterschiede zwischen den Strategien kleiner ausfallen. Das nennt die Arbeit als Einschränkung
  ([Forschungsdesign](../explanation/research-design.md#validität-und-grenzen)).
- Neutral: Der Wissensstand Mai 2026 umfasst Vue.js; Antworten aus Modellwissen statt aus den Passagen bestraft die
  Rubrik über Quellenbezug und Halluzinationsfreiheit ([ADR 0013](0013-antwort-rubrik.md)).
