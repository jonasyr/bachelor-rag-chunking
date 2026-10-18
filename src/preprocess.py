"""Preprocess the e2e pages (ADR 0019, ADR 0038).

Reads documents.jsonl (raw MDX from ingest.py), converts every page with mdx.to_markdown (content-
preserving; anchors = the site's slugs) and records the anchored H1-H3 sections with clean_markdown.
Rewrites documents.jsonl in place, writes sections.jsonl and the corpus manifest (section = area).
"""

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

import tokens
from config import (
    CORPUS_MANIFEST_FILE,
    CORPUS_PAGE_SUFFIX,
    CORPUS_PROVIDER_SNIPPET,
    DATA_RAW,
    DOCUMENTS_FILE,
    SECTION_MAX_LEVEL,
    SECTIONS_FILE,
)
from mdx import parse_provider_snippet, to_markdown

FENCE_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")  # CommonMark: at most 3 spaces of indent
FENCE_LANG_RE = re.compile(r"\s*([\w+-]*)")
# CommonMark ATX heading: up to 3 spaces of indent (API pages indent headings inside list items)
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)\s*$")
ANCHOR_RE = re.compile(r"\s*\{#([^}]+)\}\s*$")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
# CommonMark escape `\<`: a literal "<", never a tag. Only an odd run of backslashes escapes it
# (`\\<b>` is a literal backslash and a real tag); group 1 keeps the escaped backslash pairs.
ESCAPED_LT_RE = re.compile(r"(?<!\\)((?:\\\\)*)\\<")
INLINE_TAG_RE = re.compile(r"</?[A-Za-z][\w-]*(?:\s[^>]*)?/?>")
HTML_LINE_RE = re.compile(r"^\s*</?[A-Za-z][\w-]*(?=[\s/>]|$)")  # not autolinks
MANIFEST_HEADER = ["file_id", "path", "title", "section", "tokens", "included"]


@dataclass(frozen=True)
class Heading:
    level: int
    title: str
    anchor: str
    offset: int  # character offset of the heading line in the cleaned text


@dataclass(frozen=True)
class CleanResult:
    text: str
    headings: list[Heading]


def fence_marker(line: str) -> str | None:
    """The marker (``` or ~~~, length >= 3) if line opens a code fence, else None (CommonMark)."""
    m = FENCE_RE.match(line)
    if m is None or (m.group(2)[0] == "`" and "`" in m.group(3)):
        return None
    return m.group(2)


def closes_fence(line: str, marker: str) -> bool:
    """True if line closes a fence opened with marker: same character, at least as long, no info."""
    m = FENCE_RE.match(line)
    return (
        m is not None
        and m.group(2)[0] == marker[0]
        and len(m.group(2)) >= len(marker)
        and not m.group(3).strip()
    )


