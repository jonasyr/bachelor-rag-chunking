# Zweitbewertung (ADR 0046) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A second rater (pseudonym R2) scores a seeded, stratified sample of 12 questions × C1–C3 blind in the app; `analyse.py` reports agreement with Jonas' rating as appendix table `agreement.tex`.

**Architecture:** A new step `src/second_rater.py` (modes `draw`, `export`, `close`) creates the sample, the R2 scoring set and its closing record. Agreement statistics are pure functions in `src/stats.py`; `src/agreement.py` pairs the two ratings code by code and builds rows and the disagreement list; `analysis_data` loads a closed R2 rating, `report_tables` writes the table. The app finds the R2 set and, with `SCORING_RATER=R2`, shows only it.

**Tech Stack:** Python 3, numpy, pandas, Streamlit, pytest; no new dependency.

**Spec:** `docs/superpowers/specs/2026-10-22-second-rater-design.md` (approved by Jonas 22.10.2026)

## Global Constraints

- All parameters only in `src/config.py` (count 12, seeds, folder and file names, bootstrap reps/level/seed, pseudonym, env var, max draws).
- Only the pseudonym `R2` in files, run records, logs and output; no field for a name.
- R2 values only under `data/evaluation/` (main) or `DIR/second_rater/` (pilot set); never written into `scores.csv`, `scoring_checks.csv` or key points.
- Main catalogue: every guard is a hard abort; pilot sets (`--set`): the guards "own values already present" (draw) and "`scores.csv` exists" (export) only warn.
- Tests never call the OpenAI API or the network; Conventional Commits with German subjects; no AI attribution.
- Measures: simple agreement; AC1 for yes/no checks and key points; AC2 with Gwet's ordinal weights for `grounded`, `hallucination` and the five criteria; Krippendorff's α ordinal; percentile bootstrap CI over questions.
- Table `agreement.tex`, title „Übereinstimmung der Erst- und Zweitbewertung“, label `tab:agreement`, IU format via `latex_table`, German decimal comma.
- Use Serena and codebase-memory for code navigation and symbol edits.

## Review Focus

- R2 mode leaks: with `SCORING_RATER=R2` set, no other set, no catalogue page and no key file reachable from the app → test in Task 3.
- An R2 sheet edited after `close` must make `analyse.py` refuse (checksums), not silently report → test in Task 5.
- Draw on a catalogue where both marginals cannot be met (pilot) must abort with a message, not loop forever → test in Task 2.
- A key point count mismatch between R2's and Jonas' checks (same question, different number of marks) must abort in pairing, not misalign → test in Task 5.
- α undefined in some bootstrap resamples: CI from the rest, dropped count reported; α undefined on the full data: `NOT_DETERMINABLE` → test in Tasks 1 and 5.

---

### Task 1: Agreement statistics in `stats.py`

**Files:**
- Modify: `src/config.py` (new block "Second rating (D46)")
- Modify: `src/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Produces:
  - `config.AGREEMENT_BOOTSTRAP_REPS = 2000`, `config.AGREEMENT_CI_LEVEL = 0.95`, `config.AGREEMENT_SEED = 20261022`
  - `stats.ordinal_weights(q: int) -> list[list[float]]` — Gwet's ordinal weights, `w[k][l] = 1 - M(|k-l|)/M(q-1)` with `M(d) = d(d+1)/2`
  - `stats.gwet_ac(pairs: list[tuple[int, int]], q: int, weights: list[list[float]] | None = None) -> float` — two raters, categories `0..q-1`; `weights=None` = identity = AC1
  - `stats.krippendorff_alpha(units: list[list[int | None]], metric: str) -> float | None` — general coincidence-matrix α, any number of raters, `None` for missing; `metric` in `{"nominal", "ordinal"}`; `None` when expected disagreement is 0
  - `stats.cluster_bootstrap_ci(clusters: list[list], statistic: Callable[[list], float | None], reps: int, level: float, seed: int) -> dict` — resamples whole clusters with `numpy.random.default_rng(seed)`, returns `{"low": float | None, "high": float | None, "dropped": int}` (dropped = resamples where `statistic` returned None)

AC formulas (Gwet 2014, ch. 3 and 4; two raters, n units): `pa = mean(w[a][b])`; `π_k` = share of all 2n ratings in category k; `pe = sum(w) / (q(q-1)) · Σ π_k(1-π_k)`; `AC = (pa - pe)/(1 - pe)`; if `pe == 1` return 1.0 when pa == 1.

- [ ] **Step 1: Write the failing tests**

```python
def test_ac1_binary_hand_example():
    # 10 units: 7 both 1, 1 both 0, one (1,0), one (0,1): pa=0.8, pi=0.8/0.2, pe=0.32
    pairs = [(1, 1)] * 7 + [(0, 0)] + [(1, 0), (0, 1)]
    assert stats.gwet_ac(pairs, 2) == pytest.approx(12 / 17)

