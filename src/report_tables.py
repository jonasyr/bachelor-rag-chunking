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

import agreement
import stats
from analysis_data import AnalysisData
from config import (
    AGREEMENT_CI_LEVEL,
    ANALYSIS_PRIMARY,
    ANALYSIS_RULE,
    BYTES_PER_MB,
    CONTROL_ANSWER_STRATEGIES,
    CONTROL_CRITERIA,
    CONTROL_STRATEGIES,
    JSON_DECIMALS,
    RAGAS_METRICS,
    REPORT_COST_DECIMALS,
    REPORT_DECIMALS,
    REPORT_P_DECIMALS,
    RUBRIC_CRITERIA,
    STRATEGY_IDS,
)

(K1,) = CONTROL_STRATEGIES  # "K1"
(K0,) = CONTROL_ANSWER_STRATEGIES  # "K0"


TABLE_NAMES = [
    "retrieval.tex", "retrieval_sensitivity.tex", "answers.tex", "tests.tex",
    "control_k0.tex", "correlation.tex", "efficiency.tex", "breakdown.tex",
    "ragas.tex", "ragas_agreement.tex", "tests_descriptive.tex", "ragas_effects.tex",
    "agreement.tex",
]  # fmt: skip
DASH = "--"
MINUS = "\u2212"  # typographic minus, also in the figures (Arial has it)
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
RAGAS_LABELS = {
    "faithfulness": "Faithfulness",
    "response_relevancy": "Response Relevancy",
    "context_precision": "Context Precision",
    "context_recall": "Context Recall",
}
# agreement pairs: (RAGAS metric, other measure, source of the other measure)
RAGAS_PAIRS = [
    ("faithfulness", "groundedness", "scores"),
    ("faithfulness", "no_hallucination", "scores"),
    ("response_relevancy", "answers_question", "checks"),
    ("context_precision", "precision", "retrieval"),
    ("context_recall", "recall", "retrieval"),
]
RAGAS_PAIR_LABELS = {
    "groundedness": "Quellenbezug",
    "no_hallucination": "Halluzinationsfreiheit",
    "answers_question": "Frage beantwortet",
    "precision": "P@5",
    "recall": "R@5",
}
NOT_DETERMINABLE = "nicht bestimmbar"
CHECK_LABELS = {  # the eight checks of scoring_rules.CHECKS
    "declines": "Ablehnung",
    "core_wrong": "Kernaussage falsch",
    "other_error": "Anderer Fehler",
    "grounded": "Durch Passagen gestützt",
    "hallucination": "Halluzination",
    "answers_question": "Frage beantwortet",
    "direct": "Direkt",
    "wordy": "Wortreich",
}
RETRIEVAL_STRATEGIES = [*STRATEGY_IDS, K1]
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
    return text.replace(".", ",").replace("-", MINUS)


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
    name: str,
    title: str,
    header: list[str] | str,
    rows: list[list[str] | str],
    align: str,
    note: str = "",
) -> str:
    """A table after the IU rules (ZL S. 19): short title above (no final period), source line
    below (`\\source` of iupaper), alignment from the class. Cells are escaped; a header or row
    given as a string is raw LaTeX (group headings, `\\cmidrule`)."""

    def line(cells: list[str] | str) -> str:
        if isinstance(cells, str):
            return cells
        return " & ".join(latex_escape(c) for c in cells) + r" \\"

    source = "Eigene Darstellung." + (f" {latex_escape(note)}" if note else "")
    lines = [
        r"\begin{table}[htbp]",
        rf"\caption{{{latex_escape(title)}}}",
        rf"\label{{tab:{name}}}",
        rf"\begin{{tabular}}{{{align}}}",
        r"\toprule",
        line(header),
        r"\midrule",
        *(line(r) for r in rows),
        r"\bottomrule",
        r"\end{tabular}",
        rf"\source{{{source}}}",
        r"\end{table}",
    ]
    return "\n".join(lines) + "\n"


