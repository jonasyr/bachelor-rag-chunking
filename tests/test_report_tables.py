import json
import re
from dataclasses import replace

import pandas as pd
import pytest

from analysis_data import AnalysisData
from config import CONTROL_CRITERIA, RUBRIC_CRITERIA, RUBRIC_RULES_VERSION
from report_tables import (
    TABLE_NAMES,
    build_results,
    fmt_de,
    latex_escape,
    latex_table,
    write_json,
    write_tables,
)

RULES = RUBRIC_RULES_VERSION
QIDS = [f"Q{i:03d}" for i in range(1, 13)]
C = ["C1", "C2", "C3"]


def make_data(*, verdicts=True, chunks=True, embedding=True, control=True) -> AnalysisData:
    types = ["factual", "procedural", "conceptual"]
    questions = pd.DataFrame(
        {
            "question_id": QIDS,
            "type": [types[i % 3] for i in range(len(QIDS))],
            "difficulty": ["single" if i % 2 else "multi_hop" for i in range(len(QIDS))],
        }
    )
    rows = []
    for i, q in enumerate(QIDS):
        for s_i, s in enumerate([*C, "K1"]):
            for rule in ("main", "sensitivity"):
                rows.append(
                    {
                        "question_id": q, "strategy": s, "rule": rule,
                        "hit": str(int((i + s_i) % 3 != 0)),
                        "reciprocal_rank": f"{1 / (1 + (i * (s_i + 1)) % 4):.6f}",
                        "precision": f"{((i + s_i) % 5) / 5:.6f}",
                        "recall": f"{((i * (s_i + 1)) % 4) / 3:.6f}",
                        "context_tokens": str(900 + 10 * i + 50 * s_i),
                    }
                )  # fmt: skip
    scores = []
    for i, q in enumerate(QIDS):
        for s_i, s in enumerate(C):
            crit = {c: str((i + s_i + k) % 3) for k, c in enumerate(RUBRIC_CRITERIA)}
            total = sum(int(v) for v in crit.values()) / len(crit)
            scores.append({"question_id": q, "strategy": s, **crit, "total_score": str(total)})
    scores_control = None
    if control:
        rows_k = []
        for i, q in enumerate(QIDS):
            crit = {c: str((i + k) % 2) for k, c in enumerate(CONTROL_CRITERIA)}
            total = sum(int(v) for v in crit.values()) / len(crit)
            rows_k.append({"question_id": q, "strategy": "K0", **crit, "total_score": str(total)})
        scores_control = pd.DataFrame(rows_k)
    return AnalysisData(
        questions=questions,
        retrieval=pd.DataFrame(rows),
        scores=pd.DataFrame(scores),
        scores_control=scores_control,
        verdicts={q: ("dependent" if i % 2 else "known") for i, q in enumerate(QIDS)}
        if verdicts
        else None,
        chunks={"C1": [500] * 10, "C2": [500] * 12, "C3": [300, 400, 800], "K1": [375] * 14}
        if chunks
        else None,
        embedding={
            k: {
                "input_tokens": 5000 + i,
                "cost_usd": 0.00065,
                "vector_bytes": 3_000_000,
                "vectors": 10,
            }
            for i, k in enumerate([*C, "K1"])
        }
        if embedding
        else None,
        generation={
            k: {"prompt_tokens": 12000, "completion_tokens": 600, "cost_usd": 0.0015}
            for k in [*C, "K0"]
        },
        notes=["Vorab-Hinweis"],
    )


def test_german_number_format():
    assert fmt_de(0.9375, 2) == "0,94"
    assert fmt_de(-0.05, 2) == "\u22120,05"  # typographic minus
    assert fmt_de(1, 2) == "1,00"
    assert fmt_de(-0.001, 2) == "0,00"


def test_latex_escapes_special_characters():
    assert latex_escape("a_b & 5%") == r"a\_b \& 5\%"


def test_table_has_booktabs_and_label():
    tex = latex_table("retrieval", "Beschriftung", ["A", "B"], [["1", "2"]], "lr")
    assert r"\toprule" in tex and r"\midrule" in tex and r"\bottomrule" in tex
    assert r"\label{tab:retrieval}" in tex
    assert r"\hline" not in tex
    assert tex.endswith("\n")


def test_results_are_json_serialisable():
    results = build_results(make_data(), 0.05)
    json.dumps(results)
    for key in ("retrieval", "answers", "confirmatory", "descriptive_effects", "control_k0",
                "correlation", "efficiency", "breakdown", "notes"):  # fmt: skip
        assert key in results
    assert "Vorab-Hinweis" in results["notes"]


