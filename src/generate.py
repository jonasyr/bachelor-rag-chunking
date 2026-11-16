"""Answer generation (ADR 0006, 0014, 0033).

For every question of the catalogue and every experiment strategy C1-C3, builds the prompt from
the top-k chunks of retrieved_results.csv in rank order (docs/reference/prompts.md), asks the
pinned model (config.LLM_MODEL, temperature 0, reasoning effort "none") and writes
generated_answers.csv. All strategies run together from the same inputs; the control K1 gets no
answers (ADR 0026). The control K0 answers every question once without excerpts (closed-book
prompt, ADR 0040) in the same run, into generated_answers_control.csv (ADR 0041). The main
catalogue is used only while it matches its freeze record (ADR 0030), and everything is checked
before the first API call.

OpenAI offers the model only as an alias, so the answers are generated once: an existing
answer file is never overwritten, the results must come from the latest retrieval run over the
current questions and chunk files, and the run stops without writing anything if an answer is
cut off or empty, if the API reports a different model or system fingerprint within the run, or
if the creation time of the model object behind the alias differs before and after the run.
The run log records the model and fingerprint the API reported, the input and output checksums,
tokens and cost per strategy.

Output schema of both files (docs/reference/data-formats.md): question_id, strategy, answer,
sources, prompt_tokens, completion_tokens
"""

import hashlib
import json
from dataclasses import asdict, fields
from datetime import UTC, datetime
from pathlib import Path

from atomic_csv import write_csv
from config import (
    CATALOGUE_FREEZE_FILE,
    CHUNK_FILES,
    CONTROL_ANSWER_STRATEGIES,
    DOCUMENTS_FILE,
    EMBEDDING_RUNS_FILE,
    GENERATED_ANSWERS_CONTROL_FILE,
    GENERATED_ANSWERS_FILE,
    GENERATION_JOURNAL_FILE,
    GENERATION_RUNS_FILE,
    GROUND_TRUTH_FILE,
    ID_SEPARATOR,
    LLM_MODEL,
    PILOT_RUNS_FILE_NAME,
    QUESTIONS_FILE,
    RETRIEVED_RESULTS_FILE,
    SECTIONS_FILE,
    STRATEGY_IDS,
)
from embed import load_jsonl
from embedding_client import drain_http_errors
from evaluate_retrieval import ranked_results
from freeze import is_main_catalogue, require_frozen
from journal import Journal
from llm_client import Completer, Completion, ModelCreated, complete, model_created
from prompt import closed_book_messages, context, messages
from retrieve import QUESTIONS_HEADER, QUESTIONS_REQUIRED, read_rows
from run_log import (
    append_generation_run,
    environment,
    generation_cost,
    generation_settings,
    prompts_sha256,
    require_run,
    session_commits,
    sha256_of,
)

ANSWERS_HEADER = [
    "question_id",
    "strategy",
    "answer",
    "sources",
    "prompt_tokens",
    "completion_tokens",
]


COMPLETION_FIELDS = [f.name for f in fields(Completion) if f.name != "raw"]


def messages_sha256(msgs: list[dict]) -> str:
    return hashlib.sha256(json.dumps(msgs, ensure_ascii=False).encode()).hexdigest()


def usage_detail(response: dict, name: str) -> int:
    """reasoning_tokens or cached_tokens from a raw response's usage details (0 if absent)."""
    usage = response.get("usage") or {}
    for details in ("completion_tokens_details", "prompt_tokens_details"):
        value = (usage.get(details) or {}).get(name)
        if value is not None:
            return int(value)
    return 0


def checked(answer: Completion, label: str, models: set[str], fingerprints: set[str]) -> Completion:
    """The answer, unless it is cut off, empty or from another model or backend configuration
    (system_fingerprint, when the API reports one) than the run so far."""
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
    if answer.system_fingerprint:
        fingerprints.add(answer.system_fingerprint)
    if len(fingerprints) > 1:
        raise RuntimeError(
            f"{label}: the backend configuration changed within one run (system_fingerprint "
            f"{sorted(fingerprints)}); nothing was written (ADR 0033)"
        )
    return answer


def created_iso(seconds: int) -> str:
    return datetime.fromtimestamp(seconds, UTC).isoformat()


