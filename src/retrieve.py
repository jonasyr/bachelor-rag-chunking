"""Retrieval.

For every question in questions.csv × every strategy,
queries Chroma top-k and writes retrieved_results.csv.

Output schema (§10 Ground Truth): question_id, strategy, rank, chunk_id, score, is_relevant
"""
from config import RETRIEVED_RESULTS_FILE, TOP_K


def retrieve(strategy_keys: list[str]) -> None:
    """Query Chroma for each question per strategy, write retrieved_results.csv."""
    raise NotImplementedError


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--strategy", choices=["C1", "C2", "C3", "all"], default="all")
    args = p.parse_args()
    keys = ["C1", "C2", "C3"] if args.strategy == "all" else [args.strategy]
    retrieve(keys)
