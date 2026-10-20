import json

from run_log import append_step_run, sha256_of


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
