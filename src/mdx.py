"""MDX pages of the e2e documentation (Mintlify) to Markdown (ADR 0038).

to_markdown turns one page into Markdown with an anchored H1 from the frontmatter (title, then the
description as first paragraph) and the site's anchor on every H2/H3 heading. Every text a reader of
the site sees is kept: admonitions, accordions, tabs and steps become bold labels, cards and video
cards list items, agent prompts text blocks, the provider snippet a table and code blocks; code
fence titles become labels. Only imports, media embeds and legacy anchors go. Anything else raises,
naming the body line. preprocess.py then records the sections.
"""

import re
from dataclasses import dataclass
from typing import NoReturn

from config import SECTION_MAX_LEVEL

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)
FRONTMATTER_LINE_RE = re.compile(r'^"?([\w:]+)"?:\s*(.*?)\s*$')
LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
JS_TOKEN_RE = re.compile(
    r"""\s*(?:
      (?P<str>'(?:[^'\\\n]|\\.)*'|"(?:[^"\\\n]|\\.)*")
    | (?P<tpl>`(?:[^`\\$]|\\.|\$(?!\{))*`)
    | (?P<word>[A-Za-z_$][\w$]*)
    | (?P<num>-?\d+(?:\.\d+)?)
    | (?P<punct>[\[\]{}:,])
    )""",
    re.S | re.X,
)
JS_CONSTANTS = {"true": True, "false": False, "null": None}
PROVIDER_REQUIRED = {"id", "name", "group", "packages", "code", "model", "env", "docs"}
PROVIDER_OPTIONAL = {"note", "readsAtLoad"}
PROVIDER_PARTS = {
    "install": "Install",
    "env": "Environment",
    "config": "e2e.config.ts",
    "model": "Model setup",
}
READS_AT_LOAD_RE = re.compile(r"provider\.readsAtLoad\s*\?\s*('(?:[^'\\]|\\.)*')")
PLACEHOLDER_RE = re.compile(r"\$\{provider\.(\w+)\}")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """(keys, body) of a page. Values are single-line scalars, optionally quoted; anything else
    raises."""
    text = text.lstrip("\ufeff").replace("\r\n", "\n")
    m = FRONTMATTER_RE.match(text)
    if m is None:
        raise ValueError("no frontmatter")
    meta: dict[str, str] = {}
    for line in m.group(1).split("\n"):
        if not line.strip():
            continue
        f = FRONTMATTER_LINE_RE.match(line)
        if f is None or f.group(2) in (">", "|", ">-", "|-"):
            raise ValueError(f"unsupported frontmatter line: {line!r}")
        value = f.group(2)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        meta[f.group(1)] = value
    return meta, text[m.end() :]


def slug(heading: str) -> str:
    """The site's anchor of a heading: link targets and backticks dropped, lowercase, every run
    of other characters than a-z0-9 replaced by "-", "-" stripped at both ends (checked against
    the live site)."""
    text = LINK_RE.sub(r"\1", heading).replace("`", "").lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def _unescape(body: str) -> str:
    return re.sub(
        r"\\(.)", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), body, flags=re.S
    )


def _punct(src: str, pos: int, char: str) -> int | None:
    m = JS_TOKEN_RE.match(src, pos)
    return m.end() if m is not None and m.group("punct") == char else None


def _after_item(src: str, pos: int, close: str) -> int:
    comma = _punct(src, pos, ",")
    if comma is not None:
        return comma
    if _punct(src, pos, close) is not None:
        return pos
    raise ValueError(f"expected ',' or {close!r} at {src[pos : pos + 40]!r}")


