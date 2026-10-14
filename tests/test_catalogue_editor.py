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
    assert any("Slot S02" in h.value for h in at.subheader)