def _group(label: str, columns: int, first: bool) -> str:
    """A group heading across the table (italic), with a little space above all but the first."""
    space = "" if first else r"\addlinespace" + "\n"
    return rf"{space}\multicolumn{{{columns}}}{{@{{}}l}}{{\textit{{{latex_escape(label)}}}}} \\"


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
        k0w = {c: _wide(k0, c, [K0], qids)[K0] for c in k0_cols}
        answer_means[K0] = {c: _mean(v) for c, v in k0w.items()}
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
            diffs = {c: answer_means[s][c] - answer_means[K0][c] for c in CONTROL_CRITERIA}
            diffs["total_four"] = answer_means[s]["total_four"] - answer_means[K0]["total_four"]
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
        # each question appears once per strategy, so the pairs are not independent: rho only
        pooled = stats.spearman(pooled_x, pooled_y)
        per["pooled"] = {k: v for k, v in pooled.items() if k != "p"}
        correlation[col] = per
    results["correlation"] = correlation

    results["ragas"] = _ragas_block(data, qids)
    results["ragas_agreement"] = _ragas_agreement(data, qids, notes)
    if results["ragas"] is not None and data.ragas_repeat is not None:
        results["ragas_stability"] = _ragas_stability(data, qids)
    results["efficiency"] = _efficiency(data, main_means, answer_means, notes)
    results["breakdown"] = _breakdown(data, qids, awide, primary["recall"], notes)
    results["agreement"] = _agreement(data)
    results["notes"] = notes
    return _plain(results)


def _agreement(data: AnalysisData) -> dict | None:
    """Agreement of the first and the second rating (ADR 0046); None without a closed one."""
    if data.second_rating is None:
        return None
    paired = data.second_rating["paired"]
    return {
        "rows": agreement.rows(paired),
        "n_codes": len(paired),
        "n_questions": len({p["question_id"] for p in paired}),
        "reps": agreement.AGREEMENT_BOOTSTRAP_REPS,
        "level": AGREEMENT_CI_LEVEL,
    }


def _ragas_values(frame: pd.DataFrame, qids: list[str]) -> dict:
    """metric -> strategy -> question -> value; an empty cell (metric-defined NaN) is None."""
    out: dict = {m: {s: {} for s in STRATEGY_IDS} for m in RAGAS_METRICS}
    for m in RAGAS_METRICS:
        numbers = pd.to_numeric(frame[m], errors="coerce")
        for q, s, v in zip(frame["question_id"], frame["strategy"], numbers, strict=True):
            out[m][s][q] = None if math.isnan(v) else float(v)
    return out


def _ragas_block(data: AnalysisData, qids: list[str]) -> dict | None:
    """Means over the questions with a value, NaN counts, and descriptive effect sizes over the
    questions that are complete (a value for every strategy)."""
    if data.ragas is None:
        return None
    values = _ragas_values(data.ragas, qids)
    means = {
        s: {
            m: _mean(got) if (got := [v for v in values[m][s].values() if v is not None]) else None
            for m in RAGAS_METRICS
        }
        for s in STRATEGY_IDS
    }
    nan_counts = {
        s: {m: sum(v is None for v in values[m][s].values()) for m in RAGAS_METRICS}
        for s in STRATEGY_IDS
    }
    effects = {}
    for m in RAGAS_METRICS:
        complete = [q for q in qids if all(values[m][s][q] is not None for s in STRATEGY_IDS)]
        effects[m] = {
            "label": RAGAS_LABELS[m],
            **(_effects({s: [values[m][s][q] for q in complete] for s in STRATEGY_IDS})
               if complete else {"kendalls_w": None, "n": 0, "pairs": {}}),
        }  # fmt: skip
    return {"means": means, "nan_counts": nan_counts, "effects": effects}


def _other_measure(data: AnalysisData, source: str, column: str, qids: list[str]):
    """strategy -> question -> value of the rule-based measure; None if its source is absent."""
    if source == "checks":
        if data.answers_question is None:
            return None
        return {s: {q: float(data.answers_question[(q, s)]) for q in qids} for s in STRATEGY_IDS}
    frame = data.scores if source == "scores" else data.retrieval
    if source == "retrieval":
        frame = frame[frame["rule"] == ANALYSIS_RULE]
    frame = _num(frame, [column])
    return {
        s: dict(zip(frame[frame["strategy"] == s]["question_id"],
                    frame[frame["strategy"] == s][column], strict=True))
        for s in STRATEGY_IDS
    }  # fmt: skip


