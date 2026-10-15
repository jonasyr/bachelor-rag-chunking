# Catalogue Authoring Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A seeded random sampling plan for the 48 catalogue slots, a local Streamlit editor for writing and
annotating questions with live rule checks, and a logged AI review whose decisions stay with Jonas.

**Architecture:** Three focused modules next to `src/catalogue.py`: `catalogue_plan.py` (draw, skip, plan rules),
`catalogue_review.py` (review log), `catalogue_store.py` (editor read/write operations and text highlighting).
`catalogue.check`/`freeze_catalogue` integrate the plan and review rules; `app/catalogue_editor.py` is a thin
Streamlit UI that only calls these functions. All parameters in `src/config.py`.

**Tech Stack:** Python 3.13 (uv), Streamlit 1.58 (`streamlit.testing.v1.AppTest`), pytest, ruff, Pyright,
playwright-cli, the `impeccable` skill.

**Spec:** `docs/superpowers/specs/2026-10-14-catalogue-authoring-design.md`

## Global Constraints

- All parameters (paths, seed, slot counts, reserve, reasons, value sets) live only in `src/config.py`; Codex flags
  any hard-coded threshold or value set as P1 (three such rounds on PR #8).
- Jonas writes every question, reference answer and relevance judgement; no code generates question text.
- The editor never shows chunks, strategies, retrieval results or scores; it reads only the corpus and the catalogue
  files (ADR 0027).
- `questions.csv`/`ground_truth.csv` keep the exact documented format; writes are deterministic (rows sorted by
  `question_id`, `\n` line endings).
- Draw is hash-based (SHA-256), never `random`/NumPy; `CATALOGUE_SEED = 20261014`, never tuned.
- `CATALOGUE_AREA_SLOTS = {"api": 12, "style-guide": 3, "guide": 33}`; `CATALOGUE_RESERVE` the same values.
- Skip reasons: `code-or-links`, `too-short`, `duplicate-topic`, `no-answerable-content`;
  `CATALOGUE_SKIP_MIN_TOKENS = 50`.
- Review kinds `missing_section`, `wording`, `fact`, `class`; decisions `open`, `accepted`, `rejected`.
- Editor design per the spec's "Visual design" section (reading desk, highlighter, palette, serif source page,
  sentence case, plain verbs, no all-caps labels, no middle-dot meta strings, no arrows on buttons).
- Tests: no network, no API. Conventional Commits, German subject; no AI attribution. Line length 100.
- `app/streamlit_app.py` (later RAG demo) stays untouched.

## Review Focus

1. Editing a used slot must not let the slot's starting section be removed from the annotation (the editor keeps it,
   the store re-adds it) → test in Task 4.
2. Skipping a slot that already has a question must be refused, not silently orphan the question → test in Task 2.
3. Saving after the freeze must be refused with a clear message, in the store and in the UI → tests in Tasks 4 and 5.
4. A plan whose section IDs no longer exist in `sections.jsonl` (corpus rebuilt) must be an error, not a crash →
   test in Task 2.
5. Hand-edited CSVs between two editor actions must be picked up (the editor reloads from disk on every rerun;
   nothing is cached except the corpus) → test in Task 5.

---

### Task 1: Configuration and the sampling plan draw

**Files:**
- Modify: `src/config.py` (paths block; "Question catalogue" block)
- Create: `src/catalogue_plan.py`
- Modify: `tests/conftest.py` (helper `write_plan`)
- Create: `tests/test_catalogue_plan.py`

**Interfaces:**
- Produces config: `CATALOGUE_PLAN_FILE: Path`, `CATALOGUE_REVIEW_FILE: Path`, `CATALOGUE_SEED: int`,
  `CATALOGUE_AREA_SLOTS: dict[str, int]`, `CATALOGUE_RESERVE: dict[str, int]`,
  `CATALOGUE_SKIP_REASONS: tuple[str, ...]`, `CATALOGUE_SKIP_MIN_TOKENS: int`,
  `CATALOGUE_PLAN_STATUSES: tuple[str, ...]`, `CATALOGUE_REVIEW_KINDS: tuple[str, ...]`,
  `CATALOGUE_REVIEW_DECISIONS: tuple[str, ...]`.
- Produces `catalogue_plan`: `PLAN_HEADER: list[str]`; `candidates(corpus) -> dict[str, list[dict]]`;
  `draw_area(seed: int, area: str, sections: list[dict], count: int) -> list[dict]`;
  `draw_plan(corpus, seed=CATALOGUE_SEED, slots=CATALOGUE_AREA_SLOTS, reserve=CATALOGUE_RESERVE,
  classes=QUESTION_CLASSES) -> list[dict]`; `read_plan(path) -> list[dict]`; `save_plan(path, rows) -> None`;
  `write_plan(corpus, plan_file=CATALOGUE_PLAN_FILE, **draw_args) -> int` (refuses to overwrite).
- Produces (tests): `conftest.write_plan_for(tmp_path, rows) -> Path` (a plan with one `used` row per catalogue row).

- [ ] **Step 1: Configuration**

In `src/config.py` after `CATALOGUE_FREEZE_FILE = …` add:

```python
CATALOGUE_PLAN_FILE = DATA_EVAL / "catalogue_plan.csv"  # random sampling plan of the slots (D31)
CATALOGUE_REVIEW_FILE = DATA_EVAL / "catalogue_review.csv"  # AI review suggestions and decisions (D31)
```

At the end of the "Question catalogue" block add:

```python
# Random sampling plan (D31): one starting section per slot, drawn by text length from the
# innermost H2/H3 sections of an area with SHA-256 of "{seed}:{area}:{k}" (version-independent).
CATALOGUE_SEED = 20261014  # fixed on 14.10.2026, the date of the decision; never tuned
CATALOGUE_AREA_SLOTS = {"api": 12, "style-guide": 3, "guide": 33}  # sums to the catalogue size
CATALOGUE_RESERVE = {"api": 12, "style-guide": 3, "guide": 33}  # replacement sections per area
CATALOGUE_SKIP_REASONS = ("code-or-links", "too-short", "duplicate-topic", "no-answerable-content")
CATALOGUE_SKIP_MIN_TOKENS = 50  # `too-short`: starting section under this many tokens
CATALOGUE_PLAN_STATUSES = ("open", "used", "skipped", "reserve")
# AI review log (D31): kinds of suggestions and their decisions
CATALOGUE_REVIEW_KINDS = ("missing_section", "wording", "fact", "class")
CATALOGUE_REVIEW_DECISIONS = ("open", "accepted", "rejected")
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_catalogue_plan.py`:

```python
import pytest

import catalogue_plan
from catalogue_plan import candidates, draw_area, draw_plan, read_plan, save_plan, write_plan
from config import CATALOGUE_AREA_SLOTS, CATALOGUE_RESERVE, QUESTION_CLASSES

SMALL = {
    "slots": {"api": 1, "style-guide": 1, "guide": 1},
    "reserve": {"api": 1, "style-guide": 0, "guide": 1},
    "classes": {"single": 1, "multi-section": 1, "paraphrase": 1},
}


def test_config_slots_match_the_catalogue():
    assert sum(CATALOGUE_AREA_SLOTS.values()) == sum(QUESTION_CLASSES.values())
    assert set(CATALOGUE_RESERVE) == set(CATALOGUE_AREA_SLOTS)


def test_candidates_are_innermost_h2_h3_per_area(corpus):
    ids = {area: [s["section_id"] for s in secs] for area, secs in candidates(corpus).items()}
    assert ids == {
        "api": ["D001#ref", "D001#computed"],
        "style-guide": ["D003#multi-word"],
        "guide": ["D002#once", "D002#cleanup"],  # D002#deep contains D002#once
    }


def test_draw_area_maps_token_positions_to_sections(corpus, monkeypatch):
    secs = candidates(corpus)["api"]
    first = secs[0]["end_token"] - secs[0]["start_token"]
    monkeypatch.setattr(catalogue_plan, "_hash_int", lambda text: first)  # position = start of 2nd
    assert [s["section_id"] for s in draw_area(1, "api", secs, 1)] == ["D001#computed"]


def test_draw_area_draws_distinct_sections_and_refuses_too_many(corpus):
    secs = candidates(corpus)["api"]
    drawn = draw_area(7, "api", secs, 2)
    assert sorted(s["section_id"] for s in drawn) == ["D001#computed", "D001#ref"]
    with pytest.raises(ValueError, match="only 2 candidate sections"):
        draw_area(7, "api", secs, 3)


def test_draw_plan_is_deterministic_and_seed_dependent(corpus):
    assert draw_plan(corpus, seed=1, **SMALL) == draw_plan(corpus, seed=1, **SMALL)
    plans = {tuple(r["section_id"] for r in draw_plan(corpus, seed=s, **SMALL)) for s in range(8)}
    assert len(plans) > 1


def test_draw_plan_rows(corpus):
    rows = draw_plan(corpus, seed=3, **SMALL)
    slots = [r for r in rows if r["status"] == "open"]
    assert [r["slot_id"] for r in slots] == ["S01", "S02", "S03"]
    assert [r["area"] for r in slots] == ["api", "style-guide", "guide"]
    assert sorted(r["class"] for r in slots) == ["multi-section", "paraphrase", "single"]
    reserve = [r for r in rows if r["status"] == "reserve"]
    assert [(r["area"], r["slot_id"], r["class"]) for r in reserve] == [("api", "", ""), ("guide", "", "")]
    assert all(r["draw"].isdigit() and r["skip_reason"] == r["question_id"] == "" for r in rows)


def test_draw_plan_refuses_slots_that_do_not_match_the_classes(corpus):
    with pytest.raises(ValueError, match="slots must sum"):
        draw_plan(corpus, seed=1, slots={"api": 1, "style-guide": 0, "guide": 0},
                  reserve=SMALL["reserve"], classes=SMALL["classes"])


def test_write_plan_round_trip_and_never_overwrites(corpus, tmp_path):
    out = tmp_path / "catalogue_plan.csv"
    assert write_plan(corpus, out, seed=3, **SMALL) == 5
    rows = read_plan(out)
    assert rows == draw_plan(corpus, seed=3, **SMALL)
    with pytest.raises(FileExistsError, match="ADR 0031"):
        write_plan(corpus, out, seed=3, **SMALL)
    save_plan(out, rows)
    assert read_plan(out) == rows


def test_read_plan_rejects_bad_files(tmp_path):
    missing = tmp_path / "missing.csv"
    with pytest.raises(FileNotFoundError, match="catalogue.py plan"):
        read_plan(missing)
    bad = tmp_path / "bad.csv"
    bad.write_text("area,draw\napi,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="columns"):
        read_plan(bad)
    status = tmp_path / "status.csv"
    status.write_text(
        "area,draw,section_id,slot_id,class,status,skip_reason,question_id\n"
        "api,1,D001#ref,S01,single,done,,\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown status 'done'"):
        read_plan(status)
```

