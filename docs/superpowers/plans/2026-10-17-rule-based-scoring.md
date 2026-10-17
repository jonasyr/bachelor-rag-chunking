# Rule-based scoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The five rubric scores follow from factual checks through fixed rules; key points are written and frozen before scoring.

**Architecture:** A pure rules module (`src/scoring_rules.py`) turns checks into the five scores. `src/scoring_store.py`
gains key points (write, freeze, verify) and saves checks plus derived scores. `evaluate_answers.py --mode summarise`
verifies the sheet against the checks. The Scoring page gets two steps: Key points and Score.

**Tech Stack:** Python 3.11+, Streamlit 1.58 (AppTest), pytest, ruff, uv.

**Spec:** `docs/superpowers/specs/2026-10-17-rule-based-scoring-design.md`

## Global Constraints

- Blind as before (ADR 0032, 0034): no strategy, no chunk ID, the key stays closed; `scoring_store.py` and the page never mention `scoring_key`/`SCORING_KEY`.
- Key points are ground truth: written by Jonas only; the agent never writes or suggests key point text, also not in real data files (test fixtures with dummy text are fine).
- The key-point step never shows a generated answer or an excerpt.
- `scoring_sheet.csv` keeps its format (`evaluate_answers.SHEET_HEADER`).
- No manual override of a derived score.
- All thresholds in `src/config.py`: `KEY_POINTS_FILE`, `KEY_POINTS_MAX = 4`, `SCORING_CHECKS_FILE`, `RUBRIC_COMPLETENESS_PARTIAL = 0.5`, `RUBRIC_RULES_VERSION = "2026-10-17"`.
- English UI, sentence case; light and dark; 320, 768 and 1280 px.
- Tests never call the OpenAI API. Conventional Commits with German subject, no AI attribution. Plain branch `feat/rule-scoring` in the main checkout (no worktree).
- Code exploration and edits with Serena / codebase-memory where they fit (user requirement).

## Review Focus

1. Hand edit of `key_points.csv` after the freeze (adding a point, changing text): every score save must be refused with a message naming the file.
2. A question whose point count differs from the stored checks of a code (e.g. key points file restored from an older commit): saving or summarising must fail loudly, never mis-derive completeness. Covered by `validate` length check (Task 1) and the store test in Task 3.
3. Declining answer saved, then reopened and switched to `declines = no`: the skipped checks must be asked again (no silent reuse of the defaults as answers). Page test in Task 5.
4. Sheet row edited by hand after scoring (score changed): `summarise` refuses it. Test in Task 4.
5. Freeze clicked twice / freeze with a question missing points: refused, no duplicate record. Test in Task 2.

---

### Task 1: Rules module and config keys

**Files:**
- Modify: `src/config.py` (after `SCORING_ITEMS_FILE` line 49; after `RUBRIC_MAX_SCORE` line 256)
- Create: `src/scoring_rules.py`
- Test: `tests/test_scoring_rules.py`

**Interfaces:**
- Produces:
  - `scoring_rules.POINT_MARKS: tuple[str, str] = ("covered", "missing")`
  - `scoring_rules.CHECKS: dict[str, tuple[str, ...]]` (form order after the points)
  - `scoring_rules.SKIPPED_WHEN_DECLINING: dict[str, str]`
  - `scoring_rules.CHECKS_HEADER: list[str]`
  - `scoring_rules.declined(checks: dict, n_points: int) -> dict` — fills skipped values when `declines == "yes"`
  - `scoring_rules.validate(checks: dict, n_points: int) -> None` (raises `ValueError`)
  - `scoring_rules.derive(checks: dict) -> dict[str, int]` (keys = `RUBRIC_CRITERIA`)
  - `scoring_rules.to_row(code: str, checks: dict) -> dict[str, str]`, `scoring_rules.from_row(row: dict) -> tuple[str, dict]` (rules_version, checks)
  - A `checks` dict: `{"points": ["covered", "missing", ...], "declines": "no", "core_wrong": "no", ...}`

- [ ] **Step 1: Add the config keys**

In `src/config.py` after `SCORING_ITEMS_FILE = ...`:

```python
KEY_POINTS_FILE = DATA_EVAL / "key_points.csv"  # key points per question, frozen before scoring (D35)
SCORING_CHECKS_FILE = DATA_EVAL / "scoring_checks.csv"  # checks behind every derived score (D35)
```

After `RUBRIC_MAX_SCORE = 2`:

```python
KEY_POINTS_MAX = 4  # key points per question; point 1 is the core point (D35)
RUBRIC_COMPLETENESS_PARTIAL = 0.5  # share of covered key points for completeness 1 (D35)
RUBRIC_RULES_VERSION = "2026-10-17"  # version of the check-to-score rules in src/scoring_rules.py (D35)
```

- [ ] **Step 2: Write the failing tests**

`tests/test_scoring_rules.py`:

```python
import pytest

import scoring_rules as rules
from config import RUBRIC_COMPLETENESS_PARTIAL, RUBRIC_CRITERIA, RUBRIC_RULES_VERSION

GOOD = {
    "points": ["covered", "covered"],
    "declines": "no",
    "core_wrong": "no",
    "other_error": "no",
    "grounded": "all",
    "hallucination": "none",
    "answers_question": "yes",
    "direct": "yes",
    "wordy": "no",
}


def checks(**changed):
    return GOOD | changed


def test_a_flawless_answer_scores_two_everywhere():
    assert rules.derive(GOOD) == dict.fromkeys(RUBRIC_CRITERIA, 2)


@pytest.mark.parametrize(
    ("changed", "expected"),
    [
        ({"core_wrong": "yes"}, 0),
        ({"core_wrong": "yes", "other_error": "yes"}, 0),
        ({"other_error": "yes"}, 1),
        ({}, 2),
    ],
)
def test_correctness(changed, expected):
    assert rules.derive(checks(**changed))["correctness"] == expected


@pytest.mark.parametrize(
    ("points", "expected"),
    [
        (["covered"], 2),
        (["missing"], 0),
        (["covered", "missing"], 1),  # 1/2 = threshold
        (["missing", "missing"], 0),
        (["covered", "covered", "missing"], 1),
        (["covered", "missing", "missing"], 0),
        (["covered", "covered", "missing", "missing"], 1),
        (["covered", "missing", "missing", "missing"], 0),
        (["covered"] * 4, 2),
    ],
)
def test_completeness_by_share_of_covered_points(points, expected):
    assert RUBRIC_COMPLETENESS_PARTIAL == 0.5
    assert rules.derive(checks(points=points))["completeness"] == expected


@pytest.mark.parametrize(("value", "expected"), [("all", 2), ("some", 1), ("none", 0)])
def test_groundedness(value, expected):
    assert rules.derive(checks(grounded=value))["groundedness"] == expected


@pytest.mark.parametrize(("value", "expected"), [("none", 2), ("minor", 1), ("substantive", 0)])
def test_no_hallucination(value, expected):
    assert rules.derive(checks(hallucination=value))["no_hallucination"] == expected


@pytest.mark.parametrize(
    ("changed", "expected"),
    [
        ({}, 2),
        ({"direct": "no"}, 1),
        ({"wordy": "yes"}, 1),
        ({"answers_question": "no"}, 0),
        ({"answers_question": "no", "direct": "yes", "wordy": "no"}, 0),
    ],
)
def test_clarity(changed, expected):
    assert rules.derive(checks(**changed))["clarity"] == expected


def test_a_declining_answer_fills_the_skipped_checks_and_scores_as_the_spec_says():
    asked = {"declines": "yes", "answers_question": "yes", "direct": "yes", "wordy": "no"}
    full = rules.declined(asked, n_points=3)
    assert full["points"] == ["missing"] * 3
    assert {k: full[k] for k in rules.SKIPPED_WHEN_DECLINING} == rules.SKIPPED_WHEN_DECLINING
    rules.validate(full, 3)
    assert rules.derive(full) == {
        "correctness": 1,
        "completeness": 0,
        "groundedness": 2,
        "no_hallucination": 2,
        "clarity": 2,
    }


def test_declined_leaves_an_answering_answer_alone():
    assert rules.declined(GOOD, n_points=2) == GOOD


@pytest.mark.parametrize(
    ("bad", "message"),
    [
        (checks(grounded="most"), "grounded"),
        (checks(points=["covered", "partly"]), "point"),
        (checks(points=["covered"]), "2 key points"),
        ({k: v for k, v in GOOD.items() if k != "wordy"}, "wordy"),
        (checks(extra="x"), "extra"),
        (checks(declines="yes"), "declining"),  # skipped checks not at their defaults
    ],
)
def test_validate_rejects(bad, message):
    with pytest.raises(ValueError, match=message):
        rules.validate(bad, 2)


def test_rows_round_trip_with_the_rules_version():
    row = rules.to_row("H01-A", checks(points=["covered", "missing"]))
    assert list(row) == rules.CHECKS_HEADER
    assert row["points"] == "covered;missing" and row["rules_version"] == RUBRIC_RULES_VERSION
    assert rules.from_row(row) == (RUBRIC_RULES_VERSION, checks(points=["covered", "missing"]))
```

