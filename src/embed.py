"""Embed chunks and build the Chroma indices (ADR 0023, ADR 0024).

Per strategy the chunks are embedded once and stored as reference vectors
(data/processed/embeddings_cN.npz); the Chroma collection is (re)built from them.
Existing vectors are reused without an API call; if the chunk file changed, the run stops
and the vector file has to be deleted deliberately to embed again.
"""

import json
from pathlib import Path
from typing import Any

import numpy as np

import vector_index
from config import (
    CHROMA_COLLECTIONS,
    CHUNK_FILES,
    EMBEDDING_FILES,
    EMBEDDING_MODEL,
    EMBEDDING_RUNS_FILE,
)
from embedding_client import Embedder, embed_texts
from run_log import append_run, sha256_of


def load_jsonl(path: Path, hint: str) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found; {hint}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def load_vectors(path: Path, ids: list[str], texts: list[str]) -> np.ndarray | None:
    """Stored vectors for exactly these IDs and texts, None if absent; raise if they differ."""
    if not path.exists():
        return None
    with np.load(path, allow_pickle=False) as data:
        stored_model = str(data["model"]) if "model" in data else "an unknown model"
        if stored_model != EMBEDDING_MODEL:
            raise ValueError(
                f"{path} was embedded with {stored_model}, config says {EMBEDDING_MODEL}; "
                "delete it deliberately to embed again"
            )
        if data["ids"].tolist() != ids or data["texts"].tolist() != texts:
            raise ValueError(
                f"{path} does not match its inputs; delete it deliberately to embed again"
            )
        return data["vectors"]


def save_vectors(path: Path, ids: list[str], texts: list[str], vectors: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        path,
        model=np.array(EMBEDDING_MODEL),
        ids=np.array(ids),
        texts=np.array(texts),
        vectors=vectors.astype(np.float32),
    )


def embed_and_store(
    strategy_key: str,
    embedder: Embedder = embed_texts,
    client: Any = None,
    chunk_file: Path | None = None,
    vector_file: Path | None = None,
    runs_file: Path = EMBEDDING_RUNS_FILE,
) -> dict:
    """Embed (or reuse) the chunks of strategy_key and rebuild its collection; return the run."""
    chunk_file = chunk_file or CHUNK_FILES[strategy_key]
    vector_file = vector_file or EMBEDDING_FILES[strategy_key]
    chunks = load_jsonl(chunk_file, "run src/chunking.py first")
    ids = [c["chunk_id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    vectors = load_vectors(vector_file, ids, texts)
    input_tokens = 0
    if vectors is None:
        result = embedder(texts)
        vectors, input_tokens = result.vectors, result.input_tokens
        save_vectors(vector_file, ids, texts, vectors)
    metadatas = [
        {"doc_id": c["doc_id"], "start_token": c["start_token"], "end_token": c["end_token"]}
        for c in chunks
    ]
    client = client or vector_index.open_client()
    vector_index.build_collection(client, CHROMA_COLLECTIONS[strategy_key], ids, vectors, metadatas)
    return append_run(
        {
            "step": "embed",
            "strategy": strategy_key,
            "dimensions": int(vectors.shape[1]),
            "vectors": len(ids),
            "vector_bytes": int(vectors.astype(np.float32).nbytes),
            "inputs_sha256": {chunk_file.name: sha256_of(chunk_file)},
        },
        input_tokens,
        runs_file,
    )


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Embed chunks and build one Chroma index per strategy.")
    p.add_argument("--strategy", choices=["C1", "C2", "C3", "all"], default="all")
    args = p.parse_args()
    keys = ["C1", "C2", "C3"] if args.strategy == "all" else [args.strategy]
    for k in keys:
        run = embed_and_store(k)
        print(
            f"{k}: {run['vectors']} vectors, {run['input_tokens']} tokens, "
            f"USD {run['cost_usd']:.4f}, api_called={run['api_called']}"
        )
