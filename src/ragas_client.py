"""Async OpenAI client for the RAGAS run that records what the API reports (ADR 0033, 0047).

Every response passes through `ApiRecorder.on_response`: it collects the reported model names
and system fingerprints and sums the billed tokens. `check()` refuses a run in which the judge
changed (more than one model or fingerprint), so the scores are not written.
"""

import asyncio
import math
import os
from typing import TYPE_CHECKING, Any

import httpx
from dotenv import load_dotenv
from openai import AsyncOpenAI

from config import (
    EMBEDDING_MODEL,
    RAGAS_CONCURRENCY,
    RAGAS_JUDGE_MODEL,
    RAGAS_MAX_RETRIES,
    RAGAS_NAN_REASONS,
    RAGAS_REASONING_EFFORT,
    RAGAS_SEED,
    RAGAS_STRICTNESS,
    RAGAS_TEMPERATURE,
    RAGAS_TIMEOUT_S,
)

if TYPE_CHECKING:
    from ragas_eval import MetricValue, Sample, Scorer


class ApiRecorder:
    def __init__(self) -> None:
        self.models: set[str] = set()
        self.fingerprints: set[str] = set()
        self.chat_prompt_tokens = 0
        self.chat_completion_tokens = 0
        self.embedding_tokens = 0

    async def on_response(self, response: httpx.Response) -> None:
        path = response.request.url.path
        chat = path.endswith("/chat/completions")
        if not (chat or path.endswith("/embeddings")) or response.status_code != 200:
            return
        await response.aread()
        body = response.json()
        usage = body.get("usage") or {}
        if chat:
            if body.get("model"):
                self.models.add(body["model"])
            if body.get("system_fingerprint"):
                self.fingerprints.add(body["system_fingerprint"])
            self.chat_prompt_tokens += usage.get("prompt_tokens", 0)
            self.chat_completion_tokens += usage.get("completion_tokens", 0)
        else:
            self.embedding_tokens += usage.get("prompt_tokens", 0)

    def check(self) -> None:
        if len(self.models) > 1:
            raise RuntimeError(
                f"the judge reported several models {sorted(self.models)}; "
                "nothing was written (ADR 0033)"
            )
        if len(self.fingerprints) > 1:
            raise RuntimeError(
                f"the judge reported several system fingerprints {sorted(self.fingerprints)}; "
                "nothing was written (ADR 0033)"
            )


def async_client(
    recorder: ApiRecorder, transport: httpx.AsyncBaseTransport | None = None
) -> AsyncOpenAI:
    """AsyncOpenAI client whose every response is reported to `recorder`.
    The key is read from the environment only when no test transport is given."""
    api_key = "test-key"
    if transport is None:
        load_dotenv()
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set; copy .env.example to .env and add your key"
            )
    http = httpx.AsyncClient(
        transport=transport,
        timeout=RAGAS_TIMEOUT_S,
        event_hooks={"response": [recorder.on_response]},
    )
    return AsyncOpenAI(
        api_key=api_key,
        http_client=http,
        max_retries=RAGAS_MAX_RETRIES,
    )


def build_metrics(client: AsyncOpenAI) -> dict[str, Any]:
    """The four RAGAS metrics (collections API), all on the pinned judge, keyed by config name."""
    from ragas.embeddings.base import embedding_factory
    from ragas.llms import llm_factory
    from ragas.metrics.collections import (
        AnswerRelevancy,
        ContextPrecisionWithReference,
        ContextRecall,
        Faithfulness,
    )

    llm = llm_factory(
        RAGAS_JUDGE_MODEL,
        client=client,
        temperature=RAGAS_TEMPERATURE,
        seed=RAGAS_SEED,
        reasoning_effort=RAGAS_REASONING_EFFORT,
    )
    embeddings = embedding_factory(provider="openai", model=EMBEDDING_MODEL, client=client)
    return {
        "faithfulness": Faithfulness(llm=llm),
        "response_relevancy": AnswerRelevancy(
            llm=llm, embeddings=embeddings, strictness=RAGAS_STRICTNESS
        ),
        "context_precision": ContextPrecisionWithReference(llm=llm),
        "context_recall": ContextRecall(llm=llm),
    }


def _arguments(name: str, sample: "Sample") -> dict[str, Any]:
    contexts = list(sample.retrieved_contexts)
    if name == "response_relevancy":
        return {"user_input": sample.user_input, "response": sample.response}
    if name == "faithfulness":
        return {
            "user_input": sample.user_input,
            "response": sample.response,
            "retrieved_contexts": contexts,
        }
    return {
        "user_input": sample.user_input,
        "reference": sample.reference,
        "retrieved_contexts": contexts,
    }


def _value(name: str, result: Any) -> "MetricValue":
    """(value, reason). A NaN carries RAGAS' own reason, else the fixed text of RAGAS_NAN_REASONS;
    a metric without such a text gets an empty reason, which `validated` refuses."""
    value = float(result.value)
    if math.isnan(value):
        return None, result.reason or RAGAS_NAN_REASONS.get(name, "")
    return value, ""


def scorer_for(metrics: dict[str, Any]) -> "Scorer":
    """Scorer over the given metrics: all (sample, metric) jobs run concurrently, at most
    RAGAS_CONCURRENCY at a time; results come back in sample order. Any exception propagates."""

    async def score_all(samples: "list[Sample]") -> "list[dict[str, MetricValue]]":
        gate = asyncio.Semaphore(RAGAS_CONCURRENCY)

        async def one(name: str, sample: "Sample") -> "MetricValue":
            async with gate:
                result = await metrics[name].ascore(**_arguments(name, sample))
            return _value(name, result)

        names = list(metrics)
        jobs = [one(name, sample) for sample in samples for name in names]
        flat = await asyncio.gather(*jobs)
        width = len(names)
        return [
            dict(zip(names, flat[i * width : (i + 1) * width], strict=True))
            for i in range(len(samples))
        ]

    return lambda samples: asyncio.run(score_all(samples))


def make_scorer(client: AsyncOpenAI) -> "Scorer":
    return scorer_for(build_metrics(client))