def clean_markdown(text: str) -> CleanResult:
    """Anchored Markdown (from mdx.to_markdown) -> text without anchors and its H1-H3 headings.

    Fences are tracked and their info string reduced to the language; runs of blank lines collapse;
    every H1-H3 needs an anchor, anchors are unique, exactly one H1; HTML outside code raises.
    """
    text = text.lstrip("﻿").replace("\r\n", "\n")
    out: list[str] = []
    pending: list[tuple[int, int, str, str]] = []  # (out line index, level, title, anchor)
    fence: str | None = None

    def emit(line: str) -> None:
        line = line.rstrip()
        if not line and (not out or not out[-1]):
            return
        out.append(line)

    for line in text.split("\n"):
        if fence is not None:
            if closes_fence(line, fence):
                fence = None
            emit(line)
            continue
        marker = fence_marker(line)
        if marker is not None:
            fence = marker
            m = FENCE_RE.match(line)
            assert m is not None
            lang = FENCE_LANG_RE.match(m.group(3))
            emit(f"{m.group(1)}{marker}{lang.group(1) if lang else ''}")
            continue
        prose = ESCAPED_LT_RE.sub(r"\1", INLINE_CODE_RE.sub("", line))
        if HTML_LINE_RE.match(line):
            raise ValueError(f"unhandled HTML outside code fences: {line!r}")
        if INLINE_TAG_RE.search(prose):
            raise ValueError(f"unhandled inline HTML outside code: {line!r}")
        h = HEADING_RE.match(line)
        if h:
            level, title = len(h.group(1)), h.group(2)
            a = ANCHOR_RE.search(title)
            if a:
                title = title[: a.start()]
            if level <= SECTION_MAX_LEVEL:
                if not a:
                    raise ValueError(f"heading without anchor: {line!r}")
                emit("")
                pending.append(
                    (len(out), level, ESCAPED_LT_RE.sub(r"\1<", title).strip(), a.group(1))
                )
            line = f"{h.group(1)} {title}"
        emit(line)

    if fence:
        raise ValueError("unclosed code fence")
    while out and not out[-1]:
        out.pop()
    starts, pos = [], 0
    for line in out:
        starts.append(pos)
        pos += len(line) + 1
    headings = [Heading(lv, t, a, starts[i]) for i, lv, t, a in pending]
    anchors = [h.anchor for h in headings]
    if len(set(anchors)) != len(anchors):
        raise ValueError(
            f"duplicate anchor: {sorted({a for a in anchors if anchors.count(a) > 1})}"
        )
    if sum(h.level == 1 for h in headings) != 1:
        raise ValueError("document needs exactly one H1")
    return CleanResult("\n".join(out) + "\n", headings)


def section_spans(doc_id: str, result: CleanResult) -> list[dict]:
    """Token span of every heading up to the next heading of the same or a higher level."""
    starts = tokens.token_starts(result.text)
    spans = []
    for i, h in enumerate(result.headings):
        end = next(
            (o.offset for o in result.headings[i + 1 :] if o.level <= h.level), len(result.text)
        )
        spans.append(
            {
                "section_id": f"{doc_id}#{h.anchor}",
                "doc_id": doc_id,
                "anchor": h.anchor,
                "title": h.title,
                "level": h.level,
                "start_token": tokens.char_to_token(starts, h.offset),
                "end_token": tokens.char_to_token(starts, end),
            }
        )
    return spans


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def preprocess(
    doc_file: Path = DOCUMENTS_FILE,
    sections_file: Path = SECTIONS_FILE,
    manifest_file: Path = CORPUS_MANIFEST_FILE,
    snippet_file: Path = DATA_RAW / CORPUS_PROVIDER_SNIPPET,
) -> tuple[int, int]:
    """Convert and clean documents.jsonl in place; write sections.jsonl and the corpus manifest."""
    if not doc_file.exists():
        raise FileNotFoundError(f"{doc_file} not found; run src/ingest.py first")
    if not snippet_file.is_file():
        raise FileNotFoundError(f"{snippet_file} not found; run src/snapshot.py first")
    docs = [json.loads(line) for line in doc_file.read_text(encoding="utf-8").splitlines() if line]
    if docs and not any(d["text"].startswith("---\n") for d in docs):
        raise RuntimeError(f"{doc_file} is already preprocessed; run src/ingest.py first")
    snippet = parse_provider_snippet(snippet_file.read_text(encoding="utf-8"))

    sections: list[dict] = []
    for doc in docs:
        try:
            result = clean_markdown(
                to_markdown(doc["text"], doc["path"].removesuffix(CORPUS_PAGE_SUFFIX), snippet)
            )
        except ValueError as e:
            raise ValueError(f"{doc['path']}: {e}") from e
        doc["text"] = result.text
        doc["tokens"] = tokens.count(result.text)
        sections.extend(section_spans(doc["doc_id"], result))

    _write_jsonl(doc_file, docs)
    _write_jsonl(sections_file, sections)
    with manifest_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(MANIFEST_HEADER)
        for d in docs:
            writer.writerow([d["doc_id"], d["path"], d["title"], d["area"], d["tokens"], "yes"])
    return len(docs), len(sections)


if __name__ == "__main__":
    n_docs, n_sections = preprocess()
    print(
        f"{n_docs} documents, {n_sections} sections -> {DOCUMENTS_FILE.name}, {SECTIONS_FILE.name}"
    )
