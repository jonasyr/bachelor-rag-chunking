"""Preprocess / clean Markdown (ADR 0019).

Reads documents.jsonl and keeps Composition API content only: drops frontmatter, Options API
blocks, page scripts, demos, sponsor/navigation HTML, comments and container markers, and
records the anchored H1-H3 sections. Rewrites documents.jsonl in place, writes sections.jsonl
and the corpus manifest.
"""

import re
from dataclasses import dataclass

SECTION_MAX_LEVEL = 3
# HTML blocks starting a line outside code fences are page furniture (Options API variants,
# demos, sponsor boxes, navigation, promo links) and are dropped, except composition-api
# wrappers, which are unwrapped. Any other HTML line outside fences is an error.
UNWRAP_CLASS = "composition-api"
DROP_BLOCK_TAGS = ("div", "p", "ScrimbaLink", "VueSchoolLink")
DROP_LINE_TAGS = ("img", "details", "/details", "br")

FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([\w+-]*)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
ANCHOR_RE = re.compile(r"\s*\{#([^}]+)\}\s*$")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
BLOCK_OPEN_RE = re.compile(r"^\s*<(" + "|".join(DROP_BLOCK_TAGS) + r")\b([^>]*)>")
UNWRAP_OPEN_RE = re.compile(r'^\s*<(div|p) class="' + UNWRAP_CLASS + r'">\s*$')
LINE_TAG_RE = re.compile(r"^\s*<(" + "|".join(DROP_LINE_TAGS) + r")\b[^>]*>\s*$")
SUMMARY_RE = re.compile(r"^\s*<summary>(.*?)</summary>\s*$")
PAGE_TAG_RE = re.compile(r"^<(script|style)\b")
COMPONENT_LINE_RE = re.compile(r"^\s*<[A-Z][\w-]*\b[^>]*/>\s*$")
CONTAINER_OPEN_RE = re.compile(r"^\s*:::+\s*([a-z][\w-]*)\s*(.*?)\s*$")
CONTAINER_CLOSE_RE = re.compile(r"^\s*:::+\s*$")
COMMENT_RE = re.compile(r"\s*<!--.*?-->")
OPTIONS_SPAN_RE = re.compile(r'<span class="options-api">.*?</span>')
COMPOSITION_SPAN_RE = re.compile(r'<span class="composition-api">(.*?)</span>')
EMPTY_SPAN_RE = re.compile(r'<span id="[^"]*"></span>')
INLINE_SELF_CLOSING_RE = re.compile(r"\s*<(sup|[A-Z][\w-]*)\b[^>]*/>")
HTML_LINE_RE = re.compile(r"^\s*</?[A-Za-z]")


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


def _tag_balance(tag: str, line: str) -> int:
    """Opened minus closed <tag> elements on line, ignoring inline code and self-closing tags."""
    line = INLINE_CODE_RE.sub("", line)
    opens = len(re.findall(rf"<{tag}\b[^>]*(?<!/)>", line))
    return opens - len(re.findall(rf"</{tag}\s*>", line))


def _strip_frontmatter(lines: list[str]) -> list[str]:
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return lines[i + 1 :]
        raise ValueError("unclosed frontmatter")
    return lines


def clean_markdown(text: str) -> CleanResult:
    """Return Composition-API-only Markdown and its anchored H1-H3 headings."""
    text = text.lstrip("﻿").replace("\r\n", "\n")
    lines = _strip_frontmatter(text.split("\n"))

    out: list[str] = []
    pending: list[tuple[int, int, str, str]] = []  # (out line index, level, title, anchor)
    fence: str | None = None  # marker of the open code fence
    drop: tuple[str, int] | None = None  # (tag, depth) of the HTML block being dropped
    unwrap: list[tuple[str, int]] = []  # (tag, depth) of open composition-api wrappers
    page_tag: str | None = None  # open <script>/<style> being dropped
    in_comment = False

    def emit(line: str) -> None:
        line = line.rstrip()
        if not line and (not out or not out[-1]):
            return
        out.append(line)

    for line in lines:
        m = FENCE_RE.match(line)
        if fence is not None:
            if m and m.group(2)[0] == fence[0] and len(m.group(2)) >= len(fence) and not m.group(3):
                fence = None
            if drop is None:
                emit(line)
            continue
        if m:
            fence = m.group(2)
            if drop is None:
                emit(f"{m.group(1)}{m.group(2)}{m.group(3)}")
            continue
        if drop is not None:
            depth = drop[1] + _tag_balance(drop[0], line)
            drop = (drop[0], depth) if depth > 0 else None
            continue
        if page_tag:
            if f"</{page_tag}>" in line:
                page_tag = None
            continue
        if in_comment:
            if "-->" not in line:
                continue
            line, in_comment = line.split("-->", 1)[1], False
        line = COMMENT_RE.sub("", line)
        if "<!--" in line:
            line, in_comment = line.split("<!--", 1)[0], True
        u = UNWRAP_OPEN_RE.match(line)
        if u:
            unwrap.append((u.group(1), 1))
            continue
        if unwrap:
            tag, depth = unwrap[-1]
            depth += _tag_balance(tag, line)
            if depth == 0:
                unwrap.pop()
                if line.strip() == f"</{tag}>":
                    continue
                raise ValueError(f"composition-api wrapper closed mid-line: {line!r}")
            unwrap[-1] = (tag, depth)
        b = BLOCK_OPEN_RE.match(line)
        if b:
            depth = _tag_balance(b.group(1), line)
            drop = (b.group(1), depth) if depth > 0 else None
            continue
        tag = PAGE_TAG_RE.match(line)
        if tag:
            if f"</{tag.group(1)}>" not in line:
                page_tag = tag.group(1)
            continue
        s = SUMMARY_RE.match(line)
        if s:
            line = s.group(1)
        if LINE_TAG_RE.match(line) or COMPONENT_LINE_RE.match(line):
            continue
        if CONTAINER_CLOSE_RE.match(line):
            continue
        c = CONTAINER_OPEN_RE.match(line)
        if c:
            if c.group(2):
                emit(c.group(2))
            continue
        line = OPTIONS_SPAN_RE.sub("", line)
        line = COMPOSITION_SPAN_RE.sub(r"\1", line)
        line = EMPTY_SPAN_RE.sub("", line)
        line = INLINE_SELF_CLOSING_RE.sub("", line)
        if 'class="options-api"' in line:
            raise ValueError(f"options-api markup left after cleaning: {line!r}")
        if HTML_LINE_RE.match(line):
            raise ValueError(f"unhandled HTML outside code fences: {line!r}")
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
                pending.append((len(out), level, title, a.group(1)))
            line = f"{h.group(1)} {title}"
        emit(line)

    for state, what in (
        (fence, "code fence"),
        (drop, "HTML block"),
        (unwrap, "composition-api wrapper"),
        (page_tag, "<script>/<style>"),
        (in_comment, "HTML comment"),
    ):
        if state:
            raise ValueError(f"unclosed {what}")
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
