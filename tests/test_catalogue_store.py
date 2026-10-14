import pytest

import catalogue_store as store
from catalogue_plan import read_plan, write_plan
from catalogue_review import REVIEW_HEADER, read_review, save_review

SMALL = {
    "slots": {"api": 1, "style-guide": 1, "guide": 1},
    "reserve": {"api": 1, "style-guide": 0, "guide": 1},
    "classes": {"single": 1, "multi-section": 1, "paraphrase": 1},
}


@pytest.fixture
def files(corpus, tmp_path, monkeypatch):
    paths = {
        "QUESTIONS_FILE": tmp_path / "questions.csv",
        "GROUND_TRUTH_FILE": tmp_path / "ground_truth.csv",
        "CATALOGUE_PLAN_FILE": tmp_path / "catalogue_plan.csv",
        "CATALOGUE_REVIEW_FILE": tmp_path / "catalogue_review.csv",
        "CATALOGUE_FREEZE_FILE": tmp_path / "catalogue_freeze.json",
    }
    for name, path in paths.items():
        monkeypatch.setattr(store, name, path)
    write_plan(corpus, paths["CATALOGUE_PLAN_FILE"], seed=3, **SMALL)
    return paths


def test_empty_catalogue_loads_and_numbers_from_q001(files):
    assert store.load_catalogue() == ([], {})
    assert store.next_question_id([]) == "Q001"
    assert store.next_question_id([{"question_id": "Q009"}, {"question_id": "Q010"}]) == "Q011"


def test_save_writes_both_files_and_uses_the_slot(corpus, files):
    plan = read_plan(files["CATALOGUE_PLAN_FILE"])
    s01 = next(r for r in plan if r["slot_id"] == "S01")
    qid = store.save_question(
        corpus,
        "S01",
        " What does ref() return? ",
        "factual",
        "A reactive ref object.",
        "",
        ["D002#once"],
    )
    assert qid == "Q001"
    questions, truth = store.load_catalogue()
    assert questions == [
        {
            "question_id": "Q001",
            "question": "What does ref() return?",
            "type": "factual",
            "difficulty": s01["class"],
            "notes": "",
        }
    ]
    sids = truth["Q001"]["relevant_section_ids"].split(";")
    assert sids[0] == s01["section_id"] and "D002#once" in sids  # starting section always first
    docs = truth["Q001"]["relevant_doc_ids"].split(";")
    assert docs == list(dict.fromkeys(s.split("#")[0] for s in sids))
    row = next(r for r in read_plan(files["CATALOGUE_PLAN_FILE"]) if r["slot_id"] == "S01")
    assert (row["status"], row["question_id"]) == ("used", "Q001")
    assert files["QUESTIONS_FILE"].read_text(encoding="utf-8").endswith("\n")


def test_edit_keeps_id_and_cannot_drop_the_starting_section(corpus, files):
    store.save_question(corpus, "S01", "Q one?", "factual", "A.", "", [])
    s01 = next(r for r in read_plan(files["CATALOGUE_PLAN_FILE"]) if r["slot_id"] == "S01")
    store.save_question(
        corpus,
        "S01",
        "Q one, edited?",
        "conceptual",
        "B.",
        "n",
        ["D002#cleanup"],
        question_id="Q001",
    )
    questions, truth = store.load_catalogue()
    assert [q["question"] for q in questions] == ["Q one, edited?"]
    assert truth["Q001"]["relevant_section_ids"].split(";")[0] == s01["section_id"]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"question": " "}, "question is empty"),
        ({"answer": ""}, "reference answer is empty"),
        ({"qtype": "trivia"}, "unknown type"),
        ({"section_ids": ["D099#x"]}, "unknown section"),
        ({"slot_id": "S09"}, "no slot S09"),
    ],
)
def test_save_refuses_invalid_input(corpus, files, kwargs, message):
    args = {
        "slot_id": "S01",
        "question": "Q?",
        "qtype": "factual",
        "answer": "A.",
        "notes": "",
        "section_ids": [],
    } | kwargs
    with pytest.raises(ValueError, match=message):
        store.save_question(corpus, **args)
    assert not files["QUESTIONS_FILE"].exists()


def test_save_refuses_after_the_freeze(corpus, files):
    files["CATALOGUE_FREEZE_FILE"].write_text("{}", encoding="utf-8")
    with pytest.raises(PermissionError, match="frozen"):
        store.save_question(corpus, "S01", "Q?", "factual", "A.", "", [])


def test_accepting_a_missing_section_adds_it(corpus, files):
    store.save_question(corpus, "S01", "Q?", "factual", "A.", "", [])
    save_review(
        files["CATALOGUE_REVIEW_FILE"],
        [
            dict.fromkeys(REVIEW_HEADER, "")
            | {
                "round": "1",
                "question_id": "Q001",
                "kind": "missing_section",
                "suggestion": "Also cleanup.",
                "section_id": "D002#cleanup",
                "decision": "open",
            },
            dict.fromkeys(REVIEW_HEADER, "")
            | {
                "round": "1",
                "question_id": "Q001",
                "kind": "wording",
                "suggestion": "Name the hook.",
                "decision": "open",
            },
        ],
    )
    store.accept_suggestion(corpus, 0, "", "2026-10-20")
    assert "D002#cleanup" in store.load_catalogue()[1]["Q001"]["relevant_section_ids"]
    store.reject_suggestion(1, "already clear", "2026-10-20")
    assert [r["decision"] for r in read_review(files["CATALOGUE_REVIEW_FILE"])] == [
        "accepted",
        "rejected",
    ]


def test_highlight_marks_matching_words_and_escapes_html():
    out = store.highlight("Use <script setup> with Watchers.", ["watcher"])
    assert out == 'Use &lt;script setup&gt; with <mark class="hl">Watchers</mark>.'


def test_a_question_cannot_move_to_another_slot(corpus, files):
    store.save_question(corpus, "S01", "Q one?", "factual", "A.", "", [])
    with pytest.raises(ValueError, match="Q001 belongs to slot S01"):
        store.save_question(corpus, "S02", "Q two?", "factual", "B.", "", [], question_id="Q001")