- [ ] **Step 3: Run them to verify they fail**

Run: `uv run pytest tests/test_scoring_rules.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'scoring_rules'`

- [ ] **Step 4: Implement `src/scoring_rules.py`**

```python
"""Rule-based rubric scoring (ADR 0035): factual checks per answer -> the five scores 0-2.

The rater answers checks with fixed options; derive() turns them into the five criteria of
config.RUBRIC_CRITERIA by the rule table in docs/reference/evaluation.md. Same checks, same
scores; config.RUBRIC_RULES_VERSION names the version of these rules.
"""

from config import RUBRIC_COMPLETENESS_PARTIAL, RUBRIC_CRITERIA, RUBRIC_RULES_VERSION

POINT_MARKS = ("covered", "missing")
YES_NO = ("yes", "no")
CHECKS = {  # in form order, after the key points
    "declines": YES_NO,
    "core_wrong": YES_NO,
    "other_error": YES_NO,
    "grounded": ("all", "some", "none"),
    "hallucination": ("none", "minor", "substantive"),
    "answers_question": YES_NO,
    "direct": YES_NO,
    "wordy": YES_NO,
}
# a declining answer gives no content to check: these are not asked and stored as below
SKIPPED_WHEN_DECLINING = {
    "core_wrong": "no",
    "other_error": "no",
    "grounded": "all",
    "hallucination": "none",
}
CHECKS_HEADER = ["code", "rules_version", "points", *CHECKS]
LEVEL = {"all": 2, "some": 1, "none": 0}
HALLUCINATION = {"none": 2, "minor": 1, "substantive": 0}


def declined(checks: dict, n_points: int) -> dict:
    """With declines = yes: every key point missing and the skipped checks at their values."""
    if checks.get("declines") != "yes":
        return checks
    return checks | {"points": ["missing"] * n_points} | SKIPPED_WHEN_DECLINING


def validate(checks: dict, n_points: int) -> None:
    expected = {"points", *CHECKS}
    if set(checks) != expected:
        wrong = sorted(set(checks) ^ expected)
        raise ValueError(f"checks must be exactly points and {list(CHECKS)}; differs in {wrong}")
    points = checks["points"]
    if len(points) != n_points:
        raise ValueError(f"the question has {n_points} key points, the checks mark {len(points)}")
    for mark in points:
        if mark not in POINT_MARKS:
            raise ValueError(f"key point mark {mark!r} is not one of {POINT_MARKS}")
    for check, options in CHECKS.items():
        if checks[check] not in options:
            raise ValueError(f"{check} is {checks[check]!r}, not one of {options}")
    if checks["declines"] == "yes" and checks != declined(checks, n_points):
        raise ValueError("a declining answer has every key point missing and the skipped checks at "
                         f"{SKIPPED_WHEN_DECLINING}")


def derive(checks: dict) -> dict[str, int]:
    """The five criteria from valid checks (the rule table of ADR 0035)."""
    points = checks["points"]
    share = points.count("covered") / len(points)
    if checks["core_wrong"] == "yes":
        correctness = 0
    elif checks["other_error"] == "yes" or checks["declines"] == "yes":
        correctness = 1
    else:
        correctness = 2
    completeness = 2 if share == 1 else 1 if share >= RUBRIC_COMPLETENESS_PARTIAL else 0
    if checks["answers_question"] == "no":
        clarity = 0
    elif checks["direct"] == "yes" and checks["wordy"] == "no":
        clarity = 2
    else:
        clarity = 1
    values = [
        correctness,
        completeness,
        LEVEL[checks["grounded"]],
        HALLUCINATION[checks["hallucination"]],
        clarity,
    ]
    return dict(zip(RUBRIC_CRITERIA, values, strict=True))


def to_row(code: str, checks: dict) -> dict[str, str]:
    return (
        {"code": code, "rules_version": RUBRIC_RULES_VERSION, "points": ";".join(checks["points"])}
        | {c: checks[c] for c in CHECKS}
    )


def from_row(row: dict) -> tuple[str, dict]:
    checks = {"points": row["points"].split(";") if row["points"] else []}
    return row["rules_version"], checks | {c: row[c] for c in CHECKS}
```

`RUBRIC_CRITERIA` order is `correctness, completeness, groundedness, no_hallucination, clarity` (config line 255); the
`values` list follows it.

- [ ] **Step 5: Run the tests and lint**

Run: `uv run pytest tests/test_scoring_rules.py -q && uvx ruff check src/scoring_rules.py tests/test_scoring_rules.py && uvx ruff format src/scoring_rules.py tests/test_scoring_rules.py`
Expected: all pass, ruff clean.

- [ ] **Step 6: Commit**

```bash
git add src/config.py src/scoring_rules.py tests/test_scoring_rules.py
git commit -m "feat(eval): Regeln von Prüffragen zu Rubrik-Werten"
```

---

### Task 2: Key points in the store, freeze record

**Files:**
- Modify: `src/run_log.py` (add `append_key_points_run` after `append_scaffold_run`)
- Modify: `src/scoring_store.py` (`ScoringSet`, `scoring_sets`, new key point functions)
- Modify: `tests/test_scoring_store.py`, `tests/test_scoring_page.py` (fixtures: monkeypatch new globals)
- Test: `tests/test_scoring_store.py`

