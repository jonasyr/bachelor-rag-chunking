# Embedding, Vector Index and Retrieval Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Embed the chunks of C1–C3 once with `text-embedding-3-large`, build one Chroma index per strategy from the
stored vectors, and retrieve a verified exact top 5 per question and strategy with relevance flags.

**Architecture:** `embedding_client.py` (OpenAI, batched), `vector_index.py` (Chroma + exact NumPy check),
`relevance.py` (token overlap), `run_log.py` (versions, tokens, costs), filled-in `embed.py` and `retrieve.py`. Every
API result is stored once (`.npz`) and reused; tests use a deterministic fake embedder and never touch the network.

**Tech Stack:** Python 3.13 via uv, openai 2.44.0, chromadb 1.5.9, numpy, pytest, ruff, Pyright.

**Spec:** `docs/superpowers/specs/2026-10-13-embedding-retrieval-design.md`

**Verification of this plan:** all code below was applied to a throwaway clone on 13.10.2026: pre-commit clean,
Pyright 0 errors, 134 tests (131 + 3 vector checks skipped without real vectors), the new tests also pass with the
network cut off (`unshare -rn`); the vector integration test was validated with synthetic 3,072-dimension vectors.

## Global Constraints

- Parameters only in `src/config.py`; model `text-embedding-3-large`, 3,072 dimensions, batches of 100, price 0.13 USD
  per 1M tokens (ADR 0023).
- Reference vectors are stored once and only deleted deliberately; Chroma with `cosine`, `ef_search` ≥ collection
  size, `embedding_function=None`, telemetry off; every top-k verified against exact NumPy cosine, ties by
  `chunk_id` (ADR 0024).
- `retrieved_results.csv` header exactly `question_id,strategy,rank,chunk_id,score,is_relevant`; several IDs in a
  ground-truth field separated by `;`.
- No test calls the OpenAI API or the network; never print or log the API key; never commit `.env`.
- Branch `feat/embedding-retrieval`, Conventional Commits, no AI attribution; `git add` new files before
  `uvx pre-commit run --all-files`.
- The real embedding run (Task 7) costs about USD 0.05 and needs Jonas' explicit OK; the real retrieval run waits for
  the frozen ground truth.

## Review Focus

- A Chroma result that differs from the exact ranking must abort, not be written — `test_a_wrong_chroma_result_is_detected` (Task 3).
- Changed chunk or question texts must never silently reuse stale vectors — `test_changed_chunks_require_deliberate_reembedding` (Task 4), `test_changed_question_text_is_not_silently_reused` (Task 5).
- A rerun must not call the API and must reproduce the CSV byte for byte — `test_second_run_reuses_vectors_without_api_call` (Task 4), `test_rerun_is_byte_identical_without_api_call` (Task 5).
- Missing key must give a hint without printing anything secret — `test_missing_api_key_points_to_env_file` (Task 2).
- Ground truth gaps (empty file, unknown section, missing row) must stop retrieval — the three `test_refuses_*` tests (Task 5).

---

### Task 1: Configuration, pins and the relevance rule

**Files:**
- Modify: `src/config.py`, `pyproject.toml`, `uv.lock`, `.gitignore`
- Create: `src/relevance.py`
- Test: `tests/test_relevance.py`

**Interfaces:**
- Produces: `config.EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`, `EMBEDDING_BATCH_SIZE`, `EMBEDDING_PRICE_PER_MTOK`,
  `EMBEDDING_FILES: dict[str, Path]`, `QUERY_EMBEDDINGS_FILE`, `EMBEDDING_RUNS_FILE`, `SCORE_TOLERANCE`,
  `ID_SEPARATOR`; `relevance.overlap_tokens(chunk: dict, section: dict) -> int`,
  `relevance.is_relevant(chunk: dict, sections: list[dict], min_overlap: int) -> bool`.

- [ ] **Step 1: Configuration**

In `src/config.py` replace the line `EMBEDDING_MODEL = "text-embedding-3-large"  # or text-embedding-3-small for cost focus` with:

```python
# Embedding model (D23): OpenAI offers only the alias as snapshot, so vectors are stored once (D24).
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 3072  # model default
EMBEDDING_BATCH_SIZE = 100  # API: <= 2048 inputs and <= 300,000 tokens per request
EMBEDDING_PRICE_PER_MTOK = 0.13  # USD per 1M input tokens, OpenAI model page, accessed 13.10.2026
```

Directly before `CHROMA_COLLECTIONS = {` insert:

```python
EMBEDDING_FILES = {
    "C1": DATA_PROCESSED / "embeddings_c1.npz",
    "C2": DATA_PROCESSED / "embeddings_c2.npz",
    "C3": DATA_PROCESSED / "embeddings_c3.npz",
}
QUERY_EMBEDDINGS_FILE = DATA_EVAL / "query_embeddings.npz"
EMBEDDING_RUNS_FILE = DATA_PROCESSED / "embedding_runs.jsonl"

```

Directly after `TOP_K = 5  # constant — do NOT vary; would introduce a second independent variable` insert:

```python
SCORE_TOLERANCE = 1e-5  # Chroma vs exact NumPy cosine (float32), D24
ID_SEPARATOR = ";"  # several IDs in one ground_truth.csv field
```

- [ ] **Step 2: Pins and ignore rule**

