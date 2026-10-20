from test_report_tables import make_data

from report_figures import FIGURE_NAMES, write_figures
from report_tables import build_results


def _run(tmp_path, **kw):
    data = make_data(**kw)
    results = build_results(data, 0.05)
    return write_figures(data, results, tmp_path), results


def test_all_figures_written(tmp_path):
    paths, _ = _run(tmp_path)
    assert sorted(p.name for p in paths) == sorted(FIGURE_NAMES)
    for p in paths:
        assert p.read_bytes().startswith(b"%PDF")


def test_figures_are_byte_identical_on_rerun(tmp_path):
    outs = []
    for run in ("a", "b"):
        paths, _ = _run(tmp_path / run)
        outs.append({p.name: p.read_bytes() for p in paths})
    assert outs[0] == outs[1]


def test_missing_chunks_skips_histogram(tmp_path):
    paths, results = _run(tmp_path, chunks=False)
    assert "chunk_lengths.pdf" not in {p.name for p in paths}
    assert any("chunk_lengths" in n for n in results["notes"])


def test_missing_embedding_and_control_still_write(tmp_path):
    paths, results = _run(tmp_path, embedding=False, control=False)
    assert "cost.pdf" in {p.name for p in paths} and "answers_boxplot.pdf" in {
        p.name for p in paths
    }
    assert any("Embedding" in n for n in results["notes"])
