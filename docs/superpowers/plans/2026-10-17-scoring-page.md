# Scoring Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Score the blind rubric answers in the existing Streamlit app (a second page "Scoring" next to "Catalogue"), writing the same `scoring_sheet.csv` that `evaluate_answers.py --mode summarise` reads.

**Architecture:** `app/catalogue_editor.py` becomes a router (`st.navigation`) over two page files; shared CSS moves to `app/ui_theme.py`. `scaffold` writes a blind `scoring_items.jsonl`; `src/scoring_store.py` holds all scoring logic (sets, items, sheet, progress, read-only rule) and never touches the key; `app/scoring_page.py` only displays.

**Tech Stack:** Python 3.13, Streamlit 1.58 (`st.navigation`, `st.segmented_control`, AppTest), markdown-it-py, pytest, playwright-cli.

**Spec:** `docs/superpowers/specs/2026-10-17-scoring-page-design.md`

## Global Constraints

- Blind (ADR 0032): the scoring page never shows a strategy or chunk ID and never reads `scoring_key.csv`.
- The sheet stays the primary record: same file, same header (`code,question_id,correctness,completeness,groundedness,no_hallucination,clarity,notes`), written atomically via `src/atomic_csv.py`; `summarise` does not change.
- Codes appear in packet order (the shuffled order of `scaffold`, seed `config.SCORING_SEED`).
- The catalogue page never loads chunks, answers, retrieval results or scores (ADR 0027).
- Start command unchanged: `uv run streamlit run app/catalogue_editor.py --server.address localhost`.
- English UI, sentence case, no middle-dot separators, no all-caps labels; light and dark; works at 320, 768, 1280 px.
- All parameters only in `src/config.py`; Conventional Commits with German subject; no AI attribution.
- Tests never call the OpenAI API.

## Review Focus

1. Notes containing commas, quotes or line breaks: saved and read back exactly (pinned in Task 3, `test_notes_with_commas_quotes_and_newlines_round_trip`).
2. A row filled partly by hand in the CSV: counts as unscored, its values prefill the form (Task 3, `test_partly_filled_row_counts_as_unscored`).
3. The sheet edited by hand while the app is open: saving one code keeps the other rows as they are on disk (Task 3, `test_save_keeps_rows_changed_by_hand_meanwhile`).
4. Raw HTML in a model answer or excerpt (e.g. `<input v-model="x">` outside backticks): shown as text, not rendered as an element (Task 3, `test_text_html_shows_raw_html_as_text`).
5. Saving the last unscored code: the page stays usable and moves to a valid code, the sidebar says everything is scored (Task 3, `test_next_code_*`; Task 4, `test_saving_the_last_answer_reports_everything_scored`).

---

### Task 1: Router and shared theme (refactor, behaviour unchanged)

**Files:**
- Create: `app/ui_theme.py`
- Create: `app/catalogue_page.py` (moved from `app/catalogue_editor.py`)
- Modify: `app/catalogue_editor.py` (becomes the router)
- Test: `tests/test_catalogue_editor.py` (unchanged; must stay green)

**Interfaces:**
- Produces: `ui_theme.CSS: str`, `ui_theme.LIGHT: dict`, `ui_theme.DARK: dict`, `ui_theme.palette_css() -> str`; router file `app/catalogue_editor.py` with pages `catalogue_page.py` (title "Catalogue", default) — Task 4 adds `scoring_page.py`.

- [ ] **Step 1: Run the editor tests as the baseline**

Run: `uv run pytest -q tests/test_catalogue_editor.py`
Expected: all pass.

- [ ] **Step 2: Move the page code**

```bash
git mv app/catalogue_editor.py app/catalogue_page.py
```

- [ ] **Step 3: Create `app/ui_theme.py`**

Cut from `app/catalogue_page.py` the blocks `CSS = """ ... """`, `LIGHT = {...}`, `DARK = {...}` and the function `palette_css()` and paste them unchanged below this header:

```python
"""Shared look of the app's pages (spec 2026-10-14-catalogue-authoring, "Visual design"):
CSS classes and the light/dark palette as CSS variables."""

import streamlit as st

# CSS = """...""", LIGHT = {...}, DARK = {...} and palette_css() moved here unchanged
```

- [ ] **Step 4: Adapt `app/catalogue_page.py`**

Replace its module docstring with:

```python
"""Catalogue page (ADR 0029, 0031): write and annotate the question catalogue.

Shows only the corpus and the catalogue files; never chunks, strategies, retrieval results or
scores (ADR 0027). All reading and writing goes through src/catalogue_store.py. Opened through
the router app/catalogue_editor.py.
"""
```

In `main()`, delete the two lines

```python
    st.set_page_config(page_title="Question catalogue", layout="wide")
    st.markdown(CSS + palette_css(), unsafe_allow_html=True)
```

(the router sets the page config and the CSS once). Keep the `sys.path.insert` line and the final `main()` call.

- [ ] **Step 5: Write the router `app/catalogue_editor.py`**

```python
"""The app (ADR 0031, 0034): the question catalogue and the blind scoring as two pages.

Run: uv run streamlit run app/catalogue_editor.py --server.address localhost
"""

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR.parent / "src"))
sys.path.insert(0, str(APP_DIR))

import streamlit as st  # noqa: E402

from ui_theme import CSS, palette_css  # noqa: E402

st.set_page_config(layout="wide")
st.markdown(CSS + palette_css(), unsafe_allow_html=True)
st.navigation([st.Page("catalogue_page.py", title="Catalogue", default=True)]).run()
```

- [ ] **Step 6: Run the editor tests and lint**

Run: `uv run pytest -q tests/test_catalogue_editor.py && uvx pre-commit run --all-files`
Expected: all pass, no lint findings.

- [ ] **Step 7: Commit**

```bash
git add app/
git commit -m "refactor(app): Editor als Seite hinter einem Router, gemeinsames Theme"
```

---

### Task 2: Blind item file from `scaffold`

**Files:**
- Modify: `src/config.py` (after `SCORING_KEY_FILE`)
- Modify: `src/evaluate_answers.py` (`scaffold`, `pilot_paths`, module docstring)
- Modify: `.gitignore`
- Test: `tests/test_evaluate_answers.py`

