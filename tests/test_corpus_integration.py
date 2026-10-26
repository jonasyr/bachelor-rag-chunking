"""Checks on the real corpus; skipped until the snapshot and processed files exist."""

import collections
import hashlib
import json
import re

import numpy as np
import pytest

from catalogue import find, load_corpus, section_index
from catalogue_plan import candidates, draw_plan, plan_integrity, read_plan
from chunking import chunk
from config import (
    C3_MAX_TOKENS,
    C3_MIN_TOKENS,
    CATALOGUE_AREA_SLOTS,
    CATALOGUE_PLAN_FILE,
    CATALOGUE_RESERVE,
    CHUNK_FILES,
    CONTROL_STRATEGIES,
    CORPUS_AREAS,
    CORPUS_NAV_FILE,
    CORPUS_PAGE_SUFFIX,
    CORPUS_PROVIDER_SNIPPET,
    CORPUS_SUPPORT_FILES,
    DATA_RAW,
    DOCUMENTS_FILE,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_FILES,
    SECTIONS_FILE,
    SNAPSHOT_INFO_FILE,
    STRATEGY_IDS,
)
from mdx import parse_provider_snippet, to_markdown
from preprocess import ESCAPED_LT_RE, clean_markdown

HAS_SNAPSHOT = (DATA_RAW / CORPUS_NAV_FILE).is_file()
EXPECTED_FILES = 60  # ADR 0038: every page of the navigation at ef977f4
EXPECTED_SECTIONS = 571  # H1-H3 sections, measured 18.10.2026
AREA_PAGES = {
    "Get started": 5, "Platforms": 3, "Features": 6, "Models and agents": 3, "Run in CI": 6,
    "Hosted browsers and devices": 7, "Extend": 3, "Deep dive": 5, "Migrate": 5, "Test API": 5,
    "Project": 8, "Web": 1, "Mobile": 1, "Engine contract": 1, "Examples": 1,
}  # fmt: skip


def snapshot_files():
    return sorted(DATA_RAW.rglob(f"*{CORPUS_PAGE_SUFFIX}"))


@pytest.mark.skipif(not HAS_SNAPSHOT, reason="no snapshot; run src/snapshot.py")
def test_every_snapshot_file_cleans():
    files = snapshot_files()
    assert len(files) == EXPECTED_FILES
    snippet = parse_provider_snippet(
        (DATA_RAW / CORPUS_PROVIDER_SNIPPET).read_text(encoding="utf-8")
    )
    for path in files:
        page = path.relative_to(DATA_RAW).as_posix().removesuffix(CORPUS_PAGE_SUFFIX)
        markdown = to_markdown(path.read_text(encoding="utf-8"), page, snippet)
        assert clean_markdown(markdown).headings[0].level == 1, path


@pytest.mark.skipif(not SECTIONS_FILE.exists(), reason="not preprocessed; run src/preprocess.py")
def test_processed_artifacts_are_consistent():
    docs = [json.loads(line) for line in DOCUMENTS_FILE.read_text(encoding="utf-8").splitlines()]
    sections = [json.loads(line) for line in SECTIONS_FILE.read_text(encoding="utf-8").splitlines()]
    assert len(docs) == EXPECTED_FILES
    assert [d["doc_id"] for d in docs] == [f"D{i:03d}" for i in range(1, EXPECTED_FILES + 1)]
    ids = [s["section_id"] for s in sections]
    assert len(ids) == len(set(ids))
    for d in docs:
        prose = re.sub(r"^\s*(`{3,}|~{3,}).*?^\s*\1\s*$", "", d["text"], flags=re.S | re.M)
        prose = re.sub(r"`[^`\n]*`", "", prose)
        prose = ESCAPED_LT_RE.sub(r"\1", prose)  # an escaped `\<` is text, not a tag
        leftover = re.search(
            r"</?[A-Za-z][\w-]*(?:\s[^>]*)?/?>|\{#|^\s*(?:import|export) ", prose, re.M
        )
        assert leftover is None, f"{d['path']}: markup left in prose: {leftover.group(0)!r}"
    tokens_by_doc = {d["doc_id"]: d["tokens"] for d in docs}
    for s in sections:
        assert 0 <= s["start_token"] < s["end_token"] <= tokens_by_doc[s["doc_id"]], s["section_id"]


