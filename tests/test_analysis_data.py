import json

import pytest

import analysis_data
from analysis_data import load
from atomic_csv import write_csv
from config import STRATEGY_IDS
from control_k0 import CONTROL_SCORES_HEADER
from evaluate_answers import SCORES_HEADER
from evaluate_retrieval import SCORES_HEADER as RETRIEVAL_HEADER
from retrieve import GROUND_TRUTH_HEADER, QUESTIONS_HEADER
from run_log import append_step_run

QIDS = ["Q001", "Q002"]
STRATEGIES = list(STRATEGY_IDS)


def retrieval_rows(strategies, qids=QIDS):
    return [
        {"question_id": q, "strategy": s, "rule": rule, "hit": "1", "reciprocal_rank": "0.5",
         "precision": "0.2", "recall": "1.0", "context_tokens": "900"}
        for q in qids for s in strategies for rule in ("main", "sensitivity")
    ]  # fmt: skip


@pytest.fixture
def paths(tmp_path):
    p = {
        "questions_file": tmp_path / "questions.csv",
        "ground_truth_file": tmp_path / "ground_truth.csv",
        "sections_file": tmp_path / "sections.jsonl",
        "documents_file": tmp_path / "documents.jsonl",
        "freeze_file": tmp_path / "catalogue_freeze.json",
        "retrieval_file": tmp_path / "retrieval_scores.csv",
        "retrieval_control_file": tmp_path / "retrieval_scores_control.csv",
        "scores_file": tmp_path / "scores.csv",
        "scores_control_file": tmp_path / "scores_control.csv",
        "retrieval_runs_file": tmp_path / "runs.jsonl",
        "generation_runs_file": tmp_path / "runs.jsonl",
        "embedding_runs_file": tmp_path / "embedding_runs.jsonl",
        "chunk_files": {},
        "closed_book_file": None,
    }
    write_csv(
        p["questions_file"],
        QUESTIONS_HEADER,
        [{"question_id": q, "question": f"{q}?", "type": "factual", "difficulty": "single",
          "notes": ""} for q in QIDS],
    )  # fmt: skip
    write_csv(
        p["ground_truth_file"],
        GROUND_TRUTH_HEADER,
        [{"question_id": q, "expected_answer": "A.", "relevant_doc_ids": "D001",
          "relevant_section_ids": "D001#a"} for q in QIDS],
    )  # fmt: skip
    p["sections_file"].write_text("", encoding="utf-8")
    p["documents_file"].write_text("", encoding="utf-8")
    write_csv(p["retrieval_file"], RETRIEVAL_HEADER, retrieval_rows(STRATEGIES))
    write_csv(p["retrieval_control_file"], RETRIEVAL_HEADER, retrieval_rows(["K1"]))
    write_csv(
        p["scores_file"],
        SCORES_HEADER,
        [{"question_id": q, "strategy": s, "correctness": "2", "completeness": "2",
          "groundedness": "2", "no_hallucination": "2", "clarity": "2", "total_score": "2.0"}
         for q in QIDS for s in STRATEGIES],
    )  # fmt: skip
    write_csv(
        p["scores_control_file"],
        CONTROL_SCORES_HEADER,
        [{"question_id": q, "strategy": "K0", "correctness": "1", "completeness": "0",
          "no_hallucination": "1", "clarity": "2", "total_score": "1.00"} for q in QIDS],
    )  # fmt: skip
    runs = p["retrieval_runs_file"]
    append_step_run("evaluate_retrieval", ",".join(STRATEGIES), [], [p["retrieval_file"]], runs)
    append_step_run("evaluate_retrieval", "K1", [], [p["retrieval_control_file"]], runs)
    append_step_run("summarise", ",".join(STRATEGIES), [], [p["scores_file"]], runs)
    append_step_run("summarise_control", "K0", [], [p["scores_control_file"]], runs)
    with runs.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"step": "generate", "strategy": ",".join(STRATEGIES),
                            "by_strategy": {"C1": {"prompt_tokens": 10, "completion_tokens": 2,
                                                   "cost_usd": 0.001}}}) + "\n")  # fmt: skip
    return p


def test_loads_a_complete_set(paths):
    data = load(paths, main=False)
    assert sorted(data.questions["question_id"]) == QIDS
    assert set(data.retrieval["strategy"]) == {*STRATEGIES, "K1"}
    assert len(data.scores) == len(QIDS) * len(STRATEGIES)
    assert data.scores_control is not None and data.generation["C1"]["cost_usd"] == 0.001
    assert data.verdicts is None and data.chunks is None and data.embedding is None
    assert any("closed-book" in n for n in data.notes)


def test_main_refuses_unfrozen_catalogue(paths, monkeypatch):
    import freeze

    monkeypatch.setattr(freeze, "QUESTIONS_FILE", paths["questions_file"])
    with pytest.raises(RuntimeError, match="not frozen"):
        load(paths, main=True)


def test_main_refuses_stale_scores(paths):
    paths["scores_file"].write_text(
        paths["scores_file"].read_text(encoding="utf-8").replace("2.0", "1.8", 1),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="scores.csv"):
        load(paths, main=False)


def test_incomplete_grid_is_refused(paths):
    rows = [
        r for r in retrieval_rows(STRATEGIES) if (r["question_id"], r["strategy"]) != ("Q002", "C2")
    ]
    write_csv(paths["retrieval_file"], RETRIEVAL_HEADER, rows)
    append_step_run(
        "evaluate_retrieval", ",".join(STRATEGIES), [], [paths["retrieval_file"]],
        paths["retrieval_runs_file"],
    )  # fmt: skip
    with pytest.raises(ValueError, match="Q002/C2"):
        load(paths, main=False)


def test_set_without_summarise_record_notes_it(paths, tmp_path):
    runs = paths["retrieval_runs_file"]
    kept = [
        line for line in runs.read_text(encoding="utf-8").splitlines() if '"summarise' not in line
    ]
    runs.write_text("\n".join(kept) + "\n", encoding="utf-8")
    data = load(paths, main=False)
    assert any("ohne Laufeintrag" in n for n in data.notes)
    with pytest.raises(RuntimeError, match="summarise"):
        load(paths, main=True, frozen_check=False)


def test_set_paths_use_the_shared_corpus(tmp_path):
    p = analysis_data.set_paths(tmp_path)
    assert p["scores_file"] == tmp_path / "scores.csv"
    assert p["closed_book_file"] is None
    assert p["embedding_runs_file"].name == "embedding_runs.jsonl"
    assert "K1" in p["chunk_files"]
