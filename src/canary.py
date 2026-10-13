"""Model-vintage check before new embeddings are added (ADR 0024).

`text-embedding-3-large` is an alias without dated snapshots, so the model behind it can change.
Before vectors are added to an existing set (another strategy or the questions), the first,
middle and last stored text of every existing vector file are embedded again and compared with
their stored vectors. A cosine below CANARY_MIN_COSINE means the model changed; mixing vectors
would then let more than the chunking vary (ADR 0006).
"""

from pathlib import Path

import numpy as np

from config import (
    CANARY_MIN_COSINE,
    EMBEDDING_FILES,
    EMBEDDING_MODEL,
    QUERY_EMBEDDINGS_FILE,
    ROOT,
)
from embedding_client import Embedder


def _probes(path: Path) -> tuple[list[str], np.ndarray]:
    with np.load(path, allow_pickle=False) as data:
        texts, vectors = data["texts"].tolist(), data["vectors"]
    picks = sorted({0, len(texts) // 2, len(texts) - 1})
    return [texts[i] for i in picks], vectors[picks]


def check_vintage(embedder: Embedder, files: list[Path]) -> tuple[float | None, int]:
    """Lowest cosine between fresh and stored probe vectors (None if nothing stored) and tokens."""
    texts: list[str] = []
    stored: list[np.ndarray] = []
    for path in files:
        if path.exists():
            probe_texts, probe_vectors = _probes(path)
            texts += probe_texts
            stored.append(probe_vectors)
    if not texts:
        return None, 0
    result = embedder(texts)
    reference = np.vstack(stored)
    norms = np.linalg.norm(result.vectors, axis=1) * np.linalg.norm(reference, axis=1)
    lowest = float(((result.vectors * reference).sum(axis=1) / norms).min())
    if lowest < CANARY_MIN_COSINE:
        stored_files = [*EMBEDDING_FILES.values(), QUERY_EMBEDDINGS_FILE]
        raise RuntimeError(
            f"the model behind {EMBEDDING_MODEL} changed (canary cosine {lowest:.6f} < "
            f"{CANARY_MIN_COSINE}); delete all embedding files deliberately "
            f"({', '.join(str(p.relative_to(ROOT)) for p in stored_files)}) and embed again"
        )
    return lowest, result.input_tokens
