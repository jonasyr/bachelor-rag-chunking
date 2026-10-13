import pytest

import tokens
from chunking import paragraph_breaks, structure_spans


def test_paragraph_breaks_ignore_blank_lines_inside_fences():
    text = "# T\n\nPara one.\n\n```js\na\n\nb\n```\n\nEnd.\n"
    starts = tokens.token_starts(text)
    n = len(starts)
    expected = [tokens.char_to_token(starts, text.index(s)) for s in ("Para", "```js", "End.")]
    assert paragraph_breaks(text, starts, 0, n) == expected
    inside = tokens.char_to_token(starts, text.index("b\n```"))
    assert inside not in paragraph_breaks(text, starts, 0, n)


@pytest.mark.parametrize(
    ("n", "boundaries", "breaks", "expected"),
    [
        # one chunk per heading segment
        (300, [0, 100, 200], [], [(0, 100), (100, 200), (200, 300)]),
        # a short heading-only segment merges forward
        (300, [0, 10, 110], [], [(0, 110), (110, 300)]),
        # short segments chain until they reach the floor
        (400, [0, 10, 20, 200], [], [(0, 200), (200, 400)]),
        # a short last segment merges backward
        (120, [0, 100], [], [(0, 120)]),
        # an oversized segment is cut at the furthest fitting paragraph break
        (1000, [0], [300, 600, 900], [(0, 600), (600, 1000)]),
        # a merged heading stays with the start of an oversized section
        (1010, [0, 10], [400, 700], [(0, 700), (700, 1010)]),
        # no tail under the floor: the break at 990 would leave 10 tokens
        (1000, [0], [700, 990], [(0, 700), (700, 1000)]),
        # a paragraph longer than the ceiling is cut hard
        (2000, [0], [1900], [(0, 800), (800, 1600), (1600, 2000)]),
        # a break right after a heading is not used: no piece under the floor in front
        (1331, [0], [6], [(0, 800), (800, 1331)]),
        # a hard cut never leaves a tail under the floor
        (820, [0], [], [(0, 770), (770, 820)]),
    ],
)
def test_structure_spans(n, boundaries, breaks, expected):
    assert structure_spans(n, boundaries, breaks, 800, 50) == expected
