"""Cloze probes from a candidate's pages (ADR 0038).

In every prose sentence (outside code blocks, tables, HTML and admonitions) with an inline code
span, that span is masked once; the masked section text is kept for the open-book run. At most
CORPUS_PROBE_PER_PAGE probes per page, drawn with CORPUS_PROBE_SEED.

The probes of the recorded runs were drawn before the candidates were sorted, so their sample
depended on Python's hash seed. --recorded rebuilds exactly those probes (with their masked
section text) from results/<name>.jsonl and the pages, so the recorded runs can be repeated with
identical inputs; it stops if a recorded probe is not found on the pages.

Usage: uv run python scripts/corpus_probe/build_probes.py NAME [--recorded]
"""

import collections
import random
import re
import sys

from common import DOCS_DIR, PROBES_DIR, RESULTS_DIR, read_json, read_jsonl, write_json

from config import (
    CORPUS_PROBE_PER_PAGE,
    CORPUS_PROBE_SEED,
    CORPUS_PROBE_SENTENCE_CHARS,
    CORPUS_PROBE_SPAN_CHARS,
)

SPAN = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")  # one complete single-backtick code span
# The recorded runs filtered by length inside the pattern, so adjacent one-character spans
# (`+`/`×`) let a closing backtick open a bogus span; --recorded rebuilds them with this pattern.
LEGACY_SPAN = re.compile(
    rf"`([^`\n]{{{CORPUS_PROBE_SPAN_CHARS[0]},{CORPUS_PROBE_SPAN_CHARS[1]}}})`"
)
TRIVIAL = ("true", "false", "null", "undefined")


def sections(text: str, title: str) -> list[tuple[str, list[str]]]:
    """(heading, lines) per section; the page title heads the text before the first heading."""
    out, heading, lines, in_code = [], title, [], False
    for line in text.split("\n"):
        if line.strip().startswith("```"):
            in_code = not in_code
            lines.append(line)
            continue
        m = re.match(r"^(#{1,6})\s+(.*)", line) if not in_code else None
        if m:
            out.append((heading, lines))
            heading, lines = m.group(2).strip(), []
            continue
        lines.append(line)
    out.append((heading, lines))
    return out


def candidates(doc: dict, legacy: bool = False) -> list[dict]:
    lo, hi = CORPUS_PROBE_SENTENCE_CHARS
    found = []
    for heading, lines in sections(doc["text"], doc["title"]):
        body = "\n".join(lines)
        prose, in_code = [], False
        for line in lines:
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code or line.strip().startswith(("|", "<", ":::", "-  ```")):
                continue
            prose.append(line.strip(" -*>"))
        for sentence in re.split(r"(?<=[.!?])\s+", " ".join(prose)):
            if legacy:
                spans = LEGACY_SPAN.findall(sentence)
            else:
                lo_span, hi_span = CORPUS_PROBE_SPAN_CHARS
                spans = [t for t in SPAN.findall(sentence) if lo_span <= len(t) <= hi_span]
            if not (lo <= len(sentence) <= hi) or not spans:
                continue
            for term in sorted(set(spans)):  # sorted: set order depends on the hash seed
                if spans.count(term) > 1 or term.lower() in TRIVIAL:
                    continue
                masked = sentence.replace(f"`{term}`", "`[MASK]`", 1)
                if term in masked:
                    continue  # term still visible elsewhere in the sentence
                found.append(
                    {
                        "doc_id": doc["doc_id"],
                        "path": doc["path"],
                        "page": doc["title"],
                        "section": heading,
                        "sentence": masked,
                        "answer": term,
                        "section_text": body.replace(term, "[MASK]"),
                    }
                )
    return found


def kind(term: str) -> str:
    if term.startswith(("v-", "<", "@", ":", "#")):
        return "template"
    if term.endswith(")"):
        return "function"
    if re.fullmatch(r"[\d.]+|'[^']*'|\"[^\"]*\"", term):
        return "value"
    return "identifier/option"


def build(docs: list[dict]) -> list[dict]:
    random.seed(CORPUS_PROBE_SEED)  # one seeded stream over the pages in order
    probes = []
    for doc in docs:
        found = candidates(doc)
        random.shuffle(found)
        probes += found[:CORPUS_PROBE_PER_PAGE]
    for p in probes:
        p["kind"] = kind(p["answer"])
        p["area"] = p["path"].split("/")[0] if "/" in p["path"] else "root"
    return probes


def recorded(docs: list[dict], results: list[dict]) -> list[dict]:
    """The recorded probes in their order, rebuilt from the pages (ignores the leak filter's
    drops, which were never run)."""
    pool = {}
    for doc in docs:
        for c in candidates(doc, legacy=True):
            pool.setdefault((c["path"], c["section"], c["sentence"], c["answer"]), c)
    probes = []
    for r in results:
        key = (r["path"], r["section"], r["sentence"], r["answer"])
        if key not in pool:
            raise ValueError(f"recorded probe not on the pages: {key}")
        probes.append(pool[key] | {"kind": r["kind"], "area": r["area"]})
    return probes


def main() -> None:
    name = sys.argv[1]
    docs = read_json(DOCS_DIR / f"{name}.json")
    if sys.argv[2:] == ["--recorded"]:
        probes = recorded(docs, read_jsonl(RESULTS_DIR / f"{name}.jsonl"))
    else:
        probes = build(docs)
    write_json(PROBES_DIR / f"{name}.json", probes, indent=None)
    print(name, len(probes), "probes", dict(collections.Counter(p["kind"] for p in probes)))


if __name__ == "__main__":
    main()
