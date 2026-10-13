import json

import pytest

import tokens
from ingest import ingest, title_of


def make_snapshot(root, files):
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def test_title_of_skips_frontmatter_bom_and_code():
    text = "\ufeff---\noutline: deep\n---\n\n```sh\n# not a title\n```\n\n# Real Title {#real}\n"
    assert title_of(text) == "Real Title"


def test_title_of_without_h1_raises():
    with pytest.raises(ValueError, match="no H1"):
        title_of("## Only H2 {#x}\n")


def test_ingest_assigns_ids_by_path_and_writes_exact_keys(tmp_path):
    snap = tmp_path / "snap"
    make_snapshot(
        snap,
        {
            "guide/introduction.md": "# Introduction {#introduction}\n",
            "guide/components/props.md": "\ufeff# Props {#props}\n\nText\n",
            "guide/essentials/a.md": "# A {#a}\n",
        },
    )
    out = tmp_path / "processed" / "documents.jsonl"
    assert ingest(snap, out) == 3

    docs = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [(d["doc_id"], d["path"], d["title"]) for d in docs] == [
        ("D001", "guide/components/props.md", "Props"),
        ("D002", "guide/essentials/a.md", "A"),
        ("D003", "guide/introduction.md", "Introduction"),
    ]
    assert list(docs[0]) == ["doc_id", "path", "title", "text", "tokens"]
    assert not docs[0]["text"].startswith("\ufeff")
    assert docs[0]["tokens"] == tokens.count(docs[0]["text"])


def test_ingest_without_snapshot_points_to_snapshot_script(tmp_path):
    with pytest.raises(FileNotFoundError, match="run src/snapshot.py"):
        ingest(tmp_path / "empty", tmp_path / "documents.jsonl")
