import pytest

from chunking import fixed_size_spans


@pytest.mark.parametrize(
    ("n", "size", "overlap", "expected"),
    [
        (0, 500, 0, []),
        (300, 500, 0, [(0, 300)]),
        (500, 500, 0, [(0, 500)]),
        (1000, 500, 0, [(0, 500), (500, 1000)]),
        (1001, 500, 0, [(0, 500), (500, 1000), (1000, 1001)]),
        (900, 500, 100, [(0, 500), (400, 900)]),
        (950, 500, 100, [(0, 500), (400, 900), (800, 950)]),
    ],
)
def test_fixed_size_spans(n, size, overlap, expected):
    assert fixed_size_spans(n, size, overlap) == expected


@pytest.mark.parametrize(("size", "overlap"), [(500, 500), (500, -1), (0, 0)])
def test_fixed_size_spans_rejects_invalid_windows(size, overlap):
    with pytest.raises(ValueError, match="invalid window"):
        fixed_size_spans(100, size, overlap)
