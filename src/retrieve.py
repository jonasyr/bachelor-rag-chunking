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
    TOP_K,
)
from embed import load_jsonl, load_vectors, save_vectors
from embedding_client import Embedder, embed_texts
from relevance import is_relevant
from run_log import append_run, sha256_of

HEADER = ["question_id", "strategy", "rank", "chunk_id", "score", "is_relevant"]


def read_rows(path: Path, what: str) -> list[dict]:
    """Rows of a CSV file; raise if the file is missing or has no rows."""
    if not path.exists():
        raise FileNotFoundError(f"{path} not found; create the {what} first")
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"{path} has no rows; the {what} must be complete before retrieval")
    return rows


def split_ids(field: str) -> list[str]:
    return [part.strip() for part in field.split(ID_SEPARATOR) if part.strip()]


def relevant_sections(
    questions: list[dict], ground_truth: list[dict], sections: list[dict]
) -> dict[str, list[dict]]:
    """Annotated sections per question; raise on missing ground truth or unknown section IDs."""
    by_id = {s["section_id"]: s for s in sections}
    truth = {row["question_id"]: row for row in ground_truth}
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
        result[qid] = [by_id[sid] for sid in ids]
    return result


def retrieve(
    strategy_keys: list[str],
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
    """Write retrieved_results.csv for all questions and the given strategies; return row count."""
    questions = sorted(
        read_rows(questions_file, "question catalogue"), key=lambda q: q["question_id"]
    )
    ground_truth = read_rows(ground_truth_file, "ground truth")
    sections = load_jsonl(sections_file, "run src/preprocess.py first")
    relevant = relevant_sections(questions, ground_truth, sections)

    qids = [q["question_id"] for q in questions]
    texts = [q["question"] for q in questions]
    query_vectors = load_vectors(query_file, qids, texts)
    input_tokens = 0
    if query_vectors is None:
        result = embedder(texts)
        query_vectors, input_tokens = result.vectors, result.input_tokens
        save_vectors(query_file, qids, texts, query_vectors)

    client = client or vector_index.open_client()
    rows: list[list] = []
    for key in sorted(strategy_keys):
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

    if out_file.exists():  # keep the rows of strategies not part of this run
        with out_file.open(encoding="utf-8", newline="") as f:
            rows += [r for r in csv.reader(f) if r and r != HEADER and r[1] not in strategy_keys]
    rows = [[str(v) for v in r] for r in rows]
    rows.sort(key=lambda r: (r[0], r[1], int(r[2])))
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(rows)
    append_run(
        {
            "step": "retrieve",
            "strategy": ",".join(sorted(strategy_keys)),
            "dimensions": int(query_vectors.shape[1]),
            "vectors": len(qids),
            "inputs_sha256": {
                questions_file.name: sha256_of(questions_file),
                ground_truth_file.name: sha256_of(ground_truth_file),
            },
        },
        input_tokens,
        runs_file,
    )
    return len(rows)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Retrieve the top-k chunks per question and strategy.")
    p.add_argument("--strategy", choices=["C1", "C2", "C3", "all"], default="all")
    args = p.parse_args()
    keys = ["C1", "C2", "C3"] if args.strategy == "all" else [args.strategy]
    print(f"{retrieve(keys)} rows -> {RETRIEVED_RESULTS_FILE}")
