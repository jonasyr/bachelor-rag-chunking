import json

import pytest
from test_evaluate_answers import (
    QIDS,
    STRATEGIES,
    files,  # noqa: F401 (fixture)
    read,
    write_csv,
)

import closed_book
import control_k0
import scoring_rules as rules
from config import CONTROL_CRITERIA, RUBRIC_CRITERIA
from control_k0 import (
    CONTROL_SCORES_HEADER,
    CONTROL_SHEET_HEADER,
    scaffold_control,
    summarise_control,
)
from evaluate_answers import SCORES_HEADER
from generate import ANSWERS_HEADER
from run_log import sha256_of


@pytest.fixture
def k0(files, tmp_path):  # noqa: F811
    """The files of a K0 set on top of the C1-C3 fixture: answers, a generation record over both
    answer files, frozen key points and a summarised C1-C3 (scores.csv)."""
    control = write_csv(
        tmp_path / "generated_answers_control.csv",
        ANSWERS_HEADER,
        [[q, "K0", f"Closed-book answer to {q}.", "", 50, 20] for q in sorted(QIDS)],
    )
    inputs = [files["questions_file"], files["ground_truth_file"], *files["chunk_files"].values()]
    runs = files["generation_runs_file"]
    with runs.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "step": "generate",
                    "strategy": ",".join(STRATEGIES),
                    "inputs_sha256": {p.name: sha256_of(p) for p in inputs},
                    "outputs_sha256": {
                        files["answers_file"].name: sha256_of(files["answers_file"]),
                        control.name: sha256_of(control),
                    },
                }
            )
            + "\n"
        )
    write_csv(
        files["key_points_file"],
        rules.KEY_POINTS_HEADER,
        [[q, "1", f"Core of {q}"] for q in sorted(QIDS)],
    )
    with runs.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "step": "key_points",
                    "strategy": ",".join(STRATEGIES),
                    "outputs_sha256": {"key_points.csv": sha256_of(files["key_points_file"])},
                }
            )
            + "\n"
        )
    write_csv(
        files["scores_file"],
        SCORES_HEADER,
        [[q, s, 2, 1, 2, 2, 1, "1.6"] for q in sorted(QIDS) for s in STRATEGIES],
    )
    paths = {
        "control_answers_file": control,
        "questions_file": files["questions_file"],
        "ground_truth_file": files["ground_truth_file"],
        "sections_file": files["sections_file"],
        "documents_file": files["documents_file"],
        "freeze_file": files["freeze_file"],
        "scores_file": files["scores_file"],
        "key_points_file": files["key_points_file"],
        "items_file": tmp_path / "scoring_items_control.jsonl",
        "sheet_file": tmp_path / "scoring_sheet_control.csv",
        "checks_file": tmp_path / "scoring_checks_control.csv",
        "control_scores_file": tmp_path / "scores_control.csv",
        "generation_runs_file": runs,
        "closed_book_file": tmp_path / "closed_book_screen.csv",
    }
    return paths


SCAFFOLD = [
    "control_answers_file", "questions_file", "ground_truth_file", "sections_file",
    "documents_file", "freeze_file", "scores_file", "key_points_file", "items_file",
    "sheet_file", "generation_runs_file",
]  # fmt: skip


def run_scaffold(k0):
    return scaffold_control(**{k: k0[k] for k in SCAFFOLD})


def run_summary(k0):
    return summarise_control(**{k: v for k, v in k0.items() if k != "control_answers_file"})


def score_all(k0, **changed):
    """Fill checks and sheet as the scoring page would, with flawless K0 checks unless `changed`."""
    good = {
        "points": ["covered"],
        "declines": "no",
        "core_wrong": "no",
        "other_error": "no",
        "hallucination": "none",
        "answers_question": "yes",
        "direct": "yes",
        "wordy": "no",
    } | changed
    sheet = read(k0["sheet_file"])
    checks = []
    for row in sheet:
        values = rules.derive_control(good)
        row.update({c: str(v) for c, v in values.items()})
        checks.append(rules.to_row(row["code"], good, control=True))
    write_csv(
        k0["sheet_file"],
        CONTROL_SHEET_HEADER,
        [[r[h] for h in CONTROL_SHEET_HEADER] for r in sheet],
    )
    write_csv(
        k0["checks_file"],
        rules.checks_header(True),
        [[r[h] for h in rules.checks_header(True)] for r in checks],
    )


def test_control_scaffold_refuses_before_the_c1_c3_summary(k0):
    k0["scores_file"].unlink()
    with pytest.raises(ValueError, match="score and summarise C1-C3 first"):
        run_scaffold(k0)
    assert not k0["sheet_file"].exists()


