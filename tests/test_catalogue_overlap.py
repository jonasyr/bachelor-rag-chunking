import pytest

from catalogue_overlap import OVERLAP_HEADER, overlap_section_ids, read_overlap


def write(path, rows):
    lines = [",".join(OVERLAP_HEADER)] + [",".join(r) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_missing_file_is_empty(tmp_path):
    assert read_overlap(tmp_path / "catalogue_overlap.csv") == {}


def test_rows_grouped_by_section(tmp_path):
    path = write(
        tmp_path / "o.csv",
        [("D001#a", "D002#b", "Both list the login commands."), ("D001#a", "D003#c", "Same flag.")],
    )
    assert read_overlap(path) == {
        "D001#a": [("D002#b", "Both list the login commands."), ("D003#c", "Same flag.")]
    }


def test_section_ids_cover_both_columns(tmp_path):
    path = write(tmp_path / "o.csv", [("D001#a", "D002#b", "Same flag.")])
    assert overlap_section_ids(read_overlap(path)) == {"D001#a", "D002#b"}


def test_self_reference_is_an_error(tmp_path):
    with pytest.raises(ValueError, match="itself"):
        read_overlap(write(tmp_path / "o.csv", [("D001#a", "D001#a", "Same.")]))


def test_duplicate_pair_is_an_error(tmp_path):
    rows = [("D001#a", "D002#b", "Same."), ("D001#a", "D002#b", "Again.")]
    with pytest.raises(ValueError, match="twice"):
        read_overlap(write(tmp_path / "o.csv", rows))


def test_empty_note_is_an_error(tmp_path):
    with pytest.raises(ValueError, match="note"):
        read_overlap(write(tmp_path / "o.csv", [("D001#a", "D002#b", " ")]))