@pytest.mark.skipif(not SECTIONS_FILE.exists(), reason="not preprocessed; run src/preprocess.py")
@pytest.mark.parametrize("key", [*STRATEGY_IDS, *CONTROL_STRATEGIES])
def test_real_corpus_chunks(key, tmp_path):
    out = tmp_path / f"chunks_{key}.jsonl"
    count = chunk(key, out_file=out)  # chunk() checks every invariant per document
    lengths = [
        c["end_token"] - c["start_token"]
        for c in map(json.loads, out.read_text(encoding="utf-8").splitlines())
    ]
    assert count == len(lengths)
    if key == "C3":
        assert all(C3_MIN_TOKENS <= n <= C3_MAX_TOKENS for n in lengths)


@pytest.mark.skipif(not HAS_SNAPSHOT, reason="no snapshot; run src/snapshot.py")
def test_snapshot_matches_the_versioned_checksums():
    lines = SNAPSHOT_INFO_FILE.read_text(encoding="utf-8").splitlines()
    recorded: dict[str, str] = {}
    for line in lines:
        if re.match(r"^[0-9a-f]{64}  ", line):
            digest, rel = line.split("  ", 1)
            recorded[rel] = digest
    files = {p.relative_to(DATA_RAW).as_posix(): p for p in snapshot_files()}
    files |= {rel: DATA_RAW / rel for rel in CORPUS_SUPPORT_FILES}
    assert set(recorded) == set(files)
    for rel, path in files.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == recorded[rel], rel


@pytest.mark.skipif(not SECTIONS_FILE.exists(), reason="not preprocessed; run src/preprocess.py")
def test_corpus_areas():
    docs = [json.loads(line) for line in DOCUMENTS_FILE.read_text(encoding="utf-8").splitlines()]
    assert collections.Counter(d["area"] for d in docs) == AREA_PAGES
    assert list(AREA_PAGES) == list(CORPUS_AREAS)


@pytest.mark.skipif(not SECTIONS_FILE.exists(), reason="not preprocessed; run src/preprocess.py")
def test_c2_has_more_chunks_than_c1(tmp_path):
    assert chunk("C2", out_file=tmp_path / "c2.jsonl") > chunk("C1", out_file=tmp_path / "c1.jsonl")


@pytest.mark.parametrize("key", list(STRATEGY_IDS))
def test_reference_vectors_match_their_chunks(key):
    if not EMBEDDING_FILES[key].exists():
        pytest.skip("not embedded; run src/embed.py")
    if not CHUNK_FILES[key].exists():  # vectors are versioned, chunks are rebuilt (ADR 0048)
        pytest.skip("not chunked; run src/chunking.py")
    chunks = [
        json.loads(line) for line in CHUNK_FILES[key].read_text(encoding="utf-8").splitlines()
    ]
    with np.load(EMBEDDING_FILES[key], allow_pickle=False) as data:
        assert data["ids"].tolist() == [c["chunk_id"] for c in chunks]
        assert data["texts"].tolist() == [c["text"] for c in chunks]
        vectors = data["vectors"]
    assert vectors.shape == (len(chunks), EMBEDDING_DIMENSIONS)
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-3)  # OpenAI: unit length


@pytest.mark.skipif(not SECTIONS_FILE.exists(), reason="not preprocessed; run src/preprocess.py")
def test_section_index_covers_the_real_corpus():
    corpus = load_corpus()
    rows = [line for line in section_index(corpus).splitlines() if line.startswith("| `")]
    ids = [row.split("`")[1] for row in rows]
    assert len(rows) == len(corpus.sections) == EXPECTED_SECTIONS
    assert all(sid in corpus.by_id for sid in ids)
    assert {row.split(" | ")[1] for row in rows} == set(CORPUS_AREAS)
    assert any(s["section_id"].startswith("D") for s, _ in find(corpus, "toHaveScreenshot"))


@pytest.mark.skipif(not SECTIONS_FILE.exists(), reason="not preprocessed; run src/preprocess.py")
def test_every_area_has_enough_candidates():
    pools = candidates(load_corpus())
    for area in CORPUS_AREAS:
        assert len(pools[area]) >= CATALOGUE_AREA_SLOTS[area] + CATALOGUE_RESERVE[area], area


@pytest.mark.skipif(not SECTIONS_FILE.exists(), reason="not preprocessed; run src/preprocess.py")
def test_committed_plan_matches_a_fresh_draw():
    corpus = load_corpus()
    fresh = draw_plan(corpus)
    assert draw_plan(corpus) == fresh  # deterministic
    rows = read_plan(CATALOGUE_PLAN_FILE)
    assert [r["area"] for r in rows if r["slot_id"]] == [
        a for a in CORPUS_AREAS for _ in range(CATALOGUE_AREA_SLOTS[a])
    ]
    assert plan_integrity(rows, fresh) == []
