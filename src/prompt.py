"""The prompt of the answer generation (docs/reference/prompts.md), the same for every strategy
(ADR 0006). The scoring packet shows the excerpts in the same form (ADR 0032)."""

from config import CONTEXT_SEPARATOR, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


def context(chunk_ids: list[str], chunks: dict[str, dict]) -> str:
    """The chunks in the given (rank) order as numbered excerpts, without chunk IDs."""
    return CONTEXT_SEPARATOR.join(
        f"[Excerpt {n}]\n{chunks[cid]['text']}" for n, cid in enumerate(chunk_ids, start=1)
    )


def messages(question: str, excerpts: str) -> list[dict]:
    """System and user message; braces in question or excerpts stay as they are."""
    user = USER_PROMPT_TEMPLATE.format(question=question, context=excerpts)
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]
