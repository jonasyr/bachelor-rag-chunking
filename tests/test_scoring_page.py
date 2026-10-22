import dataclasses
from pathlib import Path

import pytest
from conftest import SCORING_CODES, write_control_set, write_scoring_set
from streamlit.testing.v1 import AppTest

import catalogue_store as store
import scoring_rules as rules
import scoring_store as scoring
from atomic_csv import read_csv
from config import CONTROL_CRITERIA
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
    monkeypatch.setattr(scoring, "KEY_POINTS_FILE", main / "key_points.csv")
    monkeypatch.setattr(scoring, "SCORING_CHECKS_FILE", main / "scoring_checks.csv")
    monkeypatch.setattr(scoring, "GENERATION_RUNS_FILE", main / "generation_runs.jsonl")
    return main, pilot


def title(at):
    return next(h.proto.body for h in at.get("html") if "slot-title" in h.proto.body)


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
    good = {
        "declines": "no",
        "core_wrong": "no",
        "other_error": "no",
        "grounded": "all",
        "hallucination": "none",
        "answers_question": "yes",
        "direct": "yes",
        "wordy": "no",
    }
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
        at.button_group(key=f"Pilot: hard|H01-B|{check}").set_value(
            {"wordy": "no"}.get(check, "yes")
        )
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
    freeze(dirs[1] / "hard")
    at = AppTest.from_file(str(APP / "catalogue_editor.py"), default_timeout=60)
    at.run()
    at.switch_page("scoring_page.py").run()
    assert not at.exception
    assert "H01, answer B" in title(at)


def test_key_points_edited_after_scoring_show_the_refusal_not_a_traceback(scoring_page):
    at, folder = scoring_page
    answer_all(at, "H01-B", 1)
    at.button(key="scoring_save").click().run()
    with (folder / "key_points.csv").open("a", encoding="utf-8") as f:
        f.write("H01,2,Added later\n")
    at.selectbox(key="scoring_code|Pilot: hard").set_value("H01-B").run()
    assert not at.exception
    assert any("key_points.csv" in e.value for e in at.error)


def test_a_new_scaffold_after_the_freeze_reopens_the_key_points(scoring_page):
    at, folder = scoring_page
    write_scoring_set(folder, codes=(*SCORING_CODES, "H03-A"))  # re-scaffolded with more questions
    at.run()
    assert not at.exception
    assert at.segmented_control(key="scoring_step|Pilot: hard").value == "Key points"
    assert any("2 of 3 questions" in m.value for m in at.sidebar.markdown)


@pytest.mark.parametrize("filled", [(2,), (1, 3)])
def test_key_points_need_a_core_point_and_no_gaps(page, filled):
    at, folder = page
    at.text_input(key="kp|Pilot: hard|H01|1").input("").run()  # clear the pre-filled core point
    for n in filled:
        at.text_input(key=f"kp|Pilot: hard|H01|{n}").input(f"Point {n} text").run()
    assert at.button(key="kp_save").disabled
    assert any("without gaps" in c.value for c in at.caption)
    assert not (folder / "key_points.csv").exists()


def test_key_points_are_prefilled_from_the_reference_but_saved_only_on_save(page):
    at, folder = page
    assert at.text_input(key="kp|Pilot: hard|H01|1").value == "Use `ref()`."
    assert at.text_input(key="kp|Pilot: hard|H01|2").value == ""
    assert any("reference answer" in c.value for c in at.caption)
    assert not (folder / "key_points.csv").exists()
    at.button(key="kp_save").click().run()
    (s,) = scoring.scoring_sets()
    assert scoring.load_key_points(s) == {"H01": ["Use `ref()`."]}


def test_the_checks_carry_the_rules_of_adr_0037_as_help(scoring_page):
    at, _ = scoring_page
    help_of = {g.key.rsplit("|", 1)[1]: g.help for g in at.button_group}
    assert "in brackets" in help_of["point_1"] and "other words" in help_of["point_1"]
    assert "illustrative" in help_of["hallucination"]
    assert "core point" in help_of["direct"]


def test_the_checks_carry_the_clarifications_of_adr_0043_as_help(scoring_page):
    at, _ = scoring_page
    help_of = {g.key.rsplit("|", 1)[1]: g.help for g in at.button_group}
    assert "even if it is" in help_of["direct"] and "wrong" in help_of["direct"]
    assert "part of the answer" in help_of["declines"]