**Interfaces:**
- Consumes: `config.KEY_POINTS_FILE`, `config.KEY_POINTS_MAX`, `config.GENERATION_RUNS_FILE`, `config.PILOT_RUNS_FILE_NAME`, `config.STRATEGY_IDS`; `run_log.latest_run(runs_file, step, strategy)`, `run_log.sha256_of(path)`.
- Produces:
  - `run_log.append_key_points_run(strategy: str, outputs: dict[str, str], runs_file: Path) -> dict` — record `{"date","step":"key_points","strategy","outputs_sha256"}`
  - `ScoringSet(name, items_file, sheet_file, scores_file, key_points_file, checks_file, runs_file)`
  - `scoring_store.KEY_POINTS_HEADER = ["question_id", "point", "text"]`
  - `scoring_store.questions(items: list[dict]) -> list[dict]` — `{"question_id","question","reference_answer"}` in first-appearance order
  - `scoring_store.load_key_points(s) -> dict[str, list[str]]`
  - `scoring_store.save_key_points(s, items, question_id: str, points: list[str]) -> None`
  - `scoring_store.is_frozen(s) -> bool`
  - `scoring_store.freeze_key_points(s, items) -> None`
  - `scoring_store.require_frozen_key_points(s) -> None` (raises `PermissionError`)

- [ ] **Step 1: Update the test fixtures**

In both `tests/test_scoring_store.py` and `tests/test_scoring_page.py`, the `dirs` fixture gets three more lines
after the existing `monkeypatch.setattr` calls:

```python
    monkeypatch.setattr(scoring, "KEY_POINTS_FILE", main / "key_points.csv")
    monkeypatch.setattr(scoring, "SCORING_CHECKS_FILE", main / "scoring_checks.csv")
    monkeypatch.setattr(scoring, "GENERATION_RUNS_FILE", main / "generation_runs.jsonl")
```

- [ ] **Step 2: Write the failing tests** (append to `tests/test_scoring_store.py`)

```python
import json

from config import KEY_POINTS_MAX


def items_of(s):
    return scoring.load_items(s)


def test_a_pilot_set_keeps_key_points_checks_and_run_log_in_its_folder(hard):
    folder = hard.items_file.parent
    assert hard.key_points_file == folder / "key_points.csv"
    assert hard.checks_file == folder / "scoring_checks.csv"
    assert hard.runs_file == folder / "runs.jsonl"


def test_questions_in_packet_order_without_answers(hard):
    qs = scoring.questions(items_of(hard))
    assert [q["question_id"] for q in qs] == ["H01", "H02"]
    assert set(qs[0]) == {"question_id", "question", "reference_answer"}


def test_key_points_are_saved_per_question_and_numbered(hard):
    items = items_of(hard)
    scoring.save_key_points(hard, items, "H02", ["Core two", "Second"])
    scoring.save_key_points(hard, items, "H01", ["Core one"])
    assert scoring.load_key_points(hard) == {"H01": ["Core one"], "H02": ["Core two", "Second"]}
    rows = read_csv(hard.key_points_file, scoring.KEY_POINTS_HEADER)
    assert [(r["question_id"], r["point"]) for r in rows] == [("H01", "1"), ("H02", "1"), ("H02", "2")]
    scoring.save_key_points(hard, items, "H02", ["Replaced"])
    assert scoring.load_key_points(hard)["H02"] == ["Replaced"]


@pytest.mark.parametrize(
    ("question", "points", "message"),
    [
        ("H01", [], "1 to"),
        ("H01", ["x"] * (KEY_POINTS_MAX + 1), "1 to"),
        ("H01", ["fine", "  "], "empty"),
        ("H01", ["two\nlines"], "one line"),
        ("H09", ["x"], "unknown question"),
    ],
)
def test_invalid_key_points_are_refused(hard, question, points, message):
    with pytest.raises(ValueError, match=message):
        scoring.save_key_points(hard, items_of(hard), question, points)
    assert not hard.key_points_file.exists()


def test_freeze_needs_every_question_and_writes_one_record(hard):
    items = items_of(hard)
    scoring.save_key_points(hard, items, "H01", ["Core one"])
    with pytest.raises(ValueError, match="H02"):
        scoring.freeze_key_points(hard, items)
    assert not scoring.is_frozen(hard)
    scoring.save_key_points(hard, items, "H02", ["Core two"])
    scoring.freeze_key_points(hard, items)
    assert scoring.is_frozen(hard)
    (record,) = [json.loads(line) for line in hard.runs_file.read_text().splitlines()]
    assert record["step"] == "key_points" and "key_points.csv" in record["outputs_sha256"]
    with pytest.raises(PermissionError, match="frozen"):
        scoring.freeze_key_points(hard, items)
    with pytest.raises(PermissionError, match="frozen"):
        scoring.save_key_points(hard, items, "H01", ["Changed"])
    assert len(hard.runs_file.read_text().splitlines()) == 1


def test_a_hand_edit_after_the_freeze_is_caught(hard):
    items = items_of(hard)
    scoring.save_key_points(hard, items, "H01", ["Core one"])
    scoring.save_key_points(hard, items, "H02", ["Core two"])
    with pytest.raises(PermissionError, match="not frozen"):
        scoring.require_frozen_key_points(hard)
    scoring.freeze_key_points(hard, items)
    scoring.require_frozen_key_points(hard)  # unchanged: passes
    with hard.key_points_file.open("a", encoding="utf-8") as f:
        f.write("H02,2,Added later\n")
    with pytest.raises(PermissionError, match="key_points.csv"):
        scoring.require_frozen_key_points(hard)
```

- [ ] **Step 3: Run them to verify they fail**

Run: `uv run pytest tests/test_scoring_store.py -q`
Expected: the new tests FAIL (`AttributeError: ... 'key_points_file'` / `has no attribute 'questions'`); the old ones pass.

- [ ] **Step 4: Implement**

`src/run_log.py`, after `append_scaffold_run`:

```python
def append_key_points_run(strategy: str, outputs: dict[str, str], runs_file: Path) -> dict:
    """Log the freeze of a set's key points with the file's checksum (ADR 0035)."""
    full = {
        "date": date.today().isoformat(),
        "step": "key_points",
        "strategy": strategy,
        "outputs_sha256": outputs,
    }
    _append(full, runs_file)
    return full
```

`src/scoring_store.py`:
- Module docstring: add a sentence: "Key points (ADR 0035) are written per question, then frozen with a run record; every
  score save checks that the frozen file is unchanged."
- Imports: add `GENERATION_RUNS_FILE, KEY_POINTS_FILE, KEY_POINTS_MAX, PILOT_RUNS_FILE_NAME, SCORING_CHECKS_FILE, STRATEGY_IDS`
  to the `config` import; add `from run_log import append_key_points_run, latest_run, sha256_of`.
- `ScoringSet` gets three fields:

```python
@dataclass(frozen=True)
class ScoringSet:
    name: str
    items_file: Path
    sheet_file: Path
    scores_file: Path
    key_points_file: Path
    checks_file: Path
    runs_file: Path
```

- `scoring_sets` body:

```python
def scoring_sets() -> list[ScoringSet]:
    """The main run and every pilot folder that holds an item file."""
    sets = []
    if SCORING_ITEMS_FILE.exists():
        sets.append(
            ScoringSet(
                "Main catalogue",
                SCORING_ITEMS_FILE,
                SCORING_SHEET_FILE,
                SCORES_FILE,
                KEY_POINTS_FILE,
                SCORING_CHECKS_FILE,
                GENERATION_RUNS_FILE,
            )
        )
    for items in sorted(PILOT_DIR.rglob(SCORING_ITEMS_FILE.name)):
        folder = items.parent
        rel = folder.relative_to(PILOT_DIR).as_posix()
        name = "Pilot" if rel == "." else f"Pilot: {rel}"
        sets.append(
            ScoringSet(
                name,
                items,
                folder / SCORING_SHEET_FILE.name,
                folder / SCORES_FILE.name,
                folder / KEY_POINTS_FILE.name,
                folder / SCORING_CHECKS_FILE.name,
                folder / PILOT_RUNS_FILE_NAME,
            )
        )
    return sets
```

