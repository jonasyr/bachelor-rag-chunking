"""Agreement of the first and the second rating (ADR 0046).

`pair` matches R2's checks and sheet with Jonas' own by blinded code (the key is not needed),
`rows` computes per characteristic the number of units, the simple agreement, Gwet's AC1 (yes/no
checks, key points) or AC2 with ordinal weights (`grounded`, `hallucination`, the five criteria) and
Krippendorff's alpha (ordinal), each interval a percentile bootstrap over the questions (all
answers of a question stay together). `disagreements` lists every differing value for discussion.
Statistics come from `stats.py`; the parameters from `config`.
"""

import stats
from config import (
    AGREEMENT_BOOTSTRAP_REPS,
    AGREEMENT_CI_LEVEL,
    AGREEMENT_SEED,
    RUBRIC_CRITERIA,
)
from scoring_rules import CHECKS, POINT_MARKS, YES_NO, from_row

ORDERED_CHECKS = {  # low -> high
    "grounded": ("none", "some", "all"),
    "hallucination": ("substantive", "minor", "none"),
}
CRITERION_LEVELS = 3  # criteria are scored 0-2
DISAGREEMENTS_HEADER = ["code", "question_id", "field", "first", "second"]
GROUP_CHECKS, GROUP_POINTS, GROUP_CRITERIA = "Prüffragen", "Kernpunkte", "Kriterien"
POINTS_LABEL = "Kernpunkte"
POINT_MARKS_ORDER = (POINT_MARKS[1], POINT_MARKS[0])  # missing -> covered


def _checks_by_code(rows: list[dict]) -> dict[str, tuple[str, dict]]:
    return {r["code"]: from_row(r) for r in rows}


def pair(
    first_checks: list[dict],
    first_sheet: list[dict],
    second_checks: list[dict],
    second_sheet: list[dict],
) -> list[dict]:
    """One dict per code of the second rating (its sheet order): `code`, `question_id`,
    `checks` {name: (first, second)}, `points` [(first, second), ...] and `criteria`
    {name: (first, second)}. Refused if a code is missing in the first rating, the rules
    versions differ, or the number of key point marks differs."""
    first = _checks_by_code(first_checks)
    second = _checks_by_code(second_checks)
    sheet1 = {r["code"]: r for r in first_sheet}
    paired = []
    for row in second_sheet:
        code = row["code"]
        if code not in first or code not in sheet1:
            raise ValueError(f"code {code} of the second rating is missing in the first rating")
        if code not in second:
            raise ValueError(f"code {code} has no checks in the second rating")
        (version1, checks1), (version2, checks2) = first[code], second[code]
        if version1 != version2:
            raise ValueError(f"{code}: rules_version differs ({version1!r} and {version2!r})")
        if len(checks1["points"]) != len(checks2["points"]):
            raise ValueError(
                f"{code}: the first rating marks {len(checks1['points'])} key points, the "
                f"second {len(checks2['points'])}"
            )
        if sheet1[code]["question_id"] != row["question_id"]:
            raise ValueError(f"{code}: the question differs between the ratings")
        paired.append(
            {
                "code": code,
                "question_id": row["question_id"],
                "checks": {c: (checks1[c], checks2[c]) for c in CHECKS},
                "points": list(zip(checks1["points"], checks2["points"], strict=True)),
                "criteria": {c: (int(sheet1[code][c]), int(row[c])) for c in RUBRIC_CRITERIA},
            }
        )
    return paired


def require_same_inputs(
    first_items: list[dict],
    second_items: list[dict],
    first_points: list[dict],
    second_points: list[dict],
) -> None:
    """The second rater scored the same answers against the same key points: every R2 item
    equals Jonas' item of that code and every R2 key point row equals Jonas' row (rows, not file
    checksums: the export writes the key points again)."""
    by_code = {i["code"]: i for i in first_items}
    for item in second_items:
        if by_code.get(item["code"]) != item:
            raise ValueError(f"item {item['code']} of the second rating differs from the first")
    questions = {r["question_id"] for r in second_points}
    mine = [r for r in first_points if r["question_id"] in questions]
    if mine != second_points:
        wrong = sorted(
            q
            for q in questions
            if [r for r in mine if r["question_id"] == q]
            != [r for r in second_points if r["question_id"] == q]
        )
        raise ValueError(f"key points of {', '.join(wrong)} differ between the ratings")


