import csv
import inspect
import json

import pytest

import freeze
from config import (
    CONTROL_STRATEGIES,
    RELEVANCE_MIN_OVERLAP,
    SENSITIVITY_MIN_OVERLAP,
    STRATEGY_IDS,
    TOP_K,
)
from evaluate_retrieval import SCORES_HEADER, evaluate, question_scores, summarise
from retrieve import GROUND_TRUTH_HEADER, HEADER, QUESTIONS_HEADER

# Hand-made spans in one token space (src/tokens.py): D001 has two sections, D002 one.
SECTIONS = [
    {"section_id": "D001#a", "doc_id": "D001", "start_token": 0, "end_token": 100},
    {"section_id": "D001#b", "doc_id": "D001", "start_token": 100, "end_token": 300},
    {"section_id": "D002#c", "doc_id": "D002", "start_token": 0, "end_token": 400},
]


def chunk(key, doc, number, start, end):
    return {
        "chunk_id": f"{key}_{doc}_{number:04d}",
        "doc_id": doc,
        "strategy": STRATEGY_IDS.get(key) or CONTROL_STRATEGIES[key],
        "text": "x",
        "start_token": start,
        "end_token": end,
    }


def chunks_for(key):
    """Five chunks per strategy: 1-3 in D001, 4-5 in D002 (lengths 50, 150, 10, 200, 200)."""
    return [
        chunk(key, "D001", 1, 0, 50),  # inside D001#a
        chunk(key, "D001", 2, 50, 200),  # 50 tokens of D001#a, 100 of D001#b
        chunk(key, "D001", 3, 290, 300),  # 10 tokens of D001#b
        chunk(key, "D002", 1, 0, 200),
        chunk(key, "D002", 2, 200, 400),
    ]


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def write_csv(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    return path


# Ranked chunk numbers per question (index into chunks_for); the same for every strategy
# unless a test overrides it. Q001 asks for D001#a and D001#b, Q002 for D002#c.
RANKING = {"Q001": [3, 4, 0, 1, 2], "Q002": [0, 1, 2, 3, 4]}
TRUTH = {"Q001": ["D001#a", "D001#b"], "Q002": ["D002#c"]}


def result_rows(strategies, ranking=RANKING, truth=TRUTH):
    by_id = {s["section_id"]: s for s in SECTIONS}
    rows = []
    for qid, order in sorted(ranking.items()):
        for key in strategies:
            chunks = chunks_for(key)
            for rank, index in enumerate(order, start=1):
                c = chunks[index]
                hit = any(
                    c["doc_id"] == by_id[sid]["doc_id"]
                    and min(c["end_token"], by_id[sid]["end_token"])
                    > max(c["start_token"], by_id[sid]["start_token"])
                    for sid in truth[qid]
                )
                rows.append([qid, key, rank, c["chunk_id"], "0.500000", int(hit)])
    return rows


@pytest.fixture
def files(tmp_path):
    chunk_files = {
        key: write_jsonl(tmp_path / f"chunks_{key.lower()}.jsonl", chunks_for(key))
        for key in [*STRATEGY_IDS, *CONTROL_STRATEGIES]
    }
    questions = write_csv(
        tmp_path / "questions.csv",
        QUESTIONS_HEADER,
        [
            ["Q001", "Two sections?", "comparative", "multi-section", ""],
            ["Q002", "One section?", "factual", "single", ""],
        ],
    )
    truth = write_csv(
        tmp_path / "ground_truth.csv",
        GROUND_TRUTH_HEADER,
        [["Q001", "A.", "D001", "D001#a;D001#b"], ["Q002", "B.", "D002", "D002#c"]],
    )
    return {
        "questions_file": questions,
        "ground_truth_file": truth,
        "sections_file": write_jsonl(tmp_path / "sections.jsonl", SECTIONS),
        "documents_file": write_jsonl(tmp_path / "documents.jsonl", [{"doc_id": "D001"}]),
        "results_file": write_csv(
            tmp_path / "retrieved_results.csv", HEADER, result_rows(STRATEGY_IDS)
        ),
        "chunk_files": {key: chunk_files[key] for key in STRATEGY_IDS},
        "out_file": tmp_path / "retrieval_scores.csv",
        "_control_chunk_files": {key: chunk_files[key] for key in CONTROL_STRATEGIES},
    }


def run(files, **overrides):
    paths = {k: v for k, v in files.items() if not k.startswith("_")}
    return evaluate(**{**paths, **overrides})


def by_key(rows):
    return {(r["question_id"], r["strategy"], r["rule"]): r for r in rows}


def test_metrics_follow_the_definitions_in_evaluation_md(files):
    rows = by_key(run(files))
    # Q001 ranks D002 chunks first, then chunk 1 (D001#a) at rank 3: RR = 1/3.
    # Relevant chunks at ranks 3, 4, 5 -> Precision 3/5; both sections overlapped -> Recall 1.
    q1 = rows["Q001", "C1", "main"]
    assert (q1["hit"], q1["reciprocal_rank"], q1["precision"], q1["recall"]) == (
        "1",
        "0.333333",
        "0.600000",
        "1.000000",
    )
    # Q002: D002 chunks at ranks 4 and 5 -> RR 1/4, Precision 2/5, Recall 1.
    q2 = rows["Q002", "C1", "main"]
    assert (q2["hit"], q2["reciprocal_rank"], q2["precision"], q2["recall"]) == (
        "1",
        "0.250000",
        "0.400000",
        "1.000000",
    )
    # Context@k: summed lengths of the k retrieved chunks, the same under both rules.
    assert q1["context_tokens"] == q2["context_tokens"] == str(50 + 150 + 10 + 200 + 200)


def test_sensitivity_rule_needs_min_overlap_capped_at_the_chunk_length(files):
    assert SENSITIVITY_MIN_OVERLAP == 100  # the fixture spans are built around this value
    rows = by_key(run(files))
    # Chunk 2 overlaps D001#b by 100 tokens (relevant), chunk 1 lies fully inside D001#a
    # (50 tokens = its length, relevant), chunk 3 lies fully inside D001#b (relevant).
    q1 = rows["Q001", "C1", "sensitivity"]
    assert (q1["precision"], q1["recall"]) == ("0.600000", "1.000000")
    # With only D001#a annotated, chunk 2 (rank 3) shares 50 of its 150 tokens with it:
    # the sensitivity rule drops what the main rule keeps.
    ranking = {"Q001": [3, 4, 1, 0, 0], "Q002": RANKING["Q002"]}
    truth = {"Q001": ["D001#a"], "Q002": TRUTH["Q002"]}
    write_csv(files["results_file"], HEADER, result_rows(STRATEGY_IDS, ranking, truth))
    write_csv(
        files["ground_truth_file"],
        GROUND_TRUTH_HEADER,
        [["Q001", "A.", "D001", "D001#a"], ["Q002", "B.", "D002", "D002#c"]],
    )
    rows = by_key(run(files))
    # Chunk 2 shares 50 tokens with D001#a: relevant under the main rule (>= 1), not under the
    # sensitivity rule (needs min(100, 150) = 100); chunk 1 (50 tokens, inside) stays relevant.
    assert rows["Q001", "C1", "main"]["reciprocal_rank"] == "0.333333"
    assert rows["Q001", "C1", "sensitivity"]["reciprocal_rank"] == "0.250000"


def test_no_relevant_chunk_gives_zero_hit_rank_precision_and_recall(files):
    ranking = {"Q001": [3, 4, 3, 4, 3], "Q002": RANKING["Q002"]}
    write_csv(files["results_file"], HEADER, result_rows(STRATEGY_IDS, ranking))
    q1 = by_key(run(files))["Q001", "C2", "main"]
    assert (q1["hit"], q1["reciprocal_rank"], q1["precision"], q1["recall"]) == (
        "0",
        "0.000000",
        "0.000000",
        "0.000000",
    )


def test_recall_counts_sections_and_precision_counts_chunks(files):
    # Only chunk 1 (inside D001#a) twice and D002 chunks: one of two sections -> Recall 0.5.
    ranking = {"Q001": [0, 0, 3, 4, 3], "Q002": RANKING["Q002"]}
    write_csv(files["results_file"], HEADER, result_rows(STRATEGY_IDS, ranking))
    q1 = by_key(run(files))["Q001", "C3", "main"]
    assert (q1["precision"], q1["recall"]) == ("0.400000", "0.500000")


def test_writes_one_row_per_question_strategy_and_rule_in_stable_order(files):
    run(files)
    with files["out_file"].open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0] == SCORES_HEADER
    keys = [tuple(r[:3]) for r in rows[1:]]
    assert keys == sorted(keys) and len(keys) == 2 * len(STRATEGY_IDS) * 2
    first = files["out_file"].read_bytes()
    run(files)
    assert files["out_file"].read_bytes() == first