def test_ac2_identity_weights_equal_ac1():
    pairs = [(0, 0), (1, 2), (2, 2), (2, 1), (2, 2), (0, 1)]
    identity = [[1.0 if k == l else 0.0 for l in range(3)] for k in range(3)]
    assert stats.gwet_ac(pairs, 3, identity) == pytest.approx(stats.gwet_ac(pairs, 3))

def test_ordinal_weights_three_levels():
    assert stats.ordinal_weights(3) == [[1, 2/3, 0], [2/3, 1, 2/3], [0, 2/3, 1]]

def test_ac2_ordinal_counts_near_miss_partly():
    pairs = [(2, 2)] * 8 + [(2, 1), (1, 2)]
    w = stats.ordinal_weights(3)
    assert stats.gwet_ac(pairs, 3, w) > stats.gwet_ac(pairs, 3)

def test_ac_perfect_agreement_single_category_is_one():
    assert stats.gwet_ac([(1, 1)] * 5, 2) == 1.0

KRIPP_2011 = [  # Krippendorff (2011), Computing Krippendorff's alpha-reliability: 4 observers, 12 units
    [1, 1, None, 1], [2, 2, 3, 2], [3, 3, 3, 3], [3, 3, 3, 3], [2, 2, 2, 2], [1, 2, 3, 4],
    [4, 4, 4, 4], [1, 1, 2, 1], [2, 2, 2, 2], [None, 5, 5, 5], [None, None, 1, 1], [None, 3, None, None],
]

def test_alpha_reference_example():
    assert stats.krippendorff_alpha(KRIPP_2011, "nominal") == pytest.approx(0.743, abs=5e-4)
    assert stats.krippendorff_alpha(KRIPP_2011, "ordinal") == pytest.approx(0.815, abs=5e-4)

def test_alpha_binary_hand_example():
    units = [[1, 1]] * 7 + [[0, 0]] + [[1, 0], [0, 1]]
    assert stats.krippendorff_alpha(units, "nominal") == pytest.approx(1 - 0.2 / (128 / 380))

def test_alpha_undefined_without_variation():
    assert stats.krippendorff_alpha([[2, 2]] * 4, "ordinal") is None

def test_cluster_bootstrap_is_deterministic_and_counts_dropped():
    clusters = [[(1, 1)], [(0, 0)], [(1, 0)], [(1, 1)]]
    stat = lambda units: None if len({u for c in units for u in c}) == 1 else 0.5
    a = stats.cluster_bootstrap_ci(clusters, stat, 200, 0.95, 7)
    assert a == stats.cluster_bootstrap_ci(clusters, stat, 200, 0.95, 7)
    assert a["dropped"] > 0 and a["low"] == a["high"] == 0.5