def parse_js_literal(src: str, pos: int = 0) -> tuple[object, int]:
    """The JavaScript literal (array, object, string, template without interpolation, number,
    true/false/null) at pos, and the position after it."""
    m = JS_TOKEN_RE.match(src, pos)
    if m is None:
        raise ValueError(f"unsupported JavaScript at {src[pos : pos + 40]!r}")
    kind, text = m.lastgroup, m.group(m.lastgroup)
    if kind in ("str", "tpl"):
        return _unescape(text[1:-1]), m.end()
    if kind == "num":
        return (float(text) if "." in text else int(text)), m.end()
    if kind == "word":
        if text not in JS_CONSTANTS:
            raise ValueError(f"unsupported JavaScript identifier {text!r}")
        return JS_CONSTANTS[text], m.end()
    pos = m.end()
    if text == "[":
        items: list[object] = []
        while (close := _punct(src, pos, "]")) is None:
            value, pos = parse_js_literal(src, pos)
            items.append(value)
            pos = _after_item(src, pos, "]")
        return items, close
    if text == "{":
        obj: dict[str, object] = {}
        while (close := _punct(src, pos, "}")) is None:
            key = JS_TOKEN_RE.match(src, pos)
            if key is None or key.lastgroup not in ("word", "str"):
                raise ValueError(f"expected a key at {src[pos : pos + 40]!r}")
            name = key.group("word") or _unescape(key.group("str")[1:-1])
            colon = _punct(src, key.end(), ":")
            if colon is None:
                raise ValueError(f"expected ':' after {name!r}")
            obj[name], pos = parse_js_literal(src, colon)
            pos = _after_item(src, pos, "}")
        return obj, close
    raise ValueError(f"unexpected {text!r} at {src[pos - 1 : pos + 40]!r}")


@dataclass(frozen=True)
class ProviderSnippet:
    """Data of the <ModelProvider> snippet: the provider list, the first package manager's install
    command, the templates of the config and model views, and the note for readsAtLoad providers."""

    providers: list[dict]
    install: str
    config: str
    model: str
    reads_at_load: str


def _const(jsx: str, name: str) -> object:
    marker = f"const {name} = "
    start = jsx.find(marker)
    if start < 0:
        raise ValueError(f"provider snippet: no `{marker.strip()}`")
    return parse_js_literal(jsx, start + len(marker))[0]


def _template(jsx: str, name: str) -> str:
    m = re.search(rf"const {name} = `((?:[^`\\]|\\.)*)`;", jsx, re.S)
    if m is None:
        raise ValueError(f"provider snippet: no template `const {name}`")
    return _unescape(m.group(1))


def parse_provider_snippet(jsx: str) -> ProviderSnippet:
    providers, managers = _const(jsx, "providers"), _const(jsx, "managers")
    if not isinstance(providers, list) or not providers:
        raise ValueError("provider snippet: empty provider list")
    for p in providers:
        keys = set(p) if isinstance(p, dict) else set()
        if not PROVIDER_REQUIRED <= keys <= PROVIDER_REQUIRED | PROVIDER_OPTIONAL:
            raise ValueError(f"provider snippet: unexpected provider keys {sorted(keys)}")
    ids = [p["id"] for p in providers]
    if len(set(ids)) != len(ids):
        raise ValueError("provider snippet: duplicate provider id")
    note = READS_AT_LOAD_RE.search(jsx)
    if note is None:
        raise ValueError("provider snippet: no readsAtLoad note")
    return ProviderSnippet(
        providers=providers,
        install=managers[0][1],
        config=_template(jsx, "config"),
        model=_template(jsx, "model"),
        reads_at_load=str(parse_js_literal(note.group(1))[0]),
    )


def _note(provider: dict, snippet: ProviderSnippet) -> str:
    parts = [snippet.reads_at_load if provider.get("readsAtLoad") else "", provider.get("note", "")]
    return " ".join(p for p in parts if p)


def _cell(text: str) -> str:
    return re.sub(r"\s+", " ", text).replace("|", "\\|").strip()


def _fill(template: str, provider: dict) -> str:
    text = PLACEHOLDER_RE.sub(lambda m: str(provider[m.group(1)]), template)
    if "${" in text:
        raise ValueError(f"provider snippet: unknown placeholder in {template[:40]!r}")
    return text


