import json

import pytest
from conftest import valid_rows, write_catalogue

import freeze
from catalogue import freeze_catalogue
from run_log import sha256_of


@pytest.fixture
def main_catalogue(tmp_path, monkeypatch, corpus_files):
    questions, truth = write_catalogue(tmp_path, valid_rows())
    monkeypatch.setattr(freeze, "QUESTIONS_FILE", questions)
    monkeypatch.setattr(freeze, "GROUND_TRUTH_FILE", truth)
    return questions, truth, corpus_files[1], corpus_files[0]


def test_freeze_writes_hashes_counts_and_date(corpus, main_catalogue, pilot, tmp_path):
    questions, truth, sections, documents = main_catalogue
    out = tmp_path / "catalogue_freeze.json"
    record = freeze_catalogue(corpus, questions, truth, out, pilot, sections, documents)
    stored = json.loads(out.read_text(encoding="utf-8"))
    assert stored == record
    assert stored["sha256"] == {
        "questions.csv": sha256_of(questions),
        "ground_truth.csv": sha256_of(truth),
        "sections.jsonl": sha256_of(sections),
        "documents.jsonl": sha256_of(documents),
    }
    assert stored["questions"] == 48 and stored["types"]["comparative"] == 6
    assert set(stored) == {"date", "questions", "types", "classes", "sha256"}


def test_freeze_refuses_a_failing_catalogue_and_writes_nothing(
    corpus, corpus_files, tmp_path, pilot
):
    questions, truth = write_catalogue(tmp_path, valid_rows()[:47])
    out = tmp_path / "catalogue_freeze.json"
    with pytest.raises(ValueError, match="strict check"):
        freeze_catalogue(corpus, questions, truth, out, pilot, corpus_files[1], corpus_files[0])
    assert not out.exists()


def test_freeze_never_overwrites_a_record(corpus, main_catalogue, pilot, tmp_path):
    questions, truth, sections, documents = main_catalogue
    out = tmp_path / "catalogue_freeze.json"
    freeze_catalogue(corpus, questions, truth, out, pilot, sections, documents)
    before = out.read_bytes()
    with pytest.raises(FileExistsError, match="ADR 0030"):
        freeze_catalogue(corpus, questions, truth, out, pilot, sections, documents)
    with pytest.raises(FileExistsError, match="ADR 0030"):
        freeze.write_freeze(questions, truth, sections, documents, out)
    assert out.read_bytes() == before


def test_require_frozen_ignores_other_catalogues(tmp_path):
    q, t, s, d = (tmp_path / n for n in ("q.csv", "t.csv", "s.jsonl", "d.jsonl"))
    freeze.require_frozen(q, t, s, d, tmp_path / "missing.json")  # no error, no file read


def test_require_frozen_refuses_missing_record(main_catalogue, tmp_path):
    questions, truth, sections, documents = main_catalogue
    with pytest.raises(RuntimeError, match="not frozen"):
        freeze.require_frozen(questions, truth, sections, documents, tmp_path / "missing.json")


def test_require_frozen_accepts_the_frozen_files(main_catalogue, tmp_path):
    questions, truth, sections, documents = main_catalogue
    out = tmp_path / "freeze.json"
    freeze.write_freeze(questions, truth, sections, documents, out)
    freeze.require_frozen(questions, truth, sections, documents, out)


def test_require_frozen_refuses_changed_file(main_catalogue, tmp_path):
    questions, truth, sections, documents = main_catalogue
    out = tmp_path / "freeze.json"
    freeze.write_freeze(questions, truth, sections, documents, out)
    truth.write_text(truth.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="ground_truth.csv changed since the freeze"):
        freeze.require_frozen(questions, truth, sections, documents, out)


def test_require_frozen_refuses_a_changed_corpus(main_catalogue, tmp_path):
    questions, truth, sections, documents = main_catalogue
    out = tmp_path / "freeze.json"
    freeze.write_freeze(questions, truth, sections, documents, out)
    sections.write_text(sections.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="sections.jsonl changed since the freeze"):
        freeze.require_frozen(questions, truth, sections, documents, out)


def test_require_frozen_refuses_mixed_paths(main_catalogue, tmp_path):
    questions, truth, sections, documents = main_catalogue
    out = tmp_path / "freeze.json"
    freeze.write_freeze(questions, truth, sections, documents, out)
    other_truth = tmp_path / "other" / "ground_truth.csv"
    other_truth.parent.mkdir()
    other_truth.write_text("question_id,expected_answer,relevant_doc_ids,relevant_section_ids\n")
    with pytest.raises(RuntimeError, match="changed since the freeze"):
        freeze.require_frozen(questions, other_truth, sections, documents, out)


@pytest.mark.parametrize("content", ["not json", "{}", '{"date": "2026-11-09", "sha256": []}'])
def test_require_frozen_names_a_malformed_record(main_catalogue, tmp_path, content):
    questions, truth, sections, documents = main_catalogue
    out = tmp_path / "freeze.json"
    out.write_text(content, encoding="utf-8")
    with pytest.raises(RuntimeError, match="malformed freeze record"):
        freeze.require_frozen(questions, truth, sections, documents, out)


def test_require_frozen_refuses_changed_document_text(main_catalogue, tmp_path):
    questions, truth, sections, documents = main_catalogue
    out = tmp_path / "freeze.json"
    freeze.write_freeze(questions, truth, sections, documents, out)
    documents.write_text(documents.read_text(encoding="utf-8").replace("Takes", "Gets"))
    with pytest.raises(RuntimeError, match="documents.jsonl changed since the freeze"):
        freeze.require_frozen(questions, truth, sections, documents, out)