```

(`statistic` receives the resampled list of clusters.) The Krippendorff reference values are 0.743 (nominal) and 0.815 (ordinal); if a correct-looking implementation disagrees, re-check the data and values against the paper before changing either.

- [ ] **Step 2: Run** `uv run pytest tests/test_stats.py -q` — Expected: FAIL (`AttributeError: module 'stats' has no attribute 'gwet_ac'`)
- [ ] **Step 3: Implement** the four functions and the config keys. α via the coincidence matrix over pairable values (units with ≥ 2 values); ordinal metric δ²(c,k) = (Σ_{g=c..k} n_g − (n_c + n_k)/2)² over the sorted category values.
- [ ] **Step 4: Run** `uv run pytest tests/test_stats.py -q` — Expected: PASS
- [ ] **Step 5: Commit** `git commit -m "feat(stats): Gwets AC1/AC2, Krippendorffs Alpha und Cluster-Bootstrap (ADR 0046)"`

---

### Task 2: Stratified draw (`second_rater.py --mode draw`)

**Files:**
- Modify: `src/config.py`
- Create: `src/second_rater.py`
- Test: `tests/test_second_rater.py`

**Interfaces:**
- Consumes: `freeze.require_frozen`, `run_log.append_step_run`, `run_log.latest_run`, `retrieve.read_rows`, `config.QUESTION_TYPES`, `config.QUESTION_CLASSES`
- Produces:
  - config: `SECOND_RATER_QUESTIONS = 12`, `SECOND_RATER_SEED = 20261022`, `SECOND_RATER_MAX_DRAWS = 100_000`, `SECOND_RATER_PSEUDONYM = "R2"`, `SECOND_RATER_DIR_NAME = "second_rater"`, `SECOND_RATER_DIR = DATA_EVAL / SECOND_RATER_DIR_NAME`, `SECOND_RATER_SAMPLE_FILE = DATA_EVAL / "second_rater_sample.csv"`, `SECOND_RATER_ENV = "SCORING_RATER"`
  - `SAMPLE_HEADER = ["question_id", "type", "difficulty"]`
  - `targets(counts: dict[str, int], n: int, rng: random.Random) -> dict[str, int]` — largest-remainder allocation, ties broken by `rng`
  - `draw(questions: list[dict], n: int, seed: int) -> list[dict]` — rows of `SAMPLE_HEADER`, sorted by `question_id`; marginal targets from the questions' own `type`/`difficulty` counts; rejection sampling (`rng.sample`) up to `SECOND_RATER_MAX_DRAWS`, else `ValueError("no draw meets both strata …")`
  - `paths(set_dir: Path | None) -> dict[str, Path]` — main: config files; pilot: `set_dir/second_rater_sample.csv`, `set_dir/second_rater/`, `set_dir/runs.jsonl`, plus the set's questions, items, sheet, checks, key points, scores files
  - `run_draw(p: dict, n: int, pilot: bool) -> list[dict]` — guards, write, run record step `second_rater_draw` (strategy `C1,C2,C3`, inputs `questions.csv`, outputs sample file) with extra fields `seed`, `questions`
  - CLI: `uv run python src/second_rater.py --mode {draw,export,close} [--set DIR] [--questions N]`; `--questions` only with `--set` (main always 12)

- [ ] **Step 1: Write the failing tests**

```python
def test_main_targets_meet_catalogue_quotas(catalogue48):  # fixture: 48 rows with config quotas
    rows = second_rater.draw(catalogue48, 12, 20261022)
    types = Counter(r["type"] for r in rows); classes = Counter(r["difficulty"] for r in rows)
    assert all(classes[c] == 3 for c in QUESTION_CLASSES)
    assert types["factual"] == types["procedural"] == types["conceptual"] == 3
    assert sorted([types["comparative"], types["limitation"]]) == [1, 2]

def test_draw_is_deterministic(catalogue48):
    assert second_rater.draw(catalogue48, 12, 1) == second_rater.draw(catalogue48, 12, 1)

def test_impossible_strata_abort(monkeypatch):
    # targets force type A and class X, but no question is A x X
    monkeypatch.setattr(second_rater, "targets", lambda counts, n, rng: {k: n if k in ("A", "X") else 0 for k in counts})
    monkeypatch.setattr(second_rater, "SECOND_RATER_MAX_DRAWS", 50)
    qs = [{"question_id": "Q1", "type": "A", "difficulty": "Y"}, {"question_id": "Q2", "type": "B", "difficulty": "X"}]
    with pytest.raises(ValueError, match="both strata"):
        second_rater.draw(qs, 1, 0)