**Interfaces:**
- Produces: `config.SCORING_ITEMS_FILE = DATA_EVAL / "scoring_items.jsonl"`; `scaffold(..., items_file: Path = SCORING_ITEMS_FILE)` writes one JSON object per code in packet order with exactly the keys `code, question_id, question, reference_answer, answer, excerpts` (`excerpts`: list of chunk texts in rank order); `pilot_paths(set_dir)["items_file"] == set_dir / "scoring_items.jsonl"`.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_evaluate_answers.py`; add `import re` at the top and `"items_file": tmp_path / "scoring_items.jsonl",` to the `files` fixture dict and `"items_file",` to `SCAFFOLD_ARGS`)

```python
CHUNK_ID_RE = re.compile(r"\b[CK]\d_D\d{3}_\d{4}\b")


def items_of(files):
    text = files["items_file"].read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines()]


def test_scaffold_writes_blind_items_in_sheet_order(files):
    run_scaffold(files)
    items = items_of(files)
    assert [i["code"] for i in items] == [r["code"] for r in read(files["sheet_file"])]
    first = items[0]
    assert set(first) == {"code", "question_id", "question", "reference_answer", "answer", "excerpts"}
    strategy = strategy_of(files)[first["code"]]
    assert first["answer"] == f"Answer to {first['question_id']} ({strategy})."
    assert first["excerpts"] == [f"Excerpt 1 of {strategy}.", f"Excerpt 2 of {strategy}."]
    assert first["reference_answer"] in ("Ref one.", "Ref two.")


def test_items_carry_no_strategy_and_no_chunk_id(files):
    run_scaffold(files)
    text = files["items_file"].read_text(encoding="utf-8")
    assert not CHUNK_ID_RE.search(text)
    assert all(name not in text for name in STRATEGY_IDS.values())
    assert all("strategy" not in item for item in items_of(files))


def test_scaffold_again_with_the_same_seed_gives_identical_files(files):
    run_scaffold(files, limit=1)
    before = {k: files[k].read_text(encoding="utf-8") for k in ("key_file", "items_file", "sheet_file")}
    for name in ("sheet_file", "key_file", "packet_file", "items_file"):
        files[name].unlink()
    run_scaffold(files, limit=1)
    assert {k: files[k].read_text(encoding="utf-8") for k in before} == before
```

Also extend the expected key set in `test_pilot_paths_keep_every_file_inside_the_set` with `"items_file"`.

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest -q tests/test_evaluate_answers.py`
Expected: FAIL (`scaffold() got an unexpected keyword argument 'items_file'`).

- [ ] **Step 3: Implement**

`src/config.py`, below `SCORING_KEY_FILE`:

```python
SCORING_ITEMS_FILE = DATA_EVAL / "scoring_items.jsonl"  # blind items for the scoring page (D34)
```

`src/evaluate_answers.py`: add `import json`; import `SCORING_ITEMS_FILE` from config; add the parameter `items_file: Path = SCORING_ITEMS_FILE,` after `key_file`; next to `key_rows, sheet_rows = [], []` add `items: list[dict] = []`; inside the inner loop, after `sheet_rows.append(...)`, add

```python
            items.append(
                {
                    "code": code,
                    "question_id": qid,
                    "question": questions[qid]["question"],
                    "reference_answer": truth[qid]["expected_answer"],
                    "answer": answer["answer"],
                    "excerpts": [chunks[key][cid]["text"] for cid in split_ids(answer["sources"])],
                }
            )
```

and after `packet_file.write_text(...)`:

```python
    items_file.parent.mkdir(parents=True, exist_ok=True)
    items_file.write_text(
        "".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items), encoding="utf-8"
    )
```

In `pilot_paths` add `"items_file": set_dir / SCORING_ITEMS_FILE.name,`. In the module docstring, under `--mode scaffold`, add the line
`scoring_items.jsonl the same answers as data for the scoring page (ADR 0034), equally blind;`.

`.gitignore`: add `data/evaluation/scoring_items.jsonl` after `data/evaluation/scoring_packet.md`, and `data/pilot/**/scoring_items.jsonl` after `data/pilot/**/scoring_packet.md`.

- [ ] **Step 4: Run the tests and lint**

Run: `uv run pytest -q && uvx pre-commit run --all-files`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/config.py src/evaluate_answers.py tests/test_evaluate_answers.py .gitignore
git commit -m "feat(eval): blinde Bewertungseinträge als JSONL für die App"
```

---

### Task 3: `src/scoring_store.py`

**Files:**
- Create: `src/scoring_store.py`
- Modify: `tests/conftest.py` (helper `write_scoring_set`)
- Test: `tests/test_scoring_store.py`

**Interfaces:**
- Consumes: `evaluate_answers.SHEET_HEADER`; config `SCORING_ITEMS_FILE`, `SCORING_SHEET_FILE`, `SCORES_FILE`, `PILOT_DIR`, `RUBRIC_CRITERIA`, `RUBRIC_MAX_SCORE`.
- Produces:
  - `ScoringSet(name: str, items_file: Path, sheet_file: Path, scores_file: Path)` (frozen dataclass)
  - `scoring_sets() -> list[ScoringSet]` (main first, then pilot folders sorted; names "Main catalogue", "Pilot", "Pilot: hard")
  - `load_items(s) -> list[dict]`; `load_scores(s) -> dict[str, dict]` with `{"values": {criterion: int | None}, "notes": str}`
  - `save_score(s, code: str, values: dict[str, int], notes: str) -> None`; `is_read_only(s) -> bool`
  - `is_scored(entry: dict) -> bool`; `progress(items, scores) -> tuple[int, int]`; `by_question(items, scores) -> list[tuple[str, int, int]]`
  - `first_unscored(codes, scores) -> str`; `next_code(codes, current, scores) -> str`; `text_html(text: str) -> str`
  - conftest: `write_scoring_set(folder: Path, codes: list[str]) -> None`

- [ ] **Step 1: Add the conftest helper** (append to `tests/conftest.py`)

```python
SCORING_CODES = ["H01-B", "H01-A", "H01-C", "H02-A", "H02-C", "H02-B"]  # packet order