def test_tests_table_holds_only_the_confirmatory_tests(tmp_path):
    """The descriptive effects have their own (appendix) table, so tests.tex stays short."""
    write_tables(build_results(make_data(), 0.05), tmp_path)
    tests = (tmp_path / "tests.tex").read_text(encoding="utf-8")
    assert "deskriptiv" not in tests.split(r"\end{tabular}")[0]
    for label in ("R@5", "MRR", "Gesamtwert"):
        assert rf"{{{label}}}" in tests
    desc = (tmp_path / "tests_descriptive.tex").read_text(encoding="utf-8")
    assert r"\caption{Deskriptive Effektstärken der Strategien C1 bis C3}" in desc
    assert r"\label{tab:tests_descriptive}" in desc
    # Kontext@5 differs in tokens, not in score points
    assert "Kontext@5 (Tokens)" in desc


def test_tests_table_has_no_pvalues_for_descriptive_metrics(tmp_path):
    results = build_results(make_data(), 0.05)
    write_tables(results, tmp_path)
    text = (tmp_path / "tests_descriptive.tex").read_text(encoding="utf-8")
    # no test, so no columns for statistic and p-values that would only hold dashes
    assert "Vergleich & Effekt & Median-Differenz" in text and "p (Holm)" not in text
    align = text.split(r"\begin{tabular}{")[1].split("}")[0]
    assert align == "lrr"
    groups = [line.split("{")[-1].split("}")[0] for line in text.splitlines()
              if line.startswith(r"\multicolumn")]  # fmt: skip
    assert any(g.startswith("Hit@5") for g in groups)


def test_tables_follow_the_iu_rules(tmp_path):
    """Short title without final period above, no centering, source line below (ZL S. 19)."""
    paths = write_tables(build_results(make_data(), 0.05), tmp_path)
    for path in paths:
        text = path.read_text(encoding="utf-8")
        caption = next(line for line in text.splitlines() if line.startswith(r"\caption{"))
        title = caption[len(r"\caption{") : caption.index("}")]
        assert not title.endswith("."), path.name
        assert len(title) <= 80, path.name  # one line in the list of tables
        assert r"\centering" not in text
        assert r"\source{Eigene Darstellung." in text.split(r"\end{tabular}")[1]


def test_wide_tables_are_transposed(tmp_path):
    """At most five data columns, so the tables fit the text width (paperlab check `rand`)."""
    write_tables(build_results(make_data(), 0.05), tmp_path)
    for name in ("answers.tex", "control_k0.tex"):
        text = (tmp_path / name).read_text(encoding="utf-8")
        align = text.split(r"\begin{tabular}{")[1].split("}")[0]
        assert len(align) <= 5, (name, align)
    breakdown = (tmp_path / "breakdown.tex").read_text(encoding="utf-8")
    assert r"\cmidrule" in breakdown and "Fragetyp & " not in breakdown


def test_descriptive_metrics_have_no_p_in_results():
    results = build_results(make_data(), 0.05)
    flat = json.dumps(results["descriptive_effects"])
    assert '"p"' not in flat and '"p_adj"' not in flat
    flat_k0 = json.dumps(results["control_k0"])
    assert '"p"' not in flat_k0


def test_all_tables_are_written(tmp_path):
    data = agreement_data()
    data = replace(
        data, repeat_rating=data.second_rating, llm_rating=data.second_rating | {"model": "judge-x"}
    )
    paths = write_tables(build_results(hybrid_data(data), 0.05), tmp_path)
    assert len(TABLE_NAMES) == 17
    assert sorted(p.name for p in paths) == sorted(TABLE_NAMES)
    for p in paths:
        text = p.read_text(encoding="utf-8")
        assert r"\hline" not in text and r"\label{tab:" + p.stem + "}" in text


def test_captions_name_the_kind_of_test(tmp_path):
    """The three primary tests are confirmatory, the correlations exploratory (ADR 0044)."""
    write_tables(build_results(make_data(), 0.05), tmp_path)
    tests = (tmp_path / "tests.tex").read_text(encoding="utf-8").lower()
    assert "konfirmatorisch" in tests and "explorativ" not in tests
    assert "explorativ" in (tmp_path / "correlation.tex").read_text(encoding="utf-8").lower()


def test_outputs_are_byte_identical_on_rerun(tmp_path):
    outs = []
    for run in ("a", "b"):
        results = build_results(make_data(), 0.05)
        d = tmp_path / run
        write_tables(results, d)
        write_json(results, d / "analysis.json")
        outs.append({p.name: p.read_bytes() for p in d.iterdir()})
    assert outs[0] == outs[1]


def test_write_json_format(tmp_path):
    path = tmp_path / "analysis.json"
    write_json({"b": 1.123456789, "a": [1, None]}, path)
    text = path.read_text(encoding="utf-8")
    assert text == '{\n  "a": [\n    1,\n    null\n  ],\n  "b": 1.123457\n}\n'


