"""Run records for embedding, retrieval and generation (ADR 0008: costs; ADR 0016, 0033: versions
and dates)."""

import hashlib
import json
from datetime import date
from importlib.metadata import version
from pathlib import Path

from config import (
    EMBEDDING_MODEL,
    EMBEDDING_PRICE_PER_MTOK,
    EMBEDDING_RUNS_FILE,
    GENERATION_RUNS_FILE,
    LLM_MAX_TOKENS,
    LLM_MODEL,
    LLM_PRICE_INPUT_PER_MTOK,
    LLM_PRICE_OUTPUT_PER_MTOK,
    LLM_REASONING_EFFORT,
    LLM_SEED,
    LLM_TEMPERATURE,
    RAGAS_JUDGE_MODEL,
    RAGAS_JUDGE_PRICE_INPUT_PER_MTOK,
    RAGAS_JUDGE_PRICE_OUTPUT_PER_MTOK,
    RAGAS_REASONING_EFFORT,
    RAGAS_SEED,
    RAGAS_STRICTNESS,
    RAGAS_TEMPERATURE,
    SCORING_METHOD,
)


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def append_run(
    record: dict, input_tokens: int, runs_file: Path = EMBEDDING_RUNS_FILE, canary_tokens: int = 0
) -> dict:
    """Append one JSON line with model, versions, date, tokens and cost; return the full record.

    input_tokens/cost_usd cover the step's own texts (ADR 0008); the model-vintage check is
    logged apart (canary_*), so it never changes a strategy's cost.
    """
    full = {
        "date": date.today().isoformat(),
        "model": EMBEDDING_MODEL,
        "openai_sdk": version("openai"),
        "chromadb": version("chromadb"),
        **record,
        "input_tokens": input_tokens,
        "cost_usd": _cost(input_tokens),
        "canary_input_tokens": canary_tokens,
        "canary_cost_usd": _cost(canary_tokens),
        "api_called": input_tokens + canary_tokens > 0,
    }
    _append(full, runs_file)
    return full


def generation_cost(prompt_tokens: int, completion_tokens: int) -> float:
    return round(
        (prompt_tokens * LLM_PRICE_INPUT_PER_MTOK + completion_tokens * LLM_PRICE_OUTPUT_PER_MTOK)
        / 1_000_000,
        10,
    )


def append_generation_run(
    record: dict, prompt_tokens: int, completion_tokens: int, runs_file: Path = GENERATION_RUNS_FILE
) -> dict:
    """Append one JSON line with the pinned settings, versions, date, tokens and cost."""
    full = {
        "date": date.today().isoformat(),
        "model": LLM_MODEL,
        "reasoning_effort": LLM_REASONING_EFFORT,
        "temperature": LLM_TEMPERATURE,
        "seed": LLM_SEED,
        "max_completion_tokens": LLM_MAX_TOKENS,
        "openai_sdk": version("openai"),
        **record,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": generation_cost(prompt_tokens, completion_tokens),
    }
    _append(full, runs_file)
    return full


def append_ragas_run(record: dict, runs_file: Path) -> dict:
    """Build and append the record of a RAGAS run (see `ragas_record`)."""
    full = ragas_record(record)
    _append(full, runs_file)
    return full


def append_record(record: dict, runs_file: Path) -> None:
    """Append a record that was built beforehand."""
    _append(record, runs_file)


def ragas_record(record: dict) -> dict:
    """The record of a RAGAS run (ADR 0047): the pinned judge settings, versions, date and cost,
    judge and embeddings apart, from the tokens in `record`. Nothing is written."""
    judge = round(
        (
            record["judge_prompt_tokens"] * RAGAS_JUDGE_PRICE_INPUT_PER_MTOK
            + record["judge_completion_tokens"] * RAGAS_JUDGE_PRICE_OUTPUT_PER_MTOK
        )
        / 1_000_000,
        10,
    )
    full = {
        "date": date.today().isoformat(),
        "judge_model": RAGAS_JUDGE_MODEL,
        "embedding_model": EMBEDDING_MODEL,
        "reasoning_effort": RAGAS_REASONING_EFFORT,
        "temperature": RAGAS_TEMPERATURE,
        "seed": RAGAS_SEED,
        "strictness": RAGAS_STRICTNESS,
        "ragas_version": version("ragas"),
        "openai_sdk": version("openai"),
        **record,
        "judge_cost_usd": judge,
        "embedding_cost_usd": _cost(record["embedding_tokens"]),
    }
    full["cost_usd"] = round(full["judge_cost_usd"] + full["embedding_cost_usd"], 10)
    return full