In `pyproject.toml` replace `"openai>=1.30.0",` with `"openai==2.44.0",  # pinned (ADR 0016)` and `"chromadb>=0.5.0",`
with `"chromadb==1.5.9",  # pinned (ADR 0016)`; in `.gitignore` add `data/evaluation/query_embeddings.npz` after
`data/evaluation/scores.csv`. Run `uv lock && uv sync`. Expected: versions unchanged (already locked).

- [ ] **Step 3: Write the failing test** — `tests/test_relevance.py`:

```python
import pytest

from relevance import is_relevant, overlap_tokens

SECTION = {"doc_id": "D001", "start_token": 100, "end_token": 200}


def chunk(doc_id, start, end):
    return {"doc_id": doc_id, "start_token": start, "end_token": end}


@pytest.mark.parametrize(
    ("c", "expected"),
    [
        (chunk("D001", 120, 180), 60),  # inside
        (chunk("D001", 50, 150), 50),  # partial, left
        (chunk("D001", 150, 400), 50),  # partial, right
        (chunk("D001", 0, 500), 100),  # covers the section
        (chunk("D001", 0, 100), 0),  # touching on the left
        (chunk("D001", 200, 300), 0),  # touching on the right
        (chunk("D002", 120, 180), 0),  # other document
    ],
)
def test_overlap_tokens(c, expected):
    assert overlap_tokens(c, SECTION) == expected


def test_is_relevant_thresholds():
    c = chunk("D001", 150, 400)  # 50 tokens overlap
    assert is_relevant(c, [SECTION], 1)
    assert not is_relevant(c, [SECTION], 100)
    assert is_relevant(c, [chunk("D009", 0, 10), SECTION], 1)
    assert not is_relevant(c, [], 1)
```

- [ ] **Step 4: Run it** — `uv run pytest tests/test_relevance.py -q` → FAIL with `ModuleNotFoundError: No module named 'relevance'`

- [ ] **Step 5: Implement** — `src/relevance.py`:

```python
"""Relevance of a retrieved chunk by token overlap with annotated sections (ADR 0019, 0022).

Chunks and sections share the token space of src/tokens.py; spans are [start, end).
"""


def overlap_tokens(chunk: dict, section: dict) -> int:
    """Number of tokens a chunk shares with a section of the same document (0 otherwise)."""
    if chunk["doc_id"] != section["doc_id"]:
        return 0
    start = max(chunk["start_token"], section["start_token"])
    end = min(chunk["end_token"], section["end_token"])
    return max(0, end - start)


def is_relevant(chunk: dict, sections: list[dict], min_overlap: int) -> bool:
    """True if the chunk overlaps any of the sections by at least min_overlap tokens."""
    return any(overlap_tokens(chunk, s) >= min_overlap for s in sections)
```

- [ ] **Step 6: Run it** — `uv run pytest tests/test_relevance.py -q` → 8 passed

- [ ] **Step 7: Commit** — `git add src/config.py src/relevance.py tests/test_relevance.py pyproject.toml uv.lock .gitignore && uvx pre-commit run --all-files && git commit -m "feat(relevance): Überlappungsregel, Embedding-Konfiguration und gepinnte Versionen" && git push`

---

### Task 2: OpenAI embedding client

**Files:**
- Create: `src/embedding_client.py`, `tests/conftest.py`
- Test: `tests/test_embedding_client.py`

**Interfaces:**
- Consumes: Task 1 config.
- Produces: `EmbeddingResult(vectors: np.ndarray, input_tokens: int)`, `Embedder = Callable[[list[str]], EmbeddingResult]`,
  `embed_texts(texts: list[str], client=None, batch_size=EMBEDDING_BATCH_SIZE) -> EmbeddingResult`;
  pytest fixture `fake_embedder` (class `FakeEmbedder` with `.calls`, 16 dimensions, 7 tokens per text).

- [ ] **Step 1: Write the fixture and the failing tests** — `tests/conftest.py`:

```python
import hashlib

import numpy as np
import pytest

from embedding_client import EmbeddingResult

FAKE_DIMENSIONS = 16


class FakeEmbedder:
    """Deterministic unit vectors from the text hash; records every call (no network)."""

    def __init__(self):
        self.calls: list[list[str]] = []

    def __call__(self, texts: list[str]) -> EmbeddingResult:
        self.calls.append(list(texts))
        rows = []
        for text in texts:
            seed = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
            v = np.random.default_rng(seed).normal(size=FAKE_DIMENSIONS)
            rows.append(v / np.linalg.norm(v))
        return EmbeddingResult(np.asarray(rows, dtype=np.float32), 7 * len(texts))


@pytest.fixture
def fake_embedder():
    return FakeEmbedder()
```

`tests/test_embedding_client.py`:

