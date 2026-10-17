import csv
import json
import re

import pytest

import freeze
import scoring_rules as rules
from config import CONTROL_STRATEGIES, RUBRIC_CRITERIA, RUBRIC_MAX_SCORE, STRATEGY_IDS
from evaluate_answers import (
    ANSWERS_HEADER,
    KEY_HEADER,
    SCORES_HEADER,
    SHEET_HEADER,
    pilot_paths,
    scaffold,
    summarise,
)
from retrieve import GROUND_TRUTH_HEADER, QUESTIONS_HEADER
from run_log import sha256_of
from scoring_rules import KEY_POINTS_HEADER

STRATEGIES = list(STRATEGY_IDS)
QIDS = ("Q001", "Q002")


def write_csv(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    return path


def read(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def chunk_id(key, number):
    return f"{key}_D001_{number:04d}"


def answer_rows(qids=("Q002", "Q001"), strategies=STRATEGIES):
    return [
        [q, s, f"Answer to {q} ({s}).", f"{chunk_id(s, 1)};{chunk_id(s, 2)}", 900, 80]
        for q in qids
        for s in strategies
    ]


@pytest.fixture
def files(tmp_path):
    def empty(name):
        (tmp_path / name).write_text("", encoding="utf-8")
        return tmp_path / name

    chunk_files = {}
    for key in [*STRATEGY_IDS, *CONTROL_STRATEGIES]:
        chunk_files[key] = tmp_path / f"chunks_{key.lower()}.jsonl"
        chunk_files[key].write_text(
            "".join(
                json.dumps({"chunk_id": chunk_id(key, n), "text": f"Excerpt {n} of {key}."}) + "\n"
                for n in (1, 2)
            ),
            encoding="utf-8",
        )
    return {
        "answers_file": write_csv(
            tmp_path / "generated_answers.csv", ANSWERS_HEADER, answer_rows()
        ),
        "questions_file": write_csv(
            tmp_path / "questions.csv",
            QUESTIONS_HEADER,
            [
                ["Q001", "One?", "factual", "single", ""],
                ["Q002", "Two?", "comparative", "multi-section", ""],
            ],
        ),
        "ground_truth_file": write_csv(
            tmp_path / "ground_truth.csv",
            GROUND_TRUTH_HEADER,
            [["Q001", "Ref one.", "D001", "D001#a"], ["Q002", "Ref two.", "D001", "D001#b"]],
        ),
        "sections_file": empty("sections.jsonl"),
        "documents_file": empty("documents.jsonl"),
        "freeze_file": tmp_path / "catalogue_freeze.json",
        "chunk_files": {key: chunk_files[key] for key in STRATEGY_IDS},
        "sheet_file": tmp_path / "scoring_sheet.csv",
        "packet_file": tmp_path / "scoring_packet.md",
        "key_file": tmp_path / "scoring_key.csv",
        "items_file": tmp_path / "scoring_items.jsonl",
        "scores_file": tmp_path / "scores.csv",
        "checks_file": tmp_path / "scoring_checks.csv",
        "key_points_file": tmp_path / "key_points.csv",
        "generation_runs_file": tmp_path / "generation_runs.jsonl",
    }


SCAFFOLD_ARGS = [
    "answers_file",
    "questions_file",
    "ground_truth_file",
    "sections_file",
    "documents_file",
    "freeze_file",
    "chunk_files",
    "sheet_file",
    "packet_file",
    "key_file",
    "items_file",
    "generation_runs_file",
]
SUMMARISE_ARGS = [
    "questions_file",
    "ground_truth_file",
    "sections_file",
    "documents_file",
    "freeze_file",
    "sheet_file",
    "key_file",
    "scores_file",
    "checks_file",
    "key_points_file",
    "generation_runs_file",
]


def record_generation(files, outputs=True, **changed):
    """A generate record as generate.py writes it, over the current files unless `changed`."""
    inputs = [files["questions_file"], files["ground_truth_file"], *files["chunk_files"].values()]
    record = {
        "step": "generate",
        "strategy": ",".join(STRATEGIES),
        "inputs_sha256": {f.name: sha256_of(f) for f in inputs} | changed,
    }
    if outputs:
        record["outputs_sha256"] = {
            files["answers_file"].name: sha256_of(files["answers_file"])
        } | changed
    with files["generation_runs_file"].open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def run_scaffold(files, record=True, **overrides):
    """Scaffold; first log a generation run over the current files unless `record` is False."""
    if record:
        record_generation(files)
    return scaffold(**{k: files[k] for k in SCAFFOLD_ARGS} | overrides)


def run_summarise(files, **overrides):
    return summarise(**{k: files[k] for k in SUMMARISE_ARGS} | overrides)


def strategy_of(files):
    return {r["code"]: r["strategy"] for r in read(files["key_file"])}


def write_sheet(files, rows):
    write_csv(files["sheet_file"], SHEET_HEADER, [[r[h] for h in SHEET_HEADER] for r in rows])


def fill(files, scores):
    """scores: {(question_id, strategy): [five criterion values]}, written by code."""
    strategy = strategy_of(files)
    rows = read(files["sheet_file"])
    for row in rows:
        values = scores[row["question_id"], strategy[row["code"]]]
        row.update(zip(RUBRIC_CRITERIA, (str(v) for v in values), strict=True))
    write_sheet(files, rows)


def all_two():
    return {(q, s): [2] * 5 for q in QIDS for s in STRATEGIES}


def test_documented_headers():
    assert SCORES_HEADER == ["question_id", "strategy", *RUBRIC_CRITERIA, "total_score"]
    assert SHEET_HEADER == ["code", "question_id", *RUBRIC_CRITERIA, "notes"]
    assert KEY_HEADER == ["code", "question_id", "strategy"]


def test_the_sheet_and_packet_hide_the_strategy(files):
    assert run_scaffold(files) == len(QIDS) * len(STRATEGIES)
    sheet = files["sheet_file"].read_text(encoding="utf-8")
    packet = files["packet_file"].read_text(encoding="utf-8")
    for key in [*STRATEGY_IDS, *STRATEGY_IDS.values()]:
        assert key not in sheet
    for key in STRATEGY_IDS.values():
        assert key not in packet
    for chunk in (chunk_id(s, n) for s in STRATEGIES for n in (1, 2)):
        assert chunk not in packet  # chunk IDs name the strategy
    rows = read(files["sheet_file"])
    assert [r["code"] for r in rows] == [f"{q}-{x}" for q in QIDS for x in "ABC"]
    assert all(r[c] == "" for r in rows for c in [*RUBRIC_CRITERIA, "notes"])


def test_the_key_maps_every_code_to_exactly_one_answer(files):
    run_scaffold(files)
    key = read(files["key_file"])
    assert sorted((r["question_id"], r["strategy"]) for r in key) == sorted(
        (q, s) for q in QIDS for s in STRATEGIES
    )
    assert [r["code"] for r in key] == [r["code"] for r in read(files["sheet_file"])]


def test_the_order_is_shuffled_per_question_with_a_fixed_seed(files, tmp_path):
    run_scaffold(files)
    first = files["key_file"].read_bytes()
    orders = [
        [r["strategy"] for r in read(files["key_file"]) if r["question_id"] == q] for q in QIDS
    ]
    assert any(order != STRATEGIES for order in orders)  # not simply C1, C2, C3
    again = {k: tmp_path / f"again_{files[k].name}" for k in ("sheet_file", "packet_file")}
    run_scaffold(files, key_file=tmp_path / "again_key.csv", **again)
    assert (tmp_path / "again_key.csv").read_bytes() == first


def test_the_packet_shows_question_reference_answer_and_excerpts_per_code(files):
    run_scaffold(files)
    packet = files["packet_file"].read_text(encoding="utf-8")
    code = next(c for c, s in strategy_of(files).items() if c.startswith("Q001") and s == "C2")
    block = packet.split(f"### {code}")[1].split("\n### ")[0].split("\n## ")[0]
    assert "Answer to Q001 (C2)." in block
    assert "[Excerpt 1]" in block and "Excerpt 1 of C2." in block
    assert "[Excerpt 2]" in block and "Excerpt 2 of C2." in block
    head = packet.split("## Q001")[1].split("### ")[0]
    assert "One?" in head and "Ref one." in head


def test_a_backtick_fence_in_an_answer_cannot_break_the_packet(files):
    rows = answer_rows()
    rows[0][2] = "Use:\n```js\nconst a = ref(0)\n```\n### not a heading"
    write_csv(files["answers_file"], ANSWERS_HEADER, rows)
    run_scaffold(files)
    packet = files["packet_file"].read_text(encoding="utf-8")
    assert "\n````" in packet  # the fence is longer than any backtick run inside
    assert packet.count("\n### Q") == len(QIDS) * len(STRATEGIES)


@pytest.mark.parametrize("existing", ["sheet_file", "key_file"])
def test_scaffold_never_overwrites_a_sheet_or_key(files, existing):
    files[existing].write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError, match="manual scores"):
        run_scaffold(files)
    assert files[existing].read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        (answer_rows(strategies=list(CONTROL_STRATEGIES)), "no K1"),  # no K1 answers
        (answer_rows()[:-1], "missing"),  # one strategy of one question without an answer
        (answer_rows() + answer_rows()[:1], "duplicate"),
        (answer_rows(qids=("Q001",)), "Q002"),  # a question of the catalogue left out
        (answer_rows(qids=("Q001", "Q002", "Q009")), "Q009"),  # not in the catalogue
        ([[*r[:3], "C1_D009_0001", *r[4:]] for r in answer_rows()], "unknown chunk"),
    ],
)
def test_scaffold_refuses_answers_outside_the_experiment_grid(files, rows, message):
    write_csv(files["answers_file"], ANSWERS_HEADER, rows)
    with pytest.raises(ValueError, match=message):
        run_scaffold(files)
    for name in ("sheet_file", "packet_file", "key_file"):
        assert not files[name].exists()


