import pytest

from relevance import is_relevant, overlap_tokens

SECTION = {"doc_id": "D001", "start_token": 100, "end_token": 200}


def chunk(doc_id, start, end):
    return {"doc_id": doc_id, "start_token": start, "end_token": end}


@pytest.mark.parametrize(
    ("c", "expected"),
    [
        (chunk("D001", 120, 180), 60),  # inside
        (chunk("D001", 50, 150), 50),  # partial, left
        (chunk("D001", 150, 400), 50),  # partial, right
        (chunk("D001", 0, 500), 100),  # covers the section
        (chunk("D001", 0, 100), 0),  # touching on the left
        (chunk("D001", 200, 300), 0),  # touching on the right
        (chunk("D002", 120, 180), 0),  # other document
    ],
)
def test_overlap_tokens(c, expected):
    assert overlap_tokens(c, SECTION) == expected


def test_is_relevant_thresholds():
    c = chunk("D001", 150, 400)  # 50 tokens overlap
    assert is_relevant(c, [SECTION], 1)
    assert not is_relevant(c, [SECTION], 100)
    assert is_relevant(c, [chunk("D009", 0, 10), SECTION], 1)
    assert not is_relevant(c, [], 1)


def test_short_chunk_fully_inside_meets_the_sensitivity_threshold():
    assert is_relevant(chunk("D001", 120, 180), [SECTION], 100)  # 60 tokens, all inside


def test_long_chunk_needs_the_full_threshold():
    assert not is_relevant(chunk("D001", 160, 660), [SECTION], 100)  # 500 tokens, 40 overlap


def test_short_chunk_partly_outside_does_not_count():
    assert not is_relevant(chunk("D001", 170, 230), [SECTION], 100)  # 60 tokens, 30 overlap


def test_short_chunk_of_another_document_never_counts():
    assert not is_relevant(chunk("D002", 120, 180), [SECTION], 100)


def test_main_rule_unchanged_for_short_chunks():
    assert is_relevant(chunk("D001", 199, 230), [SECTION], 1)  # one shared token
    assert not is_relevant(chunk("D001", 200, 230), [SECTION], 1)  # touching only