```python
from types import SimpleNamespace

import pytest

import embedding_client
from config import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL
from embedding_client import embed_texts


class FakeOpenAI:
    """Mimics client.embeddings.create; returns items in reverse order to test re-sorting."""

    def __init__(self, dimensions=EMBEDDING_DIMENSIONS):
        self.requests = []
        self.dimensions = dimensions
        self.embeddings = SimpleNamespace(create=self.create)

    def create(self, model, input, encoding_format):
        self.requests.append((model, list(input), encoding_format))
        data = [
            SimpleNamespace(index=i, embedding=[float(len(text))] * self.dimensions)
            for i, text in enumerate(input)
        ]
        return SimpleNamespace(data=data[::-1], usage=SimpleNamespace(prompt_tokens=3 * len(input)))


def test_batches_keep_order_and_sum_tokens():
    client = FakeOpenAI()
    texts = ["a", "bb", "ccc", "dddd", "eeeee"]
    result = embed_texts(texts, client=client, batch_size=2)
    assert [len(batch) for _, batch, _ in client.requests] == [2, 2, 1]
    assert {model for model, _, _ in client.requests} == {EMBEDDING_MODEL}
    assert result.vectors.shape == (5, EMBEDDING_DIMENSIONS)
    assert result.vectors[:, 0].tolist() == [1.0, 2.0, 3.0, 4.0, 5.0]
    assert result.input_tokens == 15


def test_wrong_dimension_raises():
    with pytest.raises(ValueError, match="dimensions"):
        embed_texts(["a"], client=FakeOpenAI(dimensions=3))


def test_empty_text_raises():
    with pytest.raises(ValueError, match="empty text"):
        embed_texts(["a", "  "], client=FakeOpenAI())


def test_missing_api_key_points_to_env_file(monkeypatch):
    monkeypatch.setattr(embedding_client, "load_dotenv", lambda *a, **k: False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not set; copy .env.example"):
        embed_texts(["a"])
```

- [ ] **Step 2: Run them** — `uv run pytest tests/test_embedding_client.py -q` → FAIL with `ModuleNotFoundError: No module named 'embedding_client'`

- [ ] **Step 3: Implement** — `src/embedding_client.py`:

```python
"""OpenAI embeddings (ADR 0023): batched, order-preserving, dimension-checked.

The API key is read from the environment (or .env) only when a call is made, so tests and
the other pipeline steps never need it.
"""

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
from dotenv import load_dotenv

from config import EMBEDDING_BATCH_SIZE, EMBEDDING_DIMENSIONS, EMBEDDING_MODEL


@dataclass(frozen=True)
class EmbeddingResult:
    vectors: np.ndarray  # float32, shape (n, dimensions)
    input_tokens: int  # as billed (usage.prompt_tokens)


Embedder = Callable[[list[str]], EmbeddingResult]


def _openai_client() -> Any:
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set; copy .env.example to .env and add your key")
    from openai import OpenAI

    return OpenAI()


def embed_texts(
    texts: list[str], client: Any = None, batch_size: int = EMBEDDING_BATCH_SIZE
) -> EmbeddingResult:
    """Embed texts in order with config.EMBEDDING_MODEL; raise on empty text or wrong dimension."""
    if any(not t.strip() for t in texts):
        raise ValueError("empty text cannot be embedded")
    client = client or _openai_client()
    rows: list[list[float]] = []
    input_tokens = 0
    for i in range(0, len(texts), batch_size):
        response = client.embeddings.create(
            model=EMBEDDING_MODEL, input=texts[i : i + batch_size], encoding_format="float"
        )
        rows.extend(d.embedding for d in sorted(response.data, key=lambda d: d.index))
        input_tokens += response.usage.prompt_tokens
    vectors = np.asarray(rows, dtype=np.float32).reshape(len(rows), -1)
    if len(rows) != len(texts) or (rows and vectors.shape[1] != EMBEDDING_DIMENSIONS):
        raise ValueError(
            f"expected {len(texts)} vectors of {EMBEDDING_DIMENSIONS} dimensions, "
            f"got shape {vectors.shape}"
        )
    return EmbeddingResult(vectors, input_tokens)
```

- [ ] **Step 4: Run them** — `uv run pytest tests/test_embedding_client.py -q` → 4 passed

- [ ] **Step 5: Commit** — `git add src/embedding_client.py tests/conftest.py tests/test_embedding_client.py && uvx pre-commit run --all-files && git commit -m "feat(embedding): OpenAI-Client mit Stapeln, Reihenfolge und Dimensionsprüfung" && git push`

---

### Task 3: Chroma index with verified exact search

**Files:**
- Create: `src/vector_index.py`
- Test: `tests/test_vector_index.py`

**Interfaces:**
- Consumes: `config.CHROMA_DIR`, `config.SCORE_TOLERANCE`.
- Produces: `Hit = tuple[str, float]`; `open_client(path=CHROMA_DIR)`; `build_collection(client, name, ids, vectors, metadatas)`;
  `exact_top_k(ids, vectors, query, k) -> list[Hit]`; `chroma_top_k(collection, query, k) -> list[Hit]`;
  `verified_top_k(collection, ids, vectors, query, k, tolerance=SCORE_TOLERANCE) -> list[Hit]` (raises `ValueError`).

- [ ] **Step 1: Write the failing tests** — `tests/test_vector_index.py`:

```python
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
```

- [ ] **Step 2: Run them** — `uv run pytest tests/test_vector_index.py -q` → FAIL with `ModuleNotFoundError: No module named 'vector_index'`

- [ ] **Step 3: Implement** — `src/vector_index.py`:

```python
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
    consistent = len(found) == len(exact) and all(
        abs(exact_sim.get(cid, -2.0) - score) <= tolerance and score >= kth - tolerance
        for cid, score in found
    )
    if not consistent:
        raise ValueError(f"Chroma result {found} differs from the exact ranking {exact}")
    return exact
```

