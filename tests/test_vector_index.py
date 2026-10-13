import numpy as np
import pytest

import vector_index
from vector_index import build_collection, exact_top_k, verified_top_k


def unit_vectors(n, d=16, seed=0):
    v = np.random.default_rng(seed).normal(size=(n, d)).astype(np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def test_exact_top_k_orders_ties_by_chunk_id():
    vectors = np.array([[1, 0], [1, 0], [0, 1]], dtype=np.float32)
    hits = exact_top_k(["b", "a", "c"], vectors, np.array([1, 0], dtype=np.float32), 2)
    assert [cid for cid, _ in hits] == ["a", "b"]
    assert hits[0][1] == pytest.approx(1.0)


def test_chroma_agrees_with_exact_ranking(tmp_path):
    client = vector_index.open_client(tmp_path)
    ids = [f"C1_D001_{i:04d}" for i in range(300)]
    vectors = unit_vectors(300)
    meta = [{"doc_id": "D001", "start_token": i, "end_token": i + 1} for i in range(300)]
    collection = build_collection(client, "rag_test", ids, vectors, meta)
    assert collection.count() == 300
    for query in unit_vectors(20, seed=1):
        hits = verified_top_k(collection, ids, vectors, query, 5)
        assert hits == exact_top_k(ids, vectors, query, 5)


def test_rebuild_replaces_the_collection(tmp_path):
    client = vector_index.open_client(tmp_path)
    meta = [{"doc_id": "D001", "start_token": 0, "end_token": 1}] * 3
    build_collection(client, "rag_test", ["a", "b", "c"], unit_vectors(3), meta)
    collection = build_collection(client, "rag_test", ["a", "b"], unit_vectors(2), meta[:2])
    assert collection.count() == 2


def test_a_wrong_chroma_result_is_detected(tmp_path, monkeypatch):
    client = vector_index.open_client(tmp_path)
    ids = ["a", "b", "c"]
    vectors = unit_vectors(3)
    meta = [{"doc_id": "D001", "start_token": 0, "end_token": 1}] * 3
    collection = build_collection(client, "rag_test", ids, vectors, meta)
    monkeypatch.setattr(vector_index, "chroma_top_k", lambda *a: [("c", 0.99), ("b", 0.5)])
    with pytest.raises(ValueError, match="differs from the exact ranking"):
        verified_top_k(collection, ids, vectors, vectors[0], 2)


def test_a_missing_higher_hit_is_detected_even_with_a_near_tie(tmp_path, monkeypatch):
    client = vector_index.open_client(tmp_path)
    ids = ["a", "b", "c", "d"]
    vectors = np.array(
        [[1, 0], [0.9, 0.43589], [0.5, 0.86603], [0.499995, 0.86603]], dtype=np.float32
    )
    meta = [{"doc_id": "D001", "start_token": 0, "end_token": 1}] * 4
    collection = build_collection(client, "rag_test", ids, vectors, meta)
    exact = dict(exact_top_k(ids, vectors, np.array([1, 0], dtype=np.float32), 4))
    found = [("a", exact["a"]), ("c", exact["c"]), ("d", exact["d"])]  # b (0.9) is missing
    monkeypatch.setattr(vector_index, "chroma_top_k", lambda *a: found)
    with pytest.raises(ValueError, match="differs from the exact ranking"):
        verified_top_k(collection, ids, vectors, np.array([1, 0], dtype=np.float32), 3)


def test_search_breadth_comes_from_the_config(tmp_path, monkeypatch):
    monkeypatch.setattr(vector_index, "HNSW_MIN_BREADTH", 250)
    meta = [{"doc_id": "D001", "start_token": 0, "end_token": 1}] * 3
    small = build_collection(
        vector_index.open_client(tmp_path), "rag_test", ["a", "b", "c"], unit_vectors(3), meta
    )
    assert small.configuration["hnsw"]["ef_search"] == 250
    assert small.configuration["hnsw"]["ef_construction"] == 250
