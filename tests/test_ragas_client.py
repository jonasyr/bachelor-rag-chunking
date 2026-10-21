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


# --- the real scorer (Task 3) -------------------------------------------------------------

import json  # noqa: E402

from pydantic import BaseModel  # noqa: E402

import ragas_client  # noqa: E402
from config import (  # noqa: E402
    EMBEDDING_MODEL,
    RAGAS_JUDGE_MODEL,
    RAGAS_MAX_TOKENS,
    RAGAS_METRICS,
    RAGAS_NAN_REASONS,
    RAGAS_REASONING_EFFORT,
    RAGAS_SEED,
    RAGAS_STRICTNESS,
    RAGAS_TEMPERATURE,
)
from ragas_eval import Sample  # noqa: E402


def sample(n: int) -> Sample:
    return Sample(f"Q{n}", "C1", f"question {n}", f"answer {n}", ("chunk a", "chunk b"), f"ref {n}")


def mock_client(handler=_handler):
    return async_client(ApiRecorder(), httpx.MockTransport(handler))


def test_make_scorer_builds_the_four_metrics():
    from ragas.metrics.collections import (
        AnswerRelevancy,
        ContextPrecisionWithReference,
        ContextRecall,
        Faithfulness,
    )

    metrics = ragas_client.build_metrics(mock_client())
    assert tuple(metrics) == RAGAS_METRICS
    assert isinstance(metrics["faithfulness"], Faithfulness)
    assert isinstance(metrics["response_relevancy"], AnswerRelevancy)
    assert isinstance(metrics["context_precision"], ContextPrecisionWithReference)
    assert isinstance(metrics["context_recall"], ContextRecall)
    assert metrics["response_relevancy"].strictness == RAGAS_STRICTNESS == 3
    for metric in metrics.values():
        assert metric.llm.model == RAGAS_JUDGE_MODEL
        args = metric.llm.model_args
        assert args["temperature"] == RAGAS_TEMPERATURE
        assert args["seed"] == RAGAS_SEED
        assert args["reasoning_effort"] == RAGAS_REASONING_EFFORT
    embeddings = metrics["response_relevancy"].embeddings
    assert embeddings.model == EMBEDDING_MODEL


class Stub:
    def __init__(self, results, delays=None):
        self.results = results
        self.delays = delays or {}
        self.calls = []

    async def ascore(self, **kwargs):
        self.calls.append(kwargs)
        key = kwargs["user_input"]
        await asyncio.sleep(self.delays.get(key, 0))
        return self.results[key]


def stubs(**overrides):
    out = {
        name: Stub({f"question {n}": ragas_result(n / 10) for n in range(3)})
        for name in RAGAS_METRICS
    }
    out.update(overrides)
    return out


def ragas_result(value, reason=None):
    from ragas.metrics.result import MetricResult

    return MetricResult(value=value, reason=reason)


def test_scorer_keeps_sample_order_and_maps_nan():
    # the first sample finishes last; the middle one is NaN with the metric's own reason
    slow = Stub(
        {
            "question 0": ragas_result(0.0),
            "question 1": ragas_result(float("nan"), "own reason"),
            "question 2": ragas_result(0.2),
        },
        delays={"question 0": 0.05, "question 1": 0.02},
    )
    metrics = stubs(faithfulness=slow)
    out = ragas_client.scorer_for(metrics)([sample(0), sample(1), sample(2)])
    assert [row["faithfulness"] for row in out] == [(0.0, ""), (None, "own reason"), (0.2, "")]
    assert [row["context_recall"][0] for row in out] == [0.0, 0.1, 0.2]
    assert all(set(row) == set(RAGAS_METRICS) for row in out)


def test_metrics_get_their_own_arguments():
    metrics = stubs()
    ragas_client.scorer_for(metrics)([sample(0)])
    assert metrics["faithfulness"].calls == [
        {
            "user_input": "question 0",
            "response": "answer 0",
            "retrieved_contexts": ["chunk a", "chunk b"],
        }
    ]
    assert metrics["response_relevancy"].calls == [
        {"user_input": "question 0", "response": "answer 0"}
    ]
    assert metrics["context_precision"].calls == [
        {
            "user_input": "question 0",
            "reference": "ref 0",
            "retrieved_contexts": ["chunk a", "chunk b"],
        }
    ]
    assert metrics["context_recall"].calls == [
        {
            "user_input": "question 0",
            "retrieved_contexts": ["chunk a", "chunk b"],
            "reference": "ref 0",
        }
    ]