- [ ] **Step 4: Run them** — `uv run pytest tests/test_vector_index.py -q` → 4 passed

- [ ] **Step 5: Commit** — `git add src/vector_index.py tests/test_vector_index.py && uvx pre-commit run --all-files && git commit -m "feat(index): Chroma mit Kosinus und geprüfter exakter Suche" && git push`

---

### Task 4: Run log and `embed.py`

**Files:**
- Create: `src/run_log.py`
- Modify: `src/embed.py` (replace the stub)
- Test: `tests/test_embed.py`

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces: `run_log.sha256_of(path) -> str`, `run_log.append_run(record: dict, input_tokens: int, runs_file=EMBEDDING_RUNS_FILE) -> dict`;
  `embed.load_jsonl(path, hint) -> list[dict]`, `embed.load_vectors(path, ids, texts) -> np.ndarray | None`,
  `embed.save_vectors(path, ids, texts, vectors)`, `embed.embed_and_store(strategy_key, embedder=embed_texts, client=None, chunk_file=None, vector_file=None, runs_file=EMBEDDING_RUNS_FILE) -> dict`.

- [ ] **Step 1: Write the failing tests** — `tests/test_embed.py`:

```python
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
```

- [ ] **Step 2: Run them** — `uv run pytest tests/test_embed.py -q` → FAIL with `TypeError: embed_and_store() got an unexpected keyword argument 'embedder'` (the stub still has the old signature)

- [ ] **Step 3: Implement** — `src/run_log.py`:

```python
"""Run records for embedding and retrieval (ADR 0008: costs; ADR 0016: versions and dates)."""

import hashlib
import json
from datetime import date
from importlib.metadata import version
from pathlib import Path

from config import EMBEDDING_MODEL, EMBEDDING_PRICE_PER_MTOK, EMBEDDING_RUNS_FILE


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def append_run(record: dict, input_tokens: int, runs_file: Path = EMBEDDING_RUNS_FILE) -> dict:
    """Append one JSON line with model, versions, date, tokens and cost; return the full record."""
    full = {
        "date": date.today().isoformat(),
        "model": EMBEDDING_MODEL,
        "openai_sdk": version("openai"),
        "chromadb": version("chromadb"),
        **record,
        "input_tokens": input_tokens,
        "cost_usd": round(input_tokens / 1_000_000 * EMBEDDING_PRICE_PER_MTOK, 10),
        "api_called": input_tokens > 0,
    }
    runs_file.parent.mkdir(parents=True, exist_ok=True)
    with runs_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(full, ensure_ascii=False) + "\n")
    return full
```

Replace `src/embed.py` with:

```python
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
from config import CHROMA_COLLECTIONS, CHUNK_FILES, EMBEDDING_FILES, EMBEDDING_RUNS_FILE
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
        if data["ids"].tolist() != ids or data["texts"].tolist() != texts:
            raise ValueError(
                f"{path} does not match its inputs; delete it deliberately to embed again"
            )
        return data["vectors"]


def save_vectors(path: Path, ids: list[str], texts: list[str], vectors: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, ids=np.array(ids), texts=np.array(texts), vectors=vectors.astype(np.float32))


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
```

- [ ] **Step 4: Run them** — `uv run pytest tests/test_embed.py -q` → 3 passed

- [ ] **Step 5: Commit** — `git add src/run_log.py src/embed.py tests/test_embed.py && uvx pre-commit run --all-files && git commit -m "feat(embed): Referenzvektoren einmal erzeugen, Index daraus bauen, Läufe protokollieren" && git push`

---

### Task 5: `retrieve.py`

**Files:**
- Modify: `src/retrieve.py` (replace the stub)
- Test: `tests/test_retrieve.py`

**Interfaces:**
- Consumes: Tasks 1–4; `chunking.chunk`, `preprocess.clean_markdown`, `preprocess.section_spans`, `tokens.count` (tests).
- Produces: `retrieve.HEADER`, `read_rows(path, what)`, `split_ids(field)`, `relevant_sections(questions, ground_truth, sections)`,
  `retrieve(strategy_keys, embedder=embed_texts, client=None, questions_file=…, ground_truth_file=…, sections_file=…, chunk_files=…, vector_files=…, query_file=…, out_file=…, runs_file=…) -> int`.

- [ ] **Step 1: Write the failing tests** — `tests/test_retrieve.py`:

