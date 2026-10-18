import pytest

from preprocess import clean_markdown, fence_marker


def test_bom_crlf_and_blank_runs_normalised():
    result = clean_markdown("﻿# T {#t}\r\n\r\n\r\n\r\nText.\r\n")
    assert result.text == "# T\n\nText.\n"


def test_headings_recorded_with_offsets_and_anchors_removed():
    text = "# Page {#page}\n\nIntro.\n\n## Part `a` {#part-a}\n\n#### Deep\n\nx\n"
    result = clean_markdown(text)
    assert result.text == "# Page\n\nIntro.\n\n## Part `a`\n\n#### Deep\n\nx\n"
    assert [(h.level, h.title, h.anchor) for h in result.headings] == [
        (1, "Page", "page"),
        (2, "Part `a`", "part-a"),
    ]
    assert result.text[result.headings[1].offset :].startswith("## Part")


def test_fence_info_strings_reduced_and_code_untouched():
    text = "# T {#t}\n\n```ts {1}\n## not a heading <div>\n```\n\n~~~bash\n# comment\n~~~\n"
    result = clean_markdown(text)
    assert "```ts\n## not a heading <div>\n```" in result.text
    assert "~~~bash\n# comment\n~~~" in result.text
    assert len(result.headings) == 1


def test_fence_closes_only_with_same_marker():
    assert fence_marker("```ts") == "```"
    assert fence_marker("``` a`b") is None
    result = clean_markdown("# T {#t}\n\n~~~\n```\n## x {#x}\n~~~\n")
    assert len(result.headings) == 1


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("# T {#t}\n\n## Y\n", "heading without anchor"),
        ("# T {#t}\n\n## A {#a}\n\n## B {#a}\n", "duplicate anchor"),
        ("## Only {#o}\n", "exactly one H1"),
        ("# A {#a}\n\n# B {#b}\n", "exactly one H1"),
        ("# T {#t}\n\n```ts\nopen\n", "unclosed code fence"),
        ("# T {#t}\n\n<div>\n", "unhandled HTML"),
        ("# T {#t}\n\nSee <b>this</b>.\n", "unhandled inline HTML"),
    ],
)
def test_anomalies_raise(body, message):
    with pytest.raises(ValueError, match=message):
        clean_markdown(body)


def test_escaped_lt_and_inline_code_are_not_html():
    result = clean_markdown("# T {#t}\n\nUse `<div>` and \\<b> literally.\n")
    assert "Use `<div>` and \\<b> literally." in result.text