def generate(
    completer: Completer = complete,
    model_created: ModelCreated = model_created,
    results_file: Path = RETRIEVED_RESULTS_FILE,
    questions_file: Path = QUESTIONS_FILE,
    ground_truth_file: Path = GROUND_TRUTH_FILE,
    sections_file: Path = SECTIONS_FILE,
    documents_file: Path = DOCUMENTS_FILE,
    freeze_file: Path = CATALOGUE_FREEZE_FILE,
    chunk_files: dict[str, Path] = CHUNK_FILES,
    out_file: Path = GENERATED_ANSWERS_FILE,
    control_file: Path = GENERATED_ANSWERS_CONTROL_FILE,
    runs_file: Path = GENERATION_RUNS_FILE,
    retrieval_runs_file: Path = EMBEDDING_RUNS_FILE,
    legacy_retrieval: bool = False,
    journal_file: Path | None = None,
) -> int:
    """Write one answer per question and experiment strategy; return the number of answers.

    `legacy_retrieval` lets a retrieval record without an output checksum (pilot sets, written
    before 17.10.2026) pass on its inputs; the main experiment always needs the checksum.
    """
    journal_file = journal_file or out_file.with_name(GENERATION_JOURNAL_FILE.name)
    for path in (out_file, control_file):
        if path.exists():
            raise FileExistsError(
                f"{path} exists; answers are generated once (ADR 0033). If it was written without "
                f"a run record (a stop right after writing), delete both answer files: a new run "
                f"takes every answer from {journal_file.name} and calls the API for none (ADR 0050)"
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
    require_run(
        retrieval_runs_file,
        "retrieve",
        ",".join(keys),
        inputs,
        [results_file],
        outputs_required=not legacy_retrieval,
    )
    grouped = ranked_results(results_file, qids, keys, chunks)

    created_before = model_created()  # free lookup, only after every local check
    jobs = [
        (
            q["question_id"],
            key,
            messages(
                q["question"],
                context([r["chunk_id"] for r in grouped[(q["question_id"], key)]], chunks),
            ),
        )
        for q in questions
        for key in keys
    ]
    (control,) = CONTROL_ANSWER_STRATEGIES  # K0: no retrieval, the closed-book prompt (ADR 0041)
    jobs += [(q["question_id"], control, closed_book_messages(q["question"])) for q in questions]
    journal = Journal(
        journal_file,
        {
            "step": "generate",
            "strategy": ",".join(keys),
            **generation_settings(),
            "prompts_sha256": prompts_sha256(),
            "model_created": created_iso(created_before),
            "inputs_sha256": {f.name: sha256_of(f) for f in [results_file, *inputs]},
        },
        session=environment(),
    )
    done = {(e["question_id"], e["strategy"]): e for e in journal.of("item")}
    answers: dict[tuple[str, str], Completion] = {}
    models: set[str] = set()
    fingerprints: set[str] = set()
    received = 0
    try:
        for qid, key, msgs in jobs:
            digest = messages_sha256(msgs)
            entry = done.get((qid, key))
            if entry is None:  # not yet paid for: ask the API and journal the answer at once
                answer = completer(msgs)
                entry = {
                    "kind": "item",
                    "question_id": qid,
                    "strategy": key,
                    "messages_sha256": digest,
                    **{k: v for k, v in asdict(answer).items() if k != "raw"},
                    "response": answer.raw,
                    "http_errors": drain_http_errors(),
                }
                journal.append(entry)
                received += 1
            elif entry["messages_sha256"] != digest:
                raise RuntimeError(
                    f"{qid}/{key}: the journaled answer was asked with another prompt; nothing "
                    "was written (ADR 0050)"
                )
            answers[(qid, key)] = checked(
                Completion(**{f: entry[f] for f in COMPLETION_FIELDS}),
                f"{qid}/{key}",
                models,
                fingerprints,
            )
        created_after = model_created()
        if created_after != created_before:
            raise RuntimeError(
                f"the model behind {LLM_MODEL} changed during the run (created "
                f"{created_iso(created_before)}, now {created_iso(created_after)}); nothing was "
                "written (ADR 0033)"
            )
    except BaseException as error:
        journal.abort(error, answers_received=received, http_errors=drain_http_errors())
        raise

    def row(qid: str, key: str) -> dict:
        answer = answers[(qid, key)]
        sources = [] if key == control else [r["chunk_id"] for r in grouped[(qid, key)]]
        return {
            "question_id": qid,
            "strategy": key,
            "answer": answer.text,
            "sources": ID_SEPARATOR.join(sources),
            "prompt_tokens": answer.prompt_tokens,
            "completion_tokens": answer.completion_tokens,
        }

    rows = [row(qid, key) for qid, key, _ in jobs if key != control]
    control_rows = [row(qid, key) for qid, key, _ in jobs if key == control]
    by_strategy = {}
    for key in [*keys, control]:
        items = [e for e in journal.of("item") if e["strategy"] == key]
        p = sum(e["prompt_tokens"] for e in items)
        c = sum(e["completion_tokens"] for e in items)
        by_strategy[key] = {
            "prompt_tokens": p,
            "completion_tokens": c,
            "reasoning_tokens": sum(usage_detail(e["response"], "reasoning_tokens") for e in items),
            "cached_tokens": sum(usage_detail(e["response"], "cached_tokens") for e in items),
            "cost_usd": generation_cost(p, c),
        }
    write_csv(out_file, ANSWERS_HEADER, rows)
    write_csv(control_file, ANSWERS_HEADER, control_rows)
    append_generation_run(
        {
            "step": "generate",
            "strategy": ",".join(keys),
            "model_reported": next(iter(models), None),
            "model_created": created_iso(created_before),
            "system_fingerprint": next(iter(fingerprints), None),
            "prompts_sha256": prompts_sha256(),
            "answers": len(rows),
            "control_answers": len(control_rows),
            "sessions": len(journal.of("session")),
            "session_commits": session_commits(journal),
            "aborts": len(journal.of("abort")),
            "http_errors": sum(len(e.get("http_errors", [])) for e in journal.entries),
            "inputs_sha256": {f.name: sha256_of(f) for f in [results_file, *inputs]},
            "outputs_sha256": {
                out_file.name: sha256_of(out_file),
                control_file.name: sha256_of(control_file),
                journal_file.name: sha256_of(journal_file),
            },
            "by_strategy": by_strategy,
        },
        sum(v["prompt_tokens"] for v in by_strategy.values()),
        sum(v["completion_tokens"] for v in by_strategy.values()),
        runs_file,
    )
    return len(rows)


def pilot_paths(set_dir: Path) -> dict:
    """The files of a pilot set (data/pilot/...); it has no freeze record and its own run log,
    whose retrieval records may predate output checksums."""
    return {
        "results_file": set_dir / RETRIEVED_RESULTS_FILE.name,
        "questions_file": set_dir / QUESTIONS_FILE.name,
        "ground_truth_file": set_dir / GROUND_TRUTH_FILE.name,
        "out_file": set_dir / GENERATED_ANSWERS_FILE.name,
        "control_file": set_dir / GENERATED_ANSWERS_CONTROL_FILE.name,
        "runs_file": set_dir / PILOT_RUNS_FILE_NAME,
        "retrieval_runs_file": set_dir / PILOT_RUNS_FILE_NAME,
        "legacy_retrieval": True,
    }


if __name__ == "__main__":
    import argparse
    import logging

    from run_log import require_clean_tree

    p = argparse.ArgumentParser(
        description="Generate one answer per question and strategy C1-C3 (ADR 0033)."
    )
    p.add_argument(
        "--set", type=Path, metavar="DIR", help="a pilot set (e.g. data/pilot/hard) instead"
    )
    args = p.parse_args()
    if args.set and is_main_catalogue(
        args.set / QUESTIONS_FILE.name, args.set / GROUND_TRUTH_FILE.name
    ):
        raise SystemExit(f"{args.set} holds the main catalogue; run without --set (ADR 0033)")
    paths = pilot_paths(args.set) if args.set else {}
    if not args.set:
        require_clean_tree()
    logging.basicConfig(format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("openai").setLevel(logging.INFO)  # shows each SDK retry (ADR 0050)
    count = generate(**paths)
    print(f"{count} answers -> {paths.get('out_file', GENERATED_ANSWERS_FILE)}")
    control_out = paths.get("control_file", GENERATED_ANSWERS_CONTROL_FILE)
    print(f"control K0 (one answer per question, no retrieval) -> {control_out}")
