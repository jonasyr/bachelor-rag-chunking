"""Retrieval evaluation.

Computes Recall@k, Precision@k, Hit@k, MRR per strategy and question type.
Reads retrieved_results.csv + ground_truth.csv + questions.csv.
"""
from config import RETRIEVED_RESULTS_FILE, GROUND_TRUTH_FILE, TOP_K


def evaluate(k: int = TOP_K) -> None:
    """Print retrieval metric summary per strategy and per question type."""
    raise NotImplementedError


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--k", type=int, default=TOP_K)
    args = p.parse_args()
    evaluate(args.k)
