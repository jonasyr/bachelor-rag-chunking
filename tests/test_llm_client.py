from types import SimpleNamespace

import pytest

from config import LLM_MAX_TOKENS, LLM_MODEL, LLM_REASONING_EFFORT, LLM_SEED, LLM_TEMPERATURE
from llm_client import complete


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
        )
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

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
