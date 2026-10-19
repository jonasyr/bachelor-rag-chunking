import pytest

import scoring_rules as rules
from config import (
    CONTROL_CRITERIA,
    KEY_POINTS_MAX,
    RUBRIC_COMPLETENESS_PARTIAL,
    RUBRIC_CRITERIA,
    RUBRIC_RULES_VERSION,
)

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


def point_rows(*rows):
    return [dict(zip(rules.KEY_POINTS_HEADER, r, strict=True)) for r in rows]


def test_key_points_group_by_question_in_point_order():
    rows = point_rows(("H01", "1", "Core"), ("H02", "1", "Other"), ("H01", "2", "Second"))
    assert rules.key_points(rows) == {"H01": ["Core", "Second"], "H02": ["Other"]}


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ((("H01", "2", "Second"), ("H01", "1", "Core")), "1 to"),  # out of order
        ((("H01", "1", "Core"), ("H01", "1", "Again")), "1 to"),  # duplicate
        ((("H01", "1", "Core"), ("H01", "3", "Gap")), "1 to"),
        ((("H01", "one", "Core"),), "1 to"),
        (tuple(("H01", str(n), "x") for n in range(1, 6)), "at most"),
        ((("H01", "1", " "),), "empty"),
        ((("H01", "1", "two\nlines"),), "one line"),
        ((("H01", "1", "carriage\rreturn"),), "one line"),
    ],
)
def test_malformed_key_points_are_refused(rows, message):
    with pytest.raises(ValueError, match=message):
        rules.key_points(point_rows(*rows))


@pytest.mark.parametrize(
    ("reference", "points"),
    [
        (
            "Use defineModel() (Vue 3.4+); the compiler expands it to a modelValue prop.",
            ["Use defineModel() (Vue 3.4+)", "the compiler expands it to a modelValue prop."],
        ),
        (
            "Supported from Vue 3.5 on. Earlier versions need toRefs().",
            ["Supported from Vue 3.5 on.", "Earlier versions need toRefs()."],
        ),
        (  # an abbreviation before a lower-case word does not end a sentence
            'Name them in camelCase starting with "use", e.g. useMouse.',
            ['Name them in camelCase starting with "use", e.g. useMouse.'],
        ),
        ("  ", []),
    ],
)
def test_reference_answers_split_at_semicolons_and_sentence_ends(reference, points):
    assert rules.split_reference(reference) == points


def test_a_long_reference_keeps_the_extra_parts_in_the_last_point():
    parts = rules.split_reference("A; b; c; d; e; f.")
    assert parts == ["A", "b", "c", "d; e; f."]
    assert len(parts) == KEY_POINTS_MAX


def k0_ok(**changed):
    checks = {
        "points": ["covered"],
        "declines": "no",
        "core_wrong": "no",
        "other_error": "no",
        "hallucination": "none",
        "answers_question": "yes",
        "direct": "yes",
        "wordy": "no",
    }
    return checks | changed


def test_k0_checks_have_no_grounded():
    assert "grounded" not in rules.CONTROL_CHECKS
    assert list(rules.CONTROL_CHECKS) == [c for c in rules.CHECKS if c != "grounded"]
    assert rules.checks_header(True) == ["code", "rules_version", "points", *rules.CONTROL_CHECKS]
    assert rules.checks_header(False) == rules.CHECKS_HEADER


def test_k0_validate_rejects_grounded_and_accepts_the_rest():
    rules.validate(k0_ok(), 1, control=True)
    with pytest.raises(ValueError, match="grounded"):
        rules.validate(k0_ok(grounded="all"), 1, control=True)
    with pytest.raises(ValueError):
        rules.validate(k0_ok(), 1)  # the C1-C3 rules need grounded


def test_k0_declining_answer_skips_without_grounded():
    stored = rules.declined(k0_ok(declines="yes"), 2, control=True)
    assert stored["points"] == ["missing", "missing"]
    assert "grounded" not in stored and stored["hallucination"] == "none"
    rules.validate(stored, 2, control=True)


def test_derive_control_follows_the_rule_table():
    assert rules.derive_control(k0_ok()) == dict.fromkeys(CONTROL_CRITERIA, 2)
    assert rules.derive_control(k0_ok(core_wrong="yes", hallucination="minor", direct="no")) == {
        "correctness": 0,
        "completeness": 2,
        "no_hallucination": 1,
        "clarity": 1,
    }
    declining = rules.declined(k0_ok(declines="yes"), 1, control=True)
    assert rules.derive_control(declining) == {
        "correctness": 1,
        "completeness": 0,
        "no_hallucination": 2,
        "clarity": 2,
    }


def test_k0_rows_round_trip():
    row = rules.to_row("Q001-K0", k0_ok(), control=True)
    assert list(row) == rules.checks_header(True)
    assert rules.from_row(row, control=True) == (rules.RUBRIC_RULES_VERSION, k0_ok())
