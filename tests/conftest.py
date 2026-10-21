import csv
import hashlib
import json
import os

import numpy as np
import pytest

import catalogue
import closed_book
import tokens
from catalogue import load_corpus
from catalogue_plan import PLAN_HEADER
from config import QUESTION_CLASSES, QUESTION_TYPES
from embedding_client import EmbeddingResult
from preprocess import clean_markdown, section_spans
from retrieve import GROUND_TRUTH_HEADER, QUESTIONS_HEADER

# ragas posts telemetry unless this is set before its first import (ADR 0047; src/ragas_client.py).
os.environ["RAGAS_DO_NOT_TRACK"] = "true"

FAKE_DIMENSIONS = 16


class FakeEmbedder:
    """Deterministic unit vectors from the text hash; records every call (no network)."""

    def __init__(self, salt: str = ""):
        self.salt = salt  # a different salt simulates a changed model behind the same name
        self.calls: list[list[str]] = []

    def __call__(self, texts: list[str]) -> EmbeddingResult:
        self.calls.append(list(texts))
        rows = []
        for text in texts:
            seed = int(hashlib.sha256((self.salt + text).encode()).hexdigest()[:8], 16)
            v = np.random.default_rng(seed).normal(size=FAKE_DIMENSIONS)
            rows.append(v / np.linalg.norm(v))
        return EmbeddingResult(np.asarray(rows, dtype=np.float32), 7 * len(texts))


@pytest.fixture
def fake_embedder():
    return FakeEmbedder()


PAGES = {
    "api/reactivity-core.md": (
        "# Reactivity API: Core {#core}\n\n## ref() {#ref}\n\n"
        "Takes an inner value and returns a reactive ref object.\n\n## computed() {#computed}\n\n"
        "Takes a getter function and returns a readonly ref.\n"
    ),
    "guide/essentials/watchers.md": (
        "# Watchers {#watchers}\n\nWatchers run side effects.\n\n## Deep Watchers {#deep}\n\n"
        "A deep watcher tracks nested props. Use the once option.\n\n### Once Watchers {#once}\n\n"
        "Set once: true to run the callback only one time.\n\n## Side Effect Cleanup {#cleanup}\n\n"
        "Register cleanup with onWatcherCleanup.\n"
    ),
    "style-guide/rules-essential.md": (
        "# Priority A Rules: Essential {#essential}\n\n"
        "## Use multi-word component names {#multi-word}\n\n"
        "User component names should always be multi-word, except for root App components.\n"
    ),
}


def build_corpus(tmp_path, pages):
    docs, sections = [], []
    for number, (path, page) in enumerate(sorted(pages.items()), start=1):
        doc_id = f"D{number:03d}"
        result = clean_markdown(page)
        spans = section_spans(doc_id, result)
        docs.append(
            {
                "doc_id": doc_id,
                "path": path,
                "title": spans[0]["title"],
                "area": path.split("/")[0],
                "text": result.text,
                "tokens": tokens.count(result.text),
            }
        )
        sections.extend(spans)
    docs_file, sections_file = tmp_path / "documents.jsonl", tmp_path / "sections.jsonl"
    docs_file.write_text("".join(json.dumps(d) + "\n" for d in docs), encoding="utf-8")
    sections_file.write_text("".join(json.dumps(s) + "\n" for s in sections), encoding="utf-8")
    return docs_file, sections_file


# Area minimums for the three-area test corpus; the configured e2e minimums (ADR 0039) need the
# real corpus and are checked in test_catalogue_plan.py and test_corpus_integration.py.
TEST_AREA_MIN = {"api": 12, "style-guide": 3}


@pytest.fixture(autouse=True)
def test_area_minimums(monkeypatch):
    monkeypatch.setattr(catalogue, "AREA_MIN_QUESTIONS", TEST_AREA_MIN)


@pytest.fixture(autouse=True)
def closed_book_file(tmp_path, monkeypatch):
    """Tests never read data/evaluation/closed_book_screen.csv; check and freeze default to this."""
    path = tmp_path / "closed_book_screen.csv"
    monkeypatch.setattr(catalogue, "CLOSED_BOOK_FILE", path)
    return path


def write_screen_for(path, rows, hits=0):
    """A screen file in which every catalogue row is screened and judged; the first `hits` hit."""
    screen_rows = [
        dict.fromkeys(closed_book.SCREEN_HEADER, "")
        | {
            "question_id": qid,
            "question_sha256": closed_book.text_sha256(text),
            "reference_sha256": closed_book.text_sha256(answer),
            "answer": "I do not know.",
            "model": "gpt-6-luna-2026-05-18",
            "core_point": "hit" if number < hits else "miss",
            "date": "2026-10-21",
        }
        for number, (qid, text, _, _, answer, _) in enumerate(rows)
    ]
    closed_book.save_screen(path, screen_rows)
    return path


@pytest.fixture
def corpus_files(tmp_path):
    return build_corpus(tmp_path, PAGES)


@pytest.fixture
def corpus(corpus_files):
    return load_corpus(*corpus_files)


def write_catalogue(tmp_path, rows):
    """rows: (question_id, question, type, difficulty, expected_answer, [section_ids])."""
    questions, truth_file = tmp_path / "questions.csv", tmp_path / "ground_truth.csv"
    with (
        questions.open("w", encoding="utf-8", newline="") as qf,
        truth_file.open("w", encoding="utf-8", newline="") as tf,
    ):
        qw, tw = csv.writer(qf, lineterminator="\n"), csv.writer(tf, lineterminator="\n")
        qw.writerow(QUESTIONS_HEADER)
        tw.writerow(GROUND_TRUTH_HEADER)
        for qid, text, qtype, cls, answer, sids in rows:
            qw.writerow([qid, text, qtype, cls, ""])
            docs = ";".join(dict.fromkeys(sid.split("#")[0] for sid in sids))
            tw.writerow([qid, answer, docs, ";".join(sids)])
    return questions, truth_file


