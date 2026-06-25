"""Preprocess / clean Markdown.

Reads documents.jsonl, strips VitePress frontmatter and custom directives,
normalises whitespace. Writes cleaned records back in-place.
"""
from pathlib import Path
from config import DOCUMENTS_FILE


def preprocess(doc_file: Path = DOCUMENTS_FILE) -> None:
    """Clean the text field of every record in documents.jsonl in-place."""
    raise NotImplementedError


if __name__ == "__main__":
    preprocess()
