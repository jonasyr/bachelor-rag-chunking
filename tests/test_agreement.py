import csv

import pytest

import agreement
from config import RUBRIC_CRITERIA, RUBRIC_RULES_VERSION
from scoring_rules import CHECKS

BASE = {
    "declines": "no", "core_wrong": "no", "other_error": "no", "grounded": "all",
    "hallucination": "none", "answers_question": "yes", "direct": "yes", "wordy": "no",
}  # fmt: skip
CODES = [f"{q}-{s}" for q in ("Q1", "Q2", "Q3") for s in "ABC"]


def checks_row(code, points="covered;missing", version=RUBRIC_RULES_VERSION, **edits):
    return {"code": code, "rules_version": version, "points": points} | BASE | edits


def sheet_row(code, **edits):
    values = dict.fromkeys(RUBRIC_CRITERIA, "2") | edits
    return {"code": code, "question_id": code.split("-")[0], **values, "notes": ""}


def rating(codes=CODES, **edits):
    return [checks_row(c, **edits) for c in codes], [sheet_row(c) for c in codes]


@pytest.fixture
def paired():
    first_checks, first_sheet = rating()
    second_checks, second_sheet = rating()
    second_checks[0] = checks_row(CODES[0], direct="no", grounded="some", points="missing;missing")
    second_sheet[0] = sheet_row(CODES[0], correctness="1")
    second_checks[4] = checks_row(CODES[4], wordy="yes")
    return agreement.pair(first_checks, first_sheet, second_checks, second_sheet)


@pytest.fixture(autouse=True)
def few_reps(monkeypatch):
    monkeypatch.setattr(agreement, "AGREEMENT_BOOTSTRAP_REPS", 100)


def test_pair_matches_codes_and_values(paired):
    assert [p["code"] for p in paired] == CODES
    assert paired[0]["question_id"] == "Q1"
    assert paired[0]["checks"]["direct"] == ("yes", "no")
    assert paired[0]["checks"]["grounded"] == ("all", "some")
    assert paired[0]["points"] == [("covered", "missing"), ("missing", "missing")]
    assert paired[0]["criteria"]["correctness"] == (2, 1)
    assert set(paired[0]["checks"]) == set(CHECKS)


def test_pair_uses_only_the_codes_of_r2():
    first_checks, first_sheet = rating()
    second_checks, second_sheet = rating(CODES[:3])
    paired = agreement.pair(first_checks, first_sheet, second_checks, second_sheet)
    assert [p["code"] for p in paired] == CODES[:3]


def test_pair_refuses_missing_code():
    first_checks, first_sheet = rating(CODES[:3])
    second_checks, second_sheet = rating(CODES[:4])
    with pytest.raises(ValueError, match=CODES[3]):
        agreement.pair(first_checks, first_sheet, second_checks, second_sheet)


def test_pair_refuses_rules_version_mismatch():
    first_checks, first_sheet = rating()
    second_checks, second_sheet = rating()
    second_checks[1] = checks_row(CODES[1], version="0-old")
    with pytest.raises(ValueError, match="rules_version"):
        agreement.pair(first_checks, first_sheet, second_checks, second_sheet)


def test_pair_refuses_point_count_mismatch():
    first_checks, first_sheet = rating()
    second_checks, second_sheet = rating()
    second_checks[2] = checks_row(CODES[2], points="covered")
    with pytest.raises(ValueError, match=CODES[2]):
        agreement.pair(first_checks, first_sheet, second_checks, second_sheet)


def test_same_inputs_accepts_equal_and_refuses_differences():
    items = [{"code": c, "answer": f"a {c}"} for c in CODES]
    points = [{"question_id": q, "point": "1", "text": "t"} for q in ("Q1", "Q2", "Q3")]
    agreement.require_same_inputs(items, items[:3], points, points[:1])
    with pytest.raises(ValueError, match=CODES[1]):
        agreement.require_same_inputs(items, [items[0], items[1] | {"answer": "x"}], points, [])
    with pytest.raises(ValueError, match="Q2"):
        agreement.require_same_inputs(items, items[:3], points, [points[1] | {"text": "other"}])
    with pytest.raises(ValueError, match=CODES[8]):
        agreement.require_same_inputs(items[:3], items[:3] + [items[8]], points, [])


