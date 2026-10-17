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
    LLM_TEMPERATURE,
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
        "max_completion_tokens": LLM_MAX_TOKENS,
        "openai_sdk": version("openai"),
        **record,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": generation_cost(prompt_tokens, completion_tokens),
    }
    _append(full, runs_file)
    return full


def _append(record: dict, runs_file: Path) -> None:
    runs_file.parent.mkdir(parents=True, exist_ok=True)
    with runs_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _cost(tokens: int) -> float:
    return round(tokens / 1_000_000 * EMBEDDING_PRICE_PER_MTOK, 10)
