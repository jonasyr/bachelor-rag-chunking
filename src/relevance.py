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