def write_scoring_set(folder, codes=tuple(SCORING_CODES)):
    """A scaffolded scoring set as evaluate_answers.py writes it: blind items and an empty sheet."""
    from atomic_csv import write_csv
    from config import RUBRIC_CRITERIA
    from evaluate_answers import SHEET_HEADER

    folder.mkdir(parents=True, exist_ok=True)
    items = [
        {
            "code": code,
            "question_id": code.split("-")[0],
            "question": f"Question {code.split('-')[0]}?",
            "reference_answer": "Use `ref()`.",
            "answer": f"Answer {code}.",
            "excerpts": [f"Excerpt one for {code}.", "Excerpt two."],
        }
        for code in codes
    ]
    (folder / "scoring_items.jsonl").write_text(
        "".join(json.dumps(i) + "\n" for i in items), encoding="utf-8"
    )
    rows = [
        {"code": c, "question_id": c.split("-")[0]} | dict.fromkeys([*RUBRIC_CRITERIA, "notes"], "")
        for c in codes
    ]
    write_csv(folder / "scoring_sheet.csv", SHEET_HEADER, rows)
```

- [ ] **Step 2: Write the failing tests** (`tests/test_scoring_store.py`)

```python
import pytest
from conftest import SCORING_CODES, write_scoring_set

import scoring_store as scoring
from atomic_csv import read_csv, write_csv
from config import RUBRIC_CRITERIA
from evaluate_answers import SHEET_HEADER

ALL_TWO = dict.fromkeys(RUBRIC_CRITERIA, 2)


@pytest.fixture
def dirs(tmp_path, monkeypatch):
    main, pilot = tmp_path / "evaluation", tmp_path / "pilot"
    main.mkdir()
    pilot.mkdir()
    monkeypatch.setattr(scoring, "SCORING_ITEMS_FILE", main / "scoring_items.jsonl")
    monkeypatch.setattr(scoring, "SCORING_SHEET_FILE", main / "scoring_sheet.csv")
    monkeypatch.setattr(scoring, "SCORES_FILE", main / "scores.csv")
    monkeypatch.setattr(scoring, "PILOT_DIR", pilot)
    return main, pilot


@pytest.fixture
def hard(dirs):
    write_scoring_set(dirs[1] / "hard")
    (s,) = scoring.scoring_sets()
    return s


def sheet(s):
    return read_csv(s.sheet_file, SHEET_HEADER)


def test_sets_are_the_main_run_and_pilot_folders_with_items(dirs):
    main, pilot = dirs
    write_scoring_set(main)
    write_scoring_set(pilot / "hard")
    (pilot / "easy").mkdir()  # no items: not a scoring set
    sets = scoring.scoring_sets()
    assert [s.name for s in sets] == ["Main catalogue", "Pilot: hard"]
    assert sets[1].sheet_file == pilot / "hard" / "scoring_sheet.csv"
    assert sets[1].scores_file == pilot / "hard" / "scores.csv"


def test_items_in_the_pilot_root_are_called_pilot(dirs):
    write_scoring_set(dirs[1])
    assert [s.name for s in scoring.scoring_sets()] == ["Pilot"]


def test_no_items_no_sets(dirs):
    assert scoring.scoring_sets() == []


def test_a_set_never_points_to_the_key(hard):
    assert all("scoring_key" not in str(p) for p in vars(hard).values())


def test_items_keep_the_packet_order(hard):
    assert [i["code"] for i in scoring.load_items(hard)] == SCORING_CODES


def test_items_that_do_not_match_the_sheet_are_refused(hard):
    rows = sheet(hard)[:-1]
    write_csv(hard.sheet_file, SHEET_HEADER, rows)
    with pytest.raises(ValueError, match="scaffold"):
        scoring.load_items(hard)


def test_missing_sheet_is_reported(hard):
    hard.sheet_file.unlink()
    with pytest.raises(FileNotFoundError, match="scaffold"):
        scoring.load_items(hard)


def test_unscored_rows_load_as_none(hard):
    entry = scoring.load_scores(hard)["H01-B"]
    assert entry == {"values": dict.fromkeys(RUBRIC_CRITERIA), "notes": ""}
    assert not scoring.is_scored(entry)


def test_malformed_value_in_the_sheet_is_reported(hard):
    rows = sheet(hard)
    rows[0]["clarity"] = "5"
    write_csv(hard.sheet_file, SHEET_HEADER, rows)
    with pytest.raises(ValueError, match="H01-B"):
        scoring.load_scores(hard)


def test_save_changes_exactly_one_row(hard):
    before = sheet(hard)
    scoring.save_score(hard, "H01-A", ALL_TWO | {"clarity": 1}, "fine")
    after = sheet(hard)
    changed = [i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b]
    assert changed == [1]
    assert after[1] | {} == {"code": "H01-A", "question_id": "H01"} | {
        c: "2" for c in RUBRIC_CRITERIA
    } | {"clarity": "1", "notes": "fine"}
    assert hard.sheet_file.read_text(encoding="utf-8").splitlines()[0] == ",".join(SHEET_HEADER)


def test_notes_with_commas_quotes_and_newlines_round_trip(hard):
    notes = 'misses "watch", adds\na second line'
    scoring.save_score(hard, "H01-B", ALL_TWO, notes)
    assert scoring.load_scores(hard)["H01-B"]["notes"] == notes


def test_save_keeps_rows_changed_by_hand_meanwhile(hard):
    rows = sheet(hard)
    rows[3].update(dict.fromkeys(RUBRIC_CRITERIA, "1"))  # edited in the CSV while the app is open
    write_csv(hard.sheet_file, SHEET_HEADER, rows)
    scoring.save_score(hard, "H01-B", ALL_TWO, "")
    assert sheet(hard)[3]["correctness"] == "1"


