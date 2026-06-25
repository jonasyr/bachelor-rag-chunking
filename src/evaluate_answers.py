"""Answer quality evaluation — manual rubric 0–2, 5 criteria.

--mode scaffold  Write scores.csv with unscored rows for manual annotation.
--mode summarise Read completed scores.csv and print summary statistics.

Rubric criteria: correctness, completeness, groundedness, no_hallucination, clarity
Output schema (§10 Ground Truth): question_id, strategy, correctness, completeness,
                                   groundedness, no_hallucination, clarity, total_score
"""
from config import GENERATED_ANSWERS_FILE, SCORES_FILE, RUBRIC_CRITERIA


def scaffold() -> None:
    """Write scores.csv with placeholder rows for manual 0–2 scoring."""
    raise NotImplementedError


def summarise() -> None:
    """Read filled scores.csv and print per-strategy and per-type summary."""
    raise NotImplementedError


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["scaffold", "summarise"], required=True)
    args = p.parse_args()
    {"scaffold": scaffold, "summarise": summarise}[args.mode]()
