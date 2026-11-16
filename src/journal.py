"""Append-only journal of a one-shot API step (ADR 0050).

Generation and RAGAS call the API once per item and must not be repeated (ADR 0033, 0047). The
journal keeps every API result the moment it arrives, so a run that stops (network, a killed
process, an empty battery) loses nothing that was paid for, and a restart continues from it
instead of drawing a second sample.

The first line is the `start` entry: the step, its pinned settings and the checksums of its
inputs. A restart continues only when these are unchanged; otherwise it refuses, and the journal
must be moved aside deliberately. Each run of the step appends a `session` entry with its code and
environment, so a run continued after a commit shows every commit it ran on; a stop appends
an `abort` entry with the error before the error propagates. Every line is flushed and synced to
disk before the step goes on.
"""

import json
import os
from datetime import UTC, datetime
from pathlib import Path


class Journal:
    def __init__(self, path: Path, start: dict, session: dict | None = None) -> None:
        """Open the journal at `path` for a step described by `start` (JSON values only);
        `session` (e.g. the commit and environment of this call) goes into the session entry."""
        self.path = path
        self.start = json.loads(json.dumps(start))  # normalised as it is stored
        self.entries: list[dict] = []
        if path.exists():
            lines = path.read_text(encoding="utf-8").splitlines()
            entries = []
            for n, line in enumerate(lines, start=1):
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    if n == len(lines):  # torn last line of a killed write: the item is redone
                        break
                    raise ValueError(f"{path}: line {n} is not JSON") from None
            if not entries or entries[0].get("kind") != "start":
                raise ValueError(f"{path} does not begin with a start entry")
            stored = {k: v for k, v in entries[0].items() if k not in ("kind", "time")}
            if stored != self.start:
                changed = sorted(
                    k
                    for k in stored.keys() | self.start.keys()
                    if stored.get(k) != self.start.get(k)
                )
                raise RuntimeError(
                    f"{path} belongs to a run with other settings or inputs (differs in "
                    f"{', '.join(changed)}); it holds paid API results, so it is never discarded "
                    "automatically: move it aside deliberately to start a new run (ADR 0050)"
                )
            self.entries = entries[1:]
            if len(entries) < len(lines):  # drop the torn line so the file stays valid JSONL
                self._rewrite([entries[0], *self.entries])
        else:
            self._write({"kind": "start", "time": _now(), **self.start})
        resumed = [e for e in self.entries if e.get("kind") not in ("session", "abort")]
        self.append({"kind": "session", "resumed_entries": len(resumed), **(session or {})})

    def of(self, kind: str) -> list[dict]:
        return [e for e in self.entries if e.get("kind") == kind]

    def append(self, entry: dict) -> None:
        entry = {**entry, "time": _now()}
        self._write(entry)
        self.entries.append(entry)

    def abort(self, error: BaseException, **extra) -> None:
        self.append({"kind": "abort", "error": f"{type(error).__name__}: {error}", **extra})

    def _write(self, entry: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def _rewrite(self, entries: list[dict]) -> None:
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(
            "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries), encoding="utf-8"
        )
        os.replace(tmp, self.path)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
