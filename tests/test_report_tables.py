import json

import pandas as pd
import pytest

from analysis_data import AnalysisData
from config import CONTROL_CRITERIA, RUBRIC_CRITERIA
from report_tables import (
    TABLE_NAMES,
    build_results,
    fmt_de,
    latex_escape,
    latex_table,
    write_json,
    write_tables,
)

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
    assert fmt_de(-0.05, 2) == "-0,05"
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


def test_tests_table_has_no_pvalues_for_descriptive_metrics(tmp_path):
    results = build_results(make_data(), 0.05)
    write_tables(results, tmp_path)
    lines = (tmp_path / "tests.tex").read_text(encoding="utf-8").splitlines()
    for line in lines:
        if line.startswith(("Hit@5", "P@5", "Kontext@5", "Korrektheit")):
            cells = [c.strip(" \\") for c in line.split("&")]
            # columns: Metrik, Vergleich, Statistik, p, p (Holm), Effekt, Median-Differenz
            assert cells[3] == "--" and cells[4] == "--", line
    assert any(line.startswith("Hit@5") for line in lines)


def test_descriptive_metrics_have_no_p_in_results():
    results = build_results(make_data(), 0.05)
    flat = json.dumps(results["descriptive_effects"])
    assert '"p"' not in flat and '"p_adj"' not in flat
    flat_k0 = json.dumps(results["control_k0"])
    assert '"p"' not in flat_k0


def test_all_eight_tables_are_written(tmp_path):
    paths = write_tables(build_results(make_data(), 0.05), tmp_path)
    assert sorted(p.name for p in paths) == sorted(TABLE_NAMES)
    for p in paths:
        text = p.read_text(encoding="utf-8")
        assert r"\hline" not in text and r"\label{tab:" + p.stem + "}" in text


def test_captions_with_pvalues_say_explorativ(tmp_path):
    write_tables(build_results(make_data(), 0.05), tmp_path)
    for name in ("tests.tex", "correlation.tex"):
        assert "explorativ" in (tmp_path / name).read_text(encoding="utf-8")


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
