"""PDF figures of the analysis (ADR 0044), in final size for the thesis.

Layout follows PaperLab's figure rules (SoT 2, AUD-01 Nr. 13): 17 cm wide, Arial >= 8 pt embedded
(the thesis uses one font family), no titles (captions live in LaTeX), axes with quantity and
scale, German decimal comma, the class palette with a validated third hue, controls in neutral
greys with hatching, so colour is never the only carrier. The data are discrete (scores in steps
of 0,2, R@5 often 0 or 1), so distributions are shown as dot plots and the retrieval-answer
relation as small multiples with marker area by count, not as box or scatter plots that hide
ties. The PDFs are byte-reproducible: Agg backend, fixed rcParams, embedded TrueType fonts, no
timestamps. Figures whose inputs are missing are skipped and listed in `results["notes"]`.
"""

import math
import os
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.ticker import FuncFormatter, MultipleLocator  # noqa: E402

from analysis_data import AnalysisData  # noqa: E402
from config import (  # noqa: E402
    ANALYSIS_RULE,
    CONTROL_CRITERIA,
    FIGURE_COLORS,
    FIGURE_DPI,
    FIGURE_FONT_FILE,
    FIGURE_FONT_SIZE,
    FIGURE_GRID,
    FIGURE_HATCHES,
    FIGURE_HEIGHT_CM,
    FIGURE_HISTOGRAM_BINS,
    FIGURE_INK,
    FIGURE_MARKERS,
    FIGURE_MUTED,
    FIGURE_SEQUENTIAL,
    FIGURE_WIDTH_CM,
    ROOT,
    RUBRIC_MAX_SCORE,
    STRATEGY_IDS,
)
from report_tables import fmt_de  # noqa: E402

FIGURE_NAMES = [
    "recall.pdf", "mrr.pdf", "answers_distribution.pdf", "heatmap.pdf",
    "scatter_retrieval_answer.pdf", "catalogue_composition.pdf", "chunk_lengths.pdf", "cost.pdf",
]  # fmt: skip
PDF_METADATA = {"CreationDate": None, "ModDate": None, "Producer": None, "Creator": None}
STRATEGIES = [*STRATEGY_IDS, "K1"]
LABEL_TOTAL = "Gesamtwert (0 bis 2)"
CM = 1 / 2.54
WIDTH = FIGURE_WIDTH_CM * CM
SEQUENTIAL = LinearSegmentedColormap.from_list("figblue", FIGURE_SEQUENTIAL)


def font_path() -> Path | None:
    """Arial from PAPERLAB_FONTS or the fonts/ folder of the PaperLab checkout this repo sits in."""
    roots = [Path(os.environ["PAPERLAB_FONTS"])] if os.environ.get("PAPERLAB_FONTS") else []
    roots += [parent / "fonts" for parent in ROOT.parents]
    for root in roots:
        candidate = root / FIGURE_FONT_FILE
        if candidate.is_file():
            return candidate
    return None


def _style(notes: list[str]) -> None:
    family = "DejaVu Sans"
    path = font_path()
    if path is None:
        notes.append("Arial nicht gefunden (PAPERLAB_FONTS): Abbildungen in DejaVu Sans")
    else:
        font_manager.fontManager.addfont(str(path))
        family = font_manager.FontProperties(fname=str(path)).get_name()
    plt.rcParams.update(
        {
            "font.family": family,
            "font.size": FIGURE_FONT_SIZE,
            "axes.labelsize": FIGURE_FONT_SIZE,
            "xtick.labelsize": FIGURE_FONT_SIZE,
            "ytick.labelsize": FIGURE_FONT_SIZE,
            "legend.fontsize": FIGURE_FONT_SIZE,
            "pdf.fonttype": 42,
            "figure.figsize": (WIDTH, FIGURE_HEIGHT_CM * CM),
            "figure.dpi": FIGURE_DPI,
            "savefig.dpi": FIGURE_DPI,
            "figure.constrained_layout.use": True,
            "figure.constrained_layout.w_pad": 0,  # ink flush with the page box: IU floats are
            "figure.constrained_layout.h_pad": 0,  # left-aligned, 6 pt to caption and source
            "axes.formatter.use_locale": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": FIGURE_MUTED,
            "axes.linewidth": 0.6,
            "axes.labelcolor": FIGURE_INK,
            "text.color": FIGURE_INK,
            "xtick.color": FIGURE_MUTED,
            "ytick.color": FIGURE_MUTED,
            "xtick.labelcolor": FIGURE_INK,
            "ytick.labelcolor": FIGURE_INK,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "axes.grid": False,
            "grid.color": FIGURE_GRID,
            "grid.linewidth": 0.6,
            "hatch.linewidth": 0.6,
            "hatch.color": "white",
            "legend.frameon": False,
        }
    )