Add to `tests/conftest.py` (imports at the top: `from catalogue_plan import PLAN_HEADER`; the helper below
`valid_rows`):

```python
def write_plan_for(tmp_path, rows):
    """A plan with one used slot per catalogue row (starting section = first annotated section)."""
    plan = tmp_path / "catalogue_plan.csv"
    with plan.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(PLAN_HEADER)
        for number, (qid, _, _, cls, _, sids) in enumerate(rows, start=1):
            area = {"D001": "api", "D002": "guide", "D003": "style-guide"}[sids[0].split("#")[0]]
            writer.writerow([area, number, sids[0], f"S{number:02d}", cls, "used", "", qid])
    return plan
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_catalogue_plan.py -q`
Expected: FAIL (`ModuleNotFoundError: No module named 'catalogue_plan'`).

- [ ] **Step 4: Write `src/catalogue_plan.py`**

```python
"""Random sampling plan of the question catalogue (ADR 0031).

One starting section per slot, drawn by text length: a token position of an area is chosen with
SHA-256 of "{seed}:{area}:{k}" and the innermost H2/H3 section containing it is drawn (no repeats).
Each slot also gets a construction class; Jonas writes the question, chooses its type and
annotates it. Unsuitable sections are skipped only with a fixed reason; the next reserve section
of the same area takes the slot. The plan file is written once and versioned.
"""

from __future__ import annotations

import csv
import hashlib
from bisect import bisect_right
from pathlib import Path
from typing import TYPE_CHECKING

from config import (
    CATALOGUE_AREA_SLOTS,
    CATALOGUE_PLAN_FILE,
    CATALOGUE_PLAN_STATUSES,
    CATALOGUE_RESERVE,
    CATALOGUE_SEED,
    QUESTION_CLASSES,
)

if TYPE_CHECKING:
    from catalogue import Corpus

PLAN_HEADER = ["area", "draw", "section_id", "slot_id", "class", "status", "skip_reason", "question_id"]


def _hash_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)


def candidates(corpus: Corpus) -> dict[str, list[dict]]:
    """Innermost sections of level 2 or 3 per area, in sections.jsonl order."""
    result: dict[str, list[dict]] = {area: [] for area in CATALOGUE_AREA_SLOTS}
    for s in corpus.sections:
        if s["level"] < 2:
            continue
        inner = any(
            c is not s
            and c["doc_id"] == s["doc_id"]
            and c["level"] > s["level"]
            and s["start_token"] <= c["start_token"]
            and c["end_token"] <= s["end_token"]
            for c in corpus.sections
        )
        area = corpus.area(s)
        if not inner and area in result:
            result[area].append(s)
    return result


def draw_area(seed: int, area: str, sections: list[dict], count: int) -> list[dict]:
    """`count` distinct sections, each drawn by a hashed token position over the area's text."""
    usable = [s for s in sections if s["end_token"] > s["start_token"]]
    if count > len(usable):
        raise ValueError(f"area {area} has only {len(usable)} candidate sections, {count} needed")
    starts, total = [], 0
    for s in usable:
        starts.append(total)
        total += s["end_token"] - s["start_token"]
    drawn: list[dict] = []
    seen: set[str] = set()
    k = 0
    while len(drawn) < count:
        position = _hash_int(f"{seed}:{area}:{k}") % total
        k += 1
        section = usable[bisect_right(starts, position) - 1]
        if section["section_id"] not in seen:
            seen.add(section["section_id"])
            drawn.append(section)
    return drawn


def draw_plan(
    corpus: Corpus,
    seed: int = CATALOGUE_SEED,
    slots: dict[str, int] = CATALOGUE_AREA_SLOTS,
    reserve: dict[str, int] = CATALOGUE_RESERVE,
    classes: dict[str, int] = QUESTION_CLASSES,
) -> list[dict]:
    """Plan rows: per area its slots, then its reserve, in draw order (ADR 0031)."""
    values = [c for c, n in classes.items() for _ in range(n)]
    if sum(slots.values()) != len(values):
        raise ValueError(f"slots must sum to {len(values)} (the class quotas), not {sum(slots.values())}")
    order = sorted(range(len(values)), key=lambda i: _hash_int(f"{seed}:class:{i}"))
    shuffled = [values[i] for i in order]
    pools = candidates(corpus)
    rows: list[dict] = []
    slot = 0
    for area, count in slots.items():
        for number, section in enumerate(
            draw_area(seed, area, pools[area], count + reserve[area]), start=1
        ):
            is_slot = number <= count
            slot += is_slot
            rows.append(
                {
                    "area": area,
                    "draw": str(number),
                    "section_id": section["section_id"],
                    "slot_id": f"S{slot:02d}" if is_slot else "",
                    "class": shuffled[slot - 1] if is_slot else "",
                    "status": "open" if is_slot else "reserve",
                    "skip_reason": "",
                    "question_id": "",
                }
            )
    return rows


def read_plan(path: Path = CATALOGUE_PLAN_FILE) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found; run `uv run python src/catalogue.py plan` first (ADR 0031)"
        )
    with path.open(encoding="utf-8", newline="") as f:
        records = [r for r in csv.reader(f) if r]
    if not records or records[0] != PLAN_HEADER:
        found = records[0] if records else []
        raise ValueError(f"{path} has columns {found}, expected {PLAN_HEADER}")
    rows = []
    for number, record in enumerate(records[1:], start=2):
        if len(record) != len(PLAN_HEADER):
            raise ValueError(f"{path}: row {number} has {len(record)} fields")
        row = dict(zip(PLAN_HEADER, record, strict=True))
        if row["status"] not in CATALOGUE_PLAN_STATUSES:
            raise ValueError(f"{path}: row {number} has unknown status {row['status']!r}")
        rows.append(row)
    return rows


def save_plan(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PLAN_HEADER, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_plan(corpus: Corpus, plan_file: Path = CATALOGUE_PLAN_FILE, **draw_args) -> int:
    """Draw and write the plan once; an existing plan is never overwritten (ADR 0031)."""
    rows = draw_plan(corpus, **draw_args)
    if plan_file.exists():
        raise FileExistsError(
            f"{plan_file} exists: the sampling plan is fixed. A new draw needs a new ADR (ADR 0031)"
        )
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    save_plan(plan_file, rows)
    return len(rows)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_catalogue_plan.py -q`
Expected: 10 passed. (`write_plan` checks existence after drawing, so a failing draw never leaves a file; the
check-then-write is single-user, the freeze record uses exclusive create.)

- [ ] **Step 6: Lint, type check, commit**

Run: `uvx ruff format -q src tests && uvx ruff check src tests && uv run pyright src/catalogue_plan.py`
Expected: clean, 0 errors.

```bash
git add src/config.py src/catalogue_plan.py tests/test_catalogue_plan.py tests/conftest.py
git commit -m "feat(catalogue): zufälliger Stichprobenplan der Slots"
```

---

### Task 2: Skipping, using slots and the plan rules in `check`

**Files:**
- Modify: `src/catalogue_plan.py` (skip, mark used, rules, summary)
- Modify: `src/catalogue.py` (`check` gets `plan_file`; `plan` CLI subcommand)
- Modify: `tests/test_catalogue_plan.py`, `tests/test_catalogue.py`, `tests/test_freeze.py` (helpers pass a plan)

**Interfaces:**
- Consumes: Task 1 functions; `catalogue.check` (existing).
- Produces: `skip_slot(plan_file: Path, slot_id: str, reason: str) -> dict` (the new open row);
  `mark_used(rows: list[dict], slot_id: str, question_id: str) -> None` (in place);
  `slot_row(rows, slot_id) -> dict` (the open or used row of a slot);
  `plan_findings(rows, questions: list[dict], relevant: dict[str, list[dict]], section_ids: set[str]) ->
  tuple[list[str], list[str]]` (errors, findings); `plan_summary(rows) -> list[str]`;
  `catalogue.check(corpus, questions_file, ground_truth_file, pilot_dir, plan_file=CATALOGUE_PLAN_FILE)`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_catalogue_plan.py` (import `mark_used, plan_findings, plan_summary, skip_slot, slot_row`):

```python
@pytest.fixture
def small_plan(corpus, tmp_path):
    out = tmp_path / "catalogue_plan.csv"
    write_plan(corpus, out, seed=3, **SMALL)
    return out


def test_skip_moves_the_slot_to_the_next_reserve_section(small_plan):
    rows = read_plan(small_plan)
    s01 = slot_row(rows, "S01")
    new = skip_slot(small_plan, "S01", "code-or-links")
    rows = read_plan(small_plan)
    skipped = next(r for r in rows if r["section_id"] == s01["section_id"])
    assert (skipped["status"], skipped["skip_reason"]) == ("skipped", "code-or-links")
    assert (new["slot_id"], new["class"], new["status"], new["area"]) == ("S01", s01["class"], "open", "api")
    assert slot_row(rows, "S01")["section_id"] == new["section_id"] != s01["section_id"]


def test_skip_needs_a_listed_reason_an_open_slot_and_a_reserve(small_plan):
    with pytest.raises(ValueError, match="reason"):
        skip_slot(small_plan, "S01", "boring")
    with pytest.raises(ValueError, match="no reserve section left in area style-guide"):
        skip_slot(small_plan, "S02", "too-short")
    rows = read_plan(small_plan)
    mark_used(rows, "S03", "Q001")
    save_plan(small_plan, rows)
    with pytest.raises(ValueError, match="S03 is not open"):
        skip_slot(small_plan, "S03", "too-short")


def test_mark_used_accepts_open_or_same_question_only(small_plan):
    rows = read_plan(small_plan)
    mark_used(rows, "S01", "Q001")
    mark_used(rows, "S01", "Q001")  # editing the same question
    with pytest.raises(ValueError, match="S01 already holds Q001"):
        mark_used(rows, "S01", "Q002")


def q(qid, cls):
    return {"question_id": qid, "question": "x", "type": "factual", "difficulty": cls}


