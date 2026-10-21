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
        "retrieval_inputs": {",".join(STRATEGIES): [tmp_path / "retrieved_results.csv"],
                             "K1": [tmp_path / "retrieved_results_control.csv"]},
        "scores_inputs": [tmp_path / "scoring_sheet.csv"],
        "scores_control_inputs": [tmp_path / "scoring_sheet_control.csv"],
        "answers_files": [tmp_path / "generated_answers.csv"],
    }  # fmt: skip
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


def test_main_refuses_stale_inputs(paths):
    """scores.csv still matches its summarise record, but the sheet it was built from changed."""
    sheet = paths["scores_inputs"][0]
    sheet.write_text("code,correctness\nA1,2\n", encoding="utf-8")
    runs = paths["generation_runs_file"]
    append_step_run("summarise", ",".join(STRATEGIES), [sheet], [paths["scores_file"]], runs)
    load(paths, main=False)
    sheet.write_text("code,correctness\nA1,1\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="scoring_sheet.csv"):
        load(paths, main=False)


def test_costs_need_the_answers_of_the_latest_generate_run(paths):
    answers = paths["answers_files"][0]
    answers.write_text("question_id,strategy,answer\n", encoding="utf-8")
    runs = paths["generation_runs_file"]
    record = json.loads(runs.read_text(encoding="utf-8").splitlines()[-1])
    record["outputs_sha256"] = {answers.name: "0" * 64}
    with runs.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    with pytest.raises(RuntimeError, match="generated_answers.csv"):
        load(paths, main=False)


def test_set_pointing_at_main_catalogue_is_refused(paths, monkeypatch):
    """--set data/evaluation must not reach the pilot exceptions: it is the main catalogue."""
    import freeze

    monkeypatch.setattr(freeze, "QUESTIONS_FILE", paths["questions_file"])
    with pytest.raises(RuntimeError, match="not frozen"):
        load(paths, main=False)


# ---------------------------------------------------------------- RAGAS (ADR 0047)


def _ragas_rows(nan=False):
    rows = []
    for q in QIDS:
        for i, s in enumerate(STRATEGIES):
            rows.append({"question_id": q, "strategy": s, "faithfulness": f"0.{i + 5}00000",
                         "response_relevancy": "0.800000", "context_precision": "0.500000",
                         "context_recall": "" if nan and (q, s) == ("Q001", "C2") else "1.000000",
                         "nan_reasons": "context_recall: no reference" if nan and
                         (q, s) == ("Q001", "C2") else ""})  # fmt: skip
    return rows


def _with_ragas(paths, tmp_path, rows=None):
    from ragas_eval import RAGAS_HEADER

    paths["ragas_file"] = tmp_path / "ragas_scores.csv"
    paths["ragas_repeat_file"] = tmp_path / "ragas_scores_repeat.csv"
    source = tmp_path / "generated_answers.csv"
    source.write_text("question_id,strategy,answer\n", encoding="utf-8")
    paths["ragas_inputs"] = [source]
    write_csv(paths["ragas_file"], RAGAS_HEADER, rows or _ragas_rows())
    append_step_run(
        "ragas", ",".join(STRATEGIES), paths["ragas_inputs"], [paths["ragas_file"]],
        paths["generation_runs_file"],
    )  # fmt: skip
    return paths


def test_ragas_loaded_and_checked(paths, tmp_path):
    assert load(paths, main=False).ragas is None  # no keys: nothing to load
    paths["ragas_file"] = tmp_path / "ragas_scores.csv"
    paths["ragas_repeat_file"] = tmp_path / "ragas_scores_repeat.csv"
    data = load(paths, main=False)
    assert data.ragas is None and data.ragas_repeat is None
    assert any("ragas_scores.csv fehlt" in n for n in data.notes)
    _with_ragas(paths, tmp_path)
    data = load(paths, main=False)
    assert len(data.ragas) == len(QIDS) * len(STRATEGIES) and data.ragas_repeat is None
    paths["ragas_file"].write_text(
        paths["ragas_file"].read_text(encoding="utf-8").replace("0.500000", "0.400000", 1),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="ragas_scores.csv"):
        load(paths, main=False)  # stale: the record hashed another file


def test_ragas_input_change_is_refused(paths, tmp_path):
    _with_ragas(paths, tmp_path)
    paths["ragas_inputs"][0].write_text(
        "question_id,strategy,answer\nQ001,C1,x\n", encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="generated_answers.csv"):
        load(paths, main=False)


def test_ragas_incomplete_grid_is_refused(paths, tmp_path):
    _with_ragas(paths, tmp_path, _ragas_rows()[:-1])
    with pytest.raises(ValueError, match="Q002/C3"):
        load(paths, main=False)


def _blinded(paths, tmp_path, answers):
    from evaluate_answers import KEY_HEADER
    from scoring_rules import CHECKS_HEADER

    paths["scoring_checks_file"] = tmp_path / "scoring_checks.csv"
    paths["scoring_key_file"] = tmp_path / "scoring_key.csv"
    codes = {(q, s): f"A{n:02d}" for n, (q, s) in enumerate(sorted(answers), 1)}
    # the codes are shuffled against the key order on purpose
    write_csv(
        paths["scoring_key_file"], KEY_HEADER,
        [{"code": c, "question_id": q, "strategy": s} for (q, s), c in codes.items()],
    )  # fmt: skip
    rows = []
    for key, value in reversed(list(answers.items())):
        row = dict.fromkeys(CHECKS_HEADER, "no")
        rows.append(row | {"code": codes[key], "rules_version": "1", "points": "covered",
                           "answers_question": value})  # fmt: skip
    write_csv(paths["scoring_checks_file"], CHECKS_HEADER, rows)


def test_answers_question_is_unblinded(paths, tmp_path):
    answers = {(q, s): "yes" for q in QIDS for s in STRATEGIES}
    answers[("Q002", "C3")] = "no"
    _blinded(paths, tmp_path, answers)
    data = load(paths, main=False)
    assert data.answers_question[("Q002", "C3")] == 0
    assert data.answers_question[("Q001", "C3")] == 1
    assert len(data.answers_question) == 6


def test_answers_question_absent_is_noted(paths, tmp_path):
    paths["scoring_checks_file"] = tmp_path / "scoring_checks.csv"
    paths["scoring_key_file"] = tmp_path / "scoring_key.csv"
    data = load(paths, main=False)
    assert data.answers_question is None
    assert any("answers_question" in n for n in data.notes)


def test_ragas_repeat_is_loaded_with_its_own_record(paths, tmp_path):
    from ragas_eval import RAGAS_HEADER

    _with_ragas(paths, tmp_path)
    write_csv(paths["ragas_repeat_file"], RAGAS_HEADER, _ragas_rows())
    append_step_run(
        "ragas_repeat", ",".join(STRATEGIES), paths["ragas_inputs"], [paths["ragas_repeat_file"]],
        paths["generation_runs_file"],
    )  # fmt: skip
    assert len(load(paths, main=False).ragas_repeat) == 6
