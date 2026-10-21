"""RAGAS scoring of the answers C1-C3 (ADR 0047), a second, automatic view next to the rule-based
scores (ADR 0007). RAGAS is never the basis of a statement about the strategies and never feeds
back into questions, references, relevance judgements or scores (ADR 0017).

One sample per question and experiment strategy: the question, the stored answer, the chunk texts
of the answer row's `sources` in that order (exactly what the answer model saw) and the frozen
reference. The scorer is injected (src/ragas_client.py builds the real one), so the step is
tested without the API. Everything is checked before the first call: the main catalogue must be
frozen, `generated_answers.csv` must be the output of the latest `generate` run and, on the main
catalogue, a current `summarise` record must exist (the rule-based scoring is done); a pilot set
without it only gets a note. The output is never overwritten. The run stops without writing
anything if a value is invalid (outside 0-1, or empty without a reason from the metric itself),
if the scorer fails, or if the judge changed (several reported models or system fingerprints, or a
new creation time of the model object, ADR 0033). A NaN that the metric gives with a reason is
valid: stored as an empty cell with the reason, counted and reported.

Output schema (docs/reference/data-formats.md): question_id, strategy, the four metrics,
nan_reasons. `--repeat` (pilot sets only) writes ragas_scores_repeat.csv under the step
`ragas_repeat`, so the `ragas` record stays the one of ragas_scores.csv.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from atomic_csv import write_csv
from config import (
    CATALOGUE_FREEZE_FILE,
    CHUNK_FILES,
    CONTROL_ANSWER_STRATEGIES,
    DOCUMENTS_FILE,
    GENERATED_ANSWERS_FILE,
    GENERATION_RUNS_FILE,
    GROUND_TRUTH_FILE,
    ID_SEPARATOR,
    PILOT_RUNS_FILE_NAME,
    QUESTIONS_FILE,
    RAGAS_DECIMALS,
    RAGAS_JUDGE_MODEL,
    RAGAS_METRICS,
    RAGAS_REPEAT_FILE_NAME,
    RAGAS_SCORES_FILE,
    RETRIEVED_RESULTS_FILE,
    SCORES_FILE,
    SECTIONS_FILE,
    STRATEGY_IDS,
)
from embed import load_jsonl
from freeze import is_main_catalogue, require_frozen
from generate import ANSWERS_HEADER, created_iso
from retrieve import GROUND_TRUTH_HEADER, QUESTIONS_HEADER, QUESTIONS_REQUIRED, read_rows
from run_log import append_record, latest_run, ragas_record, require_run, sha256_of

# ragas_client is imported only inside main(): it imports nothing from here, but the real scorer
# (make_scorer) takes its types from this module.

RAGAS_HEADER = ["question_id", "strategy", *RAGAS_METRICS, "nan_reasons"]
EXPERIMENT = ",".join(STRATEGY_IDS)

MetricValue = tuple[float | None, str]  # value, reason; value None only with a non-empty reason


@dataclass(frozen=True)
class Sample:
    question_id: str
    strategy: str
    user_input: str
    response: str
    retrieved_contexts: tuple[str, ...]
    reference: str


Scorer = Callable[[list[Sample]], list[dict[str, MetricValue]]]


def build_samples(
    answers_file: Path,
    questions_file: Path,
    ground_truth_file: Path,
    chunk_files: dict[str, Path],
) -> list[Sample]:
    """One sample per question and strategy C1-C3, sorted by question and STRATEGY_IDS order.
    K0 rows are skipped; any other strategy, a missing or duplicate answer, an empty `sources`
    or a chunk missing from the chunk files raises ValueError."""
    questions = {
        q["question_id"]: q["question"]
        for q in read_rows(
            questions_file, "question catalogue", QUESTIONS_HEADER, QUESTIONS_REQUIRED
        )
    }
    references = {
        t["question_id"]: t["expected_answer"]
        for t in read_rows(
            ground_truth_file, "ground truth", GROUND_TRUTH_HEADER, GROUND_TRUTH_HEADER
        )
    }
    chunks = {  # per strategy: a C1 answer may only name C1 chunks
        key: {
            c["chunk_id"]: c["text"]
            for c in load_jsonl(chunk_files[key], "run src/chunking.py first")
        }
        for key in STRATEGY_IDS
    }
    rows = read_rows(
        answers_file,
        "answers",
        ANSWERS_HEADER,
        ["question_id", "strategy", "answer"],
        unique_ids=False,
    )
    by_pair: dict[tuple[str, str], dict] = {}
    for row in rows:
        strategy = row["strategy"]
        if strategy in CONTROL_ANSWER_STRATEGIES:
            continue
        if strategy not in STRATEGY_IDS:
            raise ValueError(
                f"{answers_file.name}: strategy {strategy!r} of {row['question_id']} is not one "
                f"of {sorted(STRATEGY_IDS)}; RAGAS scores only C1-C3 (ADR 0047)"
            )
        pair = (row["question_id"], strategy)
        if pair in by_pair:
            raise ValueError(f"{answers_file.name}: several answers for {pair[0]}/{pair[1]}")
        by_pair[pair] = row
    unknown = sorted({q for q, _ in by_pair} - set(questions))
    if unknown:
        raise ValueError(f"{answers_file.name}: answers for unknown questions {unknown}")
    samples = []
    for qid in sorted(questions):
        for strategy in STRATEGY_IDS:
            row = by_pair.get((qid, strategy))
            if row is None:
                raise ValueError(f"{answers_file.name}: no answer for {qid}/{strategy}")
            ids = [s for s in row["sources"].split(ID_SEPARATOR) if s]
            if not ids:
                raise ValueError(f"{answers_file.name}: {qid}/{strategy} has no sources")
            missing = [i for i in ids if i not in chunks[strategy]]
            if missing:
                raise ValueError(
                    f"{answers_file.name}: {qid}/{strategy} names chunks {missing} that the "
                    f"{strategy} chunk file does not hold"
                )
            samples.append(
                Sample(
                    question_id=qid,
                    strategy=strategy,
                    user_input=questions[qid],
                    response=row["answer"],
                    retrieved_contexts=tuple(chunks[strategy][i] for i in ids),
                    reference=references[qid],
                )
            )
    return samples


def _is_nan(value: float | None) -> bool:
    return value is None or math.isnan(value)


def validated(sample: Sample, values: dict[str, MetricValue]) -> dict[str, MetricValue]:
    """The values, unless a metric is missing or unexpected, a value lies outside [0, 1], or a
    missing value (None/NaN) comes without the metric's own reason."""
    label = f"{sample.question_id}/{sample.strategy}"
    if set(values) != set(RAGAS_METRICS):
        raise RuntimeError(
            f"{label}: the scorer returned the metrics {sorted(values)}, expected "
            f"{sorted(RAGAS_METRICS)}; nothing was written (ADR 0047)"
        )
    for metric, (value, reason) in values.items():
        if _is_nan(value):
            if not reason.strip():
                raise RuntimeError(
                    f"{label}: {metric} is NaN without a reason from the metric; nothing was "
                    "written (ADR 0047)"
                )
        elif not 0.0 <= value <= 1.0:
            raise RuntimeError(
                f"{label}: {metric} = {value} lies outside 0-1; nothing was written (ADR 0047)"
            )
    return values