def _de_axis(axis, decimals: int = 2) -> None:
    axis.set_major_formatter(FuncFormatter(lambda v, _pos: fmt_de(v, decimals)))


def _score_axis(axis) -> None:
    """A 0-2 score axis: ticks at whole halves, one decimal (0,0 … 2,0)."""
    axis.set_major_locator(MultipleLocator(0.5))
    _de_axis(axis, 1)


def _cost_decimals(values: list[float]) -> int:
    """Decimals that show two significant digits of the largest value."""
    top = max(abs(v) for v in values) or 1.0
    return max(0, -math.floor(math.log10(top)) + 1)


def _ygrid(ax) -> None:
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)


def _save(fig, path: Path) -> Path:
    fig.savefig(path, format="pdf", metadata=PDF_METADATA)
    plt.close(fig)
    return path


def _wide(frame: pd.DataFrame, column: str, strategies: list[str], qids: list[str]) -> dict:
    out = {}
    for s in strategies:
        sub = frame[frame["strategy"] == s].set_index("question_id")[column].astype(float)
        out[s] = [float(sub[q]) for q in qids]
    return out


def _bar(ax, x: float, value: float, key: str, width: float = 0.62) -> None:
    ax.bar(
        x, value, width=width, color=FIGURE_COLORS[key], hatch=FIGURE_HATCHES[key],
        edgecolor=FIGURE_COLORS[key], linewidth=0.6,
    )  # fmt: skip


def _label(ax, x: float, value: float, text: str) -> None:
    """Value above a bar, 2 pt clear of its top."""
    ax.annotate(text, (x, value), xytext=(0, 2), textcoords="offset points", ha="center",
                va="bottom")  # fmt: skip


def _cells(ax, matrix: np.ndarray, vmax: float):
    """A matrix as cells, row 0 at the top, white gaps only between cells (none at the outer
    edge, so the visible object ends where the cells end)."""
    mesh = ax.pcolormesh(matrix, cmap=SEQUENTIAL, vmin=0, vmax=vmax)
    rows, cols = matrix.shape
    ax.hlines(range(1, rows), 0, cols, colors="white", linewidth=1.5)
    ax.vlines(range(1, cols), 0, rows, colors="white", linewidth=1.5)
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.invert_yaxis()
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return mesh


def _bars(results: dict, key: str, ylabel: str, path: Path) -> Path:
    """Mean of a retrieval metric per strategy (main rule), value on each bar."""
    means = results["retrieval"][ANALYSIS_RULE]
    fig, ax = plt.subplots()
    for x, s in enumerate(STRATEGIES):
        value = means[s][key]
        _bar(ax, x, value, s)
        _label(ax, x, value, fmt_de(value, 2))
    ax.set_xticks(range(len(STRATEGIES)), [*STRATEGY_IDS, "K1 (Kontrolle)"])
    ax.set_ylim(0, 1.08)
    ax.yaxis.set_major_locator(MultipleLocator(0.2))
    _de_axis(ax.yaxis, 1)
    ax.set_ylabel(ylabel)
    _ygrid(ax)
    return _save(fig, path)


def _dot_offsets(values: list[float], width: float = 0.7) -> list[float]:
    """Deterministic dot-plot offsets: equal values side by side, centred, in question order."""
    counts = Counter(values)
    step = min(0.05, width / max(counts.values()))
    seen: Counter = Counter()
    offsets = []
    for v in values:
        i = seen[v]
        seen[v] += 1
        offsets.append((i - (counts[v] - 1) / 2) * step)
    return offsets