def test_missing_inputs_skip_tables_with_note(tmp_path):
    data = make_data(verdicts=False, chunks=False, control=False)
    results = build_results(data, 0.05)
    assert results["control_k0"] is None and results["efficiency"] is None
    assert any("K0" in n for n in results["notes"])
    assert any("Effizienz" in n for n in results["notes"])
    paths = write_tables(results, tmp_path)
    names = {p.name for p in paths}
    assert "control_k0.tex" not in names and "efficiency.tex" not in names
    assert "breakdown.tex" in names  # type and class remain


def test_skipped_tables_remove_stale_files(tmp_path):
    for name in ("control_k0.tex", "agreement.tex", "agreement_intra.tex", "agreement_llm.tex"):
        (tmp_path / name).write_text("stale", encoding="utf-8")
    write_tables(build_results(make_data(control=False), 0.05), tmp_path)
    assert not (tmp_path / "control_k0.tex").exists()
    assert not (tmp_path / "agreement.tex").exists()
    assert not (tmp_path / "agreement_intra.tex").exists()
    assert not (tmp_path / "agreement_llm.tex").exists()


def test_gating_pairs_only_for_significant_metric():
    results = build_results(make_data(), 0.05)
    for r in results["confirmatory"].values():
        assert ("pairs" in r) == r["significant"]


def test_labels_are_escaped(tmp_path):
    data = make_data()
    data.questions["type"] = "multi_part"
    write_tables(build_results(data, 0.05), tmp_path)
    assert r"multi\_part" in (tmp_path / "breakdown.tex").read_text(encoding="utf-8")


def test_constant_metric_does_not_crash(tmp_path):
    data = make_data()
    data.scores.loc[:, RUBRIC_CRITERIA + ["total_score"]] = "2"
    results = build_results(data, 0.05)
    assert results["confirmatory"]["total_score"]["testable"] is False
    write_tables(results, tmp_path)
    assert "nan" not in (tmp_path / "tests.tex").read_text(encoding="utf-8").lower()


def test_pooled_spearman_has_no_pvalue(tmp_path):
    """Pooled pairs repeat each question three times (not independent): rho only, no p."""
    results = build_results(make_data(), 0.05)
    for per in results["correlation"].values():
        assert "p" not in per["pooled"]
        assert all("p" in per[s] for s in C if per[s]["testable"])
    write_tables(results, tmp_path)
    pooled = [
        line
        for line in (tmp_path / "correlation.tex").read_text(encoding="utf-8").splitlines()
        if line.startswith("gesamt &")
    ]
    assert len(pooled) == 2 and all(line.split(" & ")[2] == "--" for line in pooled)


def test_missing_effect_is_a_dash_not_r_equals_dash():
    """A constant criterion (all answers 2) has no r; the cell shows a dash, not "r = --"."""
    from report_tables import _r

    assert _r(None) == "--"
    assert _r(0.5) == "r = 0,50"


# ---------------------------------------------------------------- RAGAS (ADR 0047)

METRICS = ("faithfulness", "response_relevancy", "context_precision", "context_recall")


def ragas_frame(nan=(), shift=0.0) -> pd.DataFrame:
    """One row per question and strategy; `nan` lists (question, strategy, metric) left empty."""
    rows = []
    for i, q in enumerate(QIDS):
        for s_i, s in enumerate(C):
            row = {"question_id": q, "strategy": s, "nan_reasons": ""}
            for m_i, m in enumerate(METRICS):
                value = ((i * (m_i + 2) + s_i * 3) % 7) / 8 + shift
                missing = (q, s, m) in nan
                row[m] = "" if missing else f"{value:.6f}"
                if missing:
                    row["nan_reasons"] = f"{m}: Grund"
            rows.append(row)
    return pd.DataFrame(rows)


def answers_question(constant=False) -> dict:
    return {
        (q, s): 1 if constant or (i + s_i) % 4 else 0
        for i, q in enumerate(QIDS) for s_i, s in enumerate(C)
    }  # fmt: skip


def ragas_data(nan=(), constant=False, repeat=False):
    return replace(
        make_data(),
        ragas=ragas_frame(nan),
        ragas_repeat=ragas_frame(nan, shift=0.01) if repeat else None,
        answers_question=answers_question(constant),
    )


def test_ragas_nan_handling():
    nan = {("Q003", "C2", "faithfulness")}
    results = build_results(ragas_data(nan), 0.05)
    block = results["ragas"]
    assert block["nan_counts"]["C2"]["faithfulness"] == 1
    assert block["nan_counts"]["C1"]["faithfulness"] == 0
    frame = ragas_frame(nan)
    rest = pd.to_numeric(
        frame[(frame["strategy"] == "C2") & (frame["question_id"] != "Q003")]["faithfulness"]
    )
    assert block["means"]["C2"]["faithfulness"] == pytest.approx(rest.mean(), abs=1e-6)
    assert block["effects"]["faithfulness"]["n"] == len(QIDS) - 1  # complete questions only
    assert block["effects"]["context_recall"]["n"] == len(QIDS)
    full = build_results(ragas_data(), 0.05)["ragas_agreement"]
    cut = results["ragas_agreement"]
    pair = "faithfulness~groundedness"
    assert cut[pair]["pooled"]["n"] == full[pair]["pooled"]["n"] - 1
    assert cut[pair]["C2"]["n"] == len(QIDS) - 1 and cut[pair]["C1"]["n"] == len(QIDS)


