import csv
import importlib.util
import json

import pytest

from config import ROOT
from preprocess import clean_markdown, section_spans


def load_remap():
    spec = importlib.util.spec_from_file_location(
        "remap_pilot", ROOT / "scripts" / "remap_pilot.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Deliberately not the current names: the script must take them from config, not hard-code them.
DOCS_NAME, SECTIONS_NAME, TRUTH_NAME = "docs_v2.jsonl", "sections_v2.jsonl", "truth_v2.csv"


def write_corpus(folder, pages):
    """pages: (doc_id, path, markdown) -> documents and sections under the configured names."""
    folder.mkdir(parents=True, exist_ok=True)
    docs, sections = [], []
    for doc_id, path, markdown in pages:
        result = clean_markdown(markdown)
        docs.append({"doc_id": doc_id, "path": path, "title": "", "text": result.text})
        sections.extend(section_spans(doc_id, result))
    (folder / DOCS_NAME).write_text("".join(json.dumps(d) + "\n" for d in docs), encoding="utf-8")
    (folder / SECTIONS_NAME).write_text(
        "".join(json.dumps(s) + "\n" for s in sections), encoding="utf-8"
    )
    return folder


PAGE = "# Props {#props}\n\n## Declaration {#decl}\n\nUse defineProps.\n"


@pytest.fixture
def remap(tmp_path, monkeypatch):
    old = write_corpus(tmp_path / "old", [("D001", "guide/props.md", PAGE)])
    new = write_corpus(
        tmp_path / "new",
        [("D001", "api/core.md", "# Core {#core}\n\nText.\n"), ("D002", "guide/props.md", PAGE)],
    )
    module = load_remap()
    monkeypatch.setattr(module, "DOCUMENTS_FILE", new / DOCS_NAME)
    monkeypatch.setattr(module, "SECTIONS_FILE", new / SECTIONS_NAME)
    monkeypatch.setattr(module, "GROUND_TRUTH_FILE", tmp_path / "evaluation" / TRUTH_NAME)
    pilot = tmp_path / "pilot"
    pilot.mkdir()
    (pilot / TRUTH_NAME).write_text(
        "question_id,expected_answer,relevant_doc_ids,relevant_section_ids\n"
        "P01,Use defineProps.,D001,D001#decl\n",
        encoding="utf-8",
    )
    return module, old, pilot


def test_remap_maps_by_path_and_anchor_using_config_file_names(remap):
    module, old, pilot = remap
    module.main(old, [pilot])
    with (pilot / TRUTH_NAME).open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows == [
        {
            "question_id": "P01",
            "expected_answer": "Use defineProps.",
            "relevant_doc_ids": "D002",
            "relevant_section_ids": "D002#decl",
        }
    ]


def test_remap_aborts_when_a_section_vanished(remap, tmp_path, monkeypatch):
    module, old, pilot = remap
    gone = write_corpus(tmp_path / "gone", [("D001", "guide/props.md", "# Props {#props}\n")])
    monkeypatch.setattr(module, "DOCUMENTS_FILE", gone / DOCS_NAME)
    monkeypatch.setattr(module, "SECTIONS_FILE", gone / SECTIONS_NAME)
    with pytest.raises(SystemExit, match="no matching section"):
        module.main(old, [pilot])
