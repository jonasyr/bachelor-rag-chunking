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
    CATALOGUE_SKIP_REASONS,
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


def slot_row(rows: list[dict], slot_id: str) -> dict:
    """The current (open or used) row of a slot."""
    for row in rows:
        if row["slot_id"] == slot_id and row["status"] in ("open", "used"):
            return row
    raise ValueError(f"no slot {slot_id} in the plan")


def mark_used(rows: list[dict], slot_id: str, question_id: str) -> None:
    row = slot_row(rows, slot_id)
    if row["status"] == "used" and row["question_id"] != question_id:
        raise ValueError(f"slot {slot_id} already holds {row['question_id']}")
    row["status"], row["question_id"] = "used", question_id


def skip_slot(plan_file: Path, slot_id: str, reason: str) -> dict:
    """Skip an open slot's section with a listed reason; the area's next reserve row takes over."""
    if reason not in CATALOGUE_SKIP_REASONS:
        raise ValueError(
            f"skip reason {reason!r} not allowed; use one of {list(CATALOGUE_SKIP_REASONS)}"
        )
    rows = read_plan(plan_file)
    row = slot_row(rows, slot_id)
    if row["status"] != "open":
        raise ValueError(f"slot {slot_id} is not open (it holds {row['question_id']})")
    spare = [r for r in rows if r["area"] == row["area"] and r["status"] == "reserve"]
    if not spare:
        raise ValueError(
            f"no reserve section left in area {row['area']}; "
            "a larger reserve needs a new ADR (ADR 0031)"
        )
    new = min(spare, key=lambda r: int(r["draw"]))
    new["slot_id"], new["class"], new["status"] = row["slot_id"], row["class"], "open"
    row["status"], row["skip_reason"] = "skipped", reason
    save_plan(plan_file, rows)
    return new


def plan_findings(
    rows: list[dict],
    questions: list[dict],
    relevant: dict[str, list[dict]],
    section_ids: set[str],
) -> tuple[list[str], list[str]]:
    """Errors (plan format) and findings (slot rules) of ADR 0031."""
    errors = [
        f"plan row {r['area']}/{r['draw']}: section {r['section_id']} is not in sections.jsonl"
        for r in rows
        if r["section_id"] not in section_ids
    ]
    errors += [
        f"slot {r['slot_id']}: skip reason {r['skip_reason']!r} not allowed"
        for r in rows
        if r["status"] == "skipped" and r["skip_reason"] not in CATALOGUE_SKIP_REASONS
    ]
    findings = []
    used = [r for r in rows if r["status"] == "used"]
    known = {q["question_id"] for q in questions}
    findings += [
        f"slot {r['slot_id']}: question {r['question_id']} is not in the catalogue"
        for r in used
        if r["question_id"] not in known
    ]
    for q in questions:
        qid = q["question_id"]
        own = [r for r in used if r["question_id"] == qid]
        if len(own) != 1:
            findings.append(f"{qid}: belongs to {len(own)} slots, needs exactly 1")
            continue
        row = own[0]
        if q["difficulty"] != row["class"]:
            findings.append(
                f"{qid}: difficulty {q['difficulty']} but slot {row['slot_id']} is {row['class']}"
            )
        if row["section_id"] not in {s["section_id"] for s in relevant.get(qid, [])}:
            start, slot = row["section_id"], row["slot_id"]
            findings.append(f"{qid}: starting section {start} of slot {slot} is not annotated")
    return errors, findings


def plan_summary(rows: list[dict]) -> list[str]:
    status = {s: sum(1 for r in rows if r["status"] == s) for s in ("used", "open", "skipped")}
    reasons = {}
    for r in rows:
        if r["status"] == "skipped":
            reasons[r["skip_reason"]] = reasons.get(r["skip_reason"], 0) + 1
    detail = ", ".join(f"{k} {v}" for k, v in sorted(reasons.items()))
    line = f"Slots: {status['used']} used, {status['open']} open, {status['skipped']} skipped"
    return [line + (f" ({detail})" if detail else "")]
