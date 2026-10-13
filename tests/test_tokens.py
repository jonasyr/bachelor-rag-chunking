import tokens


def test_count_matches_encode():
    assert tokens.count("Hello world") == len(tokens.encode("Hello world")) == 2


def test_special_token_text_is_plain_text():
    assert tokens.count("<|endoftext|>") > 1


def test_token_starts_are_sorted_and_one_per_token():
    text = "ref() and reactive()\n\n## Heading\n"
    starts = tokens.token_starts(text)
    assert starts[0] == 0
    assert starts == sorted(starts)
    assert len(starts) == tokens.count(text)


def test_char_to_token_bounds_and_heading_alignment():
    text = "# Title\n\nIntro.\n\n## A\n\ntext\n"
    starts = tokens.token_starts(text)
    assert tokens.char_to_token(starts, 0) == 0
    assert tokens.char_to_token(starts, len(text)) == len(starts)
    i = tokens.char_to_token(starts, text.index("## A"))
    assert tokens.decode(tokens.encode(text)[i:]).startswith("## A")


def test_decode_round_trip():
    text = "const count = ref(0)\n"
    assert tokens.decode(tokens.encode(text)) == text