```python
import csv
import json

import pytest

import tokens
import vector_index
from chunking import chunk
from embed import embed_and_store, load_jsonl
from preprocess import clean_markdown, section_spans
from relevance import is_relevant
from retrieve import HEADER, retrieve
from run_log import sha256_of

PAGE = (
    "# {title} {{#{a}}}\n\n## First part {{#first}}\n\n{body}\n\n"
    "## Second part {{#second}}\n\n{body2}\n"
)


@pytest.fixture
def setup(tmp_path, fake_embedder):
    docs, sections = [], []
    for i in range(1, 7):
        doc_id = f"D{i:03d}"
        body = f"Topic {i} explains reactive state with ref and computed values. " * 12
        body2 = f"Topic {i} also covers watchers, props and emits in components. " * 12
        result = clean_markdown(
            PAGE.format(title=f"Page {i}", a=f"page-{i}", body=body, body2=body2)
        )
        docs.append(
            {
                "doc_id": doc_id,
                "path": f"guide/p{i}.md",
                "title": f"Page {i}",
                "text": result.text,
                "tokens": tokens.count(result.text),
            }
        )
        sections.extend(section_spans(doc_id, result))
    docs_file, sections_file = tmp_path / "documents.jsonl", tmp_path / "sections.jsonl"
    docs_file.write_text("".join(json.dumps(d) + "\n" for d in docs), encoding="utf-8")
    sections_file.write_text("".join(json.dumps(s) + "\n" for s in sections), encoding="utf-8")

    client = vector_index.open_client(tmp_path / "chroma")
    chunk_files, vector_files = {}, {}
    for key in ("C1", "C3"):
        chunk_files[key] = tmp_path / f"chunks_{key.lower()}.jsonl"
        vector_files[key] = tmp_path / f"embeddings_{key.lower()}.npz"
        chunk(key, docs_file, sections_file, chunk_files[key])
        embed_and_store(
            key,
            embedder=fake_embedder,
            client=client,
            chunk_file=chunk_files[key],
            vector_file=vector_files[key],
            runs_file=tmp_path / "runs.jsonl",
        )

    target = load_jsonl(chunk_files["C3"], "")[3]  # questions reuse a chunk text: exact match
    questions = tmp_path / "questions.csv"
    with questions.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["question_id", "question", "type", "difficulty", "notes"])
        writer.writerow(["Q002", target["text"], "factual", "easy", ""])
        writer.writerow(["Q001", "How do watchers work?", "conceptual", "medium", ""])
    truth = tmp_path / "ground_truth.csv"
    truth.write_text(
        "question_id,expected_answer,relevant_doc_ids,relevant_section_ids\n"
        'Q001,"Watchers run side effects.",D002,"D002#second; D003#second"\n'
        f'Q002,"Same text.",{target["doc_id"]},{target["doc_id"]}#first\n',
        encoding="utf-8",
    )
    paths = {
        "client": client,
        "questions_file": questions,
        "ground_truth_file": truth,
        "sections_file": sections_file,
        "chunk_files": chunk_files,
        "vector_files": vector_files,
        "query_file": tmp_path / "query_embeddings.npz",
        "out_file": tmp_path / "retrieved_results.csv",
        "runs_file": tmp_path / "runs.jsonl",
    }
    return paths, target, sections, fake_embedder


def read_out(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


def test_writes_exact_format_and_relevance(setup):
    paths, target, sections, fake = setup
    assert retrieve(["C3", "C1"], embedder=fake, **paths) == 2 * 2 * 5
    rows = read_out(paths["out_file"])
    assert rows[0] == HEADER
    body = rows[1:]
    assert [(r[0], r[1], r[2]) for r in body][:6] == [
        ("Q001", "C1", "1"),
        ("Q001", "C1", "2"),
        ("Q001", "C1", "3"),
        ("Q001", "C1", "4"),
        ("Q001", "C1", "5"),
        ("Q001", "C3", "1"),
    ]
    top_c3_q2 = next(r for r in body if r[0] == "Q002" and r[1] == "C3" and r[2] == "1")
    assert top_c3_q2[3] == target["chunk_id"] and top_c3_q2[4] == "1.000000"
    chunks = {
        c["chunk_id"]: c for k in ("C1", "C3") for c in load_jsonl(paths["chunk_files"][k], "")
    }
    by_id = {s["section_id"]: s for s in sections}
    gold = {
        "Q001": [by_id["D002#second"], by_id["D003#second"]],
        "Q002": [by_id[f"{target['doc_id']}#first"]],
    }
    for qid, _, _, chunk_id, _, flag in body:
        assert flag == str(int(is_relevant(chunks[chunk_id], gold[qid], 1)))


def test_rerun_is_byte_identical_without_api_call(setup):
    paths, _, _, fake = setup
    calls_before = len(fake.calls)
    retrieve(["C1", "C3"], embedder=fake, **paths)
    first = paths["out_file"].read_bytes()
    retrieve(["C1", "C3"], embedder=fake, **paths)
    assert paths["out_file"].read_bytes() == first
    assert len(fake.calls) == calls_before + 1  # questions embedded once only


def test_run_log_records_ground_truth_checksums(setup):
    paths, _, _, fake = setup
    retrieve(["C1"], embedder=fake, **paths)
    last = json.loads(paths["runs_file"].read_text(encoding="utf-8").splitlines()[-1])
    assert last["step"] == "retrieve"
    assert last["inputs_sha256"]["ground_truth.csv"] == sha256_of(paths["ground_truth_file"])
    assert last["inputs_sha256"]["questions.csv"] == sha256_of(paths["questions_file"])


def test_refuses_empty_ground_truth(setup):
    paths, _, _, fake = setup
    paths["ground_truth_file"].write_text(
        "question_id,expected_answer,relevant_doc_ids,relevant_section_ids\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="must be complete before retrieval"):
        retrieve(["C1"], embedder=fake, **paths)


def test_refuses_unknown_section_ids(setup):
    paths, _, _, fake = setup
    text = (
        paths["ground_truth_file"].read_text(encoding="utf-8").replace("D003#second", "D003#nope")
    )
    paths["ground_truth_file"].write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="unknown section IDs"):
        retrieve(["C1"], embedder=fake, **paths)


def test_refuses_a_question_without_ground_truth(setup):
    paths, _, _, fake = setup
    lines = paths["ground_truth_file"].read_text(encoding="utf-8").splitlines()
    paths["ground_truth_file"].write_text("\n".join(lines[:2]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Q002 has no row"):
        retrieve(["C1"], embedder=fake, **paths)


def test_changed_question_text_is_not_silently_reused(setup):
    paths, _, _, fake = setup
    retrieve(["C1"], embedder=fake, **paths)
    text = (
        paths["questions_file"].read_text(encoding="utf-8").replace("watchers work", "watchers run")
    )
    paths["questions_file"].write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="delete it deliberately"):
        retrieve(["C1"], embedder=fake, **paths)
```