def test_summarise_unblinds_into_scores_with_the_mean_as_total(files):
    run_scaffold(files)
    scores = all_two()
    scores["Q001", "C1"] = [2, 1, 2, 0, 1]  # (2 + 1 + 2 + 0 + 1) / 5 = 1.2
    fill(files, scores)
    run_summarise(files)
    rows = read(files["scores_file"])
    assert [(r["question_id"], r["strategy"]) for r in rows] == [
        (q, s) for q in QIDS for s in STRATEGIES
    ]
    assert [rows[0][c] for c in RUBRIC_CRITERIA] == ["2", "1", "2", "0", "1"]
    assert rows[0]["total_score"] == "1.2" and rows[-1]["total_score"] == "2.0"


def test_summary_per_strategy_type_and_class(files):
    run_scaffold(files)
    scores = all_two()
    scores["Q001", "C1"] = [1] * 5
    fill(files, scores)
    summary = run_summarise(files)
    c1 = summary["all", "all", "C1"]
    assert c1["n"] == 2
    assert c1["total_score"] == pytest.approx(1.5)
    assert c1["median"] == pytest.approx(1.5)
    assert c1["sd"] == pytest.approx(0.7071, abs=1e-4)
    assert c1["correctness"] == pytest.approx(1.5)
    assert summary["type", "factual", "C1"]["total_score"] == pytest.approx(1.0)
    assert summary["difficulty", "multi-section", "C2"]["total_score"] == pytest.approx(2.0)
    assert summary["type", "factual", "C2"]["sd"] == 0.0  # one question: no spread


