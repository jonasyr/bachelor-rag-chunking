import csv
import json
from collections import Counter

import pytest
from conftest import valid_rows, write_catalogue

import freeze
import second_rater
from atomic_csv import read_csv
from config import QUESTION_CLASSES, RUBRIC_CRITERIA
from run_log import latest_run, sha256_of


@pytest.fixture
def catalogue48():
    return [
        {"question_id": qid, "type": qtype, "difficulty": cls}
        for qid, _, qtype, cls, _, _ in valid_rows()
    ]


@pytest.fixture
def set_dir(tmp_path):
    """A pilot-style set with a full 48-question catalogue."""
    folder = tmp_path / "set"
    folder.mkdir()
    write_catalogue(folder, valid_rows())
    return folder


def write_sheet(folder, value=""):
    path = folder / "scoring_sheet.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["code", "question_id", *RUBRIC_CRITERIA, "notes"])
        w.writerow(["Q001-A", "Q001", value, *[""] * (len(RUBRIC_CRITERIA) - 1), ""])
    return path


def test_main_targets_meet_catalogue_quotas(catalogue48):
    rows = second_rater.draw(catalogue48, 12, 20261022)
    types = Counter(r["type"] for r in rows)
    classes = Counter(r["difficulty"] for r in rows)
    assert all(classes[c] == 3 for c in QUESTION_CLASSES)
    assert types["factual"] == types["procedural"] == types["conceptual"] == 3
    assert sorted([types["comparative"], types["limitation"]]) == [1, 2]
    assert [r["question_id"] for r in rows] == sorted(r["question_id"] for r in rows)
    assert list(rows[0]) == second_rater.SAMPLE_HEADER


def test_draw_is_deterministic(catalogue48):
    assert second_rater.draw(catalogue48, 12, 1) == second_rater.draw(catalogue48, 12, 1)


def test_targets_largest_remainder_ties_by_seed():
    import random

    counts = {"a": 6, "b": 6}
    picks = {
        tuple(sorted(second_rater.targets(counts, 3, random.Random(s)).items())) for s in range(20)
    }
    assert picks == {(("a", 2), ("b", 1)), (("a", 1), ("b", 2))}
    assert sum(second_rater.targets({"x": 5, "y": 1, "z": 1}, 4, random.Random(0)).values()) == 4


def test_impossible_strata_abort(monkeypatch):
    monkeypatch.setattr(
        second_rater,
        "targets",
        lambda counts, n, rng: {k: n if k in ("A", "X") else 0 for k in counts},
    )
    monkeypatch.setattr(second_rater, "SECOND_RATER_MAX_DRAWS", 50)
    qs = [
        {"question_id": "Q1", "type": "A", "difficulty": "Y"},
        {"question_id": "Q2", "type": "B", "difficulty": "X"},
    ]
    with pytest.raises(ValueError, match="both strata"):
        second_rater.draw(qs, 1, 0)


def test_draw_more_than_catalogue_aborts(catalogue48):
    with pytest.raises(ValueError, match="only 48"):
        second_rater.draw(catalogue48, 49, 0)


def test_paths_pilot_and_main(set_dir):
    p = second_rater.paths(set_dir)
    assert p["sample_file"] == set_dir / "second_rater_sample.csv"
    assert p["dir"] == set_dir / "second_rater"
    assert p["runs_file"] == set_dir / "runs.jsonl"
    assert p["questions_file"] == set_dir / "questions.csv"
    main = second_rater.paths(None)
    assert main["sample_file"] == second_rater.SECOND_RATER_SAMPLE_FILE


def test_draw_writes_sample_and_records_run(set_dir):
    p = second_rater.paths(set_dir)
    rows = second_rater.run_draw(p, 8, pilot=True)
    assert read_csv(p["sample_file"], second_rater.SAMPLE_HEADER) == rows
    assert len(rows) == 8
    record = latest_run(p["runs_file"], "second_rater_draw", "C1,C2,C3")
    assert record["seed"] == second_rater.SECOND_RATER_SEED
    assert record["questions"] == 8
    assert record["outputs_sha256"] == {"second_rater_sample.csv": sha256_of(p["sample_file"])}
    assert record["inputs_sha256"] == {"questions.csv": sha256_of(p["questions_file"])}


def test_draw_never_overwrites(set_dir):
    p = second_rater.paths(set_dir)
    second_rater.run_draw(p, 8, pilot=True)
    before = p["sample_file"].read_bytes()
    with pytest.raises(FileExistsError):
        second_rater.run_draw(p, 8, pilot=True)
    assert p["sample_file"].read_bytes() == before


def test_draw_refuses_unfrozen_main(set_dir, monkeypatch):
    p = second_rater.paths(set_dir) | {"freeze_file": set_dir / "catalogue_freeze.json"}
    monkeypatch.setattr(freeze, "QUESTIONS_FILE", p["questions_file"])
    with pytest.raises(RuntimeError, match="not frozen"):
        second_rater.run_draw(p, 12, pilot=False)
    assert not p["sample_file"].exists()


def test_draw_refuses_when_own_values_exist_main(set_dir):
    p = second_rater.paths(set_dir)
    write_sheet(set_dir, "1")
    with pytest.raises(RuntimeError, match="own"):
        second_rater.run_draw(p, 12, pilot=False)
    assert not p["sample_file"].exists()


def test_draw_refuses_when_checks_exist_main(set_dir):
    p = second_rater.paths(set_dir)
    (set_dir / "scoring_checks.csv").write_text("code,rules_version\nQ001-A,1\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="own"):
        second_rater.run_draw(p, 12, pilot=False)


def test_empty_sheet_is_no_values(set_dir):
    p = second_rater.paths(set_dir)
    write_sheet(set_dir, "")
    assert len(second_rater.run_draw(p, 12, pilot=False)) == 12


def test_draw_only_warns_for_pilot(set_dir, capsys):
    p = second_rater.paths(set_dir)
    write_sheet(set_dir, "1")
    second_rater.run_draw(p, 8, pilot=True)
    assert p["sample_file"].exists()
    assert "warning" in capsys.readouterr().err.lower()


def test_draw_run_record_is_json_line(set_dir):
    p = second_rater.paths(set_dir)
    second_rater.run_draw(p, 8, pilot=True)
    lines = p["runs_file"].read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[-1])["step"] == "second_rater_draw"
