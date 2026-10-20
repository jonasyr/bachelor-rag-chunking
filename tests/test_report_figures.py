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
    assert "cost.pdf" in {p.name for p in paths} and "answers_distribution.pdf" in {
        p.name for p in paths
    }
    assert any("Embedding" in n for n in results["notes"])


def test_score_axis_ticks_are_whole_halves():
    import matplotlib.pyplot as plt

    import report_figures

    fig, ax = plt.subplots()
    ax.set_ylim(0, 2)
    report_figures._score_axis(ax.yaxis)
    fig.canvas.draw()
    low, high = ax.get_ylim()
    labels = [
        t.get_text()
        for t, v in zip(ax.get_yticklabels(), ax.get_yticks(), strict=False)
        if low <= v <= high
    ]
    assert labels == ["0,0", "0,5", "1,0", "1,5", "2,0"]
    plt.close(fig)


def test_cost_decimals_fit_the_values():
    import report_figures

    assert report_figures._cost_decimals([0.00028, 0.0002]) == 5
    assert report_figures._cost_decimals([0.04, 0.0325]) == 3


def test_figures_use_the_paperlab_palette_and_final_width(tmp_path):
    from config import FIGURE_COLORS, FIGURE_WIDTH_CM

    assert FIGURE_COLORS["C1"] == "#184F95" and FIGURE_COLORS["C2"] == "#B8461A"
    paths, _ = _run(tmp_path)
    recall = next(p for p in paths if p.name == "recall.pdf").read_bytes()
    width_pt = float(recall.split(b"/MediaBox [ 0 0 ")[1].split(b" ")[0])
    assert abs(width_pt - FIGURE_WIDTH_CM / 2.54 * 72) < 0.5


def test_dot_offsets_centre_equal_values():
    import report_figures

    offsets = report_figures._dot_offsets([2.0, 2.0, 2.0, 1.0])
    assert offsets[3] == 0.0 and offsets[1] == 0.0 and offsets[0] == -offsets[2] != 0
