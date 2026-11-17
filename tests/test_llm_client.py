from types import SimpleNamespace

import pytest

from config import LLM_MAX_TOKENS, LLM_MODEL, LLM_REASONING_EFFORT, LLM_SEED, LLM_TEMPERATURE
from llm_client import complete, model_created


class FakeOpenAI:
    """Mimics client.chat.completions.create and records every request (no network)."""

    def __init__(self, content="An answer.", finish_reason="stop", model="gpt-6-luna-x"):
        self.requests = []
        self.reply = SimpleNamespace(
            model=model,
            system_fingerprint="fp_1",
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=content), finish_reason=finish_reason
                )
            ],
            usage=SimpleNamespace(prompt_tokens=120, completion_tokens=30),
            model_dump=lambda mode: {"id": "chatcmpl-1", "model": model},
        )
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        self.models = SimpleNamespace(retrieve=self.retrieve)
        self.retrieved = []

    def retrieve(self, model):
        self.retrieved.append(model)
        return SimpleNamespace(id=model, created=1789406102)

    def create(self, **kwargs):
        self.requests.append(kwargs)
        return self.reply


def test_sends_the_pinned_settings():
    client = FakeOpenAI()
    messages = [{"role": "user", "content": "Q?"}]
    complete(messages, client=client)
    assert client.requests == [
        {
            "model": LLM_MODEL,
            "messages": messages,
            "temperature": LLM_TEMPERATURE,
            "reasoning_effort": LLM_REASONING_EFFORT,
            "max_completion_tokens": LLM_MAX_TOKENS,
            "seed": LLM_SEED,
        }
    ]


def test_returns_text_reported_model_and_usage():
    result = complete([{"role": "user", "content": "Q?"}], client=FakeOpenAI())
    assert result.text == "An answer."
    assert result.model == "gpt-6-luna-x"
    assert result.finish_reason == "stop"
    assert (result.prompt_tokens, result.completion_tokens) == (120, 30)
    assert result.system_fingerprint == "fp_1"


def test_missing_content_becomes_empty_text():
    result = complete([{"role": "user", "content": "Q?"}], client=FakeOpenAI(content=None))
    assert result.text == ""


def test_missing_key_raises_before_any_call(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("embedding_client.load_dotenv", lambda: None)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        complete([{"role": "user", "content": "Q?"}])


def test_model_created_reads_the_pinned_model():
    client = FakeOpenAI()
    assert model_created(client=client) == 1789406102
    assert client.retrieved == [LLM_MODEL]


def test_keeps_the_whole_response_for_the_journal():
    assert complete([], client=FakeOpenAI()).raw == {"id": "chatcmpl-1", "model": "gpt-6-luna-x"}


def test_complete_default_request_unchanged():
    """Without overrides the request is exactly the one the generation ran with (no
    response_format key), so generate.py stays reproducible."""
    client = FakeOpenAI()
    messages = [{"role": "user", "content": "Q?"}]
    complete(messages, client)
    assert list(client.requests[0]) == [
        "model",
        "messages",
        "temperature",
        "reasoning_effort",
        "max_completion_tokens",
        "seed",
    ]
    assert "response_format" not in client.requests[0]


def test_complete_overrides_settings_and_sends_response_format():
    client = FakeOpenAI()
    fmt = {"type": "json_schema", "json_schema": {"name": "x", "strict": True, "schema": {}}}
    complete(
        [],
        client,
        model="gpt-6-sol",
        reasoning_effort="none",
        temperature=0.0,
        max_tokens=77,
        seed=5,
        response_format=fmt,
    )
    assert client.requests == [
        {
            "model": "gpt-6-sol",
            "messages": [],
            "temperature": 0.0,
            "reasoning_effort": "none",
            "max_completion_tokens": 77,
            "seed": 5,
            "response_format": fmt,
        }
    ]


def test_complete_overrides_are_keyword_only():
    with pytest.raises(TypeError):
        complete([], FakeOpenAI(), "gpt-6-sol")
