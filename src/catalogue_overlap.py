"""Sections with the same content as a plan section, prepared once by Claude (ADR 0049).

Directed: a row lists `related_section_id` for `section_id` only. The editor shows the rows next
to the section; Jonas alone decides what is relevant. The list depends on the section, never on a
question, and is found by reading the corpus, never through chunks or retrieval (ADR 0027).
"""

from pathlib import Path

from atomic_csv import read_csv

OVERLAP_HEADER = ["section_id", "related_section_id", "note"]


def read_overlap(path: Path) -> dict[str, list[tuple[str, str]]]:
    """Related sections and their note by section; a missing file has none."""
    related: dict[str, list[tuple[str, str]]] = {}
    for number, row in enumerate(read_csv(path, OVERLAP_HEADER), start=2):
        sid, other, note = row["section_id"], row["related_section_id"], row["note"].strip()
        if sid == other:
            raise ValueError(f"{path}: row {number} relates {sid} to itself")
        if not note:
            raise ValueError(f"{path}: row {number} has no note")
        if any(o == other for o, _ in related.get(sid, [])):
            raise ValueError(f"{path}: row {number} lists {sid} → {other} twice")
        related.setdefault(sid, []).append((other, note))
    return related


def overlap_section_ids(related: dict[str, list[tuple[str, str]]]) -> set[str]:
    """Every section ID the list names, in either column."""
    return set(related) | {other for rows in related.values() for other, _ in rows}
