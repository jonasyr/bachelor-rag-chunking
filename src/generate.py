"""Answer generation (ADR 0006, 0014, 0033).

For every question of the catalogue and every experiment strategy C1-C3, builds the prompt from
the top-k chunks of retrieved_results.csv in rank order (docs/reference/prompts.md), asks the
pinned model (config.LLM_MODEL, temperature 0, reasoning effort "none") and writes
generated_answers.csv. All strategies run together from the same inputs; the control K1 gets no
answers (ADR 0026). The main catalogue is used only while it matches its freeze record (ADR
0030), and everything is checked before the first API call.

OpenAI offers the model only as an alias, so the answers are generated once: an existing
answer file is never overwritten, the results must come from the latest retrieval run over the
current questions and chunk files, and the run stops without writing anything if an answer is
cut off or empty, or if the API reports a different model within the run. The run log records
the model the API reported, the input checksums, tokens and cost per strategy.

Output schema (docs/reference/data-formats.md): question_id, strategy, answer, sources,
prompt_tokens, completion_tokens
"""

from pathlib import Path

from atomic_csv import write_csv
from config import (
    CATALOGUE_FREEZE_FILE,
    CHUNK_FILES,
    DOCUMENTS_FILE,
    EMBEDDING_RUNS_FILE,
    GENERATED_ANSWERS_FILE,
    GENERATION_RUNS_FILE,
    GROUND_TRUTH_FILE,
    ID_SEPARATOR,
    PILOT_RUNS_FILE_NAME,
    QUESTIONS_FILE,
    RETRIEVED_RESULTS_FILE,
    SECTIONS_FILE,
    STRATEGY_IDS,
)
from embed import load_jsonl
from evaluate_retrieval import ranked_results
from freeze import require_frozen
from llm_client import Completer, Completion, complete
from prompt import context, messages
from retrieve import QUESTIONS_HEADER, QUESTIONS_REQUIRED, read_rows
from run_log import append_generation_run, generation_cost, require_run, sha256_of

ANSWERS_HEADER = [
    "question_id",
    "strategy",
    "answer",
    "sources",
    "prompt_tokens",
    "completion_tokens",
]


def checked(answer: Completion, label: str, models: set[str]) -> Completion:
    """The answer, unless it is cut off, empty or from another model than the run so far."""
    if answer.finish_reason != "stop":
        raise RuntimeError(
            f"{label}: the answer ended with finish_reason={answer.finish_reason!r}, not 'stop'; "
            "nothing was written (ADR 0033)"
        )
    if not answer.text.strip():
        raise RuntimeError(f"{label}: the answer is empty; nothing was written (ADR 0033)")
    models.add(answer.model)
    if len(models) > 1:
        raise RuntimeError(
            f"{label}: the API reported the models {sorted(models)} within one run; nothing was "
            "written (ADR 0033)"
        )
    return answer


def generate(
    completer: Completer = complete,
    results_file: Path = RETRIEVED_RESULTS_FILE,
    questions_file: Path = QUESTIONS_FILE,
    ground_truth_file: Path = GROUND_TRUTH_FILE,
    sections_file: Path = SECTIONS_FILE,
    documents_file: Path = DOCUMENTS_FILE,
    freeze_file: Path = CATALOGUE_FREEZE_FILE,
    chunk_files: dict[str, Path] = CHUNK_FILES,
    out_file: Path = GENERATED_ANSWERS_FILE,
    runs_file: Path = GENERATION_RUNS_FILE,
    retrieval_runs_file: Path = EMBEDDING_RUNS_FILE,
) -> int:
    """Write one answer per question and experiment strategy; return the number of answers."""
    if out_file.exists():
        raise FileExistsError(
            f"{out_file} exists; answers are generated once (ADR 0033), delete it deliberately "
            "to generate them again"
        )
    require_frozen(questions_file, ground_truth_file, sections_file, documents_file, freeze_file)
    keys = list(STRATEGY_IDS)  # always the complete experiment, never K1 (ADR 0026)
    if sorted(chunk_files) != sorted(keys):
        raise ValueError(f"chunk_files must cover exactly the strategies {sorted(keys)}")
    questions = sorted(
        read_rows(questions_file, "question catalogue", QUESTIONS_HEADER, QUESTIONS_REQUIRED),
        key=lambda q: q["question_id"],
    )
    chunks = {
        c["chunk_id"]: c
        for key in keys
        for c in load_jsonl(chunk_files[key], "run src/chunking.py first")
    }
    qids = [q["question_id"] for q in questions]
    inputs = [questions_file, ground_truth_file, *(chunk_files[k] for k in keys)]
    # the results must come from the latest retrieval over exactly these files (ADR 0033)
    require_run(retrieval_runs_file, "retrieve", ",".join(keys), inputs, [results_file], False)
    grouped = ranked_results(results_file, qids, keys, chunks)

    rows: list[dict] = []
    models: set[str] = set()
    fingerprints: set[str] = set()
    tokens = {key: [0, 0] for key in keys}  # prompt, completion
    for question in questions:
        qid = question["question_id"]
        for key in keys:
            sources = [r["chunk_id"] for r in grouped[(qid, key)]]
            answer = checked(
                completer(messages(question["question"], context(sources, chunks))),
                f"{qid}/{key}",
                models,
            )
            if answer.system_fingerprint:
                fingerprints.add(answer.system_fingerprint)
            tokens[key][0] += answer.prompt_tokens
            tokens[key][1] += answer.completion_tokens
            rows.append(
                {
                    "question_id": qid,
                    "strategy": key,
                    "answer": answer.text,
                    "sources": ID_SEPARATOR.join(sources),
                    "prompt_tokens": answer.prompt_tokens,
                    "completion_tokens": answer.completion_tokens,
                }
            )

    write_csv(out_file, ANSWERS_HEADER, rows)
    append_generation_run(
        {
            "step": "generate",
            "strategy": ",".join(keys),
            "model_reported": next(iter(models), None),
            "system_fingerprints": sorted(fingerprints),
            "answers": len(rows),
            "inputs_sha256": {f.name: sha256_of(f) for f in [results_file, *inputs]},
            "outputs_sha256": {out_file.name: sha256_of(out_file)},
            "by_strategy": {
                key: {
                    "prompt_tokens": p,
                    "completion_tokens": c,
                    "cost_usd": generation_cost(p, c),
                }
                for key, (p, c) in tokens.items()
            },
        },
        sum(p for p, _ in tokens.values()),
        sum(c for _, c in tokens.values()),
        runs_file,
    )
    return len(rows)


def pilot_paths(set_dir: Path) -> dict[str, Path]:
    """The files of a pilot set (data/pilot/...); it has no freeze record and its own run log."""
    return {
        "results_file": set_dir / RETRIEVED_RESULTS_FILE.name,
        "questions_file": set_dir / QUESTIONS_FILE.name,
        "ground_truth_file": set_dir / GROUND_TRUTH_FILE.name,
        "out_file": set_dir / GENERATED_ANSWERS_FILE.name,
        "runs_file": set_dir / PILOT_RUNS_FILE_NAME,
        "retrieval_runs_file": set_dir / PILOT_RUNS_FILE_NAME,
    }


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(
        description="Generate one answer per question and strategy C1-C3 (ADR 0033)."
    )
    p.add_argument(
        "--set", type=Path, metavar="DIR", help="a pilot set (e.g. data/pilot/hard) instead"
    )
    args = p.parse_args()
    paths: dict = pilot_paths(args.set) if args.set else {}
    count = generate(**paths)
    print(f"{count} answers -> {paths.get('out_file', GENERATED_ANSWERS_FILE)}")
