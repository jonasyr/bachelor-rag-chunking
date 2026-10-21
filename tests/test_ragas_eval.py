import csv
import json

import pytest

import freeze
from config import (
    RAGAS_METRICS,
    RAGAS_REPEAT_FILE_NAME,
    STRATEGY_IDS,
)
from ragas_client import ApiRecorder
from ragas_eval import RAGAS_HEADER, Sample, build_samples, run, set_paths, validated
from retrieve import GROUND_TRUTH_HEADER, QUESTIONS_HEADER
from run_log import latest_run, sha256_of

STRATEGIES = list(STRATEGY_IDS)
EXPERIMENT = ",".join(STRATEGIES)
QUESTIONS = {"Q001": "How do props work?", "Q002": "What is {{ msg }}?"}
ANSWER_HEADER = [
    "question_id",
    "strategy",
    "answer",
    "sources",
    "prompt_tokens",
    "completion_tokens",
]


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


class FakeScorer:
    def __init__(self, override=None, fail=False):
        self.calls: list[list[Sample]] = []
        self.override = override or {}  # (qid, strategy) -> {metric: (value, reason)}
        self.fail = fail

    def __call__(self, samples):
        self.calls.append(samples)
        if self.fail:
            raise RuntimeError("judge unavailable")
        out = []
        for s in samples:
            values = {m: (0.5, "") for m in RAGAS_METRICS}
            values |= self.override.get((s.question_id, s.strategy), {})
            out.append(values)
        return out


class FakeCreated:
    def __init__(self, *values):
        self.values = list(values) or [7, 7]
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.values[min(self.calls, len(self.values)) - 1]


