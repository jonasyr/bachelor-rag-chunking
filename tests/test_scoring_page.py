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
    return next(h.proto.body for h in at.get("html") if "slot-title" in h.proto.body)


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
