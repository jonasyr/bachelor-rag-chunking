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
([Zweitbewertung](#zweitbewertung)). Gilt stattdessen die hybride Bewertung (keine zweite Person,
[ADR 0051](../adr/0051-hybride-bewertung.md)), ist Pushen jederzeit erlaubt.

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

# 6. Eigene Bewertung C1–C3, hybrid (ADR 0051): zuerst die 12 Zusatzfragen ziehen und committen, vor jeder
#    eigenen Bewertung einer Frage außerhalb der Stichprobe (die Ziehung bricht sonst ab)
uv run python src/hybrid.py --mode draw
git add data/evaluation/hybrid_extra_sample.csv data/evaluation/generation_runs.jsonl
git commit -m "chore(data): Zusatzfragen der hybriden Bewertung gezogen"
#    App, Schritt „Score“: nur die 72 Antworten der 24 Fragen aus second_rater_sample.csv und
#    hybrid_extra_sample.csv bewerten, in beliebiger Reihenfolge; keine anderen Fragen
git add data/evaluation/scoring_sheet.csv data/evaluation/scoring_checks.csv
git commit -m "chore(data): eigene Bewertung (24 Fragen)"
# 7. Bewertung durch das Sprachmodell und Zusammenführen (ADR 0051): erst wenn alle 72 eigenen Antworten
#    bewertet sind. llm_rater bewertet alle 144 Antworten C1–C3 (ruft die API, einmal, überschreibt nie);
#    hybrid.py --mode summarise deckt auf: scores.csv mit Jonas' Werten für seine 24 Fragen und denen des
#    Sprachmodells für die übrigen (Spalte rater), dazu llm_rater/scores.csv nur mit den Werten des Sprachmodells
#    (beide nicht versioniert, wie scores.csv; versioniert ist der Laufeintrag)
uv run python src/llm_rater.py
git add data/evaluation/llm_rater/ data/evaluation/generation_runs.jsonl
git commit -m "chore(data): Bewertung des Hauptlaufs durch das Sprachmodell"
uv run python src/hybrid.py --mode summarise
git add data/evaluation/generation_runs.jsonl
git commit -m "chore(data): Werte des Hauptlaufs zusammengeführt (hybrid)"

#    Kontrolle K0: bewertet nur das Sprachmodell, verglichen mit dessen Werten für C1–C3
uv run python src/evaluate_answers.py --mode scaffold --control
uv run python src/llm_rater.py --control
uv run python src/hybrid.py --mode summarise-control
git add data/evaluation/scoring_items_control.jsonl data/evaluation/scoring_sheet_control.csv \
  data/evaluation/llm_rater/ data/evaluation/generation_runs.jsonl
git commit -m "chore(data): K0 durch das Sprachmodell bewertet"

# 8. RAGAS (erst nach dem Zusammenführen; ruft die API, einmal, überschreibt nie)
uv run python src/ragas_eval.py
git add data/evaluation/ragas_scores.csv data/evaluation/ragas_scores_journal.jsonl \
  data/evaluation/generation_runs.jsonl
git commit -m "chore(data): RAGAS des Hauptlaufs"

# 9. Nur mit R2: Zweitbewertung abschließen (R2 bewertet ab Schritt 5 an Jonas' Rechner, siehe Zweitbewertung)
SCORING_RATER=R2 uv run streamlit run app/catalogue_editor.py --server.address localhost
uv run python src/second_rater.py --mode close
git add data/evaluation/second_rater/
git commit -m "chore(data): Zweitbewertung abgeschlossen"
#    ab hier wieder pushen

# 10. Auswertung für die Arbeit
uv run python src/analyse.py
git add output/
git commit -m "chore(data): Auswertung des Hauptlaufs"
```

Danach Pull Request von `run/hauptlauf` und Submodul-Zeiger: [Ergebnisse in die Arbeit übernehmen](deliver-results-to-thesis.md).
Ohne zweite Person gilt die hybride Bewertung ([unten](#hybride-bewertung-ohne-zweite-person)); Schritt 9 entfällt
dann. Die Intra-Rater-Wiederholung (`second_rater.py --mode mark`, `--mode repeat`) gehört nicht mehr zum Hauptlauf
([ADR 0051](../adr/0051-hybride-bewertung.md)); der Code bleibt für Pilot-Sets.
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
  schreibgeschützt. Im hybriden Hauptlauf deckt `hybrid.py --mode summarise` auf (Schritt 7).
- Fehlt die nicht versionierte `scoring_items.jsonl` (neuer Klon, anderer Rechner), `--mode scaffold` mit denselben
  Optionen erneut ausführen: Er schreibt nur Lesepaket und Einträge neu, Bogen und Schlüssel bleiben unverändert.

- **Hybrid** ([ADR 0051](../adr/0051-hybride-bewertung.md)): Jonas bewertet nur die 24 Fragen aus
  `second_rater_sample.csv` und `hybrid_extra_sample.csv`, je alle drei Codes; die übrigen bewertet das Sprachmodell
  ([unten](#hybride-bewertung-ohne-zweite-person)).

**Kontrolle K0** (Schritt 7, [ADR 0041](../adr/0041-kontrolle-k0.md)): bewertet nur das Sprachmodell
([ADR 0051](../adr/0051-hybride-bewertung.md)), mit denselben eingefrorenen Kernpunkten und Prüffragen ohne
Quellenbezug: `llm_rater.py --control`, dann `hybrid.py --mode summarise-control`
([unten](#hybride-bewertung-ohne-zweite-person)). Was verglichen wird:
[Evaluation](../reference/evaluation.md#kontrolle-k0).

## Zweitbewertung

Eine zweite Person (Pseudonym R2) bewertet eine Stichprobe der Antworten C1–C3 nach denselben Regeln
([ADR 0046](../adr/0046-zweitbewertung.md)); was gemessen und wo es berichtet wird:
[Evaluation](../reference/evaluation.md#zweitbewertung). Gibt es keine zweite Person, gilt die hybride Bewertung
([unten](#hybride-bewertung-ohne-zweite-person)). Die Schritte im Hauptlauf:

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

### Hybride Bewertung (ohne zweite Person)

[ADR 0051](../adr/0051-hybride-bewertung.md) (ändert das Ersatzverfahren von
[ADR 0046, Nachtrag 17.11.2026](../adr/0046-zweitbewertung.md#nachtrag-17112026-ersatzverfahren-ausgelöst)): Jonas
bewertet 24 Fragen, das Sprachmodell alle Antworten; Schritt 9 und die Wiederholung entfallen. Dieselbe Stichprobe
(Schritt 1).

1. **Zusatzfragen ziehen** (Schritt 6, `src/hybrid.py --mode draw`): 12 Fragen aus den 36 außerhalb der Stichprobe,
   geschichtet wie die Stichprobe, Seed `config.HYBRID_SEED`. Bricht ab, wenn der Katalog nicht eingefroren ist, die
   Stichprobe nicht die ihres Laufeintrags `second_rater_draw` ist, `hybrid_extra_sample.csv` schon existiert oder eine
   Frage außerhalb der Stichprobe schon eigene Werte hat. Sofort committen.
2. **Eigene Bewertung** (Schritt 6): die 72 Antworten dieser 24 Fragen in der App, in beliebiger Reihenfolge.
3. **Bewertung durch das Sprachmodell** (Schritt 7, `llm_rater.py`): erst wenn die 72 eigenen Antworten bewertet
   sind, nach den eingefrorenen Kernpunkten, bei committetem Code-Stand; Umfang `config.LLM_RATER_SCOPE` (alle 144).
   Ergebnis: `data/evaluation/llm_rater/` (Prüfungen, Bogen, Journal), Laufeintrag `llm_rater`. Ein Pilot-Set mit
   `--set DIR`. Abbrüche: [Wenn ein Schritt abbricht](#wenn-ein-schritt-abbricht).
4. **Zusammenführen** (Schritt 7, `src/hybrid.py --mode summarise`): prüft beide Ziehungen und den Laufeintrag
   `llm_rater` (Umfang `all`), prüft Jonas' Bogen nur auf seinen 72 Codes und den des Sprachmodells auf allen, und
   schreibt `scores.csv` (Spalte `rater`: `human` oder `llm`) und `llm_rater/scores.csv` (nur Sprachmodell),
   Laufeintrag `hybrid_summarise`. Bricht ab und schreibt nichts, wenn Jonas' Bogen Werte oder Prüfungen auf einer
   Frage außerhalb seiner 24 hat, eine seiner 72 Antworten unbewertet ist oder eine Datei des Sprachmodells nicht zu
   dessen Laufeintrag passt. `evaluate_answers.py --mode summarise` gilt im hybriden Hauptlauf nicht.
5. **K0** (Schritt 7): `evaluate_answers.py --mode scaffold --control` schreibt die K0-Items wie bisher;
   `llm_rater.py --control` bewertet sie ohne Ausschnitte und ohne `grounded` (Laufeintrag `llm_rater_control`);
   `hybrid.py --mode summarise-control` schreibt `scores_control.csv` und vergleicht K0 mit den Werten des
   Sprachmodells für C1–C3, nicht mit dem gemischten Satz.
6. **Auswerten** (Schritt 10): `analyse.py` erkennt den hybriden Lauf am Laufeintrag `hybrid_summarise`. Die
   konfirmatorischen Tests laufen auf dem gemischten Satz; dazu die Übereinstimmung auf Jonas' 72 Antworten
   (`output/tables/agreement_llm.tex`, `output/llm_rater_disagreements.csv`) und die beiden beschreibenden
   Sensitivitätsanalysen (`output/tables/hybrid_sensitivity.tex`, `analysis.json` unter `hybrid`).

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