def _ragas_agreement(data: AnalysisData, qids: list[str], notes: list) -> dict | None:
    """Spearman's rho between a RAGAS metric and the rule-based measure, per strategy and pooled
    (rho only: each question appears once per strategy). A question with a missing value on
    either side is dropped from that pair."""
    if data.ragas is None:
        return None
    values = _ragas_values(data.ragas, qids)
    out: dict = {}
    for metric, column, source in RAGAS_PAIRS:
        other = _other_measure(data, source, column, qids)
        if other is None:
            notes.append(f"Übereinstimmung {metric}~{column} entfällt: {column} fehlt")
            continue
        xs: dict = {}
        ys: dict = {}
        for s in STRATEGY_IDS:
            kept = [q for q in qids if values[metric][s][q] is not None and q in other[s]]
            xs[s] = [values[metric][s][q] for q in kept]
            ys[s] = [float(other[s][q]) for q in kept]
        per = {s: stats.spearman(xs[s], ys[s]) for s in STRATEGY_IDS}
        per["pooled"] = stats.spearman(
            [v for s in STRATEGY_IDS for v in xs[s]], [v for s in STRATEGY_IDS for v in ys[s]]
        )
        # descriptive (ADR 0047): rho and n only, no p-value, pooled or per strategy
        out[f"{metric}~{column}"] = {
            g: {k: v for k, v in per[g].items() if k != "p"} for g in ["pooled", *STRATEGY_IDS]
        }
    return out


def _ragas_stability(data: AnalysisData, qids: list[str]) -> dict:
    """Run 1 against run 2 over the answers with a value in both: mean absolute difference,
    Spearman's rho and the share of equal values (to the stored decimals)."""
    first = _ragas_values(data.ragas, qids)
    second = _ragas_values(data.ragas_repeat, qids)
    out = {}
    for m in RAGAS_METRICS:
        pairs = [
            (first[m][s][q], second[m][s][q])
            for s in STRATEGY_IDS for q in qids
            if first[m][s][q] is not None and second[m][s][q] is not None
        ]  # fmt: skip
        a, b = [p[0] for p in pairs], [p[1] for p in pairs]
        out[m] = {
            "n": len(pairs),
            "mean_abs_diff": _mean([abs(x - y) for x, y in pairs]) if pairs else None,
            "rho": stats.spearman(a, b)["rho"],
            "share_equal": sum(x == y for x, y in pairs) / len(pairs) if pairs else None,
        }
    return out


def _efficiency(data: AnalysisData, retrieval: dict, answers: dict, notes: list) -> dict | None:
    if data.chunks is None or data.embedding is None:
        notes.append("Tabelle Effizienz entfällt: Chunk-Dateien oder Embedding-Läufe fehlen")
        return None
    n = len(data.questions)
    out = {}
    for s in [*RETRIEVAL_STRATEGIES, K0]:
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


def _retrieval_table(results: dict, rule: str, name: str, title: str, note: str) -> str:
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
    align = "l" + "r" * len(RETRIEVAL_METRICS)
    return latex_table(name, title, header, rows, align, note)


def _answers_table(results: dict) -> str:
    """Criteria as rows, strategies as columns: five labels side by side do not fit the page."""
    means = results["answers"]["means"]
    strategies = list(means)
    lines = [(CRITERION_LABELS[c], c) for c in RUBRIC_CRITERIA]
    lines += [("Gesamtwert", "total_score"), ("Gesamtwert (vier Kriterien)", "total_four")]
    rows = []
    for label, key in lines:
        cells = []
        for s in strategies:
            hidden = s == K0 and key == "total_score"  # K0 has no groundedness score
            cells.append(DASH if hidden else fmt_opt(means[s].get(key)))
        rows.append([label, *cells])
    note = (
        "Mittelwerte der Bewertung von 0 bis 2. K0 ohne Retrieval wird ohne Quellenbezug "
        "bewertet; der Gesamtwert über die vier gemeinsamen Kriterien macht K0 mit C1 bis C3 "
        "vergleichbar."
    )
    return latex_table(
        "answers", "Antwortqualität je Kriterium und Strategie", ["Kriterium", *strategies],
        rows, "l" + "r" * len(strategies), note,
    )  # fmt: skip


