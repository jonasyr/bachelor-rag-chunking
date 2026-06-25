"""Ingest Vue.js snapshot.

Reads .md files from data/raw/vue_docs_snapshot/,
writes data/processed/documents.jsonl.

Output schema: {"doc_id", "path", "title", "text", "tokens"}
"""
from pathlib import Path
from config import DATA_RAW, DOCUMENTS_FILE


def ingest(snapshot_dir: Path = DATA_RAW, out_file: Path = DOCUMENTS_FILE) -> None:
    """Load all .md files, count tokens with tiktoken, write documents.jsonl."""
    raise NotImplementedError


if __name__ == "__main__":
    ingest()