- New functions (insert after `load_scores`):

```python
KEY_POINTS_HEADER = ["question_id", "point", "text"]
STRATEGY = ",".join(STRATEGY_IDS)


def questions(items: list[dict]) -> list[dict]:
    """Question and reference answer per question, in packet order; never an answer."""
    seen: dict[str, dict] = {}
    for item in items:
        seen.setdefault(
            item["question_id"],
            {k: item[k] for k in ("question_id", "question", "reference_answer")},
        )
    return list(seen.values())


def load_key_points(s: ScoringSet) -> dict[str, list[str]]:
    points: dict[str, list[str]] = {}
    for row in read_csv(s.key_points_file, KEY_POINTS_HEADER):
        points.setdefault(row["question_id"], []).append(row["text"])
    return points


def is_frozen(s: ScoringSet) -> bool:
    return latest_run(s.runs_file, "key_points", STRATEGY) is not None


def save_key_points(s: ScoringSet, items: list[dict], question_id: str, points: list[str]) -> None:
    """Replace one question's key points (point 1 = core point); refused after the freeze."""
    if is_frozen(s):
        raise PermissionError(f"the key points of {s.name} are frozen")
    if question_id not in {q["question_id"] for q in questions(items)}:
        raise ValueError(f"unknown question {question_id}")
    if not 1 <= len(points) <= KEY_POINTS_MAX:
        raise ValueError(f"a question has 1 to {KEY_POINTS_MAX} key points, got {len(points)}")
    for text in points:
        if not text.strip():
            raise ValueError("a key point is empty")
        if "\n" in text or "\r" in text:
            raise ValueError("a key point is one line")
    current = load_key_points(s) | {question_id: [t.strip() for t in points]}
    rows = [
        {"question_id": qid, "point": str(n), "text": text}
        for qid in sorted(current)
        for n, text in enumerate(current[qid], start=1)
    ]
    write_csv(s.key_points_file, KEY_POINTS_HEADER, rows)


def freeze_key_points(s: ScoringSet, items: list[dict]) -> None:
    """Record the checksum of the key points once every question has some (ADR 0035)."""
    if is_frozen(s):
        raise PermissionError(f"the key points of {s.name} are frozen already")
    points = load_key_points(s)
    missing = [q["question_id"] for q in questions(items) if q["question_id"] not in points]
    if missing:
        raise ValueError(f"no key points yet for {', '.join(missing)}")
    sha = sha256_of(s.key_points_file)
    append_key_points_run(STRATEGY, {s.key_points_file.name: sha}, s.runs_file)


def require_frozen_key_points(s: ScoringSet) -> None:
    record = latest_run(s.runs_file, "key_points", STRATEGY)
    if record is None:
        raise PermissionError(f"the key points of {s.name} are not frozen yet")
    frozen = record["outputs_sha256"].get(s.key_points_file.name)
    if not s.key_points_file.exists() or sha256_of(s.key_points_file) != frozen:
        raise PermissionError(
            f"{s.key_points_file} differs from the frozen key points; restore it from git"
        )
```

Check `run_log._append` creates the parent folder or the file exists in tests (the pilot folder exists through
`write_scoring_set`); read `_append` with Serena (`find_symbol _append include_body`) before relying on it.

- [ ] **Step 5: Run the store and page tests**

Run: `uv run pytest tests/test_scoring_store.py tests/test_scoring_page.py -q`
Expected: all pass (page tests still use the old 0/1/2 form; they change in Task 5).

- [ ] **Step 6: Commit**

```bash
git add src/run_log.py src/scoring_store.py tests/test_scoring_store.py tests/test_scoring_page.py
git commit -m "feat(eval): Kernpunkte je Frage schreiben und einfrieren"
```

---

### Task 3: Saving scores through checks

**Files:**
- Modify: `src/scoring_store.py` (`save_score`, new `load_checks`)
- Modify: `tests/test_scoring_store.py` (replace the `ALL_TWO` save tests)

**Interfaces:**
- Consumes: Task 1 `scoring_rules.validate/derive/to_row/from_row/CHECKS_HEADER`; Task 2 `load_key_points`, `require_frozen_key_points`.
- Produces:
  - `scoring_store.load_checks(s) -> dict[str, dict]` — code → checks dict (only scored codes)
  - `scoring_store.save_score(s, code: str, checks: dict, notes: str) -> dict[str, int]` — returns the derived values; writes checks file then sheet

- [ ] **Step 1: Write the failing tests**

In `tests/test_scoring_store.py`, add a helper fixture and replace every test that calls
`scoring.save_score(hard, code, ALL_TWO, ...)` (find them with `grep -n "save_score" tests/test_scoring_store.py`)
so it uses `frozen` and `GOOD` instead; drop `ALL_TWO`. New helpers and tests:

```python
import scoring_rules as rules

GOOD = {
    "points": ["covered"],
    "declines": "no",
    "core_wrong": "no",
    "other_error": "no",
    "grounded": "all",
    "hallucination": "none",
    "answers_question": "yes",
    "direct": "yes",
    "wordy": "no",
}


@pytest.fixture
def frozen(hard):
    items = scoring.load_items(hard)
    scoring.save_key_points(hard, items, "H01", ["Core one"])
    scoring.save_key_points(hard, items, "H02", ["Core two", "Second two"])
    scoring.freeze_key_points(hard, items)
    return hard


def test_save_writes_the_checks_and_the_derived_scores(frozen):
    values = scoring.save_score(frozen, "H01-B", GOOD | {"other_error": "yes"}, "one slip")
    assert values == rules.derive(GOOD | {"other_error": "yes"})
    row = next(r for r in sheet(frozen) if r["code"] == "H01-B")
    assert row["correctness"] == "1" and row["clarity"] == "2" and row["notes"] == "one slip"
    assert scoring.load_checks(frozen) == {"H01-B": GOOD | {"other_error": "yes"}}
    checks_rows = read_csv(frozen.checks_file, rules.CHECKS_HEADER)
    assert [r["code"] for r in checks_rows] == ["H01-B"]


def test_checks_rows_follow_sheet_order(frozen):
    two = GOOD | {"points": ["covered", "missing"]}
    scoring.save_score(frozen, "H02-A", two, "")
    scoring.save_score(frozen, "H01-B", GOOD, "")
    rows = read_csv(frozen.checks_file, rules.CHECKS_HEADER)
    assert [r["code"] for r in rows] == ["H01-B", "H02-A"]  # sheet (packet) order


def test_save_is_refused_before_the_freeze(hard):
    with pytest.raises(PermissionError, match="not frozen"):
        scoring.save_score(hard, "H01-B", GOOD, "")
    assert not hard.checks_file.exists()


def test_save_is_refused_when_the_point_count_does_not_match(frozen):
    with pytest.raises(ValueError, match="2 key points"):
        scoring.save_score(frozen, "H02-A", GOOD, "")  # H02 has two points


def test_save_is_refused_after_a_hand_edit_of_the_key_points(frozen):
    with frozen.key_points_file.open("a", encoding="utf-8") as f:
        f.write("H01,2,Added later\n")
    with pytest.raises(PermissionError, match="key_points.csv"):
        scoring.save_score(frozen, "H01-B", GOOD, "")
```

