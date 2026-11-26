import csv
from collections import Counter

import pytest
from conftest import valid_rows, write_catalogue

import freeze
import hybrid
import second_rater
from atomic_csv import read_csv
from config import QUESTION_CLASSES, RUBRIC_CRITERIA
from run_log import latest_run, sha256_of


@pytest.fixture
def set_dir(tmp_path):
    """A pilot-style set with a full 48-question catalogue and a 12-question R2 draw."""
    folder = tmp_path / "set"
    folder.mkdir()
    write_catalogue(folder, valid_rows())
    second_rater.run_draw(second_rater.paths(folder), 12, pilot=True)
    return folder


def sample_ids(p):
    return {r["question_id"] for r in read_csv(p["sample_file"], second_rater.SAMPLE_HEADER)}


def write_sheet(folder, rows):
    """A scoring sheet with one row per (code, value) pair."""
    with (folder / "scoring_sheet.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["code", "question_id", *RUBRIC_CRITERIA, "notes"])
        for code, value in rows:
            w.writerow([code, code[:4], value, *[""] * (len(RUBRIC_CRITERIA) - 1), ""])


def test_paths_add_the_extra_sample(set_dir):
    assert hybrid.paths(set_dir)["extra_file"] == set_dir / hybrid.HYBRID_EXTRA_SAMPLE_FILE.name
    assert hybrid.paths(None)["extra_file"] == hybrid.HYBRID_EXTRA_SAMPLE_FILE


def test_extra_draw_comes_from_the_rest_and_records_the_run(set_dir):
    p = hybrid.paths(set_dir)
    rows = hybrid.run_draw(p, 12, pilot=False)
    assert len(rows) == 12
    assert not {r["question_id"] for r in rows} & sample_ids(p)
    assert read_csv(p["extra_file"], second_rater.SAMPLE_HEADER) == rows
    record = latest_run(p["runs_file"], hybrid.DRAW_STEP, "C1,C2,C3")
    assert record is not None
    assert record["seed"] == hybrid.HYBRID_SEED
    assert record["questions"] == 12
    assert record["inputs_sha256"] == {
        "questions.csv": sha256_of(p["questions_file"]),
        "second_rater_sample.csv": sha256_of(p["sample_file"]),
    }
    assert record["outputs_sha256"] == {p["extra_file"].name: sha256_of(p["extra_file"])}


def test_both_draws_together_mirror_the_catalogue(set_dir):
    p = hybrid.paths(set_dir)
    rows = hybrid.run_draw(p, 12, pilot=False)
    first = read_csv(p["sample_file"], second_rater.SAMPLE_HEADER)
    both = first + rows
    catalogue = Counter(t for _, _, t, _, _, _ in valid_rows())
    assert Counter(r["type"] for r in both) == Counter({k: v // 2 for k, v in catalogue.items()})
    assert all(Counter(r["difficulty"] for r in both)[c] == 6 for c in QUESTION_CLASSES)


def test_extra_draw_is_deterministic(set_dir, tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    write_catalogue(other, valid_rows())
    second_rater.run_draw(second_rater.paths(other), 12, pilot=True)
    assert hybrid.run_draw(hybrid.paths(set_dir), 12, pilot=False) == hybrid.run_draw(
        hybrid.paths(other), 12, pilot=False
    )


def test_extra_draw_never_overwrites(set_dir):
    p = hybrid.paths(set_dir)
    hybrid.run_draw(p, 12, pilot=False)
    before = p["extra_file"].read_bytes()
    with pytest.raises(FileExistsError):
        hybrid.run_draw(p, 12, pilot=False)
    assert p["extra_file"].read_bytes() == before


def test_extra_draw_needs_the_first_draw(tmp_path):
    folder = tmp_path / "set"
    folder.mkdir()
    write_catalogue(folder, valid_rows())
    with pytest.raises(RuntimeError, match="second_rater_draw"):
        hybrid.run_draw(hybrid.paths(folder), 12, pilot=False)


def test_extra_draw_refuses_a_changed_first_sample(set_dir):
    p = hybrid.paths(set_dir)
    p["sample_file"].write_text(
        p["sample_file"].read_text(encoding="utf-8") + "Q048,procedural,multi-section\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="second_rater_sample.csv differs"):
        hybrid.run_draw(p, 12, pilot=False)
    assert not p["extra_file"].exists()


def test_extra_draw_refuses_an_unfrozen_main(set_dir, monkeypatch):
    p = hybrid.paths(set_dir) | {"freeze_file": set_dir / "catalogue_freeze.json"}
    monkeypatch.setattr(freeze, "QUESTIONS_FILE", p["questions_file"])
    with pytest.raises(RuntimeError, match="not frozen"):
        hybrid.run_draw(p, 12, pilot=False)
    assert not p["extra_file"].exists()


def test_values_on_the_first_sample_are_allowed(set_dir):
    p = hybrid.paths(set_dir)
    qid = sorted(sample_ids(p))[0]
    write_sheet(set_dir, [(f"{qid}-A", "2")])
    (set_dir / "scoring_checks.csv").write_text(
        f"code,rules_version\n{qid}-A,2026-10-20\n", encoding="utf-8"
    )
    assert len(hybrid.run_draw(p, 12, pilot=False)) == 12


def test_values_outside_the_first_sample_abort_main(set_dir):
    p = hybrid.paths(set_dir)
    qid = next(r[0] for r in valid_rows() if r[0] not in sample_ids(p))
    write_sheet(set_dir, [(f"{qid}-B", "1")])
    with pytest.raises(RuntimeError, match=qid):
        hybrid.run_draw(p, 12, pilot=False)
    assert not p["extra_file"].exists()


def test_checks_outside_the_first_sample_abort_main(set_dir):
    p = hybrid.paths(set_dir)
    qid = next(r[0] for r in valid_rows() if r[0] not in sample_ids(p))
    (set_dir / "scoring_checks.csv").write_text(
        f"code,rules_version\n{qid}-C,2026-10-20\n", encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match=qid):
        hybrid.run_draw(p, 12, pilot=False)


def test_values_outside_the_first_sample_only_warn_for_pilot(set_dir, capsys):
    p = hybrid.paths(set_dir)
    qid = next(r[0] for r in valid_rows() if r[0] not in sample_ids(p))
    write_sheet(set_dir, [(f"{qid}-A", "1")])
    hybrid.run_draw(p, 12, pilot=True)
    assert p["extra_file"].exists()
    assert "warning" in capsys.readouterr().err.lower()


def test_human_questions_is_the_union_of_both_draws(set_dir):
    p = hybrid.paths(set_dir)
    rows = hybrid.run_draw(p, 12, pilot=False)
    assert hybrid.human_questions(p) == sample_ids(p) | {r["question_id"] for r in rows}


def test_cli_draws_the_configured_number(set_dir):
    hybrid.main(["--mode", "draw", "--set", str(set_dir)])
    rows = read_csv(hybrid.paths(set_dir)["extra_file"], second_rater.SAMPLE_HEADER)
    assert len(rows) == hybrid.HYBRID_EXTRA_QUESTIONS