def test_summary_is_the_mean_per_strategy_and_per_question_type(files):
    rows = run(files)
    summary = summarise(rows, files["questions_file"])
    overall = summary["all", "all", "C1", "main"]
    assert overall["n"] == 2
    assert overall["reciprocal_rank"] == pytest.approx((1 / 3 + 1 / 4) / 2)
    assert overall["precision"] == pytest.approx((3 / 5 + 2 / 5) / 2)
    by_type = summary["type", "factual", "C1", "main"]
    assert by_type["n"] == 1 and by_type["reciprocal_rank"] == pytest.approx(1 / 4)
    by_class = summary["difficulty", "multi-section", "C2", "sensitivity"]
    assert by_class["n"] == 1 and by_class["recall"] == pytest.approx(1.0)


def test_the_control_is_evaluated_with_its_own_strategy_set(files):
    control_results = files["results_file"].with_name("retrieved_results_control.csv")
    write_csv(control_results, HEADER, result_rows(CONTROL_STRATEGIES))
    rows = run(
        files,
        results_file=control_results,
        chunk_files=files["_control_chunk_files"],
        strategies=CONTROL_STRATEGIES,
    )
    assert {r["strategy"] for r in rows} == set(CONTROL_STRATEGIES)


def test_refuses_any_other_strategy_set(files):
    with pytest.raises(ValueError, match="experiment set or the control set"):
        run(files, strategies={"C1": STRATEGY_IDS["C1"]})


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda rows: rows[:-1], "ranks"),  # a missing rank
        (lambda rows: rows + [rows[0]], "ranks"),  # a duplicate rank
        (lambda rows: [r for r in rows if r[0] != "Q002"], "missing"),  # a missing question
        (lambda rows: [r for r in rows if r[1] != "C2"], "missing"),  # a missing strategy
        (lambda rows: rows + [["Q999", "C1", 1, "C1_D001_0001", "0.1", 0]], "unknown"),
        (lambda rows: [[*r[:3], "C1_D009_0001", *r[4:]] for r in rows], "unknown chunk"),
        # a C2 chunk in a C1 row: the chunk exists, but not in that strategy
        (
            lambda rows: [[*r[:3], r[3].replace("C1_", "C2_"), *r[4:]] for r in rows],
            "unknown chunk",
        ),
    ],
)
def test_refuses_incomplete_or_foreign_results(files, change, message):
    write_csv(files["results_file"], HEADER, change(result_rows(STRATEGY_IDS)))
    with pytest.raises(ValueError, match=message):
        run(files)