@pytest.mark.parametrize(
    ("code", "values", "message"),
    [
        ("H09-A", ALL_TWO, "unknown code"),
        ("H01-B", ALL_TWO | {"clarity": 3}, "clarity"),
        ("H01-B", ALL_TWO | {"clarity": -1}, "clarity"),
        ("H01-B", ALL_TWO | {"clarity": True}, "clarity"),
        ("H01-B", ALL_TWO | {"clarity": None}, "clarity"),
        ("H01-B", {c: 2 for c in RUBRIC_CRITERIA[:-1]}, "criteria"),
    ],
)
def test_save_refuses_unknown_codes_and_invalid_values(hard, code, values, message):
    before = hard.sheet_file.read_bytes()
    with pytest.raises(ValueError, match=message):
        scoring.save_score(hard, code, values, "")
    assert hard.sheet_file.read_bytes() == before


def test_read_only_once_scores_were_unblinded(hard):
    assert not scoring.is_read_only(hard)
    hard.scores_file.write_text("unblinded", encoding="utf-8")
    assert scoring.is_read_only(hard)
    before = hard.sheet_file.read_bytes()
    with pytest.raises(PermissionError, match="unblinded"):
        scoring.save_score(hard, "H01-B", ALL_TWO, "")
    assert hard.sheet_file.read_bytes() == before


def test_partly_filled_row_counts_as_unscored(hard):
    rows = sheet(hard)
    rows[0].update({"correctness": "2", "completeness": "1"})
    write_csv(hard.sheet_file, SHEET_HEADER, rows)
    scores = scoring.load_scores(hard)
    assert scores["H01-B"]["values"]["completeness"] == 1
    assert not scoring.is_scored(scores["H01-B"])
    assert scoring.progress(scoring.load_items(hard), scores) == (0, 6)


def test_progress_by_question(hard):
    scoring.save_score(hard, "H01-A", ALL_TWO, "")
    items, scores = scoring.load_items(hard), scoring.load_scores(hard)
    assert scoring.progress(items, scores) == (1, 6)
    assert scoring.by_question(items, scores) == [("H01", 1, 3), ("H02", 0, 3)]


def test_first_unscored_and_next_code(hard):
    codes = SCORING_CODES
    scoring.save_score(hard, "H01-B", ALL_TWO, "")
    scores = scoring.load_scores(hard)
    assert scoring.first_unscored(codes, scores) == "H01-A"
    assert scoring.next_code(codes, "H01-B", scores) == "H01-A"


def test_next_code_wraps_to_the_earliest_unscored(hard):
    for code in SCORING_CODES[1:]:
        scoring.save_score(hard, code, ALL_TWO, "")
    assert scoring.next_code(SCORING_CODES, "H02-B", scoring.load_scores(hard)) == "H01-B"


def test_next_code_when_everything_is_scored(hard):
    for code in SCORING_CODES:
        scoring.save_score(hard, code, ALL_TWO, "")
    scores = scoring.load_scores(hard)
    assert scoring.first_unscored(SCORING_CODES, scores) == "H01-B"
    assert scoring.next_code(SCORING_CODES, "H01-A", scores) == "H01-C"
    assert scoring.next_code(SCORING_CODES, "H02-B", scores) == "H02-B"


def test_text_html_shows_raw_html_as_text():
    out = scoring.text_html('Bind <input v-model="x"> like this:\n\n```js\nconst a = 1\n```')
    assert "&lt;input" in out and "<input" not in out
    assert "<pre><code" in out
```

- [ ] **Step 3: Run them to verify they fail**

Run: `uv run pytest -q tests/test_scoring_store.py`
Expected: FAIL (`ModuleNotFoundError: No module named 'scoring_store'`).

- [ ] **Step 4: Implement `src/scoring_store.py`**

```python
"""Blind scoring in the app (ADR 0032, 0034).

Reads a set's blind item file (scoring_items.jsonl from evaluate_answers.py --mode scaffold)
and its scoring sheet, and writes the sheet; it never opens the key, so nothing here can show
which strategy an answer comes from. Once scores.csv exists the scores were unblinded and the
sheet is read-only. Paths are module globals from config, read at call time, so the page and
its tests share them.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from markdown_it import MarkdownIt

from atomic_csv import read_csv, write_csv
from config import (
    PILOT_DIR,
    RUBRIC_CRITERIA,
    RUBRIC_MAX_SCORE,
    SCORES_FILE,
    SCORING_ITEMS_FILE,
    SCORING_SHEET_FILE,
)
from evaluate_answers import SHEET_HEADER

TEXT_MARKDOWN = MarkdownIt("commonmark", {"html": False}).enable("table")  # model text: no raw HTML


@dataclass(frozen=True)
class ScoringSet:
    name: str
    items_file: Path
    sheet_file: Path
    scores_file: Path


def scoring_sets() -> list[ScoringSet]:
    """The main run and every pilot folder that holds an item file."""
    sets = []
    if SCORING_ITEMS_FILE.exists():
        sets.append(
            ScoringSet("Main catalogue", SCORING_ITEMS_FILE, SCORING_SHEET_FILE, SCORES_FILE)
        )
    for items in sorted(PILOT_DIR.rglob(SCORING_ITEMS_FILE.name)):
        folder = items.parent
        rel = folder.relative_to(PILOT_DIR).as_posix()
        name = "Pilot" if rel == "." else f"Pilot: {rel}"
        sets.append(
            ScoringSet(name, items, folder / SCORING_SHEET_FILE.name, folder / SCORES_FILE.name)
        )
    return sets


def _sheet(s: ScoringSet) -> list[dict]:
    if not s.sheet_file.exists():
        raise FileNotFoundError(
            f"{s.sheet_file} not found; run src/evaluate_answers.py --mode scaffold first"
        )
    return read_csv(s.sheet_file, SHEET_HEADER)


def load_items(s: ScoringSet) -> list[dict]:
    """The items in packet order; refused unless they match the sheet code for code."""
    lines = s.items_file.read_text(encoding="utf-8").splitlines()
    items = [json.loads(line) for line in lines if line.strip()]
    if [i["code"] for i in items] != [r["code"] for r in _sheet(s)]:
        raise ValueError(
            f"{s.items_file} does not match {s.sheet_file}; move sheet and key away and run "
            "src/evaluate_answers.py --mode scaffold again"
        )
    return items


def _value(row: dict, criterion: str, path: Path) -> int | None:
    text = row[criterion].strip()
    if not text:
        return None
    if not text.isdigit() or int(text) > RUBRIC_MAX_SCORE:
        raise ValueError(f"{path}: {row['code']} {criterion} is {text!r}, not 0-{RUBRIC_MAX_SCORE}")
    return int(text)


def load_scores(s: ScoringSet) -> dict[str, dict]:
    """Per code the criterion values (None while empty) and the notes."""
    return {
        r["code"]: {
            "values": {c: _value(r, c, s.sheet_file) for c in RUBRIC_CRITERIA},
            "notes": r["notes"],
        }
        for r in _sheet(s)
    }


def is_read_only(s: ScoringSet) -> bool:
    return s.scores_file.exists()


def save_score(s: ScoringSet, code: str, values: dict[str, int], notes: str) -> None:
    """Rewrite the sheet atomically with only this code's row changed."""
    if is_read_only(s):
        raise PermissionError(f"{s.scores_file} exists: the scores were unblinded, read-only")
    if sorted(values) != sorted(RUBRIC_CRITERIA):
        raise ValueError(f"values must cover exactly the criteria {RUBRIC_CRITERIA}")
    for criterion, value in values.items():
        if type(value) is not int or not 0 <= value <= RUBRIC_MAX_SCORE:
            raise ValueError(f"{criterion} must be an integer 0-{RUBRIC_MAX_SCORE}, got {value!r}")
    rows = _sheet(s)
    row = next((r for r in rows if r["code"] == code), None)
    if row is None:
        raise ValueError(f"unknown code {code} in {s.sheet_file}")
    row.update({c: str(v) for c, v in values.items()} | {"notes": notes})
    write_csv(s.sheet_file, SHEET_HEADER, rows)


