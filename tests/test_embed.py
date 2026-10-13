import json

import numpy as np
import pytest

import vector_index
from embed import embed_and_store


def write_chunks(path, texts):
    rows = [
        {
            "chunk_id": f"C1_D001_{i:04d}",
            "doc_id": "D001",
            "strategy": "fixed_500_no_overlap",
            "text": text,
            "start_token": 10 * i,
            "end_token": 10 * i + 10,
        }
        for i, text in enumerate(texts, start=1)
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


@pytest.fixture
def paths(tmp_path):
    chunk_file = tmp_path / "chunks_c1.jsonl"
    write_chunks(
        chunk_file, ["ref() wraps a value.", "reactive() makes objects reactive.", "props"]
    )
    return {
        "chunk_file": chunk_file,
        "vector_file": tmp_path / "embeddings_c1.npz",
        "runs_file": tmp_path / "embedding_runs.jsonl",
        "client": vector_index.open_client(tmp_path / "chroma"),
    }


def test_first_run_embeds_stores_and_logs(paths, fake_embedder):
    run = embed_and_store("C1", embedder=fake_embedder, **paths)
    assert len(fake_embedder.calls) == 1
    with np.load(paths["vector_file"]) as data:
        assert data["ids"].tolist() == ["C1_D001_0001", "C1_D001_0002", "C1_D001_0003"]
        assert data["vectors"].dtype == np.float32
    assert paths["client"].get_collection("rag_c1").count() == 3
    assert run["api_called"] and run["input_tokens"] == 21
    assert run["cost_usd"] == pytest.approx(21 / 1_000_000 * 0.13)
    logged = json.loads(paths["runs_file"].read_text(encoding="utf-8"))
    assert logged["step"] == "embed" and logged["model"] == "text-embedding-3-large"
    assert set(logged) >= {
        "date",
        "openai_sdk",
        "chromadb",
        "vectors",
        "vector_bytes",
        "inputs_sha256",
    }


def test_second_run_reuses_vectors_without_api_call(paths, fake_embedder):
    embed_and_store("C1", embedder=fake_embedder, **paths)
    run = embed_and_store("C1", embedder=fake_embedder, **paths)
    assert len(fake_embedder.calls) == 1
    assert not run["api_called"] and run["cost_usd"] == 0
    assert paths["client"].get_collection("rag_c1").count() == 3


def test_changed_chunks_require_deliberate_reembedding(paths, fake_embedder):
    embed_and_store("C1", embedder=fake_embedder, **paths)
    write_chunks(paths["chunk_file"], ["ref() wraps a value.", "changed text", "props"])
    with pytest.raises(ValueError, match="delete it deliberately"):
        embed_and_store("C1", embedder=fake_embedder, **paths)


def test_vectors_of_another_model_are_not_reused(paths, fake_embedder, monkeypatch):
    embed_and_store("C1", embedder=fake_embedder, **paths)
    monkeypatch.setattr("embed.EMBEDDING_MODEL", "text-embedding-3-small")
    with pytest.raises(ValueError, match="text-embedding-3-large"):
        embed_and_store("C1", embedder=fake_embedder, **paths)