@pytest.mark.parametrize(
    ("value", "message"),
    [("", "unscored"), ("3", "0-2"), ("-1", "0-2"), ("1.5", "0-2"), ("two", "0-2")],
)
def test_summarise_refuses_unscored_or_invalid_values_and_writes_nothing(files, value, message):
    assert RUBRIC_MAX_SCORE == 2
    run_scaffold(files)
    fill(files, all_two())
    rows = read(files["sheet_file"])
    rows[3]["groundedness"] = value
    write_sheet(files, rows)
    with pytest.raises(ValueError, match=message):
        run_summarise(files)
    assert not files["scores_file"].exists()


@pytest.mark.parametrize(
    "change",
    [
        lambda rows: rows[:-1],  # a code dropped from the sheet
        lambda rows: [{**rows[0], "code": "Q001-Z"}, *rows[1:]],  # a code not in the key
        lambda rows: [{**rows[0], "question_id": "Q002"}, *rows[1:]],  # code moved to another Q
        lambda rows: [*rows, rows[0]],  # a code twice
    ],
)
def test_summarise_refuses_a_sheet_that_does_not_match_its_key(files, change):
    run_scaffold(files)
    fill(files, all_two())
    write_sheet(files, change(read(files["sheet_file"])))
    with pytest.raises(ValueError, match="key"):
        run_summarise(files)
    assert not files["scores_file"].exists()


