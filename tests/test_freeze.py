import json

import pytest
from conftest import valid_rows, write_catalogue

import freeze
from catalogue import freeze_catalogue
from run_log import sha256_of


@pytest.fixture
def main_catalogue(tmp_path, monkeypatch):
    questions, truth = write_catalogue(tmp_path, valid_rows())
    monkeypatch.setattr(freeze, "QUESTIONS_FILE", questions)
    monkeypatch.setattr(freeze, "GROUND_TRUTH_FILE", truth)
    return questions, truth


def test_freeze_writes_hashes_counts_and_date(corpus, main_catalogue, pilot, tmp_path):
    questions, truth = main_catalogue
    out = tmp_path / "catalogue_freeze.json"
    record = freeze_catalogue(corpus, questions, truth, out, pilot)
    stored = json.loads(out.read_text(encoding="utf-8"))
    assert stored == record
    assert stored["sha256"] == {
        "questions.csv": sha256_of(questions),
        "ground_truth.csv": sha256_of(truth),
    }
    assert stored["questions"] == 48 and stored["types"]["comparative"] == 6
    assert set(stored) == {"date", "questions", "types", "classes", "sha256"}


def test_freeze_refuses_a_failing_catalogue_and_writes_nothing(corpus, tmp_path, pilot):
    questions, truth = write_catalogue(tmp_path, valid_rows()[:47])
    out = tmp_path / "catalogue_freeze.json"
    with pytest.raises(ValueError, match="strict check"):
        freeze_catalogue(corpus, questions, truth, out, pilot)
    assert not out.exists()


def test_freeze_never_overwrites_a_record(corpus, main_catalogue, pilot, tmp_path):
    questions, truth = main_catalogue
    out = tmp_path / "catalogue_freeze.json"
    freeze_catalogue(corpus, questions, truth, out, pilot)
    before = out.read_bytes()
    with pytest.raises(FileExistsError, match="ADR 0030"):
        freeze_catalogue(corpus, questions, truth, out, pilot)
    assert out.read_bytes() == before


def test_require_frozen_ignores_other_catalogues(tmp_path):
    other_q, other_t = tmp_path / "q.csv", tmp_path / "t.csv"
    freeze.require_frozen(other_q, other_t, tmp_path / "missing.json")  # no error, no file read


def test_require_frozen_refuses_missing_record(main_catalogue, tmp_path):
    questions, truth = main_catalogue
    with pytest.raises(RuntimeError, match="not frozen"):
        freeze.require_frozen(questions, truth, tmp_path / "missing.json")


def test_require_frozen_refuses_changed_file(main_catalogue, tmp_path):
    questions, truth = main_catalogue
    out = tmp_path / "freeze.json"
    freeze.write_freeze(questions, truth, out)
    truth.write_text(truth.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="ground_truth.csv changed since the freeze"):
        freeze.require_frozen(questions, truth, out)


def test_require_frozen_refuses_mixed_paths(main_catalogue, tmp_path):
    questions, truth = main_catalogue
    out = tmp_path / "freeze.json"
    freeze.write_freeze(questions, truth, out)
    other_truth = tmp_path / "other" / "ground_truth.csv"
    other_truth.parent.mkdir()
    other_truth.write_text("question_id,expected_answer,relevant_doc_ids,relevant_section_ids\n")
    with pytest.raises(RuntimeError, match="changed since the freeze"):
        freeze.require_frozen(questions, other_truth, out)
