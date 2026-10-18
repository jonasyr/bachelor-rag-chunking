import csv
import json

import pytest
from test_mdx import SNIPPET

import tokens
from preprocess import clean_markdown, preprocess, section_spans

RAW_A = (
    "---\ntitle: A Page\ndescription: About A.\n---\n\n"
    "import { X } from './snippets/x.jsx';\n\n## Part\n\n<Note>\nText.\n</Note>\n"
)
RAW_B = "---\ntitle: Intro\n---\n\nHello.\n"


def write_docs(path, docs):
    path.write_text("".join(json.dumps(d) + "\n" for d in docs), encoding="utf-8")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def doc(doc_id, path, title, area, text):
    return {"doc_id": doc_id, "path": path, "title": title, "area": area, "text": text, "tokens": 0}


@pytest.fixture
def files(tmp_path):
    docs = tmp_path / "documents.jsonl"
    write_docs(
        docs,
        [
            doc("D001", "features/a.mdx", "A Page", "Features", RAW_A),
            doc("D002", "index.mdx", "Intro", "Get started", RAW_B),
        ],
    )
    snippet = tmp_path / "model-provider.jsx"
    snippet.write_text(SNIPPET, encoding="utf-8")
    return docs, tmp_path / "sections.jsonl", tmp_path / "corpus_manifest.csv", snippet


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
    assert by_id["D007#c"]["end_token"] == n
    assert list(spans[0]) == [
        "section_id", "doc_id", "anchor", "title", "level", "start_token", "end_token",
    ]  # fmt: skip


def test_preprocess_writes_documents_sections_and_manifest(files):
    assert preprocess(*files) == (2, 3)
    docs, sections, manifest, _ = files

    out = read_jsonl(docs)
    assert [list(d) for d in out] == [["doc_id", "path", "title", "area", "text", "tokens"]] * 2
    assert out[0]["text"] == "# A Page\n\nAbout A.\n\n## Part\n\n**Note**\nText.\n"
    assert out[0]["tokens"] == tokens.count(out[0]["text"])
    assert [s["section_id"] for s in read_jsonl(sections)] == [
        "D001#features-a",
        "D001#part",
        "D002#index",
    ]
    with manifest.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["file_id", "path", "title", "section", "tokens", "included"]
    assert rows[1] == ["D001", "features/a.mdx", "A Page", "Features", str(out[0]["tokens"]), "yes"]
    assert rows[2][3] == "Get started"


def test_rerun_on_cleaned_documents_asks_for_ingest(files):
    preprocess(*files)
    with pytest.raises(RuntimeError, match="run src/ingest.py"):
        preprocess(*files)


def test_anomaly_reports_document_path(files):
    docs = files[0]
    write_docs(docs, [doc("D001", "x.mdx", "X", "Features", "---\ntitle: X\n---\n\n<Frame>\n")])
    with pytest.raises(ValueError, match="x.mdx: line 2: unknown component <Frame>"):
        preprocess(*files)


def test_missing_documents_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="run src/ingest.py"):
        missing = [tmp_path / name for name in ("m.jsonl", "s.jsonl", "m.csv", "p.jsx")]
        preprocess(*missing)


def test_missing_snippet_points_to_snapshot(files, tmp_path):
    docs, sections, manifest, _ = files
    with pytest.raises(FileNotFoundError, match="run src/snapshot.py"):
        preprocess(docs, sections, manifest, tmp_path / "missing.jsx")
