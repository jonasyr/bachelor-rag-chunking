"""MDX pages of the e2e documentation (Mintlify) to Markdown (ADR 0038).

nav_areas reads the navigation (docs.json).
"""

import re
from dataclasses import dataclass

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