def test_plan_findings(corpus, small_plan):
    rows = read_plan(small_plan)
    s01 = slot_row(rows, "S01")
    mark_used(rows, "S01", "Q001")
    questions = [q("Q001", "single" if s01["class"] != "single" else "paraphrase"), q("Q002", "single")]
    relevant = {"Q001": [corpus.by_id["D002#cleanup"]], "Q002": [corpus.by_id["D002#cleanup"]]}
    errors, findings = plan_findings(rows, questions, relevant, set(corpus.by_id))
    assert errors == []
    assert f"Q001: difficulty {questions[0]['difficulty']} but slot S01 is {s01['class']}" in findings
    assert f"Q001: starting section {s01['section_id']} of slot S01 is not annotated" in findings
    assert "Q002: belongs to 0 slots, needs exactly 1" in findings


def test_plan_findings_report_unknown_sections_and_bad_reasons(corpus, small_plan):
    rows = read_plan(small_plan)
    rows[0]["section_id"] = "D099#gone"
    rows[1]["status"], rows[1]["skip_reason"] = "skipped", "boring"
    errors, _ = plan_findings(rows, [], {}, set(corpus.by_id))
    assert any("D099#gone" in e for e in errors)
    assert any("'boring'" in e for e in errors)


def test_plan_summary_counts_skips(small_plan):
    skip_slot(small_plan, "S01", "too-short")
    lines = plan_summary(read_plan(small_plan))
    assert "Slots: 0 used, 3 open, 1 skipped (too-short 1)" in lines
```

In `tests/test_catalogue.py` change `run_check` and the `cli` fixture so every strict check has a plan, and add the
integration test:

```python
def run_check(corpus, tmp_path, rows, pilot_dir):
    questions, truth = write_catalogue(tmp_path, rows)
    plan = write_plan_for(tmp_path, rows)
    return check(corpus, questions, truth, pilot_dir=pilot_dir, plan_file=plan)
```

(in `cli`: add `monkeypatch.setattr(catalogue, "CATALOGUE_PLAN_FILE", write_plan_for(tmp_path, valid_rows()))`;
import `write_plan_for` from `conftest`.)

```python
def test_check_reports_a_missing_plan(corpus, tmp_path, pilot):
    questions, truth = write_catalogue(tmp_path, valid_rows())
    report = check(corpus, questions, truth, pilot_dir=pilot, plan_file=tmp_path / "none.csv")
    assert any("catalogue.py plan" in e for e in report.errors)


def test_check_applies_the_plan_rules(corpus, tmp_path, pilot):
    rows = valid_rows()
    questions, truth = write_catalogue(tmp_path, rows)
    plan = write_plan_for(tmp_path, rows[1:])  # Q001 has no slot
    report = check(corpus, questions, truth, pilot_dir=pilot, plan_file=plan)
    assert "Q001: belongs to 0 slots, needs exactly 1" in report.findings
```

In `tests/test_freeze.py` pass a plan where `freeze_catalogue` is called (Task 3 adds the parameter; until then
these tests keep passing because `check` defaults to `config.CATALOGUE_PLAN_FILE` only in Task 2 — see Step 3).

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_catalogue_plan.py tests/test_catalogue.py -q`
Expected: FAIL (`ImportError: cannot import name 'mark_used'`).

- [ ] **Step 3: Implement**

Append to `src/catalogue_plan.py` (add `CATALOGUE_SKIP_REASONS` to the config import):

```python
def slot_row(rows: list[dict], slot_id: str) -> dict:
    """The current (open or used) row of a slot."""
    for row in rows:
        if row["slot_id"] == slot_id and row["status"] in ("open", "used"):
            return row
    raise ValueError(f"no slot {slot_id} in the plan")


def mark_used(rows: list[dict], slot_id: str, question_id: str) -> None:
    row = slot_row(rows, slot_id)
    if row["status"] == "used" and row["question_id"] != question_id:
        raise ValueError(f"slot {slot_id} already holds {row['question_id']}")
    row["status"], row["question_id"] = "used", question_id


def skip_slot(plan_file: Path, slot_id: str, reason: str) -> dict:
    """Skip an open slot's section with a listed reason; the area's next reserve row takes over."""
    if reason not in CATALOGUE_SKIP_REASONS:
        raise ValueError(f"skip reason {reason!r} not allowed; use one of {list(CATALOGUE_SKIP_REASONS)}")
    rows = read_plan(plan_file)
    row = slot_row(rows, slot_id)
    if row["status"] != "open":
        raise ValueError(f"slot {slot_id} is not open (it holds {row['question_id']})")
    spare = [r for r in rows if r["area"] == row["area"] and r["status"] == "reserve"]
    if not spare:
        raise ValueError(
            f"no reserve section left in area {row['area']}; a larger reserve needs a new ADR (ADR 0031)"
        )
    new = min(spare, key=lambda r: int(r["draw"]))
    new["slot_id"], new["class"], new["status"] = row["slot_id"], row["class"], "open"
    row["status"], row["skip_reason"] = "skipped", reason
    save_plan(plan_file, rows)
    return new


def plan_findings(
    rows: list[dict],
    questions: list[dict],
    relevant: dict[str, list[dict]],
    section_ids: set[str],
) -> tuple[list[str], list[str]]:
    """Errors (plan format) and findings (slot rules) of ADR 0031."""
    errors = [
        f"plan row {r['area']}/{r['draw']}: section {r['section_id']} is not in sections.jsonl"
        for r in rows
        if r["section_id"] not in section_ids
    ]
    errors += [
        f"slot {r['slot_id']}: skip reason {r['skip_reason']!r} not allowed"
        for r in rows
        if r["status"] == "skipped" and r["skip_reason"] not in CATALOGUE_SKIP_REASONS
    ]
    findings = []
    used = [r for r in rows if r["status"] == "used"]
    known = {q["question_id"] for q in questions}
    findings += [
        f"slot {r['slot_id']}: question {r['question_id']} is not in the catalogue"
        for r in used
        if r["question_id"] not in known
    ]
    for q in questions:
        qid = q["question_id"]
        own = [r for r in used if r["question_id"] == qid]
        if len(own) != 1:
            findings.append(f"{qid}: belongs to {len(own)} slots, needs exactly 1")
            continue
        row = own[0]
        if q["difficulty"] != row["class"]:
            findings.append(f"{qid}: difficulty {q['difficulty']} but slot {row['slot_id']} is {row['class']}")
        if row["section_id"] not in {s["section_id"] for s in relevant.get(qid, [])}:
            findings.append(
                f"{qid}: starting section {row['section_id']} of slot {row['slot_id']} is not annotated"
            )
    return errors, findings


def plan_summary(rows: list[dict]) -> list[str]:
    status = {s: sum(1 for r in rows if r["status"] == s) for s in ("used", "open", "skipped")}
    reasons = {}
    for r in rows:
        if r["status"] == "skipped":
            reasons[r["skip_reason"]] = reasons.get(r["skip_reason"], 0) + 1
    detail = ", ".join(f"{k} {v}" for k, v in sorted(reasons.items()))
    line = f"Slots: {status['used']} used, {status['open']} open, {status['skipped']} skipped"
    return [line + (f" ({detail})" if detail else "")]
```

In `src/catalogue.py`:
- import `CATALOGUE_PLAN_FILE` from config and `from catalogue_plan import plan_findings, plan_summary, read_plan,
  write_plan`;
- add the parameter `plan_file: Path = CATALOGUE_PLAN_FILE` to `check` (after `pilot_dir`);
- in `check`, directly before `report.lines = _overview(...)`, insert:

```python
    try:
        plan = read_plan(plan_file)
    except (FileNotFoundError, ValueError) as error:
        report.errors.append(str(error))
        plan = None
    plan_lines: list[str] = []
    if plan is not None:
        errors, findings = plan_findings(plan, questions, relevant, set(corpus.by_id))
        report.errors += errors
        report.findings += findings
        plan_lines = plan_summary(plan)
```

  and change the final assignment to `report.lines = _overview(corpus, questions, truth, relevant, areas) +
  plan_lines`;
- `freeze_catalogue` and `main` pass `plan_file` on (`freeze_catalogue(..., plan_file: Path = CATALOGUE_PLAN_FILE)`
  calls `check(corpus, questions_file, ground_truth_file, pilot_dir, plan_file)`; `main` passes
  `CATALOGUE_PLAN_FILE`);
- in `main`, add the subcommand `commands.add_parser("plan", help="draw the sampling plan once (ADR 0031)")` and,
  before `report = check(...)`:

```python
    if args.command == "plan":
        try:
            count = write_plan(corpus, CATALOGUE_PLAN_FILE)
        except (FileExistsError, ValueError) as error:
            print(error, file=sys.stderr)
            return 1
        print(f"{count} plan rows -> {CATALOGUE_PLAN_FILE}")
        return 0
```

In `tests/test_freeze.py`, pass `plan_file=write_plan_for(tmp_path, valid_rows())` as keyword to every
`freeze_catalogue` call (and `valid_rows()[:47]` for the failing-catalogue test).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest -q`
Expected: all pass (≈ 291).

- [ ] **Step 5: Commit**

```bash
git add src tests
git commit -m "feat(catalogue): Slots überspringen und Planregeln in der Prüfung"
```

---

### Task 3: Review log, its rules in `check`, and the freeze extension

**Files:**
- Create: `src/catalogue_review.py`
- Modify: `src/catalogue.py` (`check` gets `review_file`; `freeze_catalogue` records plan and review; `plan`
  creates the empty review file)
- Modify: `src/freeze.py` (`write_freeze(..., recorded: tuple[Path, ...] = ())`)
- Create: `tests/test_catalogue_review.py`; Modify: `tests/test_catalogue.py`, `tests/test_freeze.py`

**Interfaces:**
- Produces: `REVIEW_HEADER: list[str]`; `read_review(path) -> list[dict]` (missing file → `[]`);
  `save_review(path, rows) -> None`; `ensure_review_file(path) -> None`;
  `review_errors(rows, question_ids: set[str], section_ids: set[str]) -> list[str]`;
  `decide(path, index: int, decision: str, reason: str, today: str) -> dict`; `review_summary(rows) -> str`;
  `catalogue.check(..., review_file=CATALOGUE_REVIEW_FILE)`;
  `freeze.write_freeze(questions, truth, sections, documents, freeze_file, summary, recorded=())`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_catalogue_review.py`:

```python
import pytest

from catalogue_review import (
    REVIEW_HEADER,
    decide,
    ensure_review_file,
    read_review,
    review_errors,
    review_summary,
    save_review,
)


def row(**kw):
    base = dict.fromkeys(REVIEW_HEADER, "")
    base.update(round="1", question_id="Q001", kind="wording", suggestion="Say which hook.",
                decision="open")
    base.update(kw)
    return base


def test_missing_file_is_empty_and_ensure_writes_the_header(tmp_path):
    path = tmp_path / "catalogue_review.csv"
    assert read_review(path) == []
    ensure_review_file(path)
    assert path.read_text(encoding="utf-8") == ",".join(REVIEW_HEADER) + "\n"
    ensure_review_file(path)  # never overwrites
    save_review(path, [row()])
    assert read_review(path) == [row()]


def test_review_errors():
    rows = [
        row(),
        row(kind="guess"),
        row(decision="maybe"),
        row(question_id="Q999"),
        row(kind="missing_section", section_id=""),
        row(kind="missing_section", section_id="D099#x"),
        row(kind="wording", section_id="D001#ref"),
        row(decision="rejected", reason=""),
        row(round="x"),
    ]
    errors = review_errors(rows, {"Q001"}, {"D001#ref"})
    assert len(errors) == 8
    assert errors[0].startswith("review row 3: unknown kind 'guess'")


def test_decide_sets_decision_reason_and_date(tmp_path):
    path = tmp_path / "r.csv"
    save_review(path, [row(), row(kind="fact")])
    decided = decide(path, 1, "rejected", "the guide says so", "2026-10-20")
    assert (decided["decision"], decided["reason"], decided["date"]) == (
        "rejected", "the guide says so", "2026-10-20")
    assert read_review(path)[1] == decided and read_review(path)[0]["decision"] == "open"
    with pytest.raises(ValueError, match="already decided"):
        decide(path, 1, "accepted", "", "2026-10-20")
    with pytest.raises(ValueError, match="needs a reason"):
        decide(path, 0, "rejected", " ", "2026-10-20")
    with pytest.raises(ValueError, match="accepted or rejected"):
        decide(path, 0, "open", "", "2026-10-20")


def test_review_summary():
    rows = [row(), row(kind="fact", decision="accepted"),
            row(kind="missing_section", section_id="D001#ref", decision="accepted"),
            row(decision="rejected", reason="no")]
    assert review_summary(rows) == (
        "AI review: 4 suggestions, 2 accepted (missing_section 1, fact 1), 1 rejected, 1 open")
```

Append to `tests/test_catalogue.py`:

```python
def test_open_review_rows_warn_in_draft_and_fail_strictly(corpus, tmp_path, pilot):
    rows = valid_rows()
    questions, truth = write_catalogue(tmp_path, rows)
    review = tmp_path / "catalogue_review.csv"
    review.write_text(
        "round,question_id,kind,suggestion,section_id,decision,reason,date\n"
        "1,Q001,wording,Say which hook.,,open,,\n",
        encoding="utf-8",
    )
    report = check(corpus, questions, truth, pilot_dir=pilot,
                   plan_file=write_plan_for(tmp_path, rows), review_file=review)
    assert report.errors == []
    assert "1 review suggestion(s) still open" in report.findings
    assert exit_code(report, draft=True) == 0 and exit_code(report, draft=False) == 1
    assert any(line.startswith("AI review: 1 suggestions") for line in report.lines)
```

Append to `tests/test_freeze.py`:

```python
def test_freeze_records_plan_and_review(corpus, main_catalogue, pilot, tmp_path):
    questions, truth, sections, documents = main_catalogue
    plan = write_plan_for(tmp_path, valid_rows())
    review = tmp_path / "catalogue_review.csv"
    review.write_text("round,question_id,kind,suggestion,section_id,decision,reason,date\n")
    out = tmp_path / "catalogue_freeze.json"
    record = freeze_catalogue(corpus, questions, truth, out, pilot, sections, documents,
                              plan_file=plan, review_file=review)
    assert record["sha256"]["catalogue_plan.csv"] == sha256_of(plan)
    assert record["sha256"]["catalogue_review.csv"] == sha256_of(review)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_catalogue_review.py tests/test_catalogue.py tests/test_freeze.py -q`
Expected: FAIL (`ModuleNotFoundError: No module named 'catalogue_review'`).

- [ ] **Step 3: Write `src/catalogue_review.py`**

```python
"""AI review log of the question catalogue (ADR 0031).

After each block, Claude appends suggestions with decision `open` (missed sections, wording,
facts, class), reading only the questions, the annotation and the corpus text (ADR 0027). Jonas
accepts or rejects each one with a reason; the freeze refuses while any row is open. The
summary line goes into the AI disclosure of the thesis.
"""

import csv
from pathlib import Path

from config import CATALOGUE_REVIEW_DECISIONS, CATALOGUE_REVIEW_FILE, CATALOGUE_REVIEW_KINDS

REVIEW_HEADER = [
    "round", "question_id", "kind", "suggestion", "section_id", "decision", "reason", "date",
]  # fmt: skip


def read_review(path: Path = CATALOGUE_REVIEW_FILE) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        records = [r for r in csv.reader(f) if r]
    if not records or records[0] != REVIEW_HEADER:
        found = records[0] if records else []
        raise ValueError(f"{path} has columns {found}, expected {REVIEW_HEADER}")
    for number, record in enumerate(records[1:], start=2):
        if len(record) != len(REVIEW_HEADER):
            raise ValueError(f"{path}: row {number} has {len(record)} fields")
    return [dict(zip(REVIEW_HEADER, r, strict=True)) for r in records[1:]]


def save_review(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_HEADER, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def ensure_review_file(path: Path = CATALOGUE_REVIEW_FILE) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        save_review(path, [])


def review_errors(rows: list[dict], question_ids: set[str], section_ids: set[str]) -> list[str]:
    errors = []
    for number, r in enumerate(rows, start=2):
        where = f"review row {number}"
        if not r["round"].isdigit():
            errors.append(f"{where}: round {r['round']!r} is not a number")
        if r["kind"] not in CATALOGUE_REVIEW_KINDS:
            errors.append(f"{where}: unknown kind {r['kind']!r}")
        if r["decision"] not in CATALOGUE_REVIEW_DECISIONS:
            errors.append(f"{where}: unknown decision {r['decision']!r}")
        if r["question_id"] not in question_ids:
            errors.append(f"{where}: question {r['question_id']} is not in the catalogue")
        if r["kind"] == "missing_section" and r["section_id"] not in section_ids:
            errors.append(f"{where}: missing_section needs a known section_id, got {r['section_id']!r}")
        if r["kind"] != "missing_section" and r["section_id"]:
            errors.append(f"{where}: section_id only belongs to missing_section")
        if r["decision"] == "rejected" and not r["reason"].strip():
            errors.append(f"{where}: a rejected suggestion needs a reason")
    return errors


def decide(path: Path, index: int, decision: str, reason: str, today: str) -> dict:
    """Record Jonas' decision on the open suggestion at `index` (0-based, file order)."""
    if decision not in CATALOGUE_REVIEW_DECISIONS or decision == "open":
        raise ValueError("decision must be accepted or rejected")
    if decision == "rejected" and not reason.strip():
        raise ValueError("a rejected suggestion needs a reason")
    rows = read_review(path)
    row = rows[index]
    if row["decision"] != "open":
        raise ValueError(f"suggestion {index + 1} is already decided ({row['decision']})")
    row.update(decision=decision, reason=reason.strip(), date=today)
    save_review(path, rows)
    return row


def review_summary(rows: list[dict]) -> str:
    accepted = [r for r in rows if r["decision"] == "accepted"]
    kinds = ", ".join(
        f"{k} {n}"
        for k in CATALOGUE_REVIEW_KINDS
        if (n := sum(1 for r in accepted if r["kind"] == k))
    )
    rejected = sum(1 for r in rows if r["decision"] == "rejected")
    still_open = sum(1 for r in rows if r["decision"] == "open")
    return (
        f"AI review: {len(rows)} suggestions, {len(accepted)} accepted"
        + (f" ({kinds})" if kinds else "")
        + f", {rejected} rejected, {still_open} open"
    )
```

In `src/freeze.py`, give `write_freeze` the keyword `recorded: tuple[Path, ...] = ()` and hash those files too:
`"sha256": {f.name: sha256_of(f) for f in (questions_file, ground_truth_file, sections_file, documents_file,
*recorded)}`; docstring: "Further files (`recorded`) are hashed for the record only; `require_frozen` checks the
four retrieval inputs."

In `src/catalogue.py`:
- import `CATALOGUE_REVIEW_FILE` and `from catalogue_review import ensure_review_file, read_review, review_errors,
  review_summary`;
- `check(..., plan_file=CATALOGUE_PLAN_FILE, review_file=CATALOGUE_REVIEW_FILE)`; after the plan block insert:

```python
    try:
        review = read_review(review_file)
    except ValueError as error:
        report.errors.append(str(error))
        review = []
    report.errors += review_errors(
        review, {q["question_id"] for q in questions}, set(corpus.by_id)
    )
    still_open = sum(1 for r in review if r["decision"] == "open")
    if still_open:
        report.findings.append(f"{still_open} review suggestion(s) still open")
    plan_lines.append(review_summary(review))
```

- `freeze_catalogue(..., plan_file=CATALOGUE_PLAN_FILE, review_file=CATALOGUE_REVIEW_FILE)` passes both to `check`
  and calls `write_freeze(..., summary, recorded=tuple(p for p in (plan_file, review_file) if p.exists()))`;
  `main` passes `CATALOGUE_PLAN_FILE, CATALOGUE_REVIEW_FILE`;
- the `plan` subcommand calls `ensure_review_file(CATALOGUE_REVIEW_FILE)` after writing the plan.

Update `run_check` in `tests/test_catalogue.py` to pass `review_file=tmp_path / "catalogue_review.csv"` (absent →
empty), the `cli` fixture to monkeypatch `CATALOGUE_REVIEW_FILE` to `tmp_path / "catalogue_review.csv"`, and the
existing `freeze_catalogue` calls in `tests/test_freeze.py` to pass `review_file=tmp_path / "review.csv"`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest -q && uv run pyright src | tail -1`
Expected: all pass; `0 errors`.

- [ ] **Step 5: Commit**

```bash
git add src tests
git commit -m "feat(catalogue): Protokoll der KI-Durchsicht und Freeze mit Plan und Durchsicht"
```

---

### Task 4: Store operations for the editor

**Files:**
- Create: `src/catalogue_store.py`
- Create: `tests/test_catalogue_store.py`

**Interfaces:**
- Consumes: `Corpus`, `read_plan`, `save_plan`, `slot_row`, `mark_used`, `read_review`, `decide`, `content_words`,
  `same_word`, `QUESTIONS_HEADER`, `GROUND_TRUTH_HEADER`.
- Produces: module globals `QUESTIONS_FILE, GROUND_TRUTH_FILE, CATALOGUE_PLAN_FILE, CATALOGUE_REVIEW_FILE,
  CATALOGUE_FREEZE_FILE, DOCUMENTS_FILE, SECTIONS_FILE, PILOT_DIR` (imported from config, read at call time so tests
  and the editor tests can monkeypatch them); `load_catalogue() -> tuple[list[dict], dict[str, dict]]`;
  `next_question_id(questions) -> str`; `is_frozen() -> bool`;
  `save_question(corpus, slot_id, question, qtype, answer, notes, section_ids, question_id=None) -> str`;
  `accept_suggestion(corpus, index, reason, today) -> dict`; `reject_suggestion(index, reason, today) -> dict`;
  `highlight(text: str, words: list[str]) -> str` (HTML-escaped text with `<mark class="hl">`).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_catalogue_store.py`:

```python
import pytest

import catalogue_store as store
from catalogue_plan import read_plan, write_plan
from catalogue_review import REVIEW_HEADER, read_review, save_review

SMALL = {
    "slots": {"api": 1, "style-guide": 1, "guide": 1},
    "reserve": {"api": 1, "style-guide": 0, "guide": 1},
    "classes": {"single": 1, "multi-section": 1, "paraphrase": 1},
}


@pytest.fixture
def files(corpus, tmp_path, monkeypatch):
    paths = {
        "QUESTIONS_FILE": tmp_path / "questions.csv",
        "GROUND_TRUTH_FILE": tmp_path / "ground_truth.csv",
        "CATALOGUE_PLAN_FILE": tmp_path / "catalogue_plan.csv",
        "CATALOGUE_REVIEW_FILE": tmp_path / "catalogue_review.csv",
        "CATALOGUE_FREEZE_FILE": tmp_path / "catalogue_freeze.json",
    }
    for name, path in paths.items():
        monkeypatch.setattr(store, name, path)
    write_plan(corpus, paths["CATALOGUE_PLAN_FILE"], seed=3, **SMALL)
    return paths


def test_empty_catalogue_loads_and_numbers_from_q001(files):
    assert store.load_catalogue() == ([], {})
    assert store.next_question_id([]) == "Q001"
    assert store.next_question_id([{"question_id": "Q009"}, {"question_id": "Q010"}]) == "Q011"


def test_save_writes_both_files_and_uses_the_slot(corpus, files):
    plan = read_plan(files["CATALOGUE_PLAN_FILE"])
    s01 = next(r for r in plan if r["slot_id"] == "S01")
    qid = store.save_question(corpus, "S01", " What does ref() return? ", "factual",
                              "A reactive ref object.", "", ["D002#once"])
    assert qid == "Q001"
    questions, truth = store.load_catalogue()
    assert questions == [{"question_id": "Q001", "question": "What does ref() return?",
                          "type": "factual", "difficulty": s01["class"], "notes": ""}]
    sids = truth["Q001"]["relevant_section_ids"].split(";")
    assert sids[0] == s01["section_id"] and "D002#once" in sids  # starting section always first
    docs = truth["Q001"]["relevant_doc_ids"].split(";")
    assert docs == list(dict.fromkeys(s.split("#")[0] for s in sids))
    row = next(r for r in read_plan(files["CATALOGUE_PLAN_FILE"]) if r["slot_id"] == "S01")
    assert (row["status"], row["question_id"]) == ("used", "Q001")
    assert files["QUESTIONS_FILE"].read_text(encoding="utf-8").endswith("\n")


def test_edit_keeps_id_and_cannot_drop_the_starting_section(corpus, files):
    store.save_question(corpus, "S01", "Q one?", "factual", "A.", "", [])
    s01 = next(r for r in read_plan(files["CATALOGUE_PLAN_FILE"]) if r["slot_id"] == "S01")
    store.save_question(corpus, "S01", "Q one, edited?", "conceptual", "B.", "n", ["D002#cleanup"],
                        question_id="Q001")
    questions, truth = store.load_catalogue()
    assert [q["question"] for q in questions] == ["Q one, edited?"]
    assert truth["Q001"]["relevant_section_ids"].split(";")[0] == s01["section_id"]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"question": " "}, "question is empty"),
        ({"answer": ""}, "reference answer is empty"),
        ({"qtype": "trivia"}, "unknown type"),
        ({"section_ids": ["D099#x"]}, "unknown section"),
        ({"slot_id": "S09"}, "no slot S09"),
    ],
)
def test_save_refuses_invalid_input(corpus, files, kwargs, message):
    args = {"slot_id": "S01", "question": "Q?", "qtype": "factual", "answer": "A.", "notes": "",
            "section_ids": []} | kwargs
    with pytest.raises(ValueError, match=message):
        store.save_question(corpus, **args)
    assert not files["QUESTIONS_FILE"].exists()


def test_save_refuses_after_the_freeze(corpus, files):
    files["CATALOGUE_FREEZE_FILE"].write_text("{}", encoding="utf-8")
    with pytest.raises(PermissionError, match="frozen"):
        store.save_question(corpus, "S01", "Q?", "factual", "A.", "", [])


def test_accepting_a_missing_section_adds_it(corpus, files):
    store.save_question(corpus, "S01", "Q?", "factual", "A.", "", [])
    save_review(files["CATALOGUE_REVIEW_FILE"], [
        dict.fromkeys(REVIEW_HEADER, "") | {"round": "1", "question_id": "Q001",
         "kind": "missing_section", "suggestion": "Also cleanup.", "section_id": "D002#cleanup",
         "decision": "open"},
        dict.fromkeys(REVIEW_HEADER, "") | {"round": "1", "question_id": "Q001", "kind": "wording",
         "suggestion": "Name the hook.", "decision": "open"},
    ])
    store.accept_suggestion(corpus, 0, "", "2026-10-20")
    assert "D002#cleanup" in store.load_catalogue()[1]["Q001"]["relevant_section_ids"]
    store.reject_suggestion(1, "already clear", "2026-10-20")
    assert [r["decision"] for r in read_review(files["CATALOGUE_REVIEW_FILE"])] == ["accepted", "rejected"]


def test_highlight_marks_matching_words_and_escapes_html():
    out = store.highlight("Use <script setup> with Watchers.", ["watcher"])
    assert out == "Use &lt;script setup&gt; with <mark class=\"hl\">Watchers</mark>."
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_catalogue_store.py -q`
Expected: FAIL (`ModuleNotFoundError: No module named 'catalogue_store'`).

- [ ] **Step 3: Write `src/catalogue_store.py`**

```python
"""Reads and writes the catalogue for the editor (ADR 0029, 0031).

Only the catalogue files and the corpus; never chunks, vectors or retrieval results (ADR 0027).
Paths are module globals from config, read at call time, so the editor and its tests share them.
Every write is refused once the freeze record exists (ADR 0030).
"""

import csv
import html
import re

from catalogue import Corpus, same_word
from catalogue_plan import mark_used, read_plan, save_plan, slot_row
from catalogue_review import decide, read_review
from config import (
    CATALOGUE_FREEZE_FILE,
    CATALOGUE_PLAN_FILE,
    CATALOGUE_REVIEW_FILE,
    DOCUMENTS_FILE,
    GROUND_TRUTH_FILE,
    ID_SEPARATOR,
    PILOT_DIR,
    QUESTION_TYPES,
    QUESTIONS_FILE,
    SECTIONS_FILE,
)
from retrieve import GROUND_TRUTH_HEADER, QUESTIONS_HEADER

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _read(path, header: list[str]) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames and list(reader.fieldnames) != header:
            raise ValueError(f"{path} has columns {reader.fieldnames}, expected {header}")
        return [dict(r) for r in reader]


def _write(path, header: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: r["question_id"]))


def load_catalogue() -> tuple[list[dict], dict[str, dict]]:
    """Questions (sorted by ID) and ground truth by question ID; empty files are fine."""
    questions = sorted(_read(QUESTIONS_FILE, QUESTIONS_HEADER), key=lambda q: q["question_id"])
    truth = {r["question_id"]: r for r in _read(GROUND_TRUTH_FILE, GROUND_TRUTH_HEADER)}
    return questions, truth


def next_question_id(questions: list[dict]) -> str:
    numbers = [int(q["question_id"][1:]) for q in questions if q["question_id"][1:].isdigit()]
    return f"Q{max(numbers, default=0) + 1:03d}"


def is_frozen() -> bool:
    return CATALOGUE_FREEZE_FILE.exists()


def _refuse_if_frozen() -> None:
    if is_frozen():
        raise PermissionError("the catalogue is frozen (ADR 0030); it can no longer be edited")


def save_question(
    corpus: Corpus,
    slot_id: str,
    question: str,
    qtype: str,
    answer: str,
    notes: str,
    section_ids: list[str],
    question_id: str | None = None,
) -> str:
    """Insert or update the question of a slot; the slot's starting section always comes first."""
    _refuse_if_frozen()
    question, answer, notes = question.strip(), answer.strip(), notes.strip()
    if not question:
        raise ValueError("question is empty")
    if not answer:
        raise ValueError("reference answer is empty")
    if qtype not in QUESTION_TYPES:
        raise ValueError(f"unknown type {qtype!r}; allowed {list(QUESTION_TYPES)}")
    plan = read_plan(CATALOGUE_PLAN_FILE)
    row = slot_row(plan, slot_id)
    unknown = [s for s in section_ids if s not in corpus.by_id]
    if unknown:
        raise ValueError(f"unknown section IDs {unknown}")
    ids = list(dict.fromkeys([row["section_id"], *section_ids]))
    docs = list(dict.fromkeys(corpus.by_id[s]["doc_id"] for s in ids))
    questions, truth = load_catalogue()
    qid = question_id or (row["question_id"] if row["status"] == "used" else next_question_id(questions))
    mark_used(plan, slot_id, qid)
    questions = [q for q in questions if q["question_id"] != qid] + [
        {"question_id": qid, "question": question, "type": qtype, "difficulty": row["class"],
         "notes": notes}
    ]
    truth[qid] = {"question_id": qid, "expected_answer": answer,
                  "relevant_doc_ids": ID_SEPARATOR.join(docs),
                  "relevant_section_ids": ID_SEPARATOR.join(ids)}
    _write(QUESTIONS_FILE, QUESTIONS_HEADER, questions)
    _write(GROUND_TRUTH_FILE, GROUND_TRUTH_HEADER, list(truth.values()))
    save_plan(CATALOGUE_PLAN_FILE, plan)
    return qid


def accept_suggestion(corpus: Corpus, index: int, reason: str, today: str) -> dict:
    """Accept a review suggestion; a missing_section is added to the question's annotation."""
    _refuse_if_frozen()
    row = read_review(CATALOGUE_REVIEW_FILE)[index]
    if row["kind"] == "missing_section" and row["decision"] == "open":
        questions, truth = load_catalogue()
        entry = truth[row["question_id"]]
        ids = list(dict.fromkeys([*entry["relevant_section_ids"].split(ID_SEPARATOR),
                                  row["section_id"]]))
        entry["relevant_section_ids"] = ID_SEPARATOR.join(ids)
        entry["relevant_doc_ids"] = ID_SEPARATOR.join(
            dict.fromkeys(corpus.by_id[s]["doc_id"] for s in ids)
        )
        _write(GROUND_TRUTH_FILE, GROUND_TRUTH_HEADER, list(truth.values()))
    return decide(CATALOGUE_REVIEW_FILE, index, "accepted", reason, today)


def reject_suggestion(index: int, reason: str, today: str) -> dict:
    _refuse_if_frozen()
    return decide(CATALOGUE_REVIEW_FILE, index, "rejected", reason, today)


def highlight(text: str, words: list[str]) -> str:
    """HTML-escaped text; tokens matching any of `words` (ADR 0029 word rule) are marked."""
    out, last = [], 0
    for match in TOKEN_RE.finditer(text):
        out.append(html.escape(text[last : match.start()]))
        token = match.group()
        if any(same_word(token.lower(), w) for w in words):
            out.append(f'<mark class="hl">{html.escape(token)}</mark>')
        else:
            out.append(html.escape(token))
        last = match.end()
    out.append(html.escape(text[last:]))
    return "".join(out)
```