def test_ragas_agreement_pairs_and_pooled_rho_without_p():
    results = build_results(ragas_data(), 0.05)
    agreement = results["ragas_agreement"]
    assert list(agreement) == [
        "faithfulness~groundedness", "faithfulness~no_hallucination",
        "response_relevancy~answers_question", "context_precision~precision",
        "context_recall~recall",
    ]  # fmt: skip
    for per in agreement.values():
        # descriptive throughout (ADR 0047, spec non-goals): no p-value, pooled or per strategy
        assert all("p" not in c for c in per.values()) and set(per) == {"pooled", *C}
        assert per["pooled"]["n"] == len(QIDS) * 3


def test_ragas_tables_follow_the_iu_rules(tmp_path):
    nan = {("Q003", "C2", "faithfulness")}
    paths = write_tables(build_results(ragas_data(nan), 0.05), tmp_path)
    names = {p.name for p in paths}
    assert {"ragas.tex", "ragas_effects.tex", "ragas_agreement.tex"} <= names
    titles = {
        "ragas.tex": "RAGAS-Bewertung je Strategie",
        "ragas_effects.tex": "Paarweise Effekte der RAGAS-Metriken",
        "ragas_agreement.tex": "Übereinstimmung von RAGAS mit Bewertung und Retrieval",
    }
    for name, title in titles.items():
        text = (tmp_path / name).read_text(encoding="utf-8")
        assert rf"\caption{{{title}}}" in text and r"\centering" not in text
        tail = text.split(r"\end{tabular}")[1]
        assert r"\source{Eigene Darstellung." in tail
        align = text.split(r"\begin{tabular}{")[1].split("}")[0]
        assert len(align) <= 5, (name, align)
    note = (tmp_path / "ragas.tex").read_text(encoding="utf-8").split(r"\end{tabular}")[1]
    assert "NaN" in note and "Faithfulness C2: 1" in note
    pooled = [
        line
        for line in (tmp_path / "ragas_agreement.tex").read_text(encoding="utf-8").splitlines()
        if line.startswith("gesamt &")
    ]
    agreement = (tmp_path / "ragas_agreement.tex").read_text(encoding="utf-8")
    assert len(pooled) == 5 and "Spearmans ρ & n" in agreement and " & p & " not in agreement
    means = (tmp_path / "ragas.tex").read_text(encoding="utf-8")
    assert "n′" not in means and "Kendalls W" in means  # pairwise block moved out
    effects = (tmp_path / "ragas_effects.tex").read_text(encoding="utf-8")
    # r rests on the differences not equal to 0; with heavy ties n' can be tiny, so it is shown
    assert "n′ = " in effects and "C1–C2" in effects


def test_ragas_tables_skipped_without_ragas(tmp_path):
    results = build_results(make_data(), 0.05)
    assert results["ragas"] is None and results["ragas_agreement"] is None
    names = {p.name for p in write_tables(results, tmp_path)}
    assert not {"ragas.tex", "ragas_effects.tex", "ragas_agreement.tex"} & names


def test_ragas_agreement_without_checks_drops_that_pair():
    results = build_results(replace(ragas_data(), answers_question=None), 0.05)
    assert "response_relevancy~answers_question" not in results["ragas_agreement"]
    assert any("answers_question" in n for n in results["notes"])


def test_constant_side_is_not_determinable(tmp_path):
    """All answers answer the question (pilot e2e: 48 of 48 yes): rho cannot be computed."""
    results = build_results(ragas_data(constant=True), 0.05)
    per = results["ragas_agreement"]["response_relevancy~answers_question"]
    assert all(per[k]["rho"] is None and per[k]["testable"] is False for k in per)
    write_tables(results, tmp_path)
    text = (tmp_path / "ragas_agreement.tex").read_text(encoding="utf-8")
    assert "nicht bestimmbar" in text and "nan" not in text.lower()
    # a pair that no group can determine collapses into one row instead of one per group
    block = text.split("Response Relevancy und")[1].split(r"\multicolumn")[0]
    rows = [line for line in block.splitlines() if "&" in line]
    assert rows == [rf"gesamt und je Strategie & nicht bestimmbar & {len(QIDS) * 3} \\"]