Keep (adapted to `frozen` + `GOOD`): unknown code refused, read-only after `scores.csv`, progress counts, header kept.
Remove the tests that pass raw criterion values outside 0–2 or a missing criterion; `validate` covers bad checks in
`tests/test_scoring_rules.py`.

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_scoring_store.py -q`
Expected: FAIL (`save_score` still expects criterion values; `load_checks` missing).

- [ ] **Step 3: Implement**

Imports in `src/scoring_store.py`: `import scoring_rules as rules`. Replace `save_score` and add `load_checks`:

```python
def load_checks(s: ScoringSet) -> dict[str, dict]:
    """The stored checks of every scored code."""
    return {
        r["code"]: rules.from_row(r)[1] for r in read_csv(s.checks_file, rules.CHECKS_HEADER)
    }


def save_score(s: ScoringSet, code: str, checks: dict, notes: str) -> dict[str, int]:
    """Validate the checks, derive the five scores (ADR 0035) and write checks file and sheet
    atomically with only this code's rows changed; returns the derived values."""
    if is_read_only(s):
        raise PermissionError(f"{s.scores_file} exists: the scores were unblinded, read-only")
    require_frozen_key_points(s)
    rows = _sheet(s)
    row = next((r for r in rows if r["code"] == code), None)
    if row is None:
        raise ValueError(f"unknown code {code} in {s.sheet_file}")
    n_points = len(load_key_points(s).get(row["question_id"], []))
    rules.validate(checks, n_points)
    values = rules.derive(checks)
    stored = {r["code"]: r for r in read_csv(s.checks_file, rules.CHECKS_HEADER)}
    stored[code] = rules.to_row(code, checks)
    order = [r["code"] for r in rows]
    write_csv(
        s.checks_file,
        rules.CHECKS_HEADER,
        sorted(stored.values(), key=lambda r: order.index(r["code"])),
    )
    row.update({c: str(v) for c, v in values.items()} | {"notes": notes})
    write_csv(s.sheet_file, SHEET_HEADER, rows)
    return values
```

`RUBRIC_MAX_SCORE` may become unused in `save_score`; keep the import only if `_value` still uses it (it does).

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_scoring_store.py tests/test_scoring_rules.py -q`
Expected: all pass. (`tests/test_scoring_page.py` now fails on save; fixed in Task 5. Note it in the ledger.)

- [ ] **Step 5: Commit**

```bash
git add src/scoring_store.py tests/test_scoring_store.py
git commit -m "feat(eval): Bewertung über Prüffragen speichern"
```

---

### Task 4: `summarise` checks the sheet against the checks

**Files:**
- Modify: `src/evaluate_answers.py` (imports, new `check_derived`, `summarise`, `pilot_paths`, CLI `keep`, docstring)
- Test: `tests/test_evaluate_answers.py`

**Interfaces:**
- Consumes: Task 1 `scoring_rules.CHECKS_HEADER`, `from_row`, `derive`, `validate`; `config.SCORING_CHECKS_FILE`, `config.RUBRIC_RULES_VERSION`.
- Produces: `evaluate_answers.check_derived(sheet_file: Path, checks_file: Path) -> None`; `summarise(..., checks_file: Path = SCORING_CHECKS_FILE, ...)`; `pilot_paths(...)["checks_file"]`.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_evaluate_answers.py`)

Add `"checks_file"` to `SUMMARISE_ARGS` and to the `files` fixture (path `tmp / "scoring_checks.csv"`, same folder as
the sheet; find the fixture with `grep -n "def files" tests/test_evaluate_answers.py`). Then:

```python
import scoring_rules as rules

GOOD_CHECKS = {
    "points": ["covered"],
    "declines": "no",
    "core_wrong": "no",
    "other_error": "no",
    "grounded": "all",
    "hallucination": "none",
    "answers_question": "yes",
    "direct": "yes",
    "wordy": "no",
}


def write_checks(files, rows):
    write_csv(files["checks_file"], rules.CHECKS_HEADER, [[r[h] for h in rules.CHECKS_HEADER] for r in rows])


def test_summarise_accepts_a_sheet_that_equals_its_checks(files):
    run_scaffold(files)
    fill(files, all_two())
    codes = [r["code"] for r in read(files["sheet_file"])]
    write_checks(files, [rules.to_row(c, GOOD_CHECKS) for c in codes])
    run_summarise(files)
    assert files["scores_file"].exists()


def test_summarise_refuses_a_score_that_differs_from_its_checks(files):
    run_scaffold(files)
    fill(files, all_two())
    codes = [r["code"] for r in read(files["sheet_file"])]
    rows = [rules.to_row(c, GOOD_CHECKS) for c in codes]
    rows[0] = rules.to_row(codes[0], GOOD_CHECKS | {"wordy": "yes"})  # clarity 1, sheet says 2
    write_checks(files, rows)
    with pytest.raises(ValueError, match=f"{codes[0]}.*clarity"):
        run_summarise(files)
    assert not files["scores_file"].exists()


def test_summarise_refuses_missing_checks_and_older_rules(files):
    run_scaffold(files)
    fill(files, all_two())
    codes = [r["code"] for r in read(files["sheet_file"])]
    write_checks(files, [rules.to_row(c, GOOD_CHECKS) for c in codes[1:]])
    with pytest.raises(ValueError, match=f"no checks for {codes[0]}"):
        run_summarise(files)
    old = [rules.to_row(c, GOOD_CHECKS) | {"rules_version": "2000-01-01"} for c in codes]
    write_checks(files, old)
    with pytest.raises(ValueError, match="2000-01-01"):
        run_summarise(files)


def test_summarise_without_a_checks_file_works_as_before(files):
    run_scaffold(files)
    fill(files, all_two())
    assert not files["checks_file"].exists()
    run_summarise(files)
    assert files["scores_file"].exists()
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_evaluate_answers.py -q -k "checks"`
Expected: FAIL (`summarise() got an unexpected keyword argument 'checks_file'`).

- [ ] **Step 3: Implement**

In `src/evaluate_answers.py`: add `RUBRIC_RULES_VERSION, SCORING_CHECKS_FILE` to the `config` import and
`import scoring_rules as rules`. New function before `summarise`:

```python
def check_derived(sheet_file: Path, checks_file: Path) -> None:
    """With a checks file (ADR 0035): every sheet row equals the scores its checks derive under
    the current rules, so a hand-edited score or an older rule version cannot be unblinded."""
    if not checks_file.exists():
        return
    stored = {r["code"]: r for r in read_csv(checks_file, rules.CHECKS_HEADER)}
    for row in read_csv(sheet_file, SHEET_HEADER):
        if row["code"] not in stored:
            raise ValueError(f"{checks_file}: no checks for {row['code']}")
        version, checks = rules.from_row(stored[row["code"]])
        if version != RUBRIC_RULES_VERSION:
            raise ValueError(
                f"{checks_file}: {row['code']} was scored under rules {version}, current rules are "
                f"{RUBRIC_RULES_VERSION}; score it again"
            )
        rules.validate(checks, len(checks["points"]))
        for criterion, value in rules.derive(checks).items():
            if row[criterion].strip() != str(value):
                raise ValueError(
                    f"{sheet_file}: {row['code']} {criterion} is {row[criterion]!r}, its checks "
                    f"give {value}"
                )
