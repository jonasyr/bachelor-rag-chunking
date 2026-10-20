"""PDF figures of the analysis (ADR 0044).

Black and greys only, German labels with decimal comma, no titles (captions live in LaTeX).
The PDFs are byte-reproducible: Agg backend, fixed rcParams, embedded TrueType fonts and no
timestamps. Figures whose inputs are missing are skipped and listed in `results["notes"]`.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from analysis_data import AnalysisData  # noqa: E402
from config import (  # noqa: E402
    ANALYSIS_RULE,
    CONTROL_CRITERIA,
    FIGURE_DPI,
    FIGURE_FONT_SIZE,
    FIGURE_HISTOGRAM_BINS,
    FIGURE_SIZE,
    RUBRIC_CRITERIA,
    RUBRIC_MAX_SCORE,
    STRATEGY_IDS,
)
from report_tables import fmt_de  # noqa: E402

FIGURE_NAMES = [
    "recall.pdf", "mrr.pdf", "answers_boxplot.pdf", "heatmap.pdf",
    "scatter_retrieval_answer.pdf", "catalogue_composition.pdf", "chunk_lengths.pdf", "cost.pdf",
]  # fmt: skip
PDF_METADATA = {"CreationDate": None, "ModDate": None, "Producer": None, "Creator": None}
GREYS = {"C1": "0.25", "C2": "0.55", "C3": "0.8", "K1": "1.0", "K0": "1.0"}
HATCHES = {"C1": "", "C2": "", "C3": "", "K1": "//", "K0": "xx"}
MARKERS = {"C1": "o", "C2": "s", "C3": "^"}
STRATEGIES = [*STRATEGY_IDS, "K1"]
LABEL_TOTAL = "Gesamtwert (0 bis 2)"


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": FIGURE_FONT_SIZE,
            "pdf.fonttype": 42,
            "figure.figsize": FIGURE_SIZE,
            "figure.dpi": FIGURE_DPI,
            "savefig.dpi": FIGURE_DPI,
            "figure.constrained_layout.use": True,
            "axes.formatter.use_locale": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "black",
            "text.color": "black",
            "axes.labelcolor": "black",
            "xtick.color": "black",
            "ytick.color": "black",
            "hatch.linewidth": 0.6,
        }
    )


def _de_axis(axis, decimals: int = 2) -> None:
    axis.set_major_formatter(FuncFormatter(lambda v, _pos: fmt_de(v, decimals)))


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


def _bars(results: dict, key: str, ylabel: str, path: Path) -> Path:
    means = results["retrieval"][ANALYSIS_RULE]
    fig, ax = plt.subplots()
    values = [means[s][key] for s in STRATEGIES]
    ax.bar(
        STRATEGIES, values, color=[GREYS[s] for s in STRATEGIES], edgecolor="black",
        hatch=None, linewidth=0.8,
    )  # fmt: skip
    for bar, s in zip(ax.patches, STRATEGIES, strict=True):
        bar.set_hatch(HATCHES[s])
    for x, v in enumerate(values):
        ax.text(x, v, fmt_de(v, 2), ha="center", va="bottom")
    ax.set_ylim(0, 1)
    ax.set_xlabel("Strategie (K1: Kontrolle)")
    ax.set_ylabel(ylabel)
    _de_axis(ax.yaxis, 1)
    return _save(fig, path)


def _answers_boxplot(data: AnalysisData, qids: list[str], path: Path) -> Path:
    scores = data.scores.copy()
    for c in [*RUBRIC_CRITERIA, "total_score"]:
        scores[c] = pd.to_numeric(scores[c])
    wide = _wide(scores, "total_score", list(STRATEGY_IDS), qids)
    series = [wide[s] for s in STRATEGY_IDS]
    labels = list(STRATEGY_IDS)
    if data.scores_control is not None:
        ctrl = data.scores_control.copy()
        for c in CONTROL_CRITERIA:
            ctrl[c] = pd.to_numeric(ctrl[c])
        ctrl["total_four"] = ctrl[CONTROL_CRITERIA].mean(axis=1)
        series.append(_wide(ctrl, "total_four", ["K0"], qids)["K0"])
        labels.append("K0\n(vier Kriterien)")
    fig, ax = plt.subplots()
    box = ax.boxplot(
        series, tick_labels=labels, patch_artist=True, widths=0.5,
        medianprops={"color": "black"}, flierprops={"markeredgecolor": "black", "markersize": 3},
    )  # fmt: skip
    for patch, label in zip(box["boxes"], labels, strict=True):
        key = label.split("\n")[0]
        patch.set_facecolor(GREYS[key])
        patch.set_hatch(HATCHES[key])
        patch.set_edgecolor("black")
    ax.set_ylim(0, RUBRIC_MAX_SCORE)
    ax.set_xlabel("Strategie")
    ax.set_ylabel(LABEL_TOTAL)
    _de_axis(ax.yaxis, 1)
    return _save(fig, path)


def _heatmap(data: AnalysisData, qids: list[str], path: Path) -> Path:
    scores = data.scores.copy()
    scores["total_score"] = pd.to_numeric(scores["total_score"])
    wide = _wide(scores, "total_score", list(STRATEGY_IDS), qids)
    matrix = np.array([wide[s] for s in STRATEGY_IDS]).T
    fig, ax = plt.subplots()
    image = ax.imshow(matrix, cmap="Greys", vmin=0, vmax=RUBRIC_MAX_SCORE, aspect="auto")
    ax.set_xticks(range(len(STRATEGY_IDS)), list(STRATEGY_IDS))
    ax.set_yticks(range(len(qids)), qids, fontsize=max(4, FIGURE_FONT_SIZE - 3))
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlabel("Strategie")
    ax.set_ylabel("Frage")
    bar = fig.colorbar(image, ax=ax)
    bar.set_label(LABEL_TOTAL)
    _de_axis(bar.ax.yaxis, 1)
    return _save(fig, path)


def _scatter(data: AnalysisData, qids: list[str], path: Path) -> Path:
    scores = data.scores.copy()
    scores["total_score"] = pd.to_numeric(scores["total_score"])
    ret = data.retrieval[data.retrieval["rule"] == ANALYSIS_RULE]
    recall = _wide(ret, "recall", list(STRATEGY_IDS), qids)
    total = _wide(scores, "total_score", list(STRATEGY_IDS), qids)
    fig, ax = plt.subplots()
    for s in STRATEGY_IDS:
        ax.scatter(
            recall[s], total[s], marker=MARKERS[s], facecolors=GREYS[s], edgecolors="black",
            linewidths=0.7, s=28, label=s,
        )  # fmt: skip
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, RUBRIC_MAX_SCORE + 0.05)
    ax.set_xlabel("Recall@5")
    ax.set_ylabel(LABEL_TOTAL)
    _de_axis(ax.xaxis, 1)
    _de_axis(ax.yaxis, 1)
    ax.legend(title="Strategie", frameon=False)
    return _save(fig, path)


def _composition(data: AnalysisData, path: Path) -> Path:
    table = pd.crosstab(data.questions["type"], data.questions["difficulty"])
    table = table.reindex(sorted(table.index), axis=0).reindex(sorted(table.columns), axis=1)
    classes = list(table.columns)
    shades = [str(0.2 + 0.6 * i / max(1, len(classes) - 1)) for i in range(len(classes))]
    fig, ax = plt.subplots()
    bottom = np.zeros(len(table))
    for cls, shade in zip(classes, shades, strict=True):
        counts = table[cls].to_numpy()
        ax.bar(
            list(table.index), counts, bottom=bottom, color=shade, edgecolor="black",
            linewidth=0.8, label=cls,
        )  # fmt: skip
        bottom += counts
    ax.set_xlabel("Fragetyp")
    ax.set_ylabel("Anzahl Fragen")
    ax.yaxis.get_major_locator().set_params(integer=True)
    _de_axis(ax.yaxis, 0)
    ax.legend(title="Konstruktionsklasse", frameon=False)
    return _save(fig, path)


def _chunk_lengths(chunks: dict[str, list[int]], path: Path) -> Path:
    keys = [k for k in STRATEGIES if k in chunks]
    fig, axes = plt.subplots(len(keys), 1, sharex=True)
    top = max(max(chunks[k]) for k in keys)
    edges = np.linspace(0, top, FIGURE_HISTOGRAM_BINS + 1)
    for ax, k in zip(np.atleast_1d(axes), keys, strict=True):
        ax.hist(
            chunks[k], bins=edges, color=GREYS[k] if k != "K1" else "0.9", edgecolor="black",
            hatch=HATCHES[k], linewidth=0.6,
        )  # fmt: skip
        ax.set_ylabel(f"{k}\nAnzahl")
        ax.yaxis.get_major_locator().set_params(integer=True)
        _de_axis(ax.yaxis, 0)
        _de_axis(ax.xaxis, 0)
    np.atleast_1d(axes)[-1].set_xlabel("Chunk-Länge (Token)")
    return _save(fig, path)


def _cost(data: AnalysisData, path: Path) -> Path:
    parts = []
    n = len(data.questions)
    if data.generation:
        keys = [k for k in (*STRATEGY_IDS, "K0") if k in data.generation]
        parts.append(
            ("Generierung je Antwort", "Kosten je Antwort (USD)", keys,
             [data.generation[k]["cost_usd"] / n for k in keys])
        )  # fmt: skip
    if data.embedding:
        keys = [k for k in STRATEGIES if k in data.embedding]
        parts.append(
            ("Embedding je Strategie", "Embedding-Kosten (USD)", keys,
             [data.embedding[k]["cost_usd"] for k in keys])
        )  # fmt: skip
    fig, axes = plt.subplots(1, len(parts))
    for ax, (name, ylabel, keys, values) in zip(np.atleast_1d(axes), parts, strict=True):
        bars = ax.bar(
            keys, values, color=[GREYS[k] for k in keys], edgecolor="black", linewidth=0.8
        )
        for bar, k in zip(bars, keys, strict=True):
            bar.set_hatch(HATCHES[k])
        ax.set_xlabel(name)
        ax.set_ylabel(ylabel)
        _de_axis(ax.yaxis, 5)
    return _save(fig, path)


def write_figures(data: AnalysisData, results: dict, out_dir: Path) -> list[Path]:
    _style()
    out_dir.mkdir(parents=True, exist_ok=True)
    qids = sorted(data.questions["question_id"])
    paths = [
        _bars(results, "recall", "Recall@5", out_dir / "recall.pdf"),
        _bars(results, "reciprocal_rank", "MRR", out_dir / "mrr.pdf"),
        _answers_boxplot(data, qids, out_dir / "answers_boxplot.pdf"),
        _heatmap(data, qids, out_dir / "heatmap.pdf"),
        _scatter(data, qids, out_dir / "scatter_retrieval_answer.pdf"),
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
