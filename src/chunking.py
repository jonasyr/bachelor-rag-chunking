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


def paragraph_breaks(text: str, starts: list[int], lo: int, hi: int) -> list[int]:
    """Token positions in (lo, hi) that start a paragraph (after a blank line, outside fences)."""
    breaks: set[int] = set()
    pos = 0
    in_fence = False
    after_blank = False
    for line in text.split("\n"):
        if not in_fence and after_blank and line.strip():
            t = tokens.char_to_token(starts, pos)
            if lo < t < hi:
                breaks.add(t)
        if FENCE_RE.match(line):
            in_fence = not in_fence
        after_blank = not in_fence and not line.strip()
        pos += len(line) + 1
    return sorted(breaks)


def _merge_short(segments: list[Span], min_tokens: int) -> list[Span]:
    """Join each segment shorter than min_tokens with the next one (the last with the previous)."""
    merged: list[Span] = []
    pending: Span | None = None
    for seg in segments:
        if pending is not None:
            seg, pending = (pending[0], seg[1]), None
        if seg[1] - seg[0] < min_tokens:
            pending = seg
        else:
            merged.append(seg)
    if pending is not None:
        if merged:
            merged[-1] = (merged[-1][0], pending[1])
        else:
            merged.append(pending)
    return merged


def _split_long(seg: Span, breaks: list[int], max_tokens: int, min_tokens: int) -> list[Span]:
    """Cut at paragraph breaks into pieces of at most max_tokens; no rest under min_tokens."""
    start, end = seg
    pieces: list[Span] = []
    while end - start > max_tokens:
        fitting = [b for b in breaks if start < b <= start + max_tokens and end - b >= min_tokens]
        stop = max(fitting) if fitting else min(start + max_tokens, end - min_tokens)
        pieces.append((start, stop))
        start = stop
    pieces.append((start, end))
    return pieces


def structure_spans(
    n_tokens: int, boundaries: list[int], breaks: list[int], max_tokens: int, min_tokens: int
) -> list[Span]:
    """C3: segments between heading boundaries, short ones merged, long ones split."""
    edges = [0, *sorted({b for b in boundaries if 0 < b < n_tokens}), n_tokens]
    segments = list(zip(edges, edges[1:], strict=False))
    spans: list[Span] = []
    for seg in _merge_short(segments, min_tokens):
        if seg[1] - seg[0] <= max_tokens:
            spans.append(seg)
        else:
            spans.extend(_split_long(seg, breaks, max_tokens, min_tokens))
    return spans
