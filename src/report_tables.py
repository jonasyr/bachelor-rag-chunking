"""LaTeX tables and `analysis.json` of the analysis (ADR 0044).

`build_results` computes every number once (statistics from `stats.py`); `write_tables` and
`write_json` only format it, so the tables and the JSON can never disagree. Tables are German,
decimal comma, booktabs rules only. Where the inputs of a part are missing, the part is skipped
and a note is added to `results["notes"]`.
"""

import json
import math
import statistics
from pathlib import Path

import numpy as np
import pandas as pd

import stats
from analysis_data import AnalysisData
from config import (
    ANALYSIS_PRIMARY,
    ANALYSIS_RULE,
    BYTES_PER_MB,
    CONTROL_CRITERIA,
    JSON_DECIMALS,
    REPORT_COST_DECIMALS,
    REPORT_DECIMALS,
    REPORT_P_DECIMALS,
    RUBRIC_CRITERIA,
    STRATEGY_IDS,
)

TABLE_NAMES = [
    "retrieval.tex", "retrieval_sensitivity.tex", "answers.tex", "tests.tex",
    "control_k0.tex", "correlation.tex", "efficiency.tex", "breakdown.tex",
]  # fmt: skip
DASH = "--"
CRITERION_LABELS = {
    "correctness": "Korrektheit",
    "completeness": "Vollständigkeit",
    "groundedness": "Quellenbezug",
    "no_hallucination": "Halluzinationsfreiheit",
    "clarity": "Verständlichkeit",
}
RETRIEVAL_METRICS = {  # column -> label
    "hit": "Hit@5",
    "reciprocal_rank": "MRR",
    "precision": "P@5",
    "recall": "R@5",
    "context_tokens": "Kontext@5",
}
RETRIEVAL_STRATEGIES = [*STRATEGY_IDS, "K1"]
VERDICT_LABELS = {
    "dependent": "abhängig (miss)",
    "known": "bekannt (hit)",
    "not judged": "nicht beurteilt",
}
GROUPS = {"type": "Fragetyp", "difficulty": "Konstruktionsklasse", "verdict": "Closed-book-Urteil"}
_LATEX = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
    "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}  # fmt: skip


# ---------------------------------------------------------------- formatting


def fmt_de(x: float, decimals: int) -> str:
    text = f"{x:.{decimals}f}"
    if float(text) == 0:
        text = text.lstrip("-")
    return text.replace(".", ",")


def fmt_opt(x: float | None, decimals: int = REPORT_DECIMALS) -> str:
    return DASH if x is None else fmt_de(x, decimals)


def fmt_p(p: float | None) -> str:
    if p is None:
        return DASH
    if round(p, REPORT_P_DECIMALS) == 0:
        return "<" + fmt_de(10**-REPORT_P_DECIMALS, REPORT_P_DECIMALS)
    return fmt_de(p, REPORT_P_DECIMALS)


def latex_escape(text: str) -> str:
    return "".join(_LATEX.get(ch, ch) for ch in str(text))


def latex_table(
    name: str, caption: str, header: list[str], rows: list[list[str]], align: str
) -> str:
    def line(cells: list[str]) -> str:
        return " & ".join(latex_escape(c) for c in cells) + r" \\"

    body = [line(header), r"\midrule", *(line(r) for r in rows)]
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        rf"\caption{{{latex_escape(caption)}}}",
        rf"\label{{tab:{name}}}",
        rf"\begin{{tabular}}{{{align}}}",
        r"\toprule",
        body[0],
        *body[1:],
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- computation


