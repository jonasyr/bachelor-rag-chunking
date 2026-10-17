import re
from pathlib import Path

from config import CONTEXT_SEPARATOR, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from prompt import context, messages

PROMPTS_DOC = Path(__file__).resolve().parent.parent / "docs" / "reference" / "prompts.md"


def documented_blocks():
    return re.findall(r"```\n(.*?)\n```", PROMPTS_DOC.read_text(encoding="utf-8"), re.S)


def test_prompts_match_the_documentation():
    """The prompt is an invariant (D6); code and docs/reference/prompts.md cannot drift apart."""
    assert documented_blocks()[:2] == [SYSTEM_PROMPT, USER_PROMPT_TEMPLATE]


def test_context_numbers_excerpts_in_rank_order():
    chunks = {"C1_D001_0002": {"text": "second"}, "C1_D001_0001": {"text": "first"}}
    assert context(["C1_D001_0002", "C1_D001_0001"], chunks) == (
        f"[Excerpt 1]\nsecond{CONTEXT_SEPARATOR}[Excerpt 2]\nfirst"
    )


def test_messages_fill_question_and_context():
    result = messages("How?", "[Excerpt 1]\ntext")
    assert result == [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(question="How?", context="[Excerpt 1]\ntext"),
        },
    ]


def test_braces_in_question_or_chunk_are_kept_verbatim():
    content = messages("Is {context} a slot in {{ msg }}?", "chunk with {question}")[1]["content"]
    assert "Question: Is {context} a slot in {{ msg }}?\n" in content
    assert content.endswith("excerpts:\nchunk with {question}\n\nAnswer:")
