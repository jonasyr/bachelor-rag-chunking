import asyncio
from types import SimpleNamespace

import httpx
import pytest

from ragas_client import ApiRecorder, async_client


def _handler(request: httpx.Request) -> httpx.Response:
    if request.url.path.endswith("/chat/completions"):
        body = {
            "id": "c1",
            "object": "chat.completion",
            "created": 1,
            "model": "gpt-6-sol-2026-09",
            "system_fingerprint": "fp_1",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": "hi"},
                }
            ],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
        }
    else:
        body = {
            "object": "list",
            "model": "text-embedding-3-large",
            "data": [{"object": "embedding", "index": 0, "embedding": [0.1, 0.2]}],
            "usage": {"prompt_tokens": 7, "total_tokens": 7},
        }
    return httpx.Response(200, json=body)


def _response(model=None, fingerprint=None) -> httpx.Response:
    body = {"model": model, "system_fingerprint": fingerprint, "usage": {}}
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    return httpx.Response(200, json=body, request=request)


def test_recorder_counts_chat_and_embedding_usage():
    recorder = ApiRecorder()
    client = async_client(recorder, transport=httpx.MockTransport(_handler))

    async def run():
        await client.chat.completions.create(
            model="gpt-6-sol", messages=[{"role": "user", "content": "x"}]
        )
        await client.embeddings.create(model="text-embedding-3-large", input="x")

    asyncio.run(run())
    assert recorder.models == {"gpt-6-sol-2026-09"}
    assert recorder.fingerprints == {"fp_1"}
    assert recorder.chat_prompt_tokens == 100
    assert recorder.chat_completion_tokens == 20
    assert recorder.embedding_tokens == 7
    recorder.check()


def test_recorder_refuses_a_second_model():
    recorder = ApiRecorder()
    asyncio.run(recorder.on_response(_response(model="a", fingerprint="fp")))
    asyncio.run(recorder.on_response(_response(model="b", fingerprint="fp")))
    with pytest.raises(RuntimeError, match="nothing was written"):
        recorder.check()


def test_recorder_refuses_a_second_fingerprint():
    recorder = ApiRecorder()
    asyncio.run(recorder.on_response(_response(model="a", fingerprint="fp1")))
    asyncio.run(recorder.on_response(_response(model="a", fingerprint="fp2")))
    with pytest.raises(RuntimeError, match="nothing was written"):
        recorder.check()


def test_model_created_takes_the_model():
    from llm_client import model_created

    retrieved = []

    def retrieve(model):
        retrieved.append(model)
        return SimpleNamespace(created=5)

    fake = SimpleNamespace(models=SimpleNamespace(retrieve=retrieve))
    assert model_created(fake, model="gpt-6-sol") == 5
    assert retrieved == ["gpt-6-sol"]