def _answers_distribution(data: AnalysisData, qids: list[str], path: Path) -> Path:
    """Answer total per question as a dot plot, with median (bar) and mean (white diamond)."""
    scores = data.scores.copy()
    scores["total_score"] = pd.to_numeric(scores["total_score"])
    wide = _wide(scores, "total_score", list(STRATEGY_IDS), qids)
    series = [(s, s, wide[s]) for s in STRATEGY_IDS]
    if data.scores_control is not None:
        ctrl = data.scores_control.copy()
        for c in CONTROL_CRITERIA:
            ctrl[c] = pd.to_numeric(ctrl[c])
        ctrl["total_four"] = ctrl[CONTROL_CRITERIA].mean(axis=1)
        k0 = _wide(ctrl, "total_four", ["K0"], qids)["K0"]
        series.append(("K0", "K0 (vier Kriterien)", k0))
    fig, ax = plt.subplots(figsize=(WIDTH, 7.5 * CM))
    for x, (key, _, values) in enumerate(series):
        offsets = _dot_offsets(values)
        ax.scatter(
            [x + o for o in offsets], values, s=12, marker=FIGURE_MARKERS[key],
            color=FIGURE_COLORS[key], edgecolors="white", linewidths=0.3, zorder=3,
        )  # fmt: skip
        median, mean = float(np.median(values)), float(np.mean(values))
        ax.plot([x - 0.4, x + 0.4], [median, median], color=FIGURE_INK, linewidth=1.2, zorder=4)
        ax.scatter(
            [x + 0.45], [mean], marker="D", s=28, color="white", edgecolors=FIGURE_INK,
            linewidths=0.9, zorder=5,
        )  # fmt: skip
    ax.set_xticks(range(len(series)), [label for _, label, _ in series])
    ax.set_xlim(-0.6, len(series) - 0.35)
    ax.set_ylim(-0.08, RUBRIC_MAX_SCORE + 0.08)
    _score_axis(ax.yaxis)
    ax.set_ylabel(LABEL_TOTAL)
    _ygrid(ax)
    ax.plot([], [], color=FIGURE_INK, linewidth=1.2, label="Median")
    ax.scatter([], [], marker="D", s=28, color="white", edgecolors=FIGURE_INK, label="Mittelwert")
    ax.legend(loc="lower left", ncols=2)
    return _save(fig, path)


def _heatmap(data: AnalysisData, qids: list[str], path: Path) -> Path:
    """Answer total per question (rows) and strategy (columns), one-hue sequential scale."""
    scores = data.scores.copy()
    scores["total_score"] = pd.to_numeric(scores["total_score"])
    wide = _wide(scores, "total_score", list(STRATEGY_IDS), qids)
    matrix = np.array([wide[s] for s in STRATEGY_IDS]).T
    height = max(FIGURE_HEIGHT_CM, 2.5 + 0.42 * len(qids))
    fig, ax = plt.subplots(figsize=(WIDTH * 0.6, height * CM))
    image = _cells(ax, matrix, RUBRIC_MAX_SCORE)
    for (i, j), v in np.ndenumerate(matrix):  # the value in each cell: colour is never alone
        ax.text(j + 0.5, i + 0.5, fmt_de(v, 1), ha="center", va="center",
                color="white" if v / RUBRIC_MAX_SCORE > 0.6 else FIGURE_INK)  # fmt: skip
    ax.set_xticks(np.arange(len(STRATEGY_IDS)) + 0.5, list(STRATEGY_IDS))
    ax.set_yticks(np.arange(len(qids)) + 0.5, qids)
    ax.set_xlabel("Strategie")
    ax.set_ylabel("Frage")
    bar = fig.colorbar(image, ax=ax, shrink=0.6, aspect=25)
    bar.set_label(LABEL_TOTAL)
    bar.outline.set_visible(False)
    _score_axis(bar.ax.yaxis)
    return _save(fig, path)


