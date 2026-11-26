import csv
from collections import Counter

import pytest
from conftest import valid_rows, write_catalogue, write_scoring_set
from test_llm_rater import FakeOpenAI, valid

import freeze
import hybrid
import llm_rater
import scoring_rules as rules
import scoring_store
import second_rater
from atomic_csv import read_csv, write_csv
from config import CONTROL_CRITERIA, QUESTION_CLASSES, RUBRIC_CRITERIA, STRATEGY_IDS
from control_k0 import CONTROL_SCORES_HEADER
from evaluate_answers import HYBRID_SCORES_HEADER, KEY_HEADER, SCORES_HEADER, SHEET_HEADER
from run_log import latest_run, sha256_of


@pytest.fixture
def set_dir(tmp_path):
    """A pilot-style set with a full 48-question catalogue and a 12-question R2 draw."""
    folder = tmp_path / "set"
    folder.mkdir()
    write_catalogue(folder, valid_rows())
    second_rater.run_draw(second_rater.paths(folder), 12, pilot=True)
    return folder


def sample_ids(p):
    return {r["question_id"] for r in read_csv(p["sample_file"], second_rater.SAMPLE_HEADER)}


def write_sheet(folder, rows):
    """A scoring sheet with one row per (code, value) pair."""
    with (folder / "scoring_sheet.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["code", "question_id", *RUBRIC_CRITERIA, "notes"])
        for code, value in rows:
            w.writerow([code, code[:4], value, *[""] * (len(RUBRIC_CRITERIA) - 1), ""])


def test_paths_add_the_extra_sample(set_dir):
    assert hybrid.paths(set_dir)["extra_file"] == set_dir / hybrid.HYBRID_EXTRA_SAMPLE_FILE.name
    assert hybrid.paths(None)["extra_file"] == hybrid.HYBRID_EXTRA_SAMPLE_FILE


def test_extra_draw_comes_from_the_rest_and_records_the_run(set_dir):
    p = hybrid.paths(set_dir)
    rows = hybrid.run_draw(p, 12, pilot=False)
    assert len(rows) == 12
    assert not {r["question_id"] for r in rows} & sample_ids(p)
    assert read_csv(p["extra_file"], second_rater.SAMPLE_HEADER) == rows
    record = latest_run(p["runs_file"], hybrid.DRAW_STEP, "C1,C2,C3")
    assert record is not None
    assert record["seed"] == hybrid.HYBRID_SEED
    assert record["questions"] == 12
    assert record["inputs_sha256"] == {
        "questions.csv": sha256_of(p["questions_file"]),
        "second_rater_sample.csv": sha256_of(p["sample_file"]),
    }
    assert record["outputs_sha256"] == {p["extra_file"].name: sha256_of(p["extra_file"])}


def test_both_draws_together_mirror_the_catalogue(set_dir):
    p = hybrid.paths(set_dir)
    rows = hybrid.run_draw(p, 12, pilot=False)
    first = read_csv(p["sample_file"], second_rater.SAMPLE_HEADER)
    both = first + rows
    catalogue = Counter(t for _, _, t, _, _, _ in valid_rows())
    assert Counter(r["type"] for r in both) == Counter({k: v // 2 for k, v in catalogue.items()})
    assert all(Counter(r["difficulty"] for r in both)[c] == 6 for c in QUESTION_CLASSES)


def test_extra_draw_is_deterministic(set_dir, tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    write_catalogue(other, valid_rows())
    second_rater.run_draw(second_rater.paths(other), 12, pilot=True)
    assert hybrid.run_draw(hybrid.paths(set_dir), 12, pilot=False) == hybrid.run_draw(
        hybrid.paths(other), 12, pilot=False
    )


def test_extra_draw_never_overwrites(set_dir):
    p = hybrid.paths(set_dir)
    hybrid.run_draw(p, 12, pilot=False)
    before = p["extra_file"].read_bytes()
    with pytest.raises(FileExistsError):
        hybrid.run_draw(p, 12, pilot=False)
    assert p["extra_file"].read_bytes() == before


def test_extra_draw_needs_the_first_draw(tmp_path):
    folder = tmp_path / "set"
    folder.mkdir()
    write_catalogue(folder, valid_rows())
    with pytest.raises(RuntimeError, match="second_rater_draw"):
        hybrid.run_draw(hybrid.paths(folder), 12, pilot=False)


def test_extra_draw_refuses_a_changed_first_sample(set_dir):
    p = hybrid.paths(set_dir)
    p["sample_file"].write_text(
        p["sample_file"].read_text(encoding="utf-8") + "Q048,procedural,multi-section\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="second_rater_sample.csv differs"):
        hybrid.run_draw(p, 12, pilot=False)
    assert not p["extra_file"].exists()


def test_extra_draw_refuses_an_unfrozen_main(set_dir, monkeypatch):
    p = hybrid.paths(set_dir) | {"freeze_file": set_dir / "catalogue_freeze.json"}
    monkeypatch.setattr(freeze, "QUESTIONS_FILE", p["questions_file"])
    with pytest.raises(RuntimeError, match="not frozen"):
        hybrid.run_draw(p, 12, pilot=False)
    assert not p["extra_file"].exists()


def test_values_on_the_first_sample_are_allowed(set_dir):
    p = hybrid.paths(set_dir)
    qid = sorted(sample_ids(p))[0]
    write_sheet(set_dir, [(f"{qid}-A", "2")])
    (set_dir / "scoring_checks.csv").write_text(
        f"code,rules_version\n{qid}-A,2026-10-20\n", encoding="utf-8"
    )
    assert len(hybrid.run_draw(p, 12, pilot=False)) == 12


def test_values_outside_the_first_sample_abort_main(set_dir):
    p = hybrid.paths(set_dir)
    qid = next(r[0] for r in valid_rows() if r[0] not in sample_ids(p))
    write_sheet(set_dir, [(f"{qid}-B", "1")])
    with pytest.raises(RuntimeError, match=qid):
        hybrid.run_draw(p, 12, pilot=False)
    assert not p["extra_file"].exists()


def test_checks_outside_the_first_sample_abort_main(set_dir):
    p = hybrid.paths(set_dir)
    qid = next(r[0] for r in valid_rows() if r[0] not in sample_ids(p))
    (set_dir / "scoring_checks.csv").write_text(
        f"code,rules_version\n{qid}-C,2026-10-20\n", encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match=qid):
        hybrid.run_draw(p, 12, pilot=False)


def test_values_outside_the_first_sample_only_warn_for_pilot(set_dir, capsys):
    p = hybrid.paths(set_dir)
    qid = next(r[0] for r in valid_rows() if r[0] not in sample_ids(p))
    write_sheet(set_dir, [(f"{qid}-A", "1")])
    hybrid.run_draw(p, 12, pilot=True)
    assert p["extra_file"].exists()
    assert "warning" in capsys.readouterr().err.lower()


def test_human_questions_is_the_union_of_both_draws(set_dir):
    p = hybrid.paths(set_dir)
    rows = hybrid.run_draw(p, 12, pilot=False)
    assert hybrid.human_questions(p) == sample_ids(p) | {r["question_id"] for r in rows}


def test_cli_draws_the_configured_number(set_dir):
    hybrid.main(["--mode", "draw", "--set", str(set_dir)])
    rows = read_csv(hybrid.paths(set_dir)["extra_file"], second_rater.SAMPLE_HEADER)
    assert len(rows) == hybrid.HYBRID_EXTRA_QUESTIONS


# --- mode summarise -------------------------------------------------------------------------

HUMAN = valid(1)  # Jonas' checks: every value 2
LLM = valid(1, wordy="yes")  # the LLM's: clarity 1, so the two raters' rows differ


def own_set(p):
    return scoring_store.ScoringSet(
        "own",
        p["items_file"],
        p["sheet_file"],
        p["scores_file"],
        p["key_points_file"],
        p["checks_file"],
        p["runs_file"],
    )


def strategy_of(qid, letter):
    """The key: the letters map to another strategy order for every question."""
    shift = int(qid[1:]) % len(STRATEGY_IDS)
    ids = list(STRATEGY_IDS)
    order = ids[shift:] + ids[:shift]
    return order["ABC".index(letter)]


def build(folder, monkeypatch, skip=(), llm=True, scope="all"):
    """The extra draw, a scaffold of every question x C1-C3 with its key, frozen key points,
    Jonas' checks on his 24 questions (except `skip`) and the LLM's run over every answer."""
    p = hybrid.paths(folder)
    hybrid.run_draw(p, 12, pilot=False)
    qids = sorted(r[0] for r in valid_rows())
    codes = [f"{q}-{letter}" for q in qids for letter in "ABC"]
    write_scoring_set(folder, codes)
    write_csv(
        p["key_file"],
        KEY_HEADER,
        [{"code": c, "question_id": c[:4], "strategy": strategy_of(c[:4], c[-1])} for c in codes],
    )
    mine = own_set(p)
    items = scoring_store.load_items(mine)
    for qid in qids:
        scoring_store.save_key_points(mine, items, qid, ["Core point"])
    scoring_store.freeze_key_points(mine, items)
    human = hybrid.human_questions(p)
    for code in codes:
        if code[:4] in human and code not in skip:
            scoring_store.save_score(mine, code, llm_rater.to_checks(HUMAN, 1), "")
    if llm:
        monkeypatch.setattr(llm_rater, "LLM_RATER_SCOPE", scope)
        llm_rater.run(llm_rater.paths(folder), FakeOpenAI(reply=lambda n, call: LLM))
    return p


def no_scores(p):
    return not p["scores_file"].exists() and not p["llm_scores_file"].exists()


def expected(values):
    derived = rules.derive(llm_rater.to_checks(values, 1))
    return {c: str(v) for c, v in derived.items()}


@pytest.fixture
def scored(set_dir, monkeypatch):
    return build(set_dir, monkeypatch)


def test_paths_add_the_summarise_files(tmp_path):
    p = hybrid.paths(tmp_path)
    llm_dir = tmp_path / "llm_rater"
    assert p["key_file"] == tmp_path / "scoring_key.csv"
    assert p["llm_dir"] == llm_dir
    assert p["llm_sheet_file"] == llm_dir / "scoring_sheet.csv"
    assert p["llm_checks_file"] == llm_dir / "scoring_checks.csv"
    assert p["llm_scores_file"] == llm_dir / "scores.csv"
    main = hybrid.paths(None)
    assert main["key_file"] == hybrid.SCORING_KEY_FILE
    assert main["llm_scores_file"] == hybrid.LLM_RATER_SCORES_FILE


def test_summarise_mixes_by_question(scored):
    counts = hybrid.run_summarise(scored)
    assert counts == {"human": 72, "llm": 72}
    rows = read_csv(scored["scores_file"], HYBRID_SCORES_HEADER)
    human = hybrid.human_questions(scored)
    assert len(rows) == 144
    order = list(STRATEGY_IDS)
    assert [(r["question_id"], r["strategy"]) for r in rows] == sorted(
        ((r["question_id"], r["strategy"]) for r in rows),
        key=lambda k: (k[0], order.index(k[1])),
    )
    for row in rows:
        rater, values = (
            (hybrid.RATER_HUMAN, HUMAN) if row["question_id"] in human else (hybrid.RATER_LLM, LLM)
        )
        assert row["rater"] == rater
        assert {c: row[c] for c in RUBRIC_CRITERIA} == expected(values)
    assert expected(HUMAN) != expected(LLM)
    assert hybrid.RATER_HUMAN == "human" and hybrid.RATER_LLM == "llm"


def test_summarise_unblinds_with_the_key(scored):
    hybrid.run_summarise(scored)
    rows = read_csv(scored["scores_file"], HYBRID_SCORES_HEADER)
    by_answer = {(r["question_id"], r["strategy"]) for r in rows}
    key = read_csv(scored["key_file"], KEY_HEADER)
    assert by_answer == {(r["question_id"], r["strategy"]) for r in key}


def test_summarise_writes_llm_only_scores(scored):
    hybrid.run_summarise(scored)
    rows = read_csv(scored["llm_scores_file"], SCORES_HEADER)
    assert len(rows) == 144
    assert all({c: r[c] for c in RUBRIC_CRITERIA} == expected(LLM) for r in rows)
    mixed = read_csv(scored["scores_file"], HYBRID_SCORES_HEADER)
    assert [(r["question_id"], r["strategy"]) for r in rows] == [
        (r["question_id"], r["strategy"]) for r in mixed
    ]


def test_summarise_logs_record(scored):
    hybrid.run_summarise(scored)
    record = latest_run(scored["runs_file"], hybrid.SUMMARISE_STEP, "C1,C2,C3")
    assert record is not None
    own = ("sheet_file", "checks_file", "key_file", "key_points_file", "sample_file", "extra_file")
    assert record["inputs_sha256"] == {scored[k].name: sha256_of(scored[k]) for k in own}
    assert record["llm_inputs_sha256"] == {
        scored[k].name: sha256_of(scored[k]) for k in ("llm_sheet_file", "llm_checks_file")
    }
    assert record["outputs_sha256"] == {"scores.csv": sha256_of(scored["scores_file"])}
    assert record["llm_outputs_sha256"] == {"scores.csv": sha256_of(scored["llm_scores_file"])}
    assert record["answers"] == {"human": 72, "llm": 72}


def test_require_summarise_checks_both_raters_files(scored):
    hybrid.run_summarise(scored)
    assert hybrid.require_summarise(scored)["step"] == hybrid.SUMMARISE_STEP
    scored["llm_scores_file"].write_text(
        scored["llm_scores_file"].read_text(encoding="utf-8") + "\n", encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="scores.csv"):
        hybrid.require_summarise(scored)


def test_require_summarise_refuses_an_edited_llm_sheet(scored):
    hybrid.run_summarise(scored)
    rows = read_csv(scored["llm_sheet_file"], SHEET_HEADER)
    rows[0][RUBRIC_CRITERIA[0]] = "0"
    write_csv(scored["llm_sheet_file"], SHEET_HEADER, rows)
    with pytest.raises(RuntimeError, match="scoring_sheet.csv"):
        hybrid.require_summarise(scored)


def test_require_summarise_needs_the_record(scored):
    with pytest.raises(RuntimeError, match="hybrid_summarise"):
        hybrid.require_summarise(scored)


def outside_code(p):
    human = hybrid.human_questions(p)
    return next(f"{r[0]}-A" for r in sorted(valid_rows()) if r[0] not in human)


def test_summarise_refuses_a_sheet_value_outside_human_questions(scored):
    code = outside_code(scored)
    rows = read_csv(scored["sheet_file"], SHEET_HEADER)
    for row in rows:
        if row["code"] == code:
            row[RUBRIC_CRITERIA[0]] = "2"
    write_csv(scored["sheet_file"], SHEET_HEADER, rows)
    with pytest.raises(RuntimeError, match=code[:4]):
        hybrid.run_summarise(scored)
    assert no_scores(scored)


def test_summarise_refuses_checks_outside_human_questions(scored):
    code = outside_code(scored)
    with scored["checks_file"].open("a", encoding="utf-8") as f:
        f.write(f"{code}" + "," * (len(rules.CHECKS_HEADER) - 1) + "\n")
    with pytest.raises(RuntimeError, match=code[:4]):
        hybrid.run_summarise(scored)
    assert no_scores(scored)


def test_summarise_refuses_missing_human_code(set_dir, monkeypatch):
    p = hybrid.paths(set_dir)
    missing = f"{sorted(sample_ids(p))[0]}-B"
    p = build(set_dir, monkeypatch, skip={missing})
    with pytest.raises(ValueError, match=missing):
        hybrid.run_summarise(p)
    assert no_scores(p)


def test_summarise_needs_llm_run(set_dir, monkeypatch):
    p = build(set_dir, monkeypatch, llm=False)
    with pytest.raises(RuntimeError, match="llm_rater"):
        hybrid.run_summarise(p)
    assert no_scores(p)


def test_summarise_refuses_an_edited_llm_sheet(scored):
    rows = read_csv(scored["llm_sheet_file"], SHEET_HEADER)
    rows[0][RUBRIC_CRITERIA[0]] = "0"
    write_csv(scored["llm_sheet_file"], SHEET_HEADER, rows)
    with pytest.raises(RuntimeError, match="scoring_sheet.csv differs"):
        hybrid.run_summarise(scored)
    assert no_scores(scored)


def test_summarise_needs_the_extra_sample(scored):
    scored["extra_file"].unlink()
    with pytest.raises(RuntimeError, match="hybrid_extra_sample.csv"):
        hybrid.run_summarise(scored)
    assert no_scores(scored)


def test_summarise_refuses_a_changed_extra_sample(scored):
    scored["extra_file"].write_text(
        scored["extra_file"].read_text(encoding="utf-8") + "Q048,procedural,multi-section\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="hybrid_extra_sample.csv differs"):
        hybrid.run_summarise(scored)
    assert no_scores(scored)


def test_summarise_refuses_a_changed_first_sample(scored):
    scored["sample_file"].write_text(
        scored["sample_file"].read_text(encoding="utf-8") + "Q048,procedural,multi-section\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="second_rater_sample.csv differs"):
        hybrid.run_summarise(scored)
    assert no_scores(scored)


def test_summarise_needs_llm_scope_all(set_dir, monkeypatch):
    p = build(set_dir, monkeypatch, scope="sample")
    with pytest.raises(RuntimeError, match="every answer"):
        hybrid.run_summarise(p)
    assert no_scores(p)


def test_cli_summarise(scored, capsys):
    hybrid.main(["--mode", "summarise", "--set", str(scored["questions_file"].parent)])
    out = capsys.readouterr().out
    assert "72 human" in out and "72 llm" in out
    assert scored["scores_file"].exists() and scored["llm_scores_file"].exists()


# --- summarise-control: K0 from the LLM (ADR 0051) -----------------------------------------------

LLM_K0 = valid(1, wordy="yes")


@pytest.fixture
def k0_scored(scored, monkeypatch):
    """`scored` after hybrid summarise, plus a K0 scaffold over every question and the LLM's
    control run."""
    from conftest import write_control_set

    from run_log import append_scaffold_run

    hybrid.run_summarise(scored)
    folder = scored["llm_dir"].parent
    qids = sorted(r[0] for r in valid_rows())
    write_control_set(folder, qids)
    items = scored["control_items_file"]
    append_scaffold_run("K0", len(qids), {items.name: sha256_of(items)}, scored["runs_file"])
    llm_rater.run(
        llm_rater.paths(folder),
        FakeOpenAI(reply=lambda n, call: valid_control(n, wordy="yes")),
        control=True,
    )
    return scored


def valid_control(n, **override):
    return {k: v for k, v in valid(n).items() if k != "grounded"} | override


def test_paths_add_the_control_files(tmp_path):
    p = hybrid.paths(tmp_path)
    assert p["control_items_file"] == tmp_path / "scoring_items_control.jsonl"
    assert p["llm_control_sheet_file"] == tmp_path / "llm_rater" / "scoring_sheet_control.csv"
    assert p["llm_control_checks_file"] == tmp_path / "llm_rater" / "scoring_checks_control.csv"
    assert p["scores_control_file"] == tmp_path / "scores_control.csv"
    assert hybrid.paths(None)["scores_control_file"] == hybrid.SCORES_CONTROL_FILE


def test_summarise_control_uses_llm_values(k0_scored):
    summary = hybrid.run_summarise_control(k0_scored)
    rows = read_csv(k0_scored["scores_control_file"], CONTROL_SCORES_HEADER)
    assert len(rows) == 48 and {r["strategy"] for r in rows} == {"K0"}
    checks = rules.from_row(
        read_csv(k0_scored["llm_control_checks_file"], rules.checks_header(True))[0], control=True
    )[1]
    for criterion, value in rules.derive_control(checks).items():
        assert {r[criterion] for r in rows} == {str(value)}
    # the C1-C3 side is the LLM's values, not the mixed file's (the raters differ on clarity)
    llm = expected(LLM)
    mixed = expected(HUMAN)
    assert llm != mixed
    for strategy in STRATEGY_IDS:
        side = summary[("all", "all", strategy)]
        for criterion in CONTROL_CRITERIA:
            assert side[criterion] == pytest.approx(int(llm[criterion]))
    assert summary[("all", "all", "K0")]["n"] == 48


def test_summarise_control_logs_the_llm_inputs(k0_scored):
    hybrid.run_summarise_control(k0_scored)
    record = latest_run(k0_scored["runs_file"], "summarise_control", "K0")
    assert record["inputs_sha256"] == {
        "scoring_sheet_control.csv": sha256_of(k0_scored["llm_control_sheet_file"]),
        "scoring_checks_control.csv": sha256_of(k0_scored["llm_control_checks_file"]),
        "key_points.csv": sha256_of(k0_scored["key_points_file"]),
        "scores.csv": sha256_of(k0_scored["llm_scores_file"]),
    }


def test_summarise_control_needs_llm_control_run(scored):
    hybrid.run_summarise(scored)
    with pytest.raises(RuntimeError, match="llm_rater"):
        hybrid.run_summarise_control(scored)
    assert not scored["scores_control_file"].exists()


def test_summarise_control_refuses_an_edited_llm_control_sheet(k0_scored):
    from control_k0 import CONTROL_SHEET_HEADER

    rows = read_csv(k0_scored["llm_control_sheet_file"], CONTROL_SHEET_HEADER)
    rows[0][CONTROL_CRITERIA[0]] = "0"
    write_csv(k0_scored["llm_control_sheet_file"], CONTROL_SHEET_HEADER, rows)
    with pytest.raises(RuntimeError, match="scoring_sheet_control.csv"):
        hybrid.run_summarise_control(k0_scored)
    assert not k0_scored["scores_control_file"].exists()


def test_summarise_control_needs_hybrid_summarise(k0_scored):
    runs = k0_scored["runs_file"]
    kept = [
        line
        for line in runs.read_text(encoding="utf-8").splitlines()
        if hybrid.SUMMARISE_STEP not in line
    ]
    runs.write_text("\n".join(kept) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="hybrid_summarise"):
        hybrid.run_summarise_control(k0_scored)


def test_summarise_control_refuses_an_edited_llm_scores_file(k0_scored):
    k0_scored["llm_scores_file"].write_text(
        k0_scored["llm_scores_file"].read_text(encoding="utf-8") + "\n", encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="scores.csv"):
        hybrid.run_summarise_control(k0_scored)


def test_cli_summarise_control(k0_scored, capsys):
    hybrid.main(["--mode", "summarise-control", "--set", str(k0_scored["questions_file"].parent)])
    assert "K0 from the LLM" in capsys.readouterr().out
    assert k0_scored["scores_control_file"].exists()
