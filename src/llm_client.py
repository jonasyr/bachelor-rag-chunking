"""OpenAI chat completions for the answer generation (ADR 0014, 0033).

Every request carries the pinned settings of src/config.py: model, temperature 0, reasoning
effort "none" (the only effort at which the API accepts a temperature), the token limit and a
fixed seed (best effort only, so the answers are still stored once).
The API key is read only when a call is made, so tests never need it.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from config import LLM_MAX_TOKENS, LLM_MODEL, LLM_REASONING_EFFORT, LLM_SEED, LLM_TEMPERATURE
from embedding_client import _openai_client


@dataclass(frozen=True)
class Completion:
    text: str
    model: str  # as reported by the API; the alias may stand for a dated version
    finish_reason: str  # "stop" for a complete answer
    prompt_tokens: int  # as billed (usage)
    completion_tokens: int
    system_fingerprint: str | None


Completer = Callable[[list[dict]], Completion]
ModelCreated = Callable[[], int]


def complete(messages: list[dict], client: Any = None) -> Completion:
    """One answer to `messages` with the pinned settings."""
    client = client or _openai_client()
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=LLM_TEMPERATURE,
        reasoning_effort=LLM_REASONING_EFFORT,
        max_completion_tokens=LLM_MAX_TOKENS,
        seed=LLM_SEED,
    )
    choice = response.choices[0]
    return Completion(
        text=choice.message.content or "",
        model=response.model,
        finish_reason=choice.finish_reason,
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        system_fingerprint=getattr(response, "system_fingerprint", None),
    )


def model_created(client: Any = None, model: str = LLM_MODEL) -> int:
    """Creation time (Unix seconds) of the model object behind `model` (default config.LLM_MODEL);
    OpenAI offers no dated snapshot of it, so this is the only version marker the API reports
    (ADR 0033)."""
    client = client or _openai_client()
    return client.models.retrieve(model).created