def test_main_catalogue_is_used_only_while_frozen(files, monkeypatch):
    run_scaffold(files)
    fill(files, all_two())
    monkeypatch.setattr(freeze, "QUESTIONS_FILE", files["questions_file"])
    monkeypatch.setattr(freeze, "GROUND_TRUTH_FILE", files["ground_truth_file"])
    with pytest.raises(RuntimeError, match="not frozen"):
        run_summarise(files)
    assert not files["scores_file"].exists()
    for name in ("sheet_file", "packet_file", "key_file"):
        files[name].unlink()
    with pytest.raises(RuntimeError, match="not frozen"):
        run_scaffold(files)
    assert not files["sheet_file"].exists()


def assert_nothing_scaffolded(files):
    for name in ("sheet_file", "packet_file", "key_file"):
        assert not files[name].exists()


def test_scaffold_needs_the_generation_run(files):
    with pytest.raises(RuntimeError, match="no generate run"):
        run_scaffold(files, record=False)
    assert_nothing_scaffolded(files)


def test_scaffold_refuses_chunks_changed_since_generation(files):
    """The packet would show raters excerpts the model never saw."""
    record_generation(files)
    with files["chunk_files"]["C2"].open("a", encoding="utf-8") as f:
        f.write(json.dumps({"chunk_id": chunk_id("C2", 3), "text": "added later"}) + "\n")
    with pytest.raises(RuntimeError, match="chunks_c2.jsonl"):
        run_scaffold(files, record=False)
    assert_nothing_scaffolded(files)


def test_scaffold_refuses_answers_changed_since_generation(files):
    record_generation(files)
    rows = answer_rows()
    rows[0][2] = "Edited by hand."
    write_csv(files["answers_file"], ANSWERS_HEADER, rows)
    with pytest.raises(RuntimeError, match="generated_answers.csv"):
        run_scaffold(files, record=False)
    assert_nothing_scaffolded(files)


def test_scaffold_needs_the_answer_checksum_of_the_generation_run(files):
    record_generation(files, outputs=False)
    with pytest.raises(RuntimeError, match="generated_answers.csv"):
        run_scaffold(files, record=False)
    assert_nothing_scaffolded(files)


def test_limit_scaffolds_only_the_first_questions(files):
    assert run_scaffold(files, limit=1) == len(STRATEGIES)
    assert {r["question_id"] for r in read(files["key_file"])} == {"Q001"}
    assert {r["question_id"] for r in read(files["sheet_file"])} == {"Q001"}
    packet = files["packet_file"].read_text(encoding="utf-8")
    assert "## Q001" in packet and "## Q002" not in packet


def test_summarise_with_the_same_limit_covers_the_scored_questions(files):
    run_scaffold(files, limit=1)
    fill(files, all_two())
    summary = run_summarise(files, limit=1)
    assert {r["question_id"] for r in read(files["scores_file"])} == {"Q001"}
    assert summary["all", "all", "C1"]["n"] == 1


def test_summarise_without_the_limit_misses_the_unscored_questions(files):
    run_scaffold(files, limit=1)
    fill(files, all_two())
    with pytest.raises(ValueError, match="missing"):
        run_summarise(files)


@pytest.mark.parametrize("limit", [0, -1])
def test_limit_must_be_positive(files, limit):
    with pytest.raises(ValueError, match="limit"):
        run_scaffold(files, limit=limit)


def test_main_catalogue_is_always_scored_in_full(files, monkeypatch):
    """ADR 0032: every answer of the experiment is scored; a limit is for pilot sets only."""
    monkeypatch.setattr(freeze, "QUESTIONS_FILE", files["questions_file"])
    monkeypatch.setattr(freeze, "GROUND_TRUTH_FILE", files["ground_truth_file"])
    freeze.write_freeze(
        *(files[k] for k in ("questions_file", "ground_truth_file", "sections_file")),
        files["documents_file"],
        files["freeze_file"],
    )
    with pytest.raises(ValueError, match="pilot"):
        run_scaffold(files, limit=1)
    with pytest.raises(ValueError, match="pilot"):
        run_summarise(files, limit=1)
    assert_nothing_scaffolded(files)


def test_pilot_paths_keep_every_file_inside_the_set(tmp_path):
    paths = pilot_paths(tmp_path)
    assert set(paths) == {
        "answers_file",
        "questions_file",
        "ground_truth_file",
        "sheet_file",
        "packet_file",
        "key_file",
        "items_file",
        "scores_file",
        "checks_file",
        "key_points_file",
        "generation_runs_file",
    }
    assert all(p.parent == tmp_path for p in paths.values())
    assert paths["generation_runs_file"].name == "runs.jsonl"


CHUNK_ID_RE = re.compile(r"\b[CK]\d_D\d{3}_\d{4}\b")


