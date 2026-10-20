"""Inputs of the analysis (ADR 0044), loaded and checked.

The analysis builds only on the result files of the latest runs: retrieval scores (step
`evaluate_retrieval`), answer scores (`summarise`) and K0 scores (`summarise_control`) must match
the input and output checksums of their run records, the generation costs come from the generate
run that wrote the answers, and the main catalogue must be frozen (ADR 0030). A pilot set may lack
the summarise records (its scores predate them, and after ADR 0043 they can no longer be
summarised again); that and every other skipped part is listed in `notes`.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

import closed_book
from atomic_csv import read_csv
from config import (
    CATALOGUE_FREEZE_FILE,
    CHUNK_FILES,
    CLOSED_BOOK_FILE,
    CONTROL_CHUNK_FILES,
    CONTROL_RETRIEVAL_SCORES_FILE,
    CONTROL_RETRIEVED_FILE,
    DOCUMENTS_FILE,
    EMBEDDING_RUNS_FILE,
    GENERATED_ANSWERS_CONTROL_FILE,
    GENERATED_ANSWERS_FILE,
    GENERATION_RUNS_FILE,
    GROUND_TRUTH_FILE,
    KEY_POINTS_FILE,
    PILOT_RUNS_FILE_NAME,
    QUESTIONS_FILE,
    RETRIEVAL_SCORES_FILE,
    RETRIEVED_RESULTS_FILE,
    SCORES_CONTROL_FILE,
    SCORES_FILE,
    SCORING_CHECKS_CONTROL_FILE,
    SCORING_CHECKS_FILE,
    SCORING_KEY_FILE,
    SCORING_SHEET_CONTROL_FILE,
    SCORING_SHEET_FILE,
    SECTIONS_FILE,
    STRATEGY_IDS,
)
from control_k0 import CONTROL_SCORES_HEADER
from evaluate_answers import SCORES_HEADER
from evaluate_retrieval import SCORES_HEADER as RETRIEVAL_HEADER
from freeze import is_main_catalogue, require_frozen
from retrieve import GROUND_TRUTH_HEADER, QUESTIONS_HEADER, QUESTIONS_REQUIRED, read_rows
from run_log import latest_run, require_run

EXPERIMENT = ",".join(STRATEGY_IDS)
VERDICT_GROUPS = {"miss": "dependent", "hit": "known"}


@dataclass(frozen=True)
class AnalysisData:
    questions: pd.DataFrame
    retrieval: pd.DataFrame
    scores: pd.DataFrame
    scores_control: pd.DataFrame | None
    verdicts: dict[str, str] | None
    chunks: dict[str, list[int]] | None
    embedding: dict[str, dict] | None
    generation: dict[str, dict]
    notes: list[str]


def main_paths() -> dict:
    return _with_inputs(
        {
            "questions_file": QUESTIONS_FILE,
            "ground_truth_file": GROUND_TRUTH_FILE,
            "sections_file": SECTIONS_FILE,
            "documents_file": DOCUMENTS_FILE,
            "freeze_file": CATALOGUE_FREEZE_FILE,
            "retrieval_file": RETRIEVAL_SCORES_FILE,
            "retrieval_control_file": CONTROL_RETRIEVAL_SCORES_FILE,
            "scores_file": SCORES_FILE,
            "scores_control_file": SCORES_CONTROL_FILE,
            "retrieval_runs_file": EMBEDDING_RUNS_FILE,
            "generation_runs_file": GENERATION_RUNS_FILE,
            "embedding_runs_file": EMBEDDING_RUNS_FILE,
            "chunk_files": {**CHUNK_FILES, **CONTROL_CHUNK_FILES},
            "closed_book_file": CLOSED_BOOK_FILE,
        },
        RETRIEVED_RESULTS_FILE.parent,
    )


def set_paths(set_dir: Path) -> dict:
    """A pilot set: its own result files and run log; chunks and embedding log are the shared
    processed corpus its retrieval used; no closed-book verdicts (main catalogue only)."""
    runs = set_dir / PILOT_RUNS_FILE_NAME
    return _with_inputs(
        main_paths()
        | {
            "questions_file": set_dir / QUESTIONS_FILE.name,
            "ground_truth_file": set_dir / GROUND_TRUTH_FILE.name,
            "retrieval_file": set_dir / RETRIEVAL_SCORES_FILE.name,
            "retrieval_control_file": set_dir / CONTROL_RETRIEVAL_SCORES_FILE.name,
            "scores_file": set_dir / SCORES_FILE.name,
            "scores_control_file": set_dir / SCORES_CONTROL_FILE.name,
            "retrieval_runs_file": runs,
            "generation_runs_file": runs,
            "closed_book_file": None,
        },
        set_dir,
    )


def _with_inputs(paths: dict, results_dir: Path) -> dict:
    """The inputs each run record hashed, so that a changed input invalidates the result file:
    evaluate_retrieval (results, catalogue, sections, chunks), summarise (sheet, key, checks, key
    points), summarise_control (sheet, checks, key points, scores.csv), generate (the answers)."""
    chunks = paths["chunk_files"]
    catalogue = [paths["questions_file"], paths["ground_truth_file"], paths["sections_file"]]
    key_points = results_dir / KEY_POINTS_FILE.name
    return paths | {
        "retrieval_inputs": {
            EXPERIMENT: [results_dir / RETRIEVED_RESULTS_FILE.name, *catalogue]
            + [chunks[k] for k in STRATEGY_IDS],
            "K1": [results_dir / CONTROL_RETRIEVED_FILE.name, *catalogue, chunks["K1"]],
        },
        "scores_inputs": [
            results_dir / f.name
            for f in (SCORING_SHEET_FILE, SCORING_KEY_FILE, SCORING_CHECKS_FILE)
        ]
        + [key_points],
        "scores_control_inputs": [
            results_dir / SCORING_SHEET_CONTROL_FILE.name,
            results_dir / SCORING_CHECKS_CONTROL_FILE.name,
            key_points,
            paths["scores_file"],
        ],
        "answers_files": [
            results_dir / GENERATED_ANSWERS_FILE.name,
            results_dir / GENERATED_ANSWERS_CONTROL_FILE.name,
        ],
    }


def _checked(
    path: Path, inputs: list[Path], runs: Path, step: str, strategy: str, main: bool, notes: list
) -> None:
    """The file must be the output of the latest `step` record, and every input that record
    hashed must be unchanged; a pilot set may lack the record. An input the step skips when it
    is absent (summarise: checks, key points) is checked only if present or recorded."""
    record = latest_run(runs, step, strategy)
    if record is None and not main:
        notes.append(f"{path.name} ohne Laufeintrag `{step}` (Pilot; Werte wie gespeichert)")
        return
    recorded = (record or {}).get("inputs_sha256", {})
    used = [p for p in inputs if p.exists() or p.name in recorded]
    require_run(runs, step, strategy, used, [path])


def _complete(frame: pd.DataFrame, qids: list[str], strategies: list[str], what: str) -> None:
    pairs = set(zip(frame["question_id"], frame["strategy"], strict=True))
    missing = [f"{q}/{s}" for q in qids for s in strategies if (q, s) not in pairs]
    if missing:
        raise ValueError(f"{what}: rows missing for {missing}")


def load(paths: dict, main: bool, frozen_check: bool = True) -> AnalysisData:
    notes: list[str] = []
    # a set that resolves to the main catalogue gets no pilot exceptions
    main = main or is_main_catalogue(paths["questions_file"], paths["ground_truth_file"])
    if frozen_check:  # passes for any catalogue but the main one
        require_frozen(
            paths["questions_file"],
            paths["ground_truth_file"],
            paths["sections_file"],
            paths["documents_file"],
            paths["freeze_file"],
        )
    questions = read_rows(
        paths["questions_file"], "question catalogue", QUESTIONS_HEADER, QUESTIONS_REQUIRED
    )
    truth = read_rows(
        paths["ground_truth_file"], "ground truth", GROUND_TRUTH_HEADER, GROUND_TRUTH_HEADER
    )
    qids = sorted(q["question_id"] for q in questions)

    runs = paths["retrieval_runs_file"]
    inputs = paths["retrieval_inputs"]
    for file, key in (
        (paths["retrieval_file"], EXPERIMENT),
        (paths["retrieval_control_file"], "K1"),
    ):
        _checked(file, inputs[key], runs, "evaluate_retrieval", key, main, notes)
    retrieval = pd.DataFrame(
        read_csv(paths["retrieval_file"], RETRIEVAL_HEADER)
        + read_csv(paths["retrieval_control_file"], RETRIEVAL_HEADER)
    )
    _complete(retrieval, qids, [*STRATEGY_IDS, "K1"], paths["retrieval_file"].name)

    gen_runs = paths["generation_runs_file"]
    _checked(
        paths["scores_file"], paths["scores_inputs"], gen_runs, "summarise", EXPERIMENT, main, notes
    )
    scores = pd.DataFrame(read_csv(paths["scores_file"], SCORES_HEADER))
    _complete(scores, qids, list(STRATEGY_IDS), paths["scores_file"].name)

    control = None
    if paths["scores_control_file"].exists():
        _checked(
            paths["scores_control_file"], paths["scores_control_inputs"], gen_runs,
            "summarise_control", "K0", main, notes,
        )  # fmt: skip
        control = pd.DataFrame(read_csv(paths["scores_control_file"], CONTROL_SCORES_HEADER))
        _complete(control, qids, ["K0"], paths["scores_control_file"].name)
    else:
        notes.append("K0 ohne Bewertung: Vergleich mit K0 entfällt")

    verdicts = None
    book = paths["closed_book_file"]
    if book is not None and book.exists():
        listed = [{"question_id": q["question_id"], "question": q["question"]} for q in questions]
        by_id = {t["question_id"]: t for t in truth}
        states = closed_book.states(closed_book.read_screen(book), listed, by_id)
        verdicts = {q: VERDICT_GROUPS.get(s, "not judged") for q, s in states.items()}
    else:
        notes.append("keine closed-book-Urteile: Aufteilung nach Urteil entfällt")

    chunk_files = paths["chunk_files"]
    if chunk_files and all(p.exists() for p in chunk_files.values()):
        chunks = {
            key: [
                c["end_token"] - c["start_token"]
                for c in map(json.loads, path.read_text(encoding="utf-8").splitlines())
            ]
            for key, path in chunk_files.items()
        }
    else:
        chunks = None
        notes.append("Chunk-Dateien fehlen: Chunk-Längen entfallen")

    embedding = None
    emb = paths["embedding_runs_file"]
    if emb.exists():
        found = {k: latest_run(emb, "embed", k) for k in [*STRATEGY_IDS, "K1"]}
        if all(found.values()):
            embedding = {
                k: {f: r[f] for f in ("input_tokens", "cost_usd", "vector_bytes", "vectors")}
                for k, r in found.items()
                if r is not None
            }
    if embedding is None:
        notes.append("Embedding-Läufe fehlen: Index- und Embedding-Kosten entfallen")

    # the costs belong to the run that wrote the scored answers
    answers = [p for p in paths["answers_files"] if p.exists()]
    generate = require_run(gen_runs, "generate", EXPERIMENT, [], answers, outputs_required=False)
    return AnalysisData(
        questions=pd.DataFrame(questions).loc[:, ["question_id", "type", "difficulty"]],
        retrieval=retrieval,
        scores=scores,
        scores_control=control,
        verdicts=verdicts,
        chunks=chunks,
        embedding=embedding,
        generation=generate["by_strategy"],
        notes=notes,
    )


def load_main() -> AnalysisData:
    return load(main_paths(), main=True)


def load_set(set_dir: Path) -> AnalysisData:
    return load(set_paths(set_dir), main=False)
