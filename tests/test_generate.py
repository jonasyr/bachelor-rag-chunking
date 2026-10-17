import csv
import dataclasses
import json

import pytest

import freeze
from config import (
    CONTROL_STRATEGIES,
    LLM_MODEL,
    LLM_PRICE_INPUT_PER_MTOK,
    LLM_PRICE_OUTPUT_PER_MTOK,
    LLM_REASONING_EFFORT,
    LLM_TEMPERATURE,
    STRATEGY_IDS,
    TOP_K,
)
from generate import ANSWERS_HEADER, generate
from llm_client import Completion
from prompt import context, messages
from retrieve import GROUND_TRUTH_HEADER, HEADER, QUESTIONS_HEADER

STRATEGIES = list(STRATEGY_IDS)
QUESTIONS = {"Q001": "How do props work?", "Q002": "What is {{ msg }}?"}


class FakeCompleter:
    """Answers from the prompt it got; records every request (no network)."""

    def __init__(self, models=None, finish_reason="stop", text="Answer."):
        self.calls: list[list[dict]] = []
        self.models = models or {}  # call number -> reported model
        self.finish_reason = finish_reason
        self.text = text

    def __call__(self, prompt: list[dict]) -> Completion:
        self.calls.append(prompt)
        number = len(self.calls)
        return Completion(
            text=f"{self.text} #{number}",
            model=self.models.get(number, "gpt-6-luna-2026-05-18"),
            finish_reason=self.finish_reason,
            prompt_tokens=1000 + number,
            completion_tokens=100 + number,
            system_fingerprint=f"fp_{number % 2}",
        )