def render_provider(show: str, snippet: ProviderSnippet) -> list[str]:
    """Markdown lines for <ModelProvider show=...>: `select` lists every provider as a table; the
    parts show what the site shows before any selection (first provider, first package manager)."""
    if show == "select":
        rows = [
            "| Provider | Group | Packages | Variables | Import | Model | Note |",
            "|---|---|---|---|---|---|---|",
        ]
        for p in snippet.providers:
            cells = [
                f"[{p['name']}]({p['docs']})",
                p["group"],
                ", ".join(f"`{x}`" for x in p["packages"]),
                ", ".join(f"`{x}`" for x in p["env"]),
                f"`{p['code']}`",
                f"`{p['model']}`",
                _note(p, snippet),
            ]
            rows.append("| " + " | ".join(_cell(c) for c in cells) + " |")
        return rows
    if show not in PROVIDER_PARTS:
        raise ValueError(f"unknown <ModelProvider show={show!r}>")
    p = snippet.providers[0]
    lines = [f"**{PROVIDER_PARTS[show]} · {p['name']}**", ""]
    if show == "install":
        code = ("bash", " ".join([snippet.install, "ai", *p["packages"]]))
    elif show == "env":
        code = ("bash", "\n".join(f"export {name}=..." for name in p["env"])) if p["env"] else None
    else:
        code = ("ts", _fill(snippet.config if show == "config" else snippet.model, p))
    lines += [f"```{code[0]}", *code[1].split("\n"), "```"] if code else ["No variables."]
    if show == "env" and _note(p, snippet):
        lines += ["", _note(p, snippet)]
    return lines


def nav_areas(nav: dict) -> dict[str, str]:
    """Page (path without suffix) -> area, in navigation order: the page's group, or the tab for
    pages listed directly under a tab."""
    areas: dict[str, str] = {}
    for tab in nav["navigation"]["tabs"]:
        entries = [(group["group"], group["pages"]) for group in tab.get("groups", [])]
        if "pages" in tab:
            entries.append((tab["tab"], tab["pages"]))
        for area, pages in entries:
            for page in pages:
                if not isinstance(page, str):
                    raise ValueError(f"nested navigation entry in {area!r}: {page!r}")
                if page in areas:
                    raise ValueError(f"page {page!r} listed twice in the navigation")
                areas[page] = area
    return areas


FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)\s*$")
IMPORT_RE = re.compile(r"""^import\s.+\sfrom\s+['"][^'"]+['"];?$""")
EXPORT_RE = re.compile(r"^export const (\w+) = ")
TAG_START_RE = re.compile(r"^\s*</?(?:[A-Z]\w*|video|a|span)\b")
TAG_RE = re.compile(r"<(/?)([A-Za-z]\w*)(.*?)(/?)>", re.S)
ATTR = r'([\w-]+)(?:=(?:"([^"]*)"|(\{[^{}]*\})))?'
ATTR_RE = re.compile(ATTR)
ATTRS_RE = re.compile(rf"(?:\s+{ATTR})*\s*")
INLINE_PAIR_RE = re.compile(r"^(\s*)(<([A-Z]\w*)(?:\s[^<>]*)?>)(.+)(</\3>)\s*$")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
MARKUP_RE = re.compile(r"</?[A-Za-z][\w-]*(?:\s[^>]*)?/?>|\{[^}]*\}")
FENCE_FLAGS = ("expandable", "wrap")
ADMONITIONS = ("Note", "Warning", "Tip")
LABELLED = ("Accordion", "Tab")
WRAPPERS = (
    "AccordionGroup",
    "Tabs",
    "CodeGroup",
    "CardGroup",
    "ShowMore",
    "Video",
    "SetupPrompt",
    "Steps",
)
DROPPED = ("video", "a", "span")  # media embeds and legacy anchors, always self-closing
PROMPT_LABEL = "Agent prompt"  # header text of the SetupPrompt snippet


@dataclass
class _Frame:
    name: str
    attrs: dict[str, str]
    count: int = 0  # steps so far (Steps)
    body: list[str] | None = None  # collected lines (Card)


def _tag_end(text: str) -> int:
    """Index of the ">" ending the tag at the start of text (quotes and braces skipped), or -1."""
    quote, depth = "", 0
    for k, ch in enumerate(text):
        if quote:
            quote = "" if ch == quote else quote
        elif ch in "\"'":
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == ">" and depth == 0:
            return k
    return -1


