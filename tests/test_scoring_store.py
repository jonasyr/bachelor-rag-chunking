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
