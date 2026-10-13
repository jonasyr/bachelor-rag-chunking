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


def make_chunks(doc: dict, spans: list[Span], key: str) -> list[dict]:
    """Chunk records for one document; text is the exact character slice of each span."""
    text = doc["text"]
    starts = tokens.token_starts(text)

    def char(t: int) -> int:
        return starts[t] if t < len(starts) else len(text)

    return [
        {
            "chunk_id": f"{key}_{doc['doc_id']}_{i:04d}",
            "doc_id": doc["doc_id"],
            "strategy": STRATEGY_IDS[key],
            "text": text[char(a) : char(b)],
            "start_token": a,
            "end_token": b,
        }
        for i, (a, b) in enumerate(spans, start=1)
    ]


def check_chunks(doc: dict, chunks: list[dict], key: str) -> None:
    """Raise ValueError if the chunks of one document violate the strategy's invariants."""
    n = doc["tokens"]
    spans = [(c["start_token"], c["end_token"]) for c in chunks]

    def fail(message: str) -> None:
        raise ValueError(f"{doc['doc_id']} {key}: {message}")

    if n != tokens.count(doc["text"]):
        fail("token count does not match the text; re-run src/preprocess.py")
    if not spans or spans[0][0] != 0 or spans[-1][1] != n:
        fail("chunks do not cover the document from 0 to its end")
    for chunk_id, (a, b) in zip((c["chunk_id"] for c in chunks), spans, strict=True):
        if not 0 <= a < b <= n or b - a > MAX_LENGTH[key]:
            fail(f"{chunk_id} has invalid span [{a}, {b})")
    pairs = list(zip(spans, spans[1:], strict=False))
    if key in FIXED_WINDOWS:
        size, overlap = FIXED_WINDOWS[key]
        if any(
            cur[0] - prev[0] != size - overlap or prev[1] - prev[0] != size for prev, cur in pairs
        ):
            fail(f"windows are not {size} tokens with step {size - overlap}")
    elif any(cur[0] != prev[1] for prev, cur in pairs):
        fail("chunks leave a gap or overlap")
    if key != "C2" and "".join(c["text"] for c in chunks) != doc["text"]:
        fail("chunk texts do not reassemble the document")


def _read_jsonl(path: Path, hint: str) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found; {hint}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _section_boundaries(docs: list[dict], sections_file: Path) -> dict[str, list[int]]:
    ids = {d["doc_id"] for d in docs}
    boundaries: dict[str, list[int]] = {}
    for s in _read_jsonl(sections_file, "run src/preprocess.py first"):
        if s["doc_id"] not in ids:
            raise ValueError(f"section {s['section_id']} belongs to an unknown document")
        boundaries.setdefault(s["doc_id"], []).append(s["start_token"])
    return boundaries


def chunk(
    strategy_key: str,
    docs_file: Path = DOCUMENTS_FILE,
    sections_file: Path = SECTIONS_FILE,
    out_file: Path | None = None,
) -> int:
    """Produce the chunk file for strategy_key ('C1', 'C2' or 'C3'); return the chunk count."""
    if strategy_key not in STRATEGY_IDS:
        raise ValueError(f"unknown strategy {strategy_key!r}")
    out_file = out_file or CHUNK_FILES[strategy_key]
    docs = _read_jsonl(docs_file, "run src/preprocess.py first")
    boundaries = _section_boundaries(docs, sections_file) if strategy_key == "C3" else {}

    chunks: list[dict] = []
    for doc in docs:
        n = doc["tokens"]
        if strategy_key in FIXED_WINDOWS:
            spans = fixed_size_spans(n, *FIXED_WINDOWS[strategy_key])
        else:
            heads = boundaries.get(doc["doc_id"])
            if not heads:
                raise ValueError(f"{doc['doc_id']}: no sections; run src/preprocess.py")
            if min(heads) != 0:
                raise ValueError(f"{doc['doc_id']}: the first section does not start at token 0")
            breaks = paragraph_breaks(doc["text"], tokens.token_starts(doc["text"]), 0, n)
            spans = structure_spans(n, heads, breaks, C3_MAX_TOKENS, C3_MIN_TOKENS)
        doc_chunks = make_chunks(doc, spans, strategy_key)
        check_chunks(doc, doc_chunks, strategy_key)
        chunks.extend(doc_chunks)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    return len(chunks)


def summary(strategy_key: str, out_file: Path | None = None) -> str:
    """One line with chunk count and span lengths of a written chunk file."""
    out_file = out_file or CHUNK_FILES[strategy_key]
    lengths = [c["end_token"] - c["start_token"] for c in _read_jsonl(out_file, "run chunking")]
    return (
        f"{strategy_key}: {len(lengths)} chunks, tokens min {min(lengths)} / "
        f"mean {statistics.mean(lengths):.0f} / max {max(lengths)} -> {out_file.name}"
    )


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Chunk documents.jsonl with C1, C2 and/or C3.")
    p.add_argument("--strategy", choices=[*STRATEGY_IDS, "all"], default="all")
    args = p.parse_args()
    keys = list(STRATEGY_IDS) if args.strategy == "all" else [args.strategy]
    for k in keys:
        chunk(k)
        print(summary(k))