@pytest.fixture
def control_page(dirs):
    write_scoring_set(dirs[1] / "hard")
    freeze(dirs[1] / "hard")
    write_control_set(dirs[1] / "hard")
    at = AppTest.from_file(str(APP / "scoring_page.py"), default_timeout=60)
    at.run()
    at.selectbox(key="scoring_set").select("Pilot: hard: control K0").run()
    return at


def test_control_page_has_no_grounded_check_and_k0_wording(control_page):
    at = control_page
    assert not at.exception
    keys = [g.key for g in at.button_group]
    assert not any(k.endswith("|grounded") for k in keys)
    labels = " ".join(g.label for g in at.button_group)
    assert "does not know" in labels and "the reference does not cover" in labels
    assert any("without excerpts" in m.value for m in [*at.markdown, *at.caption])


def test_control_page_saves_four_scores(control_page):
    at = control_page
    code = "H01-K0"
    at.button_group(key=f"Pilot: hard: control K0|{code}|point_1").set_value("covered")
    for check, value in {
        "declines": "no", "core_wrong": "no", "other_error": "no", "hallucination": "none",
        "answers_question": "yes", "direct": "yes", "wordy": "no",
    }.items():  # fmt: skip
        at.button_group(key=f"Pilot: hard: control K0|{code}|{check}").set_value(value)
    at.run()
    at.button(key="scoring_save").click().run()
    assert not at.exception
    (s,) = (s for s in scoring.scoring_sets() if s.control)
    assert scoring.load_scores(s)[code]["values"] == dict.fromkeys(CONTROL_CRITERIA, 2)


def test_r2_mode_shows_only_the_second_rater_scoring_page(
    dirs, corpus_files, tmp_path, monkeypatch
):
    docs, sections = corpus_files
    monkeypatch.setattr(store, "DOCUMENTS_FILE", docs)
    monkeypatch.setattr(store, "SECTIONS_FILE", sections)
    monkeypatch.setattr(store, "CATALOGUE_PLAN_FILE", tmp_path / "missing_plan.csv")
    monkeypatch.setattr(scoring, "SECOND_RATER_DIR", dirs[0] / "second_rater")
    write_scoring_set(dirs[0])  # Jonas' own main set must stay out of sight
    write_scoring_set(dirs[1] / "hard")
    write_scoring_set(dirs[0] / "second_rater")
    monkeypatch.setenv("SCORING_RATER", "R2")
    (r2,) = scoring.scoring_sets()
    s = dataclasses.replace(r2, rater=False)  # the export freezes; only a plain set can here
    items = scoring.load_items(s)
    scoring.save_key_points(s, items, "H01", ["Core one"])
    scoring.save_key_points(s, items, "H02", ["Core two", "Second two"])
    scoring.freeze_key_points(s, items)
    at = AppTest.from_file(str(APP / "catalogue_editor.py"), default_timeout=60)
    at.run()
    assert not at.exception
    assert at.selectbox(key="scoring_set").options == ["Second rater"]
    assert "H01, answer B" in title(at)
    at.switch_page("catalogue_page.py").run()  # not registered in R2 mode: still the scoring page
    assert "H01, answer B" in title(at)
    assert not at.get("data_editor")


def test_r2_mode_without_a_single_set_says_so(dirs, monkeypatch):
    write_scoring_set(dirs[1] / "a" / "second_rater")
    write_scoring_set(dirs[1] / "b" / "second_rater")
    monkeypatch.setenv("SCORING_RATER", "R2")
    at = AppTest.from_file(str(APP / "scoring_page.py"), default_timeout=60)
    at.run()
    assert not at.exception
    assert any("second rater" in i.value.lower() for i in at.info)


def test_unfrozen_r2_set_offers_no_key_point_editing(dirs, monkeypatch):
    write_scoring_set(dirs[0] / "second_rater")  # scaffolded, but never frozen
    monkeypatch.setattr(scoring, "SECOND_RATER_DIR", dirs[0] / "second_rater")
    monkeypatch.setenv("SCORING_RATER", "R2")
    at = AppTest.from_file(str(APP / "scoring_page.py"), default_timeout=60)
    at.run()
    assert not at.exception
    assert at.error
    assert all(b.key != "kp_save" for b in at.button)
