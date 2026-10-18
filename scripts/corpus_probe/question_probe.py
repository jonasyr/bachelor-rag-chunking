"""Question-level closed-book check of candidate corpora (ADR 0038).

sample NAME...  draws sections (H2/H3, outside examples, changelogs and blogs, at least
                CORPUS_QUESTIONS_MIN_WORDS prose words, at most CORPUS_QUESTIONS_PER_PAGE per page)
                into questions/<name>-sections.json for the question writer (an agent, prompt in
                docs/reference/corpus-selection.md), who writes questions/<name>.json
answer NAME...  answers every question closed-book and open-book (llm_client; calls the API)
blind BATCH NAME...  shuffles the answers with CORPUS_QUESTIONS_JUDGE_SEEDS[BATCH] into
                questions/judge-input.json and judge-key.json (batch 1: five corpora, 2: Angular)
unblind         merges the judge's questions/judge-output.json into questions/<name>.json
summary         prints the share of retrieval-dependent questions per corpus

Usage: uv run python scripts/corpus_probe/question_probe.py COMMAND [NAME...]
(run from the repo root; the Vue row needs data/processed/documents.jsonl of the Vue snapshot)
"""

import collections
import concurrent.futures as cf
import json
import math
import random
import re
import sys

from common import CORPUS_PROBE_DIR, DOCS_DIR, ROOT, candidates, read_json, read_jsonl, write_json
from dotenv import load_dotenv

from config import (
    CORPUS_PROBE_SEED,
    CORPUS_PROBE_WORKERS,
    CORPUS_QUESTIONS_JUDGE_SEEDS,
    CORPUS_QUESTIONS_MIN_WORDS,
    CORPUS_QUESTIONS_PER_CORPUS,
    CORPUS_QUESTIONS_PER_PAGE,
    CORPUS_QUESTIONS_SECTION_CHARS,
)

QUESTIONS_DIR = CORPUS_PROBE_DIR / "questions"
SKIP_PATHS = re.compile(r"(^|/)(examples?|changelog|blog)/")
TAIL = "Answer in 1-3 sentences. If you do not know, say so instead of guessing."
VERDICTS = ("correct", "partial", "wrong", "abstain")


def pages(name: str) -> list[dict]:
    if candidates()[name]["repo"] == "local":
        return read_jsonl(ROOT / candidates()[name]["docs_path"])
    return read_json(DOCS_DIR / f"{name}.json")


def sections(doc: dict) -> list[tuple[str, str]]:
    out, heading, lines, in_code = [], doc["title"], [], False
    for line in doc["text"].split("\n"):
        if line.strip().startswith(("```", "~~~")):
            in_code = not in_code
        m = None if in_code else re.match(r"^(#{2,3})\s+(.*)", line)
        if m:
            out.append((heading, "\n".join(lines)))
            heading, lines = m.group(2).strip(), []
        else:
            lines.append(line)
    out.append((heading, "\n".join(lines)))
    return out


def sample(name: str) -> list[dict]:
    pool = []
    for doc in pages(name):
        for heading, body in sections(doc):
            prose = re.sub(r"```.*?```|~~~.*?~~~", "", body, flags=re.S)
            words = len(re.findall(r"[A-Za-z]{3,}", prose))
            if words >= CORPUS_QUESTIONS_MIN_WORDS and not SKIP_PATHS.search(doc["path"]):
                text = body.strip()[:CORPUS_QUESTIONS_SECTION_CHARS]
                pool.append(
                    {"path": doc["path"], "page": doc["title"], "section": heading, "text": text}
                )
    random.Random(CORPUS_PROBE_SEED).shuffle(pool)
    picked = []
    for s in pool:
        if sum(p["path"] == s["path"] for p in picked) < CORPUS_QUESTIONS_PER_PAGE:
            picked.append(s)
        if len(picked) == CORPUS_QUESTIONS_PER_CORPUS:
            break
    return [s | {"id": f"{name}-{i + 1:02d}"} for i, s in enumerate(picked)]