def test_ragas_stability_from_repeat():
    results = build_results(ragas_data(repeat=True), 0.05)
    st = results["ragas_stability"]
    assert set(st) == set(METRICS)
    for m in METRICS:
        assert st[m]["mean_abs_diff"] == pytest.approx(0.01, abs=1e-6)
        assert st[m]["share_equal"] == 0.0 and st[m]["n"] == len(QIDS) * 3
        assert st[m]["rho"] == pytest.approx(1.0)
    assert "ragas_stability" not in build_results(ragas_data(), 0.05)


def test_ragas_outputs_are_byte_identical_on_rerun(tmp_path):
    outs = []
    for run in ("a", "b"):
        results = build_results(ragas_data({("Q001", "C1", "context_recall")}, repeat=True), 0.05)
        write_tables(results, tmp_path / run)
        write_json(results, tmp_path / run / "analysis.json")
        outs.append({p.name: p.read_bytes() for p in (tmp_path / run).iterdir()})
    assert outs[0] == outs[1]


# ---------------------------------------------------------------- agreement (ADR 0046)


def agreement_data(constant=False):
    import agreement
    from scoring_rules import CHECKS

    codes = [f"{q}-{s}" for q in QIDS for s in "ABC"]
    base = {c: v[0] for c, v in CHECKS.items()}
    first_checks, second_checks, sheet = [], [], []
    for i, code in enumerate(codes):
        row = {"code": code, "rules_version": RULES, "points": "covered;missing"} | base
        other = dict(row)
        if not constant and i % 4 == 0:
            other["direct"] = "no" if row["direct"] == "yes" else "yes"
            other["grounded"] = "none"
        first_checks.append(row)
        second_checks.append(other)
        sheet.append(
            {"code": code, "question_id": code.split("-")[0], "notes": ""}
            | {c: str((i + k) % 3) for k, c in enumerate(RUBRIC_CRITERIA)}
        )
    other_sheet = [dict(r) for r in sheet]
    if not constant:
        for r in other_sheet[::5]:
            r["clarity"] = str((int(r["clarity"]) + 1) % 3)
    paired = agreement.pair(first_checks, sheet, second_checks, other_sheet)
    second = {"checks": second_checks, "sheet": other_sheet, "paired": paired}
    return replace(ragas_data(), second_rating=second)


def test_agreement_table_iu_rules(tmp_path, monkeypatch):
    import agreement

    monkeypatch.setattr(agreement, "AGREEMENT_BOOTSTRAP_REPS", 100)
    write_tables(build_results(agreement_data(), 0.05), tmp_path)
    text = (tmp_path / "agreement.tex").read_text(encoding="utf-8")
    caption = next(line for line in text.splitlines() if line.startswith(r"\caption{"))
    assert "Übereinstimmung der Erst- und Zweitbewertung" in caption and not caption.endswith(".}")
    assert r"\label{tab:agreement}" in text and r"\hline" not in text
    assert r"\source{Eigene Darstellung." in text.split(r"\end{tabular}")[1]
    assert re.search(r"\d,\d\d", text) and not re.search(r"\d\.\d", text)  # decimal comma
    for word in ("Prüffragen", "Kernpunkte", "Kriterien", "AC1", "AC2", "ordinal", "Bootstrap"):
        assert word in text
    assert "100 Wiederholungen" in text
    note = text.split(r"\end{tabular}")[1]
    assert (
        "„Durch Passagen gestützt“" in note and "Quellenbezug" not in note
    )  # check, not criterion
    align = text.split(r"\begin{tabular}{")[1].split("}")[0]
    assert len(align) <= 5


def test_agreement_table_marks_undefined_alpha(tmp_path, monkeypatch):
    import agreement
    from report_tables import NOT_DETERMINABLE

    monkeypatch.setattr(agreement, "AGREEMENT_BOOTSTRAP_REPS", 50)
    results = build_results(agreement_data(constant=True), 0.05)
    row = next(r for r in results["agreement"]["rows"] if r["label"] == "declines")
    assert row["alpha"] is None and row["ac"] == 1.0
    write_tables(results, tmp_path)
    text = (tmp_path / "agreement.tex").read_text(encoding="utf-8")
    assert NOT_DETERMINABLE in text


def test_agreement_skipped_without_second_rating(tmp_path):
    results = build_results(make_data(), 0.05)
    assert results["agreement"] is None
    paths = write_tables(results, tmp_path)
    assert "agreement.tex" not in {p.name for p in paths}


def test_differences_have_intervals_for_every_pair_without_gating():
    """The bootstrap intervals exist whether or not the omnibus test is significant (ADR 0044)."""
    results = build_results(make_data(), 1e-9)  # nothing significant
    diffs = results["differences"]
    assert list(diffs) == ["recall", "reciprocal_rank", "total_score"]
    for d in diffs.values():
        assert list(d["pairs"]) == ["C1-C2", "C1-C3", "C2-C3"]
        for p in d["pairs"].values():
            assert p["low"] <= p["mean_diff"] <= p["high"]
            assert p["n"] == len(QIDS)


