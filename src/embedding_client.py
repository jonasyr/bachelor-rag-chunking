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

from config import (
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    OPENAI_MAX_RETRIES,
    OPENAI_TIMEOUT_S,
)

# Every non-2xx response the client received (status, path), retried or not, in order; a step
# that journals its calls takes them with `drain_http_errors` (ADR 0050).
HTTP_ERRORS: list[dict] = []


def drain_http_errors() -> list[dict]:
    taken = list(HTTP_ERRORS)
    HTTP_ERRORS.clear()
    return taken


def _note_error(response: Any) -> None:
    if response.status_code >= 300:
        HTTP_ERRORS.append({"status": response.status_code, "path": response.request.url.path})


@dataclass(frozen=True)
class EmbeddingResult:
    vectors: np.ndarray  # float32, shape (n, dimensions)
    input_tokens: int  # as billed (usage.prompt_tokens)


Embedder = Callable[[list[str]], EmbeddingResult]


def _openai_client() -> Any:
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set; copy .env.example to .env and add your key")
    from openai import DefaultHttpxClient, OpenAI

    return OpenAI(
        max_retries=OPENAI_MAX_RETRIES,
        timeout=OPENAI_TIMEOUT_S,
        http_client=DefaultHttpxClient(event_hooks={"response": [_note_error]}),
    )


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
