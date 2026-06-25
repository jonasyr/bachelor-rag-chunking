"""Chunking strategies C1, C2, C3.

Reads documents.jsonl, writes chunks_c1/c2/c3.jsonl.

C1: fixed-size 500 tokens, overlap 0       (config.C1_CHUNK_SIZE / C1_OVERLAP)
C2: fixed-size 500 tokens, overlap 100     (config.C2_CHUNK_SIZE / C2_OVERLAP)
C3: structure-based H2/H3, max 800 tokens  (config.C3_MAX_TOKENS)

Chunk schema: {"chunk_id", "doc_id", "strategy", "text", "start_token", "end_token"}
"""
from pathlib import Path
from config import CHUNK_FILES, DOCUMENTS_FILE


def chunk(strategy_key: str, docs_file: Path = DOCUMENTS_FILE) -> None:
    """Produce chunk file for strategy_key ('C1', 'C2', or 'C3')."""
    raise NotImplementedError


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--strategy", choices=["C1", "C2", "C3", "all"], default="all")
    args = p.parse_args()
    keys = ["C1", "C2", "C3"] if args.strategy == "all" else [args.strategy]
    for k in keys:
        chunk(k)