def test_differences_table(tmp_path):
    write_tables(build_results(make_data(), 0.05), tmp_path)
    tex = (tmp_path / "differences.tex").read_text(encoding="utf-8")
    assert r"\label{tab:differences}" in tex
    for label in ("R@5", "MRR", "Gesamtwert"):
        assert rf"{{{label}}}" in tex
    assert "Bootstrap" in tex and "erste minus zweite" in tex


def test_agreement_table_unchanged_for_r2(tmp_path, monkeypatch):
    """The R2 table is byte-identical to what the code wrote before the repeat rating existed."""
    import hashlib

    import agreement

    monkeypatch.setattr(agreement, "AGREEMENT_BOOTSTRAP_REPS", 100)
    write_tables(build_results(agreement_data(), 0.05), tmp_path)
    digest = hashlib.sha256((tmp_path / "agreement.tex").read_bytes()).hexdigest()
    assert digest == "69e19423ff7ab2af0d0f9b02dd379512879c0accfdfbf86e64584977d76105b5"
    assert not (tmp_path / "agreement_intra.tex").exists()


def test_agreement_intra_table_from_repeat_rating(tmp_path, monkeypatch):
    import agreement

    monkeypatch.setattr(agreement, "AGREEMENT_BOOTSTRAP_REPS", 100)
    data = agreement_data()
    results = build_results(replace(data, repeat_rating=data.second_rating), 0.05)
    assert results["agreement_intra"]["rows"] == results["agreement"]["rows"]
    write_tables(results, tmp_path)
    text = (tmp_path / "agreement_intra.tex").read_text(encoding="utf-8")
    assert r"\label{tab:agreement_intra}" in text
    assert "Übereinstimmung der Erst- und Wiederholungsbewertung" in text
    assert "durch dieselbe Person (mindestens 14 Tage Abstand, neu gemischte Codes)" in text


def test_agreement_llm_table_written(tmp_path, monkeypatch):
    import agreement

    monkeypatch.setattr(agreement, "AGREEMENT_BOOTSTRAP_REPS", 100)
    data = agreement_data()
    llm = data.second_rating | {"model": "judge-x", "answers": len(data.second_rating["paired"])}
    results = build_results(replace(data, llm_rating=llm), 0.05)
    assert results["agreement_llm"]["rows"] == results["agreement"]["rows"]
    assert results["agreement_intra"] is None
    write_tables(results, tmp_path)
    text = (tmp_path / "agreement_llm.tex").read_text(encoding="utf-8")
    assert r"\label{tab:agreement_llm}" in text
    assert "Übereinstimmung der Bewertung mit der LLM-Gegenprobe" in text
    assert "judge-x" in text and f"{llm['answers']} Antworten" in text
    assert not (tmp_path / "agreement_intra.tex").exists()


# ---------------------------------------------------------------- hybrid scoring (ADR 0051)

HUMAN = QIDS[:6]  # Jonas' questions in the hybrid fixture


def hybrid_data(base: AnalysisData | None = None) -> AnalysisData:
    """Mixed `scores` (Jonas' values on HUMAN, the LLM's on the rest, `rater` per row) and the
    LLM's values of every answer; on HUMAN the LLM rates one point higher (capped at 2), so the
    mixed and the LLM-only set differ."""
    base = base or make_data()
    llm_rows, mixed_rows = [], []
    for r in base.scores.to_dict("records"):
        human = r["question_id"] in HUMAN
        crit = {c: str(min(2, int(r[c]) + 1)) if human else r[c] for c in RUBRIC_CRITERIA}
        total = sum(int(v) for v in crit.values()) / len(crit)
        llm = {**r, **crit, "total_score": str(total)}
        llm_rows.append(llm)
        mixed_rows.append({**(r if human else llm), "rater": "human" if human else "llm"})
    return replace(
        base,
        scores=pd.DataFrame(mixed_rows),
        scores_llm=pd.DataFrame(llm_rows),
        human_questions=list(HUMAN),
    )


def _means(frame: pd.DataFrame, qids: list[str]) -> dict:
    sub = frame[frame["question_id"].isin(qids)]
    cols = [*RUBRIC_CRITERIA, "total_score"]
    return {
        s: {c: float(pd.to_numeric(sub[sub["strategy"] == s][c]).mean()) for c in cols} for s in C
    }


