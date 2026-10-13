import json

import pytest

import tokens
from chunking import check_chunks, chunk, fixed_size_spans, make_chunks, summary
from preprocess import clean_markdown, section_spans


def doc_from_markdown(doc_id, markdown):
    result = clean_markdown(markdown)
    doc = {
        "doc_id": doc_id,
        "path": f"guide/{doc_id}.md",
        "title": "T",
        "text": result.text,
        "tokens": tokens.count(result.text),
    }
    return doc, section_spans(doc_id, result)


def test_make_chunks_slices_text_exactly():
    doc, _ = doc_from_markdown("D001", "# T {#t}\n\nHello ✔ world, `ref()` and more words here.\n")
    chunks = make_chunks(doc, fixed_size_spans(doc["tokens"], 4, 0), "C1")
    assert [c["chunk_id"] for c in chunks[:2]] == ["C1_D001_0001", "C1_D001_0002"]
    assert list(chunks[0]) == ["chunk_id", "doc_id", "strategy", "text", "start_token", "end_token"]
    assert {c["strategy"] for c in chunks} == {"fixed_500_no_overlap"}
    assert "".join(c["text"] for c in chunks) == doc["text"]


def test_check_chunks_rejects_a_gap():
    doc, _ = doc_from_markdown("D001", "# T {#t}\n\n" + "word " * 60 + "\n")
    chunks = make_chunks(doc, [(0, 10), (11, doc["tokens"])], "C3")
    with pytest.raises(ValueError, match="gap or overlap"):
        check_chunks(doc, chunks, "C3")


def test_check_chunks_rejects_a_stale_token_count():
    doc, _ = doc_from_markdown("D001", "# T {#t}\n\nText.\n")
    doc["tokens"] += 1
    with pytest.raises(ValueError, match="re-run src/preprocess.py"):
        check_chunks(doc, make_chunks(doc, [(0, doc["tokens"])], "C3"), "C3")


def test_check_chunks_enforces_the_c3_floor():
    doc, _ = doc_from_markdown("D001", "# T {#t}\n\n" + "word " * 60 + "\n")
    chunks = make_chunks(doc, [(0, 10), (10, doc["tokens"])], "C3")
    with pytest.raises(ValueError, match="shorter than 50"):
        check_chunks(doc, chunks, "C3")


@pytest.fixture
def inputs(tmp_path):
    docs, sections = [], []
    long_section = "\n\n".join(f"Paragraph {i}. " + "Reactive state " * 40 for i in range(8))
    for doc_id, markdown in [
        ("D001", "# Props {#props}\n\n## Declaration {#decl}\n\n" + long_section + "\n"),
        ("D002", "# Intro {#intro}\n\nShort page.\n"),
    ]:
        doc, secs = doc_from_markdown(doc_id, markdown)
        docs.append(doc)
        sections.extend(secs)
    docs_file, sections_file = tmp_path / "documents.jsonl", tmp_path / "sections.jsonl"
    docs_file.write_text("".join(json.dumps(d) + "\n" for d in docs), encoding="utf-8")
    sections_file.write_text("".join(json.dumps(s) + "\n" for s in sections), encoding="utf-8")
    return docs, docs_file, sections_file


@pytest.mark.parametrize("key", ["C1", "C2", "C3"])
def test_chunk_writes_checked_chunks(inputs, tmp_path, key):
    docs, docs_file, sections_file = inputs
    out = tmp_path / f"chunks_{key}.jsonl"
    count = chunk(key, docs_file, sections_file, out)
    chunks = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert count == len(chunks) > 0
    assert len({c["chunk_id"] for c in chunks}) == count
    for doc in docs:
        own = [c for c in chunks if c["doc_id"] == doc["doc_id"]]
        check_chunks(doc, own, key)


def test_c3_keeps_heading_with_its_section(inputs, tmp_path):
    _, docs_file, sections_file = inputs
    out = tmp_path / "chunks_c3.jsonl"
    chunk("C3", docs_file, sections_file, out)
    first = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    assert first["text"].startswith("# Props\n\n## Declaration\n\nParagraph 0.")
    assert 50 <= first["end_token"] - first["start_token"] <= 800


def test_chunk_without_documents_points_to_preprocess(tmp_path):
    with pytest.raises(FileNotFoundError, match="run src/preprocess.py"):
        chunk("C1", tmp_path / "missing.jsonl", tmp_path / "s.jsonl", tmp_path / "out.jsonl")


def test_c3_without_sections_for_a_document(inputs, tmp_path):
    _, docs_file, sections_file = inputs
    kept = [s for s in sections_file.read_text(encoding="utf-8").splitlines() if '"D002' not in s]
    sections_file.write_text("\n".join(kept) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="D002: no sections"):
        chunk("C3", docs_file, sections_file, tmp_path / "out.jsonl")


def test_c3_rejects_sections_of_unknown_documents(inputs, tmp_path):
    _, docs_file, sections_file = inputs
    extra = {"section_id": "D999#x", "doc_id": "D999", "start_token": 0}
    with sections_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(extra) + "\n")
    with pytest.raises(ValueError, match="unknown document"):
        chunk("C3", docs_file, sections_file, tmp_path / "out.jsonl")


def test_unknown_strategy(tmp_path):
    with pytest.raises(ValueError, match="unknown strategy"):
        chunk("C4", tmp_path / "d.jsonl", tmp_path / "s.jsonl", tmp_path / "o.jsonl")


@pytest.mark.parametrize("key", ["C1", "C2", "C3"])
def test_raw_reingested_documents_are_rejected(inputs, tmp_path, key):
    docs, docs_file, sections_file = inputs
    raw = '# Intro {#intro}\n\n<div class="options-api">\n\nOld API.\n\n</div>\n\nShort page.\n'
    stale = [docs[0], {**docs[1], "text": raw, "tokens": tokens.count(raw)}]
    docs_file.write_text("".join(json.dumps(d) + "\n" for d in stale), encoding="utf-8")
    with pytest.raises(ValueError, match="D002: sections.jsonl does not match"):
        chunk(key, docs_file, sections_file, tmp_path / "out.jsonl")


def test_window_edges_inside_multi_token_characters():
    doc, _ = doc_from_markdown("D001", "# T {#t}\n\n" + "x 𓀀 " * 40 + "\n")
    for key, (size, overlap) in {"C1": (4, 0), "C2": (5, 2)}.items():
        chunks = make_chunks(doc, fixed_size_spans(doc["tokens"], size, overlap), key)
        assert all("�" not in c["text"] for c in chunks)
    c1 = make_chunks(doc, fixed_size_spans(doc["tokens"], 4, 0), "C1")
    assert "".join(c["text"] for c in c1) == doc["text"]


def test_check_chunks_verifies_every_text_slice():
    doc, _ = doc_from_markdown("D001", "# T {#t}\n\n" + "word " * 60 + "\n")
    chunks = make_chunks(doc, fixed_size_spans(doc["tokens"], 500, 100), "C2")
    chunks[0]["text"] = chunks[0]["text"].upper()
    with pytest.raises(ValueError, match="not the document slice"):
        check_chunks(doc, chunks, "C2")


def test_summary_of_an_empty_chunk_file(tmp_path):
    out = tmp_path / "chunks_c1.jsonl"
    out.write_text("", encoding="utf-8")
    assert summary("C1", out).startswith("C1: 0 chunks")