def _scatter(data: AnalysisData, qids: list[str], results: dict, path: Path) -> Path:
    """R@5 against the answer total per question, one panel per strategy; marker area = number
    of questions at the point; Spearman rho (H2) in each panel."""
    scores = data.scores.copy()
    scores["total_score"] = pd.to_numeric(scores["total_score"])
    ret = data.retrieval[data.retrieval["rule"] == ANALYSIS_RULE]
    recall = _wide(ret, "recall", list(STRATEGY_IDS), qids)
    total = _wide(scores, "total_score", list(STRATEGY_IDS), qids)
    fig, axes = plt.subplots(1, len(STRATEGY_IDS), sharey=True, figsize=(WIDTH, 6.5 * CM))
    corr = results.get("correlation", {}).get("recall", {})
    for ax, s in zip(axes, STRATEGY_IDS, strict=True):
        points = sorted(Counter(zip(recall[s], total[s], strict=True)).items())
        ax.scatter(
            [x for (x, _), _ in points], [y for (_, y), _ in points],
            s=[14 * n for _, n in points], marker=FIGURE_MARKERS[s], color=FIGURE_COLORS[s],
            alpha=0.85, edgecolors="white", linewidths=0.5, zorder=3,
        )  # fmt: skip
        rho = corr.get(s, {}).get("rho")
        label = f"{s}: ρ = {fmt_de(rho, 2)}" if rho is not None else f"{s}: ρ nicht bestimmbar"
        ax.text(0.03, 0.04, label, transform=ax.transAxes, ha="left", va="bottom")
        ax.set_xlim(-0.08, 1.08)
        ax.set_ylim(-0.1, RUBRIC_MAX_SCORE + 0.1)
        ax.xaxis.set_major_locator(MultipleLocator(0.5))
        _de_axis(ax.xaxis, 1)
        ax.set_xlabel("Recall@5")
        _ygrid(ax)
    _score_axis(axes[0].yaxis)
    axes[0].set_ylabel(LABEL_TOTAL)
    for n in (1, 5):
        axes[-1].scatter([], [], s=14 * n, color=FIGURE_MUTED, label=f"{n} Frage{'n' * (n > 1)}")
    axes[-1].legend(loc="lower right", handletextpad=0.3)
    return _save(fig, path)


def _composition(data: AnalysisData, path: Path) -> Path:
    """Number of questions per question type and construction class, as a labelled table."""
    table = pd.crosstab(data.questions["type"], data.questions["difficulty"])
    table = table.reindex(sorted(table.index), axis=0).reindex(sorted(table.columns), axis=1)
    matrix = table.to_numpy()
    fig, ax = plt.subplots(figsize=(WIDTH * 0.75, (2.5 + 0.9 * len(table)) * CM))
    top = max(1, int(matrix.max()))
    shown = np.where(matrix == 0, np.nan, matrix)  # empty cells stay visibly empty (grid colour)
    ax.set_facecolor(FIGURE_GRID)
    _cells(ax, shown, top)
    for (i, j), n in np.ndenumerate(matrix):
        dark = n / top > 0.6
        ax.text(j + 0.5, i + 0.5, str(int(n)), ha="center", va="center",
                color="white" if dark else (FIGURE_MUTED if n == 0 else FIGURE_INK))  # fmt: skip
    ax.set_xticks(np.arange(len(table.columns)) + 0.5, list(table.columns))
    ax.set_yticks(np.arange(len(table.index)) + 0.5, list(table.index))
    ax.xaxis.tick_top()  # column header on top, as in a table; the cells end the object
    ax.xaxis.set_label_position("top")
    ax.set_xlabel("Konstruktionsklasse")
    ax.set_ylabel("Fragetyp")
    return _save(fig, path)