def test_draw_refuses_unfrozen_main(...): ...          # RuntimeError from require_frozen
def test_draw_refuses_when_own_values_exist_main(...): # sheet with one value -> RuntimeError, no file written
def test_draw_only_warns_for_pilot(...):               # same situation with pilot=True -> writes, warning in capsys
def test_draw_never_overwrites(...):                   # sample exists -> FileExistsError
def test_draw_records_run(...):                        # latest_run(runs, "second_rater_draw", "C1,C2,C3") has seed and sample checksum
```

The five guard tests use the existing `pilot`/catalogue fixtures in `tests/conftest.py`; their assertions are as commented. `second_rater` imports `SECOND_RATER_MAX_DRAWS` as a module global so the test can lower it.

- [ ] **Step 2: Run** `uv run pytest tests/test_second_rater.py -q` — Expected: FAIL (module missing)
- [ ] **Step 3: Implement** config keys, `targets`, `draw`, `paths`, `run_draw`, CLI skeleton (export/close raise `NotImplementedError` until Tasks 3–4). Pilot `n` for `--set` is required via `--questions`.
- [ ] **Step 4: Run** `uv run pytest tests/test_second_rater.py -q` — Expected: PASS
- [ ] **Step 5: Commit** `git commit -m "feat(second-rater): geschichtete Ziehung der Fragen für die Zweitbewertung (ADR 0046)"`

---

### Task 3: R2 set (`--mode export`), app discovery and R2 mode

**Files:**
- Modify: `src/second_rater.py`, `src/scoring_store.py`, `app/catalogue_editor.py`
- Test: `tests/test_second_rater.py`, `tests/test_scoring_store.py`

**Interfaces:**
- Consumes: Task 2 `paths`, `run_log.require_run`, `run_log.append_scaffold_run`, `run_log.append_key_points_run`, `scoring_store.ScoringSet`, `evaluate_answers.SHEET_HEADER`
- Produces:
  - `run_export(p: dict, pilot: bool) -> Path` — writes `second_rater/` with `scoring_items.jsonl` (lines of the sampled questions, byte-identical, original order), `key_points.csv` (rows of the sampled questions), empty `scoring_sheet.csv` (one row per code, `SHEET_HEADER`), `runs.jsonl` with a `scaffold` record (`codes` = item count, checksum of the R2 item file) then a `key_points` record (checksums of R2 `key_points.csv` and item file, as `freeze_key_points` writes them); then a record `second_rater_export` in the set's own run log (inputs: sample, items, key points; outputs: R2 items, R2 key points)
  - `scoring_store.scoring_sets()` also yields `ScoringSet("Second rater", …)` for `SECOND_RATER_DIR` and `"Pilot: <rel>: second rater"` for `PILOT_DIR/**/second_rater/`; pilot `second_rater` folders are not yielded as plain pilot sets; R2 sets have no K0 set
  - `scoring_store.rater_mode() -> str | None` — `os.environ.get(SECOND_RATER_ENV)`; when it equals `SECOND_RATER_PSEUDONYM`, `scoring_sets()` returns only R2 sets
  - `app/catalogue_editor.py`: in R2 mode the navigation holds only the Scoring page

- [ ] **Step 1: Write the failing tests**

```python
def test_export_writes_blind_subset(pilot_scaffolded):  # set with frozen key points, no scores
    out = second_rater.run_export(paths, pilot=False)
    names = {f.name for f in out.iterdir()}
    assert names == {"scoring_items.jsonl", "key_points.csv", "scoring_sheet.csv", "runs.jsonl"}
    assert {json.loads(l)["question_id"] for l in (out / "scoring_items.jsonl").open()} == sampled_ids
    assert all(set(r) == set(SHEET_HEADER) and not r["correctness"] for r in read_csv(out / "scoring_sheet.csv", SHEET_HEADER))