def _tests_table(results: dict) -> str:
    """The confirmatory tests, one group per metric (its name as heading), so the metric needs no
    column of its own. The descriptive effects are in `_tests_descriptive_table`."""
    header = ["Vergleich", "Statistik", "p", "p (Holm)", "Effekt", "Median-Differenz"]
    rows: list[list[str] | str] = []
    for r in results["confirmatory"].values():
        rows.append(_group(r["label"], len(header), not rows))
        if not r["testable"]:
            rows.append(["Friedman", "nicht testbar", DASH, DASH, DASH, DASH])
            continue
        rows.append(
            ["Friedman", fmt_de(r["statistic"], REPORT_DECIMALS), fmt_p(r["p"]),
             fmt_p(r["p_adj"]), "W = " + fmt_de(r["kendalls_w"], REPORT_DECIMALS), DASH]
        )  # fmt: skip
        for pair, w in r.get("pairs", {}).items():
            name = pair.replace("-", "–")
            if not w["testable"]:
                rows.append([name, "nicht testbar", DASH, DASH, DASH, DASH])
                continue
            rows.append(
                [name, fmt_de(w["statistic"], REPORT_DECIMALS), fmt_p(w["p"]),
                 fmt_p(w["p_adj"]), "r = " + fmt_de(w["r"], REPORT_DECIMALS),
                 fmt_de(w["median_diff"], REPORT_DECIMALS)]
            )  # fmt: skip
    note = (
        f"Explorativ, Signifikanzniveau {fmt_de(results['alpha'], 2)}. Friedman-Test je "
        "Hauptmetrik mit Holm-Korrektur über die Hauptmetriken; paarweise Wilcoxon-Tests nur bei "
        "signifikantem Gesamttest, Holm-korrigiert über alle Paare. Effekt: Kendalls W bzw. r; "
        "Median-Differenz jeweils erste minus zweite Strategie. Übrige Maße deskriptiv in einer "
        "eigenen Tabelle."
    )
    return latex_table(
        "tests", "Tests und Effektstärken der Strategien C1 bis C3", header, rows, "lrrrrr", note
    )


def _tests_descriptive_table(results: dict) -> str:
    """Kendall's W and pairwise r of the measures without a test; no columns for statistic and
    p-values, which would only hold dashes."""
    header = ["Vergleich", "Effekt", "Median-Differenz"]
    rows: list[list[str] | str] = []
    desc = results["descriptive_effects"]
    for block in (desc[ANALYSIS_RULE], desc["answers"]):
        for key, e in block.items():
            unit = " (Tokens)" if key == "context_tokens" else ""
            rows.append(_group(f"{e['label']}{unit}", len(header), not rows))
            rows.append(["Friedman", _w(e["kendalls_w"]), DASH])
            for pair, v in e["pairs"].items():
                rows.append([pair.replace("-", "–"), _r(v["r"]), fmt_opt(v["median_diff"])])
    note = (
        "Deskriptiv, ohne p-Werte: Maße ohne Test (Retrieval nach der Hauptregel, Kriterien der "
        "Antwort). Effekt: Kendalls W bzw. r; Median-Differenz jeweils erste minus zweite "
        "Strategie, bei Kontext@5 in Tokens."
    )
    return latex_table(
        "tests_descriptive", "Deskriptive Effektstärken der Strategien C1 bis C3", header, rows,
        "lrr", note,
    )  # fmt: skip


def _w(w: float | None) -> str:
    return DASH if w is None else "W = " + fmt_de(w, REPORT_DECIMALS)


def _r(r: float | None) -> str:
    return DASH if r is None else "r = " + fmt_de(r, REPORT_DECIMALS)


