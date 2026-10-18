"""Shared paths and helpers of the corpus selection probe (ADR 0038).

Layout under config.CORPUS_PROBE_DIR: candidates.csv (sources and screening facts), stats.json
(page statistics per corpus), results/<name>.jsonl (probe answers), misses/<name>.json (the
classified misses), summary.json (gap rates, scores, sensitivity). docs/ and probes/ hold the
rebuilt intermediate files and are not versioned (they quote whole pages).
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from config import CORPUS_PROBE_DIR  # noqa: E402

CANDIDATES_FILE = CORPUS_PROBE_DIR / "candidates.csv"
STATS_FILE = CORPUS_PROBE_DIR / "stats.json"
SUMMARY_FILE = CORPUS_PROBE_DIR / "summary.json"
DOCS_DIR = CORPUS_PROBE_DIR / "docs"
PROBES_DIR = CORPUS_PROBE_DIR / "probes"
RESULTS_DIR = CORPUS_PROBE_DIR / "results"
MISSES_DIR = CORPUS_PROBE_DIR / "misses"
CATEGORIES = ("fact", "example_name", "equivalent", "ambiguous")


def candidates() -> dict[str, dict]:
    with CANDIDATES_FILE.open(encoding="utf-8", newline="") as f:
        return {row["name"]: row for row in csv.DictReader(f)}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data, indent: int | None = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