def is_scored(entry: dict) -> bool:
    return all(v is not None for v in entry["values"].values())


def progress(items: list[dict], scores: dict[str, dict]) -> tuple[int, int]:
    return sum(is_scored(scores[i["code"]]) for i in items), len(items)


def by_question(items: list[dict], scores: dict[str, dict]) -> list[tuple[str, int, int]]:
    """(question_id, scored, answers) in the order the questions first appear."""
    counts: dict[str, list[int]] = {}
    for item in items:
        done_total = counts.setdefault(item["question_id"], [0, 0])
        done_total[0] += is_scored(scores[item["code"]])
        done_total[1] += 1
    return [(qid, done, total) for qid, (done, total) in counts.items()]


def first_unscored(codes: list[str], scores: dict[str, dict]) -> str:
    return next((c for c in codes if not is_scored(scores[c])), codes[0])


def next_code(codes: list[str], current: str, scores: dict[str, dict]) -> str:
    """The next unscored code after `current` (wrapping); with everything scored the
    following code, or `current` itself at the end."""
    start = codes.index(current)
    for code in codes[start + 1 :] + codes[:start]:
        if not is_scored(scores[code]):
            return code
    return codes[min(start + 1, len(codes) - 1)]


def text_html(text: str) -> str:
    """Model or corpus text as HTML for a formatted page; raw HTML stays visible as text."""
    return TEXT_MARKDOWN.render(text)
```

- [ ] **Step 5: Run the tests and lint**

Run: `uv run pytest -q tests/test_scoring_store.py && uvx pre-commit run --all-files`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/scoring_store.py tests/test_scoring_store.py tests/conftest.py
git commit -m "feat(eval): Bewertungslogik für die App ohne Zugriff auf den Schlüssel"
```

---

### Task 4: Scoring page

**Files:**
- Create: `app/scoring_page.py`
- Modify: `app/catalogue_editor.py` (second page), `app/ui_theme.py` (one CSS rule)
- Test: `tests/test_scoring_page.py`

**Interfaces:**
- Consumes: everything `scoring_store` produces (Task 3); `write_scoring_set`, `SCORING_CODES` (conftest); router from Task 1.
- Produces: page file `app/scoring_page.py`; widget keys `scoring_set`, `scoring_code|<set name>`, `<set name>|<code>|<criterion>`, `<set name>|<code>|notes`, buttons `scoring_previous`, `scoring_save`.

- [ ] **Step 1: Write the failing tests** (`tests/test_scoring_page.py`)

