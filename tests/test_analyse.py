import json

from test_analysis_data import paths  # noqa: F401 (fixture)

import analyse


def test_set_run_writes_into_the_set(paths, monkeypatch, tmp_path):  # noqa: F811
    monkeypatch.setattr(analyse.analysis_data, "set_paths", lambda set_dir: paths)
    assert analyse.main(["--set", str(tmp_path)]) == 0
    out = tmp_path / "output"
    assert (out / "analysis.json").exists()
    assert (out / "tables" / "retrieval.tex").exists()
    assert (out / "figures" / "recall.pdf").exists()


def test_set_without_optional_inputs_skips_parts(paths, monkeypatch, tmp_path):  # noqa: F811
    monkeypatch.setattr(analyse.analysis_data, "set_paths", lambda set_dir: paths)
    analyse.main(["--set", str(tmp_path)])
    notes = json.loads((tmp_path / "output" / "analysis.json").read_text(encoding="utf-8"))["notes"]
    assert any("closed-book" in n for n in notes)
    assert any("Chunk" in n for n in notes)
    assert not (tmp_path / "output" / "figures" / "chunk_lengths.pdf").exists()
