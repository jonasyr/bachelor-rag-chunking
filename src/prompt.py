"""The prompts of the answer generation (docs/reference/prompts.md): the RAG prompt, the same
for every strategy (ADR 0006), and the closed-book prompt of the screen and K0 (ADR 0040). The
scoring packet shows the excerpts in the same form (ADR 0032)."""

from config import (
    CLOSED_BOOK_SYSTEM_PROMPT,
    CLOSED_BOOK_USER_TEMPLATE,
    CONTEXT_SEPARATOR,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)


def context(chunk_ids: list[str], chunks: dict[str, dict]) -> str:
    """The chunks in the given (rank) order as numbered excerpts, without chunk IDs."""
    return CONTEXT_SEPARATOR.join(
        f"[Excerpt {n}]\n{chunks[cid]['text']}" for n, cid in enumerate(chunk_ids, start=1)
    )


def messages(question: str, excerpts: str) -> list[dict]:
    """System and user message; braces in question or excerpts stay as they are."""
    user = USER_PROMPT_TEMPLATE.format(question=question, context=excerpts)
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


def closed_book_messages(question: str) -> list[dict]:
    """System and user message without any excerpt (screen and K0, ADR 0040); braces stay."""
    user = CLOSED_BOOK_USER_TEMPLATE.format(question=question)
    return [
        {"role": "system", "content": CLOSED_BOOK_SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