```python
from pathlib import Path

import pytest
from conftest import SCORING_CODES, write_scoring_set
from streamlit.testing.v1 import AppTest

import catalogue_store as store
import scoring_store as scoring
from atomic_csv import read_csv
from evaluate_answers import SHEET_HEADER

APP = Path(__file__).resolve().parent.parent / "app"


@pytest.fixture
def dirs(tmp_path, monkeypatch):
    main, pilot = tmp_path / "evaluation", tmp_path / "pilot"
    main.mkdir()
    pilot.mkdir()
    monkeypatch.setattr(scoring, "SCORING_ITEMS_FILE", main / "scoring_items.jsonl")
    monkeypatch.setattr(scoring, "SCORING_SHEET_FILE", main / "scoring_sheet.csv")
    monkeypatch.setattr(scoring, "SCORES_FILE", main / "scores.csv")
    monkeypatch.setattr(scoring, "PILOT_DIR", pilot)
    return main, pilot


@pytest.fixture
def page(dirs):
    write_scoring_set(dirs[1] / "hard")
    at = AppTest.from_file(str(APP / "scoring_page.py"), default_timeout=60)
    at.run()
    return at, dirs[1] / "hard"


def title(at):
    return next(h.value for h in at.get("html") if "slot-title" in h.value)


def score_all(at, value=2, count=5):
    for group in at.button_group[:count]:
        group.set_value(value)
    at.run()


def test_opens_the_first_unscored_answer(page):
    at, _ = page
    assert not at.exception
    assert "H01, answer B" in title(at)
    assert "question 1 of 2" in title(at)
    assert any(m.value == "**0 of 6 scored**" for m in at.sidebar.markdown)


def test_save_and_next_writes_the_sheet_and_moves_on(page):
    at, folder = page
    score_all(at)
    at.text_input(key="Pilot: hard|H01-B|notes").input("misses watch").run()
    at.button(key="scoring_save").click().run()
    row = read_csv(folder / "scoring_sheet.csv", SHEET_HEADER)[0]
    assert row["code"] == "H01-B" and row["correctness"] == "2" and row["notes"] == "misses watch"
    assert "H01, answer A" in title(at)
    assert any(m.value == "**1 of 6 scored**" for m in at.sidebar.markdown)


def test_save_is_disabled_until_every_criterion_is_set(page):
    at, _ = page
    score_all(at, count=4)
    assert at.button(key="scoring_save").disabled


def test_saving_the_last_answer_reports_everything_scored(page):
    at, _ = page
    for _ in SCORING_CODES:
        score_all(at)
        at.button(key="scoring_save").click().run()
    assert not at.exception
    assert any(m.value == "**6 of 6 scored**" for m in at.sidebar.markdown)
    assert any("Everything is scored" in c.value for c in at.sidebar.caption)


def test_read_only_after_unblinding(page):
    at, folder = page
    (folder / "scores.csv").write_text("unblinded", encoding="utf-8")
    at.run()
    assert any("read-only" in i.value for i in at.info)
    assert at.button(key="scoring_save").disabled


def test_no_sets_explains_how_to_create_one(dirs):
    at = AppTest.from_file(str(APP / "scoring_page.py"), default_timeout=60)
    at.run()
    assert not at.exception
    assert any("--mode scaffold" in i.value for i in at.info)


def test_stale_items_show_an_error_instead_of_a_traceback(page):
    at, folder = page
    (folder / "scoring_sheet.csv").write_text(",".join(SHEET_HEADER) + "\n", encoding="utf-8")
    at.run()
    assert not at.exception
    assert any("scaffold" in e.value for e in at.error)


def test_scoring_code_never_mentions_the_key():
    """ADR 0032: the key stays closed while scoring; the page and its store cannot open it."""
    for path in (APP / "scoring_page.py", APP.parent / "src" / "scoring_store.py"):
        text = path.read_text(encoding="utf-8")
        assert "scoring_key" not in text and "SCORING_KEY" not in text


def test_the_router_offers_the_scoring_page(dirs, corpus_files, tmp_path, monkeypatch):
    docs, sections = corpus_files
    monkeypatch.setattr(store, "DOCUMENTS_FILE", docs)
    monkeypatch.setattr(store, "SECTIONS_FILE", sections)
    monkeypatch.setattr(store, "CATALOGUE_PLAN_FILE", tmp_path / "missing_plan.csv")
    write_scoring_set(dirs[1] / "hard")
    at = AppTest.from_file(str(APP / "catalogue_editor.py"), default_timeout=60)
    at.run()
    at.switch_page("scoring_page.py").run()
    assert not at.exception
    assert "H01, answer B" in title(at)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest -q tests/test_scoring_page.py`
Expected: FAIL (scoring page file missing).

- [ ] **Step 3: Implement `app/scoring_page.py`**

```python
"""Scoring page (ADR 0032, 0034): blind rubric scoring of the generated answers.

Shows only a set's blind item file and its scoring sheet: no strategy, no chunk ID, and the key
stays closed. All reading and writing goes through src/scoring_store.py. Opened through the
router app/catalogue_editor.py.
"""

import html

import streamlit as st

import scoring_store as scoring
from config import RUBRIC_CRITERIA, RUBRIC_MAX_SCORE

SCORES = list(range(RUBRIC_MAX_SCORE + 1))
LABELS = {
    "correctness": "Correctness",
    "completeness": "Completeness",
    "groundedness": "Grounded in the excerpts",
    "no_hallucination": "Free of hallucination",
    "clarity": "Clarity",
}
# English rendering of the rubric in docs/reference/evaluation.md (scores 0, 1, 2)
ANCHORS = {
    "correctness": ("wrong", "partly correct", "correct"),
    "completeness": ("key points missing", "partly complete", "complete"),
    "groundedness": ("not supported", "partly supported", "clearly supported by the excerpts"),
    "no_hallucination": ("false or unsupported claims", "small unsupported additions", "none"),
    "clarity": ("unclear", "understandable with weaknesses", "clear and precise"),
}
SUMMARISE = (
    "Everything is scored. Unblind with `uv run python src/evaluate_answers.py --mode summarise`"
    " (for a pilot set add `--set DIR --limit N` as in scaffold)."
)


def choose_set(sets: list[scoring.ScoringSet]) -> scoring.ScoringSet:
    names = [s.name for s in sets]
    with st.sidebar:
        name = st.selectbox("Set", names, key="scoring_set") or names[0]
    return sets[names.index(name)]


def sidebar(items: list[dict], scores: dict[str, dict]) -> None:
    done, total = scoring.progress(items, scores)
    with st.sidebar:
        st.markdown(f"**{done} of {total} scored**")
        st.progress(done / total if total else 0.0)
        rows = ["| Question | Scored |", "|---|---:|"]
        rows += [f"| {q} | {d} of {n} |" for q, d, n in scoring.by_question(items, scores)]
        st.markdown("\n".join(rows))
        if done == total:
            st.caption(SUMMARISE)


def page(text: str) -> None:
    st.html(f'<div class="formatted">{scoring.text_html(text)}</div>')


def form(s: scoring.ScoringSet, item: dict, saved: dict, codes: list[str], locked: bool) -> None:
    code = item["code"]
    st.markdown("**Question**")
    st.html(f'<div class="formatted reference">{scoring.text_html(item["question"])}</div>')
    st.markdown("**Reference answer**")
    st.html(f'<div class="formatted reference">{scoring.text_html(item["reference_answer"])}</div>')
    values = {}
    for criterion in RUBRIC_CRITERIA:
        values[criterion] = st.segmented_control(
            LABELS[criterion],
            SCORES,
            default=saved["values"][criterion],
            key=f"{s.name}|{code}|{criterion}",
            disabled=locked,
        )
        anchors = ANCHORS[criterion]
        chosen = values[criterion]
        st.caption(
            anchors[chosen].capitalize()
            if chosen is not None
            else ", ".join(f"{n} {a}" for n, a in zip(SCORES, anchors, strict=True))
        )
    notes = st.text_input(
        "Notes", value=saved["notes"], key=f"{s.name}|{code}|notes", disabled=locked
    )
    back, forward = st.columns(2)
    position = codes.index(code)
    if back.button("Previous", key="scoring_previous", disabled=position == 0, width="stretch"):
        st.session_state["scoring_goto"] = codes[position - 1]
        st.rerun()
    incomplete = any(v is None for v in values.values())
    if forward.button(
        "Save and next",
        key="scoring_save",
        type="primary",
        disabled=locked or incomplete,
        width="stretch",
    ):
        try:
            scoring.save_score(s, code, values, notes)
        except (ValueError, PermissionError) as error:
            st.error(str(error))
            return
        st.session_state["scoring_goto"] = scoring.next_code(codes, code, scoring.load_scores(s))
        st.session_state["scoring_saved"] = code
        st.rerun()


def main() -> None:
    sets = scoring.scoring_sets()
    if not sets:
        st.info(
            "Nothing to score yet. Run `uv run python src/evaluate_answers.py --mode scaffold` "
            "(with `--set DIR` for a pilot set) after generating the answers."
        )
        return
    s = choose_set(sets)
    try:
        items, scores = scoring.load_items(s), scoring.load_scores(s)
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        return
    sidebar(items, scores)
    locked = scoring.is_read_only(s)
    if locked:
        st.info("The scores of this set were unblinded (scores.csv exists), so it is read-only.")
    codes = [i["code"] for i in items]
    key = f"scoring_code|{s.name}"
    if "scoring_goto" in st.session_state:  # set by a button; allowed before the widget exists
        st.session_state[key] = st.session_state.pop("scoring_goto")
    if st.session_state.get(key) not in codes:
        st.session_state[key] = scoring.first_unscored(codes, scores)
    if saved := st.session_state.pop("scoring_saved", None):
        st.toast(f"Saved {saved}")

    title, picker = st.columns([7, 5], vertical_alignment="bottom", gap="large")
    with picker:
        code = st.selectbox(
            "Jump to",
            codes,
            key=key,
            format_func=lambda c: f"{c}, scored" if scoring.is_scored(scores[c]) else c,
        )
    item = items[codes.index(code)]
    questions = list(dict.fromkeys(i["question_id"] for i in items))
    number = questions.index(item["question_id"]) + 1
    title.html(
        f'<h2 class="slot-title">{html.escape(item["question_id"])}, answer '
        f"{html.escape(code.rsplit('-', 1)[1])} "
        f"<span>question {number} of {len(questions)}</span></h2>"
    )
    reader, side = st.columns([7, 5], gap="large")
    with reader:
        st.markdown("**Answer under review**")
        page(item["answer"])
        st.markdown("**Excerpts the model saw**")
        tabs = st.tabs([str(n) for n in range(1, len(item["excerpts"]) + 1)])
        for tab, text in zip(tabs, item["excerpts"], strict=True):
            with tab:
                page(text)
    with side:
        form(s, item, scores[code], codes, locked)


main()
```

