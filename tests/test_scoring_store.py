import json

import pytest
from conftest import SCORING_CODES, log_scaffold, write_control_set, write_scoring_set

import scoring_rules as rules
import scoring_store as scoring
from atomic_csv import read_csv, write_csv
from config import CONTROL_CRITERIA, KEY_POINTS_MAX, RUBRIC_CRITERIA
from evaluate_answers import SHEET_HEADER

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


def ok(code, **changed):
    """A flawless answer's checks for `code` (H01 has one key point, H02 two in `frozen`)."""
    return GOOD | {"points": ["covered"] * (1 if code.startswith("H01") else 2)} | changed


@pytest.fixture
def dirs(tmp_path, monkeypatch):
    main, pilot = tmp_path / "evaluation", tmp_path / "pilot"
    main.mkdir()
    pilot.mkdir()
    monkeypatch.setattr(scoring, "SCORING_ITEMS_FILE", main / "scoring_items.jsonl")
    monkeypatch.setattr(scoring, "SCORING_SHEET_FILE", main / "scoring_sheet.csv")
    monkeypatch.setattr(scoring, "SCORES_FILE", main / "scores.csv")
    monkeypatch.setattr(scoring, "PILOT_DIR", pilot)
    monkeypatch.setattr(scoring, "SECOND_RATER_DIR", main / "second_rater")
    monkeypatch.delenv("SCORING_RATER", raising=False)
    monkeypatch.setattr(scoring, "KEY_POINTS_FILE", main / "key_points.csv")
    monkeypatch.setattr(scoring, "SCORING_CHECKS_FILE", main / "scoring_checks.csv")
    monkeypatch.setattr(scoring, "GENERATION_RUNS_FILE", main / "generation_runs.jsonl")
    return main, pilot


@pytest.fixture
def hard(dirs):
    write_scoring_set(dirs[1] / "hard")
    (s,) = scoring.scoring_sets()
    return s


@pytest.fixture
def frozen(hard):
    items = scoring.load_items(hard)
    scoring.save_key_points(hard, items, "H01", ["Core one"])
    scoring.save_key_points(hard, items, "H02", ["Core two", "Second two"])
    scoring.freeze_key_points(hard, items)
    return hard


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


def test_save_changes_exactly_one_row(frozen):
    hard = frozen
    before = sheet(hard)
    scoring.save_score(hard, "H01-A", ok("H01-A", wordy="yes"), "fine")
    after = sheet(hard)
    changed = [i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b]
    assert changed == [1]
    assert after[1] | {} == {"code": "H01-A", "question_id": "H01"} | {
        c: "2" for c in RUBRIC_CRITERIA
    } | {"clarity": "1", "notes": "fine"}
    assert hard.sheet_file.read_text(encoding="utf-8").splitlines()[0] == ",".join(SHEET_HEADER)


def test_notes_with_commas_quotes_and_newlines_round_trip(frozen):
    notes = 'misses "watch", adds\na second line'
    scoring.save_score(frozen, "H01-B", ok("H01-B"), notes)
    assert scoring.load_scores(frozen)["H01-B"]["notes"] == notes


def test_save_keeps_rows_changed_by_hand_meanwhile(frozen):
    hard = frozen
    rows = sheet(hard)
    rows[3].update(dict.fromkeys(RUBRIC_CRITERIA, "1"))  # edited in the CSV while the app is open
    write_csv(hard.sheet_file, SHEET_HEADER, rows)
    scoring.save_score(hard, "H01-B", ok("H01-B"), "")
    assert sheet(hard)[3]["correctness"] == "1"


@pytest.mark.parametrize(
    ("code", "checks", "message"),
    [
        ("H09-A", ok("H01-A"), "unknown code"),
        ("H01-B", ok("H01-B", grounded="most"), "grounded"),
        ("H01-B", {k: v for k, v in ok("H01-B").items() if k != "wordy"}, "wordy"),
    ],
)
def test_save_refuses_unknown_codes_and_invalid_checks(frozen, code, checks, message):
    before = frozen.sheet_file.read_bytes()
    with pytest.raises(ValueError, match=message):
        scoring.save_score(frozen, code, checks, "")
    assert frozen.sheet_file.read_bytes() == before
    assert not frozen.checks_file.exists()


def test_read_only_once_scores_were_unblinded(frozen):
    hard = frozen
    assert not scoring.is_read_only(hard)
    hard.scores_file.write_text("unblinded", encoding="utf-8")
    assert scoring.is_read_only(hard)
    before = hard.sheet_file.read_bytes()
    with pytest.raises(PermissionError, match="unblinded"):
        scoring.save_score(hard, "H01-B", ok("H01-B"), "")
    assert hard.sheet_file.read_bytes() == before