def _k0_table(results: dict) -> str:
    """Measures as rows, one column per difference strategy minus K0."""
    control = results["control_k0"]
    strategies = list(control)
    lines = [(CRITERION_LABELS[k], lambda c, k=k: fmt_de(c["diff"][k], REPORT_DECIMALS))
             for k in CONTROL_CRITERIA]  # fmt: skip
    lines += [
        ("Gesamtwert (vier Kriterien)", lambda c: fmt_de(c["diff"]["total_four"], REPORT_DECIMALS)),
        ("Effektstärke r (Gesamtwert)", lambda c: fmt_opt(c["r"])),
        ("Median-Differenz (Gesamtwert)", lambda c: fmt_opt(c["median_diff"])),
    ]
    rows = [[label, *(cell(control[s]) for s in strategies)] for label, cell in lines]
    note = (
        "Mittlere Differenz der Bewertung (Strategie minus K0, Kontrolle ohne Retrieval), "
        "deskriptiv, ohne p-Werte."
    )
    header = ["Maß", *(f"{s} {MINUS} K0" for s in strategies)]
    return latex_table(
        "control_k0", "Antwortqualität im Vergleich mit der Kontrolle K0", header, rows,
        "l" + "r" * len(strategies), note,
    )  # fmt: skip


def _correlation_table(results: dict) -> str:
    header = ["Gruppe", "Spearmans ρ", "p", "n"]
    rows: list[list[str] | str] = []
    for col, per in results["correlation"].items():
        rows.append(_group(ANALYSIS_PRIMARY[col], len(header), not rows))
        for group, c in per.items():
            label = "gesamt" if group == "pooled" else group
            rows.append([label, fmt_opt(c["rho"]), fmt_p(c.get("p")), str(c["n"])])
    note = (
        "Explorativ. Retrieval je Frage (Hauptregel) gegen den Gesamtwert der Antwort, je "
        "Strategie und über alle Strategien (gesamt: jede Frage dreifach, daher ohne p-Wert)."
    )
    return latex_table(
        "correlation", "Rangkorrelation zwischen Retrieval- und Antwortqualität", header, rows,
        "lrrr", note,
    )  # fmt: skip


def _ragas_table(results: dict) -> str:
    """Means and Kendall's W per metric; the pairwise effects are in `_ragas_effects_table`.
    Descriptive: RAGAS is a second view, no basis of a statement (ADR 0047)."""
    block = results["ragas"]
    header = ["Metrik", *STRATEGY_IDS, "Kendalls W"]
    rows: list[list[str] | str] = []
    for m in RAGAS_METRICS:
        rows.append(
            [RAGAS_LABELS[m], *(fmt_opt(block["means"][s][m]) for s in STRATEGY_IDS),
             fmt_opt(block["effects"][m]["kendalls_w"])]
        )  # fmt: skip
    counts = [
        f"{RAGAS_LABELS[m]} {s}: {block['nan_counts'][s][m]}"
        for m in RAGAS_METRICS for s in STRATEGY_IDS if block["nan_counts"][s][m]
    ]  # fmt: skip
    nan = (
        "NaN der Metrik (je Metrik und Strategie): " + ", ".join(counts) + "."
        if counts
        else "Kein NaN der Metrik."
    )
    n = min(e["n"] for e in block["effects"].values())
    note = (
        "Mittelwerte der RAGAS-Metriken von 0 bis 1 über die Fragen mit Wert. "
        f"{nan} Kendalls W über die Fragen mit Wert in allen Strategien (mindestens {n}), "
        "deskriptiv, ohne p-Werte. RAGAS ist eine zweite Sicht neben der regelbasierten Bewertung."
    )
    return latex_table(
        "ragas", "RAGAS-Bewertung je Strategie", header, rows, "l" + "r" * (len(header) - 1), note
    )


def _ragas_effects_table(results: dict) -> str:
    """Per metric and pair r, median difference and n′ (the questions r rests on)."""
    effects = results["ragas"]["effects"]
    pair_names = list(dict.fromkeys(p for e in effects.values() for p in e["pairs"]))
    header = ["Metrik", *(p.replace("-", "–") for p in pair_names)]
    rows: list[list[str] | str] = []
    for m in RAGAS_METRICS:
        pairs = effects[m]["pairs"]
        rows.append(
            [RAGAS_LABELS[m]]
            + [
                f"{fmt_opt(pairs[p]['r'])} ({fmt_opt(pairs[p]['median_diff'])}; "
                f"n′ = {pairs[p]['n_nonzero']})"
                if p in pairs else DASH
                for p in pair_names
            ]
        )  # fmt: skip
    note = (
        "Deskriptiv, ohne p-Werte. Je Paar Effektstärke r (Median-Differenz erste minus zweite "
        "Strategie; n′ Fragen mit Differenz ungleich 0, auf denen r beruht, bei vielen gleichen "
        "Werten klein)."
    )
    return latex_table(
        "ragas_effects", "Paarweise Effekte der RAGAS-Metriken", header, rows,
        "l" + "r" * len(pair_names), note,
    )  # fmt: skip


