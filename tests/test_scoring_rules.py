import pytest

import scoring_rules as rules
from config import RUBRIC_COMPLETENESS_PARTIAL, RUBRIC_CRITERIA, RUBRIC_RULES_VERSION

GOOD = {
    "points": ["covered", "covered"],
    "declines": "no",
    "core_wrong": "no",
    "other_error": "no",
    "grounded": "all",
    "hallucination": "none",
    "answers_question": "yes",
    "direct": "yes",
    "wordy": "no",
}


def checks(**changed):
    return GOOD | changed


def test_a_flawless_answer_scores_two_everywhere():
    assert rules.derive(GOOD) == dict.fromkeys(RUBRIC_CRITERIA, 2)


@pytest.mark.parametrize(
    ("changed", "expected"),
    [
        ({"core_wrong": "yes"}, 0),
        ({"core_wrong": "yes", "other_error": "yes"}, 0),
        ({"other_error": "yes"}, 1),
        ({}, 2),
    ],
)
def test_correctness(changed, expected):
    assert rules.derive(checks(**changed))["correctness"] == expected


@pytest.mark.parametrize(
    ("points", "expected"),
    [
        (["covered"], 2),
        (["missing"], 0),
        (["covered", "missing"], 1),  # 1/2 = threshold
        (["missing", "missing"], 0),
        (["covered", "covered", "missing"], 1),
        (["covered", "missing", "missing"], 0),
        (["covered", "covered", "missing", "missing"], 1),
        (["covered", "missing", "missing", "missing"], 0),
        (["covered"] * 4, 2),
    ],
)
def test_completeness_by_share_of_covered_points(points, expected):
    assert RUBRIC_COMPLETENESS_PARTIAL == 0.5
    assert rules.derive(checks(points=points))["completeness"] == expected


@pytest.mark.parametrize(("value", "expected"), [("all", 2), ("some", 1), ("none", 0)])
def test_groundedness(value, expected):
    assert rules.derive(checks(grounded=value))["groundedness"] == expected


@pytest.mark.parametrize(("value", "expected"), [("none", 2), ("minor", 1), ("substantive", 0)])
def test_no_hallucination(value, expected):
    assert rules.derive(checks(hallucination=value))["no_hallucination"] == expected


@pytest.mark.parametrize(
    ("changed", "expected"),
    [
        ({}, 2),
        ({"direct": "no"}, 1),
        ({"wordy": "yes"}, 1),
        ({"answers_question": "no"}, 0),
        ({"answers_question": "no", "direct": "yes", "wordy": "no"}, 0),
    ],
)
def test_clarity(changed, expected):
    assert rules.derive(checks(**changed))["clarity"] == expected


def test_a_declining_answer_fills_the_skipped_checks_and_scores_as_the_spec_says():
    asked = {"declines": "yes", "answers_question": "yes", "direct": "yes", "wordy": "no"}
    full = rules.declined(asked, n_points=3)
    assert full["points"] == ["missing"] * 3
    assert {k: full[k] for k in rules.SKIPPED_WHEN_DECLINING} == rules.SKIPPED_WHEN_DECLINING
    rules.validate(full, 3)
    assert rules.derive(full) == {
        "correctness": 1,
        "completeness": 0,
        "groundedness": 2,
        "no_hallucination": 2,
        "clarity": 2,
    }


def test_declined_leaves_an_answering_answer_alone():
    assert rules.declined(GOOD, n_points=2) == GOOD


@pytest.mark.parametrize(
    ("bad", "message"),
    [
        (checks(grounded="most"), "grounded"),
        (checks(points=["covered", "partly"]), "point"),
        (checks(points=["covered"]), "2 key points"),
        ({k: v for k, v in GOOD.items() if k != "wordy"}, "wordy"),
        (checks(extra="x"), "extra"),
        (checks(declines="yes"), "declining"),  # skipped checks not at their defaults
    ],
)
def test_validate_rejects(bad, message):
    with pytest.raises(ValueError, match=message):
        rules.validate(bad, 2)


def test_rows_round_trip_with_the_rules_version():
    row = rules.to_row("H01-A", checks(points=["covered", "missing"]))
    assert list(row) == rules.CHECKS_HEADER
    assert row["points"] == "covered;missing" and row["rules_version"] == RUBRIC_RULES_VERSION
    assert rules.from_row(row) == (RUBRIC_RULES_VERSION, checks(points=["covered", "missing"]))


def test_validate_rejects_a_question_without_key_points():
    with pytest.raises(ValueError, match="no frozen key points"):
        rules.validate(checks(points=[]), 0)
