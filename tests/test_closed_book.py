import pytest

import closed_book
from closed_book import (
    NOT_JUDGED,
    NOT_SCREENED,
    SCREEN_HEADER,
    counts,
    findings,
    judge,
    min_dependent,
    read_screen,
    save_screen,
    screen,
    states,
    status,
    summary,
    text_sha256,
)
from llm_client import Completion


class FakeCompleter:
    """Answers from a list; records each request (no network)."""

    def __init__(self, finish_reasons=None):
        self.calls: list[list[dict]] = []
        self.finish_reasons = finish_reasons or {}  # call number -> finish_reason

    def __call__(self, messages: list[dict]) -> Completion:
        self.calls.append(messages)
        number = len(self.calls)
        return Completion(
            text=f"  Guess {number}.  ",
            model="gpt-6-luna-2026-05-18",
            finish_reason=self.finish_reasons.get(number, "stop"),
            prompt_tokens=50 + number,
            completion_tokens=10 + number,
            system_fingerprint="fp_a",
        )


def catalogue(n=3):
    questions = [
        {"question_id": f"Q{i:03d}", "question": f"Question {i}?"} for i in range(1, n + 1)
    ]
    truth = {
        q["question_id"]: {"expected_answer": f"Answer {q['question_id']}."} for q in questions
    }
    return questions, truth


def run(path, questions, truth, completer=None):
    done: list[Completion] = []
    screen(questions, truth, completer or FakeCompleter(), path, done)
    return done


def test_min_dependent_rounds_up_two_thirds():
    assert min_dependent(48) == 32 and min_dependent(3) == 2 and min_dependent(4) == 3


def test_status_of_a_question():
    q, ref = "Question 1?", "Answer."
    assert status(None, q, ref) == NOT_SCREENED
    row = dict.fromkeys(SCREEN_HEADER, "") | {"question_sha256": text_sha256(q)}
    assert status(row, q, ref) == NOT_JUDGED
    row |= {"core_point": "hit", "reference_sha256": text_sha256(ref)}
    assert status(row, q, ref) == "hit"
    assert status(row, q, "Changed answer.") == NOT_JUDGED
    assert status(row, "Changed question?", ref) == NOT_SCREENED


