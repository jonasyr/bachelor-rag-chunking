"""Closed-book and open-book run of a candidate's probes (ADR 0038).

Drops probes whose term appears in the page or section title (leak), asks the answer model
(llm_client, the experiment's pinned settings) for every probe once without and once with the
masked section text, and scores exact match after normalisation. Writes results/<name>.jsonl
(without the section text) and misses/<name>.json: the well-posed probes (open-book correct)
missed closed-book, with an empty category for the classification. Calls the OpenAI API.

The open-book context is a CORPUS_PROBE_CONTEXT_CHARS window around the probed sentence; the
recorded runs used the start of the section (--recorded repeats that). Every result row keeps the
model and system fingerprint the API reported; a run whose replies name more than one model stops.

Usage: uv run python scripts/corpus_probe/run_probes.py NAME "PRODUCT (description)" [--recorded]
"""

import concurrent.futures as cf
import json
import re
import sys

from common import MISSES_DIR, PROBES_DIR, RESULTS_DIR, read_json, write_json
from dotenv import load_dotenv

from config import (
    CORPUS_PROBE_CONTEXT_CHARS,
    CORPUS_PROBE_GUESS_CHARS,
    CORPUS_PROBE_WORKERS,
    LLM_PRICE_INPUT_PER_MTOK,
    LLM_PRICE_OUTPUT_PER_MTOK,
)
from llm_client import complete

SYSTEM = "You are an expert on {product}."
HEAD = (
    'The following sentence is from the official {product} documentation, page "{page}", '
    'section "{section}". One code term was replaced by [MASK].\n\nSentence: {sentence}\n\n'
)
CONTEXT = "Section text (the term is masked there too):\n{context}\n\n"
TAIL = "Reply with the masked code term only, without backticks or explanation."


def norm(term: str) -> str:
    """First line, without backticks, quotes, whitespace, trailing dot and call parentheses."""
    first = term.strip().split("\n")[0]
    return re.sub(r"[`'\"\s]|\(\)$", "", first).rstrip(".").lower().removesuffix("()")


def window(probe: dict, recorded: bool) -> str:
    """The section text shown open-book: a window that contains the probed sentence."""
    text, size = probe["section_text"], CORPUS_PROBE_CONTEXT_CHARS
    if recorded or len(text) <= size:
        return text[:size]
    before = probe["sentence"].split("[MASK]")[0].replace("`", "").strip()[-30:]
    pos = text.find(before) if before else -1
    pos = pos if pos >= 0 else max(text.find("[MASK]"), 0)
    start = max(0, min(pos - size // 2, len(text) - size))
    return text[start : start + size]


def ask(probe: dict, product: str, open_book: bool, recorded: bool) -> tuple:
    user = HEAD.format(product=product, **probe)
    if open_book:
        user += CONTEXT.format(context=window(probe, recorded))
    reply = complete(
        [
            {"role": "system", "content": SYSTEM.format(product=product)},
            {"role": "user", "content": user + TAIL},
        ]
    )
    return (
        reply.text,
        reply.prompt_tokens,
        reply.completion_tokens,
        reply.model,
        reply.system_fingerprint,
    )


def main() -> None:
    load_dotenv()
    name, product = sys.argv[1], sys.argv[2]
    recorded = sys.argv[3:] == ["--recorded"]
    probes = [
        p
        for p in read_json(PROBES_DIR / f"{name}.json")
        if norm(p["answer"]) not in norm(p["section"]) and norm(p["answer"]) not in norm(p["page"])
    ]
    jobs = [(i, open_book) for i in range(len(probes)) for open_book in (False, True)]
    tokens = [0, 0]
    with cf.ThreadPoolExecutor(CORPUS_PROBE_WORKERS) as pool:
        replies = list(pool.map(lambda job: ask(probes[job[0]], product, job[1], recorded), jobs))
    models = sorted({reply[3] for reply in replies})
    if len(models) != 1:
        raise SystemExit(f"the replies name several models {models}; run again")
    for (i, open_book), (text, prompt_tokens, completion_tokens, model, fingerprint) in zip(
        jobs, replies, strict=True
    ):
        run = "open" if open_book else "closed"
        probes[i][run] = text
        probes[i]["model"] = model
        probes[i][run + "_fingerprint"] = fingerprint
        tokens[0] += prompt_tokens
        tokens[1] += completion_tokens
    results, misses = [], []
    for i, p in enumerate(probes):
        p.pop("section_text")
        for run in ("closed", "open"):
            p[run + "_ok"] = norm(p[run]) == norm(p["answer"])
        results.append(p)
        if p["open_ok"] and not p["closed_ok"]:
            misses.append(
                {
                    "id": i,
                    "page": p["page"],
                    "section": p["section"],
                    "sentence": p["sentence"],
                    "answer": p["answer"],
                    "closed_book_guess": p["closed"].strip()[:CORPUS_PROBE_GUESS_CHARS],
                    "category": "",
                }
            )
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / f"{name}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in results), encoding="utf-8"
    )
    write_json(MISSES_DIR / f"{name}.json", misses)
    cost = tokens[0] / 1e6 * LLM_PRICE_INPUT_PER_MTOK + tokens[1] / 1e6 * LLM_PRICE_OUTPUT_PER_MTOK
    print(
        name, len(probes), "probes,", len(misses), "misses; tokens", tokens, "USD", round(cost, 4)
    )


if __name__ == "__main__":
    main()
