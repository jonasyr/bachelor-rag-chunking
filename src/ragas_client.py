"""Async OpenAI client for the RAGAS run that records what the API reports (ADR 0033, 0047).

Every response passes through `ApiRecorder.on_response`: it collects the reported model names
and system fingerprints and sums the billed tokens. `check()` refuses a run in which the judge
changed (more than one model or fingerprint), so the scores are not written.
"""

import os

import httpx
from dotenv import load_dotenv
from openai import AsyncOpenAI

from config import RAGAS_MAX_RETRIES, RAGAS_TIMEOUT_S


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
