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
        "CLOSED_BOOK_FILE": tmp_path / "closed_book_screen.csv",
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
    assert any("Slot S01" in h.proto.body for h in at.get("html"))


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
    after = next(
        r
        for r in read_plan(paths["CATALOGUE_PLAN_FILE"])
        if r["slot_id"] == "S01" and r["status"] == "open"
    )
    assert after["section_id"] != before["section_id"]


def test_hand_edited_files_are_picked_up_on_rerun(app):
    at, paths = app
    paths["QUESTIONS_FILE"].write_text(
        "question_id,question,type,difficulty,notes\nQ007,Hand made?,factual,single,\n",
        encoding="utf-8",
    )
    at.run()
    assert not at.exception
    assert any("1 of 48" in m.value for m in at.sidebar.markdown)


def test_frozen_catalogue_is_read_only(app):
    at, paths = app
    paths["CATALOGUE_FREEZE_FILE"].write_text("{}", encoding="utf-8")
    at.run()
    assert any("frozen" in i.value for i in at.info)
    assert at.button(key="save").disabled


def test_an_accepted_section_survives_the_next_save(app):
    from catalogue_review import REVIEW_HEADER, save_review

    at, paths = app
    at.text_area(key="question_S01").input("What does it return?")
    at.text_area(key="answer_S01").input("A ref.")
    at.button(key="save").click().run()  # S01 used; the editor caches its section list
    suggestion = dict.fromkeys(REVIEW_HEADER, "") | {
        "round": "1",
        "question_id": "Q001",
        "kind": "missing_section",
        "suggestion": "Also cleanup.",
        "section_id": "D002#cleanup",
        "decision": "open",
    }
    save_review(paths["CATALOGUE_REVIEW_FILE"], [suggestion])
    at.run()
    at.button(key="accept_0").click().run()
    at.selectbox(key="slot").select("S01").run()
    at.button(key="save").click().run()  # saving again must keep the accepted section
    assert not at.exception
    assert "D002#cleanup" in paths["GROUND_TRUTH_FILE"].read_text(encoding="utf-8")


def test_saving_moves_to_the_next_open_slot(app):
    at, _ = app
    at.text_area(key="question_S01").input("What does it return?")
    at.text_area(key="answer_S01").input("A ref.")
    at.button(key="save").click().run()
    assert not at.exception
    assert any("Slot S02" in h.proto.body for h in at.get("html"))


def test_skip_clears_the_draft_and_sections_of_the_slot(app):
    at, _ = app
    at.text_area(key="question_S01").input("Draft for the old section?")
    at.session_state["extra_S01"] = ["D002#cleanup"]
    at.run()
    at.selectbox(key="skip_reason").select("code-or-links")
    at.button(key="skip").click().run()
    assert not at.exception
    assert at.session_state["extra_S01"] == []
    assert at.text_area(key="question_S01").value == ""


def test_hand_edited_rows_replace_the_form(app):
    at, paths = app
    at.text_area(key="question_S01").input("What does it return?")
    at.text_area(key="answer_S01").input("A ref.")
    at.button(key="save").click().run()
    at.selectbox(key="slot").select("S01").run()  # the form now shows the saved question
    path = paths["QUESTIONS_FILE"]
    path.write_text(
        path.read_text(encoding="utf-8").replace("What does it return?", "Hand edited?"),
        encoding="utf-8",
    )
    at.run()  # still on S01: the edit on disk must replace the form
    assert not at.exception
    assert at.text_area(key="question_S01").value == "Hand edited?"


def test_unknown_section_ids_show_an_error_instead_of_crashing(app):
    at, paths = app
    plan = paths["CATALOGUE_PLAN_FILE"]
    rows = read_plan(plan)
    rows[0]["section_id"] = "D999#gone"
    from catalogue_plan import save_plan

    save_plan(plan, rows)
    at.run()
    assert not at.exception
    assert any("D999#gone" in e.value for e in at.error)


def test_the_source_is_formatted_by_default_and_raw_on_request(app):
    at, _ = app
    assert at.segmented_control(key="view").value == "Formatted"
    # rendered on the server (st.html): no code block left for the client's lazy highlighter
    assert any("<h2>" in h.proto.body for h in at.get("html"))
    assert not any(m.value.lstrip().startswith("#") for m in at.markdown)
    at.segmented_control(key="view").set_value("Source text").run()
    assert not at.exception
    assert at.segmented_control(key="view").value == "Source text"


def save_and_screen(at, paths):
    """Write Q001 through the editor, then screen it with a fake completer."""
    from test_closed_book import FakeCompleter

    import closed_book

    at.text_area(key="question_S01").input("What does it return?")
    at.text_area(key="answer_S01").input("A reactive ref object.")
    at.button(key="save").click().run()
    questions, truth = store.load_catalogue()
    closed_book.screen(questions, truth, FakeCompleter(), paths["CLOSED_BOOK_FILE"], [])
    at.run()


def test_closed_book_tab_asks_to_screen_first(app):
    at, _ = app
    at.text_area(key="question_S01").input("What does it return?")
    at.text_area(key="answer_S01").input("A ref.")
    at.button(key="save").click().run()
    assert any("catalogue.py screen" in i.value for i in at.info)


def test_closed_book_verdict_is_saved(app):
    import closed_book

    at, paths = app
    save_and_screen(at, paths)
    assert any("Guess 1." in h.proto.body for h in at.get("html"))
    at.text_input(key="cb_note_Q001").input("knows the return value")
    at.button(key="cb_hit_Q001").click().run()
    assert not at.exception
    row = closed_book.read_screen(paths["CLOSED_BOOK_FILE"])[0]
    assert row["core_point"] == "hit" and row["note"] == "knows the return value"
    assert any(
        "0 retrieval-dependent (at least 32), 1 known" in c.value for c in at.sidebar.caption
    )


def test_a_verdict_can_be_changed(app):
    import closed_book

    at, paths = app
    save_and_screen(at, paths)
    at.button(key="cb_miss_Q001").click().run()
    at.button(key="cb_flip_Q001").click().run()
    assert not at.exception
    assert closed_book.read_screen(paths["CLOSED_BOOK_FILE"])[0]["core_point"] == "hit"


def test_closed_book_tab_is_read_only_when_frozen(app):
    at, paths = app
    save_and_screen(at, paths)
    paths["CATALOGUE_FREEZE_FILE"].write_text("{}", encoding="utf-8")
    at.run()
    assert at.button(key="cb_hit_Q001").disabled and at.button(key="cb_miss_Q001").disabled


def test_judge_closed_book_refuses_after_the_freeze(app):
    at, paths = app
    save_and_screen(at, paths)
    paths["CATALOGUE_FREEZE_FILE"].write_text("{}", encoding="utf-8")
    with pytest.raises(PermissionError, match="frozen"):
        store.judge_closed_book("Q001", "hit", "", "2026-10-21")


def test_write_tab_shows_no_model_answer(app):
    at, paths = app
    save_and_screen(at, paths)
    at.selectbox(key="slot").select("S01").run()
    write_tab_html = [h.proto.body for h in at.tabs[0].get("html")]
    assert not any("Guess 1." in body for body in write_tab_html)
