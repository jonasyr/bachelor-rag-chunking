# Ersatzverfahren der Zweitbewertung Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Das Ersatzverfahren von ADR 0046 umsetzen: Jonas bewertet die 12 Stichprobenfragen frühestens 14 Tage
später ein zweites Mal blind (Intra-Rater), und gpt-6-sol beantwortet die Prüffragen als LLM-Gegenprobe. Beides
erscheint als eigene Übereinstimmungstabelle.

**Architecture:**
- **Wiederholungssatz:** `second_rater.py` bekommt zwei neue Modi, `mark` und `repeat`, und `close` lernt
  `--repeat`. Der Wiederholungssatz liegt in einem eigenen Ordner mit neu gemischten Codes; ein interner Schlüssel
  ordnet jeden neuen Code dem alten zu.
- **LLM-Gegenprobe:** `src/llm_rater.py` nach dem Muster von `generate.py` (Journal nach ADR 0050, Laufeintrag,
  sauberer Code-Stand). Es schreibt `scoring_checks.csv` und `scoring_sheet.csv` im Format der eigenen Bewertung.
- **Auswertung:** `analysis_data`, `report_tables` und `analyse` paaren jede vorhandene Zweitquelle mit Jonas'
  Erstbewertung über `agreement.pair`.

**Tech Stack:** Python 3.13, uv, pytest, OpenAI SDK (`response_format` json_schema), pandas; vorhandene Module
`agreement`, `scoring_rules`, `scoring_store`, `journal`, `run_log`.

**Spec:** ADR 0046 mit dem Nachtrag vom 17.11.2026 (Task 1 schreibt ihn). Dazu die Entscheidungen von Jonas im Chat
vom 17.11.2026:
- Ersatzverfahren auslösen.
- Die Stichprobe zuerst bewerten.
- Die Wiederholung kommt frühestens 14 Tage nach der Erstbewertung der Stichprobe und blockiert das Schreiben nicht.

## Global Constraints

- Alle Parameter nur in `src/config.py` (AGENTS.md); neue Schlüssel stehen in `docs/reference/configuration.md`.
- Tests rufen nie die OpenAI-API auf; der LLM-Client wird injiziert (wie `complete(messages, client)`).
- Kein Schritt ändert Jonas' Erstbewertung, `key_points.csv`, `scoring_key.csv` oder die Daten des Hauptlaufs.
- Die Werte der Arbeit bleiben Jonas' Erstbewertung. Wiederholung und LLM sind „Konsistenz- bzw.
  Triangulationsprüfung“, nie „Inter-Rater-Reliabilität“.
- Der R2-Weg bleibt unverändert nutzbar (Kollege springt doch ein): `SCORING_RATER=R2`, `second_rater/`,
  `agreement.tex`.
- `generate.py` sendet nach der Änderung von `llm_client.complete` bitgleich dieselbe Anfrage wie vorher.
- Repo-Doku Deutsch; Commits Conventional Commits auf Englisch, ohne AI-Attribution.
- Werte: `INTRA_RATER_PSEUDONYM = "R1W"`, `INTRA_RATER_DIR_NAME = "intra_rater"`, `INTRA_RATER_MIN_DAYS = 14`,
  `INTRA_RATER_SEED = 20261117`, `INTRA_RATER_KEY_FILE_NAME = "intra_rater_key.csv"`,
  `LLM_RATER_MODEL = RAGAS_JUDGE_MODEL`, `LLM_RATER_REASONING_EFFORT = "none"`, `LLM_RATER_TEMPERATURE = 0.0`,
  `LLM_RATER_SEED = 20261117`, `LLM_RATER_MAX_TOKENS = 1024`, `LLM_RATER_DIR_NAME = "llm_rater"`,
  `LLM_RATER_SCOPE = "all"` (alle 144 Antworten; Alternative `"sample"` = die 36 der Stichprobe; Jonas bestätigt).

## Review Focus

1. **Wiederholung vor Ablauf der 14 Tage:** `repeat` verweigert mit dem frühesten erlaubten Datum.
   (Test in Task 2.)
2. **Stichproben-Prüfantworten nach `mark` geändert:** `repeat` verweigert, ein neues `mark` startet die Frist neu.
   (Test in Task 2.)
3. **Im Wiederholungssatz verrät der Satz selbst die Zuordnung:** Die Buchstaben sind je Frage zufällig permutiert
   und die Fragenreihenfolge gemischt. Der Schlüssel steht nie in Items, Bogen oder App. (Test in Task 2.)
