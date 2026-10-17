"""Rule-based rubric scoring (ADR 0035): factual checks per answer -> the five scores 0-2.

The rater answers checks with fixed options; derive() turns them into the five criteria of
config.RUBRIC_CRITERIA by the rule table in docs/reference/evaluation.md. Same checks, same
scores; config.RUBRIC_RULES_VERSION names the version of these rules.
"""

from config import (
    KEY_POINTS_MAX,
    RUBRIC_COMPLETENESS_PARTIAL,
    RUBRIC_CRITERIA,
    RUBRIC_RULES_VERSION,
)

POINT_MARKS = ("covered", "missing")
YES_NO = ("yes", "no")
CHECKS = {  # in form order, after the key points
    "declines": YES_NO,
    "core_wrong": YES_NO,
    "other_error": YES_NO,
    "grounded": ("all", "some", "none"),
    "hallucination": ("none", "minor", "substantive"),
    "answers_question": YES_NO,
    "direct": YES_NO,
    "wordy": YES_NO,
}
# a declining answer gives no content to check: these are not asked and stored as below
SKIPPED_WHEN_DECLINING = {
    "core_wrong": "no",
    "other_error": "no",
    "grounded": "all",
    "hallucination": "none",
}
CHECKS_HEADER = ["code", "rules_version", "points", *CHECKS]
KEY_POINTS_HEADER = ["question_id", "point", "text"]  # key_points.csv, one row per point
LEVEL = {"all": 2, "some": 1, "none": 0}
HALLUCINATION = {"none": 2, "minor": 1, "substantive": 0}


def declined(checks: dict, n_points: int) -> dict:
    """With declines = yes: every key point missing and the skipped checks at their values."""
    if checks.get("declines") != "yes":
        return checks
    return checks | {"points": ["missing"] * n_points} | SKIPPED_WHEN_DECLINING


def validate(checks: dict, n_points: int) -> None:
    expected = {"points", *CHECKS}
    if set(checks) != expected:
        wrong = sorted(set(checks) ^ expected)
        raise ValueError(f"checks must be exactly points and {list(CHECKS)}; differs in {wrong}")
    if n_points < 1:
        raise ValueError(
            "the question has no frozen key points (added after the freeze?); a set needs key "
            "points for every question before it can be scored"
        )
    points = checks["points"]
    if len(points) != n_points:
        raise ValueError(f"the question has {n_points} key points, the checks mark {len(points)}")
    for mark in points:
        if mark not in POINT_MARKS:
            raise ValueError(f"key point mark {mark!r} is not one of {POINT_MARKS}")
    for check, options in CHECKS.items():
        if checks[check] not in options:
            raise ValueError(f"{check} is {checks[check]!r}, not one of {options}")
    if checks["declines"] == "yes" and checks != declined(checks, n_points):
        raise ValueError(
            "a declining answer has every key point missing and the skipped checks at "
            f"{SKIPPED_WHEN_DECLINING}"
        )


def derive(checks: dict) -> dict[str, int]:
    """The five criteria from valid checks (the rule table of ADR 0035)."""
    points = checks["points"]
    share = points.count("covered") / len(points)
    if checks["core_wrong"] == "yes":
        correctness = 0
    elif checks["other_error"] == "yes" or checks["declines"] == "yes":
        correctness = 1
    else:
        correctness = 2
    completeness = 2 if share == 1 else 1 if share >= RUBRIC_COMPLETENESS_PARTIAL else 0
    if checks["answers_question"] == "no":
        clarity = 0
    elif checks["direct"] == "yes" and checks["wordy"] == "no":
        clarity = 2
    else:
        clarity = 1
    values = [
        correctness,
        completeness,
        LEVEL[checks["grounded"]],
        HALLUCINATION[checks["hallucination"]],
        clarity,
    ]
    return dict(zip(RUBRIC_CRITERIA, values, strict=True))


def to_row(code: str, checks: dict) -> dict[str, str]:
    return {
        "code": code,
        "rules_version": RUBRIC_RULES_VERSION,
        "points": ";".join(checks["points"]),
    } | {c: checks[c] for c in CHECKS}


def from_row(row: dict) -> tuple[str, dict]:
    checks = {"points": row["points"].split(";") if row["points"] else []}
    return row["rules_version"], checks | {c: row[c] for c in CHECKS}


def key_points(rows: list[dict]) -> dict[str, list[str]]:
    """Rows of key_points.csv as texts per question in point order; refused unless every
    question numbers its points 1..N in file order, N <= config.KEY_POINTS_MAX, texts non-empty."""
    points: dict[str, list[str]] = {}
    for row in rows:
        qid = row["question_id"]
        texts = points.setdefault(qid, [])
        if row["point"] != str(len(texts) + 1):
            raise ValueError(
                f"{qid}: points must be numbered 1 to N in order, found {row['point']!r} "
                f"after {len(texts)}"
            )
        if not row["text"].strip():
            raise ValueError(f"{qid}: key point {row['point']} is empty")
        texts.append(row["text"])
        if len(texts) > KEY_POINTS_MAX:
            raise ValueError(f"{qid}: at most {KEY_POINTS_MAX} key points")
    return points
