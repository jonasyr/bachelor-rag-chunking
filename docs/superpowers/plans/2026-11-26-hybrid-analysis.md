# Hybrid Scoring, Code (ADR 0051, package 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn Jonas' 72 ratings and the LLM's 144 + 48 ratings into the thesis' values as ADR 0051 decides: a mixed C1–C3 set with the rater per row, K0 rated by the LLM and compared with the LLM's C1–C3 values, two sensitivity analyses and human–LLM agreement on 72 answers.

**Architecture:** `llm_rater.py --control` rates the 48 K0 items with a K0 prompt (no excerpts, no `grounded`). `hybrid.py` gets two more modes: `summarise` merges Jonas' sheet (his 24 questions) with the LLM sheet (the other 24) into `scores.csv` with a `rater` column and writes the LLM-only `llm_rater/scores.csv`; `summarise-control` writes `scores_control.csv` from the LLM's K0 rating and compares it with the LLM's C1–C3. `analysis_data` detects the hybrid run by its `hybrid_summarise` record; `report_tables` then compares K0 against the LLM values, adds the sensitivity block and pairs the LLM with Jonas only on his 72 codes. Pilot sets and every non-hybrid path stay as they are.

**Tech Stack:** Python 3.13, pandas, pytest, uv; no new dependency.

**Spec:** `docs/adr/0051-hybride-bewertung.md`; the vault handoff "Übergabe an die Repo-Session", Paket 2.

## Global Constraints

- Only chunking differs between C1–C3; K0 answers and their closed-book prompt are untouched (AGENTS.md, ADR 0006, 0014, 0041).
- Every parameter (paths, file names, model settings, prompts) lives in `src/config.py`, documented in `docs/reference/configuration.md`.
- Strategy keys come from `config.STRATEGY_IDS` / `config.CONTROL_ANSWER_STRATEGIES`; formats exactly as in `docs/reference/data-formats.md` (update it in the same PR).
- Deterministic: stable sort orders (`question_id`, then `STRATEGY_IDS` order); no new randomness.
- Tests never call the OpenAI API (fake client as in `tests/test_llm_rater.py`); no real result values in tests or docs (blindness: Jonas has not finished scoring).
- Rater labels in files: `human` and `llm` (no names).
- Conventional Commits, English, no AI attribution; branch `feat/hybrid-analysis`, PR with Codex review, merge after Jonas approves.
- Never touch `data/evaluation/key_points.csv`, `scoring_key.csv` or any file on `run/hauptlauf`; the app's checkout stays on `run/hauptlauf` (work in the worktree).

## Review Focus

1. Jonas' sheet holds a value or checks on a question outside his 24, or misses one of his 72 codes → `hybrid.py --mode summarise` refuses and names the codes (tested in Task 3).
2. The LLM's files changed after its run record, or its run is missing → refuse, nothing written (Task 3, Task 4).
3. A pilot set or any run without a `hybrid_summarise` record → analysis exactly as before; `scores.csv` with the old header still reads (Task 5, Task 6).
4. `llm_rater.py --control` on K0 items from an older scaffold, or before `scaffold --control` ran → refuse before any API call (Task 1).
5. The LLM answers `declines = yes` for a K0 item → the fixed K0 values (no `grounded`) and a valid row (Task 1).

---

### Task 1: `llm_rater.py --control` rates K0

**Files:**
- Modify: `src/config.py` (LLM rater block), `src/llm_rater.py`
- Test: `tests/test_llm_rater.py`

