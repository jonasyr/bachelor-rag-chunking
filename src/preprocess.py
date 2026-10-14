"""Preprocess / clean Markdown (ADR 0019).

Reads documents.jsonl and keeps Composition API content only: drops frontmatter, Options API
blocks, page scripts, demos, sponsor/navigation HTML, comments and container markers, and
records the anchored H1-H3 sections. Rewrites documents.jsonl in place, writes sections.jsonl
and the corpus manifest.
"""

import csv
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path

import tokens
from config import CORPUS_MANIFEST_FILE, DOCUMENTS_FILE, SECTION_MAX_LEVEL, SECTIONS_FILE

# HTML blocks starting a line outside code fences are page furniture (Options API variants,
# demos, sponsor boxes, navigation, promo links) and are dropped, except composition-api
# wrappers, which are unwrapped. Any other HTML line outside fences is an error.
UNWRAP_CLASS = "composition-api"
DROP_BLOCK_TAGS = ("div", "p", "ScrimbaLink", "VueSchoolLink")
DROP_LINE_TAGS = ("img", "details", "/details", "br")

FENCE_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")  # CommonMark: at most 3 spaces of indent
FENCE_LANG_RE = re.compile(r"\s*([\w+-]*)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
ANCHOR_RE = re.compile(r"\s*\{#([^}]+)\}\s*$")
API_MARKER_RE = re.compile(r"\s*(\\\*)+$")  # `\*` / `\*\*`: API-style markers on headings
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
VERSION_BADGE_RE = re.compile(r'<sup class="vt-badge" data-text="([^"]+)"\s*/>')
WBR_RE = re.compile(r"<wbr\s*/?>")
# A v-pre span holds inline code (which may itself contain tags) or plain text.
V_PRE_SPAN_RE = re.compile(r"<span v-pre>((?:`[^`]*`|[^`<])*)</span>")
BR_RE = re.compile(r"\s*<br\s*/?>\s*")  # inline line break (API page titles): a space
# CommonMark escape `\<`: a literal "<", never a tag. Only an odd run of backslashes escapes it
# (`\\<b>` is a literal backslash and a real tag); group 1 keeps the escaped backslash pairs.
ESCAPED_LT_RE = re.compile(r"(?<!\\)((?:\\\\)*)\\<")
CODE_TAG_RE = re.compile(r"<code(?: v-pre)?>(.*?)</code>")
INLINE_TAG_RE = re.compile(r"</?[A-Za-z][\w-]*(?:\s[^>]*)?/?>")
# Vue tool links carry the whole demo as an encoded URL hash: noise for retrieval (ADR 0020).
ENCODED_TOOL_URL_RE = re.compile(
    r"(https://(?:play|sfc|explorer|template-explorer)\.vuejs\.org/)#[^)\s>\"']*"
)
# Pre-rendered, syntax-highlighted listings (e.g. the create-vue prompts) become fenced code.
LANGUAGE_BLOCK_RE = re.compile(r'^\s*<div class="language-([\w-]+)"><pre><code>(.*)$')
LANGUAGE_BLOCK_END = "</code></pre></div>"
INLINE_SELF_CLOSING_RE = re.compile(r"\s*<(sup|[A-Z][\w-]*)\b[^>]*/>")
HTML_LINE_RE = re.compile(r"^\s*</?[A-Za-z][\w-]*(?=[\s/>]|$)")  # not autolinks
MANIFEST_HEADER = ["file_id", "path", "title", "section", "tokens", "included"]
# Manifest section of the areas without subfolders (D25).
AREA_SECTIONS = {"api": "API Reference", "style-guide": "Style Guide"}
# Manifest `section` per folder below guide/ (pages directly in guide/ get "Guide").
SECTION_NAMES = {
    "best-practices": "Best Practices",
    "built-ins": "Built-ins",
    "components": "Components",
    "essentials": "Essentials",
    "extras": "Extras",
    "reusability": "Reusability",
    "scaling-up": "Scaling Up",
    "typescript": "TypeScript",
}


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


def _code_spans(line: str) -> list[tuple[int, int]]:
    return [m.span() for m in INLINE_CODE_RE.finditer(line)]


def _sub_outside_code(pattern: re.Pattern[str], repl: str, line: str) -> str:
    """pattern.sub(repl, line), leaving matches that start inside inline code untouched."""
    spans = _code_spans(line)

    def replace(m: re.Match[str]) -> str:
        if any(start <= m.start() < end for start, end in spans):
            return m.group(0)
        return m.expand(repl)

    return pattern.sub(replace, line)


def _find_outside_code(line: str, token: str) -> int:
    """Index of the first token outside inline code, or -1."""
    spans = _code_spans(line)
    i = line.find(token)
    while i >= 0 and any(start <= i < end for start, end in spans):
        i = line.find(token, i + 1)
    return i


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


def has_anchored_heading(text: str) -> bool:
    """True if a heading outside code fences still carries a {#anchor}, i.e. text is not cleaned."""
    fence: str | None = None
    for line in text.split("\n"):
        if fence is not None:
            if closes_fence(line, fence):
                fence = None
        elif (marker := fence_marker(line)) is not None:
            fence = marker
        elif HEADING_RE.match(line) and ANCHOR_RE.search(line):
            return True
    return False


def heading_title(raw: str) -> str:
    """Display title of a heading: inline line breaks as spaces, escaped `\\<` as `<`."""
    return ESCAPED_LT_RE.sub(r"\1<", BR_RE.sub(" ", raw)).strip()


def _strip_frontmatter(lines: list[str]) -> list[str]:
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return lines[i + 1 :]
        raise ValueError("unclosed frontmatter")
    return lines


def clean_markdown(text: str) -> CleanResult:
    """Return Composition-API-only Markdown and its anchored H1-H3 headings."""
    text = text.lstrip("\ufeff").replace("\r\n", "\n")
    lines = _strip_frontmatter(text.split("\n"))

    out: list[str] = []
    pending: list[tuple[int, int, str, str]] = []  # (out line index, level, title, anchor)
    fence: str | None = None  # marker of the open code fence
    drop: tuple[str, int] | None = None  # (tag, depth) of the HTML block being dropped
    unwrap: list[tuple[str, int]] = []  # (tag, depth) of open composition-api wrappers
    page_tag: str | None = None  # open <script>/<style> being dropped
    in_comment = False
    listing: str | None = None  # language of the open pre-rendered listing

    def emit(line: str) -> None:
        line = line.rstrip()
        if not line and (not out or not out[-1]):
            return
        out.append(line)

    for line in lines:
        if listing is None and fence is None and drop is None and not (page_tag or in_comment):
            lb = LANGUAGE_BLOCK_RE.match(line)
            if lb:
                listing, line = lb.group(1), lb.group(2)
                emit(f"```{listing}")
        if listing is not None:
            end = line.find(LANGUAGE_BLOCK_END)
            content = line if end < 0 else line[:end]
            out.append(html.unescape(INLINE_TAG_RE.sub("", content)).rstrip())
            if end >= 0:
                emit("```")
                listing = None
            continue
        if fence is not None:
            if closes_fence(line, fence):
                fence = None
            if drop is None:
                emit(line)
            continue
        marker = fence_marker(line)
        if marker is not None:
            fence = marker
            if drop is None:
                m = FENCE_RE.match(line)
                assert m is not None
                lang = FENCE_LANG_RE.match(m.group(3))
                emit(f"{m.group(1)}{marker}{lang.group(1) if lang else ''}")
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
        line = _sub_outside_code(COMMENT_RE, "", line)
        opening = _find_outside_code(line, "<!--")
        if opening >= 0:
            line, in_comment = line[:opening], True
        u = UNWRAP_OPEN_RE.match(line)
        if u:
            unwrap.append((u.group(1), 1))
            continue
        b = BLOCK_OPEN_RE.match(line)
        if b:  # checked before the wrapper count: a dropped block's tags never reach it
            depth = _tag_balance(b.group(1), line)
            drop = (b.group(1), depth) if depth > 0 else None
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
        for pattern, repl in (
            (OPTIONS_SPAN_RE, ""),
            (COMPOSITION_SPAN_RE, r"\1"),
            (EMPTY_SPAN_RE, ""),
            (VERSION_BADGE_RE, r"(\1)"),
            (INLINE_SELF_CLOSING_RE, ""),
            (WBR_RE, ""),
            (BR_RE, " "),
            (V_PRE_SPAN_RE, r"\1"),
            (CODE_TAG_RE, r"`\1`"),
            (ENCODED_TOOL_URL_RE, r"\1"),
        ):
            line = _sub_outside_code(pattern, repl, line)
        prose = ESCAPED_LT_RE.sub(r"\1", INLINE_CODE_RE.sub("", line))
        if 'class="options-api"' in prose:
            raise ValueError(f"options-api markup left after cleaning: {line!r}")
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
            title = API_MARKER_RE.sub("", title)
            if level <= SECTION_MAX_LEVEL:
                if not a:
                    raise ValueError(f"heading without anchor: {line!r}")
                emit("")
                pending.append((len(out), level, heading_title(title), a.group(1)))
            line = f"{h.group(1)} {title}"
        emit(line)

    for state, what in (
        (fence, "code fence"),
        (drop, "HTML block"),
        (unwrap, "composition-api wrapper"),
        (page_tag, "<script>/<style>"),
        (in_comment, "HTML comment"),
        (listing, "pre-rendered listing"),
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


def manifest_section(path: str) -> str:
    """Manifest `section` column: the area name, or for guide/<folder>/<page>.md the folder."""
    parts = path.split("/")
    if parts[0] in AREA_SECTIONS:
        return AREA_SECTIONS[parts[0]]
    if parts[0] != "guide":
        raise ValueError(f"{path}: no manifest section for area {parts[0]!r}")
    if len(parts) == 2:
        return "Guide"
    if parts[1] not in SECTION_NAMES:
        raise ValueError(f"{path}: no manifest section for folder {parts[1]!r}")
    return SECTION_NAMES[parts[1]]


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def preprocess(
    doc_file: Path = DOCUMENTS_FILE,
    sections_file: Path = SECTIONS_FILE,
    manifest_file: Path = CORPUS_MANIFEST_FILE,
) -> tuple[int, int]:
    """Clean documents.jsonl in place; write sections.jsonl and the corpus manifest."""
    if not doc_file.exists():
        raise FileNotFoundError(f"{doc_file} not found; run src/ingest.py first")
    docs = [json.loads(line) for line in doc_file.read_text(encoding="utf-8").splitlines() if line]
    if docs and not any(has_anchored_heading(d["text"]) for d in docs):
        raise RuntimeError(f"{doc_file} is already preprocessed; run src/ingest.py first")

    sections: list[dict] = []
    for doc in docs:
        try:
            result = clean_markdown(doc["text"])
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
            writer.writerow(
                [
                    d["doc_id"],
                    d["path"],
                    d["title"],
                    manifest_section(d["path"]),
                    d["tokens"],
                    "yes",
                ]
            )
    return len(docs), len(sections)


if __name__ == "__main__":
    n_docs, n_sections = preprocess()
    print(
        f"{n_docs} documents, {n_sections} sections -> {DOCUMENTS_FILE.name}, {SECTIONS_FILE.name}"
    )