def _num(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    frame = frame.copy()
    for c in columns:
        frame[c] = pd.to_numeric(frame[c])
    return frame


def _wide(frame: pd.DataFrame, column: str, strategies: list[str], qids: list[str]) -> dict:
    """strategy -> values in question order."""
    out = {}
    for s in strategies:
        sub = frame[frame["strategy"] == s].set_index("question_id")[column]
        out[s] = [float(sub[q]) for q in qids]
    return out


def _mean(values: list[float]) -> float:
    return float(statistics.fmean(values))


def _effects(values: dict[str, list[float]]) -> dict:
    """Descriptive effect sizes: Kendall's W, pairwise r and median difference; no p-values."""
    omnibus = stats.friedman(values)
    pairs = {}
    for x, y in stats._pair_names(values):  # noqa: SLF001 (same pair order as the tests)
        pair = stats.wilcoxon_pair(values[x], values[y])
        pairs[f"{x}-{y}"] = {
            "r": pair["r"],
            "median_diff": pair.get("median_diff", 0.0 if pair["n_nonzero"] == 0 else None),
            "n_nonzero": pair["n_nonzero"],
        }
    return {"kendalls_w": omnibus["kendalls_w"], "n": omnibus["n"], "pairs": pairs}


def _retrieval_block(data: AnalysisData, rule: str, qids: list[str]) -> tuple[dict, dict]:
    frame = _num(data.retrieval[data.retrieval["rule"] == rule], list(RETRIEVAL_METRICS))
    means, effects = {}, {}
    wide = {m: _wide(frame, m, RETRIEVAL_STRATEGIES, qids) for m in RETRIEVAL_METRICS}
    for s in RETRIEVAL_STRATEGIES:
        means[s] = {m: _mean(wide[m][s]) for m in RETRIEVAL_METRICS}
    for m in RETRIEVAL_METRICS:
        effects[m] = {
            "label": RETRIEVAL_METRICS[m],
            **_effects({s: wide[m][s] for s in STRATEGY_IDS}),
        }
    return means, effects


def _answer_frame(data: AnalysisData) -> pd.DataFrame:
    frame = _num(data.scores, [*RUBRIC_CRITERIA, "total_score"])
    frame["total_four"] = frame[CONTROL_CRITERIA].mean(axis=1)
    return frame


def _k0_frame(data: AnalysisData) -> pd.DataFrame:
    frame = _num(data.scores_control, [*CONTROL_CRITERIA, "total_score"])
    frame["total_four"] = frame[CONTROL_CRITERIA].mean(axis=1)
    return frame


def build_results(data: AnalysisData, alpha: float) -> dict:
    qids = sorted(data.questions["question_id"])
    notes = list(data.notes)
    results: dict = {"n_questions": len(qids), "alpha": alpha}

    # retrieval
    main_means, main_effects = _retrieval_block(data, ANALYSIS_RULE, qids)
    sens_means, sens_effects = _retrieval_block(data, "sensitivity", qids)
    results["retrieval"] = {ANALYSIS_RULE: main_means, "sensitivity": sens_means}

    # answers
    scores = _answer_frame(data)
    answer_cols = [*RUBRIC_CRITERIA, "total_score", "total_four"]
    awide = {c: _wide(scores, c, list(STRATEGY_IDS), qids) for c in answer_cols}
    answer_means = {s: {c: _mean(awide[c][s]) for c in answer_cols} for s in STRATEGY_IDS}
    k0 = None
    if data.scores_control is not None:
        k0 = _k0_frame(data)
        k0_cols = [*CONTROL_CRITERIA, "total_score", "total_four"]
        k0w = {c: _wide(k0, c, ["K0"], qids)["K0"] for c in k0_cols}
        answer_means["K0"] = {c: _mean(v) for c, v in k0w.items()}
    results["answers"] = {"means": answer_means}

    # confirmatory family
    primary = {}
    for col in ANALYSIS_PRIMARY:
        if col == "total_score":
            primary[col] = awide[col]
        else:
            frame = _num(data.retrieval[data.retrieval["rule"] == ANALYSIS_RULE], [col])
            primary[col] = _wide(frame, col, list(STRATEGY_IDS), qids)
    confirm = stats.confirmatory(primary, alpha)
    results["confirmatory"] = {
        col: {"label": ANALYSIS_PRIMARY[col], **r} for col, r in confirm.items()
    }

    # descriptive effect sizes
    desc_retrieval = {m: e for m, e in main_effects.items() if m not in ANALYSIS_PRIMARY}
    desc_sens = dict(sens_effects)
    desc_answers = {
        c: {"label": CRITERION_LABELS[c], **_effects(awide[c])} for c in RUBRIC_CRITERIA
    }
    results["descriptive_effects"] = {
        ANALYSIS_RULE: desc_retrieval,
        "sensitivity": desc_sens,
        "answers": desc_answers,
    }

    # K0 control
    if k0 is None:
        results["control_k0"] = None
        notes.append("Tabelle K0-Vergleich entfällt: keine K0-Bewertung")
    else:
        control = {}
        for s in STRATEGY_IDS:
            diffs = {c: answer_means[s][c] - answer_means["K0"][c] for c in CONTROL_CRITERIA}
            diffs["total_four"] = answer_means[s]["total_four"] - answer_means["K0"]["total_four"]
            pair = stats.wilcoxon_pair(awide["total_four"][s], k0w["total_four"])
            control[s] = {
                "diff": diffs,
                "r": pair["r"],
                "median_diff": pair.get("median_diff", 0.0 if pair["n_nonzero"] == 0 else None),
                "n_nonzero": pair["n_nonzero"],
            }
        results["control_k0"] = control

    # correlation retrieval vs answer total (H2)
    correlation = {}
    for col in ("recall", "reciprocal_rank"):
        frame = _num(data.retrieval[data.retrieval["rule"] == ANALYSIS_RULE], [col])
        wide = _wide(frame, col, list(STRATEGY_IDS), qids)
        per = {s: stats.spearman(wide[s], awide["total_score"][s]) for s in STRATEGY_IDS}
        pooled_x = [v for s in STRATEGY_IDS for v in wide[s]]
        pooled_y = [v for s in STRATEGY_IDS for v in awide["total_score"][s]]
        per["pooled"] = stats.spearman(pooled_x, pooled_y)
        correlation[col] = per
    results["correlation"] = correlation

    results["efficiency"] = _efficiency(data, main_means, answer_means, notes)
    results["breakdown"] = _breakdown(data, qids, awide, primary["recall"], notes)
    results["notes"] = notes
    return _plain(results)


def _efficiency(data: AnalysisData, retrieval: dict, answers: dict, notes: list) -> dict | None:
    if data.chunks is None or data.embedding is None:
        notes.append("Tabelle Effizienz entfällt: Chunk-Dateien oder Embedding-Läufe fehlen")
        return None
    n = len(data.questions)
    out = {}
    for s in [*RETRIEVAL_STRATEGIES, "K0"]:
        entry: dict = {}
        if s in data.chunks:
            lengths = data.chunks[s]
            entry["chunks"] = len(lengths)
            entry["length_median"] = float(statistics.median(lengths))
            entry["length_mean"] = _mean(lengths)
        if s in retrieval:
            entry["context_tokens"] = retrieval[s]["context_tokens"]
        if s in data.embedding:
            emb = data.embedding[s]
            entry["index_mb"] = emb["vector_bytes"] / BYTES_PER_MB
            entry["embedding_tokens"] = emb["input_tokens"]
            entry["embedding_cost_usd"] = emb["cost_usd"]
        if s in data.generation:
            gen = data.generation[s]
            entry["prompt_tokens_per_answer"] = gen["prompt_tokens"] / n
            entry["completion_tokens_per_answer"] = gen["completion_tokens"] / n
            entry["cost_per_answer_usd"] = gen["cost_usd"] / n
        if s in answers:
            entry["answer_total"] = answers[s]["total_score"]
        if s in retrieval:
            entry["recall"] = retrieval[s]["recall"]
        out[s] = entry
    return out


def _breakdown(data, qids, awide, rwide, notes) -> dict:
    labels = {
        "type": dict(zip(data.questions["question_id"], data.questions["type"], strict=True)),
        "difficulty": dict(
            zip(data.questions["question_id"], data.questions["difficulty"], strict=True)
        ),
    }
    if data.verdicts is not None:
        labels["verdict"] = {q: data.verdicts.get(q, "not judged") for q in qids}
    else:
        notes.append("Aufteilung nach Closed-book-Urteil entfällt: keine Urteile")
    out: dict = {}
    for group, mapping in labels.items():
        levels = {}
        for level in sorted(set(mapping.values())):
            idx = [i for i, q in enumerate(qids) if mapping[q] == level]
            levels[level] = {
                "n": len(idx),
                "total_score": {
                    s: _mean([awide["total_score"][s][i] for i in idx]) for s in STRATEGY_IDS
                },
                "recall": {s: _mean([rwide[s][i] for i in idx]) for s in STRATEGY_IDS},
            }
        out[group] = levels
    return out


# ---------------------------------------------------------------- tables


def _retrieval_table(results: dict, rule: str, name: str, caption: str) -> str:
    block = results["retrieval"][rule]
    header = ["Strategie", *RETRIEVAL_METRICS.values()]
    rows = []
    for s, m in block.items():
        rows.append(
            [s]
            + [
                fmt_de(m[col], 1 if col == "context_tokens" else REPORT_DECIMALS)
                for col in RETRIEVAL_METRICS
            ]
        )
    return latex_table(name, caption, header, rows, "l" + "r" * len(RETRIEVAL_METRICS))


def _answers_table(results: dict) -> str:
    means = results["answers"]["means"]
    header = ["Strategie", *CRITERION_LABELS.values(), "Gesamtwert", "Gesamtwert (vier Kriterien)"]
    rows = []
    for s, m in means.items():
        rows.append(
            [s]
            + [fmt_opt(m.get(c)) for c in RUBRIC_CRITERIA]
            + [fmt_opt(m["total_score"]) if s != "K0" else DASH, fmt_opt(m["total_four"])]
        )
    caption = (
        "Antwortqualität je Strategie (Mittelwerte der Bewertung 0 bis 2). K0 ohne Retrieval wird "
        "ohne Quellenbezug bewertet; der Gesamtwert über die vier gemeinsamen Kriterien macht K0 "
        "mit C1 bis C3 vergleichbar."
    )
    return latex_table("answers", caption, header, rows, "l" + "r" * 7)


def _tests_table(results: dict) -> str:
    header = ["Metrik", "Vergleich", "Statistik", "p", "p (Holm)", "Effekt", "Median-Differenz"]
    rows: list[list[str]] = []
    for r in results["confirmatory"].values():
        label = r["label"]
        if not r["testable"]:
            rows.append([label, "Friedman", "nicht testbar", DASH, DASH, DASH, DASH])
            continue
        rows.append(
            [label, "Friedman", fmt_de(r["statistic"], REPORT_DECIMALS), fmt_p(r["p"]),
             fmt_p(r["p_adj"]), "W = " + fmt_de(r["kendalls_w"], REPORT_DECIMALS), DASH]
        )  # fmt: skip
        for pair, w in r.get("pairs", {}).items():
            name = pair.replace("-", "--")
            if not w["testable"]:
                rows.append([label, name, "nicht testbar", DASH, DASH, DASH, DASH])
                continue
            rows.append(
                [label, name, fmt_de(w["statistic"], REPORT_DECIMALS), fmt_p(w["p"]),
                 fmt_p(w["p_adj"]), "r = " + fmt_de(w["r"], REPORT_DECIMALS),
                 fmt_de(w["median_diff"], REPORT_DECIMALS)]
            )  # fmt: skip
    desc = results["descriptive_effects"]
    for block in (desc[ANALYSIS_RULE], desc["answers"]):
        for e in block.values():
            rows.append([e["label"], "Friedman", DASH, DASH, DASH, _w(e["kendalls_w"]), DASH])
            for pair, v in e["pairs"].items():
                rows.append(
                    [e["label"], pair.replace("-", "--"), DASH, DASH, DASH,
                     "r = " + fmt_opt(v["r"]), fmt_opt(v["median_diff"])]
                )  # fmt: skip
    caption = (
        "Tests und Effektstärken der Strategien C1 bis C3, explorativ (Signifikanzniveau "
        f"{fmt_de(results['alpha'], 2)}). Friedman-Test je Hauptmetrik mit Holm-Korrektur über die "
        "Hauptmetriken; paarweise Wilcoxon-Tests nur bei signifikantem Gesamttest, Holm-korrigiert "
        "über alle Paare. Übrige Maße deskriptiv, ohne p-Werte; Effekt: Kendalls W bzw. r, "
        "Median-Differenz jeweils erste minus zweite Strategie."
    )
    return latex_table("tests", caption, header, rows, "llrrrrr")


def _w(w: float | None) -> str:
    return DASH if w is None else "W = " + fmt_de(w, REPORT_DECIMALS)


def _k0_table(results: dict) -> str:
    header = ["Strategie", *(CRITERION_LABELS[c] for c in CONTROL_CRITERIA),
              "Gesamtwert (vier Kriterien)", "r", "Median-Differenz"]  # fmt: skip
    rows = []
    for s, c in results["control_k0"].items():
        rows.append(
            [f"{s} -- K0"]
            + [fmt_de(c["diff"][k], REPORT_DECIMALS) for k in CONTROL_CRITERIA]
            + [fmt_de(c["diff"]["total_four"], REPORT_DECIMALS), fmt_opt(c["r"]),
               fmt_opt(c["median_diff"])]
        )  # fmt: skip
    caption = (
        "Mittlere Differenz der Antwortqualität zwischen C1 bis C3 und der Kontrolle K0 ohne "
        "Retrieval (Strategie minus K0), je Kriterium und im Gesamtwert über die vier gemeinsamen "
        "Kriterien; Effektstärke r und Median-Differenz des Gesamtwerts. K0 ist Kontrolle, "
        "deskriptiv, ohne p-Werte."
    )
    return latex_table("control_k0", caption, header, rows, "l" + "r" * 7)


def _correlation_table(results: dict) -> str:
    header = ["Metrik", "Gruppe", "Spearman rho", "p", "n"]
    rows = []
    for col, per in results["correlation"].items():
        for group, c in per.items():
            label = "gesamt" if group == "pooled" else group
            rows.append(
                [ANALYSIS_PRIMARY[col], label, fmt_opt(c["rho"]), fmt_p(c.get("p")), str(c["n"])]
            )
    caption = (
        "Rangkorrelation (Spearman, explorativ) zwischen dem Retrieval je Frage (R@5 bzw. MRR, "
        "Hauptregel) und dem Gesamtwert der Antwort, je Strategie und über alle Strategien."
    )
    return latex_table("correlation", caption, header, rows, "llrrr")


def _efficiency_table(results: dict) -> str:
    eff = results["efficiency"]
    strategies = list(eff)
    d, c = REPORT_DECIMALS, REPORT_COST_DECIMALS
    lines = [
        ("Chunks", "chunks", 0),
        ("Chunklänge (Median, Tokens)", "length_median", 0),
        ("Chunklänge (Mittel, Tokens)", "length_mean", 1),
        ("Kontext@5 (Tokens)", "context_tokens", 1),
        ("Indexgröße (MB)", "index_mb", d),
        ("Embedding-Tokens", "embedding_tokens", 0),
        ("Embedding-Kosten (USD)", "embedding_cost_usd", c),
        ("Prompt-Tokens je Antwort", "prompt_tokens_per_answer", 0),
        ("Antwort-Tokens je Antwort", "completion_tokens_per_answer", 0),
        ("Kosten je Antwort (USD)", "cost_per_answer_usd", c),
        ("Gesamtwert der Antwort", "answer_total", d),
        ("R@5", "recall", d),
    ]
    rows = [
        [label, *(fmt_opt(eff[s].get(key), dec) for s in strategies)] for label, key, dec in lines
    ]
    caption = (
        "Aufwand und Kosten je Strategie neben Antwortqualität und R@5, ohne zusammengefasste "
        "Kennzahl. Indexgröße und Embedding einmalig; Generierung je Antwort; K1 nur Retrieval, "
        "K0 nur Generierung."
    )
    return latex_table(
        "efficiency", caption, ["Kennzahl", *strategies], rows, "l" + "r" * len(strategies)
    )


def _breakdown_table(results: dict) -> str:
    header = ["Aufteilung", "Gruppe", "n"]
    for s in STRATEGY_IDS:
        header += [f"{s} Gesamtwert", f"{s} R@5"]
    rows = []
    for group, levels in results["breakdown"].items():
        for level, v in levels.items():
            shown = VERDICT_LABELS.get(level, level) if group == "verdict" else level
            row = [GROUPS[group], shown, str(v["n"])]
            for s in STRATEGY_IDS:
                row += [
                    fmt_de(v["total_score"][s], REPORT_DECIMALS),
                    fmt_de(v["recall"][s], REPORT_DECIMALS),
                ]
            rows.append(row)
    caption = (
        "Gesamtwert der Antwort und R@5 (Hauptregel) je Fragetyp, Konstruktionsklasse und "
        "Closed-book-Urteil. Rein deskriptiv: pro Gruppe zu wenige Fragen für Tests."
    )
    return latex_table("breakdown", caption, header, rows, "llr" + "r" * (2 * len(STRATEGY_IDS)))


def write_tables(results: dict, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "retrieval.tex": lambda: _retrieval_table(
            results,
            ANALYSIS_RULE,
            "retrieval",
            "Retrieval-Qualität je Strategie (Mittelwerte über alle Fragen, Hauptregel der "
            "Relevanz); K1 ist die Kontrolle mit gleich langen Fenstern.",
        ),
        "retrieval_sensitivity.tex": lambda: _retrieval_table(
            results,
            "sensitivity",
            "retrieval_sensitivity",
            "Retrieval-Qualität je Strategie nach der Sensitivitätsregel der Relevanz "
            "(Mittelwerte über alle Fragen).",
        ),
        "answers.tex": lambda: _answers_table(results),
        "tests.tex": lambda: _tests_table(results),
        "control_k0.tex": lambda: _k0_table(results),
        "correlation.tex": lambda: _correlation_table(results),
        "efficiency.tex": lambda: _efficiency_table(results),
        "breakdown.tex": lambda: _breakdown_table(results),
    }
    skipped = {"control_k0.tex": "control_k0", "efficiency.tex": "efficiency"}
    written = []
    for name in TABLE_NAMES:
        if skipped.get(name) and results.get(skipped[name]) is None:
            continue
        path = out_dir / name
        path.write_text(tables[name](), encoding="utf-8")
        written.append(path)
    return written


# ---------------------------------------------------------------- json


def _plain(obj):
    if isinstance(obj, dict):
        return {str(k): _plain(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_plain(v) for v in obj]
    if isinstance(obj, bool | np.bool_):
        return bool(obj)
    if isinstance(obj, int | np.integer):
        return int(obj)
    if isinstance(obj, float | np.floating):
        x = float(obj)
        if not math.isfinite(x):
            raise ValueError("non-finite number in the results")
        return round(x, JSON_DECIMALS)
    return obj


def write_json(results: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_plain(results), sort_keys=True, indent=2, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8")
