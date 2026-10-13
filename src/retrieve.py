"""Retrieval (ADR 0012, 0014, 0019, 0024).

For every question in questions.csv and every strategy, takes Chroma's top-k, verifies it
against the exact cosine ranking and writes retrieved_results.csv with relevance flags
(any token overlap with the annotated sections). Questions are embedded once and stored
(data/evaluation/query_embeddings.npz); SHA-256 of questions.csv and ground_truth.csv go
into the run log, so the frozen ground truth can be checked later (ADR 0017).

Output schema: question_id, strategy, rank, chunk_id, score, is_relevant
"""

import csv
from pathlib import Path
from typing import Any

import vector_index
from canary import check_vintage
from config import (
    CHROMA_COLLECTIONS,
    CHUNK_FILES,
    EMBEDDING_FILES,
    EMBEDDING_RUNS_FILE,
    GROUND_TRUTH_FILE,
    ID_SEPARATOR,
    QUERY_EMBEDDINGS_FILE,
    QUESTIONS_FILE,
    RELEVANCE_MIN_OVERLAP,
    RETRIEVED_RESULTS_FILE,
    SECTIONS_FILE,
    STRATEGY_IDS,
    TOP_K,
)
from embed import load_jsonl, load_vectors, save_vectors
from embedding_client import Embedder, embed_texts
from relevance import is_relevant
from run_log import append_run, sha256_of

HEADER = ["question_id", "strategy", "rank", "chunk_id", "score", "is_relevant"]
# Exact input schemas from docs/reference/data-formats.md
QUESTIONS_HEADER = ["question_id", "question", "type", "difficulty", "notes"]
GROUND_TRUTH_HEADER = ["question_id", "expected_answer", "relevant_doc_ids", "relevant_section_ids"]
QUESTIONS_REQUIRED = ["question_id", "question", "type", "difficulty"]  # `notes` may be empty


def read_rows(path: Path, what: str, header: list[str], required: list[str]) -> list[dict]:
    """Rows with exactly `header` and non-blank `required` fields; raise on any violation."""
    if not path.exists():
        raise FileNotFoundError(f"{path} not found; create the {what} first")
    with path.open(encoding="utf-8", newline="") as f:
        records = [record for record in csv.reader(f) if record]  # blank lines are no rows
    found = records[0] if records else []
    if found != header:
        raise ValueError(
            f"{path} has columns {found}, docs/reference/data-formats.md requires {header}"
        )
    for number, record in enumerate(records[1:], start=2):
        if len(record) != len(header):
            raise ValueError(
                f"{path}: row {number} has {len(record)} fields, expected {len(header)}"
            )
    rows = [dict(zip(header, record, strict=True)) for record in records[1:]]
    if not rows:
        raise ValueError(f"{path} has no rows; the {what} must be complete before retrieval")
    for row in rows:
        for field in required:
            if not row[field].strip():
                raise ValueError(f"{path}: {row['question_id'] or '?'}: empty {field}")
    ids = [row["question_id"] for row in rows]
    duplicates = sorted({qid for qid in ids if ids.count(qid) > 1})
    if duplicates:
        raise ValueError(f"{path}: duplicate question_id {duplicates}")
    return rows


def split_ids(field: str) -> list[str]:
    return [part.strip() for part in field.split(ID_SEPARATOR) if part.strip()]


def relevant_sections(
    questions: list[dict], ground_truth: list[dict], sections: list[dict]
) -> dict[str, list[dict]]:
    """Annotated sections per question; raise if the ground truth is incomplete or inconsistent."""
    by_id = {s["section_id"]: s for s in sections}
    corpus_docs = {s["doc_id"] for s in sections}
    truth = {row["question_id"]: row for row in ground_truth}
    orphans = sorted(set(truth) - {q["question_id"] for q in questions})
    if orphans:
        raise ValueError(f"ground truth for unknown questions {orphans}")
    result: dict[str, list[dict]] = {}
    for q in questions:
        qid = q["question_id"]
        if qid not in truth:
            raise ValueError(f"{qid} has no row in ground_truth.csv")
        ids = split_ids(truth[qid]["relevant_section_ids"])
        if not ids:
            raise ValueError(f"{qid} has no relevant_section_ids")
        unknown = [sid for sid in ids if sid not in by_id]
        if unknown:
            raise ValueError(f"{qid}: unknown section IDs {unknown}")
        listed = set(split_ids(truth[qid]["relevant_doc_ids"]))
        outside = sorted(listed - corpus_docs)
        if outside:
            raise ValueError(f"{qid}: relevant_doc_ids {outside} not in the corpus")
        expected = sorted({by_id[sid]["doc_id"] for sid in ids})
        if sorted(listed) != expected:
            raise ValueError(
                f"{qid}: relevant_doc_ids must be exactly the documents of "
                f"relevant_section_ids {expected}"
            )
        result[qid] = [by_id[sid] for sid in ids]
    return result


