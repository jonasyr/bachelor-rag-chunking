"""Random sampling plan of the question catalogue (ADR 0031).

One starting section per slot, drawn by text length: a token position of an area is chosen with
SHA-256 of "{seed}:{area}:{k}" and the innermost H2/H3 section containing it is drawn (no repeats).
Each slot also gets a construction class; Jonas writes the question, chooses its type and
annotates it. Unsuitable sections are skipped only with a fixed reason; the next reserve section
of the same area takes the slot. The plan file is written once and versioned.
"""

from __future__ import annotations

import csv
import hashlib
from bisect import bisect_right
from pathlib import Path
from typing import TYPE_CHECKING

from config import (
    CATALOGUE_AREA_SLOTS,
    CATALOGUE_PLAN_FILE,
    CATALOGUE_PLAN_STATUSES,
    CATALOGUE_RESERVE,
    CATALOGUE_SEED,
    QUESTION_CLASSES,
)

if TYPE_CHECKING:
    from catalogue import Corpus

PLAN_HEADER = [
    "area",
    "draw",
    "section_id",
    "slot_id",
    "class",
    "status",
    "skip_reason",
    "question_id",
]


def _hash_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)


def candidates(corpus: Corpus) -> dict[str, list[dict]]:
    """Innermost sections of level 2 or 3 per area, in sections.jsonl order."""
    result: dict[str, list[dict]] = {area: [] for area in CATALOGUE_AREA_SLOTS}
    for s in corpus.sections:
        if s["level"] < 2:
            continue
        inner = any(
            c is not s
            and c["doc_id"] == s["doc_id"]
            and c["level"] > s["level"]
            and s["start_token"] <= c["start_token"]
            and c["end_token"] <= s["end_token"]
            for c in corpus.sections
        )
        area = corpus.area(s)
        if not inner and area in result:
            result[area].append(s)
    return result


def draw_area(seed: int, area: str, sections: list[dict], count: int) -> list[dict]:
    """`count` distinct sections, each drawn by a hashed token position over the area's text."""
    usable = [s for s in sections if s["end_token"] > s["start_token"]]
    if count > len(usable):
        raise ValueError(f"area {area} has only {len(usable)} candidate sections, {count} needed")
    starts, total = [], 0
    for s in usable:
        starts.append(total)
        total += s["end_token"] - s["start_token"]
    drawn: list[dict] = []
    seen: set[str] = set()
    k = 0
    while len(drawn) < count:
        position = _hash_int(f"{seed}:{area}:{k}") % total
        k += 1
        section = usable[bisect_right(starts, position) - 1]
        if section["section_id"] not in seen:
            seen.add(section["section_id"])
            drawn.append(section)
    return drawn


def draw_plan(
    corpus: Corpus,
    seed: int = CATALOGUE_SEED,
    slots: dict[str, int] = CATALOGUE_AREA_SLOTS,
    reserve: dict[str, int] = CATALOGUE_RESERVE,
    classes: dict[str, int] = QUESTION_CLASSES,
) -> list[dict]:
    """Plan rows: per area its slots, then its reserve, in draw order (ADR 0031)."""
    values = [c for c, n in classes.items() for _ in range(n)]
    if sum(slots.values()) != len(values):
        raise ValueError(
            f"slots must sum to {len(values)} (the class quotas), not {sum(slots.values())}"
        )
    order = sorted(range(len(values)), key=lambda i: _hash_int(f"{seed}:class:{i}"))
    shuffled = [values[i] for i in order]
    pools = candidates(corpus)
    rows: list[dict] = []
    slot = 0
    for area, count in slots.items():
        for number, section in enumerate(
            draw_area(seed, area, pools[area], count + reserve[area]), start=1
        ):
            is_slot = number <= count
            slot += is_slot
            rows.append(
                {
                    "area": area,
                    "draw": str(number),
                    "section_id": section["section_id"],
                    "slot_id": f"S{slot:02d}" if is_slot else "",
                    "class": shuffled[slot - 1] if is_slot else "",
                    "status": "open" if is_slot else "reserve",
                    "skip_reason": "",
                    "question_id": "",
                }
            )
    return rows


def read_plan(path: Path = CATALOGUE_PLAN_FILE) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found; run `uv run python src/catalogue.py plan` first (ADR 0031)"
        )
    with path.open(encoding="utf-8", newline="") as f:
        records = [r for r in csv.reader(f) if r]
    if not records or records[0] != PLAN_HEADER:
        found = records[0] if records else []
        raise ValueError(f"{path} has columns {found}, expected {PLAN_HEADER}")
    rows = []
    for number, record in enumerate(records[1:], start=2):
        if len(record) != len(PLAN_HEADER):
            raise ValueError(f"{path}: row {number} has {len(record)} fields")
        row = dict(zip(PLAN_HEADER, record, strict=True))
        if row["status"] not in CATALOGUE_PLAN_STATUSES:
            raise ValueError(f"{path}: row {number} has unknown status {row['status']!r}")
        rows.append(row)
    return rows


def save_plan(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PLAN_HEADER, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_plan(corpus: Corpus, plan_file: Path = CATALOGUE_PLAN_FILE, **draw_args) -> int:
    """Draw and write the plan once; an existing plan is never overwritten (ADR 0031)."""
    rows = draw_plan(corpus, **draw_args)
    if plan_file.exists():
        raise FileExistsError(
            f"{plan_file} exists: the sampling plan is fixed. A new draw needs a new ADR (ADR 0031)"
        )
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    save_plan(plan_file, rows)
    return len(rows)
