import json

import pytest

import tokens
from ingest import ingest

NAV = {
    "navigation": {
        "tabs": [
            {"tab": "Docs", "groups": [{"group": "Start", "pages": ["index", "ci/a"]}]},
            {"tab": "Examples", "pages": ["examples"]},
        ]
    }
}
PAGES = {
    "index.mdx": "---\ntitle: Introduction\ndescription: Hi.\n---\n\nText.\n",
    "ci/a.mdx": '﻿---\ntitle: "GitHub Actions"\n---\n\nRun it.\n',
    "examples.mdx": "---\ntitle: Example projects\n---\n",
}


def make_snapshot(root, pages=PAGES, nav=NAV):
    for rel, text in pages.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (root / "docs.json").write_text(json.dumps(nav), encoding="utf-8")


def run(snap, out, areas=("Start", "Examples")):
    return ingest(snap, out, ".mdx", "docs.json", areas)


def test_ingest_assigns_ids_by_path_with_title_and_area(tmp_path):
    make_snapshot(tmp_path / "snap")
    out = tmp_path / "processed" / "documents.jsonl"
    assert run(tmp_path / "snap", out) == 3

    docs = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [(d["doc_id"], d["path"], d["title"], d["area"]) for d in docs] == [
        ("D001", "ci/a.mdx", "GitHub Actions", "Start"),
        ("D002", "examples.mdx", "Example projects", "Examples"),
        ("D003", "index.mdx", "Introduction", "Start"),
    ]
    assert list(docs[0]) == ["doc_id", "path", "title", "area", "text", "tokens"]
    assert docs[0]["text"].startswith("---\n")  # raw text, BOM removed
    assert docs[0]["tokens"] == tokens.count(docs[0]["text"])


def test_ingest_without_snapshot_points_to_snapshot_script(tmp_path):
    with pytest.raises(FileNotFoundError, match="run src/snapshot.py"):
        run(tmp_path / "empty", tmp_path / "documents.jsonl")


def test_ingest_rejects_areas_that_differ_from_the_config(tmp_path):
    make_snapshot(tmp_path / "snap")
    with pytest.raises(ValueError, match="CORPUS_AREAS"):
        run(tmp_path / "snap", tmp_path / "d.jsonl", areas=("Start",))


def test_ingest_rejects_a_page_outside_the_navigation(tmp_path):
    make_snapshot(tmp_path / "snap", {**PAGES, "draft.mdx": "---\ntitle: D\n---\n"})
    with pytest.raises(ValueError, match="draft.mdx: not in the navigation"):
        run(tmp_path / "snap", tmp_path / "d.jsonl")


def test_ingest_rejects_a_navigation_page_without_file(tmp_path):
    pages = {k: v for k, v in PAGES.items() if k != "examples.mdx"}
    make_snapshot(tmp_path / "snap", pages)
    with pytest.raises(ValueError, match="examples"):
        run(tmp_path / "snap", tmp_path / "d.jsonl")


def test_ingest_requires_a_title(tmp_path):
    make_snapshot(tmp_path / "snap", {**PAGES, "index.mdx": "---\ndescription: x\n---\n"})
    with pytest.raises(ValueError, match="index.mdx: no title"):
        run(tmp_path / "snap", tmp_path / "d.jsonl")
