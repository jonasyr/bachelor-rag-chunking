import json

from test_analysis_data import llm, paths, repeat, second  # noqa: F401 (fixtures)

import analyse


def test_set_run_writes_into_the_set(paths, monkeypatch, tmp_path):  # noqa: F811 (fixture)
    monkeypatch.setattr(analyse.analysis_data, "set_paths", lambda set_dir: paths)
    assert analyse.main(["--set", str(tmp_path)]) == 0
    out = tmp_path / "output"
    assert (out / "analysis.json").exists()
    assert (out / "tables" / "retrieval.tex").exists()
    assert (out / "figures" / "recall.pdf").exists()


def test_set_without_optional_inputs_skips_parts(paths, monkeypatch, tmp_path):  # noqa: F811 (fixture)
    monkeypatch.setattr(analyse.analysis_data, "set_paths", lambda set_dir: paths)
    analyse.main(["--set", str(tmp_path)])
    notes = json.loads((tmp_path / "output" / "analysis.json").read_text(encoding="utf-8"))["notes"]
    assert any("closed-book" in n for n in notes)
    assert any("Chunk" in n for n in notes)
    assert not (tmp_path / "output" / "figures" / "chunk_lengths.pdf").exists()


def test_run_writes_disagreements_when_second_rating_present(second, monkeypatch, tmp_path):  # noqa: F811 (fixture)
    import agreement

    monkeypatch.setattr(agreement, "AGREEMENT_BOOTSTRAP_REPS", 50)
    monkeypatch.setattr(analyse.analysis_data, "set_paths", lambda set_dir: second)
    analyse.main(["--set", str(tmp_path)])
    out = tmp_path / "output"
    assert (out / "tables" / "agreement.tex").exists()
    lines = (out / "second_rater_disagreements.csv").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "code,question_id,field,first,second"
    assert any(",direct,yes,no" in line for line in lines)


def test_run_without_second_rating_writes_no_disagreements(paths, monkeypatch, tmp_path):  # noqa: F811 (fixture)
    monkeypatch.setattr(analyse.analysis_data, "set_paths", lambda set_dir: paths)
    analyse.main(["--set", str(tmp_path)])
    assert not (tmp_path / "output" / "second_rater_disagreements.csv").exists()
    assert not (tmp_path / "output" / "tables" / "agreement.tex").exists()


def test_run_without_second_rating_removes_stale_disagreements(paths, monkeypatch, tmp_path):  # noqa: F811 (fixture)
    monkeypatch.setattr(analyse.analysis_data, "set_paths", lambda set_dir: paths)
    stale = tmp_path / "output" / "second_rater_disagreements.csv"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale", encoding="utf-8")
    analyse.main(["--set", str(tmp_path)])
    assert not stale.exists()


def test_set_output_folder_name_comes_from_config(paths, monkeypatch, tmp_path):  # noqa: F811 (fixture)
    root = tmp_path / "elsewhere" / "results"
    monkeypatch.setattr(analyse, "OUTPUT_DIR", root)
    monkeypatch.setattr(analyse, "TABLES_DIR", root / "tables")
    monkeypatch.setattr(analyse, "FIGURES_DIR", root / "figures")
    monkeypatch.setattr(analyse, "ANALYSIS_FILE", root / "analysis.json")
    monkeypatch.setattr(analyse.analysis_data, "set_paths", lambda set_dir: paths)
    analyse.main(["--set", str(tmp_path)])
    assert (tmp_path / "results" / "analysis.json").exists()


def test_run_writes_intra_outputs_and_removes_them_again(repeat, monkeypatch, tmp_path):  # noqa: F811 (fixture)
    import agreement

    monkeypatch.setattr(agreement, "AGREEMENT_BOOTSTRAP_REPS", 50)
    monkeypatch.setattr(analyse.analysis_data, "set_paths", lambda set_dir: repeat)
    analyse.main(["--set", str(tmp_path)])
    out = tmp_path / "output"
    assert (out / "tables" / "agreement_intra.tex").exists()
    lines = (out / "intra_rater_disagreements.csv").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "code,question_id,field,first,second"
    assert any(",direct,yes,no" in line for line in lines)
    assert (out / "tables" / "agreement.tex").exists()  # the R2 path is untouched
    repeat["intra_rater_dir"].joinpath("runs.jsonl").unlink()  # not closed any more
    analyse.main(["--set", str(tmp_path)])
    assert not (out / "intra_rater_disagreements.csv").exists()
    assert not (out / "tables" / "agreement_intra.tex").exists()
    notes = json.loads((out / "analysis.json").read_text(encoding="utf-8"))["notes"]
    assert any("Wiederholungsbewertung fehlt" in n for n in notes)


def test_only_some_sources_present(llm, repeat, monkeypatch, tmp_path):  # noqa: F811 (fixtures)
    """None / only LLM / only repeat / both: only the matching outputs, a note for each missing
    source, and no stale file of an earlier run."""
    import agreement

    monkeypatch.setattr(agreement, "AGREEMENT_BOOTSTRAP_REPS", 50)
    monkeypatch.setattr(analyse.analysis_data, "set_paths", lambda set_dir: both)
    both = llm | {"intra_rater_dir": repeat["intra_rater_dir"]}
    out = tmp_path / "output"
    intra = ("agreement_intra.tex", "intra_rater_disagreements.csv")
    llm_files = ("agreement_llm.tex", "llm_rater_disagreements.csv")

    def produced() -> set[str]:
        return {
            n for n in (*intra, *llm_files) if (out / n).exists() or (out / "tables" / n).exists()
        }

    def notes() -> list[str]:
        return json.loads((out / "analysis.json").read_text(encoding="utf-8"))["notes"]

    analyse.main(["--set", str(tmp_path)])  # both
    assert produced() == {*intra, *llm_files}
    assert not any("fehlt" in n and ("LLM" in n or "Wiederholung" in n) for n in notes())

    intra_dir = both["intra_rater_dir"]
    (intra_dir / "runs.jsonl").rename(intra_dir / "runs.off")  # only LLM
    analyse.main(["--set", str(tmp_path)])
    assert produced() == set(llm_files)
    assert any("Wiederholungsbewertung fehlt" in n for n in notes())

    (intra_dir / "runs.off").rename(intra_dir / "runs.jsonl")  # only repeat
    runs = both["generation_runs_file"]
    with_llm = runs.read_text(encoding="utf-8")
    runs.write_text(
        "".join(x + "\n" for x in with_llm.splitlines() if '"llm_rater"' not in x),
        encoding="utf-8",
    )  # no run record of the cross-check
    analyse.main(["--set", str(tmp_path)])
    assert produced() == set(intra)
    assert any("LLM-Gegenprobe fehlt" in n for n in notes())

    both["intra_rater_dir"] = intra_dir / "gone"  # none
    analyse.main(["--set", str(tmp_path)])
    assert produced() == set()
    assert any("LLM-Gegenprobe fehlt" in n for n in notes())
    assert any("Wiederholungsbewertung fehlt" in n for n in notes())
