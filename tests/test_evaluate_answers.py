import csv

import pytest

from config import CONTROL_STRATEGIES, RUBRIC_CRITERIA, RUBRIC_MAX_SCORE, STRATEGY_IDS
from evaluate_answers import ANSWERS_HEADER, SCORES_HEADER, scaffold, summarise
from retrieve import QUESTIONS_HEADER

STRATEGIES = list(STRATEGY_IDS)


def write_csv(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    return path


def read(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


def answer_rows(qids=("Q002", "Q001"), strategies=STRATEGIES):
    return [[q, s, f"Answer {q} {s}.", f"{s}_D001_0001", 900, 80] for q in qids for s in strategies]


@pytest.fixture
def files(tmp_path):
    return {
        "answers_file": write_csv(
            tmp_path / "generated_answers.csv", ANSWERS_HEADER, answer_rows()
        ),
        "scores_file": tmp_path / "scores.csv",
        "questions_file": write_csv(
            tmp_path / "questions.csv",
            QUESTIONS_HEADER,
            [
                ["Q001", "One?", "factual", "single", ""],
                ["Q002", "Two?", "comparative", "multi-section", ""],
            ],
        ),
    }


def fill(path, scores):
    """scores: {(question_id, strategy): [five criterion values]}; total_score stays empty."""
    rows = read(path)
    for row in rows[1:]:
        values = scores[row[0], row[1]]
        row[2 : 2 + len(RUBRIC_CRITERIA)] = [str(v) for v in values]
    write_csv(path, rows[0], rows[1:])


def test_scores_header_is_the_documented_schema():
    assert SCORES_HEADER == ["question_id", "strategy", *RUBRIC_CRITERIA, "total_score"]


def test_scaffold_writes_one_empty_row_per_answer_in_stable_order(files):
    assert scaffold(files["answers_file"], files["scores_file"]) == 2 * len(STRATEGIES)
    rows = read(files["scores_file"])
    assert rows[0] == SCORES_HEADER
    assert [r[:2] for r in rows[1:]] == [[q, s] for q in ("Q001", "Q002") for s in STRATEGIES]
    assert all(cell == "" for r in rows[1:] for cell in r[2:])


def test_scaffold_never_overwrites_existing_scores(files):
    scaffold(files["answers_file"], files["scores_file"])
    fill(files["scores_file"], {(q, s): [2] * 5 for q in ("Q001", "Q002") for s in STRATEGIES})
    before = files["scores_file"].read_bytes()
    with pytest.raises(FileExistsError, match="manual scores"):
        scaffold(files["answers_file"], files["scores_file"])
    assert files["scores_file"].read_bytes() == before


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        (answer_rows(strategies=list(CONTROL_STRATEGIES)), "K1|strategy"),  # control: no answers
        (answer_rows()[:-1], "missing"),  # one strategy of one question without an answer
        (answer_rows() + answer_rows()[:1], "duplicate"),
    ],
)
def test_scaffold_refuses_answers_outside_the_experiment_grid(files, rows, message):
    write_csv(files["answers_file"], ANSWERS_HEADER, rows)
    with pytest.raises(ValueError, match=message):
        scaffold(files["answers_file"], files["scores_file"])
    assert not files["scores_file"].exists()


def test_summarise_fills_total_score_as_the_mean_of_the_criteria(files):
    scaffold(files["answers_file"], files["scores_file"])
    scores = {(q, s): [2, 2, 2, 2, 2] for q in ("Q001", "Q002") for s in STRATEGIES}
    scores["Q001", "C1"] = [2, 1, 2, 0, 1]  # (2 + 1 + 2 + 0 + 1) / 5 = 1.2
    fill(files["scores_file"], scores)
    summarise(files["scores_file"], files["questions_file"])
    rows = {(r[0], r[1]): r for r in read(files["scores_file"])[1:]}
    assert rows["Q001", "C1"][-1] == "1.2"
    assert rows["Q002", "C3"][-1] == "2.0"


def test_summary_per_strategy_type_and_class(files):
    scaffold(files["answers_file"], files["scores_file"])
    scores = {(q, s): [2] * 5 for q in ("Q001", "Q002") for s in STRATEGIES}
    scores["Q001", "C1"] = [1] * 5
    fill(files["scores_file"], scores)
    summary = summarise(files["scores_file"], files["questions_file"])
    c1 = summary["all", "all", "C1"]
    assert c1["n"] == 2
    assert c1["total_score"] == pytest.approx(1.5)
    assert c1["median"] == pytest.approx(1.5)
    assert c1["sd"] == pytest.approx(0.7071, abs=1e-4)
    assert c1["correctness"] == pytest.approx(1.5)
    assert summary["type", "factual", "C1"]["total_score"] == pytest.approx(1.0)
    assert summary["difficulty", "multi-section", "C2"]["total_score"] == pytest.approx(2.0)
    assert summary["type", "factual", "C2"]["sd"] == 0.0  # one question: no spread


@pytest.mark.parametrize(
    ("value", "message"),
    [("", "unscored"), ("3", "0-2"), ("-1", "0-2"), ("1.5", "0-2"), ("two", "0-2")],
)
def test_summarise_refuses_unscored_or_invalid_values_and_writes_nothing(files, value, message):
    assert RUBRIC_MAX_SCORE == 2
    scaffold(files["answers_file"], files["scores_file"])
    scores = {(q, s): [2] * 5 for q in ("Q001", "Q002") for s in STRATEGIES}
    fill(files["scores_file"], scores)
    rows = read(files["scores_file"])
    rows[3][4] = value
    write_csv(files["scores_file"], rows[0], rows[1:])
    before = files["scores_file"].read_bytes()
    with pytest.raises(ValueError, match=message):
        summarise(files["scores_file"], files["questions_file"])
    assert files["scores_file"].read_bytes() == before


def test_summarise_refuses_a_total_score_that_disagrees_with_the_criteria(files):
    scaffold(files["answers_file"], files["scores_file"])
    fill(files["scores_file"], {(q, s): [2] * 5 for q in ("Q001", "Q002") for s in STRATEGIES})
    rows = read(files["scores_file"])
    rows[1][-1] = "1.0"
    write_csv(files["scores_file"], rows[0], rows[1:])
    with pytest.raises(ValueError, match="total_score"):
        summarise(files["scores_file"], files["questions_file"])


def test_summarise_refuses_scores_of_unknown_questions(files):
    write_csv(files["answers_file"], ANSWERS_HEADER, answer_rows(qids=("Q001", "Q009")))
    scaffold(files["answers_file"], files["scores_file"])
    fill(files["scores_file"], {(q, s): [2] * 5 for q in ("Q001", "Q009") for s in STRATEGIES})
    with pytest.raises(ValueError, match="Q009"):
        summarise(files["scores_file"], files["questions_file"])
