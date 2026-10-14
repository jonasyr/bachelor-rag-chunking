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
    assert [(r["area"], r["slot_id"], r["class"]) for r in reserve] == [
        ("api", "", ""),
        ("guide", "", ""),
    ]
    assert all(r["draw"].isdigit() and r["skip_reason"] == r["question_id"] == "" for r in rows)


def test_draw_plan_refuses_slots_that_do_not_match_the_classes(corpus):
    with pytest.raises(ValueError, match="slots must sum"):
        draw_plan(
            corpus,
            seed=1,
            slots={"api": 1, "style-guide": 0, "guide": 0},
            reserve=SMALL["reserve"],
            classes=SMALL["classes"],
        )


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