4. **LLM-Antwort ungültig** (Option außerhalb der Liste, falsche Zahl Kernpunkte, `declines` = yes mit Markierungen
   oder abgeschnitten): Der Schritt bricht mit `abort` im Journal ab; ein Neustart fragt die Antwort nicht neu an
   (ADR 0050). (Test in Task 4.)
5. **`analyse.py` mit nur einem Teil der Quellen** (nur LLM, nur Wiederholung, keine): Es entstehen nur die
   passenden Tabellen; jede fehlende bekommt einen Hinweis, und alte Dateien eines früheren Laufs werden entfernt.
   (Test in Task 5.)

---

### Task 1: Entscheidung dokumentieren

**Files:**
- Modify: `docs/adr/0046-zweitbewertung.md` (Nachtrag vor `## Literatur`, Statuszeile), `docs/adr/README.md`
  (Statusspalte 0046)
- Modify: `docs/plan.md` (offene Punkte 2 und 3, Stand, Verlauf 17.11.2026)

- [ ] **Step 1: Nachtrag schreiben**, Überschrift `## Nachtrag 17.11.2026: Ersatzverfahren ausgelöst`, erster Satz
  „Von Jonas entschieden; …“. Der Nachtrag hält fest:
  - Es gibt keine zweite Person, weil der Kollege wegen paralleler Prüfungen keine Zeit hat; das Ersatzverfahren
    gilt.
  - Jonas bewertet die 36 Antworten der Stichprobe als Erstes in der eigenen Bewertung.
  - Die Wiederholung startet frühestens `INTRA_RATER_MIN_DAYS` Tage nach dem Eintrag `intra_rater_mark` und wird
    technisch erzwungen.
  - Codes und Fragenreihenfolge der Wiederholung sind neu gemischt (`INTRA_RATER_SEED`). Die Wiederholung folgt dem
    Aufdecken; das ist eine Grenze, die neue Codes mildern.
  - Die LLM-Gegenprobe: `LLM_RATER_MODEL` (gpt-6-sol, nicht das Antwortmodell) beantwortet die Prüffragen mit
    Jonas' eingefrorenen Kernpunkten für `LLM_RATER_SCOPE` Antworten, blind, Temperatur 0, einmalig mit Journal
    (ADR 0050).
  - Berichtet wird beides als Konsistenz- bzw. Triangulationsprüfung (Zheng et al., 2023) mit denselben Maßen wie
    R2. Sagt R2 doch zu, gilt zusätzlich der ursprüngliche Weg.
- [ ] **Step 2: Plan aktualisieren.** Punkt 2 ist erledigt (keine Person); Punkt 3 wird umgesetzt (dieser Plan).
- [ ] **Step 3: Commit** `docs(adr): trigger the second-rating fallback (ADR 0046)`

### Task 2: Wiederholungssatz (mark, repeat, close --repeat, App)

**Files:**
- Modify: `src/config.py` (INTRA_RATER_* aus Global Constraints; `INTRA_RATER_DIR = DATA_EVAL / INTRA_RATER_DIR_NAME`)
- Modify: `src/second_rater.py`, `src/scoring_store.py`, `app/scoring_page.py` (nur Texte, die „R2“ fest nennen)
- Test: `tests/test_second_rater.py`, `tests/test_scoring_store.py`

**Interfaces:**
- Produces:
  - `second_rater.MARK_STEP = "intra_rater_mark"`, `REPEAT_STEP = "intra_rater_export"`,
    `REPEAT_CLOSE_STEP = "intra_rater_close"`, `REPEAT_KEY_HEADER = ["code", "original_code"]`
  - `second_rater.sample_rows_sha256(p: dict) -> str`: SHA-256 über die Prüfzeilen und Bogenzeilen der
    Stichproben-Codes aus Jonas' Dateien, in kanonischem JSON
  - `second_rater.run_mark(p: dict) -> dict`
  - `second_rater.run_repeat(p: dict, now: datetime | None = None) -> Path`
  - `second_rater.run_close(p: dict, repeat: bool = False) -> dict`
  - `second_rater.relabel(items: list[dict], seed: int) -> tuple[list[dict], list[dict]]`: liefert die neuen Items
    und die Schlüsselzeilen
  - `paths()` bekommt `"intra_dir"` (Hauptlauf `INTRA_RATER_DIR`, Pilot `set_dir / INTRA_RATER_DIR_NAME`)
  - `scoring_store.rater_mode()` akzeptiert `SECOND_RATER_PSEUDONYM` oder `INTRA_RATER_PSEUDONYM`;
    `single_rater_set()` liefert für `R1W` den Satz in `intra_dir` (Name „Repeat rating“)