def items_of(files):
    text = files["items_file"].read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines()]


def test_scaffold_writes_blind_items_in_sheet_order(files):
    run_scaffold(files)
    items = items_of(files)
    assert [i["code"] for i in items] == [r["code"] for r in read(files["sheet_file"])]
    first = items[0]
    assert set(first) == {
        "code",
        "question_id",
        "question",
        "reference_answer",
        "answer",
        "excerpts",
    }
    strategy = strategy_of(files)[first["code"]]
    assert first["answer"] == f"Answer to {first['question_id']} ({strategy})."
    assert first["excerpts"] == [f"Excerpt 1 of {strategy}.", f"Excerpt 2 of {strategy}."]
    assert first["reference_answer"] in ("Ref one.", "Ref two.")


def test_items_carry_no_strategy_and_no_chunk_id(files):
    run_scaffold(files)
    text = files["items_file"].read_text(encoding="utf-8")
    assert not CHUNK_ID_RE.search(text)
    assert all(name not in text for name in STRATEGY_IDS.values())
    assert all("strategy" not in item for item in items_of(files))


def test_scaffold_again_with_the_same_seed_gives_identical_files(files):
    run_scaffold(files, limit=1)
    before = {
        k: files[k].read_text(encoding="utf-8") for k in ("key_file", "items_file", "sheet_file")
    }
    for name in ("sheet_file", "key_file", "packet_file", "items_file"):
        files[name].unlink()
    run_scaffold(files, limit=1)
    assert {k: files[k].read_text(encoding="utf-8") for k in before} == before


def test_scaffold_again_restores_lost_items_and_keeps_the_scores(files):
    """After a fresh clone the ignored item file is gone but the scored sheet is versioned."""
    run_scaffold(files, limit=1)
    items_before = files["items_file"].read_text(encoding="utf-8")
    key_before = files["key_file"].read_text(encoding="utf-8")
    fill(files, all_two())
    sheet_before = files["sheet_file"].read_text(encoding="utf-8")
    files["items_file"].unlink()
    assert run_scaffold(files, limit=1) == len(STRATEGIES)
    assert files["items_file"].read_text(encoding="utf-8") == items_before
    assert files["sheet_file"].read_text(encoding="utf-8") == sheet_before
    assert files["key_file"].read_text(encoding="utf-8") == key_before


def test_scaffold_with_another_key_still_refuses_the_existing_sheet(files):
    run_scaffold(files, limit=1)
    files["items_file"].unlink()
    with pytest.raises(FileExistsError, match="manual scores"):
        run_scaffold(files)  # no limit: other codes than the existing key
    assert not files["items_file"].exists()


def scaffold_records(files):
    lines = files["generation_runs_file"].read_text(encoding="utf-8").splitlines()
    return [r for r in map(json.loads, lines) if r.get("step") == "scaffold"]


def test_scaffold_logs_the_checksum_of_its_items(files):
    run_scaffold(files, limit=1)
    (record,) = scaffold_records(files)
    assert record["outputs_sha256"] == {"scoring_items.jsonl": sha256_of(files["items_file"])}
    assert record["strategy"] == ",".join(STRATEGIES)


def test_restore_refuses_regenerated_answers(files):
    """Scores must never be paired with answers the rater did not see (review of PR #17)."""
    run_scaffold(files, limit=1)
    fill(files, all_two())
    sheet_before = files["sheet_file"].read_text(encoding="utf-8")
    files["items_file"].unlink()
    rows = answer_rows()
    next(r for r in rows if r[0] == "Q001")[2] = "A regenerated answer."  # a scored question
    write_csv(files["answers_file"], ANSWERS_HEADER, rows)
    with pytest.raises(FileExistsError, match="items differ"):
        run_scaffold(files, limit=1)  # records a matching generation run first
    assert not files["items_file"].exists()
    assert files["sheet_file"].read_text(encoding="utf-8") == sheet_before