def test_partly_filled_row_counts_as_unscored(hard):
    rows = sheet(hard)
    rows[0].update({"correctness": "2", "completeness": "1"})
    write_csv(hard.sheet_file, SHEET_HEADER, rows)
    scores = scoring.load_scores(hard)
    assert scores["H01-B"]["values"]["completeness"] == 1
    assert not scoring.is_scored(scores["H01-B"])
    assert scoring.progress(scoring.load_items(hard), scores) == (0, 6)


def test_progress_by_question(frozen):
    hard = frozen
    scoring.save_score(hard, "H01-A", ok("H01-A"), "")
    items, scores = scoring.load_items(hard), scoring.load_scores(hard)
    assert scoring.progress(items, scores) == (1, 6)
    assert scoring.by_question(items, scores) == [("H01", 1, 3), ("H02", 0, 3)]


def test_first_unscored_and_next_code(frozen):
    hard = frozen
    codes = SCORING_CODES
    scoring.save_score(hard, "H01-B", ok("H01-B"), "")
    scores = scoring.load_scores(hard)
    assert scoring.first_unscored(codes, scores) == "H01-A"
    assert scoring.next_code(codes, "H01-B", scores) == "H01-A"


def test_next_code_wraps_to_the_earliest_unscored(frozen):
    hard = frozen
    for code in SCORING_CODES[1:]:
        scoring.save_score(hard, code, ok(code), "")
    assert scoring.next_code(SCORING_CODES, "H02-B", scoring.load_scores(hard)) == "H01-B"


def test_next_code_when_everything_is_scored(frozen):
    hard = frozen
    for code in SCORING_CODES:
        scoring.save_score(hard, code, ok(code), "")
    scores = scoring.load_scores(hard)
    assert scoring.first_unscored(SCORING_CODES, scores) == "H01-B"
    assert scoring.next_code(SCORING_CODES, "H01-A", scores) == "H01-C"
    assert scoring.next_code(SCORING_CODES, "H02-B", scores) == "H02-B"


def test_text_html_shows_raw_html_as_text():
    out = scoring.text_html('Bind <input v-model="x"> like this:\n\n```js\nconst a = 1\n```')
    assert "&lt;input" in out and "<input" not in out
    assert "<pre><code" in out


def freezes(s):
    lines = s.runs_file.read_text(encoding="utf-8").splitlines()
    return [r for r in map(json.loads, lines) if r["step"] == "key_points"]


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
    assert [(r["question_id"], r["point"]) for r in rows] == [
        ("H01", "1"),
        ("H02", "1"),
        ("H02", "2"),
    ]
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
    (record,) = freezes(hard)
    assert record["step"] == "key_points" and "key_points.csv" in record["outputs_sha256"]
    with pytest.raises(PermissionError, match="frozen"):
        scoring.freeze_key_points(hard, items)
    with pytest.raises(PermissionError, match="frozen"):
        scoring.save_key_points(hard, items, "H01", ["Changed"])
    assert len(freezes(hard)) == 1


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


