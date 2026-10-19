"""One-off: remap the pilot ground truth from the old corpus IDs to the new ones (ADR 0025).

Documents are matched by path, sections by anchor; title and level must agree. Prints every
annotated section and marks those whose cleaned text changed between the corpora, so they can be
checked by hand. Aborts if a document or section no longer exists.

Usage: uv run python scripts/remap_pilot.py OLD_DIR PILOT_DIR [PILOT_DIR ...]
OLD_DIR holds the documents and sections files of the old corpus (names as in src/config.py).
One-shot: the ground truth is rewritten in place, so a second run aborts on the new IDs.
Historical (Vue.js corpus, ADR 0025): the new corpus is read from data/processed/, which now holds
the e2e corpus (ADR 0038), so the script no longer applies to the Vue pilot sets.
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import tokens  # noqa: E402
from config import DOCUMENTS_FILE, GROUND_TRUTH_FILE, ID_SEPARATOR, SECTIONS_FILE  # noqa: E402
from retrieve import GROUND_TRUTH_HEADER, split_ids  # noqa: E402


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def section_text(doc: dict, section: dict) -> str:
    starts = tokens.token_starts(doc["text"])

    def char(t: int) -> int:
        return starts[t] if t < len(starts) else len(doc["text"])

    return doc["text"][char(section["start_token"]) : char(section["end_token"])]


def main(old_dir: Path, pilots: list[Path]) -> None:
    old_docs = {d["doc_id"]: d for d in load(old_dir / DOCUMENTS_FILE.name)}
    old_secs = {s["section_id"]: s for s in load(old_dir / SECTIONS_FILE.name)}
    new_docs = {d["path"]: d for d in load(DOCUMENTS_FILE)}
    new_secs = {s["section_id"]: s for s in load(SECTIONS_FILE)}
    for pilot in pilots:
        path = pilot / GROUND_TRUTH_FILE.name
        with path.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            mapped = []
            for sid in split_ids(row["relevant_section_ids"]):
                old = old_secs[sid]
                old_doc = old_docs[old["doc_id"]]
                if old_doc["path"] not in new_docs:
                    raise SystemExit(f"{sid}: {old_doc['path']} is not in the new corpus")
                new_doc = new_docs[old_doc["path"]]
                new_sid = f"{new_doc['doc_id']}#{old['anchor']}"
                new = new_secs.get(new_sid)
                if new is None or (new["title"], new["level"]) != (old["title"], old["level"]):
                    raise SystemExit(f"{sid}: no matching section {new_sid} in {old_doc['path']}")
                same = section_text(old_doc, old) == section_text(new_doc, new)
                flag = "" if same else "  TEXT CHANGED: check by hand"
                print(f"{pilot.name}/{row['question_id']}: {sid} -> {new_sid}{flag}")
                mapped.append(new_sid)
            row["relevant_section_ids"] = ID_SEPARATOR.join(mapped)
            docs = dict.fromkeys(s.split("#")[0] for s in mapped)
            row["relevant_doc_ids"] = ID_SEPARATOR.join(docs)
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=GROUND_TRUTH_HEADER, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main(Path(sys.argv[1]), [Path(p) for p in sys.argv[2:]])