@pytest.mark.parametrize("name", ["faithfulness", "context_precision", "context_recall"])
def test_bare_nan_gets_the_fixed_reason(name):
    nan = Stub({"question 0": ragas_result(float("nan"))})
    out = ragas_client.scorer_for(stubs(**{name: nan}))([sample(0)])
    assert out[0][name] == (None, RAGAS_NAN_REASONS[name])
    assert RAGAS_NAN_REASONS[name].strip()


def test_response_relevancy_nan_is_rejected():
    from ragas_eval import validated

    nan = Stub({"question 0": ragas_result(float("nan"))})
    out = ragas_client.scorer_for(stubs(response_relevancy=nan))([sample(0)])
    assert out[0]["response_relevancy"] == (None, "")
    assert "response_relevancy" not in RAGAS_NAN_REASONS
    with pytest.raises(RuntimeError):
        validated(sample(0), out[0])


def test_scoring_error_propagates():
    class Boom:
        async def ascore(self, **kwargs):
            raise ValueError("boom")

    with pytest.raises(ValueError):
        ragas_client.scorer_for(stubs(faithfulness=Boom()))([sample(0)])


def chat_body(content):
    return {
        "id": "c",
        "object": "chat.completion",
        "created": 1,
        "model": "gpt-6-sol",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": content},
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


def captured_request_body() -> dict:
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json=chat_body('{"x": 1}'))

    class Out(BaseModel):
        x: int

    metric = ragas_client.build_metrics(mock_client(handler))["faithfulness"]
    assert asyncio.run(metric.llm.agenerate("hi", Out)).x == 1
    return bodies[0]


def test_seed_and_reasoning_effort_reach_the_request():
    body = captured_request_body()
    assert body["max_completion_tokens"] == RAGAS_MAX_TOKENS == 4096
    assert body["model"] == RAGAS_JUDGE_MODEL
    assert body["seed"] == RAGAS_SEED
    assert body["reasoning_effort"] == RAGAS_REASONING_EFFORT


def test_temperature_reaches_the_request():
    assert captured_request_body()["temperature"] == RAGAS_TEMPERATURE


def test_temperature_is_kept_only_with_reasoning_effort_none():
    judge = ragas_client.build_metrics(mock_client())["faithfulness"].llm
    judge.model_args["reasoning_effort"] = "low"
    assert judge._map_provider_params()["temperature"] == 1.0  # ragas' own rule applies


def test_subclass_tied_to_pinned_ragas():
    import ragas

    # JudgeLLM overrides ragas 0.4.3 InstructorLLM._map_openai_params; recheck it on a version bump
    assert ragas.__version__ == "0.4.3"


def test_truncated_judge_output_is_an_error():
    def handler(request):
        body = chat_body('{"x"')
        body["choices"][0]["finish_reason"] = "length"
        return httpx.Response(200, json=body)

    class Out(BaseModel):
        x: int

    llm = ragas_client.build_metrics(mock_client(handler))["faithfulness"].llm
    with pytest.raises(Exception) as caught:  # instructor: IncompleteOutputException
        asyncio.run(llm.agenerate("hi", Out))
    assert type(caught.value).__name__ == "IncompleteOutputException"


def test_main_wires_the_scorer_without_network(monkeypatch):
    import ragas_eval

    seen = {}
    monkeypatch.setattr(
        ragas_client,
        "async_client",
        lambda recorder: async_client(recorder, httpx.MockTransport(_handler)),
    )

    def fake_run(scorer, recorder, model_created, paths, main, repeat=False):
        seen.update(scorer=scorer, recorder=recorder, main=main, repeat=repeat, paths=paths)
        return 0

    monkeypatch.setattr(ragas_eval, "run", fake_run)
    ragas_eval.main([])
    assert callable(seen["scorer"])
    assert isinstance(seen["recorder"], ApiRecorder)
    assert seen["main"] is True and seen["repeat"] is False