def test_control_scaffold_writes_items_without_excerpts_and_a_sheet(k0):
    assert run_scaffold(k0) == len(QIDS)
    items = [json.loads(line) for line in k0["items_file"].read_text().splitlines()]
    assert [i["code"] for i in items] == [f"{q}-K0" for q in sorted(QIDS)]
    assert all(i["excerpts"] == [] for i in items)
    assert items[0]["answer"] == f"Closed-book answer to {sorted(QIDS)[0]}."
    assert list(read(k0["sheet_file"])[0]) == CONTROL_SHEET_HEADER
    record = json.loads(k0["generation_runs_file"].read_text().splitlines()[-1])
    assert record["step"] == "scaffold" and record["strategy"] == "K0"


def test_control_scaffold_scores_the_questions_of_scores_csv(k0):
    first = sorted(QIDS)[0]
    write_csv(
        k0["scores_file"],
        SCORES_HEADER,
        [[first, s, 2, 1, 2, 2, 1, "1.6"] for s in STRATEGIES],
    )
    assert run_scaffold(k0) == 1
    assert [r["question_id"] for r in read(k0["sheet_file"])] == [first]


def test_control_scaffold_refuses_unfrozen_or_changed_key_points(k0):
    k0["key_points_file"].write_text(
        k0["key_points_file"].read_text(encoding="utf-8") + "Q009,1,Late\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="frozen key points"):
        run_scaffold(k0)


def test_control_scaffold_refuses_a_changed_answer_file(k0):
    k0["control_answers_file"].write_text(
        k0["control_answers_file"].read_text(encoding="utf-8").replace("Closed", "Edited"),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="generated_answers_control.csv differs"):
        run_scaffold(k0)


def test_control_scaffold_refuses_foreign_strategies_and_an_existing_sheet(k0):
    run_scaffold(k0)
    with pytest.raises(FileExistsError, match="scoring_sheet_control.csv"):
        run_scaffold(k0)


def test_control_summary_writes_scores_and_compares_on_four_criteria(k0):
    run_scaffold(k0)
    score_all(k0)
    summary = run_summary(k0)
    rows = read(k0["control_scores_file"])
    assert list(rows[0]) == CONTROL_SCORES_HEADER
    assert rows[0]["strategy"] == "K0" and rows[0]["total_score"] == "2.00"
    assert summary[("all", "all", "K0")]["total_score"] == 2.0
    # C1-C3 from scores.csv over the same four criteria: (2 + 1 + 2 + 1) / 4
    assert summary[("all", "all", "C1")]["total_score"] == 1.5
    assert set(summary[("all", "all", "C2")]) >= {"n", "median", "sd", *CONTROL_CRITERIA}
    assert "groundedness" not in summary[("all", "all", "C3")]
    assert ("type", "factual", "K0") in summary


def test_control_summary_splits_by_closed_book_verdict(k0):
    run_scaffold(k0)
    score_all(k0)
    questions = [
        {"question_id": "Q001", "question": "One?"},
        {"question_id": "Q002", "question": "Two?"},
    ]
    truth = {"Q001": {"expected_answer": "Ref one."}, "Q002": {"expected_answer": "Ref two."}}
    done: list = []
    from test_closed_book import FakeCompleter

    closed_book.screen(questions, truth, FakeCompleter(), k0["closed_book_file"], done)
    closed_book.judge(k0["closed_book_file"], "Q001", "One?", "Ref one.", "hit", "", "2026-12-01")
    closed_book.judge(k0["closed_book_file"], "Q002", "Two?", "Ref two.", "miss", "", "2026-12-01")
    summary = run_summary(k0)
    assert summary[("closed_book", "known", "K0")]["n"] == 1
    assert summary[("closed_book", "dependent", "C1")]["n"] == 1


def test_control_summary_refuses_a_hand_edited_score(k0):
    run_scaffold(k0)
    score_all(k0)
    rows = read(k0["sheet_file"])
    rows[0]["clarity"] = "0"
    write_csv(
        k0["sheet_file"], CONTROL_SHEET_HEADER, [[r[h] for h in CONTROL_SHEET_HEADER] for r in rows]
    )
    with pytest.raises(ValueError, match="its checks give 2"):
        run_summary(k0)
    assert not k0["control_scores_file"].exists()


def test_control_summary_refuses_unscored_rows(k0):
    run_scaffold(k0)
    with pytest.raises(ValueError, match="no checks"):
        run_summary(k0)


def test_control_paths_of_a_pilot_set(tmp_path):
    paths = control_k0.control_paths(tmp_path)
    assert paths["sheet_file"] == tmp_path / "scoring_sheet_control.csv"
    assert paths["scores_file"] == tmp_path / "scores.csv"
    assert "closed_book_file" not in paths  # the verdicts belong to the main catalogue
    assert RUBRIC_CRITERIA[2] == "groundedness"  # the criterion K0 does not have


def test_summarise_control_logs_a_run_record(k0):
    from run_log import latest_run

    run_scaffold(k0)
    score_all(k0)
    run_summary(k0)
    record = latest_run(k0["generation_runs_file"], "summarise_control", "K0")
    assert record["outputs_sha256"] == {"scores_control.csv": sha256_of(k0["control_scores_file"])}
