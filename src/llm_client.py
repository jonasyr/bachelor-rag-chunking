"""OpenAI chat completions for the answer generation (ADR 0014, 0033).

Every request carries the pinned settings of src/config.py: model, temperature 0, reasoning
effort "none" (the only effort at which the API accepts a temperature), the token limit and a
fixed seed (best effort only, so the answers are still stored once).
The API key is read only when a call is made, so tests never need it.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
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
    raw: dict = field(default_factory=dict)  # the whole API response, kept in the journal (D50)


Completer = Callable[[list[dict]], Completion]
ModelCreated = Callable[[], int]


def complete(
    messages: list[dict],
    client: Any = None,
    *,
    model: str = LLM_MODEL,
    reasoning_effort: str = LLM_REASONING_EFFORT,
    temperature: float = LLM_TEMPERATURE,
    max_tokens: int = LLM_MAX_TOKENS,
    seed: int = LLM_SEED,
    response_format: dict | None = None,
) -> Completion:
    """One answer to `messages` with the pinned settings (default: the answer model of ADR 0033;
    another step passes its own config values). `response_format` (structured output) is sent
    only when given, so the default request stays exactly the one the generation ran with."""
    client = client or _openai_client()
    request = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "reasoning_effort": reasoning_effort,
        "max_completion_tokens": max_tokens,
        "seed": seed,
    }
    if response_format is not None:
        request["response_format"] = response_format
    response = client.chat.completions.create(**request)
    choice = response.choices[0]
    return Completion(
        text=choice.message.content or "",
        model=response.model,
        finish_reason=choice.finish_reason,
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        system_fingerprint=getattr(response, "system_fingerprint", None),
        raw=response.model_dump(mode="json"),
    )


def model_created(client: Any = None, model: str = LLM_MODEL) -> int:
    """Creation time (Unix seconds) of the model object behind `model` (default config.LLM_MODEL);
    OpenAI offers no dated snapshot of it, so this is the only version marker the API reports
    (ADR 0033)."""
    client = client or _openai_client()
    return client.models.retrieve(model).created