- [ ] **Step 1: Failing tests** in `tests/test_second_rater.py` (Pilot-Fixture wie die vorhandenen Export-Tests):
  - `test_mark_needs_every_sample_answer_scored`: Fehlt eine Prüfzeile → `RuntimeError` mit dem fehlenden Code.
  - `test_mark_records_sample_hash`: Der Eintrag enthält `sample_sha256 == sample_rows_sha256(p)`.
  - `test_repeat_refused_before_min_days`: `now = mark + 13 Tage` → `RuntimeError` mit dem Datum `mark + 14 Tage`
    im Text.
  - `test_repeat_refused_when_sample_changed_after_mark`: Prüfzeile nach `mark` geändert → `RuntimeError`
    („mark again“).
  - `test_repeat_writes_relabelled_set`:
    - Items ohne `code` sind gleich den Originalen.
    - Codes sind je Frage eine Permutation von A–C, und die Fragenreihenfolge unterscheidet sich von der sortierten.
    - Die Schlüsseldatei bildet jeden neuen Code auf den alten ab, und das Original-Item zum alten Code gleicht dem
      neuen bis auf `code`.
    - Bogen und Laufprotokoll sind wie beim Export, und `scores.csv` darf existieren.
  - `test_relabel_is_seeded`: Dasselbe Ergebnis bei gleichem Seed.
  - `test_repeat_never_overwrites_values`: Wie beim Export.
  - `test_close_repeat_records_rater_R1W`: `extra["rater"] == "R1W"`.
  - In `tests/test_scoring_store.py`:
    - `test_rater_mode_accepts_R1W`: Mit `R1W` zeigt `single_rater_set()` den Wiederholungssatz.
    - `test_rater_mode_rejects_other`: Jeder andere Wert wirft wie bisher.
- [ ] **Step 2:** `uv run pytest tests/test_second_rater.py tests/test_scoring_store.py -q` → die neuen Tests
  scheitern.
- [ ] **Step 3: Implementieren.**
  - Den Schreibteil von `run_export` (Items, Kernpunkte, leerer Bogen, Laufprotokoll mit Scaffold- und
    Key-points-Eintrag) in `_write_set(out: Path, lines: list[str], points: list[dict]) -> tuple[Path, Path]`
    auslagern; `run_export` und `run_repeat` nutzen ihn.
  - `run_repeat` prüft:
    - den `mark`-Eintrag;
    - `now >= mark.time + INTRA_RATER_MIN_DAYS`;
    - den Hash gegen den markierten;
    - die eingefrorenen Kernpunkte;
    - dass der Ordner keine Werte hält.
  - Danach schreibt `run_repeat` `relabel(...)` und `intra_rater_key.csv`.
  - `relabel` mischt die Fragenreihenfolge und je Frage die Buchstaben mit `random.Random(seed)`.
  - CLI: `--mode mark|repeat`; `--repeat` nur mit `close`.
  - App: der Name `R1W` statt fest „R2“ in den Hinweisen; der Inhalt der Schlüsseldatei erscheint nie.
- [ ] **Step 4:** Dieselben Tests laufen durch; danach `uv run pytest -q` komplett grün.
- [ ] **Step 5: Commit** `feat(second-rater): repeat rating as the ADR 0046 fallback`

### Task 3: Auswertung der Wiederholung

**Files:**
- Modify: `src/analysis_data.py` (Feld `repeat_rating`), `src/report_tables.py`, `src/analyse.py`, `src/config.py`
  (`INTRA_RATER_DISAGREEMENTS_FILE_NAME = "intra_rater_disagreements.csv"`)
- Test: `tests/test_analysis_data.py`, `tests/test_report_tables.py`, `tests/test_analyse.py`

**Interfaces:**
- Consumes: `REPEAT_CLOSE_STEP`, `REPEAT_KEY_HEADER`, `paths()["intra_dir"]` aus Task 2
- Produces:
  - `analysis_data.AnalysisData.repeat_rating: dict | None` (gleiche Form wie `second_rating`; `paired` mit den
    Original-Codes)
  - `report_tables._agreement(paired_source: dict | None) -> dict | None`, aufgerufen für `second_rating` →
    `results["agreement"]` und `repeat_rating` → `results["agreement_intra"]`
  - `_agreement_table(results, key: str, title: str, lead: str) -> str`; neue Datei `agreement_intra.tex`, Titel
    „Übereinstimmung der Erst- und Wiederholungsbewertung“, Lead „Erst- und Wiederholungsbewertung durch dieselbe
    Person (mindestens {INTRA_RATER_MIN_DAYS} Tage Abstand, neu gemischte Codes) derselben …“