def _cell(value: float | None) -> str:
    return "" if _is_nan(value) else f"{value:.{RAGAS_DECIMALS}f}"


def run(
    scorer: Scorer,
    recorder,  # ragas_client.ApiRecorder
    model_created: Callable[[], int],
    paths: dict,
    main: bool,
    repeat: bool = False,
) -> int:
    """Score the answers C1-C3 and write the scores file; return the number of rows written.

    `main` is the main catalogue; a set whose files resolve to it counts as main too (no pilot
    exceptions, as in analysis_data.load). `repeat` (pilot sets only) writes the repeat file under
    the step `ragas_repeat`.
    """
    main = main or is_main_catalogue(paths["questions_file"], paths["ground_truth_file"])
    if repeat and main:
        raise RuntimeError("--repeat is for pilot sets only; the main run happens once (ADR 0047)")
    if repeat:  # the repeat compares with the first run, which must be the current file
        require_run(paths["runs_file"], "ragas", EXPERIMENT, [], [paths["out_file"]])
    step = "ragas_repeat" if repeat else "ragas"
    out_file: Path = paths["repeat_file"] if repeat else paths["out_file"]
    runs_file: Path = paths["runs_file"]
    answers_file: Path = paths["answers_file"]
    scores_file: Path = paths["scores_file"]
    chunk_files: dict[str, Path] = paths["chunk_files"]
    keys = list(STRATEGY_IDS)

    require_frozen(
        paths["questions_file"],
        paths["ground_truth_file"],
        paths["sections_file"],
        paths["documents_file"],
        paths["freeze_file"],
    )
    # the answers are the output of the latest generate run, over exactly these inputs, so the
    # contexts below are the passages the answer model saw (spec, first anti-goal)
    generate_inputs = [
        paths["results_file"],
        paths["questions_file"],
        paths["ground_truth_file"],
        *(chunk_files[k] for k in keys),
    ]
    require_run(runs_file, "generate", EXPERIMENT, generate_inputs, [answers_file])
    if latest_run(runs_file, "summarise", EXPERIMENT) is None and not main:
        print(
            f"note: {runs_file} has no `summarise` record (pilot set, scored under an older rule "
            "version); RAGAS runs anyway (ADR 0047)"
        )
    else:
        require_run(runs_file, "summarise", EXPERIMENT, [], [scores_file])
    if out_file.exists():
        raise FileExistsError(
            f"{out_file} exists; RAGAS runs once (ADR 0047), delete it deliberately to run again"
        )
    samples = build_samples(
        answers_file, paths["questions_file"], paths["ground_truth_file"], chunk_files
    )

    created_before = model_created()  # free lookup, only after every local check
    results = scorer(samples)
    if len(results) != len(samples):
        raise RuntimeError(
            f"the scorer returned {len(results)} results for {len(samples)} samples; nothing "
            "was written (ADR 0047)"
        )
    nan_counts = dict.fromkeys(RAGAS_METRICS, 0)
    rows = []
    for sample, values in zip(samples, results, strict=True):
        values = validated(sample, values)
        reasons = []
        for metric in RAGAS_METRICS:
            if _is_nan(values[metric][0]):
                nan_counts[metric] += 1
                reasons.append(f"{metric}: {values[metric][1].strip()}")
        rows.append(
            {
                "question_id": sample.question_id,
                "strategy": sample.strategy,
                **{m: _cell(values[m][0]) for m in RAGAS_METRICS},
                "nan_reasons": "; ".join(reasons),
            }
        )
    recorder.check()
    if not recorder.models:
        raise RuntimeError(
            "no judge model reported by the API for the scored samples; nothing was written "
            "(ADR 0033)"
        )
    created_after = model_created()
    if created_after != created_before:
        raise RuntimeError(
            f"the model behind {RAGAS_JUDGE_MODEL} changed during the run (created "
            f"{created_iso(created_before)}, now {created_iso(created_after)}); nothing was "
            "written (ADR 0033)"
        )

    inputs = [
        answers_file,
        paths["results_file"],
        paths["questions_file"],
        paths["ground_truth_file"],
        *(chunk_files[k] for k in keys),
    ]
    if main:
        inputs.append(scores_file)
    # the complete record is built before anything is written; only the output hash follows
    record = ragas_record(
        {
            "step": step,
            "strategy": EXPERIMENT,
            "model_reported": next(iter(recorder.models), None),
            "model_created": created_iso(created_before),
            "system_fingerprint": next(iter(recorder.fingerprints), None),
            "rows": len(rows),
            "nan_counts": nan_counts,
            "inputs_sha256": {f.name: sha256_of(f) for f in inputs},
            "judge_prompt_tokens": recorder.chat_prompt_tokens,
            "judge_completion_tokens": recorder.chat_completion_tokens,
            "embedding_tokens": recorder.embedding_tokens,
        }
    )
    write_csv(out_file, RAGAS_HEADER, rows)
    append_record(record | {"outputs_sha256": {out_file.name: sha256_of(out_file)}}, runs_file)
    return len(rows)


