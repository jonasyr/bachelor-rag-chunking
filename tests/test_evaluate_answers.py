import csv
import json

import pytest

import freeze
from config import CONTROL_STRATEGIES, RUBRIC_CRITERIA, RUBRIC_MAX_SCORE, STRATEGY_IDS
from evaluate_answers import (
    ANSWERS_HEADER,
    KEY_HEADER,
    SCORES_HEADER,
    SHEET_HEADER,
    scaffold,
    summarise,
)
from retrieve import GROUND_TRUTH_HEADER, QUESTIONS_HEADER

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
        "scores_file": tmp_path / "scores.csv",
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
]


def run_scaffold(files, **overrides):
    return scaffold(**{k: files[k] for k in SCAFFOLD_ARGS} | overrides)


def run_summarise(files):
    return summarise(**{k: files[k] for k in SUMMARISE_ARGS})


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
