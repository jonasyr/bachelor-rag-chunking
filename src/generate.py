"""Answer generation.

Assembles prompt from top-k chunks (see docs/prompts.md),
calls LLM (config.LLM_MODEL, temperature=0), writes generated_answers.csv.

Output schema (§10 Ground Truth): question_id, strategy, answer, sources,
                                   prompt_tokens, completion_tokens
"""
from config import GENERATED_ANSWERS_FILE, LLM_MODEL, LLM_TEMPERATURE


def generate_answers(strategy_keys: list[str]) -> None:
    """Generate LLM answers for each question × strategy, write generated_answers.csv."""
    raise NotImplementedError


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--strategy", choices=["C1", "C2", "C3", "all"], default="all")
    args = p.parse_args()
    keys = ["C1", "C2", "C3"] if args.strategy == "all" else [args.strategy]
    generate_answers(keys)
