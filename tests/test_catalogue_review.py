import pytest

from catalogue_review import (
    REVIEW_HEADER,
    decide,
    ensure_review_file,
    read_review,
    review_errors,
    review_summary,
    save_review,
)


def row(**kw):
    base = dict.fromkeys(REVIEW_HEADER, "")
    base.update(
        round="1", question_id="Q001", kind="wording", suggestion="Say which hook.", decision="open"
    )
    base.update(kw)
    return base


def test_missing_file_is_empty_and_ensure_writes_the_header(tmp_path):
    path = tmp_path / "catalogue_review.csv"
    assert read_review(path) == []
    ensure_review_file(path)
    assert path.read_text(encoding="utf-8") == ",".join(REVIEW_HEADER) + "\n"
    ensure_review_file(path)  # never overwrites
    save_review(path, [row()])
    assert read_review(path) == [row()]


def test_review_errors():
    rows = [
        row(),
        row(kind="guess"),
        row(decision="maybe"),
        row(question_id="Q999"),
        row(kind="missing_section", section_id=""),
        row(kind="missing_section", section_id="D099#x"),
        row(kind="wording", section_id="D001#ref"),
        row(decision="rejected", reason=""),
        row(round="x"),
    ]
    errors = review_errors(rows, {"Q001"}, {"D001#ref"})
    assert len(errors) == 8
    assert errors[0].startswith("review row 3: unknown kind 'guess'")


def test_decide_sets_decision_reason_and_date(tmp_path):
    path = tmp_path / "r.csv"
    save_review(path, [row(), row(kind="fact")])
    decided = decide(path, 1, "rejected", "the guide says so", "2026-10-20")
    assert (decided["decision"], decided["reason"], decided["date"]) == (
        "rejected",
        "the guide says so",
        "2026-10-20",
    )
    assert read_review(path)[1] == decided and read_review(path)[0]["decision"] == "open"
    with pytest.raises(ValueError, match="already decided"):
        decide(path, 1, "accepted", "", "2026-10-20")
    with pytest.raises(ValueError, match="needs a reason"):
        decide(path, 0, "rejected", " ", "2026-10-20")
    with pytest.raises(ValueError, match="accepted or rejected"):
        decide(path, 0, "open", "", "2026-10-20")


def test_review_summary():
    rows = [
        row(),
        row(kind="fact", decision="accepted"),
        row(kind="missing_section", section_id="D001#ref", decision="accepted"),
        row(decision="rejected", reason="no"),
    ]
    assert review_summary(rows) == (
        "AI review: 4 suggestions, 2 accepted (missing_section 1, fact 1), 1 rejected, 1 open"
    )
