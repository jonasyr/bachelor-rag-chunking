import json

import pytest

from run_log import append_step_run, require_run, sha256_of


def test_append_step_run_records_hashes(tmp_path):
    a, b = tmp_path / "in.csv", tmp_path / "out.csv"
    a.write_text("x\n", encoding="utf-8")
    b.write_text("y\n", encoding="utf-8")
    runs = tmp_path / "runs.jsonl"
    record = append_step_run("summarise", "C1,C2,C3", [a], [b], runs)
    assert record["step"] == "summarise" and record["strategy"] == "C1,C2,C3"
    assert record["inputs_sha256"] == {"in.csv": sha256_of(a)}
    assert record["outputs_sha256"] == {"out.csv": sha256_of(b)}
    assert json.loads(runs.read_text(encoding="utf-8")) == record


@pytest.mark.parametrize(
    ("step", "strategy", "command"),
    [
        ("summarise", "C1,C2,C3", "src/evaluate_answers.py --mode summarise"),
        ("summarise_control", "K0", "src/evaluate_answers.py --mode summarise --control"),
        ("evaluate_retrieval", "K1", "src/evaluate_retrieval.py --control"),
        ("generate", "C1,C2,C3", "src/generate.py"),
    ],
)
def test_missing_run_names_the_real_command(tmp_path, step, strategy, command):
    runs = tmp_path / "runs.jsonl"
    runs.write_text("", encoding="utf-8")
    with pytest.raises(RuntimeError) as error:
        require_run(runs, step, strategy, [], [])
    assert f"run {command}" in str(error.value)


def test_step_command_names_the_ragas_runs():
    from run_log import step_command

    assert step_command("ragas", "C1,C2,C3") == "src/ragas_eval.py"
    assert step_command("ragas_repeat", "C1,C2,C3") == "src/ragas_eval.py --repeat"