- [ ] **Step 2: Run them** — `uv run pytest tests/test_retrieve.py -q` → FAIL with `ImportError: cannot import name 'HEADER' from 'retrieve'`

- [ ] **Step 3: Implement** — replace `src/retrieve.py` with:

```python
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

    rows.sort(key=lambda r: (r[0], r[1], r[2]))
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
```

- [ ] **Step 4: Run all tests** — `uv run pytest -q` → all passed; then without network:
`unshare -rn env PATH=$PATH HOME=$HOME uv run --offline --no-sync pytest -q -p no:cacheprovider tests/test_relevance.py tests/test_embedding_client.py tests/test_vector_index.py tests/test_embed.py tests/test_retrieve.py` → 26 passed

- [ ] **Step 5: Commit** — `git add src/retrieve.py tests/test_retrieve.py && uvx pre-commit run --all-files && git commit -m "feat(retrieve): geprüftes exaktes Top-5 mit Relevanz und Ground-Truth-Prüfsummen" && git push`

---

### Task 6: Integration check, ADRs, sources and docs

**Files:**
- Modify: `tests/test_corpus_integration.py`, `docs/reference/literature.md`, `docs/reference/data-formats.md`,
  `docs/reference/tooling.md`, `docs/plan.md`, `docs/adr/README.md`, `docs/README.md`, `AGENTS.md`,
  `docs/superpowers/specs/2026-10-13-embedding-retrieval-design.md`, `.serena/memories/tech_stack.md`, `.serena/memories/pipeline.md`
- Create: `docs/adr/0023-embedding-modell.md`, `docs/adr/0024-referenzvektoren-und-exakte-suche.md`

- [ ] **Step 1: Integration test.** In `tests/test_corpus_integration.py` add `import numpy as np` before `import pytest`,
add `CHUNK_FILES`, `EMBEDDING_DIMENSIONS`, `EMBEDDING_FILES` to the `from config import (...)` block, and append:

```python


@pytest.mark.parametrize("key", ["C1", "C2", "C3"])
def test_reference_vectors_match_their_chunks(key):
    if not EMBEDDING_FILES[key].exists():
        pytest.skip("not embedded; run src/embed.py")
    chunks = [
        json.loads(line) for line in CHUNK_FILES[key].read_text(encoding="utf-8").splitlines()
    ]
    with np.load(EMBEDDING_FILES[key], allow_pickle=False) as data:
        assert data["ids"].tolist() == [c["chunk_id"] for c in chunks]
        assert data["texts"].tolist() == [c["text"] for c in chunks]
        vectors = data["vectors"]
    assert vectors.shape == (len(chunks), EMBEDDING_DIMENSIONS)
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-3)  # OpenAI: unit length
```

Run `uv run pytest -q` → passes, the three vector checks skipped until Task 7.

- [ ] **Step 2: ADR 0023** — `docs/adr/0023-embedding-modell.md`:

```markdown
# 0023. Embedding-Modell: text-embedding-3-large mit 3.072 Dimensionen

## Status

Angenommen (13.10.2026; konkretisiert [ADR 0015](0015-tech-stack.md) und [ADR 0016](0016-modell-neutralitaet.md))

## Kontext

- ADR 0016 verlangt, das Embedding-Modell zum Implementierungszeitpunkt festzulegen; offen war `-large` oder `-small`.
- Die aktuellen Embedding-Modelle von OpenAI sind `text-embedding-3-small` und `text-embedding-3-large`, eingeführt
  im Januar 2024; ein Nachfolger ist nicht veröffentlicht (Stand 13.10.2026; `openai2024embeddingmodels`,
  `openai2026te3large`).
- Laut OpenAI erreicht `-large` auf MTEB 64,6 %, `-small` 62,3 %; beide verarbeiten bis 8.192 Tokens je Eingabe und
  nutzen die Kodierung `cl100k_base` wie `src/tokens.py` (`openai2026embeddingsguide`). C3-Chunks haben höchstens
  800 Tokens ([ADR 0021](0021-c3-grenzen.md)).
- Preise: 0,13 USD (`-large`) bzw. 0,02 USD (`-small`) je 1 Mio. Eingabe-Tokens (`openai2026te3large`). Alle Chunks
  zusammen (C1 117.594, C2 142.894, C3 117.594 Tokens) kosten mit `-large` rund 0,05 USD, mit `-small` rund 0,008 USD.
- Das Embedding-Modell ist für alle Strategien identisch ([ADR 0006](0006-nur-chunking-variiert.md)); ein schwächeres
  Modell kann Unterschiede zwischen den Strategien verdecken.

## Entscheidung

Wir werden für Chunks und Fragen aller Strategien `text-embedding-3-large` mit der Standarddimension 3.072 verwenden.
Wir werden das OpenAI-SDK (2.44.0) und Chroma (1.5.9) in `pyproject.toml` pinnen; Modell, Dimension, Stapelgröße und
Preis stehen in [`src/config.py`](../../src/config.py).

## Konsequenzen

- Gut: Das stärkere Modell macht Unterschiede zwischen den Chunking-Strategien besser sichtbar; die Mehrkosten sind
  vernachlässigbar.
- Gut: Gleiche Tokenisierung wie bei Chunking und Relevanz; kein Chunk wird abgeschnitten.
- Neutral: OpenAI bietet keinen datierten Snapshot des Modells; die Reproduzierbarkeit sichert
  [ADR 0024](0024-referenzvektoren-und-exakte-suche.md).
- Schlecht: Lokal betriebene Open-Weight-Modelle erreichen auf MTEB inzwischen höhere Werte; sie scheiden nach ADR 0015
  aus und werden in der Arbeit als Einschränkung genannt.
```