def test_hybrid_sensitivity_blocks():
    data = hybrid_data()
    hyb = build_results(data, 0.05)["hybrid"]
    assert hyb["n_human_questions"] == len(HUMAN)
    assert hyb["n_llm_questions"] == len(QIDS) - len(HUMAN)
    assert hyb["raters"] == {"human": len(HUMAN) * 3, "llm": (len(QIDS) - len(HUMAN)) * 3}
    human, llm = hyb["sensitivity"]["human"], hyb["sensitivity"]["llm"]
    assert human["n_questions"] == len(HUMAN) and llm["n_questions"] == len(QIDS)
    for block, expected in (
        (human, _means(data.scores, HUMAN)),
        (llm, _means(data.scores_llm, QIDS)),
    ):
        for s in C:
            for c, v in expected[s].items():
                assert block["means"][s][c] == pytest.approx(v)
        assert block["test"]["n"] == block["n_questions"]
        assert "significant" in block["test"] and "p_adj" in block["test"]
        assert set(block["differences"]) == {"C1-C2", "C1-C3", "C2-C3"}
        assert block["descriptive"] is True
    d = llm["differences"]["C1-C2"]["mean_diff"]
    assert d == pytest.approx(llm["means"]["C1"]["total_score"] - llm["means"]["C2"]["total_score"])
    # the mixed means stay those of `scores`, and the confirmatory family is unchanged
    results = build_results(data, 0.05)
    mixed = _means(data.scores, QIDS)
    assert results["answers"]["means"]["C1"]["total_score"] == pytest.approx(
        mixed["C1"]["total_score"]
    )
    assert set(results["confirmatory"]) == {"recall", "reciprocal_rank", "total_score"}


def test_hybrid_k0_uses_llm_side():
    data = hybrid_data()
    results = build_results(data, 0.05)
    k0 = pd.to_numeric(data.scores_control[CONTROL_CRITERIA].stack()).groupby(level=0).mean()
    k0_mean = float(k0.mean())
    for s in C:
        llm = data.scores_llm[data.scores_llm["strategy"] == s]
        llm_four = float(llm[CONTROL_CRITERIA].apply(pd.to_numeric).mean(axis=1).mean())
        mixed = data.scores[data.scores["strategy"] == s]
        mixed_four = float(mixed[CONTROL_CRITERIA].apply(pd.to_numeric).mean(axis=1).mean())
        assert llm_four != pytest.approx(mixed_four)  # the fixture separates the two sides
        diff = results["control_k0"][s]["diff"]
        assert diff["total_four"] == pytest.approx(llm_four - k0_mean)
        for c in CONTROL_CRITERIA:
            assert diff[c] == pytest.approx(
                float(pd.to_numeric(llm[c]).mean())
                - float(pd.to_numeric(data.scores_control[c]).mean())
            )
    # the answers table keeps the mixed set for C1-C3
    mixed_c1 = data.scores[data.scores["strategy"] == "C1"]
    assert results["answers"]["means"]["C1"]["total_four"] == pytest.approx(
        float(mixed_c1[CONTROL_CRITERIA].apply(pd.to_numeric).mean(axis=1).mean())
    )
    # the effect compares the LLM's C1 with K0, question by question
    import stats

    llm_c1 = data.scores_llm[data.scores_llm["strategy"] == "C1"].set_index("question_id")
    four = llm_c1[CONTROL_CRITERIA].apply(pd.to_numeric).mean(axis=1)
    k0_four = data.scores_control.set_index("question_id")[CONTROL_CRITERIA]
    k0_four = k0_four.apply(pd.to_numeric).mean(axis=1)
    pair = stats.wilcoxon_pair([float(four[q]) for q in QIDS], [float(k0_four[q]) for q in QIDS])
    assert results["control_k0"]["C1"]["n_nonzero"] == pair["n_nonzero"]
    assert results["control_k0"]["C1"]["r"] == pytest.approx(pair["r"])


# sha256 of the results (without `hybrid` and the hybrid skip note) computed before the hybrid
# analysis existed (commit 9b555d9); a changed digest means the non-hybrid numbers moved.
# To regenerate: `git checkout 9b555d9`, then run with `uv run python` from the repo root:
#   import hashlib, json, sys; from dataclasses import replace; sys.path[:0] = ["src", "tests"]
#   import test_report_tables as t; from report_tables import build_results
#   h = lambda d: hashlib.sha256(json.dumps(build_results(d, 0.05), sort_keys=True).encode())
#   full = t.agreement_data(); full = replace(full, repeat_rating=full.second_rating,
#       llm_rating=full.second_rating | {"model": "judge-x"})
#   for d in (full, t.make_data(verdicts=False, chunks=False, embedding=False, control=False),
#             t.ragas_data(repeat=True)): print(h(d).hexdigest())
NON_HYBRID_DIGESTS = {
    "full": "f2fa8fe9125200fee579eaff2ea7a75cec1b11e7abdc0e18e6f6d236f2e638b4",
    "minimal": "e4861a98d14099397ea9fa64d039bb6fa151c0467cb1be10a96396745fc597a3",
    "ragas_repeat": "316ed8ff1b6ac533133eeb68c0f0b38ef1a1dd31495d415bde1590c1750fdc5d",
}
HYBRID_NOTE = "Tabelle Sensitivität der hybriden Bewertung entfällt: keine hybride Bewertung"


