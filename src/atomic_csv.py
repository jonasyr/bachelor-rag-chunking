"""Strict reading and atomic writing of the hand-written catalogue files (ADR 0030, 0031).

A row with too many or too few fields is an error, never silently filled or dropped. A write goes
to a temporary file in the same directory and replaces the old file in one step, so a failure
can never leave a truncated ground truth behind.
"""

import csv
import os
import tempfile
from pathlib import Path


def read_csv(path: Path, header: list[str]) -> list[dict]:
    """Rows of a CSV with exactly `header`; a missing or empty file has no rows."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        records = [r for r in csv.reader(f) if r]
    if not records:
        return []
    if records[0] != header:
        raise ValueError(f"{path} has columns {records[0]}, expected {header}")
    for number, record in enumerate(records[1:], start=2):
        if len(record) != len(header):
            raise ValueError(
                f"{path}: row {number} has {len(record)} fields, expected {len(header)}"
            )
    return [dict(zip(header, r, strict=True)) for r in records[1:]]


def write_csv(path: Path, header: list[str], rows: list[dict]) -> None:
    """Write all rows atomically: temporary file in the same directory, then os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
