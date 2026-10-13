"""Token counting shared by ingest, preprocess and chunking (ADR 0019).

One encoding (config.TOKEN_ENCODING) for all steps, so chunk and section token spans share
one index space.
"""

from bisect import bisect_left
from functools import cache

import tiktoken

from config import TOKEN_ENCODING


@cache
def _encoding() -> tiktoken.Encoding:
    return tiktoken.get_encoding(TOKEN_ENCODING)


def encode(text: str) -> list[int]:
    """Token ids of text; special-token strings are treated as plain text."""
    return _encoding().encode(text, disallowed_special=())


def decode(ids: list[int]) -> str:
    """Text of a token id sequence."""
    return _encoding().decode(ids)


def count(text: str) -> int:
    """Number of tokens in text."""
    return len(encode(text))


def token_starts(text: str) -> list[int]:
    """Character offset at which each token of text starts."""
    _, offsets = _encoding().decode_with_offsets(encode(text))
    return offsets


def char_to_token(starts: list[int], char_offset: int) -> int:
    """Index of the first token starting at or after char_offset (len(starts) at the end)."""
    return bisect_left(starts, char_offset)