def _chunk_lengths(chunks: dict[str, list[int]], path: Path) -> Path:
    """Chunk length distribution per strategy, shared bins and axis, median marked."""
    keys = [k for k in STRATEGIES if k in chunks]
    fig, axes = plt.subplots(
        len(keys), 1, sharex=True, figsize=(WIDTH, (2.2 + 2.6 * len(keys)) * CM)
    )
    top = max(max(chunks[k]) for k in keys)
    edges = np.linspace(0, top, FIGURE_HISTOGRAM_BINS + 1)
    for ax, k in zip(np.atleast_1d(axes), keys, strict=True):
        ax.hist(
            chunks[k], bins=edges, color=FIGURE_COLORS[k], hatch=FIGURE_HATCHES[k],
            edgecolor="white", linewidth=0.5,
        )  # fmt: skip
        median = float(np.median(chunks[k]))
        ax.axvline(median, color=FIGURE_INK, linewidth=0.9, linestyle=(0, (3, 2)))
        ax.text(
            0.0, 1.02, f"{k}: n = {len(chunks[k])}, Median {fmt_de(median, 0)} (gestrichelt)",
            transform=ax.transAxes, ha="left", va="bottom",
        )  # fmt: skip
        ax.set_ylabel("Anzahl")
        ax.yaxis.get_major_locator().set_params(integer=True, nbins=3)
        _de_axis(ax.yaxis, 0)
        _ygrid(ax)
    last = np.atleast_1d(axes)[-1]
    _de_axis(last.xaxis, 0)
    last.set_xlabel("Chunk-Länge (Tokens)")
    return _save(fig, path)


def _cost(data: AnalysisData, path: Path) -> Path:
    """Generation cost per answer and one-time embedding cost per strategy, side by side."""
    parts = []
    n = len(data.questions)
    if data.generation:
        keys = [k for k in (*STRATEGY_IDS, "K0") if k in data.generation]
        values = [1000 * data.generation[k]["cost_usd"] / n for k in keys]
        parts.append(("Generierung", "Kosten je 1.000 Antworten (USD)", keys, values))
    if data.embedding:
        keys = [k for k in STRATEGIES if k in data.embedding]
        values = [data.embedding[k]["cost_usd"] for k in keys]
        parts.append(("Embedding des Korpus (einmalig)", "Kosten (USD)", keys, values))
    fig, axes = plt.subplots(1, len(parts))
    for ax, (name, ylabel, keys, values) in zip(np.atleast_1d(axes), parts, strict=True):
        decimals = _cost_decimals(values)
        for x, (k, v) in enumerate(zip(keys, values, strict=True)):
            _bar(ax, x, v, k)
            _label(ax, x, v, fmt_de(v, decimals))
        ax.set_xticks(range(len(keys)), keys)
        ax.set_ylim(0, max(values) * 1.15)
        _de_axis(ax.yaxis, decimals)
        ax.yaxis.get_major_locator().set_params(nbins=4)
        ax.set_xlabel(name)
        ax.set_ylabel(ylabel)
        _ygrid(ax)
    return _save(fig, path)


def write_figures(data: AnalysisData, results: dict, out_dir: Path) -> list[Path]:
    _style(results["notes"])
    out_dir.mkdir(parents=True, exist_ok=True)
    qids = sorted(data.questions["question_id"])
    paths = [
        _bars(results, "recall", "Recall@5 (Mittelwert)", out_dir / "recall.pdf"),
        _bars(results, "reciprocal_rank", "MRR (Mittelwert)", out_dir / "mrr.pdf"),
        _answers_distribution(data, qids, out_dir / "answers_distribution.pdf"),
        _heatmap(data, qids, out_dir / "heatmap.pdf"),
        _scatter(data, qids, results, out_dir / "scatter_retrieval_answer.pdf"),
        _composition(data, out_dir / "catalogue_composition.pdf"),
    ]
    if data.chunks is None:
        results["notes"].append("Abbildung chunk_lengths.pdf entfällt: Chunk-Dateien fehlen")
    else:
        paths.append(_chunk_lengths(data.chunks, out_dir / "chunk_lengths.pdf"))
    if data.embedding is None:
        results["notes"].append("Embedding-Kosten in cost.pdf entfallen: Embedding-Läufe fehlen")
    paths.append(_cost(data, out_dir / "cost.pdf"))
    return paths