def retrieve(
    embedder: Embedder = embed_texts,
    client: Any = None,
    questions_file: Path = QUESTIONS_FILE,
    ground_truth_file: Path = GROUND_TRUTH_FILE,
    sections_file: Path = SECTIONS_FILE,
    chunk_files: dict[str, Path] = CHUNK_FILES,
    vector_files: dict[str, Path] = EMBEDDING_FILES,
    query_file: Path = QUERY_EMBEDDINGS_FILE,
    out_file: Path = RETRIEVED_RESULTS_FILE,
    runs_file: Path = EMBEDDING_RUNS_FILE,
) -> int:
    """Write retrieved_results.csv afresh for all questions and all strategies; return row count.

    All strategies always run together from the same inputs, so no row of an older run is kept.
    """
    for name, mapping in (("chunk_files", chunk_files), ("vector_files", vector_files)):
        if sorted(mapping) != sorted(STRATEGY_IDS):
            raise ValueError(
                f"{name} must cover exactly the strategies {sorted(STRATEGY_IDS)}, "
                f"got {sorted(mapping)}"
            )
    questions = sorted(
        read_rows(questions_file, "question catalogue", QUESTIONS_HEADER, QUESTIONS_REQUIRED),
        key=lambda q: q["question_id"],
    )
    ground_truth = read_rows(
        ground_truth_file, "ground truth", GROUND_TRUTH_HEADER, GROUND_TRUTH_HEADER
    )
    sections = load_jsonl(sections_file, "run src/preprocess.py first")
    relevant = relevant_sections(questions, ground_truth, sections)

    missing = [str(vector_files[key]) for key in STRATEGY_IDS if not vector_files[key].exists()]
    if missing:  # before any API call, so the vintage check always covers every strategy
        raise FileNotFoundError(f"{', '.join(missing)} not found; run src/embed.py first")

    qids = [q["question_id"] for q in questions]
    texts = [q["question"] for q in questions]
    query_vectors = load_vectors(query_file, qids, texts)
    input_tokens = canary_tokens = 0
    canary_cosine = None
    if query_vectors is None:  # questions must share the model vintage of the chunk vectors
        canary_cosine, canary_tokens = check_vintage(embedder, list(vector_files.values()))
        result = embedder(texts)
        query_vectors, input_tokens = result.vectors, result.input_tokens
        save_vectors(query_file, qids, texts, query_vectors)

    client = client or vector_index.open_client()
    strategies = list(STRATEGY_IDS)  # the experiment is always the complete configured set
    rows: list[list] = []
    for key in strategies:
        chunks = load_jsonl(chunk_files[key], "run src/chunking.py first")
        ids = [c["chunk_id"] for c in chunks]
        vectors = load_vectors(vector_files[key], ids, [c["text"] for c in chunks])
        if vectors is None:
            raise FileNotFoundError(f"{vector_files[key]} not found; run src/embed.py first")
        collection = client.get_collection(CHROMA_COLLECTIONS[key])
        if collection.count() != len(ids):
            raise ValueError(f"collection {collection.name} is out of date; run src/embed.py")
        chunk_by_id = {c["chunk_id"]: c for c in chunks}
        for qid, query in zip(qids, query_vectors, strict=True):
            hits = vector_index.verified_top_k(collection, ids, vectors, query, TOP_K)
            for rank, (chunk_id, score) in enumerate(hits, start=1):
                hit = is_relevant(chunk_by_id[chunk_id], relevant[qid], RELEVANCE_MIN_OVERLAP)
                rows.append([qid, key, rank, chunk_id, f"{score:.6f}", int(hit)])

    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(rows)
    # Provenance of every input the rows depend on (frozen ground truth, ADR 0017).
    sources = [questions_file, ground_truth_file, sections_file, query_file]
    sources += [files[key] for files in (chunk_files, vector_files) for key in strategies]
    append_run(
        {
            "step": "retrieve",
            "strategy": ",".join(strategies),
            "dimensions": int(query_vectors.shape[1]),
            "vectors": len(qids),
            "inputs_sha256": {f.name: sha256_of(f) for f in sources},
            "canary_min_cosine": canary_cosine,
        },
        input_tokens,
        runs_file,
        canary_tokens,
    )
    return len(rows)


if __name__ == "__main__":
    import argparse

    argparse.ArgumentParser(
        description="Retrieve the top-k chunks per question for all strategies at once."
    ).parse_args()
    print(f"{retrieve()} rows -> {RETRIEVED_RESULTS_FILE}")