def test_a_hand_edited_key_points_file_with_bad_numbering_cannot_be_frozen(hard):
    hard.key_points_file.write_text(
        "question_id,point,text\nH01,2,Second\nH01,1,Core\nH02,1,Core two\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="H01"):
        scoring.freeze_key_points(hard, scoring.load_items(hard))
    assert not scoring.is_frozen(hard)


@pytest.mark.parametrize(
    ("extra", "message"),
    [("H01-B", "more than once"), ("H09-A", "not in")],
)
def test_save_refuses_a_malformed_checks_file(frozen, extra, message):
    scoring.save_score(frozen, "H01-B", ok("H01-B"), "")
    with frozen.checks_file.open("a", encoding="utf-8") as f:
        f.write(",".join(rules.to_row(extra, ok("H01-B")).values()) + "\n")
    with pytest.raises(ValueError, match=message):
        scoring.save_score(frozen, "H01-A", ok("H01-A"), "")


def test_key_points_for_a_question_outside_the_set_cannot_be_frozen(hard):
    hard.key_points_file.write_text(
        "question_id,point,text\nH01,1,Core\nH02,1,Core two\nH09,1,Stray\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="H09"):
        scoring.freeze_key_points(hard, scoring.load_items(hard))
    assert not scoring.is_frozen(hard)


def rescaffold(s, record=True):
    """A new scaffold of the same set: same codes, other answer texts (other items checksum),
    logged like evaluate_answers.py --mode scaffold unless `record` is False."""
    text = s.items_file.read_text(encoding="utf-8").replace("Answer ", "New answer ")
    s.items_file.write_text(text, encoding="utf-8")
    if record:
        log_scaffold(s.items_file)


def test_a_freeze_only_holds_for_the_scaffold_it_was_made_on(frozen):
    record = json.loads(frozen.runs_file.read_text().splitlines()[-1])
    assert "scoring_items.jsonl" in record["outputs_sha256"]
    rescaffold(frozen)
    assert not scoring.is_frozen(frozen)
    with pytest.raises(PermissionError, match="not frozen"):
        scoring.require_frozen_key_points(frozen)
    scoring.freeze_key_points(frozen, scoring.load_items(frozen))  # freeze again for the new one
    assert scoring.is_frozen(frozen)


def test_freezing_is_refused_while_checks_of_an_earlier_scaffold_remain(frozen):
    scoring.save_score(frozen, "H01-B", ok("H01-B"), "")
    rescaffold(frozen)
    with pytest.raises(ValueError, match="scoring_checks.csv"):
        scoring.freeze_key_points(frozen, scoring.load_items(frozen))


def test_an_item_file_that_differs_from_its_scaffold_record_cannot_be_frozen(hard):
    items = scoring.load_items(hard)
    scoring.save_key_points(hard, items, "H01", ["Core one"])
    scoring.save_key_points(hard, items, "H02", ["Core two"])
    rescaffold(hard, record=False)  # item file changed without a scaffold run
    with pytest.raises(ValueError, match="scaffold"):
        scoring.freeze_key_points(hard, scoring.load_items(hard))
    assert not scoring.is_frozen(hard)


def test_saving_drops_key_points_of_questions_outside_the_scaffold(hard):
    hard.key_points_file.write_text(
        "question_id,point,text\nH01,1,Core\nH02,1,Core two\nH09,1,Removed question\n",
        encoding="utf-8",
    )
    items = scoring.load_items(hard)
    with pytest.raises(ValueError, match="save the key points of any question"):
        scoring.freeze_key_points(hard, items)
    scoring.save_key_points(hard, items, "H01", ["Core"])
    assert scoring.load_key_points(hard) == {"H01": ["Core"], "H02": ["Core two"]}
    scoring.freeze_key_points(hard, items)
    assert scoring.is_frozen(hard)


def control_set(frozen):
    write_control_set(frozen.items_file.parent)
    return next(s for s in scoring.scoring_sets() if s.control)


def k0_checks(**changed):
    checks = {k: v for k, v in ok("H01-K0").items() if k != "grounded"}
    return checks | changed


def test_a_control_set_is_listed_after_its_c1_c3_set(frozen):
    s = control_set(frozen)
    assert s.name == "Pilot: hard: control K0"
    assert s.key_points_file == frozen.key_points_file
    assert scoring.criteria(s) == list(CONTROL_CRITERIA)


def test_the_control_set_uses_the_frozen_key_points_of_its_c1_c3_set(frozen):
    s = control_set(frozen)
    assert scoring.is_frozen(s)
    with pytest.raises(PermissionError, match="C1-C3"):
        scoring.save_key_points(s, scoring.load_items(s), "H01", ["Other"])


def test_control_save_derives_four_criteria_and_refuses_grounded(frozen):
    s = control_set(frozen)
    values = scoring.save_score(s, "H01-K0", k0_checks(), "")
    assert values == dict.fromkeys(CONTROL_CRITERIA, 2)
    assert scoring.load_scores(s)["H01-K0"]["values"] == values
    with pytest.raises(ValueError, match="grounded"):
        scoring.save_score(s, "H02-K0", k0_checks(grounded="all"), "")


def test_control_save_refuses_changed_key_points(frozen):
    s = control_set(frozen)
    s.key_points_file.write_text(
        s.key_points_file.read_text(encoding="utf-8").replace("Core one", "Edited"),
        encoding="utf-8",
    )
    with pytest.raises(PermissionError, match="frozen"):
        scoring.save_score(s, "H01-K0", k0_checks(), "")


def test_scoring_sets_lists_second_rater(dirs):
    main, pilot = dirs
    write_scoring_set(main)
    write_scoring_set(main / "second_rater")
    write_scoring_set(pilot / "hard")
    write_scoring_set(pilot / "hard" / "second_rater")
    names = [s.name for s in scoring.scoring_sets()]
    assert names == ["Main catalogue", "Pilot: hard", "Second rater", "Pilot: hard: second rater"]
    r2 = scoring.scoring_sets()[2]
    assert r2.rater and r2.items_file == main / "second_rater" / "scoring_items.jsonl"


def test_second_rater_set_has_no_control_set(dirs):
    main, _ = dirs
    write_scoring_set(main / "second_rater")
    write_control_set(main / "second_rater")
    assert [s.name for s in scoring.scoring_sets()] == ["Second rater"]


def test_rater_mode_shows_only_r2(dirs, monkeypatch):
    main, pilot = dirs
    write_scoring_set(main)
    write_scoring_set(main / "second_rater")
    write_scoring_set(pilot / "hard")
    write_scoring_set(pilot / "hard" / "second_rater")
    monkeypatch.setenv("SCORING_RATER", "R2")
    assert scoring.rater_mode() == "R2"
    assert [s.name for s in scoring.scoring_sets()] == ["Second rater", "Pilot: hard: second rater"]


def test_other_rater_value_does_not_restrict(dirs, monkeypatch):
    main, _ = dirs
    write_scoring_set(main)
    monkeypatch.setenv("SCORING_RATER", "someone")
    assert [s.name for s in scoring.scoring_sets()] == ["Main catalogue"]
