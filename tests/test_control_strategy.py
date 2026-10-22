import ast
import json
from pathlib import Path

import pytest

import chunking
import tokens
from chunking import check_chunks, chunk, control_size, rounded_mean
from config import CONTROL_ANSWER_STRATEGIES, CONTROL_STRATEGIES, K1_CHUNK_SIZE, STRATEGY_IDS
from preprocess import clean_markdown, section_spans


@pytest.fixture
def inputs(tmp_path):
    docs, sections = [], []
    for i, n in enumerate((3, 9), start=1):
        body = "\n\n".join(f"Paragraph {j}. " + "Reactive state " * 30 for j in range(n))
        markdown = f"# Page {i} {{#p{i}}}\n\n## Part {{#part}}\n\n{body}\n"
        result = clean_markdown(markdown)
        doc_id = f"D{i:03d}"
        docs.append(
            {
                "doc_id": doc_id,
                "path": f"guide/p{i}.md",
                "title": f"Page {i}",
                "text": result.text,
                "tokens": tokens.count(result.text),
            }
        )
        sections.extend(section_spans(doc_id, result))
    docs_file, sections_file = tmp_path / "documents.jsonl", tmp_path / "sections.jsonl"
    docs_file.write_text("".join(json.dumps(d) + "\n" for d in docs), encoding="utf-8")
    sections_file.write_text("".join(json.dumps(s) + "\n" for s in sections), encoding="utf-8")
    by_doc = {d["doc_id"]: [s for s in sections if s["doc_id"] == d["doc_id"]] for d in docs}
    return docs, by_doc, docs_file, sections_file


def test_control_is_kept_apart_from_the_experiment():
    assert list(CONTROL_STRATEGIES) == ["K1"]
    assert set(CONTROL_STRATEGIES).isdisjoint(STRATEGY_IDS)
    assert CONTROL_STRATEGIES["K1"] == f"fixed_{K1_CHUNK_SIZE}_no_overlap"


@pytest.mark.parametrize(("values", "expected"), [([238, 239], 239), ([1, 2, 2], 2), ([5], 5)])
def test_rounded_mean_rounds_half_up(values, expected):
    assert rounded_mean(values) == expected


def test_k1_uses_the_c3_mean_as_window(inputs, tmp_path, monkeypatch):
    docs, by_doc, docs_file, sections_file = inputs
    size = control_size(docs, by_doc)
    monkeypatch.setattr(chunking, "K1_CHUNK_SIZE", size)
    monkeypatch.setitem(chunking.FIXED_WINDOWS, "K1", (size, 0))
    monkeypatch.setitem(chunking.MAX_LENGTH, "K1", size)
    out = tmp_path / "chunks_k1.jsonl"
    assert chunk("K1", docs_file, sections_file, out) > 0
    chunks = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert {c["strategy"] for c in chunks} == {CONTROL_STRATEGIES["K1"]}
    assert all(c["chunk_id"].startswith("K1_") for c in chunks)
    for doc in docs:
        own = [c for c in chunks if c["doc_id"] == doc["doc_id"]]
        check_chunks(doc, own, "K1")
        assert all(c["end_token"] - c["start_token"] == size for c in own[:-1])


def test_k1_refuses_a_size_that_is_not_the_c3_mean(inputs, tmp_path, monkeypatch):
    docs, by_doc, docs_file, sections_file = inputs
    monkeypatch.setattr(chunking, "K1_CHUNK_SIZE", control_size(docs, by_doc) + 1)
    with pytest.raises(ValueError, match="set config.K1_CHUNK_SIZE"):
        chunk("K1", docs_file, sections_file, tmp_path / "k1.jsonl")


def test_control_keys_come_from_config_only():
    """Strategy keys of the controls are read from config, never spelled out (AGENTS.md)."""
    keys = {*CONTROL_STRATEGIES, *CONTROL_ANSWER_STRATEGIES}
    found = []
    files = [*Path("src").glob("*.py"), *Path("app").glob("*.py"), *Path("scripts").glob("*.py")]
    for path in sorted(files):
        if path.name == "config.py":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and node.value in keys:
                found.append(f"{path}:{node.lineno}")
    assert found == []
