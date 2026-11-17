# Experiment durchführen

*[Doku-Index](../README.md) · Anleitung · Verwandt: [Fragenkatalog erstellen](build-the-question-catalogue.md), [Evaluation](../reference/evaluation.md), [Werkzeuge](../reference/tooling.md#skripte-und-optionen)*

Diese Seite ist die einzige Beschreibung der Reihenfolge aller Schritte. Voraussetzungen: [Einrichten](set-up.md),
Fragenkatalog und Ground Truth fertig und eingefroren ([Fragenkatalog erstellen](build-the-question-catalogue.md),
[ADR 0017](../adr/0017-fragenkatalog.md), [ADR 0027](../adr/0027-blinde-annotation.md)). Nur das Chunking variiert
([ADR 0006](../adr/0006-nur-chunking-variiert.md)). Welche Schritte schon gelaufen sind: [Plan](../plan.md#stand).
Optionen der Skripte: [Werkzeuge](../reference/tooling.md#skripte-und-optionen); Ausgabedateien:
[Datenformate](../reference/data-formats.md).

## Vorbereitung

Einmal je Korpus, vor dem Fragenkatalog. Snapshot und Vektoren des e2e-Korpus sind versioniert
([ADR 0048](../adr/0048-korpus-und-chunk-vektoren-versioniert.md)); auf einem neuen Klon oder zweiten Rechner
entstehen Chunks und Index ohne API-Aufruf neu ([Auf zwei Rechnern arbeiten](work-on-two-machines.md)).

1. Snapshot, Ingest, Preprocessing: [Korpus-Snapshot erstellen](create-corpus-snapshot.md).
2. Chunking für C1–C3 und die Kontrolle K1: `uv run python src/chunking.py`
3. Embeddings und ein Chroma-Index je Strategie und für K1: `uv run python src/embed.py` (vorhandene Vektoren werden
   ohne API wiederverwendet; neue Vektoren brauchen `OPENAI_API_KEY`).

## Hauptlauf auf einen Blick

Der Hauptlauf beginnt mit dem eingefrorenen Katalog. Jeder Schritt ab `retrieve.py` prüft den Freeze-Datensatz vor
jedem API-Aufruf und bricht sonst ab. `retrieve.py`, `generate.py` und `ragas_eval.py` rufen die API außerdem nur
bei committetem Code-Stand auf (Änderungen in `data/` und `output/` zählen nicht), damit der Laufeintrag den Commit nennt
([ADR 0050](../adr/0050-journal-und-fortsetzen-der-api-schritte.md)). Der ganze Lauf geschieht auf einem eigenen Branch `run/hauptlauf`, nie auf
`main` ([AGENTS.md](../../AGENTS.md#conventions)); nach Schritt 10 wird er per Pull Request zusammengeführt
([Ergebnisse in die Arbeit übernehmen](deliver-results-to-thesis.md)). Nach jedem Schritt die versionierten Dateien committen
([Datenformate](../reference/data-formats.md#versioniert-und-ignoriert)), auch Fragevektoren und Retrieval-Ergebnisse
([ADR 0045](../adr/0045-retrieval-ergebnisse-versioniert.md)). **Pushen** (auf `run/hauptlauf`): mit R2 von Schritt 6 bis zum Abschluss der
Zweitbewertung in Schritt 9 nichts pushen; das Repo ist öffentlich, und R2 darf Jonas' Prüfantworten nicht sehen
([Zweitbewertung](#zweitbewertung)). Gilt stattdessen das Ersatzverfahren (keine zweite Person, Schritte 8a und 9a), ist
Pushen nach Schritt 6 wieder erlaubt; nur der Schlüssel der Wiederholung (`intra_rater_key.csv`) wird erst nach
`--mode close --repeat` committet, und nie vorher gepusht.

```bash
# 0. Katalog eingefroren: der Freeze-Commit existiert; Lauf-Branch anlegen
git log -1 --oneline -- data/evaluation/catalogue_freeze.json
git switch -c run/hauptlauf

# 1. Zweitbewertung ziehen: direkt nach dem Einfrieren, vor jedem eigenen Wert
uv run python src/second_rater.py --mode draw
git add data/evaluation/second_rater_sample.csv data/evaluation/generation_runs.jsonl
git commit -m "chore(data): Stichprobe der Zweitbewertung gezogen"

# 2. Retrieval C1–C3 und K1 (Fragevektoren: zwei API-Aufrufe, Modellstand-Prüfung und Fragen;
#    danach aus data/evaluation/query_embeddings.npz)
uv run python src/retrieve.py
uv run python src/retrieve.py --control
git add data/evaluation/query_embeddings.npz data/evaluation/retrieved_results.csv \
  data/evaluation/retrieved_results_control.csv data/processed/embedding_runs.jsonl
git commit -m "chore(data): Retrieval des Hauptlaufs"

# 3. Antworten C1–C3 und K0, genau einmal (überschreibt nie), sofort committen
uv run python src/generate.py
git add data/evaluation/generated_answers.csv data/evaluation/generated_answers_control.csv \
  data/evaluation/generation_journal.jsonl data/evaluation/generation_runs.jsonl
git commit -m "chore(data): Antworten des Hauptlaufs"

# 4. Retrieval-Metriken C1–C3 und K1
uv run python src/evaluate_retrieval.py
uv run python src/evaluate_retrieval.py --control
git add data/evaluation/retrieval_scores.csv data/evaluation/retrieval_scores_control.csv \
  data/processed/embedding_runs.jsonl
git commit -m "chore(data): Retrieval-Metriken des Hauptlaufs"

# 5. Bewertungsbogen, Kernpunkte und Satz für R2
uv run python src/evaluate_answers.py --mode scaffold
#    App, Seite „Scoring“, Schritt „Key points“: Kernpunkte prüfen und einfrieren (siehe Bewerten)
uv run python src/second_rater.py --mode export
git add data/evaluation/scoring_sheet.csv data/evaluation/scoring_key.csv data/evaluation/key_points.csv \
  data/evaluation/generation_runs.jsonl data/evaluation/second_rater/
git commit -m "chore(data): Bewertungsbogen, Kernpunkte und Satz der Zweitbewertung"

# 6. Eigene Bewertung C1–C3 (App, Schritt „Score“): zuerst die 36 Antworten der 12 Fragen der Stichprobe
#    (Fragen: data/evaluation/second_rater_sample.csv), dann festhalten, dass sie bewertet sind
#    (Ersatzverfahren: ab jetzt laufen die 14 Tage; danach die Zeilen der Stichprobe nicht mehr ändern)
uv run python src/second_rater.py --mode mark
git add data/evaluation/scoring_sheet.csv data/evaluation/scoring_checks.csv \
  data/evaluation/generation_runs.jsonl
git commit -m "chore(data): Stichprobe der Zweitbewertung bewertet"
#    übrige Antworten bewerten, dann aufdecken; mit R2 committen, aber NICHT pushen (siehe oben)
uv run python src/evaluate_answers.py --mode summarise
git add data/evaluation/scoring_sheet.csv data/evaluation/scoring_checks.csv \
  data/evaluation/generation_runs.jsonl
git commit -m "chore(data): Bewertung C1–C3"

# 7. Kontrolle K0 (erst nach scores.csv)
uv run python src/evaluate_answers.py --mode scaffold --control
#    App, Satz „Main catalogue: control K0“: jede Antwort prüfen
uv run python src/evaluate_answers.py --mode summarise --control
git add data/evaluation/scoring_items_control.jsonl data/evaluation/scoring_sheet_control.csv \
  data/evaluation/scoring_checks_control.csv data/evaluation/generation_runs.jsonl
git commit -m "chore(data): Bewertung K0"

# 8. RAGAS (erst nach summarise; ruft die API, einmal, überschreibt nie)
uv run python src/ragas_eval.py
git add data/evaluation/ragas_scores.csv data/evaluation/ragas_scores_journal.jsonl \
  data/evaluation/generation_runs.jsonl
git commit -m "chore(data): RAGAS des Hauptlaufs"

# 8a. LLM-Gegenprobe (Ersatzverfahren; ruft die API, einmal, überschreibt nie; nach den eingefrorenen Kernpunkten)
uv run python src/llm_rater.py
git add data/evaluation/llm_rater/ data/evaluation/generation_runs.jsonl
git commit -m "chore(data): LLM-Gegenprobe des Hauptlaufs"

# 9. Zweitbewertung abschließen (R2 bewertet ab Schritt 5 an Jonas' Rechner, siehe Zweitbewertung)
SCORING_RATER=R2 uv run streamlit run app/catalogue_editor.py --server.address localhost
uv run python src/second_rater.py --mode close
git add data/evaluation/second_rater/
git commit -m "chore(data): Zweitbewertung abgeschlossen"
#    ab hier wieder pushen

# 10. Auswertung für die Arbeit
uv run python src/analyse.py
git add output/
git commit -m "chore(data): Auswertung des Hauptlaufs"

# 9a. Wiederholung (Ersatzverfahren; frühestens 14 Tage nach dem mark in Schritt 6, ab dann erlaubt es der Code)
uv run python src/second_rater.py --mode repeat
#    Schlüssel nicht committen und nicht öffnen: Satz und Laufeintrag zuerst
git add data/evaluation/intra_rater/ ':!data/evaluation/intra_rater/intra_rater_key.csv' \
  data/evaluation/generation_runs.jsonl
git commit -m "chore(data): Wiederholungssatz der Zweitbewertung"
SCORING_RATER=R1W uv run streamlit run app/catalogue_editor.py --server.address localhost
uv run python src/second_rater.py --mode close --repeat
git add data/evaluation/intra_rater/
git commit -m "chore(data): Wiederholung der Bewertung abgeschlossen"
uv run python src/analyse.py   # jetzt mit der Wiederholungstabelle
git add output/
git commit -m "chore(data): Auswertung mit Wiederholungsbewertung"
```

Danach Pull Request von `run/hauptlauf` und Submodul-Zeiger: [Ergebnisse in die Arbeit übernehmen](deliver-results-to-thesis.md).
Die Schritte 8a und 9a gehören zum Ersatzverfahren ([Zweitbewertung](#zweitbewertung)); Schritt 9 entfällt dann.
Bricht ein Schritt ab, nennt die Meldung den Befehl, der den fehlenden oder veralteten Laufeintrag schreibt.
`retrieve.py` schreibt seine Ergebnisdateien bei jedem Lauf neu; weicht eine neue `retrieved_results.csv` von der ab,
auf der `generate` lief, bricht `ragas_eval.py` ab (der Scaffold prüft die Retrieval-Datei nicht). Nach Schritt 3
deshalb nicht neu retrieven. Der Probelauf dieser Befehlsfolge ist im
[Experiment-Protokoll](../reference/experiment-record.md#probelauf-hauptlauf-21102026) festgehalten, die Generalprobe
mit Störungen ebenda ([Generalprobe](../reference/experiment-record.md#generalprobe-hauptlauf-16112026)).

**Kosten** (geschätzt aus dem Pilot e2e mit 16 Fragen, mal 3 für 48 Fragen; Pilotwerte:
[Experiment-Protokoll](../reference/experiment-record.md#pilot-e2e-1920102026)): Generierung C1–C3 und K0 etwa
0,04 USD; Fragevektoren und Modellstand-Prüfung zusammen unter 0,01 USD; RAGAS etwa 6 USD für die Antworten C1–C3
([RAGAS-Pilot](../reference/experiment-record.md#ragas-pilot-e2e-21102026), 2,02 USD je Lauf mit 48 Antworten). Es
sind Schätzungen, keine Messwerte. Die LLM-Gegenprobe über 144 Antworten liegt nach der Schätzung im ADR bei unter
1 USD ([ADR 0046](../adr/0046-zweitbewertung.md#nachtrag-17112026-ersatzverfahren-ausgelöst)); ihr Laufeintrag zählt
alle Eingabe-Tokens zum vollen Eingabepreis, auch zwischengespeicherte (wie die Kosten der Generierung), und
überschätzt die Kosten daher leicht.

## Wenn ein Schritt abbricht

Generierung und RAGAS schreiben jede API-Antwort sofort in ein Journal
([ADR 0050](../adr/0050-journal-und-fortsetzen-der-api-schritte.md)); nichts Bezahltes geht verloren, und ein Neustart
erzeugt keine zweite Stichprobe.

- **Netz weg, Timeout, Ratenlimit:** Das SDK wiederholt eine Anfrage bis zu `OPENAI_MAX_RETRIES` Mal (RAGAS:
  `RAGAS_MAX_RETRIES`), jede Wiederholung steht als `INFO openai: Retrying …` auf der Konsole. Scheitert sie danach,
  bricht der Schritt ab, schreibt `abort` ins Journal und keine Ergebnisdatei. Denselben Befehl wieder ausführen,
  sobald das Netz wieder da ist: Er übernimmt alle journalisierten Antworten und fragt nur die fehlenden an.
- **Prozess getötet, Akku leer:** genauso; eine halb geschriebene letzte Journalzeile wird verworfen und diese eine
  Antwort neu angefragt.
- **Ergebnisdatei da, aber kein Laufeintrag** (Abbruch genau zwischen Schreiben und Eintrag: der Schritt meldet
  „exists“, der nächste einen fehlenden oder veralteten Eintrag): die Ergebnisdatei(en) des Schritts löschen, nie das
  Journal, und den Schritt erneut ausführen. Er baut sie aus dem Journal ohne einen Antwort-Aufruf neu.
- **„belongs to a run with other settings or inputs“:** Einstellungen, Prompts, Modellstand oder Eingaben weichen
  vom Journal ab. Nicht fortsetzen; mit Jonas klären, was sich geändert hat. Das Journal wird nie automatisch
  verworfen.
- **Abgeschnittene oder leere Antwort, ungültiger RAGAS-Wert, gewechseltes Modell:** Der Schritt bricht bei jedem
  Neustart erneut ab, weil das Journal die Antwort behält; Jonas entscheidet über das weitere Vorgehen
  ([ADR 0033](../adr/0033-antwortmodell.md)).
- **LLM-Gegenprobe, Antwort „leer“:** Verweigert das Modell die strukturierte Ausgabe (Refusal), erscheint das als
  „the answer is empty“; die Rohantwort mit der Verweigerung steht im Journal (`llm_rater_journal.jsonl`). Der Schritt
  bricht bei jedem Neustart erneut ab; Jonas entscheidet.
- **Gewechselter `system_fingerprint` zwischen Sitzungen:** Auch beim Fortsetzen vergleicht der Schritt mit den
  journalisierten Antworten; ein anderer Fingerprint (oder ein anderes Modell) beendet den Lauf, und Jonas entscheidet,
  wie bei der Generierung ([ADR 0033](../adr/0033-antwortmodell.md), [ADR 0050](../adr/0050-journal-und-fortsetzen-der-api-schritte.md)).
- **Zerrissene Zeile im Laufprotokoll** (`… line N is not JSON`): die genannte letzte Zeile prüfen und entfernen, wenn sie
  unvollständig ist; dann den Schritt erneut ausführen.

Abbrüche stehen mit Fehler und bezahlten Tokens im Journal; der Laufeintrag zählt `sessions`, `aborts` und
`http_errors`, die Kosten enthalten auch abgebrochene Aufrufe. Alles davon ins Experiment-Protokoll übernehmen.

## Bewerten (Schritte 5 und 6)

Blind ([ADR 0032](../adr/0032-blinde-rubrik-bewertung.md)) in der App
([ADR 0034](../adr/0034-bewertung-in-der-app.md)): `uv run streamlit run app/catalogue_editor.py --server.address
localhost`, Seite „Scoring“; Regeln: [Evaluation](../reference/evaluation.md#regelbasierte-bewertung).

- **Kernpunkte** (Schritt „Key points“): je Frage die aus der Referenzantwort vorbefüllten Kernpunkte prüfen, wo nötig
  weiter teilen, speichern und einfrieren; sichtbar sind nur Frage und Referenzantwort
  ([ADR 0037](../adr/0037-praezisierte-pruefregeln-und-vorbefuellte-kernpunkte.md)). Das Einfrieren gilt nur für
  dieses Scaffold; nach einem neuen Scaffold erneut einfrieren.
- **Bewerten** (Schritt „Score“): je Code die Prüffragen beantworten, die fünf Werte folgen aus den Regeln; `notes`
  frei, z. B. wenn eine Regel nicht passt. Von Hand eingetragene Werte nimmt `summarise` nicht an
  ([ADR 0036](../adr/0036-regelbasierte-bewertung-verpflichtend.md)). Das Lesepaket
  `data/evaluation/scoring_packet.md` ist nur Lesekopie; `scoring_key.csv` nie öffnen.
- **Aufdecken:** `--mode summarise` schreibt `scores.csv` (nicht versioniert); danach ist der Satz in der App
  schreibgeschützt.
- Fehlt die nicht versionierte `scoring_items.jsonl` (neuer Klon, anderer Rechner), `--mode scaffold` mit denselben
  Optionen erneut ausführen: Er schreibt nur Lesepaket und Einträge neu, Bogen und Schlüssel bleiben unverändert.

**Kontrolle K0** (Schritt 7, [ADR 0041](../adr/0041-kontrolle-k0.md)): erst nach `scores.csv`; dieselben eingefrorenen
Kernpunkte, Prüffragen ohne Quellenbezug, nicht blind; `--mode summarise --control` schreibt `scores_control.csv`
(nicht versioniert, entsteht mit demselben Befehl neu). Was verglichen wird:
[Evaluation](../reference/evaluation.md#kontrolle-k0).

## Zweitbewertung

Eine zweite Person (Pseudonym R2) bewertet eine Stichprobe der Antworten C1–C3 nach denselben Regeln
([ADR 0046](../adr/0046-zweitbewertung.md)); was gemessen und wo es berichtet wird:
[Evaluation](../reference/evaluation.md#zweitbewertung). Gibt es keine zweite Person, gilt das Ersatzverfahren
([unten](#ersatzverfahren-ohne-zweite-person)). Die Schritte im Hauptlauf:

1. **Ziehen** (Schritt 1, `--mode draw`): direkt nach dem Einfrieren und vor jedem eigenen Wert. Die Ziehung bricht ab,
   sobald Bogen oder Prüfantworten des Hauptlaufs Werte enthalten, und überschreibt keine vorhandene Stichprobe. Findet
   sie in `config.SECOND_RATER_MAX_DRAWS` Versuchen keine Stichprobe, die beide Schichtungen genau trifft, bricht sie
   ab.
2. **Exportieren** (Schritt 5, `--mode export`): nach Scaffold und eingefrorenen Kernpunkten, vor `summarise`. Der
   Export verweigert, sobald `scores.csv` existiert oder der R2-Ordner schon Werte hält. Er schreibt nach
   `data/evaluation/second_rater/` die Items, die Kernpunkte, einen leeren Bogen und ein Laufprotokoll, nie den
   Schlüssel und nie eigene Prüfantworten.
3. **R2 bewertet** an Jonas' Rechner, jederzeit nach dem Export:
   `SCORING_RATER=R2 uv run streamlit run app/catalogue_editor.py --server.address localhost` zeigt nur die Seite
   Scoring und nur den R2-Satz; die Kernpunkte sind dort nicht bearbeitbar. Jeder andere Wert von `SCORING_RATER`
   bricht ab. R2 sieht das Repo nicht. Jonas committet seine eigene Bewertung (Schritt 6), pusht `scoring_checks.csv`
   und `scoring_sheet.csv` aber erst nach dem Abschluss (Regel, nicht technisch erzwungen).
4. **Abschließen** (Schritt 9, `--mode close`): prüft, dass der Bogen alle exportierten Antworten in ihrer Reihenfolge
   nennt, die Kernpunkte die eingefrorenen sind und jeder Wert aus seinen Prüfantworten folgt; schreibt den Eintrag
   `second_rater_close` ins Laufprotokoll des R2-Ordners und macht den Satz schreibgeschützt. Ein abgeschlossener Satz
   lässt sich nicht erneut abschließen. Danach ist Pushen wieder erlaubt.
5. **Auswerten** (Schritt 10): `analyse.py` vergleicht beide Bewertungen und schreibt `output/tables/agreement.tex` und
   `output/second_rater_disagreements.csv`. Ohne Abschluss entfallen beide mit Hinweis; wurden R2-Dateien nach dem
   Abschluss geändert, bricht `analyse.py` ab.

### Ersatzverfahren ohne zweite Person

[ADR 0046, Nachtrag 17.11.2026](../adr/0046-zweitbewertung.md#nachtrag-17112026-ersatzverfahren-ausgelöst): Wiederholung und LLM-Gegenprobe statt R2; Schritt 9 entfällt. Dieselbe Stichprobe (Schritt 1).

1. **Stichprobe zuerst bewerten** (Schritt 6): Jonas bewertet die 36 Antworten der Fragen aus
   `data/evaluation/second_rater_sample.csv` als Erstes, dann `--mode mark`. Der Befehl verlangt Prüfungen und einen
   ausgefüllten Bogen für jede Antwort der Stichprobe und hält Zeit und Prüfsumme dieser Zeilen (einschließlich `notes`)
   im Eintrag `intra_rater_mark` fest. Ändert Jonas die Zeilen danach, verweigert `--mode repeat`; ein neues `mark`
   startet die Wartezeit neu.
2. **LLM-Gegenprobe** (Schritt 8a, `llm_rater.py`): nach den eingefrorenen Kernpunkten, bei committetem Code-Stand;
   Umfang `config.LLM_RATER_SCOPE`. Ergebnis: `data/evaluation/llm_rater/` (Prüfungen, Bogen, Journal), Laufeintrag
   `llm_rater`. Ein Pilot-Set mit `--set DIR`. Abbrüche: [Wenn ein Schritt abbricht](#wenn-ein-schritt-abbricht).
3. **Wiederholung erzeugen** (Schritt 9a, `--mode repeat`): frühestens `config.INTRA_RATER_MIN_DAYS` (14) Tage nach dem
   `mark`; vorher nennt die Fehlermeldung den frühesten Zeitpunkt. Der Befehl schreibt `data/evaluation/intra_rater/`
   mit denselben Antworten unter neuen Codes in neuer Fragenreihenfolge, dazu die Schlüsseldatei
   `intra_rater_key.csv`, und die Einträge `intra_rater_export`. Er verweigert, sobald der Ordner Werte hält.
4. **Wiederholung bewerten**: `SCORING_RATER=R1W uv run streamlit run app/catalogue_editor.py --server.address
   localhost` zeigt nur die Seite Scoring und nur den Wiederholungssatz (er fehlt in der normalen App). Regeln wie in
   [Bewerten](#bewerten-schritte-5-und-6); die eigenen Erstwerte vorher nicht ansehen, den Schlüssel nie öffnen.
5. **Abschließen** (`--mode close --repeat`): prüft wie bei R2 (alle Antworten in der Reihenfolge, eingefrorene
   Kernpunkte, Werte folgen aus den Prüfungen) und schreibt `intra_rater_close` in `intra_rater/runs.jsonl`, mit der
   Schlüsseldatei unter den Eingaben. **Erst danach** wird der Ordner einschließlich Schlüssel committet; vorher bleibt
   der Schlüssel aus dem Commit und aus jedem Push.
6. **Auswerten**: `analyse.py` schreibt `output/tables/agreement_intra.tex` und `output/tables/agreement_llm.tex` sowie
   `output/intra_rater_disagreements.csv` und `output/llm_rater_disagreements.csv`; fehlt eine Quelle, entfällt ihr Teil
   mit Hinweis. Da die Wiederholung erst Wochen nach der ersten Analyse vorliegt, läuft `analyse.py` ein zweites Mal.

## Auswertung (Schritt 10)

Als Letztes, wenn alle Ergebnisdateien zu den aktuellen Läufen gehören ([ADR 0044](../adr/0044-statistische-auswertung.md)).
`analyse.py` schreibt `output/tables/*.tex`, `output/figures/*.pdf`, `output/analysis.json` und
`output/second_rater_disagreements.csv` (alle versioniert) und bricht ab, wenn der Katalog nicht eingefroren ist oder
eine Ergebnisdatei nicht zum letzten Laufeintrag passt (dann den Schritt wiederholen); entfallene Teile meldet es als
`note:`. Die Retrieval-Metriken aus Schritt 4 nur dann erneut berechnen, wenn sie älter sind als das letzte Retrieval.

## Vor jedem Evaluationslauf prüfen

Erzwungen durch den Freeze-Datensatz und die Laufeinträge: `questions.csv`, `ground_truth.csv`, `sections.jsonl` und
`documents.jsonl` unverändert seit dem Einfrieren; Bewertung nach der Regelversion des Freeze-Datensatzes
(`config.RUBRIC_RULES_VERSION`, sonst brechen Scaffold und Summarise ab); jede Ergebnisdatei passt zu ihrem
Laufeintrag. Von Hand prüfen:

- [ ] Snapshot-Commit in `docs/corpus_snapshot.txt` und im [Experiment-Protokoll](../reference/experiment-record.md)
- [ ] Exakte Modellversionen im Experiment-Protokoll eingetragen
- [ ] Jedes Zwischenartefakt gespeichert, nicht nur das Endergebnis (alle versionierten Dateien aus
      [Datenformate](../reference/data-formats.md#versioniert-und-ignoriert), auch `retrieved_results_control.csv` und
      die Laufprotokolle)
- [ ] Prompts in allen Strategieläufen unverändert, für K0 der Closed-Book-Prompt ([Prompts](../reference/prompts.md))
- [ ] `LLM_TEMPERATURE` und `TOP_K` in `src/config.py` unverändert ([Konfiguration](../reference/configuration.md),
      [ADR 0014](../adr/0014-temperatur-und-topk.md))