Router `app/catalogue_editor.py`, replace the `st.navigation(...)` line with:

```python
st.navigation(
    [
        st.Page("catalogue_page.py", title="Catalogue", default=True),
        st.Page("scoring_page.py", title="Scoring"),
    ]
).run()
```

`app/ui_theme.py`, add to `CSS` before `</style>`:

```css
.formatted.reference {background: transparent; color: var(--muted); max-height: none;}
```

- [ ] **Step 4: Run the tests and lint**

Run: `uv run pytest -q && uvx pre-commit run --all-files`
Expected: all pass (the editor tests unchanged).

- [ ] **Step 5: Commit**

```bash
git add app/ tests/test_scoring_page.py
git commit -m "feat(app): Bewertungsseite für die blinde Rubrik-Bewertung"
```

---

### Task 5: ADR 0034 and docs

**Files:**
- Create: `docs/adr/0034-bewertung-in-der-app.md`
- Modify: `docs/adr/README.md`, `docs/adr/0032-blinde-rubrik-bewertung.md` (status line), `AGENTS.md`, `docs/README.md`, `docs/reference/data-formats.md`, `docs/reference/tooling.md`, `docs/reference/configuration.md`, `docs/how-to/run-the-experiment.md`, `.serena/memories/pipeline.md`

- [ ] **Step 1: Write ADR 0034**

```markdown
# 0034. Bewertung in der App

## Status

Angenommen (17.10.2026; ergänzt [ADR 0032](0032-blinde-rubrik-bewertung.md))

## Kontext

- Die blinde Bewertung (ADR 0032) lief über ein Markdown-Lesepaket und eine CSV, die von Hand gefüllt wird; das ist
  bei 144 Antworten fehleranfällig (Tippfehler, falsche Zeile) und mühsam.
- Die App hat schon eine Seite für den Fragenkatalog, die nie Chunks oder Ergebnisse zeigt (ADR 0027).
- Für eine Oberfläche braucht die App Antworten und Passagen je Code als Daten; ohne Schlüssel ist das Lesepaket die
  einzige blinde Quelle, und Markdown zu parsen wäre brüchig.

## Entscheidung

Wir werden die Bewertung als zweite Seite „Scoring“ der App anbieten (Start wie bisher über
`app/catalogue_editor.py`). `evaluate_answers.py --mode scaffold` schreibt zusätzlich `scoring_items.jsonl`: je Code
Frage, Referenzantwort, Antwort und die Passagen in Rangfolge, ohne Strategie und ohne Chunk-IDs. Die Seite liest nur
diese Datei und den Bewertungsbogen und schreibt nur den Bogen; den Schlüssel öffnet sie nie. Sobald `scores.csv`
existiert, ist der Bogen in der App schreibgeschützt.

## Konsequenzen

- Gut: Bewertung ohne Tippfehler im CSV, mit Fortschritt und Rubrik-Ankern; der Bogen bleibt die Primärquelle und
  `summarise` unverändert.
- Gut: Die Katalogseite behält ihre Zusicherung aus ADR 0027; Antworten und Passagen stehen nur auf der Bewertungsseite.
- Neutral: Lesepaket und Bogen bleiben für die Zweitbewertung ohne App erhalten.
- Schlecht: Eine weitere abgeleitete Datei, die zu Bogen und Schlüssel passen muss; die App prüft, dass die Codes
  übereinstimmen.
```

