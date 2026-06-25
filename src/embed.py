"""Embed chunks and build Chroma vector indices.

One persistent Chroma collection per strategy (config.CHROMA_COLLECTIONS).
Uses OpenAI Embeddings API (config.EMBEDDING_MODEL).
"""
from config import CHROMA_COLLECTIONS


def embed_and_store(strategy_key: str) -> None:
    """Embed all chunks for strategy_key and upsert into Chroma."""
    raise NotImplementedError


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--strategy", choices=["C1", "C2", "C3", "all"], default="all")
    args = p.parse_args()
    keys = ["C1", "C2", "C3"] if args.strategy == "all" else [args.strategy]
    for k in keys:
        embed_and_store(k)