**Interfaces:**
- Consumes: `scoring_rules.checks_for(control)`, `declined(..., control=True)`, `validate(..., control=True)`, `derive_control`, `to_row(..., control=True)`; `control_k0.CONTROL_SHEET_HEADER`, `control_k0.CODE_SUFFIX`; the K0 scaffold record (`append_scaffold_run(CODE_SUFFIX, …)`, step `scaffold`, strategy `K0`).
- Produces:
  - config: `LLM_RATER_CONTROL_SYSTEM_PROMPT`, `LLM_RATER_CONTROL_USER_TEMPLATE` (no excerpts section), `LLM_RATER_CONTROL_JOURNAL_FILE_NAME = "llm_rater_control_journal.jsonl"`.
  - `llm_rater.CONTROL_STEP = "llm_rater_control"`.
  - `paths(set_dir)` additionally returns `control_items_file` (`SCORING_ITEMS_CONTROL_FILE` or the set's).
  - `schema(n_points, control=False)`, `response_format(n_points, control=False)`, `messages(item, key_points, control=False)`, `to_checks(parsed, n_points, control=False)`, `prompts_sha256(control=False)`.
  - `run(p, client=None, control=False) -> dict`; with `control` it reads `control_items_file`, writes `out_dir/scoring_checks_control.csv` (`rules.checks_header(True)`) and `out_dir/scoring_sheet_control.csv` (`CONTROL_SHEET_HEADER`, values by `derive_control`, empty notes), journals to `LLM_RATER_CONTROL_JOURNAL_FILE_NAME`, appends a record with step `CONTROL_STEP`, strategy `K0`, always the whole K0 set (scope does not apply).
  - CLI: `--control`.

- [ ] **Step 1: Write the failing tests** (reuse the module's fake client and fixtures)
  - `test_control_schema_has_no_grounded`: `"grounded" not in schema(2, control=True)["properties"]`; `set(schema(2, control=True)["required"]) == {"points", *rules.CONTROL_CHECKS, "reason"}`.
  - `test_control_messages_have_no_excerpts`: the user message of a K0 item contains `"## Reference answer"` and `"## Answer"` and not `"## Excerpts"`; the system message is `LLM_RATER_CONTROL_SYSTEM_PROMPT`.
  - `test_control_prompt_uses_k0_wording`: `RUBRIC_CONTROL_QUESTIONS["hallucination"]` and `["declines"]` are in `LLM_RATER_CONTROL_SYSTEM_PROMPT`; `RUBRIC_CHECK_QUESTIONS["grounded"]` is not.
  - `test_control_declines_takes_fixed_values`: `to_checks({declines: "yes", …, reason: "x"}, 2, control=True)` equals `rules.declined(…, 2, control=True)` without `reason`.
  - `test_run_control_writes_k0_files_and_record`: after a K0 scaffold in a tmp set, `run(p, fake, control=True)` writes both control files in code order, sheet values equal `derive_control` of the fake answers, the record has `step == "llm_rater_control"`, `strategy == "K0"`, `answers == n_k0`, and `outputs_sha256` holds the two files and the journal.
  - `test_run_control_needs_k0_scaffold`: without the K0 items file or its scaffold record → `RuntimeError`, fake client never called.
  - `test_run_control_refuses_changed_items`: K0 items edited after the scaffold record → `RuntimeError` before any call.
  - `test_c1_c3_run_unchanged`: the existing C1–C3 tests pass unchanged (`prompts_sha256()` without `control` is the same value as before; assert against the value computed from the unchanged prompts).

- [ ] **Step 2: Run them, verify they fail**
  Run: `uv run pytest tests/test_llm_rater.py -q`
  Expected: the new tests FAIL (unknown keyword `control`, missing config names).

- [ ] **Step 3: Implement**
  - Config: build `LLM_RATER_CONTROL_SYSTEM_PROMPT` like the C1–C3 one, but from `RUBRIC_CONTROL_QUESTIONS` without `grounded`, first line "You score one answer of a language model given without any excerpts …, from the question, the reference answer and the key points shown"; last rule "If declines is yes, … core_wrong, other_error and hallucination are not asked: mark every key point missing and answer no, no, none." `LLM_RATER_CONTROL_USER_TEMPLATE` = the C1–C3 template without the excerpts section.
  - `run(control=True)`: guard with `require_run(runs_file, "scaffold", CODE_SUFFIX, [], [control_items_file])`; inputs hashed: control items file and key points; record carries `"control": True` next to `llm_rater_settings("all")`. Keep one code path with `control` switches; no copy of `run`.

- [ ] **Step 4: Run, verify pass**
  Run: `uv run pytest tests/test_llm_rater.py -q` → all PASS.

- [ ] **Step 5: Commit**
  `git commit -m "feat(llm-rater): rate the control K0 without excerpts (ADR 0051)"`

---

### Task 2: Reusable pieces in `evaluate_answers.py`

**Files:**
- Modify: `src/evaluate_answers.py`
- Test: `tests/test_evaluate_answers.py`

**Interfaces:**
- Produces:
  - `HYBRID_SCORES_HEADER = [*SCORES_HEADER, "rater"]`.
  - `read_scores(path: Path) -> list[dict]`: rows of a scores file with `SCORES_HEADER` or `HYBRID_SCORES_HEADER`, always without `rater` (so readers that need only values keep working); `ValueError` for any other header.
  - `check_derived(sheet_file, checks_file, key_points_file, runs_file, codes: set[str] | None = None) -> None`: with `codes` only those sheet rows are checked and checks rows outside `codes` are an error ("… has checks outside the codes to summarise"); `None` = today's behaviour.
  - `unblind_rows(sheet: list[dict], key: list[dict], qids: list[str], where: Path) -> list[dict]`: the body of today's `unblind` on rows; `unblind` becomes a thin wrapper reading the files.

- [ ] **Step 1: Failing tests**
  - `test_read_scores_accepts_both_headers`: a file with `HYBRID_SCORES_HEADER` returns rows whose keys are exactly `SCORES_HEADER`; an old file returns the same rows.
  - `test_read_scores_rejects_other_header` → `ValueError`.
  - `test_check_derived_limited_to_codes`: sheet with 6 codes, checks and values for 3 of them, `codes` = those 3 → passes; same with `codes=None` → `ValueError` "no checks for".
  - `test_check_derived_codes_rejects_checks_outside`: a checks row for a code outside `codes` → `ValueError`.
  - `test_unblind_rows_matches_unblind`: same output as `unblind` on the same files.

- [ ] **Step 2: Run, verify fail** — `uv run pytest tests/test_evaluate_answers.py -q`.

- [ ] **Step 3: Implement** the three functions; switch `control_k0.scaffold_control` and `control_k0.summarise_control` to `read_scores` for `scores_file` (they need only question IDs and values).

- [ ] **Step 4: Run** `uv run pytest tests/test_evaluate_answers.py tests/test_control_k0.py -q` → PASS.

- [ ] **Step 5: Commit** `git commit -m "refactor(scoring): reusable unblinding and checks for a subset of codes"`

---

### Task 3: `hybrid.py --mode summarise` writes the mixed set

**Files:**
- Modify: `src/config.py` (`LLM_RATER_SCORES_FILE = LLM_RATER_DIR / SCORES_FILE.name`), `src/hybrid.py`
- Test: `tests/test_hybrid.py`

**Interfaces:**
- Consumes: Task 2 (`check_derived(codes=…)`, `unblind_rows`, `HYBRID_SCORES_HEADER`); `llm_rater.STEP`, `llm_rater.paths`; `hybrid.human_questions`, `DRAW_STEP`; `second_rater.DRAW_STEP`.
- Produces:
  - `SUMMARISE_STEP = "hybrid_summarise"`, `RATER_HUMAN = "human"`, `RATER_LLM = "llm"`.
  - `paths(set_dir)` additionally returns `key_file`, `llm_dir`, `llm_sheet_file`, `llm_checks_file`, `llm_scores_file`.
  - `run_summarise(p: dict) -> dict[str, int]`: returns `{"human": 72, "llm": 72}` (answer counts per rater).
  - Writes `scores.csv` (`HYBRID_SCORES_HEADER`, (question_id, strategy) order, `rater` = `human` for Jonas' 24 questions, `llm` for the rest) and `llm_rater/scores.csv` (`SCORES_HEADER`, all answers, LLM values). Record `hybrid_summarise`, strategy `C1,C2,C3`, inputs: own sheet, own checks, key, key points, LLM sheet, LLM checks, R2 sample, extra sample; outputs: both scores files.

- [ ] **Step 1: Failing tests** (tmp set built with the existing `test_hybrid.py` / `test_llm_rater.py` fixtures; small catalogue, e.g. 4 questions with 2 human)
  - `test_summarise_mixes_by_question`: every row of `scores.csv` for a human question equals Jonas' unblinded values and has `rater == "human"`; every other row equals the LLM's and has `rater == "llm"`; row order (question_id, STRATEGY_IDS).
  - `test_summarise_writes_llm_only_scores`: `llm_rater/scores.csv` holds all answers with the LLM values and `SCORES_HEADER`.
  - `test_summarise_logs_record`: record `hybrid_summarise` with the eight inputs and two outputs hashed.
  - `test_summarise_refuses_values_outside_human_questions`: a filled sheet row or a checks row on a non-human question → `RuntimeError` naming the code; no file written.
  - `test_summarise_refuses_missing_human_code`: one of Jonas' codes unscored → `ValueError` (from `unblind_rows`/`check_derived`); no file written.
  - `test_summarise_needs_llm_run`: no `llm_rater` record, or LLM sheet edited after it → `RuntimeError`.
  - `test_summarise_needs_both_draws`: extra sample missing or changed after `hybrid_draw` → `RuntimeError`.
  - `test_summarise_needs_llm_scope_all`: an `llm_rater` record with scope `sample` → `RuntimeError` ("the LLM must rate every answer, ADR 0051").
  - `test_cli_summarise`: `main(["--mode", "summarise", "--set", dir])` prints the two counts.

- [ ] **Step 2: Run, verify fail** — `uv run pytest tests/test_hybrid.py -q`.

- [ ] **Step 3: Implement** `run_summarise`:
  1. `require_frozen(...)` as in `run_draw`; `require_run` on both draws (`second_rater.DRAW_STEP` with the R2 sample, `DRAW_STEP` with the extra sample).
  2. `require_run(runs, llm_rater.STEP, STRATEGY, [items, key points], [llm sheet, llm checks])`, then its record's `scope == "all"`.
  3. Human codes = sheet codes whose question is in `human_questions(p)`; `questions_with_values(...) - human` non-empty → `RuntimeError`.
  4. `check_derived(own sheet, own checks, key points, runs, codes=human codes)`; `check_derived(llm sheet, llm checks, key points, runs)`.
  5. Merged sheet rows = own rows for human codes + LLM rows for the others, in own-sheet order; `unblind_rows(merged, key, all qids, …)`; add `rater`. LLM-only: `unblind_rows(llm sheet, key, all qids, …)`.
  6. Write both files, then `append_step_run(SUMMARISE_STEP, …)`.
  CLI: `--mode` choices `draw`, `summarise`.

- [ ] **Step 4: Run** `uv run pytest tests/test_hybrid.py -q` → PASS.

- [ ] **Step 5: Commit** `git commit -m "feat(hybrid): merge Jonas' and the LLM's values with the rater per row"`

---

### Task 4: `hybrid.py --mode summarise-control` scores K0 from the LLM

**Files:**
- Modify: `src/hybrid.py`, `src/control_k0.py` (only if a parameter is missing)
- Test: `tests/test_hybrid.py`

**Interfaces:**
- Consumes: Task 1 outputs (`llm_rater/scoring_sheet_control.csv`, `scoring_checks_control.csv`, record `llm_rater_control`), Task 3 (`llm_scores_file`, record `hybrid_summarise`); `control_k0.summarise_control(...)`, `control_k0.print_control_summary`.
- Produces: `run_summarise_control(p: dict) -> dict[tuple, dict]` (the summary of `summarise_control`); CLI mode `summarise-control`. `scores_control.csv` as today (`CONTROL_SCORES_HEADER`), its `summarise_control` record lists the LLM K0 sheet and checks and `llm_rater/scores.csv` as inputs.

- [ ] **Step 1: Failing tests**
  - `test_summarise_control_uses_llm_values`: K0 rows of `scores_control.csv` equal `derive_control` of the LLM's K0 checks; the C1–C3 side of the returned summary equals the means of `llm_rater/scores.csv` on the four criteria (not the mixed `scores.csv`).
  - `test_summarise_control_needs_llm_control_run`: no `llm_rater_control` record, or its sheet edited after it → `RuntimeError`.
  - `test_summarise_control_needs_hybrid_summarise`: no `hybrid_summarise` record → `RuntimeError`.
  - `test_scaffold_control_reads_mixed_scores`: `control_k0.scaffold_control` on a `scores.csv` with `HYBRID_SCORES_HEADER` writes the K0 items for its questions.

- [ ] **Step 2: Run, verify fail** — `uv run pytest tests/test_hybrid.py -q`.

- [ ] **Step 3: Implement**: guards via `require_run`, then `summarise_control(…, scores_file=llm_scores_file, sheet_file=llm K0 sheet, checks_file=llm K0 checks, items_file=K0 items, control_scores_file=…, generation_runs_file=runs)`.

- [ ] **Step 4: Run** `uv run pytest tests/test_hybrid.py tests/test_control_k0.py -q` → PASS.

- [ ] **Step 5: Commit** `git commit -m "feat(hybrid): score K0 from the LLM and compare it with the LLM's C1-C3"`

---

### Task 5: `analysis_data` loads the hybrid run

**Files:**
- Modify: `src/analysis_data.py`
- Test: `tests/test_analysis_data.py`

**Interfaces:**
- Consumes: Task 3 (`hybrid.SUMMARISE_STEP`, `HYBRID_SCORES_HEADER`, `llm_scores_file`, `RATER_HUMAN`); `hybrid.human_questions`.
- Produces on `AnalysisData` (new fields, default `None`):
  - `scores_llm: pd.DataFrame | None` — `llm_rater/scores.csv` (all 144, LLM values).
  - `human_questions: list[str] | None` — sorted IDs of Jonas' 24 questions.
  - In a hybrid run `scores` has a `rater` column (`human`/`llm`).
  - `llm_rating["paired"]` holds only the codes of `human_questions` in a hybrid run.
- `main_paths()` / `set_paths()` add `llm_scores_file`, `hybrid_extra_file`, `second_rater_sample_file` (if not already present).

- [ ] **Step 1: Failing tests**
  - `test_load_hybrid_run`: with a `hybrid_summarise` record, `scores` matches `scores.csv` incl. `rater`, `scores_llm` the LLM file, `human_questions` the 24 IDs, and `scores` is checked against the `hybrid_summarise` record (a later edit of `scores.csv` → `RuntimeError`).
  - `test_load_hybrid_pairs_llm_on_human_codes`: `len(llm_rating["paired"]) == 3 * len(human_questions)` and all paired codes belong to human questions.
  - `test_load_hybrid_needs_llm_rating`: hybrid record present but no `llm_rater` record → `RuntimeError` (no silent note).
  - `test_load_non_hybrid_unchanged`: the existing fixtures (no hybrid record) load as before; `scores_llm is None`, `human_questions is None`, no `rater` column.

- [ ] **Step 2: Run, verify fail** — `uv run pytest tests/test_analysis_data.py -q`.

- [ ] **Step 3: Implement**: detect hybrid by `latest_run(gen_runs, hybrid.SUMMARISE_STEP, EXPERIMENT)`; then `_checked` against that step, read with `HYBRID_SCORES_HEADER`, load `scores_llm`, and in `_load_llm_rating` filter the LLM's checks and sheet to the human codes before `agreement.pair`.

- [ ] **Step 4: Run** `uv run pytest tests/test_analysis_data.py -q` → PASS.

- [ ] **Step 5: Commit** `git commit -m "feat(analysis): load the mixed set, the LLM-only set and Jonas' questions"`

---

### Task 6: Results, sensitivity analyses and tables

**Files:**
- Modify: `src/report_tables.py`, `src/analyse.py` (only if the disagreements list needs it)
- Test: `tests/test_report_tables.py` (or the existing analysis test module), `tests/test_analyse.py`

**Interfaces:**
- Consumes: Task 5 fields.
- Produces in `build_results` (only when `data.human_questions` is not `None`; otherwise the key is `None`):
  - `results["hybrid"] = {"n_human_questions", "n_llm_questions", "raters": {"human": n_answers, "llm": n_answers}, "sensitivity": {"human": block, "llm": block}}`, where `block = {"n_questions", "means": {strategy: {criterion…, "total_score"}}, "test": stats.confirmatory({"total_score": wide}, alpha)["total_score"], "differences": {pair: mean_diff_ci}}`; `human` = mixed `scores` on `human_questions`, `llm` = `scores_llm` on all questions.
  - K0 comparison (`results["control_k0"]`, and `answer_means` used for it) takes the C1–C3 side from `scores_llm` in a hybrid run; `results["answers"]["means"]` for C1–C3 stays the mixed set.
  - Table `hybrid_sensitivity.tex`: rows Gesamtwert per strategy for gemischt / nur Jonas / nur LLM, plus Friedman p and n; skipped with a note when not hybrid.
  - `analysis.json` carries `hybrid`.

- [ ] **Step 1: Failing tests**
  - `test_hybrid_sensitivity_blocks`: on a small hybrid fixture, `results["hybrid"]["sensitivity"]["human"]["n_questions"] == len(human_questions)`, its means equal pandas means of the human rows, `["llm"]` means equal `scores_llm` means.
  - `test_hybrid_k0_uses_llm_side`: `control_k0[s]["diff"]["total_four"]` equals the LLM C1–C3 mean minus the K0 mean (construct values where mixed and LLM differ).
  - `test_non_hybrid_results_unchanged`: `results["hybrid"] is None` and every other key equals the result before the change on the existing fixture.
  - `test_write_hybrid_sensitivity_table`: `hybrid_sensitivity.tex` is written for a hybrid run and listed as skipped otherwise.

- [ ] **Step 2: Run, verify fail** — `uv run pytest tests -q -k "hybrid or report or analyse"`.

- [ ] **Step 3: Implement**: factor the C1–C3 means, test and differences of the total into one helper `_total_block(frame, qids, alpha) -> dict` used for both sensitivity blocks; no change to the confirmatory family of the main analysis.

- [ ] **Step 4: Run the full suite** `uv run pytest -q` and `uvx pre-commit run --all-files` → PASS.

- [ ] **Step 5: Commit** `git commit -m "feat(analysis): sensitivity analyses and K0 comparison of the hybrid scoring"`

---

### Task 7: Documentation

**Files:**
- Modify: `docs/how-to/run-the-experiment.md` (steps 6–8: exact commands `llm_rater.py`, `hybrid.py --mode summarise`, `evaluate_answers.py --mode scaffold --control`, `llm_rater.py --control`, `hybrid.py --mode summarise-control`, then RAGAS and `analyse.py`; what to commit after each), `docs/reference/data-formats.md` (`scores.csv` with `rater` in the hybrid run, `llm_rater/scores.csv`, `llm_rater/scoring_*_control.csv`, the K0 journal, run steps `hybrid_summarise` and `llm_rater_control`), `docs/reference/configuration.md` (new keys), `docs/reference/evaluation.md` (hybrid section: where each value comes from), `docs/reference/tooling.md` (new modes and `--control`), `docs/reference/experiment-record.md` (hybrid procedure; numbers left for package 3), `docs/plan.md` (backlog item 3(b) done), `data/evaluation/scoring_cheatsheet.md` is **not** touched here (run branch only), `.serena/memories/evaluation.md` if a link changes.

- [ ] **Step 1:** Update the docs above; no result values.
- [ ] **Step 2:** Run the `loadout:docs-sync` skill and fix what it finds; `uvx pre-commit run --all-files` → PASS.
- [ ] **Step 3: Commit** `git commit -m "docs: hybrid scoring commands, formats and record (ADR 0051)"`

---

## After the plan

Push, open the PR, `@codex review`, fix until CI and Codex are clean, merge after Jonas approves, then merge `main` into `run/hauptlauf`. Package 3 (the runs) starts only after Jonas' 72 ratings are done.