def _ragas_agreement_table(results: dict) -> str:
    header = ["Gruppe", "Spearmans ρ", "n"]
    rows: list[list[str] | str] = []
    for pair, per in results["ragas_agreement"].items():
        metric, column = pair.split("~")
        label = f"{RAGAS_LABELS[metric]} und {RAGAS_PAIR_LABELS[column]}"
        rows.append(_group(label, len(header), not rows))
        if not any(c["testable"] for c in per.values()):
            rows.append(["gesamt und je Strategie", NOT_DETERMINABLE, str(per["pooled"]["n"])])
            continue
        for group, c in per.items():
            shown = "gesamt" if group == "pooled" else group
            rho = fmt_opt(c["rho"]) if c["testable"] else NOT_DETERMINABLE
            rows.append([shown, rho, str(c["n"])])
    note = (
        "Deskriptiv, ohne p-Werte. Spearmans ρ je Antwort zwischen RAGAS-Metrik und Bewertung "
        "bzw. Retrieval (Hauptregel), je Strategie und über alle Strategien (gesamt: jede Frage "
        "dreifach). Fragen ohne RAGAS-Wert entfallen im jeweiligen Paar; „nicht bestimmbar“: "
        "eine Seite ist konstant."
    )
    return latex_table(
        "ragas_agreement", "Übereinstimmung von RAGAS mit Bewertung und Retrieval", header, rows,
        "lrr", note,
    )  # fmt: skip


def _with_interval(value: float | None, ci: dict) -> str:
    if value is None:
        return NOT_DETERMINABLE
    if ci["low"] is None:
        return fmt_de(value, REPORT_DECIMALS)
    low, high = (fmt_de(ci[k], REPORT_DECIMALS) for k in ("low", "high"))
    return f"{fmt_de(value, REPORT_DECIMALS)} [{low}; {high}]"


def _agreement_table(results: dict) -> str:
    block = results["agreement"]
    header = ["Merkmal", "n", "Übereinstimmung", "AC1/AC2 [KI]", "α [KI]"]
    rows: list[list[str] | str] = []
    group = None
    for r in block["rows"]:
        if r["group"] != group:
            group = r["group"]
            rows.append(_group(group, len(header), not rows))
        label = CHECK_LABELS.get(r["label"]) or CRITERION_LABELS.get(r["label"]) or r["label"]
        rows.append(
            [
                f"{label} ({r['measure']})", str(r["n"]), fmt_de(r["agreement"], REPORT_DECIMALS),
                _with_interval(r["ac"], r["ac_ci"]), _with_interval(r["alpha"], r["alpha_ci"]),
            ]
        )  # fmt: skip
    dropped = max(r["dropped"] for r in block["rows"])
    level = round(block["level"] * 100)
    note = (
        f"Erst- und Zweitbewertung derselben {block['n_codes']} Antworten ({block['n_questions']} "
        "Fragen, je C1 bis C3). n: Antworten, bei den Kernpunkten alle Kernpunkt-Markierungen. "
        "AC1: Gwets Koeffizient für Ja/Nein-Prüffragen und Kernpunkte, AC2: mit ordinalen "
        "Gewichten für „Durch Passagen gestützt“, „Halluzination“ und die Kriterien. α: "
        "Krippendorffs Alpha, "
        f"ordinal. Intervalle: Perzentil-Bootstrap über die Fragen ({block['reps']} "
        f"Wiederholungen, {level} %-Niveau)."
        + (
            f" Bei α blieben bis zu {dropped} Stichproben unberücksichtigt, in denen α nicht "
            "bestimmbar war."
            if dropped
            else ""
        )
        + (
            f" „{NOT_DETERMINABLE}“: beide Personen vergaben nur eine Kategorie."
            if any(r["alpha"] is None for r in block["rows"])
            else ""
        )
    )
    return latex_table(
        "agreement", "Übereinstimmung der Erst- und Zweitbewertung", header, rows, "lrrrr", note
    )


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
    note = (
        "Ohne zusammengefasste Kennzahl. Indexgröße und Embedding einmalig, Generierung je "
        "Antwort; K1 nur Retrieval, K0 nur Generierung."
    )
    return latex_table(
        "efficiency", "Aufwand und Kosten je Strategie", ["Kennzahl", *strategies], rows,
        "l" + "r" * len(strategies), note,
    )  # fmt: skip