def main_paths() -> dict:
    return {
        "answers_file": GENERATED_ANSWERS_FILE,
        "results_file": RETRIEVED_RESULTS_FILE,
        "questions_file": QUESTIONS_FILE,
        "ground_truth_file": GROUND_TRUTH_FILE,
        "sections_file": SECTIONS_FILE,
        "documents_file": DOCUMENTS_FILE,
        "freeze_file": CATALOGUE_FREEZE_FILE,
        "chunk_files": dict(CHUNK_FILES),
        "scores_file": SCORES_FILE,
        "runs_file": GENERATION_RUNS_FILE,
        "out_file": RAGAS_SCORES_FILE,
        "repeat_file": RAGAS_SCORES_FILE.with_name(RAGAS_REPEAT_FILE_NAME),
    }


def set_paths(set_dir: Path) -> dict:
    """A pilot set: its own files and run log; the chunk files are the shared processed corpus.
    A set that resolves to the main catalogue gets the main paths (and so the main run log)."""
    if is_main_catalogue(set_dir / QUESTIONS_FILE.name, set_dir / GROUND_TRUTH_FILE.name):
        return main_paths()
    return main_paths() | {
        "answers_file": set_dir / GENERATED_ANSWERS_FILE.name,
        "results_file": set_dir / RETRIEVED_RESULTS_FILE.name,
        "questions_file": set_dir / QUESTIONS_FILE.name,
        "ground_truth_file": set_dir / GROUND_TRUTH_FILE.name,
        "scores_file": set_dir / SCORES_FILE.name,
        "runs_file": set_dir / PILOT_RUNS_FILE_NAME,
        "out_file": set_dir / RAGAS_SCORES_FILE.name,
        "repeat_file": set_dir / RAGAS_REPEAT_FILE_NAME,
    }


def main(argv: list[str] | None = None) -> None:
    import argparse

    p = argparse.ArgumentParser(
        description="Score the answers C1-C3 with RAGAS (ADR 0047); runs once, never overwrites."
    )
    p.add_argument("--set", type=Path, metavar="DIR", help="a pilot set instead of the catalogue")
    p.add_argument(
        "--repeat",
        action="store_true",
        help="second run of a pilot set into ragas_scores_repeat.csv (stability, ADR 0047)",
    )
    args = p.parse_args(argv)
    paths = set_paths(args.set) if args.set else main_paths()

    from llm_client import model_created
    from ragas_client import ApiRecorder, async_client, make_scorer

    recorder = ApiRecorder()
    scorer = make_scorer(async_client(recorder))
    count = run(
        scorer,
        recorder,
        lambda: model_created(model=RAGAS_JUDGE_MODEL),
        paths,
        main=args.set is None,
        repeat=args.repeat,
    )
    print(f"{count} rows -> {paths['repeat_file'] if args.repeat else paths['out_file']}")


if __name__ == "__main__":
    main()
