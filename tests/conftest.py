import hashlib

import numpy as np
import pytest

from embedding_client import EmbeddingResult

FAKE_DIMENSIONS = 16


class FakeEmbedder:
    """Deterministic unit vectors from the text hash; records every call (no network)."""

    def __init__(self, salt: str = ""):
        self.salt = salt  # a different salt simulates a changed model behind the same name
        self.calls: list[list[str]] = []

    def __call__(self, texts: list[str]) -> EmbeddingResult:
        self.calls.append(list(texts))
        rows = []
        for text in texts:
            seed = int(hashlib.sha256((self.salt + text).encode()).hexdigest()[:8], 16)
            v = np.random.default_rng(seed).normal(size=FAKE_DIMENSIONS)
            rows.append(v / np.linalg.norm(v))
        return EmbeddingResult(np.asarray(rows, dtype=np.float32), 7 * len(texts))


@pytest.fixture
def fake_embedder():
    return FakeEmbedder()