```

`summarise`: add parameter `checks_file: Path = SCORING_CHECKS_FILE,` after `key_file`, and call
`check_derived(sheet_file, checks_file)` as the first line after `scored = scored_questions(...)` (before
`unblind`). `pilot_paths`: add `"checks_file": set_dir / SCORING_CHECKS_FILE.name,`. CLI: add `"checks_file"` to
`keep` in the summarise branch; in the scaffold branch exclude it like `scores_file`:

```python
        scaffold_args = {k: v for k, v in paths.items() if k not in ("scores_file", "checks_file")}
```

Module docstring, `--mode summarise` paragraph: append "With a checks file (scoring_checks.csv, ADR 0035) every
sheet row must equal the scores its checks derive under the current rules."

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_evaluate_answers.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/evaluate_answers.py tests/test_evaluate_answers.py
git commit -m "feat(eval): Zusammenfassung prüft Werte gegen die Prüffragen"
```

---

### Task 5: Scoring page — Key points step and checks form

**Files:**
- Modify: `app/scoring_page.py`
- Modify: `app/ui_theme.py` (`SCORING_CSS`, only if the browser check in Task 7 needs it)
- Test: `tests/test_scoring_page.py`

**Interfaces:**
- Consumes: Task 1 `scoring_rules.CHECKS`, `POINT_MARKS`, `SKIPPED_WHEN_DECLINING`, `declined`, `derive`; Tasks 2–3 store functions.
- Produces: widget keys used by tests:
  - step control `scoring_step|<set>` (options `"Key points"`, `"Score"`)
  - key point inputs `kp|<set>|<qid>|<n>` (n = 1..`KEY_POINTS_MAX`), question picker `kp_question|<set>`, buttons `kp_save`, `kp_freeze`, checkbox `kp_confirm`
  - check controls `<set>|<code>|point_<n>` and `<set>|<code>|<check>`; notes `<set>|<code>|notes`; buttons `scoring_previous`, `scoring_save` (unchanged)

- [ ] **Step 1: Rewrite the page tests** (`tests/test_scoring_page.py`)

Keep `dirs`, `title`, the no-sets test, the stale-items test, the key-blindness test and the router test. Replace
`score_all` and the scoring tests:

```python
import scoring_rules as rules

ANSWER_TEXT = "Answer H01-B."  # write_scoring_set: answers are "Answer <code>."


def freeze(folder):
    (s,) = scoring.scoring_sets()
    items = scoring.load_items(s)
    scoring.save_key_points(s, items, "H01", ["Core one"])
    scoring.save_key_points(s, items, "H02", ["Core two", "Second two"])
    scoring.freeze_key_points(s, items)


@pytest.fixture
def page(dirs):
    write_scoring_set(dirs[1] / "hard")
    at = AppTest.from_file(str(APP / "scoring_page.py"), default_timeout=60)
    at.run()
    return at, dirs[1] / "hard"


@pytest.fixture
def scoring_page(dirs):
    write_scoring_set(dirs[1] / "hard")
    freeze(dirs[1] / "hard")
    at = AppTest.from_file(str(APP / "scoring_page.py"), default_timeout=60)
    at.run()
    return at, dirs[1] / "hard"


def answer_all(at, code, n_points, **changed):
    """Answer every shown check of `code` with a flawless answer unless `changed`."""
    good = {"declines": "no", "core_wrong": "no", "other_error": "no", "grounded": "all",
            "hallucination": "none", "answers_question": "yes", "direct": "yes", "wordy": "no"}
    for n in range(1, n_points + 1):
        at.button_group(key=f"Pilot: hard|{code}|point_{n}").set_value("covered")
    for check, value in (good | changed).items():
        key = f"Pilot: hard|{code}|{check}"
        if any(g.key == key for g in at.button_group):
            at.button_group(key=key).set_value(value)
    at.run()


def test_before_the_freeze_the_page_opens_on_key_points_without_answers(page):
    at, _ = page
    assert not at.exception
    assert at.segmented_control(key="scoring_step|Pilot: hard").value == "Key points"
    bodies = " ".join(h.proto.body for h in at.get("html")) + " ".join(m.value for m in at.markdown)
    assert ANSWER_TEXT not in bodies and "Excerpt one" not in bodies
    assert "Question H01?" in bodies


def test_key_points_are_saved_and_freezing_opens_scoring(page):
    at, folder = page
    at.text_input(key="kp|Pilot: hard|H01|1").input("Core one").run()
    at.button(key="kp_save").click().run()
    at.text_input(key="kp|Pilot: hard|H02|1").input("Core two").run()
    at.button(key="kp_save").click().run()
    assert (folder / "key_points.csv").exists()
    at.checkbox(key="kp_confirm").check().run()
    at.button(key="kp_freeze").click().run()
    assert not at.exception
    assert (folder / "runs.jsonl").exists()
    assert at.segmented_control(key="scoring_step|Pilot: hard").value == "Score"
    assert "H01, answer B" in title(at)


def test_freeze_is_disabled_until_every_question_has_key_points(page):
    at, _ = page
    at.checkbox(key="kp_confirm").check().run()
    assert at.button(key="kp_freeze").disabled


def test_scoring_through_the_checks_writes_the_derived_scores(scoring_page):
    at, folder = scoring_page
    assert at.segmented_control(key="scoring_step|Pilot: hard").value == "Score"
    answer_all(at, "H01-B", 1, wordy="yes")
    at.button(key="scoring_save").click().run()
    row = read_csv(folder / "scoring_sheet.csv", SHEET_HEADER)[0]
    assert row["code"] == "H01-B" and row["clarity"] == "1" and row["correctness"] == "2"
    assert "H01, answer A" in title(at)


def test_save_is_disabled_until_every_shown_check_is_answered(scoring_page):
    at, _ = scoring_page
    at.button_group(key="Pilot: hard|H01-B|point_1").set_value("covered").run()
    assert at.button(key="scoring_save").disabled


def test_declining_hides_the_skipped_checks_and_reopening_asks_them_again(scoring_page):
    at, folder = scoring_page
    at.button_group(key="Pilot: hard|H01-B|declines").set_value("yes").run()
    keys = {g.key for g in at.button_group}
    assert "Pilot: hard|H01-B|point_1" not in keys
    for check in rules.SKIPPED_WHEN_DECLINING:
        assert f"Pilot: hard|H01-B|{check}" not in keys
    for check in ("answers_question", "direct", "wordy"):
        at.button_group(key=f"Pilot: hard|H01-B|{check}").set_value({"wordy": "no"}.get(check, "yes"))
    at.run()
    at.button(key="scoring_save").click().run()
    row = read_csv(folder / "scoring_sheet.csv", SHEET_HEADER)[0]
    assert (row["correctness"], row["completeness"], row["groundedness"]) == ("1", "0", "2")
    at.selectbox(key="scoring_code|Pilot: hard").set_value("H01-B").run()
    at.button_group(key="Pilot: hard|H01-B|declines").set_value("no").run()
    assert at.button_group(key="Pilot: hard|H01-B|core_wrong").value is None
    assert at.button(key="scoring_save").disabled


def test_saving_the_last_answer_reports_everything_scored(scoring_page):
    at, _ = scoring_page
    points = {"H01": 1, "H02": 2}
    for code in SCORING_CODES:
        answer_all(at, code, points[code.split("-")[0]])
        at.button(key="scoring_save").click().run()
    assert not at.exception
    assert any(m.value == "**6 of 6 scored**" for m in at.sidebar.markdown)


def test_read_only_after_unblinding(scoring_page):
    at, folder = scoring_page
    (folder / "scores.csv").write_text("unblinded", encoding="utf-8")
    at.run()
    assert any("read-only" in i.value for i in at.info)
    assert at.button(key="scoring_save").disabled
```

