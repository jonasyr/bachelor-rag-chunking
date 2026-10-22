import csv
import json
from collections import Counter

import pytest
from conftest import valid_rows, write_catalogue, write_scoring_set

import freeze
import scoring_store
import second_rater
from atomic_csv import read_csv, write_csv
from config import QUESTION_CLASSES, RUBRIC_CRITERIA
from evaluate_answers import SHEET_HEADER
from run_log import append_step_run, latest_run, sha256_of


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


@pytest.fixture
def scaffolded(tmp_path):
    """A pilot set with items for H01 and H02, frozen key points and a draw of H01 only."""
    folder = tmp_path / "pilot_set"
    write_scoring_set(folder)
    p = second_rater.paths(folder)
    mine = scoring_store.ScoringSet(
        "own",
        p["items_file"],
        p["sheet_file"],
        p["scores_file"],
        p["key_points_file"],
        p["checks_file"],
        p["runs_file"],
    )
    items = scoring_store.load_items(mine)
    scoring_store.save_key_points(mine, items, "H01", ["Core one"])
    scoring_store.save_key_points(mine, items, "H02", ["Core two", "Second two"])
    scoring_store.freeze_key_points(mine, items)
    write_csv(
        p["sample_file"],
        second_rater.SAMPLE_HEADER,
        [{"question_id": "H01", "type": "factual", "difficulty": "hard"}],
    )
    append_step_run("second_rater_draw", "C1,C2,C3", [], [p["sample_file"]], p["runs_file"])
    return p


def test_export_writes_blind_subset(scaffolded):
    out = second_rater.run_export(scaffolded, pilot=False)
    names = {f.name for f in out.iterdir()}
    assert names == {"scoring_items.jsonl", "key_points.csv", "scoring_sheet.csv", "runs.jsonl"}
    original = scaffolded["items_file"].read_text(encoding="utf-8").splitlines(keepends=True)
    kept = (out / "scoring_items.jsonl").read_text(encoding="utf-8").splitlines(keepends=True)
    assert kept == [line for line in original if json.loads(line)["question_id"] == "H01"]
    rows = read_csv(out / "scoring_sheet.csv", SHEET_HEADER)
    assert [r["code"] for r in rows] == [json.loads(line)["code"] for line in kept]
    assert all(set(r) == set(SHEET_HEADER) and not r["correctness"] for r in rows)
    points = read_csv(out / "key_points.csv", ["question_id", "point", "text"])
    assert {r["question_id"] for r in points} == {"H01"}
    assert latest_run(scaffolded["runs_file"], "second_rater_export", "C1,C2,C3")


def test_export_set_is_frozen_for_the_app(scaffolded, monkeypatch):
    out = second_rater.run_export(scaffolded, pilot=False)
    monkeypatch.setattr(scoring_store, "PILOT_DIR", out.parent.parent)
    (r2,) = (s for s in scoring_store.scoring_sets() if s.rater)
    assert scoring_store.is_frozen(r2)
    scoring_store.require_frozen_key_points(r2)


def test_export_refuses_without_frozen_key_points(scaffolded):
    scaffolded["key_points_file"].write_text("question_id,point,text\nH01,1,changed\n")
    with pytest.raises(RuntimeError, match="frozen"):
        second_rater.run_export(scaffolded, pilot=False)


def test_export_refuses_changed_sample(scaffolded):
    with scaffolded["sample_file"].open("a", encoding="utf-8") as f:
        f.write("H02,factual,hard\n")
    with pytest.raises(RuntimeError, match="differs"):
        second_rater.run_export(scaffolded, pilot=False)


def test_export_refuses_without_draw(scaffolded):
    scaffolded["sample_file"].unlink()
    with pytest.raises(RuntimeError, match="draw"):
        second_rater.run_export(scaffolded, pilot=False)


def test_export_refuses_when_scores_exist_main(scaffolded, capsys):
    scaffolded["scores_file"].write_text("question_id,strategy\n")
    with pytest.raises(RuntimeError, match="unblinded"):
        second_rater.run_export(scaffolded, pilot=False)
    assert not scaffolded["dir"].exists()
    out = second_rater.run_export(scaffolded, pilot=True)
    assert out.exists()
    assert "warning" in capsys.readouterr().err.lower()


def test_export_refuses_existing_values(scaffolded):
    out = second_rater.run_export(scaffolded, pilot=False)
    rows = read_csv(out / "scoring_sheet.csv", SHEET_HEADER)
    rows[0]["correctness"] = "2"
    write_csv(out / "scoring_sheet.csv", SHEET_HEADER, rows)
    with pytest.raises(FileExistsError):
        second_rater.run_export(scaffolded, pilot=False)
    assert read_csv(out / "scoring_sheet.csv", SHEET_HEADER)[0]["correctness"] == "2"