def test_rows_order_and_measures(paired):
    rows = agreement.rows(paired)
    assert [r["label"] for r in rows] == [*CHECKS, "Kernpunkte", *RUBRIC_CRITERIA]
    assert [r["group"] for r in rows[:8]] == ["Prüffragen"] * 8
    assert rows[8]["group"] == "Kernpunkte" and {r["group"] for r in rows[9:]} == {"Kriterien"}
    measure = {r["label"]: r["measure"] for r in rows}
    assert measure["grounded"] == measure["hallucination"] == measure["correctness"] == "AC2"
    assert measure["direct"] == measure["Kernpunkte"] == "AC1"
    by = {r["label"]: r for r in rows}
    assert by["direct"]["n"] == 9 and by["Kernpunkte"]["n"] == 18
    assert by["direct"]["agreement"] == pytest.approx(8 / 9)
    assert by["Kernpunkte"]["agreement"] == pytest.approx(17 / 18)
    assert by["wordy"]["agreement"] == pytest.approx(8 / 9)


def test_rows_have_intervals_that_contain_the_estimate(paired):
    for r in agreement.rows(paired):
        assert set(r) == {
            "group", "label", "n", "agreement", "measure", "ac", "ac_ci", "alpha", "alpha_ci",
            "dropped",
        }  # fmt: skip
        assert 0 <= r["agreement"] <= 1
        assert r["ac_ci"]["low"] <= r["ac_ci"]["high"]


def test_ordered_checks_run_low_to_high():
    assert agreement.ORDERED_CHECKS == {
        "grounded": ("none", "some", "all"),
        "hallucination": ("substantive", "minor", "none"),
    }


def test_rows_alpha_not_determinable_when_constant():
    first_checks, first_sheet = rating()
    second_checks, second_sheet = rating()
    rows = {r["label"]: r for r in agreement.rows(
        agreement.pair(first_checks, first_sheet, second_checks, second_sheet)
    )}  # fmt: skip
    assert rows["declines"]["ac"] == 1.0 and rows["declines"]["agreement"] == 1.0
    assert rows["declines"]["alpha"] is None
    assert rows["declines"]["alpha_ci"] == {"low": None, "high": None}


def test_rows_bootstrap_is_deterministic(paired):
    assert agreement.rows(paired) == agreement.rows(paired)


def test_disagreements_list_has_no_strategy(paired):
    rows = agreement.disagreements(paired)
    assert agreement.DISAGREEMENTS_HEADER == ["code", "question_id", "field", "first", "second"]
    assert all(list(r) == agreement.DISAGREEMENTS_HEADER for r in rows)
    got = {(r["code"], r["field"]): (r["first"], r["second"]) for r in rows}
    assert got[(CODES[0], "direct")] == ("yes", "no")
    assert got[(CODES[0], "grounded")] == ("all", "some")
    assert got[(CODES[0], "correctness")] == ("2", "1")
    assert got[(CODES[0], "point 1")] == ("covered", "missing")
    assert got[(CODES[4], "wordy")] == ("no", "yes")
    assert (CODES[0], "wordy") not in got and (CODES[0], "point 2") not in got
    assert not any("strategy" in r["field"] for r in rows)


def test_disagreements_csv_roundtrip(paired, tmp_path):
    path = tmp_path / "d.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, agreement.DISAGREEMENTS_HEADER)
        w.writeheader()
        w.writerows(agreement.disagreements(paired))
    assert path.read_text(encoding="utf-8").splitlines()[0] == "code,question_id,field,first,second"
