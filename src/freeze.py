"""Freeze record of the question catalogue (ADR 0030).

`write_freeze` records the SHA-256 of questions.csv and ground_truth.csv after the strict
coverage check passed (src/catalogue.py freeze). `require_frozen` lets retrieval use the main
catalogue only while both files still match that record, so the ground truth is final before
any retrieval (ADR 0017, 0027). Other catalogues (pilot sets, tests) are not affected.
"""

import json
from datetime import date
from pathlib import Path

from config import CATALOGUE_FREEZE_FILE, GROUND_TRUTH_FILE, QUESTIONS_FILE
from run_log import sha256_of


def write_freeze(
    questions_file: Path,
    ground_truth_file: Path,
    freeze_file: Path = CATALOGUE_FREEZE_FILE,
    summary: dict | None = None,
) -> dict:
    """Write the record once; an existing record is never overwritten."""
    if freeze_file.exists():
        raise FileExistsError(
            f"{freeze_file} exists: the catalogue is frozen. A new freeze needs a new ADR and "
            "deleting the record by hand (ADR 0030)"
        )
    record = {
        "date": date.today().isoformat(),
        **(summary or {}),
        "sha256": {
            questions_file.name: sha256_of(questions_file),
            ground_truth_file.name: sha256_of(ground_truth_file),
        },
    }
    freeze_file.parent.mkdir(parents=True, exist_ok=True)
    freeze_file.write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return record


def is_main_catalogue(questions_file: Path, ground_truth_file: Path) -> bool:
    """True if either file is the main catalogue (config.QUESTIONS_FILE, GROUND_TRUTH_FILE)."""
    main = {QUESTIONS_FILE.resolve(), GROUND_TRUTH_FILE.resolve()}
    return bool({questions_file.resolve(), ground_truth_file.resolve()} & main)


def require_frozen(
    questions_file: Path, ground_truth_file: Path, freeze_file: Path = CATALOGUE_FREEZE_FILE
) -> None:
    """Raise unless the main catalogue is frozen and unchanged; other catalogues pass."""
    if not is_main_catalogue(questions_file, ground_truth_file):
        return
    if not freeze_file.exists():
        raise RuntimeError(
            "the question catalogue is not frozen; run `uv run python src/catalogue.py freeze` "
            "first (ADR 0030)"
        )
    record = json.loads(freeze_file.read_text(encoding="utf-8"))
    for path in (questions_file, ground_truth_file):
        if record["sha256"].get(path.name) != sha256_of(path):
            raise RuntimeError(
                f"{path.name} changed since the freeze on {record['date']} (ADR 0030)"
            )
