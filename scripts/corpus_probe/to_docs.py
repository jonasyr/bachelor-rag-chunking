"""Pages of a candidate's docs folder as one JSON list (ADR 0038).

Keeps .md/.mdx files, drops translations, changelogs (unless the candidate's skip_changelogs is
"no") and the candidate's drops (prefixes relative to the docs folder) from candidates.csv,
takes the title from the frontmatter (else the file name) and removes MDX import/export lines.
With a documents.jsonl as SOURCE (the Vue snapshot after preprocessing) its pages are taken as
they are. The Vue row's SOURCE, data/processed/documents.jsonl, now holds the e2e corpus (ADR
0038): rebuild the Vue corpus first (vuejs/docs at 40aa88a, with the code of commit 4115ffc).
Tokens = characters / 4 (not the tiktoken count of the pipeline). Also records the page
statistics in stats.json.

Usage: uv run python scripts/corpus_probe/to_docs.py NAME SOURCE
"""

import json
import pathlib
import re
import sys

from common import DOCS_DIR, STATS_FILE, candidates, read_json, write_json

TRANSLATIONS = re.compile(r"/(hi|ja|de|pt|zh|zh-cn|zh-CN|fr|es|ko|ru)/|\.(zh|ko|ja)\.mdx?$")
CHANGELOGS = re.compile(r"(^|/)(CHANGELOG|changelog)")
REFERENCE = re.compile(
    r"(^|/)(reference|references|api|api-reference|api_reference|cli|configuration|config|spec"
    r"|specs|options|policy|policies)(/|\.|-|_|$)",
    re.I,
)


def pages(root: pathlib.Path, drops: list[str], skip_changelogs: bool = True) -> list[dict]:
    files = sorted(
        p
        for p in root.rglob("*.md*")
        if p.suffix in (".md", ".mdx")
        and not TRANSLATIONS.search("/" + str(p.relative_to(root)))
        and not (skip_changelogs and CHANGELOGS.search("/" + str(p.relative_to(root))))
        and not any(str(p.relative_to(root)).startswith(d) for d in drops)
    )
    docs = []
    for i, f in enumerate(files):
        text = f.read_text(encoding="utf-8", errors="replace")
        title = f.stem
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if m:
            tm = re.search(r"^title:\s*['\"]?(.+?)['\"]?\s*$", m.group(1), re.M)
            title = tm.group(1) if tm else title
            text = text[m.end() :]
        text = re.sub(r"^(import|export) .*$", "", text, flags=re.M)
        docs.append(
            {
                "doc_id": f"D{i + 1:03d}",
                "path": str(f.relative_to(root)),
                "title": title,
                "text": text,
            }
        )
    return docs


def stats(docs: list[dict]) -> dict:
    """Page statistics for the score (approximate tokens = characters / 4)."""
    tokens = [len(d["text"]) // 4 for d in docs]
    total = sum(tokens) or 1
    jumps = 0  # heading level jumps (h2 -> h4) as a hierarchy defect
    for d in docs:
        levels = [len(m) for m in re.findall(r"^(#{1,6}) ", d["text"], re.M)]
        jumps += sum(1 for a, b in zip(levels, levels[1:], strict=False) if b - a > 1)
    return {
        "docs": len(docs),
        "tokens": sum(tokens),
        "page_tokens": tokens,
        "headings_h2_h4": [len(re.findall(r"^#{2,4} ", d["text"], re.M)) for d in docs],
        "jsx_lines": sum(len(re.findall(r"^\s*<[A-Z][A-Za-z]*", d["text"], re.M)) for d in docs),
        "code_blocks": sum(len(re.findall(r"^\s*(```|~~~)", d["text"], re.M)) // 2 for d in docs),
        "frontmatter_titles": sum(d["title"] != pathlib.Path(d["path"]).stem for d in docs)
        / len(docs),
        "heading_jumps": jumps,
        "reference_share": sum(
            t for d, t in zip(docs, tokens, strict=True) if REFERENCE.search(d["path"])
        )
        / total,
    }


def main() -> None:
    name, source = sys.argv[1], pathlib.Path(sys.argv[2])
    row = candidates()[name]
    drops = [d for d in row["drops"].split(",") if d]
    if source.suffix == ".jsonl":
        docs = [
            json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line
        ]
    else:
        docs = pages(source, drops, row["skip_changelogs"] == "yes")
    write_json(DOCS_DIR / f"{name}.json", docs, indent=None)
    all_stats = read_json(STATS_FILE) if STATS_FILE.exists() else {}
    all_stats[name] = stats(docs)
    write_json(STATS_FILE, dict(sorted(all_stats.items())))
    print(name, len(docs), "pages,", all_stats[name]["tokens"], "approx. tokens")


if __name__ == "__main__":
    main()
