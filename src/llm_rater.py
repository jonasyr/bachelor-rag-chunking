"""LLM cross-check of the rubric checks (ADR 0046, addendum 17.11.2026).

The judge model config.LLM_RATER_MODEL (the RAGAS judge, not the answer model) answers the same
checks Jonas answers in the app (ADR 0035), for the blind C1-C3 items of scoring_items.jsonl and
with his frozen key points. It sees only question, reference answer, key points, the excerpts and
the answer, never the code or the strategy, and the wording of the app (config.RUBRIC_*). Scope
config.LLM_RATER_SCOPE: "all" answers or only the questions of the R2 draw ("sample").

Each answer is one request with a strict JSON schema (the options of scoring_rules.CHECKS, one mark
per key point, a short `reason` that stays in the journal). The step runs once like the generation
(ADR 0033, 0050): every API result goes into llm_rater_journal.jsonl the moment it arrives, a
restart asks only for the missing answers, and the outputs are rebuilt from the journal. A cut-off
answer, an invalid parsed answer, another model or fingerprint within the run, or a changed model
behind the alias stops the run with an `abort` entry and writes nothing; a journaled answer that
fails stops every restart again, until Jonas decides.

Outputs in data/evaluation/llm_rater/ (pilot: DIR/llm_rater/), in exactly the formats of Jonas'
own files and in their code order: scoring_checks.csv (scoring_rules.CHECKS_HEADER) and
scoring_sheet.csv (evaluate_answers.SHEET_HEADER, values by scoring_rules.derive, empty notes).
Run record `llm_rater` in the run log (main: generation_runs.jsonl).
"""

import hashlib
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

import llm_client
import scoring_rules as rules
import scoring_store
import second_rater
from atomic_csv import read_csv, write_csv
from config import (
    GENERATION_RUNS_FILE,
    GROUND_TRUTH_FILE,
    LLM_RATER_CONTROL_JOURNAL_FILE_NAME,
    LLM_RATER_CONTROL_SYSTEM_PROMPT,
    LLM_RATER_CONTROL_USER_TEMPLATE,
    LLM_RATER_DIR,
    LLM_RATER_DIR_NAME,
    LLM_RATER_EXCERPT_TEMPLATE,
    LLM_RATER_JOURNAL_FILE_NAME,
    LLM_RATER_MAX_TOKENS,
    LLM_RATER_MODEL,
    LLM_RATER_POINT_TEMPLATE,
    LLM_RATER_REASONING_EFFORT,
    LLM_RATER_SCHEMA_NAME,
    LLM_RATER_SCOPE,
    LLM_RATER_SEED,
    LLM_RATER_SYSTEM_PROMPT,
    LLM_RATER_TEMPERATURE,
    LLM_RATER_USER_TEMPLATE,
    QUESTIONS_FILE,
    SCORING_CHECKS_CONTROL_FILE,
    SCORING_CHECKS_FILE,
    SCORING_ITEMS_CONTROL_FILE,
    SCORING_SHEET_CONTROL_FILE,
    SCORING_SHEET_FILE,
    STRATEGY_IDS,
)
from control_k0 import CODE_SUFFIX, CONTROL_SHEET_HEADER
from embedding_client import drain_http_errors
from evaluate_answers import SHEET_HEADER
from generate import COMPLETION_FIELDS, checked, created_iso, usage_detail
from journal import Journal
from llm_client import Completion
from run_log import (
    append_record,
    environment,
    llm_rater_cost,
    llm_rater_settings,
    require_run,
    session_commits,
    sha256_of,
)

STEP = "llm_rater"
CONTROL_STEP = "llm_rater_control"  # the closed-book control K0 (ADR 0041, 0051)
STRATEGY = ",".join(STRATEGY_IDS)
SCOPES = ("all", "sample")


def paths(set_dir: Path | None) -> dict:
    """The files of the main run or, with `set_dir`, of a pilot set; `out_dir` holds the output."""
    p = second_rater.paths(set_dir)
    keep = (
        "questions_file",
        "ground_truth_file",
        "items_file",
        "sheet_file",
        "checks_file",
        "key_points_file",
        "scores_file",
        "sample_file",
        "runs_file",
    )
    out = LLM_RATER_DIR if set_dir is None else set_dir / LLM_RATER_DIR_NAME
    control_items = (
        SCORING_ITEMS_CONTROL_FILE if set_dir is None else set_dir / SCORING_ITEMS_CONTROL_FILE.name
    )
    return {k: p[k] for k in keep} | {"out_dir": out, "control_items_file": control_items}


