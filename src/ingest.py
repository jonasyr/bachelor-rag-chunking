"""Ingest Vue.js snapshot.

Reads guide/**/*.md from data/raw/vue_docs_snapshot/ sorted by path, assigns D001, D002, ...
in that order and writes data/processed/documents.jsonl with the raw text.

Output schema: {"doc_id", "path", "title", "text", "tokens"}
"""

import json
import re
from pathlib import Path

import tokens
from config import DATA_RAW, DOCUMENTS_FILE, SNAPSHOT_SUBDIR
from preprocess import closes_fence, fence_marker

H1_RE = re.compile(r"^#\s+(.*?)(?:\s*\{#[^}]+\})?\s*$")


def title_of(text: str) -> str:
    """Text of the first H1 outside code fences, without its anchor."""
    fence: str | None = None
    for line in text.lstrip("\ufeff").split("\n"):
        if fence is not None:
            if closes_fence(line, fence):
                fence = None
        elif (marker := fence_marker(line)) is not None:
            fence = marker
        elif m := H1_RE.match(line):
            return m.group(1)
    raise ValueError("no H1 found")


def ingest(snapshot_dir: Path = DATA_RAW, out_file: Path = DOCUMENTS_FILE) -> int:
    """Load all guide Markdown files, count tokens, write documents.jsonl; return the count."""
    files = sorted(
        snapshot_dir.glob(f"{SNAPSHOT_SUBDIR}/**/*.md"),
        key=lambda p: p.relative_to(snapshot_dir).as_posix(),
    )
    if not files:
        raise FileNotFoundError(
            f"no Markdown files under {snapshot_dir / SNAPSHOT_SUBDIR}; run src/snapshot.py first"
        )
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        for i, path in enumerate(files, start=1):
            rel = path.relative_to(snapshot_dir).as_posix()
            text = path.read_text(encoding="utf-8-sig")
            try:
                title = title_of(text)
            except ValueError as e:
                raise ValueError(f"{rel}: {e}") from e
            record = {
                "doc_id": f"D{i:03d}",
                "path": rel,
                "title": title,
                "text": text,
                "tokens": tokens.count(text),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return len(files)


if __name__ == "__main__":
    print(f"{ingest()} documents -> {DOCUMENTS_FILE}")
