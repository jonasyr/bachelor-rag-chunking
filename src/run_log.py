"""Run records for embedding and retrieval (ADR 0008: costs; ADR 0016: versions and dates)."""

import hashlib
import json
from datetime import date
from importlib.metadata import version
from pathlib import Path

from config import EMBEDDING_MODEL, EMBEDDING_PRICE_PER_MTOK, EMBEDDING_RUNS_FILE


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
    runs_file.parent.mkdir(parents=True, exist_ok=True)
    with runs_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(full, ensure_ascii=False) + "\n")
    return full


def _cost(tokens: int) -> float:
    return round(tokens / 1_000_000 * EMBEDDING_PRICE_PER_MTOK, 10)