def ask(product: str, question: dict, section: dict, open_book: bool) -> tuple[str, str]:
    from llm_client import complete

    user = f"Question about {product}: {question['question']}\n\n"
    if open_book:
        user += f'Documentation section "{section["section"]}" (page "{section["page"]}"):\n'
        user += f"{section['text']}\n\n"
    reply = complete(
        [
            {"role": "system", "content": f"You are an expert on {product}."},
            {"role": "user", "content": user + TAIL},
        ]
    )
    return reply.text.strip(), reply.model


def answer(name: str) -> None:
    product = candidates()[name]["product"]
    questions = read_json(QUESTIONS_DIR / f"{name}.json")
    drawn = {s["id"]: s for s in read_json(QUESTIONS_DIR / f"{name}-sections.json")}
    jobs = [(q, ob) for q in questions for ob in (False, True)]
    with cf.ThreadPoolExecutor(CORPUS_PROBE_WORKERS) as pool:
        replies = list(pool.map(lambda j: ask(product, j[0], drawn[j[0]["id"]], j[1]), jobs))
    models = sorted({model for _, model in replies})
    if len(models) != 1:
        raise SystemExit(f"the replies name several models {models}; run again")
    for (q, open_book), (text, model) in zip(jobs, replies, strict=True):
        q["open" if open_book else "closed"] = text
        q["model"] = model
    write_json(QUESTIONS_DIR / f"{name}.json", questions)


def blind(names: list[str], batch: int) -> None:
    items = [
        (q["id"], run, {"question": q["question"], "reference": q["reference"], "answer": q[run]})
        for name in names
        for q in read_json(QUESTIONS_DIR / f"{name}.json")
        for run in ("closed", "open")
    ]
    random.Random(CORPUS_QUESTIONS_JUDGE_SEEDS[batch]).shuffle(items)
    write_json(
        QUESTIONS_DIR / "judge-input.json",
        [{"item": f"J{i + 1:03d}", **x} for i, (_, _, x) in enumerate(items)],
    )
    write_json(
        QUESTIONS_DIR / "judge-key.json",
        {f"J{i + 1:03d}": [qid, run] for i, (qid, run, _) in enumerate(items)},
    )


def unblind() -> None:
    key = read_json(QUESTIONS_DIR / "judge-key.json")
    verdicts = {}
    for row in read_json(QUESTIONS_DIR / "judge-output.json"):
        if row["verdict"] not in VERDICTS:
            raise ValueError(f"unknown verdict {row}")
        qid, run = key[row["item"]]
        verdicts[(qid, run)] = row["verdict"]
    for name in sorted({qid.rsplit("-", 1)[0] for qid, _ in verdicts}):
        questions = read_json(QUESTIONS_DIR / f"{name}.json")
        for q in questions:
            for run in ("closed", "open"):
                q[f"{run}_verdict"] = verdicts[(q["id"], run)]
        write_json(QUESTIONS_DIR / f"{name}.json", questions)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def summary() -> None:
    for path in sorted(QUESTIONS_DIR.glob("*.json")):
        if path.name.startswith("judge") or path.name.endswith("-sections.json"):
            continue
        questions = read_json(path)
        if "closed_verdict" not in questions[0]:
            continue
        closed = collections.Counter(q["closed_verdict"] for q in questions)
        posed = [q for q in questions if q["open_verdict"] == "correct"]
        dependent = sum(q["closed_verdict"] != "correct" for q in posed)
        lo, hi = wilson(dependent, len(posed))
        print(
            f"{path.stem:9} closed-book correct {closed['correct']}/{len(questions)} "
            f"{dict(closed)}; open-book correct {len(posed)}; retrieval-dependent "
            f"{dependent}/{len(posed)} = {dependent / len(posed):.0%} [{lo:.0%}, {hi:.0%}]"
        )


def main() -> None:
    load_dotenv()
    command, names = sys.argv[1], sys.argv[2:]
    if command == "sample":
        for name in names:
            write_json(QUESTIONS_DIR / f"{name}-sections.json", sample(name))
    elif command == "answer":
        for name in names:
            answer(name)
    elif command == "blind":
        blind(names[1:], int(names[0]))
    elif command == "unblind":
        unblind()
    elif command == "summary":
        summary()
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