def valid_rows():
    """A catalogue that meets every quota, floor and rule on the test corpus."""
    types = [t for t, n in QUESTION_TYPES.items() for _ in range(n)]
    classes = [c for c, n in QUESTION_CLASSES.items() for _ in range(n)]
    rows = []
    for i, (qtype, cls) in enumerate(zip(types, classes, strict=True)):
        if i < TEST_AREA_MIN["api"]:
            first = "D001#ref"
        elif i < TEST_AREA_MIN["api"] + TEST_AREA_MIN["style-guide"]:
            first = "D003#multi-word"
        else:
            first = "D002#once"
        sids = [first, "D002#cleanup"] if cls == "multi-section" else [first]
        rows.append((f"Q{i + 1:03d}", f"Question number zq{i}", qtype, cls, "Short answer.", sids))
    return rows


@pytest.fixture
def pilot(tmp_path):
    pilot_dir = tmp_path / "pilot"
    (pilot_dir / "hard").mkdir(parents=True)
    (pilot_dir / "hard" / "questions.csv").write_text(
        "question_id,question,type,difficulty,notes\n"
        "H01,How do I copy a pilot question?,factual,hard,pilot detail\n",
        encoding="utf-8",
    )
    return pilot_dir


def write_plan_for(tmp_path, rows):
    """A plan with one used slot per catalogue row (starting section = first annotated section)."""
    plan = tmp_path / "catalogue_plan.csv"
    with plan.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(PLAN_HEADER)
        for number, (qid, _, _, cls, _, sids) in enumerate(rows, start=1):
            areas = {"D001": "api", "D003": "style-guide"}
            area = areas.get(sids[0].split("#")[0], "guide")  # unknown IDs: format tests
            writer.writerow([area, number, sids[0], f"S{number:02d}", cls, "used", "", qid])
    return plan


def fresh_plan_for(rows):
    """The fresh draw that matches write_plan_for(rows): same rows, every slot still open."""
    fresh = []
    for number, (_, _, _, cls, _, sids) in enumerate(rows, start=1):
        areas = {"D001": "api", "D003": "style-guide"}
        area = areas.get(sids[0].split("#")[0], "guide")
        fresh.append(
            {
                "area": area,
                "draw": str(number),
                "section_id": sids[0],
                "slot_id": f"S{number:02d}",
                "class": cls,
                "status": "open",
                "skip_reason": "",
                "question_id": "",
            }
        )
    return fresh


SCORING_CODES = ["H01-B", "H01-A", "H01-C", "H02-A", "H02-C", "H02-B"]  # packet order


def write_scoring_set(folder, codes=tuple(SCORING_CODES)):
    """A scaffolded scoring set as evaluate_answers.py writes it: blind items and an empty sheet."""
    from atomic_csv import write_csv
    from config import RUBRIC_CRITERIA
    from evaluate_answers import SHEET_HEADER

    folder.mkdir(parents=True, exist_ok=True)
    items = [
        {
            "code": code,
            "question_id": code.split("-")[0],
            "question": f"Question {code.split('-')[0]}?",
            "reference_answer": "Use `ref()`.",
            "answer": f"Answer {code}.",
            "excerpts": [f"Excerpt one for {code}.", "Excerpt two."],
        }
        for code in codes
    ]
    (folder / "scoring_items.jsonl").write_text(
        "".join(json.dumps(i) + "\n" for i in items), encoding="utf-8"
    )
    rows = [
        {"code": c, "question_id": c.split("-")[0]} | dict.fromkeys([*RUBRIC_CRITERIA, "notes"], "")
        for c in codes
    ]
    write_csv(folder / "scoring_sheet.csv", SHEET_HEADER, rows)
    log_scaffold(folder / "scoring_items.jsonl")


def write_control_set(folder, qids=("H01", "H02")):
    """A K0 set next to a scaffolded C1-C3 set, as control_k0.scaffold_control writes it."""
    from atomic_csv import write_csv
    from config import CONTROL_CRITERIA
    from control_k0 import CONTROL_SHEET_HEADER

    items = [
        {
            "code": f"{q}-K0",
            "question_id": q,
            "question": f"Question {q}?",
            "reference_answer": "Use `ref()`.",
            "answer": f"Closed-book {q}.",
            "excerpts": [],
        }
        for q in qids
    ]
    (folder / "scoring_items_control.jsonl").write_text(
        "".join(json.dumps(i) + "\n" for i in items), encoding="utf-8"
    )
    rows = [
        {"code": i["code"], "question_id": i["question_id"]}
        | dict.fromkeys([*CONTROL_CRITERIA, "notes"], "")
        for i in items
    ]
    write_csv(folder / "scoring_sheet_control.csv", CONTROL_SHEET_HEADER, rows)


def log_scaffold(items_file):
    """The scaffold record evaluate_answers.py writes into a pilot set's runs.jsonl."""
    import hashlib

    from config import STRATEGY_IDS

    record = {
        "step": "scaffold",
        "strategy": ",".join(STRATEGY_IDS),
        "outputs_sha256": {items_file.name: hashlib.sha256(items_file.read_bytes()).hexdigest()},
    }
    with (items_file.parent / "runs.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