- [ ] **Step 3: ADR 0024** — `docs/adr/0024-referenzvektoren-und-exakte-suche.md`:

```markdown
# 0024. Referenzvektoren speichern und exakt suchen

## Status

Angenommen (13.10.2026; konkretisiert [ADR 0015](0015-tech-stack.md))

## Kontext

- Für `text-embedding-3-large` führt OpenAI nur den Alias selbst als Snapshot; eine datierte Version gibt es nicht
  (`openai2026te3large`). Das Modell hinter dem Namen kann sich ändern, und wiederholte Aufrufe liefern nicht
  zwingend bitgleiche Vektoren.
- Chroma sucht mit einem HNSW-Index approximativ; Standard sind die Metrik `l2` und `ef_search` = 100
  (`chroma2026configure`).
- OpenAI-Vektoren sind auf Länge 1 normiert; Kosinus und Skalarprodukt ergeben dieselbe Rangfolge
  (`openai2026embeddingsguide`).
- Nichtdeterminismus in allem, was in die Evaluation eingeht, verletzt die Code-Review-Regeln (`AGENTS.md`); mit
  höchstens 493 Vektoren je Strategie ist eine exakte Suche billig.

## Entscheidung

Wir werden Chunk- und Fragevektoren einmal erzeugen und mit IDs und Texten speichern (`embeddings_cN.npz`,
`query_embeddings.npz`); die Chroma-Indizes werden nur aus diesen Vektoren gebaut, eine Neuberechnung erfordert das
bewusste Löschen der Datei.
Wir werden Chroma mit der Metrik `cosine` und `ef_search` mindestens in Größe der Sammlung betreiben, jedes Top-k gegen
eine exakte NumPy-Kosinus-Rangfolge prüfen (Toleranz 1e-5), bei Abweichung abbrechen und Gleichstände nach `chunk_id`
ordnen. Telemetrie und Chromas eingebaute Embedding-Funktion bleiben abgeschaltet.

## Konsequenzen

- Gut: Indexaufbau und Retrieval lassen sich ohne API-Aufruf byte-gleich wiederholen; die Top-5 sind nachweislich
  exakt.
- Neutral: Die Vektordateien sind nicht versioniert (`data/` ist ausgeschlossen) und werden für die Archivierung
  (DOI) gesondert gesichert.
- Schlecht: Die zusätzliche Prüfung kostet etwas Laufzeit; bei dieser Korpusgröße vernachlässigbar.
```

Append to `docs/adr/README.md`:

```markdown
| [0023](0023-embedding-modell.md) | Embedding-Modell: text-embedding-3-large mit 3.072 Dimensionen | Angenommen |
| [0024](0024-referenzvektoren-und-exakte-suche.md) | Referenzvektoren speichern und exakt suchen | Angenommen |
```

- [ ] **Step 4: Sources** — append to `docs/reference/literature.md`:

```markdown

## Technische Quellen (Web)

Abgerufen am 13.10.2026; Grundlage von [ADR 0023](../adr/0023-embedding-modell.md) und
[ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md). Für die Arbeit als APA-7-Webquellen in die BibTeX-Datei
(PaperLab) übernehmen.

| Kurzname | Quelle (APA 7) | Belegt |
|----------|----------------|--------|
| `openai2024embeddingmodels` | OpenAI. (2024, 25. Januar). *New embedding models and API updates*. https://openai.com/index/new-embedding-models-and-api-updates/ | Einführung von `text-embedding-3-small/-large` |
| `openai2026embeddingsguide` | OpenAI. (o. J.). *Vector embeddings* [Leitfaden]. https://developers.openai.com/api/docs/guides/embeddings | MTEB 64,6 % / 62,3 %, max. 8.192 Tokens, `cl100k_base`, Normierung auf Länge 1, Kosinus, Dimensionen |
| `openai2026te3large` | OpenAI. (o. J.). *text-embedding-3-large* [Modellseite]. https://developers.openai.com/api/docs/models/text-embedding-3-large | Preis 0,13 USD je 1 Mio. Tokens, Snapshot nur als Alias |
| `openai2026embeddingsapi` | OpenAI. (o. J.). *Create embeddings* [API-Referenz]. https://developers.openai.com/api/reference/resources/embeddings/methods/create | ≤ 2.048 Eingaben und ≤ 300.000 Tokens je Anfrage, `usage.prompt_tokens` |
| `chroma2026configure` | Chroma. (o. J.). *Configure collections*. https://docs.trychroma.com/docs/collections/configure | HNSW ist approximativ; Standard `l2`, `ef_search` = 100 |
```