def test_export_set_is_frozen_for_the_app(...):        # scoring_store.is_frozen(r2_set) is True
def test_export_refuses_without_frozen_key_points(...): # RuntimeError
def test_export_refuses_changed_sample(...):           # edit sample after draw -> RuntimeError (require_run)
def test_export_refuses_when_scores_exist_main(...):   # scores.csv present -> RuntimeError; pilot -> warning, writes
def test_export_refuses_existing_values(...):          # R2 sheet with a value -> FileExistsError
def test_scoring_sets_lists_second_rater(...):         # names include "Second rater"; pilot R2 folder not also listed as plain pilot set
def test_rater_mode_shows_only_r2(monkeypatch, ...):   # monkeypatch.setenv("SCORING_RATER", "R2") -> [s.name for s in scoring_sets()] == ["Second rater"]
```

- [ ] **Step 2: Run** `uv run pytest tests/test_second_rater.py tests/test_scoring_store.py -q` — Expected: FAIL
- [ ] **Step 3: Implement** `run_export`, the discovery and `rater_mode`, and the navigation switch in `app/catalogue_editor.py`.
- [ ] **Step 4: Run** the same command — Expected: PASS; then `uv run pytest -q` — Expected: all pass
- [ ] **Step 5: Commit** `git commit -m "feat(second-rater): Bewertungssatz für R2 und R2-Modus der App (ADR 0046)"`

---

### Task 4: Closing the R2 rating (`--mode close`)

**Files:**
- Modify: `src/second_rater.py`, `src/scoring_store.py`
- Test: `tests/test_second_rater.py`, `tests/test_scoring_store.py`

**Interfaces:**
- Consumes: `evaluate_answers.check_derived(sheet_file, checks_file, key_points_file, runs_file)`, `run_log.append_step_run`
- Produces:
  - `run_close(p: dict) -> dict` — requires every R2 code to have a checks row and a full sheet row, calls `check_derived` on the R2 folder files, then appends record step `second_rater_close` to the R2 `runs.jsonl` (strategy `C1,C2,C3`; inputs: R2 items and key points; outputs: R2 checks and sheet; extra fields `rater: "R2"`, `rules_version`)
  - `scoring_store.is_read_only(s)` is also True for an R2 set with a `second_rater_close` record

- [ ] **Step 1: Write the failing tests**

```python
def test_close_refuses_incomplete(...):    # one code without checks -> ValueError naming the code; no record
def test_close_refuses_hand_edited_score(...):  # sheet value differs from derived -> error from check_derived
def test_close_writes_record_and_locks(...):    # record has rater == "R2" and no other name field; is_read_only(r2_set) is True
def test_save_score_refused_after_close(...):   # scoring_store.save_score -> PermissionError
```

- [ ] **Step 2: Run** `uv run pytest tests/test_second_rater.py tests/test_scoring_store.py -q` — Expected: FAIL
- [ ] **Step 3: Implement** `run_close` and the read-only extension (error message names the close, not `scores.csv`).
- [ ] **Step 4: Run** the same command — Expected: PASS
- [ ] **Step 5: Commit** `git commit -m "feat(second-rater): Abschluss der Zweitbewertung mit Laufeintrag (ADR 0046)"`

---

### Task 5: Pairing, analysis and table `agreement`

**Files:**
- Create: `src/agreement.py`
- Modify: `src/analysis_data.py`, `src/report_tables.py`, `src/analyse.py`, `src/config.py`
- Test: `tests/test_agreement.py`, `tests/test_analysis_data.py`, `tests/test_report_tables.py`

**Interfaces:**
- Consumes: Task 1 functions and config; Task 4 record; `scoring_rules.CHECKS`, `config.RUBRIC_CRITERIA`, `report_tables.latex_table`, `NOT_DETERMINABLE`
- Produces:
  - config: `SECOND_RATER_DISAGREEMENTS_FILE_NAME = "second_rater_disagreements.csv"`
  - `agreement.ORDERED_CHECKS = {"grounded": ("none", "some", "all"), "hallucination": ("substantive", "minor", "none")}` (low → high)
  - `agreement.pair(first_checks: list[dict], first_sheet: list[dict], second_checks: list[dict], second_sheet: list[dict]) -> list[dict]` — one dict per R2 code: `code`, `question_id`, `checks: {name: (a, b)}`, `points: [(a, b), ...]`, `criteria: {name: (a, b)}`; raises `ValueError` if a code is missing in the first rating, the rules versions differ, or the number of point marks differs
  - `agreement.rows(paired: list[dict]) -> list[dict]` — in order: the eight checks, `Kernpunkte`, the five criteria; each `{"group", "label", "n", "agreement", "measure": "AC1"|"AC2", "ac", "ac_ci", "alpha", "alpha_ci", "dropped"}`; bootstrap clusters = questions; `alpha` None → reported as `NOT_DETERMINABLE`
  - `agreement.disagreements(paired) -> list[dict]` with header `["code", "question_id", "field", "first", "second"]`
  - `AnalysisData.second_rating: dict | None = None` (`{"checks", "sheet"}` of R2) loaded only when a `second_rater_close` record exists and `require_run` passes on its files; absent → note „Zweitbewertung fehlt oder ist nicht abgeschlossen“; changed after close → `RuntimeError`
  - `results["agreement"]` (None when absent); `"agreement.tex"` in `TABLE_NAMES` and `write_tables` (skipped when None); `analyse.run` writes `second_rater_disagreements.csv` into `out_dir` when present

- [ ] **Step 1: Write the failing tests**

```python
def test_pair_matches_codes_and_values(): ...          # two small ratings -> checks["direct"] == ("yes", "no") for the edited code
def test_pair_refuses_rules_version_mismatch(): ...    # ValueError, "rules_version"
def test_pair_refuses_point_count_mismatch(): ...      # ValueError naming the code
def test_rows_use_ac2_for_ordered_checks_and_criteria():
    labels = {r["label"]: r["measure"] for r in agreement.rows(paired)}
    assert labels["grounded"] == labels["hallucination"] == labels["correctness"] == "AC2"
    assert labels["direct"] == labels["Kernpunkte"] == "AC1"