- [ ] **Step 1: Failing tests:**
  - `test_repeat_rating_paired_by_original_code`: Die Wiederholung bewertet `Q001-B` (Schlüssel → `Q001-A`); in
    `paired` steht `Q001-A` mit Jonas' erster Bewertung von `Q001-A`.
  - `test_repeat_rating_changed_after_close_aborts`: Eine Datei wurde nach dem Abschluss geändert →
    `RuntimeError`.
  - `test_agreement_intra_table_written`: Mit Wiederholung entsteht `agreement_intra.tex`; ohne entfallen die
    Datei und `intra_rater_disagreements.csv` mit dem Hinweis „Wiederholungsbewertung fehlt …“, und alte Dateien
    werden entfernt.
  - `test_agreement_table_unchanged_for_r2`: Die R2-Tabelle ist bitgleich mit der vorherigen Ausgabe
    (Snapshot-Vergleich der vorhandenen Testdaten).
- [ ] **Step 2:** Die Tests scheitern.
- [ ] **Step 3: Implementieren.**
  - Die Items der Wiederholung über den Schlüssel auf die alten Codes umschreiben.
  - Danach `agreement.require_same_inputs` und `agreement.pair` wie bei R2.
  - `require_run(..., REPEAT_CLOSE_STEP, ...)` schließt auch die Schlüsseldatei ein.
- [ ] **Step 4:** Komplette Testsuite grün.
- [ ] **Step 5: Commit** `feat(analysis): agreement of the repeat rating`

### Task 4: LLM-Gegenprobe

**Files:**
- Modify: `src/llm_client.py`
- Modify: `src/config.py`: LLM_RATER_* aus Global Constraints, `LLM_RATER_DIR = DATA_EVAL / LLM_RATER_DIR_NAME`,
  `LLM_RATER_SYSTEM_PROMPT`, `LLM_RATER_USER_TEMPLATE`
- Modify: `src/run_log.py`: `llm_rater_settings() -> dict` wie `ragas_settings`
- Create: `src/llm_rater.py`
- Test: `tests/test_llm_rater.py`, `tests/test_llm_client.py`

**Interfaces:**
- Produces:
  - `llm_client.complete(messages, client=None, *, model=LLM_MODEL, reasoning_effort=LLM_REASONING_EFFORT,
    temperature=LLM_TEMPERATURE, max_tokens=LLM_MAX_TOKENS, seed=LLM_SEED, response_format=None) -> Completion`.
    Ohne `response_format` wird der Parameter nicht gesendet.
  - `llm_rater.schema(n_points: int) -> dict`: ein JSON-Schema, strict. Felder `declines`, `points` (Liste der
    Länge n mit `covered`/`missing`), die übrigen Prüffragen mit den Optionen aus `scoring_rules.CHECKS` und
    `reason` (kurzer Text).
  - `llm_rater.messages(item: dict, key_points: list[str]) -> list[dict]`
  - `llm_rater.to_checks(parsed: dict, n_points: int) -> dict`: bei `declines` = yes über `rules.declined`, dann
    `rules.validate`
  - `llm_rater.run(paths: dict, client=None) -> dict`: schreibt `llm_rater/scoring_checks.csv`, `scoring_sheet.csv`
    (abgeleitet über `rules.derive`) und `llm_rater_journal.jsonl` und hängt den Laufeintrag `llm_rater`
    (Einstellungen, `model_created`, Tokens, Kosten zu den RAGAS-Preisen, Umgebung, Sitzungen, Abbrüche) an
    `generation_runs.jsonl` an.
- Prompt (exakter Text, Englisch wie die App):
  - Der Systemprompt beschreibt die Rolle („You score one answer of a RAG system against fixed checks. Answer only
    from the question, the reference answer, the key points and the excerpts shown.“) und danach für jede Prüffrage
    deren Text aus `app/scoring_page.QUESTIONS`, `POINT_HELP` und `HELP` (aus `scoring_page` nach `config`
    verschieben und dort von beiden importieren, damit App und LLM denselben Wortlaut sehen).
  - Das User-Template enthält Frage, Referenz, nummerierte Kernpunkte, die Passagen 1–5 und die Antwort, jeweils
    mit einer Überschrift.