def write_csv(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    return path


def read(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def chunk_id(key, number):
    return f"{key}_D001_{number:04d}"


def result_rows(strategies=STRATEGIES, qids=("Q002", "Q001")):
    """Top-k per question and strategy; rank r holds chunk number TOP_K + 1 - r (reverse order)."""
    return [
        [q, s, rank, chunk_id(s, TOP_K + 1 - rank), "0.500000", 0]
        for q in qids
        for s in strategies
        for rank in range(1, TOP_K + 1)
    ]


@pytest.fixture
def files(tmp_path):
    def empty(name):
        (tmp_path / name).write_text("", encoding="utf-8")
        return tmp_path / name

    chunk_files = {}
    for key in [*STRATEGY_IDS, *CONTROL_STRATEGIES]:
        strategy = STRATEGY_IDS.get(key) or CONTROL_STRATEGIES[key]
        chunk_files[key] = tmp_path / f"chunks_{key.lower()}.jsonl"
        chunk_files[key].write_text(
            "".join(
                json.dumps(
                    {"chunk_id": chunk_id(key, n), "strategy": strategy, "text": f"{key} text {n}"}
                )
                + "\n"
                for n in range(1, TOP_K + 1)
            ),
            encoding="utf-8",
        )
    return {
        "results_file": write_csv(tmp_path / "retrieved_results.csv", HEADER, result_rows()),
        "questions_file": write_csv(
            tmp_path / "questions.csv",
            QUESTIONS_HEADER,
            [[q, text, "factual", "single", ""] for q, text in QUESTIONS.items()],
        ),
        "ground_truth_file": write_csv(
            tmp_path / "ground_truth.csv",
            GROUND_TRUTH_HEADER,
            [[q, "Ref.", "D001", "D001#a"] for q in QUESTIONS],
        ),
        "sections_file": empty("sections.jsonl"),
        "documents_file": empty("documents.jsonl"),
        "freeze_file": tmp_path / "catalogue_freeze.json",
        "chunk_files": {key: chunk_files[key] for key in STRATEGY_IDS},
        "out_file": tmp_path / "generated_answers.csv",
        "runs_file": tmp_path / "runs.jsonl",
        "control_chunk_file": chunk_files["K1"],
    }


def run(files, completer=None, **overrides):
    args = {k: v for k, v in files.items() if k != "control_chunk_file"} | overrides
    return generate(completer or FakeCompleter(), **args)


def runs(files):
    return [json.loads(line) for line in files["runs_file"].read_text().splitlines()]


def test_writes_one_answer_per_question_and_strategy(files):
    assert run(files) == len(QUESTIONS) * len(STRATEGIES)
    rows = read(files["out_file"])
    assert list(rows[0]) == ANSWERS_HEADER
    assert [(r["question_id"], r["strategy"]) for r in rows] == [
        (q, s) for q in sorted(QUESTIONS) for s in STRATEGIES
    ]


def test_prompt_holds_the_top_k_in_rank_order(files):
    completer = FakeCompleter()
    run(files, completer)
    chunks = {
        chunk_id(s, n): {"text": f"{s} text {n}"} for s in STRATEGIES for n in range(1, TOP_K + 1)
    }
    ranked = [chunk_id("C1", TOP_K + 1 - rank) for rank in range(1, TOP_K + 1)]
    assert completer.calls[0] == messages(QUESTIONS["Q001"], context(ranked, chunks))


def test_sources_and_tokens_come_from_retrieval_and_api(files):
    run(files)
    first = read(files["out_file"])[0]
    assert first["sources"] == ";".join(
        chunk_id("C1", TOP_K + 1 - rank) for rank in range(1, TOP_K + 1)
    )
    assert first["answer"] == "Answer. #1"
    assert (first["prompt_tokens"], first["completion_tokens"]) == ("1001", "101")


def test_answer_text_is_stored_verbatim(files):
    run(files, FakeCompleter(text='  Line one,\n"quoted"\n'))
    assert read(files["out_file"])[0]["answer"] == '  Line one,\n"quoted"\n #1'


def test_run_log_records_versions_inputs_and_cost(files):
    run(files)
    (record,) = runs(files)
    count = len(QUESTIONS) * len(STRATEGIES)
    prompt_tokens = sum(1000 + n for n in range(1, count + 1))
    completion_tokens = sum(100 + n for n in range(1, count + 1))
    assert record["step"] == "generate"
    assert record["model"] == LLM_MODEL
    assert record["model_reported"] == "gpt-6-luna-2026-05-18"
    assert record["system_fingerprints"] == ["fp_0", "fp_1"]
    assert record["temperature"] == LLM_TEMPERATURE
    assert record["reasoning_effort"] == LLM_REASONING_EFFORT
    assert record["strategy"] == ",".join(STRATEGIES)
    assert record["answers"] == count
    assert record["openai_sdk"]
    assert set(record["inputs_sha256"]) == {
        "retrieved_results.csv",
        "questions.csv",
        "ground_truth.csv",
        *(f"chunks_{s.lower()}.jsonl" for s in STRATEGIES),
    }
    assert (record["prompt_tokens"], record["completion_tokens"]) == (
        prompt_tokens,
        completion_tokens,
    )
    expected = (
        prompt_tokens * LLM_PRICE_INPUT_PER_MTOK + completion_tokens * LLM_PRICE_OUTPUT_PER_MTOK
    ) / 1_000_000
    assert record["cost_usd"] == pytest.approx(expected)
    assert sum(s["cost_usd"] for s in record["by_strategy"].values()) == pytest.approx(expected)
    assert record["by_strategy"]["C1"]["prompt_tokens"] == 1001 + 1004


def test_existing_answers_are_never_overwritten(files):
    files["out_file"].write_text("kept", encoding="utf-8")
    completer = FakeCompleter()
    with pytest.raises(FileExistsError, match="delete it"):
        run(files, completer)
    assert completer.calls == []
    assert files["out_file"].read_text(encoding="utf-8") == "kept"


@pytest.mark.parametrize("reason", ["length", "content_filter"])
def test_answer_not_ended_by_stop_writes_nothing(files, reason):
    with pytest.raises(RuntimeError, match=reason):
        run(files, FakeCompleter(finish_reason=reason))
    assert not files["out_file"].exists()
    assert not files["runs_file"].exists()


def test_empty_answer_writes_nothing(files):
    class Empty(FakeCompleter):
        def __call__(self, prompt):
            result = super().__call__(prompt)
            return dataclasses.replace(result, text="  ")

    with pytest.raises(RuntimeError, match="empty"):
        run(files, Empty())
    assert not files["out_file"].exists()


def test_changed_model_behind_the_alias_writes_nothing(files):
    with pytest.raises(RuntimeError, match="gpt-6-luna-2026-07-01"):
        run(files, FakeCompleter(models={4: "gpt-6-luna-2026-07-01"}))
    assert not files["out_file"].exists()


def test_control_strategy_is_refused(files):
    rows = result_rows() + result_rows(strategies=["K1"])
    write_csv(files["results_file"], HEADER, rows)
    completer = FakeCompleter()
    with pytest.raises(ValueError, match="K1"):
        run(files, completer)
    assert completer.calls == []


def test_chunk_files_must_be_exactly_the_experiment(files):
    with pytest.raises(ValueError, match="chunk_files"):
        run(files, chunk_files={k: files["chunk_files"][k] for k in ("C1", "C2")})


def test_chunk_of_another_strategy_is_refused(files):
    rows = result_rows()
    rows[0][3] = chunk_id("C2", 1)  # C2 chunk in a C1 row
    write_csv(files["results_file"], HEADER, rows)
    completer = FakeCompleter()
    with pytest.raises(ValueError, match="unknown chunk"):
        run(files, completer)
    assert completer.calls == []


def test_missing_retrieval_rows_are_refused_before_any_call(files):
    write_csv(files["results_file"], HEADER, result_rows()[:-1])
    completer = FakeCompleter()
    with pytest.raises(ValueError, match="ranks"):
        run(files, completer)
    assert completer.calls == []


def test_main_catalogue_must_be_frozen(files, monkeypatch):
    monkeypatch.setattr(freeze, "QUESTIONS_FILE", files["questions_file"])
    monkeypatch.setattr(freeze, "GROUND_TRUTH_FILE", files["ground_truth_file"])
    completer = FakeCompleter()
    with pytest.raises(RuntimeError, match="not frozen"):
        run(files, completer)
    assert completer.calls == []