Note on `accept_suggestion`: it reads the review row before deciding so an already decided row raises in
`decide` without touching the ground truth: guard the annotation change with `row["decision"] == "open"` (as
written).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_catalogue_store.py -q && uv run pytest -q | tail -1 && uv run pyright src | tail -1`
Expected: 12 passed; full suite passes; `0 errors`.

- [ ] **Step 5: Commit**

```bash
git add src/catalogue_store.py tests/test_catalogue_store.py
git commit -m "feat(catalogue): Lese- und Schreiboperationen für den Editor"
```

---

### Task 5: The editor UI

**Files:**
- Create: `app/catalogue_editor.py`
- Create: `.streamlit/config.toml`
- Create: `tests/test_catalogue_editor.py`

**Interfaces:**
- Consumes: `catalogue.load_corpus`, `find`, `class_findings`, `shared_words`, `heading_texts`, `content_words`,
  `normalised_question`; `catalogue_plan.read_plan`, `skip_slot`, `plan_summary`; `catalogue_review.read_review`;
  `catalogue_store.*`; config value sets.
- Produces: `uv run streamlit run app/catalogue_editor.py`; widget keys used by tests: `slot`, `question_<slot>`,
  `qtype_<slot>`, `answer_<slot>`, `notes_<slot>` (per slot, so switching slots never carries text over), `save`, `skip_reason`, `skip`, `find`, `add_section`, `accept_<i>`, `reject_<i>`,
  `reason_<i>`.

- [ ] **Step 1: Confirm the design direction before building**

Re-read the spec's "Visual design" section (reading desk; serif source page; highlighter as the one memorable
element; palette; sentence case; plain verbs). Check the Streamlit theme options available in 1.58:

Run: `uv run streamlit config show 2>/dev/null | grep -n -E "^\[theme|primaryColor|backgroundColor|font" | head -30`
Expected: a `[theme]` section; if `[theme.light]`/`[theme.dark]` sections are listed, use them; otherwise set the
light palette in `[theme]` and rely on Streamlit's dark mode for dark (ledger a ruling).

- [ ] **Step 2: Write the failing UI tests**

Create `tests/test_catalogue_editor.py`:

```python
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import catalogue_store as store
from catalogue_plan import read_plan, write_plan

APP = str(Path(__file__).resolve().parent.parent / "app" / "catalogue_editor.py")
SMALL = {
    "slots": {"api": 1, "style-guide": 1, "guide": 1},
    "reserve": {"api": 1, "style-guide": 0, "guide": 1},
    "classes": {"single": 1, "multi-section": 1, "paraphrase": 1},
}


@pytest.fixture
def app(corpus_files, corpus, tmp_path, monkeypatch, pilot):
    docs, sections = corpus_files
    paths = {
        "QUESTIONS_FILE": tmp_path / "questions.csv",
        "GROUND_TRUTH_FILE": tmp_path / "ground_truth.csv",
        "CATALOGUE_PLAN_FILE": tmp_path / "catalogue_plan.csv",
        "CATALOGUE_REVIEW_FILE": tmp_path / "catalogue_review.csv",
        "CATALOGUE_FREEZE_FILE": tmp_path / "catalogue_freeze.json",
        "DOCUMENTS_FILE": docs,
        "SECTIONS_FILE": sections,
        "PILOT_DIR": pilot,
    }
    for name, path in paths.items():
        monkeypatch.setattr(store, name, path)
    write_plan(corpus, paths["CATALOGUE_PLAN_FILE"], seed=3, **SMALL)
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    return at, paths


def test_renders_the_first_open_slot_without_errors(app):
    at, _ = app
    assert not at.exception
    assert any("Slot S01" in h.value for h in at.subheader)


def test_save_writes_the_catalogue(app):
    at, paths = app
    at.text_area(key="question_S01").input("What does it return?")
    at.text_area(key="answer_S01").input("A reactive ref object.")
    at.selectbox(key="qtype_S01").select("factual")
    at.button(key="save").click().run()
    assert not at.exception
    assert "Q001" in paths["QUESTIONS_FILE"].read_text(encoding="utf-8")


def test_skip_moves_to_the_reserve_section(app):
    at, paths = app
    before = next(r for r in read_plan(paths["CATALOGUE_PLAN_FILE"]) if r["slot_id"] == "S01")
    at.selectbox(key="skip_reason").select("code-or-links")
    at.button(key="skip").click().run()
    assert not at.exception
    after = next(r for r in read_plan(paths["CATALOGUE_PLAN_FILE"])
                 if r["slot_id"] == "S01" and r["status"] == "open")
    assert after["section_id"] != before["section_id"]


def test_hand_edited_files_are_picked_up_on_rerun(app):
    at, paths = app
    paths["QUESTIONS_FILE"].write_text(
        "question_id,question,type,difficulty,notes\nQ007,Hand made?,factual,single,\n",
        encoding="utf-8")
    at.run()
    assert not at.exception
    assert any("1 of 48" in m.value for m in at.sidebar.markdown)


def test_frozen_catalogue_is_read_only(app):
    at, paths = app
    paths["CATALOGUE_FREEZE_FILE"].write_text("{}", encoding="utf-8")
    at.run()
    assert any("frozen" in i.value for i in at.info)
    assert at.button(key="save").disabled
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_catalogue_editor.py -q`
Expected: FAIL (`AppTest` cannot find `app/catalogue_editor.py`).

- [ ] **Step 4: Write the theme and the editor**

Create `.streamlit/config.toml` (values from the spec's palette; if Step 1 showed no `[theme.light]`/`[theme.dark]`,
keep only the `[theme]` block with the light values):

```toml
[theme]
base = "light"
primaryColor = "#2457A6"
backgroundColor = "#FAFBFC"
secondaryBackgroundColor = "#F1F3F6"
textColor = "#1F2933"
borderColor = "#D9DEE4"
font = "sans-serif"

[theme.light]
primaryColor = "#2457A6"
backgroundColor = "#FAFBFC"
secondaryBackgroundColor = "#F1F3F6"
textColor = "#1F2933"

[theme.dark]
primaryColor = "#7AA5E8"
backgroundColor = "#15191E"
secondaryBackgroundColor = "#1D232A"
textColor = "#E4E8EC"

[client]
toolbarMode = "minimal"
```

Create `app/catalogue_editor.py`:

```python
"""Catalogue editor (ADR 0029, 0031): write and annotate the question catalogue.

Run: uv run streamlit run app/catalogue_editor.py

Shows only the corpus and the catalogue files; never chunks, strategies, retrieval results or
scores (ADR 0027). All reading and writing goes through src/catalogue_store.py.
"""

import html
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import streamlit as st  # noqa: E402

import catalogue  # noqa: E402
import catalogue_plan  # noqa: E402
import catalogue_review  # noqa: E402
import catalogue_store as store  # noqa: E402
from config import (  # noqa: E402
    AREA_MIN_QUESTIONS,
    CATALOGUE_SKIP_REASONS,
    DETAIL_MAX_ANSWER_WORDS,
    QUESTION_CLASSES,
    QUESTION_TYPES,
)

AREA_NAMES = {"api": "API reference", "guide": "Guide", "style-guide": "Style guide"}
SKIP_LABELS = {
    "code-or-links": "Only code or links",
    "too-short": "Too short to ask about",
    "duplicate-topic": "Same topic as an earlier slot",
    "no-answerable-content": "Nothing a question could ask",
}
CSS = """
<style>
.source {font-family: "Source Serif Pro", "Source Serif 4", Georgia, serif; font-size: 1.02rem;
  line-height: 1.7; max-width: 72ch; white-space: pre-wrap; overflow-wrap: anywhere;
  padding: 1.25rem 1.5rem; border: 1px solid var(--line); border-radius: 6px;
  background: var(--surface); color: var(--ink);}
.heading-path {color: var(--muted); font-size: 0.92rem; margin-bottom: 0.4rem;}
mark.hl {background: var(--marker); color: inherit; padding: 0 0.12em; border-radius: 2px;}
.checks {list-style: none; padding-left: 0; margin: 0.25rem 0 0.75rem;}
.checks li {margin: 0.15rem 0;}
.checks .ok {color: var(--ok);} .checks .problem {color: var(--problem);}
</style>
"""
LIGHT = {"line": "#D9DEE4", "surface": "#FFFFFF", "ink": "#1F2933", "muted": "#616E7C",
         "marker": "#FFE58A", "ok": "#2F7D4F", "problem": "#B3261E"}
DARK = {"line": "#2E3640", "surface": "#1D232A", "ink": "#E4E8EC", "muted": "#9AA5B1",
        "marker": "rgba(255, 214, 90, 0.35)", "ok": "#6CC48F", "problem": "#F2877F"}