- [ ] **Step 5: Formats** — in `docs/reference/data-formats.md` insert after the `sections.jsonl` block (before the
paragraph starting `` `start_token`/`end_token` von Chunks``):

```markdown

**`embeddings_c1.npz`** (analog c2/c3; `data/processed/`, nicht versioniert; [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md))
Arrays `ids` (Chunk-IDs in Dateireihenfolge), `texts` (Chunk-Texte), `vectors` (float32, n × 3.072).

**`query_embeddings.npz`** (`data/evaluation/`, nicht versioniert): Arrays `ids` (Frage-IDs), `texts` (Fragen), `vectors`.

**`embedding_runs.jsonl`** (ein Eintrag je Lauf von `embed.py` oder `retrieve.py`; Kosten nach [ADR 0008](../adr/0008-kosten-als-variable.md))
```json
{"date":"2026-10-13","model":"text-embedding-3-large","openai_sdk":"2.44.0","chromadb":"1.5.9","step":"embed","strategy":"C1","dimensions":3072,"vectors":260,"vector_bytes":3194880,"inputs_sha256":{"chunks_c1.jsonl":"…"},"input_tokens":117594,"cost_usd":0.01528722,"api_called":true}
```
```

and after the `ground_truth.csv` example block add this line:

```markdown
Mehrere IDs in `relevant_doc_ids` bzw. `relevant_section_ids` werden durch `;` getrennt (`config.ID_SEPARATOR`).
```

- [ ] **Step 6: Other docs**
- `docs/reference/tooling.md`: Embeddings row → `OpenAI API, `text-embedding-3-large` (3.072 Dimensionen; [ADR 0023](../adr/0023-embedding-modell.md))`;
  Vector-Store row → `Chroma 1.5.9 (lokal, persistent; Kosinus, exakte Suche geprüft; [ADR 0024](../adr/0024-referenzvektoren-und-exakte-suche.md))`;
  in the `Umgesetzt:` line add `embed.py`, `retrieve.py`; in the tree add `embedding_client.py`, `vector_index.py`, `relevance.py`, `run_log.py`;
  `(Entscheidungen D1–D22)` → `(Entscheidungen D1–D24)`.
- `docs/plan.md`: in the bullet **Modell-/Versionswahl** replace `Embedding-Modell (`-large` vs. `-small`), ` with nothing and append
  ` Entschieden: Embedding-Modell und SDK-/Chroma-Version ([ADR 0023](adr/0023-embedding-modell.md)); offen: GPT-Modell.`
- `docs/README.md`: `ADR 0019–0022` → `ADR 0019–0024`; `AGENTS.md`: `D1–D22` → `D1–D24`, Purpose list adds `embed.py`, `retrieve.py`.
- Spec: in "Artefacts and formats" use the array names `ids`, `texts`, `vectors` for both `.npz` files and the run-log
  field `vector_bytes` instead of `index_bytes` (as implemented).
- Memories: `tech_stack` → model/SDK pins point to ADR 0023/0024; `pipeline` → `embed.py`/`retrieve.py` implemented;
  gotcha: delete an `.npz` deliberately to re-embed, never edit it.

- [ ] **Step 7: Verify and commit**

```bash
git add -A tests docs AGENTS.md .serena/memories
uvx pre-commit run --all-files && uv run pytest -q && uvx pyright src tests
git commit -m "docs(adr): ADR 0023 Embedding-Modell, ADR 0024 exakte Suche, technische Quellen und Formate"
git push
```

---

### Task 7: Real embedding run (only after Jonas' explicit OK)

**Files:**
- Modify: `docs/reference/experiment-record.md`

- [ ] **Step 1: Ask for the OK** (cost about USD 0.05, needs `OPENAI_API_KEY` in `.env`).
- [ ] **Step 2: Run** `uv run python src/embed.py` → `C1: 260 vectors, 117594 tokens …`, `C2: 305 …`, `C3: 493 …`,
  `api_called=True`. Run it a second time → `api_called=False`, no costs.
- [ ] **Step 3: Verify** `uv run pytest -q` → the three `test_reference_vectors_match_their_chunks` cases pass (not skipped).
- [ ] **Step 4: Record** in `docs/reference/experiment-record.md` (Modellversionen): Embedding-Modell
  `text-embedding-3-large` (3.072), OpenAI Python SDK 2.44.0, ChromaDB 1.5.9, each with today's date; add a section
  "Embedding" with tokens and costs per strategy from `data/processed/embedding_runs.jsonl`.
- [ ] **Step 5: Commit** `docs(record): Embedding-Lauf mit Tokens und Kosten protokolliert`, push; open the PR, request
  `@codex review` and run the `codex-reviewer` agent; merge only after Jonas approves.