def _fence_info(info: str) -> tuple[str, str]:
    """(language, label) of a fence info string: `ts title="a.ts" expandable` -> ("ts", "a.ts"),
    `bash npm` -> ("bash", "npm")."""
    title = re.search(r'title="([^"]*)"', info)
    words = re.sub(r'\s*title="[^"]*"', "", info).split()
    rest = [w for w in words[1:] if w not in FENCE_FLAGS]
    if any(c in w for w in rest for c in "={}") or (title and rest):
        raise ValueError(f"unsupported fence info {info!r}")
    return (words[0] if words else ""), (title.group(1) if title else " ".join(rest))


def _prose(line: str, open_span: bool) -> tuple[str, bool]:
    """The line without inline code, and whether a code span stays open into the next line. A
    blank line ends the paragraph and with it any open span."""
    if not line.strip():
        return "", False
    if open_span:
        if "`" not in line:
            return "", True
        line = line[line.index("`") + 1 :]
    line = INLINE_CODE_RE.sub("", line)
    if "`" in line:
        return line[: line.index("`")], True
    return line, False


def _dedent(line: str, indent: int) -> str:
    return line[min(indent, len(line) - len(line.lstrip(" "))) :]


def to_markdown(text: str, page: str, snippet: ProviderSnippet | None = None) -> str:
    meta, body = parse_frontmatter(text)
    if not meta.get("title"):
        raise ValueError("no title in the frontmatter")
    out = [f"# {meta['title']} {{#{slug(page)}}}", ""]
    if meta.get("description"):
        out += [meta["description"], ""]
    lines = body.split("\n")
    exports: dict[str, str] = {}
    stack: list[_Frame] = []
    fence: tuple[str, int] | None = None  # (marker, indent) of the open fence
    i = 0
    open_span = False  # an inline code span continues from the previous line (CommonMark)
    origin = list(range(1, len(lines) + 1))  # source line of each entry (tag pairs get split)

    def fail(message: str) -> NoReturn:
        raise ValueError(f"line {origin[max(i, 1) - 1]}: {message}")

    def emit(line: str) -> None:
        if stack and stack[-1].body is not None:
            stack[-1].body.append(line)
        elif line.strip() or out[-1].strip():  # runs of blank lines collapse to one
            out.append(line)

    def label(textline: str) -> None:
        emit("")
        emit(textline)

    def open_tag(name: str, attrs: dict[str, str]) -> None:
        frame = _Frame(name, attrs)
        if name in ADMONITIONS:
            label(f"**{name}**")
        elif name in LABELLED:
            label(f"**{attrs.get('title', '')}**")
        elif name == "Step":
            if not stack or stack[-1].name != "Steps":
                fail("<Step> outside <Steps>")
            stack[-1].count += 1
            label(f"**{stack[-1].count}. {attrs.get('title', '')}**")
        elif name == "Card":
            frame.body = []
        elif name not in WRAPPERS:
            fail(f"unknown component <{name}>")
        stack.append(frame)

    def close_tag(name: str) -> None:
        if not stack or stack[-1].name != name:
            fail(f"</{name}> closes <{stack[-1].name if stack else 'nothing'}>")
        frame = stack.pop()
        if frame.body is not None:
            card = " ".join(t.strip() for t in frame.body if t.strip())
            title, href = frame.attrs.get("title", ""), frame.attrs.get("href")
            head = f"[{title}]({href})" if href else f"**{title}**"
            emit(f"- {head}: {card}" if card else f"- {head}")
        elif name in ADMONITIONS or name in LABELLED or name == "Step":
            emit("")

    def self_closing(name: str, attrs: dict[str, str]) -> None:
        if name in DROPPED:
            return
        if name == "ModelProvider":
            if snippet is None:
                fail("<ModelProvider> needs the provider snippet")
            label("")
            for row in render_provider(attrs.get("show", ""), snippet):
                emit(row)
            emit("")
        elif name == "Prompt":
            if not stack or stack[-1].name != "SetupPrompt":
                fail("<Prompt> outside <SetupPrompt>")
            ref = attrs.get("children", "").strip("{} ")
            if ref not in exports:
                fail(f"<Prompt> names unknown export {ref!r}")
            label(f"**{PROMPT_LABEL}**")
            emit("")
            for row in ["```text", *exports[ref].split("\n"), "```"]:
                emit(row)
        elif name == "VideoCard":
            emit(f"- **{attrs.get('title', '')}**: {attrs.get('subtitle', '')}")
        else:
            fail(f"unknown component <{name} />")

    while i < len(lines):
        line = lines[i].rstrip()
        i += 1
        f = FENCE_RE.match(line)
        if fence is not None:
            marker, indent = fence
            if (
                f
                and f.group(2)[0] == marker[0]
                and len(f.group(2)) >= len(marker)
                and not f.group(3).strip()
            ):
                fence = None
                emit(f.group(2))
            else:
                emit(_dedent(line, indent))
            continue
        if f and not (f.group(2)[0] == "`" and "`" in f.group(3)):
            try:
                lang, name = _fence_info(f.group(3).strip())
            except ValueError as e:
                fail(str(e))
            if stack and stack[-1].body is not None:
                fail("code fence inside <Card>")
            if name:
                emit("")
                emit(f"**{name}**")
            fence = (f.group(2), len(f.group(1)))
            emit(f"{f.group(2)}{lang}")
            continue
        stripped = line.strip()
        if not stack and IMPORT_RE.match(stripped):
            continue
        e = EXPORT_RE.match(line)
        if e:
            block = "\n".join(lines[i - 1 :])
            try:
                value, end = parse_js_literal(block, e.end())
            except ValueError as err:
                fail(f"export {e.group(1)}: {err}")
            tail = re.match(r"[ \t]*;?[ \t]*(?:\n|$)", block[end:])
            if not isinstance(value, str) or tail is None:
                fail(f"export {e.group(1)} is not a string constant")
            exports[e.group(1)] = value
            i += block[: end + tail.end()].rstrip("\n").count("\n")
            continue
        pair = INLINE_PAIR_RE.match(line)
        if pair:
            lines[i:i] = [pair.group(4), pair.group(1) + pair.group(5)]
            origin[i:i] = [origin[i - 1]] * 2
            line = pair.group(1) + pair.group(2)
        if TAG_START_RE.match(line):
            tag = line.strip()
            while (end := _tag_end(tag)) < 0:
                if i >= len(lines):
                    fail(f"unclosed tag {tag[:40]!r}")
                tag += "\n" + lines[i].strip()
                i += 1
            if tag[end + 1 :].strip():
                fail(f"text after a tag: {tag!r}")
            t = TAG_RE.fullmatch(tag[: end + 1])
            if t is None or not ATTRS_RE.fullmatch(t.group(3)):
                fail(f"unparsed tag {tag!r}")
            closing, name, raw, selfclose = t.groups()
            attrs = {
                a.group(1): a.group(2) if a.group(2) is not None else (a.group(3) or "")
                for a in ATTR_RE.finditer(raw)
            }
            if closing:
                close_tag(name)
            elif selfclose:
                self_closing(name, attrs)
            elif name in DROPPED:
                fail(f"<{name}> must be self-closing")
            else:
                open_tag(name, attrs)
            continue
        prose, open_span = _prose(line, open_span)
        # a JSX expression may span lines: an unbalanced brace marks one as well
        if MARKUP_RE.search(prose) or prose.count("{") != prose.count("}"):
            fail(f"unhandled markup: {line!r}")
        h = HEADING_RE.match(line)
        if h:
            level, title = len(h.group(1)), h.group(2)
            if level == 1:
                fail("H1 in the page body")
            if level <= SECTION_MAX_LEVEL:
                anchor = slug(title)
                if not anchor:
                    fail(f"heading without slug: {line!r}")
                emit(f"{h.group(1)} {title} {{#{anchor}}}")
                continue
        emit(line)

    if fence is not None:
        raise ValueError("unclosed code fence")
    if stack:
        raise ValueError(f"unclosed <{stack[-1].name}>")
    return "\n".join(out).rstrip("\n") + "\n"
