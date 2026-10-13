"""Checks on the real corpus; skipped until the snapshot and processed files exist."""

import json
import re

import pytest

from config import DATA_RAW, DOCUMENTS_FILE, SECTIONS_FILE
from preprocess import clean_markdown

GUIDE = DATA_RAW / "guide"
EXPECTED_FILES = 52  # ADR 0019


@pytest.mark.skipif(not GUIDE.is_dir(), reason="no snapshot; run src/snapshot.py")
def test_every_snapshot_file_cleans():
    files = sorted(GUIDE.rglob("*.md"))
    assert len(files) == EXPECTED_FILES
    for path in files:
        result = clean_markdown(path.read_text(encoding="utf-8"))
        assert result.headings[0].level == 1, path


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
        leftover = re.search(
            r'</?[A-Za-z][\w-]*(?:\s[^>]*)?/?>|class="options-api"|\{#|vuejs\.org/#', prose
        )
        assert leftover is None, f"{d['path']}: markup left in prose: {leftover.group(0)!r}"
    tokens_by_doc = {d["doc_id"]: d["tokens"] for d in docs}
    for s in sections:
        assert 0 <= s["start_token"] < s["end_token"] <= tokens_by_doc[s["doc_id"]], s["section_id"]