def test_rows_alpha_not_determinable_when_constant(): ...  # all "yes" on both sides -> alpha None, ac == 1.0
def test_disagreements_list_has_no_strategy(): ...     # header exactly as above
def test_analysis_loads_closed_second_rating(...): ... # data.second_rating not None
def test_analysis_refuses_r2_changed_after_close(...): # edit R2 sheet -> RuntimeError
def test_analysis_without_r2_notes_it(...): ...        # second_rating None, note present
def test_agreement_table_iu_rules(...): ...            # title, \label{tab:agreement}, decimal comma, \source{Eigene Darstellung
def test_all_tables_are_written(...)                   # update: 13 tables when R2 present
```

Display labels in the table are German (`Prüffragen`, `Kernpunkte`, `Kriterien` as groups; check and criterion names as in `docs/reference/evaluation.md`); the note explains AC1/AC2, α ordinal, the CI method with reps from config, and dropped resamples when any.

- [ ] **Step 2: Run** `uv run pytest tests/test_agreement.py tests/test_analysis_data.py tests/test_report_tables.py -q` — Expected: FAIL
- [ ] **Step 3: Implement** `agreement.py`, the loading, the table and the CSV output.
- [ ] **Step 4: Run** `uv run pytest -q` — Expected: all pass; `uvx pre-commit run --all-files` — Expected: pass
- [ ] **Step 5: Commit** `git commit -m "feat(analysis): Übereinstimmung der Zweitbewertung als Anhangstabelle (ADR 0046)"`

---

### Task 6: Docs, ADR notes and pilot trial

**Files:**
- Modify: `docs/reference/evaluation.md` (§ Zweitbewertung: procedure, folder `data/evaluation/second_rater/`, R2 mode, push rule), `docs/reference/data-formats.md` (sample file, R2 folder, disagreements CSV, table count 13), `docs/reference/tooling.md` (`second_rater.py` row), `docs/reference/configuration.md` (new keys), `docs/plan.md#stand`, `docs/adr/0046-zweitbewertung.md` (Nachtrag 22.10.2026: AC2 with ordinal weights for `grounded` and `hallucination`, Jonas), `docs/adr/0033-*.md` (status note 22.10.2026: Renze & Guven (2024) is two authors and covers multiple-choice problem solving only; Lee et al. (2026) is an unreviewed preprint that shows reasoning models do not withstand distractors and longer reasoning goes with lower accuracy, without a comparison of reasoning on/off; the decision stays), `.serena/memories/` status memory
- Pilot data: `data/pilot/e2e/second_rater_sample.csv`, `data/pilot/e2e/second_rater/`, `data/pilot/e2e/runs.jsonl`

- [ ] **Step 1:** Update the docs listed above (German, existing style; ADR decisions unchanged, notes only).
- [ ] **Step 2: Pilot trial** `uv run python src/second_rater.py --mode draw --set data/pilot/e2e --questions 4` then `--mode export --set data/pilot/e2e` — Expected: both warn that the pilot is already scored, write the files; `SCORING_RATER=R2 uv run streamlit run app/catalogue_editor.py --server.address localhost` shows only „Pilot: e2e: second rater“ (check with playwright-cli, screenshot to scratchpad). Claude writes no R2 values.
- [ ] **Step 3: Run** `uv run pytest -q` and `uvx pre-commit run --all-files` — Expected: pass
- [ ] **Step 4: Commit** `git commit -m "docs: Zweitbewertung dokumentiert, Nachträge zu ADR 0046 und 0033, Probelauf Pilot e2e"`