def test_restore_needs_the_scaffold_record(files):
    run_scaffold(files, limit=1)
    files["items_file"].unlink()
    lines = files["generation_runs_file"].read_text(encoding="utf-8").splitlines()
    kept = [line for line in lines if json.loads(line).get("step") != "scaffold"]
    files["generation_runs_file"].write_text("\n".join(kept) + "\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="no scaffold record"):
        run_scaffold(files, limit=1)


GOOD_CHECKS = {
    "points": ["covered"],
    "declines": "no",
    "core_wrong": "no",
    "other_error": "no",
    "grounded": "all",
    "hallucination": "none",
    "answers_question": "yes",
    "direct": "yes",
    "wordy": "no",
}


def freeze_points(files, points=1):
    """Key points for every question and their freeze record, as the scoring page writes them."""
    rows = [[q, str(n), f"Point {n}"] for q in QIDS for n in range(1, points + 1)]
    write_csv(files["key_points_file"], KEY_POINTS_HEADER, rows)
    record = {
        "step": "key_points",
        "strategy": ",".join(STRATEGIES),
        "outputs_sha256": {"key_points.csv": sha256_of(files["key_points_file"])},
    }
    with files["generation_runs_file"].open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def write_checks(files, rows):
    write_csv(
        files["checks_file"],
        rules.CHECKS_HEADER,
        [[r[h] for h in rules.CHECKS_HEADER] for r in rows],
    )


def test_summarise_accepts_a_sheet_that_equals_its_checks(files):
    run_scaffold(files)
    fill(files, all_two())
    codes = [r["code"] for r in read(files["sheet_file"])]
    freeze_points(files)
    write_checks(files, [rules.to_row(c, GOOD_CHECKS) for c in codes])
    run_summarise(files)
    assert files["scores_file"].exists()


def test_summarise_refuses_a_score_that_differs_from_its_checks(files):
    run_scaffold(files)
    fill(files, all_two())
    codes = [r["code"] for r in read(files["sheet_file"])]
    freeze_points(files)
    rows = [rules.to_row(c, GOOD_CHECKS) for c in codes]
    rows[0] = rules.to_row(codes[0], GOOD_CHECKS | {"wordy": "yes"})  # clarity 1, sheet says 2
    write_checks(files, rows)
    with pytest.raises(ValueError, match=f"{codes[0]}.*clarity"):
        run_summarise(files)
    assert not files["scores_file"].exists()


def test_summarise_refuses_missing_checks_and_older_rules(files):
    run_scaffold(files)
    fill(files, all_two())
    codes = [r["code"] for r in read(files["sheet_file"])]
    freeze_points(files)
    write_checks(files, [rules.to_row(c, GOOD_CHECKS) for c in codes[1:]])
    with pytest.raises(ValueError, match=f"no checks for {codes[0]}"):
        run_summarise(files)
    old = [rules.to_row(c, GOOD_CHECKS) | {"rules_version": "2000-01-01"} for c in codes]
    write_checks(files, old)
    with pytest.raises(ValueError, match="2000-01-01"):
        run_summarise(files)


def test_summarise_without_a_checks_file_works_as_before(files):
    run_scaffold(files)
    fill(files, all_two())
    assert not files["checks_file"].exists()
    run_summarise(files)
    assert files["scores_file"].exists()


def scored_with_checks(files):
    run_scaffold(files)
    fill(files, all_two())
    codes = [r["code"] for r in read(files["sheet_file"])]
    write_checks(files, [rules.to_row(c, GOOD_CHECKS) for c in codes])


def test_summarise_refuses_checks_without_frozen_key_points(files):
    scored_with_checks(files)
    with pytest.raises(ValueError, match="not frozen"):
        run_summarise(files)
    assert not files["scores_file"].exists()


def test_summarise_refuses_key_points_changed_after_the_freeze(files):
    scored_with_checks(files)
    freeze_points(files)
    with files["key_points_file"].open("a", encoding="utf-8") as f:
        f.write("Q001,2,Added later\n")
    with pytest.raises(ValueError, match="key_points.csv"):
        run_summarise(files)


def test_summarise_refuses_checks_whose_point_count_differs(files):
    scored_with_checks(files)  # checks mark one point per answer
    freeze_points(files, points=2)
    with pytest.raises(ValueError, match="2 key points"):
        run_summarise(files)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda rows: rows + [rows[0]], "more than once"),  # duplicate code
        (lambda rows: rows + [rules.to_row("Q009-A", GOOD_CHECKS)], "not in"),  # stray code
        (lambda rows: rows[::-1], "order"),
    ],
)
def test_summarise_refuses_a_malformed_checks_sequence(files, change, message):
    run_scaffold(files)
    fill(files, all_two())
    codes = [r["code"] for r in read(files["sheet_file"])]
    freeze_points(files)
    write_checks(files, change([rules.to_row(c, GOOD_CHECKS) for c in codes]))
    with pytest.raises(ValueError, match=message):
        run_summarise(files)
    assert not files["scores_file"].exists()
