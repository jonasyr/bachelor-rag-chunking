import csv
import json

import pytest

import tokens
from preprocess import clean_markdown, manifest_section, preprocess, section_spans

RAW_A = (
    '# A Page {#a-page}\n\n<div class="options-api">\n\nOld\n\n</div>\n\n## Part {#part}\n\nText.\n'
)
RAW_B = "# Intro {#intro}\n\nHello.\n"


def write_docs(path, docs):
    path.write_text("".join(json.dumps(d) + "\n" for d in docs), encoding="utf-8")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


@pytest.fixture
def files(tmp_path):
    docs = tmp_path / "documents.jsonl"
    write_docs(
        docs,
        [
            {
                "doc_id": "D001",
                "path": "guide/essentials/a.md",
                "title": "A Page",
                "text": RAW_A,
                "tokens": 0,
            },
            {
                "doc_id": "D002",
                "path": "guide/introduction.md",
                "title": "Intro",
                "text": RAW_B,
                "tokens": 0,
            },
        ],
    )
    return docs, tmp_path / "sections.jsonl", tmp_path / "corpus_manifest.csv"


def test_section_spans_nest_and_cover_document():
    result = clean_markdown(
        "# T {#t}\n\nIntro.\n\n## A {#a}\n\ntext\n\n### B {#b}\n\nmore\n\n## C {#c}\n\nend\n"
    )
    spans = section_spans("D007", result)
    n = tokens.count(result.text)
    by_id = {s["section_id"]: s for s in spans}
    assert list(by_id) == ["D007#t", "D007#a", "D007#b", "D007#c"]
    assert (by_id["D007#t"]["start_token"], by_id["D007#t"]["end_token"]) == (0, n)
    assert by_id["D007#a"]["end_token"] == by_id["D007#c"]["start_token"]
    assert by_id["D007#b"]["end_token"] == by_id["D007#c"]["start_token"]
    assert by_id["D007#a"]["start_token"] < by_id["D007#b"]["start_token"]
    assert by_id["D007#c"]["end_token"] == n
    assert list(spans[0]) == [
        "section_id",
        "doc_id",
        "anchor",
        "title",
        "level",
        "start_token",
        "end_token",
    ]


@pytest.mark.parametrize(
    ("path", "section"),
    [
        ("guide/essentials/a.md", "Essentials"),
        ("guide/best-practices/performance.md", "Best Practices"),
        ("guide/typescript/overview.md", "TypeScript"),
        ("guide/introduction.md", "Guide"),
        ("api/reactivity-core.md", "API Reference"),
        ("style-guide/rules-essential.md", "Style Guide"),
    ],
)
def test_manifest_section(path, section):
    assert manifest_section(path) == section


def test_manifest_section_unknown_folder_raises():
    with pytest.raises(ValueError, match="no manifest section"):
        manifest_section("guide/new-folder/page.md")


def test_manifest_section_unknown_area_raises():
    with pytest.raises(ValueError, match="no manifest section"):
        manifest_section("tutorial/step-1.md")


def test_preprocess_writes_documents_sections_and_manifest(files):
    docs, sections, manifest = files
    assert preprocess(docs, sections, manifest) == (2, 3)

    out = read_jsonl(docs)
    assert [list(d) for d in out] == [["doc_id", "path", "title", "text", "tokens"]] * 2
    assert out[0]["text"] == "# A Page\n\n## Part\n\nText.\n"
    assert out[0]["tokens"] == tokens.count(out[0]["text"])

    assert [s["section_id"] for s in read_jsonl(sections)] == [
        "D001#a-page",
        "D001#part",
        "D002#intro",
    ]

    with manifest.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["file_id", "path", "title", "section", "tokens", "included"]
    assert rows[1] == [
        "D001",
        "guide/essentials/a.md",
        "A Page",
        "Essentials",
        str(out[0]["tokens"]),
        "yes",
    ]
    assert rows[2][3] == "Guide"


def test_rerun_on_cleaned_documents_asks_for_ingest(files):
    docs, sections, manifest = files
    preprocess(docs, sections, manifest)
    with pytest.raises(RuntimeError, match="run src/ingest.py"):
        preprocess(docs, sections, manifest)


def test_anomaly_reports_document_path(files):
    docs, sections, manifest = files
    write_docs(
        docs,
        [
            {
                "doc_id": "D001",
                "path": "guide/x.md",
                "title": "X",
                "text": "# X {#x}\n\n## Y\n",
                "tokens": 0,
            }
        ],
    )
    with pytest.raises(ValueError, match="guide/x.md: heading without anchor"):
        preprocess(docs, sections, manifest)


def test_missing_documents_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="run src/ingest.py"):
        preprocess(tmp_path / "missing.jsonl", tmp_path / "s.jsonl", tmp_path / "m.csv")


def test_rerun_detected_even_with_anchor_text_inside_code(files):
    docs, sections, manifest = files
    cleaned = {
        "doc_id": "D001",
        "path": "guide/x.md",
        "title": "X",
        "text": "# X\n\n```md\n## Y {#y}\n```\n",
        "tokens": 0,
    }
    write_docs(docs, [cleaned])
    with pytest.raises(RuntimeError, match="already preprocessed"):
        preprocess(docs, sections, manifest)