- [ ] **Step 1: Failing tests** (Fake-Client, der eine geparste JSON-Antwort liefert):
  - `test_complete_default_request_unchanged`: Die Keyword-Argumente von `create` ohne neue Parameter sind exakt
    die bisherigen.
  - `test_schema_enums_match_rules`: Die Optionen im Schema entsprechen `scoring_rules.CHECKS`, und `points` hat
    `minItems = maxItems = n`.
  - `test_to_checks_declines_forces_skipped`: `declines` = yes mit Markierungen `covered` → alle `missing` und die
    übersprungenen Prüffragen auf die Standardwerte.
  - `test_run_writes_sheet_derived_from_checks`: Jede Bogenzeile ist `rules.derive` der Prüfzeile, und die
    Reihenfolge entspricht den Items.
  - `test_run_scope_sample_only_36` und `test_run_scope_all`.
  - `test_run_resumes_from_journal_without_calls`: Bei einem Neustart nach 5 Antworten fragt der Client nur die
    fehlenden an.
  - `test_run_aborts_on_invalid_option`: `abort` im Journal, keine Ausgabedatei; auch ein Neustart bricht ab.
  - `test_run_refuses_unfrozen_key_points` und `test_main_requires_clean_tree` (über `run_log.require_clean_tree`).
  - `test_messages_have_no_strategy`: Die Zeichenketten `C1`, `C2`, `C3` und `strategy` kommen außerhalb des
    Antworttexts nicht vor.
- [ ] **Step 2:** Die Tests scheitern.
- [ ] **Step 3: Implementieren** nach dem Muster von `generate.py`:
  - Journal-Start mit `llm_rater_settings()`, Prompt-Prüfsumme, `model_created` und Eingabe-Hashes (Items,
    Kernpunkte, Stichprobe).
  - Je Antwort ein `item`-Eintrag mit der vollständigen Antwort.
  - Gilt `finish_reason != "stop"` → Abbruch.
- [ ] **Step 4:** Komplette Testsuite grün.
- [ ] **Step 5: Commit** `feat(llm-rater): LLM cross-check of the rubric checks (ADR 0046)`

### Task 5: Auswertung der LLM-Gegenprobe

**Files:**
- Modify: `src/analysis_data.py` (`llm_rating`), `src/report_tables.py`, `src/analyse.py`
- Test: wie in Task 3

**Interfaces:**
- Consumes: der Laufeintrag `llm_rater` und die Dateien aus Task 4; `_agreement`/`_agreement_table` aus Task 3
- Produces: `results["agreement_llm"]`, `agreement_llm.tex` mit dem Titel „Übereinstimmung der Bewertung mit der
  LLM-Gegenprobe“. Der Lead nennt Modell und Zahl der Antworten. `llm_rater_disagreements.csv` wird nicht versioniert.

- [ ] **Step 1: Failing tests:**
  - `test_llm_rating_requires_matching_run_record`: Die Dateien wurden nach dem Laufeintrag geändert →
    `RuntimeError`.
  - `test_agreement_llm_table_written`.
  - `test_only_some_sources_present`: Die Kombinationen aus Review Focus 5.
- [ ] **Step 2:** Die Tests scheitern.
- [ ] **Step 3: Implementieren.**
- [ ] **Step 4:** Komplette Testsuite grün, `uvx pre-commit run --all-files` grün.
- [ ] **Step 5: Commit** `feat(analysis): agreement with the LLM cross-check`

### Task 6: Doku und Spickzettel

**Files:**
- Modify:
  - `docs/reference/evaluation.md`: Abschnitt Zweitbewertung, den Punkt „Ersatzverfahren … noch nicht umgesetzt“
    ersetzen.
  - `docs/how-to/run-the-experiment.md`:
    - Schritt 6 beginnt mit der Stichprobe und `--mode mark`.
    - neue Schritte für die LLM-Gegenprobe (nach Schritt 8) und die Wiederholung (`repeat`,
      `SCORING_RATER=R1W`, `close --repeat`).
    - Push-Regel: Mit der Wiederholung statt R2 ist Pushen nach Schritt 6 wieder erlaubt; der Schlüssel der
      Wiederholung wird erst nach `close --repeat` committet.
  - `docs/reference/data-formats.md`: die Ordner `intra_rater/` und `llm_rater/`, die Schlüsseldatei, das Journal
    und die Laufeinträge.
  - `docs/reference/configuration.md` und `docs/reference/prompts.md` (Prompt der LLM-Gegenprobe).
  - `.serena/memories` falls dort Zweitbewertung steht.
- Stays on `run/hauptlauf`: In `data/evaluation/scoring_cheatsheet.md` den Abschnitt „Wiederholung“ ergänzen
  (dieselben Regeln; den Schlüssel nie öffnen; die eigenen Erstwerte vorher nicht ansehen).

- [ ] **Step 1:** Doku schreiben; `uvx pre-commit run --all-files`.
- [ ] **Step 2: Commit** `docs: second-rating fallback (repeat rating, LLM cross-check)`
- [ ] **Step 3:** `codex-reviewer`-Agent auf den Branch, Befunde beheben, PR öffnen.