def _breakdown_table(results: dict) -> str:
    """Groups (question type, construction class, verdict) as headings; per strategy the answer
    total and R@5 under a shared column heading."""
    n = len(STRATEGY_IDS)
    columns = 2 + 2 * n
    spans = " & ".join(rf"\multicolumn{{2}}{{c}}{{{s}}}" for s in STRATEGY_IDS)
    rules = "".join(rf"\cmidrule(lr){{{3 + 2 * i}-{4 + 2 * i}}}" for i in range(n))
    header = (
        rf"& & {spans} \\" + "\n" + rules + "\n"
        + " & ".join(["Gruppe", "n", *(["Antwort", "R@5"] * n)]) + r" \\"
    )  # fmt: skip
    rows: list[list[str] | str] = []
    for group, levels in results["breakdown"].items():
        rows.append(_group(GROUPS[group], columns, not rows))
        for level, v in levels.items():
            shown = VERDICT_LABELS.get(level, level) if group == "verdict" else level
            row = [shown, str(v["n"])]
            for s in STRATEGY_IDS:
                row += [
                    fmt_de(v["total_score"][s], REPORT_DECIMALS),
                    fmt_de(v["recall"][s], REPORT_DECIMALS),
                ]
            rows.append(row)
    note = (
        "Antwort: Gesamtwert der Antwort; R@5 nach der Hauptregel. Rein deskriptiv: je Gruppe zu "
        "wenige Fragen für Tests."
    )
    return latex_table(
        "breakdown", "Antwortqualität und R@5 je Fragegruppe", header, rows,
        "lr" + "r" * (2 * n), note,
    )  # fmt: skip


def write_tables(results: dict, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "retrieval.tex": lambda: _retrieval_table(
            results,
            ANALYSIS_RULE,
            "retrieval",
            "Retrieval-Qualität je Strategie (Hauptregel der Relevanz)",
            "Mittelwerte über alle Fragen; K1 ist die Kontrolle mit gleich langen Fenstern.",
        ),
        "retrieval_sensitivity.tex": lambda: _retrieval_table(
            results,
            "sensitivity",
            "retrieval_sensitivity",
            "Retrieval-Qualität je Strategie (Sensitivitätsregel der Relevanz)",
            "Mittelwerte über alle Fragen.",
        ),
        "answers.tex": lambda: _answers_table(results),
        "tests.tex": lambda: _tests_table(results),
        "tests_descriptive.tex": lambda: _tests_descriptive_table(results),
        "control_k0.tex": lambda: _k0_table(results),
        "correlation.tex": lambda: _correlation_table(results),
        "efficiency.tex": lambda: _efficiency_table(results),
        "breakdown.tex": lambda: _breakdown_table(results),
        "ragas.tex": lambda: _ragas_table(results),
        "ragas_effects.tex": lambda: _ragas_effects_table(results),
        "ragas_agreement.tex": lambda: _ragas_agreement_table(results),
        "agreement.tex": lambda: _agreement_table(results),
    }
    skipped = {
        "control_k0.tex": "control_k0", "efficiency.tex": "efficiency",
        "ragas.tex": "ragas", "ragas_effects.tex": "ragas",
        "ragas_agreement.tex": "ragas_agreement", "agreement.tex": "agreement",
    }  # fmt: skip
    written = []
    for name in TABLE_NAMES:
        path = out_dir / name
        if skipped.get(name) and results.get(skipped[name]) is None:
            path.unlink(missing_ok=True)  # no stale table from an earlier run
            continue
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
