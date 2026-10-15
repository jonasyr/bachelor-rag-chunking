import pytest

import catalogue_plan
from catalogue_plan import (
    candidates,
    draw_area,
    draw_plan,
    mark_used,
    plan_findings,
    plan_integrity,
    plan_summary,
    read_plan,
    save_plan,
    skip_slot,
    slot_row,
    write_plan,
)
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


@pytest.fixture
def small_plan(corpus, tmp_path):
    out = tmp_path / "catalogue_plan.csv"
    write_plan(corpus, out, seed=3, **SMALL)
    return out


def test_skip_moves_the_slot_to_the_next_reserve_section(corpus, small_plan):
    rows = read_plan(small_plan)
    s01 = slot_row(rows, "S01")
    new = skip_slot(small_plan, "S01", "code-or-links", corpus)
    rows = read_plan(small_plan)
    skipped = next(r for r in rows if r["section_id"] == s01["section_id"])
    assert (skipped["status"], skipped["skip_reason"]) == ("skipped", "code-or-links")
    assert (new["slot_id"], new["class"], new["status"], new["area"]) == (
        "S01",
        s01["class"],
        "open",
        "api",
    )
    assert slot_row(rows, "S01")["section_id"] == new["section_id"] != s01["section_id"]


def test_skip_needs_a_listed_reason_an_open_slot_and_a_reserve(corpus, small_plan):
    with pytest.raises(ValueError, match="reason"):
        skip_slot(small_plan, "S01", "boring", corpus)
    with pytest.raises(ValueError, match="no reserve section left in area style-guide"):
        skip_slot(small_plan, "S02", "too-short", corpus)
    rows = read_plan(small_plan)
    mark_used(rows, "S03", "Q001")
    save_plan(small_plan, rows)
    with pytest.raises(ValueError, match="S03 is not open"):
        skip_slot(small_plan, "S03", "too-short", corpus)


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
    questions = [
        q("Q001", "single" if s01["class"] != "single" else "paraphrase"),
        q("Q002", "single"),
    ]
    relevant = {"Q001": [corpus.by_id["D002#cleanup"]], "Q002": [corpus.by_id["D002#cleanup"]]}
    errors, findings = plan_findings(rows, questions, relevant, set(corpus.by_id))
    assert errors == []
    assert (
        f"Q001: difficulty {questions[0]['difficulty']} but slot S01 is {s01['class']}" in findings
    )
    assert f"Q001: starting section {s01['section_id']} of slot S01 is not annotated" in findings
    assert "Q002: belongs to 0 slots, needs exactly 1" in findings


def test_plan_findings_report_unknown_sections_and_bad_reasons(corpus, small_plan):
    rows = read_plan(small_plan)
    rows[0]["section_id"] = "D099#gone"
    rows[1]["status"], rows[1]["skip_reason"] = "skipped", "boring"
    errors, _ = plan_findings(rows, [], {}, set(corpus.by_id))
    assert any("D099#gone" in e for e in errors)
    assert any("'boring'" in e for e in errors)


def test_plan_summary_counts_skips(corpus, small_plan):
    skip_slot(small_plan, "S01", "too-short", corpus)
    lines = plan_summary(read_plan(small_plan))
    assert "Slots: 0 used, 3 open, 1 skipped (too-short 1)" in lines
    assert "Skipped by area: api 1, style-guide 0, guide 0" in lines


def test_too_short_only_for_sections_under_the_minimum(corpus, small_plan, monkeypatch):
    monkeypatch.setattr(catalogue_plan, "CATALOGUE_SKIP_MIN_TOKENS", 1)
    with pytest.raises(ValueError, match="too-short needs fewer than 1 tokens"):
        skip_slot(small_plan, "S01", "too-short", corpus)


def fresh_of(corpus):
    return draw_plan(corpus, seed=3, **SMALL)


def test_untouched_and_legitimately_used_plans_are_intact(corpus, small_plan):
    assert plan_integrity(read_plan(small_plan), fresh_of(corpus)) == []
    skip_slot(small_plan, "S01", "code-or-links", corpus)
    rows = read_plan(small_plan)
    mark_used(rows, "S03", "Q001")
    assert plan_integrity(rows, fresh_of(corpus)) == []


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda rows: rows[0].update(section_id="D003#multi-word"), "differ from a fresh draw"),
        (lambda rows: rows[0].update(**{"class": "detail"}), "differs from the draw"),
        (
            lambda rows: rows[1].update(slot_id="S09", status="used", question_id="Q9"),
            "unknown slots",
        ),
        (
            lambda rows: rows[1].update(status="open", slot_id="S01", **{"class": "x"}),
            "class changed",
        ),
        (lambda rows: rows[0].update(status="used"), "used without a question"),
        (lambda rows: rows[0].update(skip_reason="too-short"), "skip_reason only on skipped"),
    ],
)
def test_plan_integrity_flags_hand_edits(corpus, small_plan, change, message):
    rows = read_plan(small_plan)
    change(rows)
    errors = plan_integrity(rows, fresh_of(corpus))
    assert any(message in e for e in errors), errors


def test_plan_integrity_flags_skips_without_promotion(corpus, small_plan):
    rows = read_plan(small_plan)
    rows[0].update(status="skipped", skip_reason="code-or-links")  # no reserve took over
    errors = plan_integrity(rows, fresh_of(corpus))
    assert any("slot S01: 0 open or used rows" in e for e in errors)
    assert any("area api: 1 skipped but 0 reserve sections used" in e for e in errors)


def test_slot_ids_follow_the_configured_format(corpus, monkeypatch):
    monkeypatch.setattr(catalogue_plan, "CATALOGUE_SLOT_FORMAT", "T{:03d}")
    slots = [r["slot_id"] for r in draw_plan(corpus, seed=3, **SMALL) if r["slot_id"]]
    assert slots == ["T001", "T002", "T003"]


def test_plan_integrity_keeps_promoted_reserves_in_their_own_area(corpus, small_plan):
    rows = read_plan(small_plan)
    fresh = fresh_of(corpus)
    api_slot = next(r for r in rows if r["area"] == "api" and r["slot_id"])
    guide_reserve = next(r for r in rows if r["area"] == "guide" and r["status"] == "reserve")
    api_slot.update(status="skipped", skip_reason="code-or-links")
    guide_reserve.update(slot_id=api_slot["slot_id"], status="open", **{"class": api_slot["class"]})
    errors = plan_integrity(rows, fresh)
    assert any(
        f"slot {api_slot['slot_id']}: a section from area guide cannot fill a slot of area api" in e
        for e in errors
    ), errors
