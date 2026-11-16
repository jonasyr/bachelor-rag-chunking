"""Run records for embedding, retrieval and generation (ADR 0008: costs; ADR 0016, 0033: versions
and dates)."""

import hashlib
import json
import os
import platform
import subprocess
from datetime import date
from importlib.metadata import version
from pathlib import Path

from config import (
    CLOSED_BOOK_SYSTEM_PROMPT,
    CLOSED_BOOK_USER_TEMPLATE,
    CONTEXT_SEPARATOR,
    CONTROL_ANSWER_STRATEGIES,
    CONTROL_STRATEGIES,
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
    ROOT,
    SCORING_METHOD,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)

(K1,) = CONTROL_STRATEGIES  # "K1"
(K0,) = CONTROL_ANSWER_STRATEGIES  # "K0"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str | None:
    try:
        done = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True, timeout=30
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip()


def environment() -> dict:
    """Code and environment of a run (ADR 0050): commit, uncommitted changes, Python and the
    checksum of uv.lock (every package version), so the run can be tied to its exact code."""
    status = _git("status", "--porcelain")
    lock = ROOT / "uv.lock"
    return {
        "git_commit": _git("rev-parse", "HEAD"),
        "git_dirty": None if status is None else bool(status),
        "python": platform.python_version(),
        "uv_lock_sha256": sha256_of(lock) if lock.exists() else None,
    }


def require_clean_tree() -> None:
    """Refuse an API step of the main run while the repository has uncommitted changes, so the
    commit in its record is exactly the code that ran (ADR 0050)."""
    status = _git("status", "--porcelain")
    if status is None:
        raise RuntimeError("git status failed; the main run needs the repository (ADR 0050)")
    if status:
        raise RuntimeError(
            "the repository has uncommitted changes; commit them first so the run record names "
            f"the exact code (ADR 0050):\n{status}"
        )


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
        **environment(),
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


def generation_settings() -> dict:
    """The pinned settings of the answer model (ADR 0033) and the SDK that sent them."""
    return {
        "model": LLM_MODEL,
        "reasoning_effort": LLM_REASONING_EFFORT,
        "temperature": LLM_TEMPERATURE,
        "seed": LLM_SEED,
        "max_completion_tokens": LLM_MAX_TOKENS,
        "openai_sdk": version("openai"),
    }


def prompts_sha256() -> str:
    """Checksum of the answer prompts in force (RAG and closed-book, docs/reference/prompts.md)."""
    text = "\x00".join(
        [
            SYSTEM_PROMPT,
            USER_PROMPT_TEMPLATE,
            CONTEXT_SEPARATOR,
            CLOSED_BOOK_SYSTEM_PROMPT,
            CLOSED_BOOK_USER_TEMPLATE,
        ]
    )
    return hashlib.sha256(text.encode()).hexdigest()


def append_generation_run(
    record: dict, prompt_tokens: int, completion_tokens: int, runs_file: Path = GENERATION_RUNS_FILE
) -> dict:
    """Append one JSON line with the pinned settings, versions, date, tokens and cost."""
    full = {
        "date": date.today().isoformat(),
        **generation_settings(),
        **environment(),
        **record,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": generation_cost(prompt_tokens, completion_tokens),
    }
    _append(full, runs_file)
    return full


def append_record(record: dict, runs_file: Path) -> None:
    """Append a record that was built beforehand."""
    _append(record, runs_file)


def ragas_settings() -> dict:
    """The pinned judge settings of a RAGAS run (ADR 0047) and the library versions."""
    return {
        "judge_model": RAGAS_JUDGE_MODEL,
        "embedding_model": EMBEDDING_MODEL,
        "reasoning_effort": RAGAS_REASONING_EFFORT,
        "temperature": RAGAS_TEMPERATURE,
        "seed": RAGAS_SEED,
        "strictness": RAGAS_STRICTNESS,
        "ragas_version": version("ragas"),
        "openai_sdk": version("openai"),
    }


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
        **ragas_settings(),
        **environment(),
        **record,
        "judge_cost_usd": judge,
        "embedding_cost_usd": _cost(record["embedding_tokens"]),
    }
    full["cost_usd"] = round(full["judge_cost_usd"] + full["embedding_cost_usd"], 10)
    return full


def step_command(step: str, strategy: str) -> str:
    """The command that writes the `step` record over `strategy`, for error messages."""
    if step in ("scaffold", "summarise"):
        control = " --control" if strategy == K0 else ""
        return f"src/evaluate_answers.py --mode {step}{control}"
    if step == "summarise_control":
        return "src/evaluate_answers.py --mode summarise --control"
    if step.startswith("second_rater_"):
        return f"src/second_rater.py --mode {step.removeprefix('second_rater_')}"
    if step == "ragas_repeat":
        return "src/ragas_eval.py --repeat"
    if step == "ragas":
        return "src/ragas_eval.py"
    if step in ("retrieve", "evaluate_retrieval") and strategy == K1:
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
    records = []
    for n, line in enumerate(runs_file.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            raise ValueError(
                f"{runs_file}: line {n} is not JSON (a write cut off by a killed process?); "
                "check that line and remove it if it is a torn record"
            ) from None
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
    step: str,
    strategy: str,
    inputs: list[Path],
    outputs: list[Path],
    runs_file: Path,
    extra: dict | None = None,
) -> dict:
    """Log a local step (no API) with the checksums of its inputs and outputs, so a later step
    can check it builds on exactly these files (`require_run`); `extra` adds step fields."""
    full = {
        "date": date.today().isoformat(),
        "step": step,
        "strategy": strategy,
        "inputs_sha256": {f.name: sha256_of(f) for f in inputs},
        "outputs_sha256": {f.name: sha256_of(f) for f in outputs},
        **(extra or {}),
    }
    _append(full, runs_file)
    return full


def _append(record: dict, runs_file: Path) -> None:
    runs_file.parent.mkdir(parents=True, exist_ok=True)
    with runs_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def _cost(tokens: int) -> float:
    return round(tokens / 1_000_000 * EMBEDDING_PRICE_PER_MTOK, 10)