@pytest.fixture
def files(tmp_path):
    chunk_files = {}
    for key in STRATEGIES:
        chunk_files[key] = tmp_path / f"chunks_{key.lower()}.jsonl"
        chunk_files[key].write_text(
            "".join(
                json.dumps({"chunk_id": chunk_id(key, n), "text": f"{key} text {n}"}) + "\n"
                for n in (1, 2)
            ),
            encoding="utf-8",
        )
    answers = [
        [q, s, f"Answer {q} {s}", f"{chunk_id(s, 2)};{chunk_id(s, 1)}", 10, 5]
        for q in sorted(QUESTIONS)
        for s in STRATEGIES
    ]
    answers.append(["Q001", "K0", "closed", "", 10, 5])
    (tmp_path / "sections.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "documents.jsonl").write_text("", encoding="utf-8")
    return {
        "answers_file": write_csv(tmp_path / "generated_answers.csv", ANSWER_HEADER, answers),
        "results_file": write_csv(tmp_path / "retrieved_results.csv", ["a"], [["1"]]),
        "questions_file": write_csv(
            tmp_path / "questions.csv",
            QUESTIONS_HEADER,
            [[q, t, "factual", "single", ""] for q, t in QUESTIONS.items()],
        ),
        "ground_truth_file": write_csv(
            tmp_path / "ground_truth.csv",
            GROUND_TRUTH_HEADER,
            [[q, f"Ref {q}", "D001", "D001#a"] for q in QUESTIONS],
        ),
        "sections_file": tmp_path / "sections.jsonl",
        "documents_file": tmp_path / "documents.jsonl",
        "freeze_file": tmp_path / "catalogue_freeze.json",
        "chunk_files": chunk_files,
        "scores_file": write_csv(tmp_path / "scores.csv", ["a"], [["1"]]),
        "runs_file": tmp_path / "runs.jsonl",
        "out_file": tmp_path / "ragas_scores.csv",
        "repeat_file": tmp_path / RAGAS_REPEAT_FILE_NAME,
    }


def log(files, step, inputs=(), outputs=(), strategy=EXPERIMENT):
    record = {
        "step": step,
        "strategy": strategy,
        "inputs_sha256": {f.name: sha256_of(f) for f in inputs},
        "outputs_sha256": {f.name: sha256_of(f) for f in outputs},
    }
    with files["runs_file"].open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def record_upstream(files, summarise=True):
    log(files, "generate", outputs=[files["answers_file"]])
    if summarise:
        log(files, "summarise", outputs=[files["scores_file"]])


def go(files, scorer=None, recorder=None, created=None, main=True, record=True, **kw):
    if record:
        record_upstream(files, summarise=main)
    return run(
        scorer or FakeScorer(),
        recorder or ApiRecorder(),
        created or FakeCreated(),
        files,
        main,
        **kw,
    )


def records(files):
    return [json.loads(x) for x in files["runs_file"].read_text().splitlines()]


def test_contexts_are_the_sources_in_order(files):
    samples = build_samples(
        files["answers_file"],
        files["questions_file"],
        files["ground_truth_file"],
        files["chunk_files"],
    )
    first = samples[0]
    assert (first.question_id, first.strategy) == ("Q001", "C1")
    assert first.retrieved_contexts == ("C1 text 2", "C1 text 1")
    assert first.user_input == QUESTIONS["Q001"]
    assert first.response == "Answer Q001 C1"
    assert first.reference == "Ref Q001"


def test_k0_and_k1_rows_are_not_scored(files):
    scorer = FakeScorer()
    assert go(files, scorer) == len(QUESTIONS) * 3
    assert {s.strategy for s in scorer.calls[0]} == set(STRATEGIES)
    assert [(r["question_id"], r["strategy"]) for r in read(files["out_file"])] == [
        (q, s) for q in sorted(QUESTIONS) for s in STRATEGIES
    ]
    assert list(read(files["out_file"])[0]) == RAGAS_HEADER


def test_other_strategy_is_refused(files):
    rows = read(files["answers_file"])
    write_csv(
        files["answers_file"],
        ANSWER_HEADER,
        [list(r.values()) for r in rows] + [["Q001", "K1", "x", "", 1, 1]],
    )
    with pytest.raises(ValueError, match="K1"):
        build_samples(
            files["answers_file"],
            files["questions_file"],
            files["ground_truth_file"],
            files["chunk_files"],
        )


def test_missing_chunk_is_refused_before_any_call(files):
    rows = read(files["answers_file"])
    rows[0]["sources"] = "C1_D001_0099"
    write_csv(files["answers_file"], ANSWER_HEADER, [list(r.values()) for r in rows])
    scorer = FakeScorer()
    with pytest.raises(ValueError, match="C1_D001_0099"):
        go(files, scorer)
    assert scorer.calls == []
    assert not files["out_file"].exists()


@pytest.mark.parametrize("case", ["not_frozen", "no_summarise", "stale_answers"])
def test_main_requires_freeze_summarise_and_current_answers(files, monkeypatch, case):
    monkeypatch.setattr(freeze, "QUESTIONS_FILE", files["questions_file"])
    monkeypatch.setattr(freeze, "GROUND_TRUTH_FILE", files["ground_truth_file"])
    if case != "not_frozen":
        names = [
            files[k]
            for k in ("questions_file", "ground_truth_file", "sections_file", "documents_file")
        ]
        files["freeze_file"].write_text(
            json.dumps({"date": "2026-10-01", "sha256": {f.name: sha256_of(f) for f in names}})
        )
    scorer = FakeScorer()
    record_upstream(files, summarise=case != "no_summarise")
    if case == "stale_answers":
        with files["answers_file"].open("a", encoding="utf-8") as f:
            f.write("Q002,C1,late,C1_D001_0001,1,1\n")
    with pytest.raises(RuntimeError):
        run(scorer, ApiRecorder(), FakeCreated(), files, True)
    assert scorer.calls == []
    assert not files["out_file"].exists()


def test_pilot_without_summarise_notes_and_runs(files, capsys):
    assert go(files, main=False) == len(QUESTIONS) * 3
    assert "summarise" in capsys.readouterr().out


def test_existing_output_is_refused(files):
    files["out_file"].write_text("keep", encoding="utf-8")
    scorer = FakeScorer()
    with pytest.raises(FileExistsError):
        go(files, scorer)
    assert files["out_file"].read_text() == "keep"
    assert scorer.calls == []


def test_nan_with_reason_is_stored_and_counted(files):
    scorer = FakeScorer({("Q001", "C2"): {"faithfulness": (None, "no statements")}})
    go(files, scorer)
    row = next(
        r for r in read(files["out_file"]) if (r["question_id"], r["strategy"]) == ("Q001", "C2")
    )
    assert row["faithfulness"] == ""
    assert row["nan_reasons"] == "faithfulness: no statements"
    assert row["response_relevancy"] == "0.500000"
    (record,) = (r for r in records(files) if r["step"] == "ragas")
    assert record["nan_counts"] == {m: int(m == "faithfulness") for m in RAGAS_METRICS}


@pytest.mark.parametrize(
    "bad",
    [
        {"faithfulness": (1.2, "")},
        {"faithfulness": (None, "")},
        {"faithfulness": (float("nan"), "")},
        "missing",
        "raises",
    ],
)
def test_invalid_value_writes_nothing(files, bad):
    if bad == "raises":
        scorer = FakeScorer(fail=True)
    elif bad == "missing":
        scorer = FakeScorer()
        inner = scorer.__call__
        scorer = lambda samples: [  # noqa: E731
            {k: v for k, v in d.items() if k != "faithfulness"} for d in inner(samples)
        ]
    else:
        scorer = FakeScorer({("Q002", "C3"): bad})
    with pytest.raises(Exception):  # noqa: B017
        go(files, scorer)
    assert not files["out_file"].exists()
    assert [r for r in records(files) if r["step"] == "ragas"] == []


def test_judge_model_change_writes_nothing(files):
    with pytest.raises(RuntimeError, match="changed during the run"):
        go(files, created=FakeCreated(1, 2))
    assert not files["out_file"].exists()
    recorder = ApiRecorder()
    recorder.models = {"a", "b"}
    with pytest.raises(RuntimeError, match="nothing was written"):
        go(files, recorder=recorder, record=False)
    assert not files["out_file"].exists()
    assert [r for r in records(files) if r["step"] == "ragas"] == []


def test_record_hashes_inputs_and_output(files):
    recorder = ApiRecorder()
    recorder.models = {"gpt-6-sol-x"}
    recorder.chat_prompt_tokens, recorder.chat_completion_tokens = 1000, 200
    recorder.embedding_tokens = 50
    go(files, recorder=recorder)
    (record,) = (r for r in records(files) if r["step"] == "ragas")
    expected = {
        files[k].name
        for k in (
            "answers_file",
            "results_file",
            "questions_file",
            "ground_truth_file",
            "scores_file",
        )
    } | {f.name for f in files["chunk_files"].values()}
    assert set(record["inputs_sha256"]) == expected
    assert record["outputs_sha256"] == {"ragas_scores.csv": sha256_of(files["out_file"])}
    assert record["strategy"] == "C1,C2,C3"
    assert record["model_reported"] == "gpt-6-sol-x"
    assert record["judge_cost_usd"] == pytest.approx((1000 * 2.0 + 200 * 10.0) / 1e6)
    assert record["ragas_version"]
    assert record["date"]


def test_record_has_no_scores_input_on_a_set(files):
    go(files, main=False)
    (record,) = (r for r in records(files) if r["step"] == "ragas")
    assert files["scores_file"].name not in record["inputs_sha256"]


def test_repeat_only_for_pilot_sets_and_logged_apart(files):
    scorer = FakeScorer()
    with pytest.raises(RuntimeError, match="repeat"):
        go(files, scorer, repeat=True)
    assert scorer.calls == []
    files["runs_file"].unlink()
    assert go(files, main=False) == 6
    assert go(files, main=False, repeat=True, record=False) == 6
    assert files["repeat_file"].exists()
    assert latest_run(files["runs_file"], "ragas_repeat", EXPERIMENT)["outputs_sha256"] == {
        RAGAS_REPEAT_FILE_NAME: sha256_of(files["repeat_file"])
    }
    assert latest_run(files["runs_file"], "ragas", EXPERIMENT)["outputs_sha256"] == {
        "ragas_scores.csv": sha256_of(files["out_file"])
    }


def test_set_on_main_catalogue_gets_no_pilot_exception(files, monkeypatch, tmp_path):
    monkeypatch.setattr(freeze, "QUESTIONS_FILE", files["questions_file"])
    monkeypatch.setattr(freeze, "GROUND_TRUTH_FILE", files["ground_truth_file"])
    paths = set_paths(tmp_path)
    assert paths["questions_file"] == files["questions_file"]
    scorer = FakeScorer()
    record_upstream(files, summarise=False)  # no summarise, not frozen
    with pytest.raises(RuntimeError):
        run(scorer, ApiRecorder(), FakeCreated(), files, False)
    assert scorer.calls == []
    with pytest.raises(RuntimeError, match="repeat"):
        run(scorer, ApiRecorder(), FakeCreated(), files, False, repeat=True)


def test_validated_accepts_a_clean_sample():
    s = Sample("Q1", "C1", "q", "a", ("c",), "r")
    values = {m: (0.25, "") for m in RAGAS_METRICS}
    assert validated(s, values) == values