def schema(n_points: int, control: bool = False) -> dict:
    """The strict JSON schema of one answer: every check with its options, one mark per key point
    and a short reason (OpenAI strict mode: every property required, no other properties).
    K0 (`control`) has no `grounded`: it saw no excerpts."""
    checks = rules.checks_for(control)
    properties: dict[str, dict] = {
        "declines": {"type": "string", "enum": list(checks["declines"])},
        "points": {
            "type": "array",
            "items": {"type": "string", "enum": list(rules.POINT_MARKS)},
            "minItems": n_points,
            "maxItems": n_points,
        },
    }
    for check, options in checks.items():
        properties.setdefault(check, {"type": "string", "enum": list(options)})
    properties["reason"] = {"type": "string"}
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def response_format(n_points: int, control: bool = False) -> dict:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": LLM_RATER_SCHEMA_NAME,
            "strict": True,
            "schema": schema(n_points, control),
        },
    }


def messages(item: dict, key_points: list[str], control: bool = False) -> list[dict]:
    """System prompt and the user message of one blind item; only question, reference answer,
    key points, excerpts and answer are used (never the code or anything else of the item).
    K0 (`control`) has no excerpts section."""
    template = LLM_RATER_CONTROL_USER_TEMPLATE if control else LLM_RATER_USER_TEMPLATE
    system = LLM_RATER_CONTROL_SYSTEM_PROMPT if control else LLM_RATER_SYSTEM_PROMPT
    user = template.format(
        question=item["question"],
        reference_answer=item["reference_answer"],
        key_points="\n".join(
            LLM_RATER_POINT_TEMPLATE.format(n=n, text=text)
            for n, text in enumerate(key_points, start=1)
        ),
        excerpts="\n\n".join(
            LLM_RATER_EXCERPT_TEMPLATE.format(n=n, text=text)
            for n, text in enumerate(item["excerpts"], start=1)
        ),
        answer=item["answer"],
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def to_checks(parsed: Any, n_points: int, control: bool = False) -> dict:
    """The checks of a parsed answer, as the app stores them: with declines = yes the key points
    and skipped checks take their fixed values (rules.declined); then validated (rules.validate).
    Raise ValueError for anything else than the schema's fields and options."""
    if not isinstance(parsed, dict):
        raise ValueError(f"the answer is not a JSON object: {parsed!r}")
    if not isinstance(parsed.get("reason"), str):
        raise ValueError("the answer has no text `reason`")
    if not isinstance(parsed.get("points"), list):
        raise ValueError("the answer's `points` is not a list")
    checks = {k: v for k, v in parsed.items() if k != "reason"}
    if set(checks) == {"points", *rules.checks_for(control)}:
        checks = rules.declined(checks, n_points, control)
    rules.validate(checks, n_points, control)
    return checks


def prompts_sha256(control: bool = False) -> str:
    """Checksum of the prompt texts and the schema layout (with one key point)."""
    if control:
        texts = [LLM_RATER_CONTROL_SYSTEM_PROMPT, LLM_RATER_CONTROL_USER_TEMPLATE]
        texts += [LLM_RATER_POINT_TEMPLATE]
    else:
        texts = [LLM_RATER_SYSTEM_PROMPT, LLM_RATER_USER_TEMPLATE, LLM_RATER_POINT_TEMPLATE]
        texts += [LLM_RATER_EXCERPT_TEMPLATE]
    text = "\x00".join([*texts, json.dumps(response_format(1, control), sort_keys=True)])
    return hashlib.sha256(text.encode()).hexdigest()


def request_sha256(msgs: list[dict], fmt: dict) -> str:
    request = {"messages": msgs, "response_format": fmt}
    return hashlib.sha256(json.dumps(request, ensure_ascii=False).encode()).hexdigest()


def _own_set(p: dict) -> scoring_store.ScoringSet:
    return scoring_store.ScoringSet(
        "own",
        p["items_file"],
        p["sheet_file"],
        p["scores_file"],
        p["key_points_file"],
        p["checks_file"],
        p["runs_file"],
    )


def _selected(p: dict, items: list[dict], scope: str) -> tuple[list[dict], list[Path]]:
    """The items of the scope in sheet order and the input files to hash."""
    inputs = [p["items_file"], p["key_points_file"]]
    if scope == "all":
        return items, inputs
    if scope != "sample":
        raise ValueError(f"LLM_RATER_SCOPE is {scope!r}, not one of {SCOPES}")
    if not p["sample_file"].exists():
        raise RuntimeError(f"{p['sample_file']} not found; run src/second_rater.py --mode draw")
    require_run(p["runs_file"], second_rater.DRAW_STEP, STRATEGY, [], [p["sample_file"]])
    sampled = {r["question_id"] for r in read_csv(p["sample_file"], second_rater.SAMPLE_HEADER)}
    return [i for i in items if i["question_id"] in sampled], [*inputs, p["sample_file"]]


def _control_items(p: dict) -> list[dict]:
    """The K0 items, refused unless the K0 scaffold record covers the file as it is now."""
    items_file = p["control_items_file"]
    if not items_file.exists():
        raise RuntimeError(f"{items_file} not found; scaffold the control K0 first (ADR 0041)")
    require_run(p["runs_file"], "scaffold", CODE_SUFFIX, [], [items_file])
    lines = items_file.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def run(p: dict, client: Any = None, control: bool = False) -> dict:
    """Ask the judge for every item of the scope (or take its answer from the journal), write
    the checks and the sheet and append the run record; return the record. With `control` the
    judge rates the whole closed-book K0 set instead (no excerpts, no grounded)."""
    out = p["out_dir"]
    step, strategy = (CONTROL_STEP, CODE_SUFFIX) if control else (STEP, STRATEGY)
    if control:
        checks_file = out / SCORING_CHECKS_CONTROL_FILE.name
        sheet_file = out / SCORING_SHEET_CONTROL_FILE.name
        journal_file = out / LLM_RATER_CONTROL_JOURNAL_FILE_NAME
    else:
        checks_file, sheet_file = out / SCORING_CHECKS_FILE.name, out / SCORING_SHEET_FILE.name
        journal_file = out / LLM_RATER_JOURNAL_FILE_NAME
    for path in (checks_file, sheet_file):
        if path.exists():
            raise FileExistsError(
                f"{path} exists; the LLM cross-check runs once (ADR 0046, 0050). If it was "
                f"written without a run record, delete both output files: a new run takes every "
                f"answer from {journal_file.name} and calls the API for none"
            )
    own = _own_set(p)
    try:
        scoring_store.require_frozen_key_points(own)
    except PermissionError as error:
        raise RuntimeError(f"{error}; freeze the key points in the app first") from None
    if control:  # K0 is always rated whole: the scope does not apply
        scope = "all"
        items = _control_items(p)
        inputs = [p["control_items_file"], p["key_points_file"]]
    else:
        scope = LLM_RATER_SCOPE
        items, inputs = _selected(p, scoring_store.load_items(own), scope)
    points = scoring_store.load_key_points(own)
    if not items:
        raise RuntimeError(f"no items in scope {scope!r}")
    for item in items:
        if not points.get(item["question_id"]):
            raise RuntimeError(f"{item['question_id']} has no frozen key points")

    def completer(msgs: list[dict], fmt: dict) -> Completion:
        return llm_client.complete(
            msgs,
            client,
            model=LLM_RATER_MODEL,
            reasoning_effort=LLM_RATER_REASONING_EFFORT,
            temperature=LLM_RATER_TEMPERATURE,
            max_tokens=LLM_RATER_MAX_TOKENS,
            seed=LLM_RATER_SEED,
            response_format=fmt,
        )

    def model_created() -> int:
        return llm_client.model_created(client, model=LLM_RATER_MODEL)

    inputs_sha256 = {f.name: sha256_of(f) for f in inputs}
    created_before = model_created()  # free lookup, only after every local check
    journal = Journal(
        journal_file,
        {
            "step": step,
            "strategy": strategy,
            **llm_rater_settings(scope),
            "prompts_sha256": prompts_sha256(control),
            "model_created": created_iso(created_before),
            "inputs_sha256": inputs_sha256,
        },
        session=environment(),
    )
    done = {e["code"]: e for e in journal.of("item")}
    results: dict[str, dict] = {}
    models: set[str] = set()
    fingerprints: set[str] = set()
    received = 0
    try:
        for item in items:
            code, qid = item["code"], item["question_id"]
            n_points = len(points[qid])
            msgs = messages(item, points[qid], control)
            fmt = response_format(n_points, control)
            digest = request_sha256(msgs, fmt)
            entry = done.get(code)
            if entry is None:  # not yet paid for: ask the API and journal the answer at once
                answer = completer(msgs, fmt)
                entry = {
                    "kind": "item",
                    "code": code,
                    "question_id": qid,
                    "request_sha256": digest,
                    **{k: v for k, v in asdict(answer).items() if k != "raw"},
                    "response": answer.raw,
                    "http_errors": drain_http_errors(),
                }
                journal.append(entry)
                received += 1
            elif entry["request_sha256"] != digest:
                raise RuntimeError(
                    f"{code}: the journaled answer was asked with another request; nothing was "
                    "written (ADR 0050)"
                )
            answer = checked(
                Completion(**{f: entry[f] for f in COMPLETION_FIELDS}), code, models, fingerprints
            )
            try:
                parsed = json.loads(answer.text)
                results[code] = to_checks(parsed, n_points, control)
            except ValueError as error:  # JSONDecodeError is a ValueError
                raise ValueError(f"{code}: invalid answer of the judge: {error}") from None
        created_after = model_created()
        if created_after != created_before:
            raise RuntimeError(
                f"the model behind {LLM_RATER_MODEL} changed during the run (created "
                f"{created_iso(created_before)}, now {created_iso(created_after)}); nothing was "
                "written (ADR 0033)"
            )
    except BaseException as error:
        journal.abort(error, answers_received=received, http_errors=drain_http_errors())
        raise

    derive = rules.derive_control if control else rules.derive
    checks_rows = [rules.to_row(i["code"], results[i["code"]], control) for i in items]
    sheet_rows = [
        {"code": i["code"], "question_id": i["question_id"]}
        | {c: str(v) for c, v in derive(results[i["code"]]).items()}
        | {"notes": ""}
        for i in items
    ]
    write_csv(checks_file, rules.checks_header(control), checks_rows)
    write_csv(sheet_file, CONTROL_SHEET_HEADER if control else SHEET_HEADER, sheet_rows)
    entries = journal.of("item")
    prompt_tokens = sum(e["prompt_tokens"] for e in entries)
    completion_tokens = sum(e["completion_tokens"] for e in entries)
    record = {
        "date": date.today().isoformat(),
        **llm_rater_settings(scope),
        **environment(),
        "step": step,
        "strategy": strategy,
        "model_reported": next(iter(models), None),
        "model_created": created_iso(created_before),
        "system_fingerprint": next(iter(fingerprints), None),
        "prompts_sha256": prompts_sha256(control),
        "answers": len(items),
        "sessions": len(journal.of("session")),
        "session_commits": session_commits(journal),
        "aborts": len(journal.of("abort")),
        "http_errors": sum(len(e.get("http_errors", [])) for e in journal.entries),
        "inputs_sha256": inputs_sha256,
        "outputs_sha256": {f.name: sha256_of(f) for f in (checks_file, sheet_file, journal_file)},
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "reasoning_tokens": sum(usage_detail(e["response"], "reasoning_tokens") for e in entries),
        "cached_tokens": sum(usage_detail(e["response"], "cached_tokens") for e in entries),
        "cost_usd": llm_rater_cost(prompt_tokens, completion_tokens),
    }
    if control:
        record["control"] = True
    append_record(record, p["runs_file"])
    return record


def main(argv: list[str] | None = None) -> None:
    import argparse
    import logging

    from freeze import is_main_catalogue
    from run_log import require_clean_tree

    parser = argparse.ArgumentParser(
        description="LLM cross-check of the rubric checks of C1-C3 (ADR 0046); runs once."
    )
    parser.add_argument(
        "--set", type=Path, metavar="DIR", help="a pilot set (e.g. data/pilot/hard) instead"
    )
    parser.add_argument(
        "--control", action="store_true", help="rate the closed-book control K0 instead (ADR 0051)"
    )
    args = parser.parse_args(argv)
    if args.set and is_main_catalogue(
        args.set / QUESTIONS_FILE.name, args.set / GROUND_TRUTH_FILE.name
    ):
        raise SystemExit(f"{args.set} holds the main catalogue; run without --set")
    p = paths(args.set)
    if p["runs_file"] == GENERATION_RUNS_FILE:  # the main run
        require_clean_tree()
    logging.basicConfig(format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("openai").setLevel(logging.INFO)  # shows each SDK retry (ADR 0050)
    record = run(p, control=True) if args.control else run(p)
    print(f"{record['answers']} answers checked -> {p['out_dir']}")


if __name__ == "__main__":
    main()