@st.cache_resource
def load_corpus(documents: str, sections: str) -> catalogue.Corpus:
    return catalogue.load_corpus(Path(documents), Path(sections))


def palette_css() -> str:
    dark = getattr(getattr(st.context, "theme", None), "type", "light") == "dark"
    tokens = DARK if dark else LIGHT
    return "<style>:root {" + "".join(f"--{k}: {v};" for k, v in tokens.items()) + "}</style>"


def source_page(corpus: catalogue.Corpus, section: dict, words: list[str]) -> None:
    path = store.highlight(corpus.heading_path(section), words)
    st.markdown(f'<div class="heading-path">{path}</div>', unsafe_allow_html=True)
    body = store.highlight(corpus.text(section), words)
    st.markdown(f'<div class="source">{body}</div>', unsafe_allow_html=True)


def sidebar(questions: list[dict], plan: list[dict], review: list[dict]) -> None:
    total = sum(QUESTION_CLASSES.values())
    with st.sidebar:
        st.markdown(f"**{len(questions)} of {total} questions**")
        st.progress(min(len(questions) / total, 1.0))
        rows = ["| | " + " | ".join(QUESTION_CLASSES) + " |", "|---" * (len(QUESTION_CLASSES) + 1) + "|"]
        for qtype, quota in QUESTION_TYPES.items():
            cells = [sum(1 for q in questions if q["type"] == qtype and q["difficulty"] == c)
                     for c in QUESTION_CLASSES]
            rows.append(f"| {qtype} ({sum(cells)}/{quota}) | " + " | ".join(map(str, cells)) + " |")
        st.markdown("\n".join(rows))
        used = {r["question_id"]: r["area"] for r in plan if r["status"] == "used"}
        areas = "; ".join(
            f"{AREA_NAMES[a]} {sum(1 for v in used.values() if v == a)} of at least {n}"
            for a, n in AREA_MIN_QUESTIONS.items()
        )
        st.caption(f"Areas: {areas}")
        for line in catalogue_plan.plan_summary(plan):
            st.caption(line)
        st.caption(catalogue_review.review_summary(review))


def checks(corpus, row, question, answer, sections, questions, qid) -> list[tuple[bool, str]]:
    draft = {"question_id": qid or "new", "question": question, "type": "", "difficulty": row["class"]}
    found = catalogue.class_findings(corpus, draft, {"expected_answer": answer}, sections)
    items = [(not found, "Class rule met" if not found else "; ".join(found))]
    words = len(answer.split())
    if row["class"] == "detail":
        items.append((words <= DETAIL_MAX_ANSWER_WORDS,
                      f"Answer has {words} words (at most {DETAIL_MAX_ANSWER_WORDS})"))
    key = catalogue.normalised_question(question)
    twin = next((q["question_id"] for q in questions
                 if q["question_id"] != qid and catalogue.normalised_question(q["question"]) == key), None)
    if question.strip():
        items.append((twin is None, "No duplicate" if twin is None else f"Same wording as {twin}"))
    return items


def render_checks(items: list[tuple[bool, str]]) -> None:
    lis = "".join(
        f'<li class="{"ok" if ok else "problem"}">{"Met" if ok else "Not met"}: {html.escape(text)}</li>'
        for ok, text in items
    )
    st.markdown(f'<ul class="checks">{lis}</ul>', unsafe_allow_html=True)


def write_tab(corpus, plan, questions, truth, frozen: bool) -> None:
    slots = sorted({r["slot_id"] for r in plan if r["status"] in ("open", "used")})
    first_open = next((r["slot_id"] for r in sorted(plan, key=lambda r: r["slot_id"])
                       if r["status"] == "open"), slots[0])

    def label(sid: str) -> str:
        row = catalogue_plan.slot_row(plan, sid)
        return f"{sid}, {row['question_id']}" if row["status"] == "used" else f"{sid}, open"

    sid = st.selectbox("Slot", slots, index=slots.index(first_open), format_func=label, key="slot")
    row = catalogue_plan.slot_row(plan, sid)
    seed = corpus.by_id[row["section_id"]]
    qid = row["question_id"] if row["status"] == "used" else None
    saved_q = next((q for q in questions if q["question_id"] == qid), None)
    saved_t = truth.get(qid or "", {})
    st.subheader(f"Slot {sid}: {AREA_NAMES[row['area']]}, {row['class']}")

    extra_key = f"extra_{sid}"
    if extra_key not in st.session_state:
        saved_ids = saved_t.get("relevant_section_ids", "").split(";") if saved_t else []
        st.session_state[extra_key] = [s for s in saved_ids if s and s != seed["section_id"]]

    left, right = st.columns([6, 5], gap="large")
    with right:
        question = st.text_area("Question", value=saved_q["question"] if saved_q else "",
                                key=f"question_{sid}", height=110)
        types = list(QUESTION_TYPES)
        qtype = st.selectbox("Type", types, key=f"qtype_{sid}",
                             index=types.index(saved_q["type"]) if saved_q else 0)
        answer = st.text_area("Reference answer", value=saved_t.get("expected_answer", ""),
                              key=f"answer_{sid}", height=130)
        notes = st.text_input("Notes", value=saved_q["notes"] if saved_q else "", key=f"notes_{sid}")
        ids = [seed["section_id"], *st.session_state[extra_key]]
        sections = [corpus.by_id[s] for s in ids]
        st.markdown("**Relevant sections**")
        for s in sections:
            cols = st.columns([5, 1])
            cols[0].markdown(f"`{s['section_id']}` {corpus.heading_path(s)}")
            if s["section_id"] != seed["section_id"] and cols[1].button(
                "Remove", key=f"remove_{s['section_id']}", disabled=frozen
            ):
                st.session_state[extra_key].remove(s["section_id"])
                st.rerun()
        render_checks(checks(corpus, row, question, answer, sections, questions, qid))
        if st.button("Save question", type="primary", key="save", disabled=frozen):
            try:
                saved = store.save_question(corpus, sid, question, qtype, answer, notes,
                                            st.session_state[extra_key], question_id=qid)
                st.toast(f"Saved {saved}")
                st.rerun()
            except (ValueError, PermissionError) as error:
                st.error(str(error))
        if row["status"] == "open":
            with st.expander("Skip this section"):
                reason = st.selectbox("Reason", list(CATALOGUE_SKIP_REASONS), key="skip_reason",
                                      format_func=SKIP_LABELS.get)
                if st.button("Skip this section", key="skip", disabled=frozen):
                    catalogue_plan.skip_slot(store.CATALOGUE_PLAN_FILE, sid, reason)
                    st.rerun()

    with left:
        words = catalogue.shared_words(question, catalogue.heading_texts(corpus, sections)) if question else []
        source_page(corpus, seed, words)
        term = st.text_input("Find more sections", key="find", placeholder="Search the documentation")
        if term.strip():
            hits = catalogue.find(corpus, term)
            if not hits:
                st.caption("No section contains this text.")
            else:
                options = {h[0]["section_id"]: h for h in hits}
                pick = st.selectbox(
                    f"{len(hits)} sections", list(options), key="hit",
                    format_func=lambda s: f"{s}  {corpus.heading_path(options[s][0])}",
                )
                source_page(corpus, options[pick][0], words)
                if st.button("Add this section", key="add_section", disabled=frozen
                             or pick in ids):
                    st.session_state[extra_key].append(pick)
                    st.rerun()


def review_tab(corpus, review: list[dict], questions: list[dict], frozen: bool) -> None:
    text = {q["question_id"]: q["question"] for q in questions}
    pending = [(i, r) for i, r in enumerate(review) if r["decision"] == "open"]
    if not pending:
        st.info("No open suggestions.")
    for i, r in pending:
        with st.container(border=True):
            st.markdown(f"**{r['question_id']}**: {text.get(r['question_id'], '')}")
            st.markdown(f"{r['kind'].replace('_', ' ').capitalize()}: {r['suggestion']}")
            if r["section_id"]:
                source_page(corpus, corpus.by_id[r["section_id"]], [])
            reason = st.text_input("Reason", key=f"reason_{i}")
            a, b = st.columns(2)
            today = date.today().isoformat()
            if a.button("Accept", key=f"accept_{i}", disabled=frozen):
                store.accept_suggestion(corpus, i, reason, today)
                st.rerun()
            if b.button("Reject", key=f"reject_{i}", disabled=frozen):
                try:
                    store.reject_suggestion(i, reason, today)
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
    decided = [r for r in review if r["decision"] != "open"]
    if decided:
        with st.expander(f"Decided ({len(decided)})"):
            for r in decided:
                st.markdown(f"{r['question_id']}, {r['kind']}: {r['decision']} ({r['reason'] or 'no reason'})")


def main() -> None:
    st.set_page_config(page_title="Question catalogue", layout="wide")
    st.markdown(CSS + palette_css(), unsafe_allow_html=True)
    corpus = load_corpus(str(store.DOCUMENTS_FILE), str(store.SECTIONS_FILE))
    try:
        plan = catalogue_plan.read_plan(store.CATALOGUE_PLAN_FILE)
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        return
    questions, truth = store.load_catalogue()
    review = catalogue_review.read_review(store.CATALOGUE_REVIEW_FILE)
    frozen = store.is_frozen()
    sidebar(questions, plan, review)
    if frozen:
        st.info("The catalogue is frozen (ADR 0030). You can read it, but not change it.")
    open_count = sum(1 for r in review if r["decision"] == "open")
    write, rev = st.tabs(["Write", f"Review ({open_count})" if open_count else "Review"])
    with write:
        write_tab(corpus, plan, questions, truth, frozen)
    with rev:
        review_tab(corpus, review, questions, frozen)


main()
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_catalogue_editor.py -q`
Expected: 5 passed. Then the full suite and Pyright: `uv run pytest -q | tail -1 && uv run pyright | tail -1`
(only the 6 pre-existing errors).

- [ ] **Step 6: Commit**

```bash
git add app/catalogue_editor.py .streamlit/config.toml tests/test_catalogue_editor.py
git commit -m "feat(app): Editor für den Fragenkatalog"
```

---

### Task 6: Browser check, audit and polish (inline, real machine)

**Files:**
- Modify (polish only): `app/catalogue_editor.py`, `.streamlit/config.toml`

- [ ] **Step 1: Prepare a throwaway workspace** (never the real `data/evaluation` files)

```bash
SP=/tmp/claude-1000/<session>/scratchpad/editor-check   # the session's scratchpad
mkdir -p $SP && cp data/processed/documents.jsonl data/processed/sections.jsonl $SP/
```

Write `$SP/run_editor.py` (never committed) and draw a throwaway plan there with the real config:

```python
import runpy
import sys
from pathlib import Path