def test_refuses_results_whose_relevance_flags_disagree_with_the_ground_truth(files):
    rows = result_rows(STRATEGY_IDS)
    rows[0][5] = 1 - rows[0][5]  # stale: retrieved against another annotation
    write_csv(files["results_file"], HEADER, rows)
    with pytest.raises(ValueError, match="is_relevant.*run src/retrieve.py"):
        run(files)


def test_main_catalogue_is_evaluated_only_while_frozen(files, monkeypatch):
    monkeypatch.setattr(freeze, "QUESTIONS_FILE", files["questions_file"])
    monkeypatch.setattr(freeze, "GROUND_TRUTH_FILE", files["ground_truth_file"])
    freeze_file = files["out_file"].with_name("catalogue_freeze.json")
    with pytest.raises(RuntimeError, match="not frozen"):
        run(files, freeze_file=freeze_file)
    assert not files["out_file"].exists()


def test_the_cutoff_is_always_top_k_and_cannot_be_overridden(files):
    """k is fixed by ADR 0014; a smaller cut-off would write files that look like @5 results."""
    assert "k" not in inspect.signature(evaluate).parameters
    with pytest.raises(TypeError):
        run(files, k=3)


def test_question_scores_is_pure(files):
    """The metric core takes plain rows, so the pilot probe and tests can reuse it."""
    chunks = {c["chunk_id"]: c for c in chunks_for("C1")}
    ranked = [chunks_for("C1")[i] for i in RANKING["Q002"]]
    scores = question_scores(ranked, [SECTIONS[2]], TOP_K, RELEVANCE_MIN_OVERLAP)
    assert scores == {
        "hit": 1,
        "reciprocal_rank": 0.25,
        "precision": 0.4,
        "recall": 1.0,
        "context_tokens": 610,
    }
    assert chunks  # chunk IDs are unique per strategy
