# 0050. Journal und Fortsetzen der API-Schritte

## Status

Angenommen (16.11.2026; von Jonas entschieden nach der Generalprobe des Hauptlaufs; ergänzt
[ADR 0033](0033-antwortmodell.md) und [ADR 0047](0047-ragas-als-triangulation.md))

## Kontext

- Antworten und RAGAS-Werte entstehen genau einmal ([ADR 0033](0033-antwortmodell.md),
  [ADR 0047](0047-ragas-als-triangulation.md)): Die Modelle gibt es nur als Alias, ein zweiter Lauf wäre eine zweite
  Stichprobe.
- Die Generalprobe am 16.11.2026 (alle zehn Schritte gegen einen nachgebauten API-Server,
  [Experiment-Protokoll](../reference/experiment-record.md#generalprobe-hauptlauf-16112026)) und zwei unabhängige
  Prüfungen zeigten:
  - Generierung und RAGAS hielten alle Ergebnisse bis zum Ende im Speicher. Ein Netzausfall nach Antwort 150 verwarf
    alle bezahlten Antworten ohne Spur; ein einziger fehlgeschlagener RAGAS-Auftrag verwarf den ganzen Lauf.
  - Zwischen dem Schreiben der Ausgabe und dem Laufeintrag lag ein ungeschütztes Fenster. Ein Abbruch dort ließ
    Antworten ohne Eintrag zurück; Ausweg wäre nur eine zweite Generierung gewesen.
  - Gespeichert waren nur Antworttext und Zahlen. Die vollständigen API-Antworten (unter anderem `reasoning_tokens`
    als Beleg für Aufwand `none`, `cached_tokens`) und die Begründungen des RAGAS-Richters gingen verloren. ADR 0047
    nennt eine Abweichung zwischen RAGAS und Rubrik „selbst ein Befund“; erklären lässt sie sich nur mit diesen
    Begründungen.
  - Kein Laufeintrag nannte Commit, Python-Version oder Paketstand; die Generierung wiederholte eine Anfrage nur zweimal
    (SDK-Standard), ohne dass das sichtbar war.
  - Die pre-commit-Hooks `trailing-whitespace` und `end-of-file-fixer` liefen auch über `data/` und hätten eine
    Antwortdatei beim Commit verändern können; dann passt ihre Prüfsumme nicht mehr zum Laufeintrag.

## Entscheidung

Wir werden jede API-Antwort der einmaligen Schritte in dem Moment, in dem sie eintrifft, in ein versioniertes Journal
schreiben und einen abgebrochenen Lauf aus diesem Journal fortsetzen statt ihn neu zu beginnen:

- **Journal** (`journal.Journal`): JSONL, jede Zeile vor dem nächsten Schritt auf die Platte geschrieben (`fsync`).
  Die erste Zeile (`start`) hält Schritt, gepinnte Einstellungen, Prompt-Prüfsumme, Erstellungszeitpunkt des Modells
  und die Prüfsummen der Eingaben; jeder Lauf hängt `session` an, ein Abbruch `abort` mit dem Fehler.
- **Generierung**: `generation_journal.jsonl` hält je Antwort die vollständige API-Antwort. Ein Neustart übernimmt
  jede journalisierte Antwort und fragt nur die fehlenden an. Fehlen nach einem Abbruch die Antwortdateien, entstehen
  sie aus dem Journal ohne einen Antwort-Aufruf neu.
- **RAGAS**: `ragas_scores_journal.jsonl` hält je Block von `config.RAGAS_JOURNAL_BATCH` Antworten die Werte und jeden
  Richteraufruf (Anfrage, Antwort, Status, Auftrag); ein Neustart verliert höchstens einen Block. Tokens und Kosten
  zählen auch die Aufrufe abgebrochener Blöcke.
- **Nie verworfen**: Weichen Einstellungen, Prompts, Modellstand oder Eingaben vom `start`-Eintrag ab, setzt der Lauf
  nicht fort, sondern bricht ab; das Journal wird nur von Hand beiseitegelegt. Eine journalisierte Antwort, die die
  Prüfung nicht besteht (abgeschnitten, leer), stoppt jeden Neustart erneut, bis Jonas entscheidet.
- **Laufeinträge** von `embed`, `retrieve`, `generate` und `ragas` tragen `git_commit`, `git_dirty`, `python` und
  `uv_lock_sha256`; `generate` zusätzlich `prompts_sha256`, `sessions`, `aborts`, `http_errors` und je Strategie
  `reasoning_tokens` und `cached_tokens`.
- **Sauberer Code-Stand**: `retrieve.py`, `generate.py` und `ragas_eval.py` verweigern auf dem Hauptkatalog jeden
  API-Aufruf, solange Code, Doku oder Konfiguration ungespeicherte Änderungen haben; `data/` und `output/` sind
  ausgenommen, sie sind in den Laufeinträgen gehasht.
- **Wiederholungen**: Generierung und Embeddings wiederholen eine Anfrage bis zu `config.OPENAI_MAX_RETRIES` Mal mit
  Zeitgrenze `config.OPENAI_TIMEOUT_S`; jede Wiederholung erscheint auf der Konsole, jede Fehlerantwort im Journal.
- **Hooks**: Die verändernden pre-commit-Hooks laufen nicht über `data/`; die Journale sind von der Größengrenze
  ausgenommen.

## Konsequenzen

- Ein abgebrochener Hauptlauf kostet höchstens die eine laufende Anfrage (Generierung) bzw. einen Block (RAGAS) und
  erzeugt keine zweite Stichprobe. Abbrüche und ihre Kosten stehen im Journal und im Laufeintrag und können in der
  Arbeit berichtet werden.
- Die Begründungen des RAGAS-Richters und die vollständigen Antworten bleiben für die Analyse von Ausreißern erhalten.
  Das RAGAS-Journal wird etwa 12–15 MB groß (Generalprobe: 12 MB mit kurzen Richterantworten).
- Ein Schritt des Hauptlaufs startet erst nach dem Commit des vorigen Code-Stands; die Anleitung committet ohnehin
  nach jedem Schritt.
- Die Prüfung eines gewechselten Fingerabdrucks gilt über alle Sitzungen eines Laufs; wechselt die API ihn zwischen
  zwei Sitzungen, bricht der Lauf ab, und Jonas entscheidet über das Journal.