- [ ] **Step 2: Update the index and status lines**

- `docs/adr/README.md`: header range `0019–0033` → `0019–0034`; after the 0033 row add
  `| [0034](0034-bewertung-in-der-app.md) | Bewertung als Seite der App, blinde Einträge `scoring_items.jsonl` | Angenommen |`;
  row 0032 status `Angenommen` → `Angenommen; ergänzt durch 0034`.
- `docs/adr/0032-blinde-rubrik-bewertung.md` status: append `; in der App umgesetzt: [ADR 0034](0034-bewertung-in-der-app.md)`.
- `AGENTS.md`: `decisions D1–D33` → `decisions D1–D34`. `docs/README.md`: `ADR 0019–0033` → `ADR 0019–0034`.

- [ ] **Step 3: Reference docs**

- `docs/reference/data-formats.md`, after the `scoring_key.csv` block:

```markdown
**`scoring_items.jsonl`** (Daten der Bewertungsseite, [ADR 0034](../adr/0034-bewertung-in-der-app.md); nicht
versioniert): eine Zeile je Code in der Reihenfolge des Lesepakets mit `code`, `question_id`, `question`,
`reference_answer`, `answer` und `excerpts` (Texte der Passagen in Rangfolge, ohne Chunk-IDs); keine Strategie.
```

  In the pilot table row `scoring_packet.md`, `scores.csv` add `scoring_items.jsonl`.
- `docs/reference/tooling.md`: app row → `app/catalogue_editor.py` | `uv run streamlit run app/catalogue_editor.py --server.address localhost`: zwei Seiten, „Catalogue“ (schreibgeschützt nach dem Einfrieren, [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md)) und „Scoring“ (blinde Bewertung, schreibgeschützt nach dem Entblinden, [ADR 0034](../adr/0034-bewertung-in-der-app.md)); ignored table: add `scoring_items.jsonl` to the `data/evaluation/...` row and the `data/pilot/**` row; repo tree: add a line `├── app/  catalogue_editor.py (Router)  catalogue_page.py  scoring_page.py  ui_theme.py` if `app/` is listed, else add it after `scripts/`.
- `docs/reference/configuration.md`: row `| `SCORING_ITEMS_FILE` | `data/evaluation/scoring_items.jsonl` | blinde Einträge der Bewertungsseite | [ADR 0034](../adr/0034-bewertung-in-der-app.md) |` after `SCORING_KEY_FILE`.
- `docs/how-to/run-the-experiment.md` step 6: after `--mode scaffold` say: bewerten in der App (`uv run streamlit run app/catalogue_editor.py --server.address localhost`, Seite „Scoring“); Lesepaket und Bogen nur noch für die Zweitbewertung oder ohne App.
- `.serena/memories/pipeline.md`: add bullet `- Scoring page (ADR 0034): app/scoring_page.py + src/scoring_store.py read only scoring_items.jsonl and the sheet, never the key; tests/test_scoring_page.py checks that statically.`

- [ ] **Step 4: Check links and lint**

Run: `uvx pre-commit run --all-files && grep -rn "0034" docs AGENTS.md | head`
Expected: no lint findings; every new link resolves (`ls docs/adr/0034-bewertung-in-der-app.md`).

- [ ] **Step 5: Commit**

```bash
git add docs AGENTS.md .serena
git commit -m "docs: ADR 0034 zur Bewertung in der App und Doku"
```

---

### Task 6: Regenerate the pilot scoring files (real data, inline)

**Files:** `data/pilot/hard/scoring_sheet.csv`, `scoring_key.csv` (versioned; must stay byte-identical), `scoring_items.jsonl`, `scoring_packet.md` (ignored)

- [ ] **Step 1: Confirm the sheet is still empty** — `python3 -c "import csv;print(any(any(r[c] for c in ('correctness','completeness','groundedness','no_hallucination','clarity')) for r in csv.DictReader(open('data/pilot/hard/scoring_sheet.csv'))))"` in the main checkout. Expected: `False`. If `True`, stop and ask Jonas.
- [ ] **Step 2: Keep copies, remove sheet, key and packet** in the main checkout (`cp` both CSVs to the scratchpad, then `rm` sheet, key, packet).
- [ ] **Step 3: Scaffold with the branch code** against the main checkout's data (the worktree has no chunk files): from `../wt-scoring/src`, `scaffold(**pilot_paths(main/"data/pilot/hard") minus scores_file, chunk_files=main chunks, sections_file=main sections, documents_file=main documents, limit=8)`. Expected: `24`.
- [ ] **Step 4: Verify** `cmp` of both CSVs against the copies (identical), and `wc -l data/pilot/hard/scoring_items.jsonl` = 24. No commit needed (versioned files unchanged, items ignored after merge).

---

### Task 7: Browser verification and design passes (inline)

- [ ] **Step 1: Run the branch app on a copy of the pilot set**: in the worktree, link the main checkout's ignored corpus files into `data/processed/` (`documents.jsonl`, `sections.jsonl`), copy `data/pilot/hard/scoring_items.jsonl` and `scoring_sheet.csv` from the main checkout into `data/pilot/ui-check/`, start `uv run streamlit run app/catalogue_editor.py --server.address localhost --server.port 8502` in the background.
- [ ] **Step 2: playwright-cli** at 320, 768 and 1280 px in light and dark: open the Scoring page, select "Pilot: ui-check", score one answer end to end (five controls, notes, save and next), use Previous and Jump to, read the console for errors; open the Catalogue page once to confirm it still renders. Screenshots to the scratchpad.
- [ ] **Step 3: impeccable `audit`, then `polish`** on `app/scoring_page.py` and `app/ui_theme.py`; fix findings in one batch, re-run the tests, re-check the three widths once.
- [ ] **Step 4: Clean up**: stop the server, delete `data/pilot/ui-check/` and the links in `data/processed/`; `git status` shows no data changes. Commit fixes from Step 3 as `fix(app): ...` if any.