def test_non_hybrid_results_unchanged():
    import hashlib

    full = agreement_data()
    full = replace(
        full, repeat_rating=full.second_rating, llm_rating=full.second_rating | {"model": "judge-x"}
    )
    cases = {
        "full": full,
        "minimal": make_data(verdicts=False, chunks=False, embedding=False, control=False),
        "ragas_repeat": ragas_data(repeat=True),
    }
    for name, data in cases.items():
        results = build_results(data, 0.05)
        assert results.pop("hybrid") is None
        assert results["notes"][-1] == HYBRID_NOTE
        results["notes"] = results["notes"][:-1]
        text = json.dumps(results, sort_keys=True)
        assert hashlib.sha256(text.encode()).hexdigest() == NON_HYBRID_DIGESTS[name], name


def test_write_hybrid_sensitivity_table(tmp_path):
    results = build_results(hybrid_data(), 0.05)
    paths = {p.name for p in write_tables(results, tmp_path / "h")}
    assert "hybrid_sensitivity.tex" in paths
    text = (tmp_path / "h" / "hybrid_sensitivity.tex").read_text(encoding="utf-8")
    assert r"\label{tab:hybrid_sensitivity}" in text
    assert "Sensitivitätsanalyse der hybriden Bewertung (ADR 0051)" in text
    for label in ("gemischt", "nur Jonas' Fragen", "nur Sprachmodell"):
        assert label in text
    assert "beschreibend" in text and r"\hline" not in text
    assert fmt_de(results["hybrid"]["sensitivity"]["llm"]["means"]["C2"]["total_score"], 2) in text
    # not hybrid: no table (a stale one is removed) and a note
    (tmp_path / "n").mkdir()
    (tmp_path / "n" / "hybrid_sensitivity.tex").write_text("stale", encoding="utf-8")
    plain = build_results(make_data(), 0.05)
    assert plain["hybrid"] is None and HYBRID_NOTE in plain["notes"]
    assert "hybrid_sensitivity.tex" not in {p.name for p in write_tables(plain, tmp_path / "n")}
    assert not (tmp_path / "n" / "hybrid_sensitivity.tex").exists()


def test_hybrid_results_in_json(tmp_path):
    results = build_results(hybrid_data(), 0.05)
    write_json(results, tmp_path / "analysis.json")
    loaded = json.loads((tmp_path / "analysis.json").read_text(encoding="utf-8"))
    assert loaded["hybrid"]["n_human_questions"] == len(HUMAN)
    assert set(loaded["hybrid"]["sensitivity"]) == {"human", "llm"}


def test_hybrid_fields_change_only_hybrid_and_k0():
    """At test time: the hybrid fields move only `hybrid`, the K0 comparison and the notes."""
    hyb = hybrid_data()
    h = build_results(hyb, 0.05)
    p = build_results(replace(hyb, scores_llm=None, human_questions=None), 0.05)
    assert set(h) == set(p)
    for key in set(h) - {"hybrid", "control_k0", "notes"}:
        assert h[key] == p[key], key


def test_hybrid_table_shows_holm_adjusted_p(tmp_path):
    results = build_results(hybrid_data(), 0.05)
    results["confirmatory"]["total_score"].update(p=0.02, p_adj=0.06, testable=True)
    for b, (p, p_adj) in zip(
        results["hybrid"]["sensitivity"].values(), ((0.11, 0.21), (0.31, 0.41)), strict=True
    ):
        b["test"].update(p=p, p_adj=p_adj, testable=True)
    write_tables(results, tmp_path)
    text = (tmp_path / "hybrid_sensitivity.tex").read_text(encoding="utf-8")
    assert "p (Friedman, Holm)" in text
    rows = {line.split(" & ")[0]: line.split(" & ") for line in text.splitlines() if " & " in line}
    assert rows["gemischt"][4] == fmt_de(0.06, 3)
    assert rows["nur Jonas' Fragen"][4] == fmt_de(0.21, 3)
    assert rows["nur Sprachmodell"][4] == fmt_de(0.41, 3)
    assert "gemischt: p nach Holm wie in Tabelle tests" in text


def test_hybrid_answers_table_does_not_call_k0_comparable(tmp_path):
    """ADR 0051: K0 is rated only by the LLM, C1-C3 are mixed; answers.tex must not present them
    as comparable and must point to control_k0, which compares on the LLM's values only."""
    write_tables(build_results(hybrid_data(), 0.05), tmp_path)
    text = (tmp_path / "answers.tex").read_text(encoding="utf-8")
    assert "macht K0 mit C1 bis C3 vergleichbar" not in text
    assert "nur vom Sprachmodell" in text and "control" in text
    write_tables(build_results(make_data(), 0.05), tmp_path / "plain")
    plain = (tmp_path / "plain" / "answers.tex").read_text(encoding="utf-8")
    assert "macht K0 mit C1 bis C3 vergleichbar" in plain
