"""Chunking strategies C1, C2, C3 (ADR 0005, ADR 0021).

Reads documents.jsonl (and sections.jsonl for C3), writes chunks_c1/c2/c3.jsonl.

C1: fixed-size 500 tokens, overlap 0       (config.C1_CHUNK_SIZE / C1_OVERLAP)
C2: fixed-size 500 tokens, overlap 100     (config.C2_CHUNK_SIZE / C2_OVERLAP)
C3: structure-based H1-H3, 50-800 tokens   (config.C3_MIN_TOKENS / C3_MAX_TOKENS, ADR 0021)

Spans are [start_token, end_token) in the token space of src/tokens.py (the same as
sections.jsonl); every chunk's text is the exact slice of its document for its span.

Chunk schema: {"chunk_id", "doc_id", "strategy", "text", "start_token", "end_token"}
"""

import json
import re
import statistics
from pathlib import Path

import tokens
from config import (
    C1_CHUNK_SIZE,
    C1_OVERLAP,
    C2_CHUNK_SIZE,
    C2_OVERLAP,
    C3_MAX_TOKENS,
    C3_MIN_TOKENS,
    CHUNK_FILES,
    DOCUMENTS_FILE,
    SECTIONS_FILE,
    STRATEGY_IDS,
)

Span = tuple[int, int]

FIXED_WINDOWS = {"C1": (C1_CHUNK_SIZE, C1_OVERLAP), "C2": (C2_CHUNK_SIZE, C2_OVERLAP)}
MAX_LENGTH = {"C1": C1_CHUNK_SIZE, "C2": C2_CHUNK_SIZE, "C3": C3_MAX_TOKENS}
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")


def fixed_size_spans(n_tokens: int, size: int, overlap: int) -> list[Span]:
    """Windows of `size` tokens with step `size - overlap`; the last one ends at n_tokens."""
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError(f"invalid window: size={size}, overlap={overlap}")
    spans: list[Span] = []
    start = 0
    while start < n_tokens:
        end = min(start + size, n_tokens)
        spans.append((start, end))
        if end == n_tokens:
            break
        start += size - overlap
    return spans
