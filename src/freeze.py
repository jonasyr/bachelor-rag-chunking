"""Freeze record of the question catalogue (ADR 0030).

`write_freeze` records the SHA-256 of questions.csv, ground_truth.csv, sections.jsonl and
documents.jsonl after the strict coverage check passed (src/catalogue.py freeze); the two
corpus files pin which text the annotated section IDs refer to. `require_frozen` lets
retrieval use the main catalogue only while all four files still match that record, so the
ground truth is final before any retrieval (ADR 0017, 0027). The record also keeps the version
of the scoring rules; `require_rules_version` refuses scoring of the main run under other rules
(ADR 0035, 0043). Other catalogues (pilot sets, tests) are not affected.
"""

import json
from datetime import date
from pathlib import Path

from config import (
    CATALOGUE_FREEZE_FILE,
    GROUND_TRUTH_FILE,
    QUESTIONS_FILE,
    RUBRIC_RULES_VERSION,
)
from run_log import sha256_of


def write_freeze(
    questions_file: Path,
    ground_truth_file: Path,
    sections_file: Path,
    documents_file: Path,
    freeze_file: Path = CATALOGUE_FREEZE_FILE,
    summary: dict | None = None,
    recorded: tuple[Path, ...] = (),
) -> dict:
    """Write the record once; an existing record is never overwritten (exclusive create).

    Further files (`recorded`) are hashed for the record only; `require_frozen` checks the four
    retrieval inputs.
    """
    record = {
        "date": date.today().isoformat(),
        "rules_version": RUBRIC_RULES_VERSION,
        **(summary or {}),
        "sha256": {
            f.name: sha256_of(f)
            for f in (questions_file, ground_truth_file, sections_file, documents_file, *recorded)
        },
    }
    freeze_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with freeze_file.open("x", encoding="utf-8") as f:
            f.write(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    except FileExistsError:
        raise FileExistsError(
            f"{freeze_file} exists: the catalogue is frozen. A new freeze needs a new ADR and "
            "deleting the record by hand (ADR 0030)"
        ) from None
    return record


def is_main_catalogue(questions_file: Path, ground_truth_file: Path) -> bool:
    """True if either file is the main catalogue (config.QUESTIONS_FILE, GROUND_TRUTH_FILE)."""
    main = {QUESTIONS_FILE.resolve(), GROUND_TRUTH_FILE.resolve()}
    return bool({questions_file.resolve(), ground_truth_file.resolve()} & main)


def require_frozen(
    questions_file: Path,
    ground_truth_file: Path,
    sections_file: Path,
    documents_file: Path,
    freeze_file: Path = CATALOGUE_FREEZE_FILE,
) -> None:
    """Raise unless the main catalogue is frozen and unchanged; other catalogues pass."""
    if not is_main_catalogue(questions_file, ground_truth_file):
        return
    if not freeze_file.exists():
        raise RuntimeError(
            "the question catalogue is not frozen; run `uv run python src/catalogue.py freeze` "
            "first (ADR 0030)"
        )
    try:
        record = json.loads(freeze_file.read_text(encoding="utf-8"))
        frozen, when = record["sha256"], record["date"]
        if not isinstance(frozen, dict):
            raise TypeError("sha256 must map file names to hashes")
    except (ValueError, KeyError, TypeError) as error:
        raise RuntimeError(f"malformed freeze record {freeze_file} (ADR 0030): {error}") from None
    for path in (questions_file, ground_truth_file, sections_file, documents_file):
        if frozen.get(path.name) != sha256_of(path):
            raise RuntimeError(f"{path.name} changed since the freeze on {when} (ADR 0030)")


def require_rules_version(freeze_file: Path = CATALOGUE_FREEZE_FILE) -> None:
    """Raise unless the freeze record holds the current scoring rules version."""
    record = json.loads(freeze_file.read_text(encoding="utf-8"))
    frozen = record.get("rules_version")
    if frozen is None:
        raise RuntimeError(f"freeze record {freeze_file} has no rules_version (ADR 0035)")
    if frozen != RUBRIC_RULES_VERSION:
        raise RuntimeError(
            f"the scoring rules changed since the freeze ({frozen}, now {RUBRIC_RULES_VERSION}); "
            "the main run is scored under the frozen rules (ADR 0035, 0043)"
        )