The router test keeps asserting `"H01, answer B" in title(at)`; call `freeze(dirs[1] / "hard")` in it after
`write_scoring_set`. The opens-first-unscored test becomes part of `test_scoring_through_the_checks...` (title
check) — remove the old one.

Saved-checks reopen: the declining test's last part requires that a stored skipped value is **not** used as the
default once `declines` is switched to `no` — implement defaults so skipped checks of a declined code start empty.

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_scoring_page.py -q`
Expected: FAIL (no `scoring_step` control, no `kp` inputs).

- [ ] **Step 3: Implement `app/scoring_page.py`**

Keep `choose_set`, `page`, `SUMMARISE`, the item/sheet loading and the reader column. Remove `ANCHORS` and `SCORES`.
Add the check texts and the two steps:

```python
import scoring_rules as rules  # noqa: E402
from config import KEY_POINTS_MAX, RUBRIC_CRITERIA  # noqa: E402

STEPS = ["Key points", "Score"]
# the checks of ADR 0035 as the form asks them (docs/reference/evaluation.md)
QUESTIONS = {
    "declines": "Does the answer say the excerpts do not contain the answer, and give none?",
    "core_wrong": "Does it state the core point wrongly or contradict it?",
    "other_error": "Is any other statement factually wrong?",
    "grounded": "How many of its statements are backed by the excerpts?",
    "hallucination": "Does it contain anything that neither the excerpts nor the reference cover?",
    "answers_question": "Does it address what was asked?",
    "direct": "Is the answer given directly, in the first two sentences?",
    "wordy": "Is it repetitive, padded or confusing?",
}
OPTION_LABELS = {
    "minor": "minor addition",
    "substantive": "substantive",
    "covered": "covered",
    "missing": "missing",
}
```

`main()` after loading items and scores:

```python
    frozen = scoring.is_frozen(s)
    step_key = f"scoring_step|{s.name}"
    if st.session_state.pop("scoring_frozen_now", False) or step_key not in st.session_state:
        st.session_state[step_key] = "Score" if frozen else "Key points"
    step = st.segmented_control(
        "Step", STEPS, key=step_key, label_visibility="collapsed", required=True
    )
    if step == "Key points" or not frozen:
        if step == "Score":
            st.caption("Scoring opens once the key points are frozen.")
        key_points_step(s, items, frozen or locked)
        return
```

(`required=True` exists on `st.segmented_control` in 1.58? Verify with Context7 `/streamlit/docs` "segmented_control
required"; if absent, treat `None` as the previous step.)

`key_points_step(s, items, read_only)`:

```python
def key_points_step(s: scoring.ScoringSet, items: list[dict], read_only: bool) -> None:
    qs = scoring.questions(items)
    points = scoring.load_key_points(s)
    ids = [q["question_id"] for q in qs]
    with st.sidebar:
        st.markdown(f"**{sum(q in points for q in ids)} of {len(ids)} questions have key points**")
    pick_key = f"kp_question|{s.name}"
    if "kp_goto" in st.session_state:
        st.session_state[pick_key] = st.session_state.pop("kp_goto")
    if st.session_state.get(pick_key) not in ids:
        st.session_state[pick_key] = next((q for q in ids if q not in points), ids[0])
    qid = st.selectbox(
        "Question", ids, key=pick_key,
        format_func=lambda q: f"{q}, done" if q in points else q,
    )
    q = qs[ids.index(qid)]
    st.markdown("**Question**")
    st.html(f'<div class="context inert">{scoring.text_html(q["question"])}</div>')
    st.markdown("**Reference answer**")
    st.html(f'<div class="context reference inert">{scoring.text_html(q["reference_answer"])}</div>')
    saved = points.get(qid, [])
    texts = [
        st.text_input(
            "Core point" if n == 1 else f"Point {n}",
            value=saved[n - 1] if n <= len(saved) else "",
            key=f"kp|{s.name}|{qid}|{n}",
            disabled=read_only,
            help="The direct answer to the question" if n == 1 else None,
        )
        for n in range(1, KEY_POINTS_MAX + 1)
    ]
    filled = [t for t in texts if t.strip()]
    if st.button("Save and next", key="kp_save", type="primary", disabled=read_only or not filled):
        try:
            scoring.save_key_points(s, items, qid, filled)
        except (ValueError, PermissionError) as error:
            st.error(str(error))
            return
        rest = [x for x in ids if x not in scoring.load_key_points(s)]
        st.session_state["kp_goto"] = rest[0] if rest else qid
        st.rerun()
    if read_only:
        st.info("The key points are frozen.")
        return
    st.divider()
    confirm = st.checkbox(
        "Freeze the key points. They cannot be changed afterwards.", key="kp_confirm"
    )
    if st.button(
        "Freeze key points", key="kp_freeze",
        disabled=not confirm or any(x not in points for x in ids),
    ):
        try:
            scoring.freeze_key_points(s, items)
        except (ValueError, PermissionError) as error:
            st.error(str(error))
            return
        st.session_state["scoring_frozen_now"] = True
        st.rerun()
```

Score step: the existing title/picker/reader code stays; `form(...)` becomes:

```python
def control(label: str, options: tuple[str, ...], default, key: str, locked: bool):
    return st.segmented_control(
        label, list(options), default=default, key=key, disabled=locked,
        format_func=lambda o: OPTION_LABELS.get(o, o),
    )


def form(s, item, saved_notes, saved_checks, key_points, codes, locked) -> None:
    code = item["code"]
    st.markdown("**Question**")
    st.html(f'<div class="context inert">{scoring.text_html(item["question"])}</div>')
    st.markdown("**Reference answer**")
    st.html(f'<div class="context reference inert">{scoring.text_html(item["reference_answer"])}</div>')
    stored = saved_checks or {}
    declined_before = stored.get("declines") == "yes"
    answers = {"declines": control(QUESTIONS["declines"], rules.CHECKS["declines"],
                                   stored.get("declines"), f"{s.name}|{code}|declines", locked)}
    declines = answers["declines"] == "yes"
    marks = []
    if not declines:
        st.markdown("**Key points**")
        for n, text in enumerate(key_points, start=1):
            marks.append(control(
                f"{'Core point' if n == 1 else f'Point {n}'}: {text}", rules.POINT_MARKS,
                None if declined_before or not stored else stored["points"][n - 1],
                f"{s.name}|{code}|point_{n}", locked,
            ))
    for check in list(rules.CHECKS)[1:]:
        if declines and check in rules.SKIPPED_WHEN_DECLINING:
            continue
        default = None if declined_before and check in rules.SKIPPED_WHEN_DECLINING else stored.get(check)
        answers[check] = control(QUESTIONS[check], rules.CHECKS[check], default,
                                 f"{s.name}|{code}|{check}", locked)
    complete = all(v is not None for v in answers.values()) and all(m is not None for m in marks)
    checks = rules.declined(answers | {"points": marks}, len(key_points)) if complete else None
    if checks:
        values = rules.derive(checks)
        st.markdown(
            "| " + " | ".join(LABELS[c] for c in RUBRIC_CRITERIA) + " |\n|"
            + "---:|" * len(RUBRIC_CRITERIA) + "\n| "
            + " | ".join(str(values[c]) for c in RUBRIC_CRITERIA) + " |"
        )
    notes = st.text_input("Notes", value=saved_notes, key=f"{s.name}|{code}|notes",
                          disabled=locked, placeholder="e.g. rule did not fit")
    # Previous / Save and next exactly as before, with:
    #   disabled=locked or checks is None
    #   scoring.save_score(s, code, checks, notes)