def step_command(step: str, strategy: str) -> str:
    """The command that writes the `step` record over `strategy`, for error messages."""
    if step in ("scaffold", "summarise"):
        control = " --control" if strategy == "K0" else ""
        return f"src/evaluate_answers.py --mode {step}{control}"
    if step == "summarise_control":
        return "src/evaluate_answers.py --mode summarise --control"
    if step == "ragas_repeat":
        return "src/ragas_eval.py --repeat"
    if step == "ragas":
        return "src/ragas_eval.py"
    if step in ("retrieve", "evaluate_retrieval") and strategy == "K1":
        return f"src/{step}.py --control"
    return f"src/{step}.py"


def require_run(
    runs_file: Path,
    step: str,
    strategy: str,
    inputs: list[Path],
    outputs: list[Path],
    outputs_required: bool = True,
) -> dict:
    """The latest record of `step` over `strategy`; raise unless it hashed `inputs` and `outputs`
    exactly as they are now, so a later step never builds on files another run produced.

    Without `outputs_required`, a record that predates output checksums (no `outputs_sha256`)
    is checked on its inputs only.
    """
    record = latest_run(runs_file, step, strategy)
    if record is None:
        raise RuntimeError(
            f"{runs_file} has no {step} run over {strategy}; run {step_command(step, strategy)}"
        )
    checks = [("inputs_sha256", f) for f in inputs]
    if outputs_required or "outputs_sha256" in record:
        checks += [("outputs_sha256", f) for f in outputs]
    for field, path in checks:
        if record.get(field, {}).get(path.name) != sha256_of(path):
            raise RuntimeError(
                f"{path.name} differs from the latest {step} run of {record.get('date', '?')} "
                f"({runs_file}); run {step_command(step, strategy)} again"
            )
    return record


def latest_run(runs_file: Path, step: str, strategy: str) -> dict | None:
    """The latest record of `step` over `strategy`, or None."""
    if not runs_file.exists():
        return None
    records = [json.loads(line) for line in runs_file.read_text(encoding="utf-8").splitlines()]
    matching = [r for r in records if r.get("step") == step and r.get("strategy") == strategy]
    return matching[-1] if matching else None


def append_scaffold_run(
    strategy: str, codes: int, outputs: dict[str, str], runs_file: Path
) -> dict:
    """Log a fresh blind-scoring scaffold with the checksum of its item file (ADR 0034)."""
    full = {
        "date": date.today().isoformat(),
        "step": "scaffold",
        "strategy": strategy,
        "scoring": SCORING_METHOD,  # rule-based scoring is required for this scaffold (ADR 0036)
        "codes": codes,
        "outputs_sha256": outputs,
    }
    _append(full, runs_file)
    return full


def append_key_points_run(strategy: str, outputs: dict[str, str], runs_file: Path) -> dict:
    """Log the freeze of a set's key points with the file's checksum (ADR 0035)."""
    full = {
        "date": date.today().isoformat(),
        "step": "key_points",
        "strategy": strategy,
        "outputs_sha256": outputs,
    }
    _append(full, runs_file)
    return full


def append_step_run(
    step: str, strategy: str, inputs: list[Path], outputs: list[Path], runs_file: Path
) -> dict:
    """Log a local step (no API) with the checksums of its inputs and outputs, so a later step
    can check it builds on exactly these files (`require_run`)."""
    full = {
        "date": date.today().isoformat(),
        "step": step,
        "strategy": strategy,
        "inputs_sha256": {f.name: sha256_of(f) for f in inputs},
        "outputs_sha256": {f.name: sha256_of(f) for f in outputs},
    }
    _append(full, runs_file)
    return full


def _append(record: dict, runs_file: Path) -> None:
    runs_file.parent.mkdir(parents=True, exist_ok=True)
    with runs_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _cost(tokens: int) -> float:
    return round(tokens / 1_000_000 * EMBEDDING_PRICE_PER_MTOK, 10)