def test_screen_answers_every_question_once_with_the_closed_book_prompt(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    fake = FakeCompleter()
    done = run(path, questions, truth, fake)
    assert len(done) == 3 and len(fake.calls) == 3
    assert fake.calls[0][1]["content"].endswith("Question: Question 1?\n\nAnswer:")
    rows = read_screen(path)
    assert [r["question_id"] for r in rows] == ["Q001", "Q002", "Q003"]
    assert rows[0]["answer"] == "Guess 1." and rows[0]["model"] == "gpt-6-luna-2026-05-18"
    assert rows[0]["core_point"] == "" and rows[0]["reference_sha256"] == ""
    assert run(path, questions, truth, fake) == [] and len(fake.calls) == 3  # nothing left to ask


def test_changed_question_is_asked_again_and_loses_its_verdict(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    run(path, questions, truth)
    judge(path, "Q002", "Question 2?", "Answer Q002.", "hit", "knows it", "2026-10-21")
    questions[1]["question"] = "Question 2, rephrased?"
    fake = FakeCompleter()
    assert len(run(path, questions, truth, fake)) == 1
    row = next(r for r in read_screen(path) if r["question_id"] == "Q002")
    assert row["question_sha256"] == text_sha256("Question 2, rephrased?")
    assert row["core_point"] == "" and row["note"] == "" and row["date"] == ""
    assert states(read_screen(path), questions, truth)["Q002"] == NOT_JUDGED


def test_changed_reference_keeps_the_answer_and_reopens_the_verdict(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    run(path, questions, truth)
    judge(path, "Q001", "Question 1?", "Answer Q001.", "miss", "", "2026-10-21")
    truth["Q001"]["expected_answer"] = "A better answer."
    fake = FakeCompleter()
    assert run(path, questions, truth, fake) == [] and fake.calls == []
    assert states(read_screen(path), questions, truth)["Q001"] == NOT_JUDGED
    assert read_screen(path)[0]["answer"] == "Guess 1."


def test_rows_of_removed_questions_disappear(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    run(path, questions, truth)
    run(path, questions[:2], truth)
    assert [r["question_id"] for r in read_screen(path)] == ["Q001", "Q002"]


def test_cut_off_answer_stops_and_keeps_earlier_answers(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    done: list[Completion] = []
    with pytest.raises(RuntimeError, match="Q002.*finish_reason='length'"):
        screen(questions, truth, FakeCompleter({2: "length"}), path, done)
    assert [r["question_id"] for r in read_screen(path)] == ["Q001"]
    assert len(done) == 2  # the cut-off reply was billed too, so the run record counts it


def test_judge_records_the_verdict_and_the_reference_hash(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    run(path, questions, truth)
    row = judge(path, "Q003", "Question 3?", "Answer Q003.", "hit", " partly known ", "2026-10-21")
    assert row["core_point"] == "hit" and row["note"] == "partly known"
    assert row["reference_sha256"] == text_sha256("Answer Q003.") and row["date"] == "2026-10-21"
    assert states(read_screen(path), questions, truth)["Q003"] == "hit"


def test_judge_refuses_unknown_verdicts_and_unscreened_questions(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    run(path, questions, truth)
    with pytest.raises(ValueError, match="hit or miss"):
        judge(path, "Q001", "Question 1?", "Answer Q001.", "", "", "2026-10-21")
    with pytest.raises(ValueError, match="Q009 is not screened"):
        judge(path, "Q009", "Question 9?", "Answer.", "hit", "", "2026-10-21")


def test_judge_refuses_a_stale_question(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    run(path, questions, truth)
    with pytest.raises(ValueError, match="changed since it was screened"):
        judge(path, "Q001", "Question 1, edited?", "Answer Q001.", "miss", "", "2026-10-21")


def test_findings_warn_about_unscreened_unjudged_and_too_many_hits(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue(4)
    run(path, questions[:3], truth)
    judge(path, "Q001", "Question 1?", "Answer Q001.", "hit", "", "2026-10-21")
    judge(path, "Q002", "Question 2?", "Answer Q002.", "hit", "", "2026-10-21")
    errors, found = findings(read_screen(path), questions, truth, n_quota=4)
    assert errors == []
    assert "closed-book: not screened Q004; run `catalogue.py screen` (ADR 0040)" in found
    assert "closed-book: not judged Q003; judge it in the editor tab Closed-book" in found
    assert "closed-book: 2 questions hit without context, at most 1 of 4 (ADR 0038)" in found


def test_findings_errors_for_unknown_questions_and_verdicts(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    run(path, questions, truth)
    rows = read_screen(path)
    rows[0]["core_point"] = "maybe"
    save_screen(path, rows)
    errors, _ = findings(read_screen(path), questions[1:], truth, n_quota=3)
    assert "closed-book row Q001: question is not in the catalogue" in errors
    assert "closed-book row Q001: unknown core_point 'maybe'" in errors


def test_counts_and_summary(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue(4)
    run(path, questions[:3], truth)
    judge(path, "Q001", "Question 1?", "Answer Q001.", "hit", "", "2026-10-21")
    judge(path, "Q002", "Question 2?", "Answer Q002.", "miss", "", "2026-10-21")
    c = counts(read_screen(path), questions, truth)
    assert c == {"dependent": 1, "known": 1, "not_screened": 1, "not_judged": 1}
    assert summary(c, 48) == (
        "Closed-book: 1 retrieval-dependent (at least 32), 1 known, 1 not screened, 1 not judged"
    )


def test_read_screen_rejects_wrong_columns_and_duplicates(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    path.write_text("question_id,answer\nQ001,x\n", encoding="utf-8")
    with pytest.raises(ValueError, match="columns"):
        read_screen(path)
    row = ",".join(["Q001", *[""] * (len(SCREEN_HEADER) - 1)])
    path.write_text(",".join(SCREEN_HEADER) + f"\n{row}\n{row}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate question_id"):
        read_screen(path)


def test_missing_file_has_no_rows(tmp_path):
    assert read_screen(tmp_path / "none.csv") == []
    assert closed_book.CLOSED_BOOK_VERDICTS == ("", "hit", "miss")
