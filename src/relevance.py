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
    """True if the chunk overlaps a section by at least min(min_overlap, chunk length) tokens.

    Capping the threshold at the chunk length keeps a chunk shorter than min_overlap eligible
    when it lies fully inside a relevant section; at least one shared token is always needed
    (ADR 0026).
    """
    needed = max(1, min(min_overlap, chunk["end_token"] - chunk["start_token"]))
    return any(overlap_tokens(chunk, s) >= needed for s in sections)