def _units(paired: list[dict]) -> list[tuple[str, str, list, list]]:
    """(group, label, [(question, a, b)], categories-or-None): one entry per output row."""
    out = []
    for name in CHECKS:
        categories = ORDERED_CHECKS.get(name, YES_NO)
        values = [(p["question_id"], *p["checks"][name]) for p in paired]
        out.append((GROUP_CHECKS, name, values, categories, name in ORDERED_CHECKS))
    points = [(p["question_id"], a, b) for p in paired for a, b in p["points"]]
    out.append((GROUP_POINTS, POINTS_LABEL, points, POINT_MARKS_ORDER, False))
    for name in RUBRIC_CRITERIA:
        values = [(p["question_id"], *p["criteria"][name]) for p in paired]
        out.append((GROUP_CRITERIA, name, values, tuple(range(CRITERION_LEVELS)), True))
    return out


def rows(paired: list[dict]) -> list[dict]:
    """The eight checks, the pooled key points and the five criteria; see the module docstring."""
    result = []
    for group, label, values, categories, ordinal in _units(paired):
        q = len(categories)
        code = {c: i for i, c in enumerate(categories)}
        coded = [(question, code[a], code[b]) for question, a, b in values]
        clusters: dict[str, list[tuple[int, int]]] = {}
        for question, a, b in coded:
            clusters.setdefault(question, []).append((a, b))
        groups = [clusters[k] for k in sorted(clusters)]
        weights = stats.ordinal_weights(q) if ordinal else None

        def ac(sample, q=q, weights=weights):
            return stats.gwet_ac([p for cluster in sample for p in cluster], q, weights)

        def alpha(sample):
            return stats.krippendorff_alpha(
                [[a, b] for cluster in sample for a, b in cluster], "ordinal"
            )

        every = [p for cluster in groups for p in cluster]
        estimate_alpha = alpha(groups)
        ac_ci = stats.cluster_bootstrap_ci(
            groups, ac, AGREEMENT_BOOTSTRAP_REPS, AGREEMENT_CI_LEVEL, AGREEMENT_SEED
        )
        if estimate_alpha is None:  # one category only: undefined in every resample as well
            alpha_ci = {"low": None, "high": None, "dropped": 0}
        else:
            alpha_ci = stats.cluster_bootstrap_ci(
                groups, alpha, AGREEMENT_BOOTSTRAP_REPS, AGREEMENT_CI_LEVEL, AGREEMENT_SEED
            )
        result.append(
            {
                "group": group,
                "label": label,
                "n": len(every),
                "agreement": sum(a == b for a, b in every) / len(every),
                "measure": "AC2" if ordinal else "AC1",
                "ac": stats.gwet_ac(every, q, weights),
                "ac_ci": {"low": ac_ci["low"], "high": ac_ci["high"]},
                "alpha": estimate_alpha,
                "alpha_ci": {"low": alpha_ci["low"], "high": alpha_ci["high"]},
                "dropped": alpha_ci["dropped"],
            }
        )
    return result


def disagreements(paired: list[dict]) -> list[dict]:
    """One row per differing check, key point or criterion, to be discussed; no strategy."""
    out = []
    for p in paired:
        fields = [(name, a, b) for name, (a, b) in p["checks"].items()]
        fields += [(f"point {i}", a, b) for i, (a, b) in enumerate(p["points"], start=1)]
        fields += [(name, a, b) for name, (a, b) in p["criteria"].items()]
        out += [
            dict(
                zip(
                    DISAGREEMENTS_HEADER,
                    [p["code"], p["question_id"], name, str(a), str(b)],
                    strict=True,
                )
            )
            for name, a, b in fields
            if a != b
        ]
    return out
