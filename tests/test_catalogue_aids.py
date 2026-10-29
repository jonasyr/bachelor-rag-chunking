from test_catalogue import DUPLICATE_PAGES, duplicate_corpus  # noqa: F401  (fixture)

from catalogue_aids import also_covered, save_blocker, type_quota_left


def test_also_covered_merges_same_text_and_related(duplicate_corpus):  # noqa: F811
    seed = duplicate_corpus.by_id["D001#alpha"]
    overlap = {"D001#alpha": [("D002#beta", "Both name the skills."), ("D002#gamma", "Same.")]}
    rows = also_covered(duplicate_corpus, seed, overlap)
    assert [(r["section"]["section_id"], r["kind"]) for r in rows] == [
        ("D002#beta", "same text"),
        ("D002#gamma", "related"),
    ]
    assert rows[0]["note"] == "Both name the skills." and rows[0]["detail"]
    assert rows[1]["detail"] == "Same."


def test_type_quota_left_ignores_the_question_itself():
    questions = [{"question_id": "Q001", "type": "comparative"}]
    assert type_quota_left(questions, "comparative", "Q001") == 6
    assert type_quota_left(questions, "comparative", None) == 5


def test_save_blocker_order():
    ok = [(True, "class rule")]
    assert save_blocker("", "a", "factual", ok, [], None) == "Write a question"
    assert save_blocker("q?", "", "factual", ok, [], None) == "Write a reference answer"
    assert save_blocker("q?", "a", None, ok, [], None) == "Choose a type"
    failing = [(False, "too long")]
    assert save_blocker("q?", "a", "factual", failing, [], None) == "Not met: too long"
    assert save_blocker("q?", "a", "factual", ok, [], None) is None