ROOT = Path("/home/jonas/Documents/Code/PaperLab/scientific-papers/thesis/thesis-semester-7-rag-chunking_jonas/code")
SP = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
import catalogue_store as store  # noqa: E402

for name, file in {
    "QUESTIONS_FILE": "questions.csv", "GROUND_TRUTH_FILE": "ground_truth.csv",
    "CATALOGUE_PLAN_FILE": "catalogue_plan.csv", "CATALOGUE_REVIEW_FILE": "catalogue_review.csv",
    "CATALOGUE_FREEZE_FILE": "catalogue_freeze.json", "DOCUMENTS_FILE": "documents.jsonl",
    "SECTIONS_FILE": "sections.jsonl",
}.items():
    setattr(store, name, SP / file)
runpy.run_path(str(ROOT / "app" / "catalogue_editor.py"), run_name="__main__")
```

```bash
uv run python -c "import sys; sys.path.insert(0,'src'); from pathlib import Path; import catalogue, catalogue_plan; \
SP=Path('$SP'); c=catalogue.load_corpus(SP/'documents.jsonl', SP/'sections.jsonl'); \
print(catalogue_plan.write_plan(c, SP/'catalogue_plan.csv'))"
cp .streamlit/config.toml $SP/ 2>/dev/null; cd $SP && mkdir -p .streamlit && cp $OLDPWD/.streamlit/config.toml .streamlit/
uv run --project $OLDPWD streamlit run $SP/run_editor.py --server.headless true --server.port 8599   # background
```

Expected: the plan prints 96 rows; the editor answers on `http://localhost:8599`.

- [ ] **Step 2: playwright-cli at 320, 768 and 1280 px**

Read `playwright-cli --help` first. For each width: open `http://localhost:8599`, screenshot to the scratchpad,
read the console for errors. Exercise: type a question that reuses a heading word (highlight appears in the source
and heading), find "v-model", add a section, save, skip with a reason, switch to Review (empty state text "No open
suggestions."). Check: no horizontal scroll at 320 px, visible keyboard focus, light and dark (toggle via the
Streamlit settings menu).

- [ ] **Step 3: `impeccable` audit, then polish**

Invoke the `impeccable` skill: `audit` on the editor with the screenshots and the spec's "Visual design" section,
then `polish`. Apply only changes that keep the design direction (no new colours or decorations); re-run Task 5's
tests after every change.

- [ ] **Step 4: Commit**

```bash
git add app/catalogue_editor.py .streamlit/config.toml
git commit -m "style(app): Editor nach Browserprüfung und Audit poliert"
```

---

### Task 7: ADR 0031 and documentation

**Files:**
- Create: `docs/adr/0031-stichprobenplan-und-ki-durchsicht.md`
- Modify: `docs/adr/0030-einfrieren-des-fragenkatalogs.md` (status line), `docs/adr/README.md`,
  `docs/how-to/build-the-question-catalogue.md` (rewrite), `docs/reference/data-formats.md`,
  `docs/reference/configuration.md`, `docs/reference/tooling.md`, `docs/reference/question-catalogue.md`,
  `docs/plan.md`, `docs/README.md` (ADR range), `AGENTS.md` (D1–D31), `.serena/memories/pipeline.md`,
  `.serena/memories/decisions.md`

- [ ] **Step 1: ADR 0031**

```markdown
# 0031. Zufälliger Stichprobenplan und protokollierte KI-Durchsicht des Fragenkatalogs

## Status

Angenommen (14.10.2026; ergänzt [ADR 0029](0029-fragetypen-und-konstruktionsklassen.md) und
[ADR 0030](0030-einfrieren-des-fragenkatalogs.md))

## Kontext

- Ohne Vorgabe wählt die verfassende Person Themen aus dem Gedächtnis; das bevorzugt bekannte Themen und kann
  Strategien begünstigen. Eine reproduzierbare Zufallsauswahl der Ausgangsabschnitte macht den Katalog zu einer
  Stichprobe der Dokumentation.
- 644 innerste H2/H3-Abschnitte (Guide 431, API 183, Style Guide 30), Median 190 Tokens, 30 unter 50 Tokens. Gleiche
  Gewichte je Abschnitt würden kleine Abschnitte überbetonen, an deren Grenzen C3-Chunks genau liegen.
- Python garantiert nur den Strom von `random()` über Versionen, NumPy keine festen `Generator`-Ströme; ein
  SHA-256-Hash ist überall gleich.
- Exposé („manuell kuratierter Fragenkatalog“), ADR 0017 (Eigenleistung) und die KI-Richtlinie der IU (KI ersetzt
  keine Datenerhebung, die menschlich zu leisten ist; Verantwortung bei den Studierenden; Offenlegung empfohlen)
  erlauben KI als Hilfsmittel, nicht als Autorin der Fragen.
- Pilotprobe: nachträglich ergänzte Abschnitte verschoben Recall@5 um bis zu 0,07; übersehene Abschnitte sind das
  größte gemessene Risiko der Annotation.

## Entscheidung

Wir werden je Slot einen Ausgangsabschnitt nach Textlänge ziehen: eine Tokenposition im Bereich über SHA-256 von
„{Seed}:{Bereich}:{k}“, gezogen wird der innerste H2/H3-Abschnitt an dieser Stelle, ohne Wiederholung. Seed
`20261014` (Tag der Entscheidung), 12 Slots API, 3 Style Guide, 33 Guide und ebenso viele Reserveabschnitte je Bereich;
die 48 Konstruktionsklassen werden mit demselben Seed gemischt und den Slots zugeordnet. Den Fragetyp wählt Jonas.
Wir werden den Plan einmal schreiben (`data/evaluation/catalogue_plan.csv`, versioniert) und nie überschreiben.
Wir werden einen Ausgangsabschnitt nur mit einem festen Grund überspringen (nur Code oder Links, unter 50 Tokens, gleiches
Thema wie ein früherer Slot, keine beantwortbaren Inhalte); den Slot übernimmt der nächste Reserveabschnitt desselben
Bereichs. Jeder Sprung wird protokolliert und in der Arbeit berichtet.
Wir werden nach jedem Block eine KI-Durchsicht (Claude) durchführen, die nur Fragen, Annotation und Korpustext liest
und Vorschläge (übersehene Abschnitte, Formulierung, Fakten, Klasse) als offene Zeilen in
`data/evaluation/catalogue_review.csv` schreibt; Jonas nimmt jeden Vorschlag an oder lehnt ihn mit Grund ab. Fragen,
Referenzantworten und Relevanzurteile schreibt nur Jonas.
Wir werden einfrieren nur, wenn kein Vorschlag offen ist; der Freeze-Datensatz enthält die Prüfsummen von Plan und
Durchsicht.

## Konsequenzen

- Gut: Themen sind eine reproduzierbare Zufallsstichprobe; die Auswahl ist nachprüfbar und nicht von Vorlieben oder
  Pilotwissen geprägt.
- Gut: Die KI-Unterstützung ist vollständig protokolliert und für die KI-Offenlegung zählbar (Vorschläge, angenommen,
  abgelehnt je Art).
- Neutral: Ein ungeeigneter Abschnitt kostet einen protokollierten Sprung; ist eine Reserve erschöpft, braucht eine
  größere Reserve ein neues ADR.
- Schlecht: Zufällige Abschnitte erfordern mehr Einarbeitung je Frage als frei gewählte Themen.
```

- [ ] **Step 2: Update the other pages** (German, like the surroundings)

1. ADR 0030 status: append "; erweitert um Plan und Durchsicht durch [ADR 0031](0031-stichprobenplan-und-ki-durchsicht.md)".
2. `docs/adr/README.md`: row for 0031; ranges "0019–0030" → "0019–0031"; 0029 and 0030 rows: "ergänzt durch 0031".
3. `docs/how-to/build-the-question-catalogue.md`: rewrite steps: 1) once `uv run python src/catalogue.py plan`, then
   commit `catalogue_plan.csv` and `catalogue_review.csv`; 2) `uv run streamlit run app/catalogue_editor.py`; per
   slot: read the starting section, write question, type, answer, add further sections via search, save or skip with
   a reason; 3) after each block of 8: ask Claude "review block N"; decide every suggestion in the Review tab; 4)
   `check --draft` anytime; 5) at 48: `check`, `freeze`, commit all five catalogue files. Keep the existing rules
   (blind, exact copies, no retrieval before the freeze).
4. `docs/reference/data-formats.md`: sections `catalogue_plan.csv` and `catalogue_review.csv` (columns, values,
   example rows, who writes them); freeze example adds `"catalogue_plan.csv": "…", "catalogue_review.csv": "…"`.
5. `docs/reference/configuration.md`: rows for every new key (Task 1 Step 1) with ADR 0031.
6. `docs/reference/tooling.md`: tree (`catalogue_plan.py`, `catalogue_review.py`, `catalogue_store.py`,
   `app/catalogue_editor.py`, `.streamlit/config.toml`); `catalogue.py` row adds `plan`; a row for the editor;
   versioned files add `catalogue_plan.csv`, `catalogue_review.csv`.
7. `docs/reference/question-catalogue.md`: a short paragraph "Auswahl der Themen" linking ADR 0031.
8. `docs/plan.md`: Stand (tools for plan, editor, review); schedule: six blocks of 8 from 20.10., freeze target
   06.11.2026; open decisions: "Zweitannotation durch eine zweite Person: später, falls Zeit bleibt".
9. `docs/README.md` ADR range; `AGENTS.md` "D1–D31"; memories: `pipeline.md` (editor command, review rule: Claude
   only appends open rows, never edits the CSVs), `decisions.md` (0031).

- [ ] **Step 3: Validate**

Run the link check from the previous plan (excluding `docs/superpowers`) and
`grep -rn "D1–D30\|0019–0030" docs AGENTS.md .serena/memories || echo "no stale ranges"`.
Expected: all links resolve; no stale ranges.

- [ ] **Step 4: Commit**

```bash
git add docs AGENTS.md .serena/memories
git commit -m "docs: Stichprobenplan, Editor und KI-Durchsicht (ADR 0031)"
```

---

## After the last task

Final whole-branch review (top tier), push, PR, `@codex review`, act on findings, merge after Jonas approves, bump
the PaperLab pointer. Do **not** run `catalogue.py plan` on the real data in this PR: drawing the real plan is
Jonas' first step after the merge (so the seed and rules are merged and reviewed before the draw).
