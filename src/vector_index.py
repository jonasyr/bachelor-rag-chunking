"""Chroma collections with exact, verified cosine search (ADR 0024).

Chroma's HNSW index is approximate; with ef_search >= collection size it visits every vector,
and every result is checked against an exact NumPy cosine ranking over the stored vectors.
"""

from typing import Any

import chromadb
import numpy as np
from chromadb.config import Settings
from chromadb.errors import NotFoundError

from config import CHROMA_DIR, SCORE_TOLERANCE

Hit = tuple[str, float]  # (chunk_id, cosine similarity)


def open_client(path=CHROMA_DIR) -> Any:
    """Persistent Chroma client without telemetry."""
    return chromadb.PersistentClient(path=str(path), settings=Settings(anonymized_telemetry=False))


def build_collection(
    client: Any, name: str, ids: list[str], vectors: np.ndarray, metadatas: list[dict]
) -> Any:
    """(Re)create collection `name` from the given vectors, cosine space, exhaustive search."""
    try:
        client.delete_collection(name)
    except NotFoundError:
        pass
    breadth = max(len(ids), 100)
    collection = client.create_collection(
        name=name,
        embedding_function=None,  # vectors always come from the stored reference vectors
        configuration={
            "hnsw": {"space": "cosine", "ef_search": breadth, "ef_construction": breadth}
        },
    )
    step = client.get_max_batch_size()
    for i in range(0, len(ids), step):
        collection.add(
            ids=ids[i : i + step],
            embeddings=vectors[i : i + step],
            metadatas=metadatas[i : i + step],
        )
    return collection


def exact_top_k(ids: list[str], vectors: np.ndarray, query: np.ndarray, k: int) -> list[Hit]:
    """Exact cosine ranking: similarity descending, ties by chunk_id."""
    norms = np.linalg.norm(vectors, axis=1) * np.linalg.norm(query)
    sims = (vectors @ query) / norms
    order = sorted(range(len(ids)), key=lambda i: (-float(sims[i]), ids[i]))
    return [(ids[i], float(sims[i])) for i in order[:k]]


def chroma_top_k(collection: Any, query: np.ndarray, k: int) -> list[Hit]:
    """Chroma's top k as (chunk_id, cosine similarity = 1 - cosine distance)."""
    result = collection.query(query_embeddings=[query.tolist()], n_results=k, include=["distances"])
    return [(cid, 1.0 - d) for cid, d in zip(result["ids"][0], result["distances"][0], strict=True)]


def verified_top_k(
    collection: Any,
    ids: list[str],
    vectors: np.ndarray,
    query: np.ndarray,
    k: int,
    tolerance: float = SCORE_TOLERANCE,
) -> list[Hit]:
    """Chroma's top k, checked against the exact ranking; returns the exact, deterministic order."""
    ranking = exact_top_k(ids, vectors, query, len(ids))
    exact = ranking[:k]
    exact_sim = dict(ranking)
    found = chroma_top_k(collection, query, k)
    kth = exact[-1][1] if exact else 0.0
    # Every hit clearly above the rank-k score must be found; only near-ties at rank k may swap.
    required = {cid for cid, score in ranking if score > kth + tolerance}
    consistent = (
        len(found) == len(exact)
        and required <= {cid for cid, _ in found}
        and all(
            abs(exact_sim.get(cid, -2.0) - score) <= tolerance and score >= kth - tolerance
            for cid, score in found
        )
    )
    if not consistent:
        raise ValueError(f"Chroma result {found} differs from the exact ranking {exact}")
    return exact