def test_export_refuses_incomplete_question(scaffolded):
    lines = scaffolded["items_file"].read_text(encoding="utf-8").splitlines(keepends=True)
    drop = next(line for line in lines if json.loads(line)["question_id"] == "H01")
    scaffolded["items_file"].write_text("".join(x for x in lines if x != drop), encoding="utf-8")
    with pytest.raises(RuntimeError):
        second_rater.run_export(scaffolded, pilot=False)


def test_cli_export_with_set_reaches_run_export(set_dir, monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr(
        second_rater, "run_export", lambda p, pilot: seen.update(p=p, pilot=pilot) or set_dir
    )
    second_rater.main(["--mode", "export", "--set", str(set_dir)])
    assert seen["pilot"] is True and seen["p"]["dir"] == set_dir / "second_rater"
    assert "R2 set" in capsys.readouterr().out


def test_cli_draw_with_set_needs_questions(set_dir):
    with pytest.raises(SystemExit):
        second_rater.main(["--mode", "draw", "--set", str(set_dir)])
    second_rater.main(["--mode", "draw", "--set", str(set_dir), "--questions", "8"])
    assert (set_dir / "second_rater_sample.csv").exists()


@pytest.mark.parametrize("mode", ["export", "close"])
def test_cli_questions_only_for_draw(set_dir, mode):
    with pytest.raises(SystemExit):
        second_rater.main(["--mode", mode, "--set", str(set_dir), "--questions", "8"])


GOOD = {
    "points": ["covered"],
    "declines": "no",
    "core_wrong": "no",
    "other_error": "no",
    "grounded": "all",
    "hallucination": "none",
    "answers_question": "yes",
    "direct": "yes",
    "wordy": "no",
}


@pytest.fixture
def exported(scaffolded):
    out = second_rater.run_export(scaffolded, pilot=False)
    return scaffolded, scoring_store._rater_set("Second rater", out)


def score_all(r2, skip=()):
    for code in (i["code"] for i in scoring_store.load_items(r2)):
        if code not in skip:
            scoring_store.save_score(r2, code, GOOD, "")


def test_close_refuses_incomplete(exported):
    p, r2 = exported
    score_all(r2, skip=("H01-C",))
    with pytest.raises(ValueError, match="H01-C"):
        second_rater.run_close(p)
    assert latest_run(r2.runs_file, "second_rater_close", "C1,C2,C3") is None


def test_close_refuses_hand_edited_score(exported):
    p, r2 = exported
    score_all(r2)
    rows = read_csv(r2.sheet_file, SHEET_HEADER)
    rows[0]["correctness"] = "0"
    write_csv(r2.sheet_file, SHEET_HEADER, rows)
    with pytest.raises(ValueError, match="correctness"):
        second_rater.run_close(p)


def test_close_refuses_changed_items(exported):
    p, r2 = exported
    score_all(r2)
    with r2.items_file.open("a", encoding="utf-8") as f:
        f.write("\n")
    with pytest.raises(RuntimeError, match="differs"):
        second_rater.run_close(p)


def test_close_writes_record_and_locks(exported):
    p, r2 = exported
    score_all(r2)
    assert not scoring_store.is_read_only(r2)
    record = second_rater.run_close(p)
    assert record["rater"] == "R2" and record["rules_version"]
    assert not {"name", "rater_name", "email"} & set(record)
    assert record["outputs_sha256"] == {
        "scoring_checks.csv": sha256_of(r2.checks_file),
        "scoring_sheet.csv": sha256_of(r2.sheet_file),
    }
    assert set(record["inputs_sha256"]) == {"scoring_items.jsonl", "key_points.csv"}
    assert latest_run(r2.runs_file, "second_rater_close", "C1,C2,C3") == record
    assert scoring_store.is_read_only(r2)


def test_save_score_refused_after_close(exported):
    p, r2 = exported
    score_all(r2)
    second_rater.run_close(p)
    with pytest.raises(PermissionError, match="closed"):
        scoring_store.save_score(r2, "H01-A", GOOD, "")


def test_close_twice_refused(exported):
    p, r2 = exported
    score_all(r2)
    second_rater.run_close(p)
    with pytest.raises(RuntimeError, match="closed already"):
        second_rater.run_close(p)


def test_export_never_rewrites_a_closed_set(exported):
    p, r2 = exported
    score_all(r2)
    second_rater.run_close(p)
    with pytest.raises(FileExistsError):
        second_rater.run_export(p, pilot=True)


def test_export_refuses_stray_scores_file(exported):
    p, r2 = exported
    r2.scores_file.write_text("question_id,strategy\n", encoding="utf-8")
    with pytest.raises(FileExistsError):
        second_rater.run_export(p, pilot=True)


def test_cli_close_with_set(exported):
    p, r2 = exported
    score_all(r2)
    second_rater.main(["--mode", "close", "--set", str(p["sample_file"].parent)])
    assert scoring_store.is_read_only(r2)
