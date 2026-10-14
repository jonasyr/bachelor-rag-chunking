import json

import pytest

import tokens
from catalogue import find, load_corpus, section_index, show, write_section_index
from config import (
    AREA_MIN_QUESTIONS,
    QUESTION_CLASSES,
    QUESTION_TYPES,
    VUE_DOCS_AREAS,
)
from preprocess import clean_markdown, section_spans

PAGES = {
    "api/reactivity-core.md": (
        "# Reactivity API: Core {#core}\n\n## ref() {#ref}\n\n"
        "Takes an inner value and returns a reactive ref object.\n\n## computed() {#computed}\n\n"
        "Takes a getter function and returns a readonly ref.\n"
    ),
    "guide/essentials/watchers.md": (
        "# Watchers {#watchers}\n\nWatchers run side effects.\n\n## Deep Watchers {#deep}\n\n"
        "A deep watcher tracks nested props. Use the once option.\n\n### Once Watchers {#once}\n\n"
        "Set once: true to run the callback only one time.\n\n## Side Effect Cleanup {#cleanup}\n\n"
        "Register cleanup with onWatcherCleanup.\n"
    ),
    "style-guide/rules-essential.md": (
        "# Priority A Rules: Essential {#essential}\n\n"
        "## Use multi-word component names {#multi-word}\n\n"
        "User component names should always be multi-word, except for root App components.\n"
    ),
}


def build_corpus(tmp_path, pages):
    docs, sections = [], []
    for number, (path, page) in enumerate(sorted(pages.items()), start=1):
        doc_id = f"D{number:03d}"
        result = clean_markdown(page)
        spans = section_spans(doc_id, result)
        docs.append(
            {
                "doc_id": doc_id,
                "path": path,
                "title": spans[0]["title"],
                "text": result.text,
                "tokens": tokens.count(result.text),
            }
        )
        sections.extend(spans)
    docs_file, sections_file = tmp_path / "documents.jsonl", tmp_path / "sections.jsonl"
    docs_file.write_text("".join(json.dumps(d) + "\n" for d in docs), encoding="utf-8")
    sections_file.write_text("".join(json.dumps(s) + "\n" for s in sections), encoding="utf-8")
    return docs_file, sections_file


@pytest.fixture
def corpus_files(tmp_path):
    return build_corpus(tmp_path, PAGES)


@pytest.fixture
def corpus(corpus_files):
    return load_corpus(*corpus_files)


def test_config_quotas_are_consistent():
    assert sum(QUESTION_TYPES.values()) == sum(QUESTION_CLASSES.values()) == 48
    assert set(AREA_MIN_QUESTIONS) <= set(VUE_DOCS_AREAS)


def test_corpus_text_is_the_exact_token_slice(corpus):
    once = corpus.by_id["D002#once"]
    doc = corpus.docs["D002"]
    starts = tokens.token_starts(doc["text"])
    assert corpus.text(once) == doc["text"][starts[once["start_token"]] : starts[once["end_token"]]]
    assert corpus.text(once).startswith("### Once Watchers")


def test_heading_path_area_and_page_title(corpus):
    once = corpus.by_id["D002#once"]
    assert corpus.heading_path(once) == "Watchers › Deep Watchers › Once Watchers"
    assert corpus.heading_path(corpus.by_id["D001#core"]) == "Reactivity API: Core"
    assert corpus.area(once) == "guide"
    assert corpus.area(corpus.by_id["D003#multi-word"]) == "style-guide"
    assert corpus.page_title(once) == "Watchers"


def test_section_index_has_one_row_per_section_in_order(corpus):
    lines = section_index(corpus).splitlines()
    rows = [line for line in lines if line.startswith("| `")]
    assert [row.split("`")[1] for row in rows] == [s["section_id"] for s in corpus.sections]
    once = corpus.by_id["D002#once"]
    tokens_once = once["end_token"] - once["start_token"]
    assert (
        f"| `D002#once` | guide | guide/essentials/watchers.md | "
        f"Watchers › Deep Watchers › Once Watchers | {tokens_once} |"
    ) in rows


def test_section_index_escapes_pipes_in_titles(tmp_path):
    pages = {"guide/a.md": "# A | B {#a}\n\nText.\n"}
    index = section_index(load_corpus(*build_corpus(tmp_path, pages)))
    assert "| A \\| B |" in index


def test_write_section_index_is_deterministic(corpus, tmp_path):
    out = tmp_path / "index.md"
    assert write_section_index(corpus, out) == len(corpus.sections)
    first = out.read_bytes()
    write_section_index(corpus, out)
    assert out.read_bytes() == first


def test_find_reports_only_the_innermost_section(corpus):
    hits = find(corpus, "callback only")
    assert [s["section_id"] for s, _ in hits] == ["D002#once"]
    assert "callback only one time" in hits[0][1]


def test_find_is_case_insensitive_and_reports_each_owning_section(corpus):
    ids = [s["section_id"] for s, _ in find(corpus, "ONCE")]
    assert ids == ["D002#deep", "D002#once"]  # "Use the once option" is in Deep's own text


def test_find_matches_regex_characters_literally(corpus):
    assert [s["section_id"] for s, _ in find(corpus, "ref()")] == ["D001#ref"]
    assert find(corpus, "r.f") == []


def test_find_rejects_an_empty_term(corpus):
    with pytest.raises(ValueError, match="empty search term"):
        find(corpus, "  ")


def test_show_prints_heading_path_tokens_and_exact_text(corpus):
    once = corpus.by_id["D002#once"]
    out = show(corpus, "D002#once")
    assert out.splitlines()[0] == (
        f"D002#once  Watchers › Deep Watchers › Once Watchers  "
        f"({once['end_token'] - once['start_token']} tokens)"
    )
    assert out.endswith(corpus.text(once))


def test_show_rejects_an_unknown_section(corpus):
    with pytest.raises(ValueError, match="unknown section D009#x"):
        show(corpus, "D009#x")