```

In `main()` pass
`scores[code]["notes"]`, `scoring.load_checks(s).get(code)`, and `scoring.load_key_points(s)[item["question_id"]]`.

- [ ] **Step 4: Run the page tests, then the whole suite**

Run: `uv run pytest tests/test_scoring_page.py -q && uv run pytest -q`
Expected: all pass.

- [ ] **Step 5: Lint and commit**

```bash
uvx pre-commit run --all-files
git add app/scoring_page.py tests/test_scoring_page.py
git commit -m "feat(app): Kernpunkte und Prüffragen auf der Bewertungsseite"
```

---

### Task 6: Documentation

**Files:**
- Create: `docs/adr/0035-regelbasierte-bewertung.md`
- Modify: `docs/adr/README.md`, `docs/adr/0013-antwort-rubrik.md`, `docs/adr/0032-blinde-rubrik-bewertung.md`, `docs/adr/0034-bewertung-in-der-app.md` (status lines), `AGENTS.md` (D1–D35), `docs/README.md` (if it counts ADRs), `docs/reference/evaluation.md`, `docs/reference/data-formats.md`, `docs/reference/configuration.md`, `docs/how-to/run-the-experiment.md`, `docs/reference/tooling.md`, `.serena/memories/pipeline.md`

- [ ] **Step 1: ADR 0035** (German, format of ADR 0034: Status, Kontext, Entscheidung, Konsequenzen)

```markdown
# 0035. Regelbasierte Rubrik-Bewertung mit Kernpunkten

## Status

Angenommen (17.10.2026; ergänzt [ADR 0013](0013-antwort-rubrik.md), [ADR 0032](0032-blinde-rubrik-bewertung.md) und
[ADR 0034](0034-bewertung-in-der-app.md))

## Kontext

- Die Rubrik (ADR 0013) beschreibt die Stufen mit Adjektiven („teilweise korrekt“). Dieselbe Person kann dieselbe
  Antwort an zwei Tagen verschieden einstufen; das schwächt die primäre Bewertung (ADR 0007).
- Ein LLM als Bewerter wäre wiederholbar, aber nicht valide geprüft; RAGAS bleibt sekundär (ADR 0007).

## Entscheidung

Wir werden die fünf Kriterien aus Prüffragen mit festen Antwortoptionen nach festen Regeln ableiten:

- Je Frage schreibt Jonas vor der Bewertung 1–4 Kernpunkte (`key_points.csv`, Punkt 1 = Kernaussage) und friert sie
  mit einem Protokolleintrag (Prüfsumme) ein; danach sind sie unveränderlich, jede Speicherung prüft die Prüfsumme.
- Je Antwort werden die Kernpunkte als „enthalten/fehlt“ markiert und acht Prüffragen beantwortet; die Werte folgen
  aus der Regeltabelle in [Evaluation](../reference/evaluation.md#regelbasierte-bewertung) (`src/scoring_rules.py`,
  Version `config.RUBRIC_RULES_VERSION`). Ein manuelles Überschreiben gibt es nicht.
- Eine Antwort, die erklärt, der Kontext enthalte die Antwort nicht, erhält Korrektheit 1, Vollständigkeit 0,
  Quellenbezug 2 und Halluzinationsfreiheit 2.
- Die Antworten auf die Prüffragen stehen in `scoring_checks.csv`; `--mode summarise` prüft jede Zeile des Bogens gegen
  sie.
- Die Regeln werden nach dem Pilot-Set `hard` einmal angepasst und dann für den Hauptlauf eingefroren.

## Konsequenzen

- Jeder Wert ist auf beobachtbare Prüfantworten zurückführbar; die Methodik kann die Regeln vollständig angeben.
- Ermessen bleibt in den Prüffragen selbst (z. B. „klein“ vs. „wesentlich“); die Intra-Rater-Übereinstimmung wird
  nach dem Pilot an einer Stichprobe gemessen (Folgeschritt).
- Kernpunkte sind Teil der Ground Truth: nur Jonas schreibt sie, vor jeder Bewertung (Geist von ADR 0017).
```

- [ ] **Step 2: The other docs**

- `docs/adr/README.md`: row `| [0035](0035-regelbasierte-bewertung.md) | Regelbasierte Rubrik-Bewertung mit Kernpunkten | Angenommen |`.
- Status lines: 0013 "… ergänzt durch [ADR 0035](0035-regelbasierte-bewertung.md)"; 0032 and 0034 likewise.
- `AGENTS.md`: `decisions D1–D34` → `D1–D35`.
- `docs/reference/evaluation.md`: new section `## Regelbasierte Bewertung` after the rubric table: one sentence that
  the adjective table is the summary and the rules below are operative (ADR 0035); the checks table and the rule table
  from the spec, in German (Prüffrage, Optionen; Kriterium, 2/1/0), the declining rule, and the threshold names.
- `docs/reference/data-formats.md`: `key_points.csv` and `scoring_checks.csv` (header, example row, meaning), the
  `key_points` record next to the `scaffold` record in the run-log paragraph, both files in the pilot table.
- `docs/reference/configuration.md`: the five new keys with meaning and "D35".
- `docs/how-to/run-the-experiment.md`: scoring section: 1) Key points step, write per question, freeze;
  2) Score step, answer the checks; scores follow; 3) summarise checks sheet vs. checks.
- `docs/reference/tooling.md`: versioned-files table: `key_points.csv`, `scoring_checks.csv` (main and pilot).
- `.serena/memories/pipeline.md`: one line: "Rule-based scoring (D35): key points → freeze → checks → `scoring_rules.derive`; see docs/reference/evaluation.md#regelbasierte-bewertung".

- [ ] **Step 3: Check links and lint**

Run: `uvx pre-commit run --all-files && grep -rn "0035" docs AGENTS.md | head`
Expected: passes; every reference resolves to `docs/adr/0035-regelbasierte-bewertung.md`.

- [ ] **Step 4: Commit**

```bash
git add docs AGENTS.md .serena/memories/pipeline.md
git commit -m "docs: regelbasierte Bewertung (ADR 0035)"
```

---

### Task 7: Browser check, impeccable audit and polish

**Files:**
- Modify (only if findings): `app/scoring_page.py`, `app/ui_theme.py`

- [ ] **Step 1: Test data outside the real set**

Copy `data/pilot/hard` to `data/pilot/ui-check` (items, sheet, runs; the copy is not committed: delete it after the
check). Do not write key points into `data/pilot/hard`: key points of the real set are Jonas's. In the copy, use
dummy text ("Dummy point 1") only.

- [ ] **Step 2: Run the app and exercise both steps**

Run `uv run streamlit run app/catalogue_editor.py --server.port 8502 --server.headless true` in the background; with
`playwright-cli` (read `playwright-cli --help` first) at 320, 768 and 1280 px, light and dark: Key points step (write,
save, freeze), Score step (all checks, declining path, derived table, save and next), read console errors. Screenshots
to the scratchpad.

- [ ] **Step 3: impeccable audit, then polish**, on `app/scoring_page.py`; fix findings in one batch, confirm once.

- [ ] **Step 4: Clean up and commit**

Stop the server, delete `data/pilot/ui-check`, run `uv run pytest -q` and `uvx pre-commit run --all-files`, commit
any fixes: `git commit -m "fix(app): Feinschliff der Prüffragen-Ansicht"`.
