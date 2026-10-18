"""Ingest the e2e snapshot (ADR 0038).

Reads every page (*.mdx) of data/raw/e2e_docs_snapshot/ sorted by path, assigns D001, D002, ... in
that order and writes data/processed/documents.jsonl with the raw text. The title comes from the
frontmatter, the area from the navigation (config.CORPUS_NAV_FILE), whose groups must equal
config.CORPUS_AREAS and whose pages must equal the snapshot's pages.

Output schema: {"doc_id", "path", "title", "area", "text", "tokens"}
"""

import json
from pathlib import Path

import tokens
from config import CORPUS_AREAS, CORPUS_NAV_FILE, CORPUS_PAGE_SUFFIX, DATA_RAW, DOCUMENTS_FILE
from mdx import nav_areas, parse_frontmatter


def ingest(
    snapshot_dir: Path = DATA_RAW,
    out_file: Path = DOCUMENTS_FILE,
    suffix: str = CORPUS_PAGE_SUFFIX,
    nav_file: str = CORPUS_NAV_FILE,
    areas: tuple[str, ...] = CORPUS_AREAS,
) -> int:
    """Load the pages, take title and area, count tokens, write documents.jsonl; return count."""
    nav_path = snapshot_dir / nav_file
    if not nav_path.is_file():
        raise FileNotFoundError(f"{nav_path} not found; run src/snapshot.py first")
    page_areas = nav_areas(json.loads(nav_path.read_text(encoding="utf-8")))
    found_areas = tuple(dict.fromkeys(page_areas.values()))
    if found_areas != tuple(areas):
        raise ValueError(f"navigation areas {list(found_areas)} differ from config.CORPUS_AREAS")
    files = sorted(
        snapshot_dir.rglob(f"*{suffix}"), key=lambda p: p.relative_to(snapshot_dir).as_posix()
    )
    pages = {p.relative_to(snapshot_dir).as_posix().removesuffix(suffix) for p in files}
    for page in pages:
        if page not in page_areas:
            raise ValueError(f"{page}{suffix}: not in the navigation")
    missing = sorted(set(page_areas) - pages)
    if missing:
        raise ValueError(f"navigation pages without a file: {missing}")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        for i, path in enumerate(files, start=1):
            rel = path.relative_to(snapshot_dir).as_posix()
            text = path.read_text(encoding="utf-8-sig")
            try:
                meta, _ = parse_frontmatter(text)
            except ValueError as e:
                raise ValueError(f"{rel}: {e}") from e
            if not meta.get("title"):
                raise ValueError(f"{rel}: no title in the frontmatter")
            record = {
                "doc_id": f"D{i:03d}",
                "path": rel,
                "title": meta["title"],
                "area": page_areas[rel.removesuffix(suffix)],
                "text": text,
                "tokens": tokens.count(text),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return len(files)


if __name__ == "__main__":
    print(f"{ingest()} documents -> {DOCUMENTS_FILE}")
