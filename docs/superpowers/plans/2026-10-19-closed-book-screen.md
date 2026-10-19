# Closed-book screen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every catalogue question is answered once without context; Jonas judges in the editor whether the answer hits
the core point; check and freeze enforce "screened, judged, at least 32 of 48 retrieval-dependent".

**Architecture:** A new module `src/closed_book.py` owns the CSV, the per-question state, the screen loop (with an
injected completer) and the check findings. `src/catalogue.py` gains the `screen` subcommand (API + run record) and
wires the findings into `check` and the counts into `freeze`. The editor gets a tab that only reads the CSV and writes
verdicts through `catalogue_store`.

**Tech Stack:** Python 3.12, uv, pytest, Streamlit 1.58 (AppTest), OpenAI SDK via `src/llm_client.py`.

**Spec:** `docs/superpowers/specs/2026-10-19-closed-book-screen-design.md`

## Global Constraints

- All parameters only in `src/config.py`; nothing hard-coded elsewhere (path, share, prompt text, verdict values).
- Tests never call the OpenAI API (fake completer; `llm_client.complete` is never reached in tests).
- Model, temperature 0, reasoning effort, seed and token limit of the screen are those of `llm_client.complete`.
- The editor never calls the API; the Write tab shows no model answers.
- Conventional Commits, German subjects, no AI attribution lines. Never commit `.env`.
- Claude writes no question, reference answer, key point or verdict; test data are synthetic.
- Docs in German (repo docs), code and comments in English, matching the surrounding files.

## Review Focus

1. A question edited after its verdict: the old verdict must not count; the next `screen` re-asks only that question
   (Task 2 `test_changed_question_is_asked_again_and_loses_its_verdict`).
2. Only the reference answer edited: the model answer stays, only the verdict is reopened
   (Task 2 `test_changed_reference_keeps_the_answer_and_reopens_the_verdict`).
3. A run that fails half-way (cut-off answer, API error): answers already received stay on disk and are logged
   (Task 2 `test_cut_off_answer_stops_and_keeps_earlier_answers`, Task 3 `test_cli_screen_logs_a_partial_run`).
4. Real data file present on disk while tests run: tests must not read `data/evaluation/closed_book_screen.csv`
   (Task 3 autouse fixture redirects `catalogue.CLOSED_BOOK_FILE`; `test_check_uses_the_redirected_screen_file`).
5. Judging after the freeze or judging a question whose text changed since screening: refused
   (Task 4 `test_judge_refuses_a_stale_question`, `test_closed_book_tab_is_read_only_when_frozen`).

---

### Task 1: Closed-book prompt and configuration

**Files:**
- Modify: `src/config.py` (file paths block near `CATALOGUE_REVIEW_FILE`; catalogue block after
  `CATALOGUE_REVIEW_DECISIONS`; prompt block after `CONTEXT_SEPARATOR`)
- Modify: `src/prompt.py`
- Modify: `docs/reference/prompts.md`
- Test: `tests/test_prompt.py`

**Interfaces:**
- Produces: `config.CLOSED_BOOK_FILE: Path`, `config.CLOSED_BOOK_VERDICTS = ("", "hit", "miss")`,
  `config.CLOSED_BOOK_MIN_DEPENDENT_SHARE = Fraction(2, 3)`, `config.CLOSED_BOOK_SYSTEM_PROMPT: str`,
  `config.CLOSED_BOOK_USER_TEMPLATE: str`, `prompt.closed_book_messages(question: str) -> list[dict]`.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_prompt.py`; extend the import lines)

```python
from config import (
    CLOSED_BOOK_SYSTEM_PROMPT,
    CLOSED_BOOK_USER_TEMPLATE,
    CONTEXT_SEPARATOR,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)
from prompt import closed_book_messages, context, messages


def test_closed_book_prompt_matches_the_documentation():
    """The closed-book prompt (screen and K0, ADR 0040) is documented right after the RAG prompt."""
    assert documented_blocks()[2:4] == [CLOSED_BOOK_SYSTEM_PROMPT, CLOSED_BOOK_USER_TEMPLATE]


def test_closed_book_messages_have_no_context_and_keep_braces():
    result = closed_book_messages("Is {context} a slot in {{ msg }}?")
    assert result[0] == {"role": "system", "content": CLOSED_BOOK_SYSTEM_PROMPT}
    assert result[1]["role"] == "user"
    assert result[1]["content"] == (
        "Answer the following question.\n\nQuestion: Is {context} a slot in {{ msg }}?\n\nAnswer:"
    )
    assert "excerpt" not in result[0]["content"].lower() + result[1]["content"].lower()
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_prompt.py -q`
Expected: FAIL / ERROR with `ImportError: cannot import name 'CLOSED_BOOK_SYSTEM_PROMPT'`.

- [ ] **Step 3: Add the configuration** (`src/config.py`)

At the top, next to the other imports (add the import if the file has none):

```python
from fractions import Fraction
```

In the file paths block, directly after `CATALOGUE_REVIEW_FILE = (...)`:

```python
CLOSED_BOOK_FILE = (
    DATA_EVAL / "closed_book_screen.csv"
)  # answers without context and Jonas' verdicts (D38, D40)
```

In the catalogue block, directly after `CATALOGUE_REVIEW_DECISIONS = (...)`:

```python
# Closed-book screen (D38, D40): "" = not judged, "hit" = the answer without context hits the core
# point of the reference answer (retrieval-independent), "miss" = it does not or only partly.
CLOSED_BOOK_VERDICTS = ("", "hit", "miss")
CLOSED_BOOK_MIN_DEPENDENT_SHARE = Fraction(2, 3)  # at least this share retrieval-dependent (D38)
```

In the prompt block, directly after `CONTEXT_SEPARATOR = ...`:

```python
# Closed-book prompt (docs/reference/prompts.md): the screen of the catalogue and the control K0
# (D38, D40); the RAG prompt without excerpts, so the model may answer from its own knowledge.
CLOSED_BOOK_SYSTEM_PROMPT = """You are a helpful assistant that answers questions about the e2e testing framework.
If you do not know the answer, state that explicitly."""  # noqa: E501 (verbatim prompt text)
CLOSED_BOOK_USER_TEMPLATE = """Answer the following question.

Question: {question}

Answer:"""
```

- [ ] **Step 4: Add `closed_book_messages`** (`src/prompt.py`)

Docstring first line becomes: `"""The prompts of the answer generation (docs/reference/prompts.md): the RAG prompt, the same
for every strategy (ADR 0006), and the closed-book prompt of the screen and K0 (ADR 0040). The scoring packet shows the
excerpts in the same form (ADR 0032)."""`. Import line:

```python
from config import (
    CLOSED_BOOK_SYSTEM_PROMPT,
    CLOSED_BOOK_USER_TEMPLATE,
    CONTEXT_SEPARATOR,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)
```

Append:

```python
def closed_book_messages(question: str) -> list[dict]:
    """System and user message without any excerpt (screen and K0, ADR 0040); braces stay."""
    user = CLOSED_BOOK_USER_TEMPLATE.format(question=question)
    return [
        {"role": "system", "content": CLOSED_BOOK_SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
```

- [ ] **Step 5: Document the prompt** (`docs/reference/prompts.md`)

Insert after the paragraph that ends "Geschweifte Klammern in Frage oder Chunk bleiben unverändert." and before
"## Parameter":

````markdown
## Closed-Book-Prompt (Prüfung und K0)

Ohne Ausschnitte beantwortet das Antwortmodell jede Katalogfrage bei der Closed-Book-Prüfung und in der Kontrolle K0
([ADR 0038](../adr/0038-korpus-e2e.md), [ADR 0040](../adr/0040-closed-book-pruefung.md)). Der RAG-Prompt ohne
Kontext ließe das Modell nur ablehnen; dieser Prompt ist derselbe ohne Ausschnitte und ohne die Bindung an sie.

```
You are a helpful assistant that answers questions about the e2e testing framework.
If you do not know the answer, state that explicitly.
```

```
Answer the following question.

Question: {question}

Answer:
```
````

In "## Parameter", change the first sentence to: "Konstant für alle Strategien, die Closed-Book-Prüfung und K0:".

- [ ] **Step 6: Run the tests**

Run: `uv run pytest tests/test_prompt.py -q`
Expected: all pass (6 tests).

- [ ] **Step 7: Commit**

```bash
git add src/config.py src/prompt.py docs/reference/prompts.md tests/test_prompt.py
git commit -m "feat(prompt): Closed-Book-Prompt für Prüfung und K0"
```

---

### Task 2: `src/closed_book.py`

**Files:**
- Create: `src/closed_book.py`
- Test: `tests/test_closed_book.py`

**Interfaces:**
- Consumes: Task 1 config names and `prompt.closed_book_messages`; `atomic_csv.read_csv/write_csv`;
  `llm_client.Completer`, `llm_client.Completion`.
- Produces:
  - `SCREEN_HEADER: list[str]`, `NOT_SCREENED = "not screened"`, `NOT_JUDGED = "not judged"`
  - `text_sha256(text: str) -> str`
  - `read_screen(path: Path) -> list[dict]`, `save_screen(path: Path, rows: list[dict]) -> None`
  - `min_dependent(n_questions: int) -> int`
  - `status(row: dict | None, question: str, reference: str) -> str` → `NOT_SCREENED | NOT_JUDGED | "hit" | "miss"`
  - `states(rows, questions, truth) -> dict[str, str]` (question_id → state, catalogue order)
  - `screen(questions, truth, completer, path, done: list[Completion]) -> None`
  - `judge(path, question_id, question, reference, verdict, note, today) -> dict`
  - `findings(rows, questions, truth, n_quota) -> tuple[list[str], list[str]]` (errors, findings)
  - `counts(rows, questions, truth) -> dict[str, int]` with keys `dependent`, `known`, `not_screened`, `not_judged`
  - `summary(counts: dict, n_quota: int) -> str`
  - `questions` is a list of dicts with `question_id`, `question`; `truth` maps question_id → dict with
    `expected_answer`.

- [ ] **Step 1: Write the failing tests** (`tests/test_closed_book.py`)

```python
import pytest

import closed_book
from closed_book import (
    NOT_JUDGED,
    NOT_SCREENED,
    SCREEN_HEADER,
    counts,
    findings,
    judge,
    min_dependent,
    read_screen,
    save_screen,
    screen,
    states,
    status,
    summary,
    text_sha256,
)
from llm_client import Completion


class FakeCompleter:
    """Answers from a list; records each request (no network)."""

    def __init__(self, finish_reasons=None):
        self.calls: list[list[dict]] = []
        self.finish_reasons = finish_reasons or {}  # call number -> finish_reason

    def __call__(self, messages: list[dict]) -> Completion:
        self.calls.append(messages)
        number = len(self.calls)
        return Completion(
            text=f"  Guess {number}.  ",
            model="gpt-6-luna-2026-05-18",
            finish_reason=self.finish_reasons.get(number, "stop"),
            prompt_tokens=50 + number,
            completion_tokens=10 + number,
            system_fingerprint="fp_a",
        )


def catalogue(n=3):
    questions = [{"question_id": f"Q{i:03d}", "question": f"Question {i}?"} for i in range(1, n + 1)]
    truth = {q["question_id"]: {"expected_answer": f"Answer {q['question_id']}."} for q in questions}
    return questions, truth


def run(path, questions, truth, completer=None):
    done: list[Completion] = []
    screen(questions, truth, completer or FakeCompleter(), path, done)
    return done


def test_min_dependent_rounds_up_two_thirds():
    assert min_dependent(48) == 32 and min_dependent(3) == 2 and min_dependent(4) == 3


def test_status_of_a_question():
    q, ref = "Question 1?", "Answer."
    assert status(None, q, ref) == NOT_SCREENED
    row = dict.fromkeys(SCREEN_HEADER, "") | {"question_sha256": text_sha256(q)}
    assert status(row, q, ref) == NOT_JUDGED
    row |= {"core_point": "hit", "reference_sha256": text_sha256(ref)}
    assert status(row, q, ref) == "hit"
    assert status(row, q, "Changed answer.") == NOT_JUDGED
    assert status(row, "Changed question?", ref) == NOT_SCREENED


def test_screen_answers_every_question_once_with_the_closed_book_prompt(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    fake = FakeCompleter()
    done = run(path, questions, truth, fake)
    assert len(done) == 3 and len(fake.calls) == 3
    assert fake.calls[0][1]["content"].endswith("Question: Question 1?\n\nAnswer:")
    rows = read_screen(path)
    assert [r["question_id"] for r in rows] == ["Q001", "Q002", "Q003"]
    assert rows[0]["answer"] == "Guess 1." and rows[0]["model"] == "gpt-6-luna-2026-05-18"
    assert rows[0]["core_point"] == "" and rows[0]["reference_sha256"] == ""
    assert run(path, questions, truth, fake) == [] and len(fake.calls) == 3  # nothing left to ask


def test_changed_question_is_asked_again_and_loses_its_verdict(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    run(path, questions, truth)
    judge(path, "Q002", "Question 2?", "Answer Q002.", "hit", "knows it", "2026-10-21")
    questions[1]["question"] = "Question 2, rephrased?"
    fake = FakeCompleter()
    assert len(run(path, questions, truth, fake)) == 1
    row = next(r for r in read_screen(path) if r["question_id"] == "Q002")
    assert row["question_sha256"] == text_sha256("Question 2, rephrased?")
    assert row["core_point"] == "" and row["note"] == "" and row["date"] == ""
    assert states(read_screen(path), questions, truth)["Q002"] == NOT_JUDGED


def test_changed_reference_keeps_the_answer_and_reopens_the_verdict(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    run(path, questions, truth)
    judge(path, "Q001", "Question 1?", "Answer Q001.", "miss", "", "2026-10-21")
    truth["Q001"]["expected_answer"] = "A better answer."
    fake = FakeCompleter()
    assert run(path, questions, truth, fake) == [] and fake.calls == []
    assert states(read_screen(path), questions, truth)["Q001"] == NOT_JUDGED
    assert read_screen(path)[0]["answer"] == "Guess 1."


def test_rows_of_removed_questions_disappear(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    run(path, questions, truth)
    run(path, questions[:2], truth)
    assert [r["question_id"] for r in read_screen(path)] == ["Q001", "Q002"]


def test_cut_off_answer_stops_and_keeps_earlier_answers(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    done: list[Completion] = []
    with pytest.raises(RuntimeError, match="Q002.*finish_reason='length'"):
        screen(questions, truth, FakeCompleter({2: "length"}), path, done)
    assert [r["question_id"] for r in read_screen(path)] == ["Q001"]
    assert len(done) == 1


def test_judge_records_the_verdict_and_the_reference_hash(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    run(path, questions, truth)
    row = judge(path, "Q003", "Question 3?", "Answer Q003.", "hit", " partly known ", "2026-10-21")
    assert row["core_point"] == "hit" and row["note"] == "partly known"
    assert row["reference_sha256"] == text_sha256("Answer Q003.") and row["date"] == "2026-10-21"
    assert states(read_screen(path), questions, truth)["Q003"] == "hit"


def test_judge_refuses_unknown_verdicts_and_unscreened_questions(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    run(path, questions, truth)
    with pytest.raises(ValueError, match="hit or miss"):
        judge(path, "Q001", "Question 1?", "Answer Q001.", "", "", "2026-10-21")
    with pytest.raises(ValueError, match="Q009 is not screened"):
        judge(path, "Q009", "Question 9?", "Answer.", "hit", "", "2026-10-21")


def test_judge_refuses_a_stale_question(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    run(path, questions, truth)
    with pytest.raises(ValueError, match="changed since it was screened"):
        judge(path, "Q001", "Question 1, edited?", "Answer Q001.", "miss", "", "2026-10-21")


def test_findings_warn_about_unscreened_unjudged_and_too_many_hits(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue(4)
    run(path, questions[:3], truth)
    judge(path, "Q001", "Question 1?", "Answer Q001.", "hit", "", "2026-10-21")
    judge(path, "Q002", "Question 2?", "Answer Q002.", "hit", "", "2026-10-21")
    errors, found = findings(read_screen(path), questions, truth, n_quota=4)
    assert errors == []
    assert "closed-book: not screened Q004; run `catalogue.py screen` (ADR 0040)" in found
    assert "closed-book: not judged Q003; judge it in the editor tab Closed-book" in found
    assert "closed-book: 2 questions hit without context, at most 1 of 4 (ADR 0038)" in found


def test_findings_errors_for_unknown_questions_and_verdicts(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue()
    run(path, questions, truth)
    rows = read_screen(path)
    rows[0]["core_point"] = "maybe"
    save_screen(path, rows)
    errors, _ = findings(read_screen(path), questions[1:], truth, n_quota=3)
    assert "closed-book row Q001: question is not in the catalogue" in errors
    assert "closed-book row Q001: unknown core_point 'maybe'" in errors


def test_counts_and_summary(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    questions, truth = catalogue(4)
    run(path, questions[:3], truth)
    judge(path, "Q001", "Question 1?", "Answer Q001.", "hit", "", "2026-10-21")
    judge(path, "Q002", "Question 2?", "Answer Q002.", "miss", "", "2026-10-21")
    c = counts(read_screen(path), questions, truth)
    assert c == {"dependent": 1, "known": 1, "not_screened": 1, "not_judged": 1}
    assert summary(c, 48) == (
        "Closed-book: 1 retrieval-dependent (at least 32), 1 known, 1 not screened, 1 not judged"
    )


def test_read_screen_rejects_wrong_columns_and_duplicates(tmp_path):
    path = tmp_path / "closed_book_screen.csv"
    path.write_text("question_id,answer\nQ001,x\n", encoding="utf-8")
    with pytest.raises(ValueError, match="columns"):
        read_screen(path)
    row = ",".join(["Q001", *[""] * (len(SCREEN_HEADER) - 1)])
    path.write_text(",".join(SCREEN_HEADER) + f"\n{row}\n{row}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate question_id"):
        read_screen(path)


def test_missing_file_has_no_rows(tmp_path):
    assert read_screen(tmp_path / "none.csv") == []
    assert closed_book.CLOSED_BOOK_VERDICTS == ("", "hit", "miss")
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_closed_book.py -q`
Expected: ERROR `ModuleNotFoundError: No module named 'closed_book'`.

- [ ] **Step 3: Implement `src/closed_book.py`**

```python
"""Closed-book screen of the question catalogue (ADR 0038, 0040).

`catalogue.py screen` lets the answer model answer every catalogue question once without any
context (prompt.closed_book_messages); Jonas judges in the editor whether that answer hits the
core point of his reference answer. A question it hits is retrieval-independent and stays marked
in the catalogue. Each row keeps the SHA-256 of the question the answer belongs to and of the
reference answer the verdict belongs to, so an edit reopens exactly what it affects. Reads only
the catalogue, never chunks or retrieval results (ADR 0027).
"""

import hashlib
import math
from pathlib import Path

from atomic_csv import read_csv, write_csv
from config import CLOSED_BOOK_MIN_DEPENDENT_SHARE, CLOSED_BOOK_VERDICTS
from llm_client import Completer, Completion
from prompt import closed_book_messages

SCREEN_HEADER = [
    "question_id", "question_sha256", "reference_sha256", "answer", "model", "core_point",
    "note", "date",
]  # fmt: skip
NOT_SCREENED = "not screened"
NOT_JUDGED = "not judged"


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_screen(path: Path) -> list[dict]:
    """Rows of the screen file; a missing file has none."""
    rows = read_csv(path, SCREEN_HEADER)
    ids = [r["question_id"] for r in rows]
    repeated = sorted({qid for qid in ids if ids.count(qid) > 1})
    if repeated:
        raise ValueError(f"{path}: duplicate question_id {repeated}")
    return rows


def save_screen(path: Path, rows: list[dict]) -> None:
    """Atomic write, rows sorted by question_id (deterministic)."""
    write_csv(path, SCREEN_HEADER, sorted(rows, key=lambda r: r["question_id"]))


def min_dependent(n_questions: int) -> int:
    return math.ceil(CLOSED_BOOK_MIN_DEPENDENT_SHARE * n_questions)


def _reference(truth: dict, question_id: str) -> str:
    return truth.get(question_id, {}).get("expected_answer", "")


def status(row: dict | None, question: str, reference: str) -> str:
    if row is None or row["question_sha256"] != text_sha256(question):
        return NOT_SCREENED
    if not row["core_point"] or row["reference_sha256"] != text_sha256(reference):
        return NOT_JUDGED
    return row["core_point"]


def states(rows: list[dict], questions: list[dict], truth: dict) -> dict[str, str]:
    by_id = {r["question_id"]: r for r in rows}
    return {
        q["question_id"]: status(
            by_id.get(q["question_id"]), q["question"], _reference(truth, q["question_id"])
        )
        for q in questions
    }


def screen(
    questions: list[dict],
    truth: dict,
    completer: Completer,
    path: Path,
    done: list[Completion],
) -> None:
    """Answer every question without a current answer; save after each answer.

    Rows of questions no longer in the catalogue are dropped. Every reply is appended to `done`,
    so the caller can log a run that stops half-way.
    """
    keep = {q["question_id"] for q in questions}
    rows = {r["question_id"]: r for r in read_screen(path) if r["question_id"] in keep}
    save_screen(path, list(rows.values()))
    for q in questions:
        qid = q["question_id"]
        if status(rows.get(qid), q["question"], _reference(truth, qid)) != NOT_SCREENED:
            continue
        reply = completer(closed_book_messages(q["question"]))
        if reply.finish_reason != "stop" or not reply.text.strip():
            raise RuntimeError(
                f"{qid}: the answer ended with finish_reason={reply.finish_reason!r} or is empty; "
                "the answers before it are saved (ADR 0040)"
            )
        done.append(reply)
        rows[qid] = dict.fromkeys(SCREEN_HEADER, "") | {
            "question_id": qid,
            "question_sha256": text_sha256(q["question"]),
            "answer": reply.text.strip(),
            "model": reply.model,
        }
        save_screen(path, list(rows.values()))


def judge(
    path: Path,
    question_id: str,
    question: str,
    reference: str,
    verdict: str,
    note: str,
    today: str,
) -> dict:
    """Record Jonas' verdict for the current question text and reference answer."""
    if verdict not in CLOSED_BOOK_VERDICTS or not verdict:
        raise ValueError("the verdict must be hit or miss")
    rows = read_screen(path)
    row = next((r for r in rows if r["question_id"] == question_id), None)
    if row is None:
        raise ValueError(f"{question_id} is not screened; run `catalogue.py screen`")
    if row["question_sha256"] != text_sha256(question):
        raise ValueError(f"{question_id} changed since it was screened; run `catalogue.py screen`")
    row.update(
        core_point=verdict,
        note=note.strip(),
        reference_sha256=text_sha256(reference),
        date=today,
    )
    save_screen(path, rows)
    return row


def counts(rows: list[dict], questions: list[dict], truth: dict) -> dict[str, int]:
    found = list(states(rows, questions, truth).values())
    return {
        "dependent": found.count("miss"),
        "known": found.count("hit"),
        "not_screened": found.count(NOT_SCREENED),
        "not_judged": found.count(NOT_JUDGED),
    }


def findings(
    rows: list[dict], questions: list[dict], truth: dict, n_quota: int
) -> tuple[list[str], list[str]]:
    """Errors (malformed rows) and findings (open work, too many hits) of the screen."""
    known_ids = {q["question_id"] for q in questions}
    errors = []
    for r in rows:
        if r["question_id"] not in known_ids:
            errors.append(f"closed-book row {r['question_id']}: question is not in the catalogue")
        if r["core_point"] not in CLOSED_BOOK_VERDICTS:
            errors.append(
                f"closed-book row {r['question_id']}: unknown core_point {r['core_point']!r}"
            )
    found = states(rows, questions, truth)
    result = []
    unscreened = [qid for qid, s in found.items() if s == NOT_SCREENED]
    if unscreened:
        result.append(
            f"closed-book: not screened {', '.join(unscreened)}; run `catalogue.py screen` "
            "(ADR 0040)"
        )
    unjudged = [qid for qid, s in found.items() if s == NOT_JUDGED]
    if unjudged:
        result.append(
            f"closed-book: not judged {', '.join(unjudged)}; judge it in the editor tab Closed-book"
        )
    hits = sum(1 for s in found.values() if s == "hit")
    allowed = n_quota - min_dependent(n_quota)
    if hits > allowed:
        result.append(
            f"closed-book: {hits} questions hit without context, at most {allowed} of {n_quota} "
            "(ADR 0038)"
        )
    return errors, result


def summary(c: dict[str, int], n_quota: int) -> str:
    return (
        f"Closed-book: {c['dependent']} retrieval-dependent (at least {min_dependent(n_quota)}), "
        f"{c['known']} known, {c['not_screened']} not screened, {c['not_judged']} not judged"
    )
```

Note for the implementer: the test `test_missing_file_has_no_rows` reads `closed_book.CLOSED_BOOK_VERDICTS`; the
`from config import ...` line above makes it a module attribute. The spec's strict row "fewer than 32 judged `miss`"
needs no rule of its own: in the strict check every unscreened or unjudged question is already a finding, and with
all 48 judged, "at most 16 hits" is the same condition.

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_closed_book.py -q`
Expected: all pass (15 tests). Then `uvx pre-commit run --files src/closed_book.py tests/test_closed_book.py`
(ruff may reflow lines; rerun the tests if it changed anything).

- [ ] **Step 5: Commit**

```bash
git add src/closed_book.py tests/test_closed_book.py
git commit -m "feat(catalogue): Closed-Book-Prüfung: Datei, Zustände, Lauf und Befunde"
```

---

### Task 3: `catalogue.py screen`, check and freeze

**Files:**
- Modify: `src/catalogue.py` (imports; docstring command list; `check`; `freeze_catalogue`; new `run_screen`; `main`)
- Modify: `tests/conftest.py` (autouse redirect, `write_screen_for`)
- Modify: `tests/test_catalogue.py` (`run_check`, new tests)
- Modify: `tests/test_freeze.py` (fixture, expected record)

**Interfaces:**
- Consumes: everything Task 2 produces; `config.CLOSED_BOOK_FILE`, `config.GENERATION_RUNS_FILE`;
  `run_log.append_generation_run(record, prompt_tokens, completion_tokens, runs_file)`, `run_log.sha256_of`;
  `llm_client.complete`.
- Produces: `catalogue.check(..., closed_book_file: Path | None = None)`,
  `catalogue.freeze_catalogue(..., closed_book_file: Path | None = None)` (both resolve `None` to the module global
  `catalogue.CLOSED_BOOK_FILE` at call time), `catalogue.run_screen(completer=complete,
  runs_file=GENERATION_RUNS_FILE) -> int`; freeze record key `"closed_book": {"dependent": int, "known": int}`;
  `conftest.write_screen_for(path, rows, hits=0) -> Path`.

- [ ] **Step 1: Test helpers** (`tests/conftest.py`)

Add to the imports: `import closed_book`. Add after the `test_area_minimums` fixture:

```python
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
```

- [ ] **Step 2: Write the failing tests**

In `tests/test_catalogue.py`, import `write_screen_for` from conftest, and change `run_check` to take the screen file:

```python
def run_check(corpus, tmp_path, rows, pilot_dir, screen=True):
    questions, truth = write_catalogue(tmp_path, rows)
    plan = write_plan_for(tmp_path, rows)
    review = tmp_path / "catalogue_review.csv"
    ensure_review_file(review)
    if screen:
        write_screen_for(tmp_path / "closed_book_screen.csv", rows)
    return check(
        corpus,
        questions,
        truth,
        pilot_dir=pilot_dir,
        plan_file=plan,
        review_file=review,
        fresh_plan=fresh_plan_for(rows),
    )
```

In `test_valid_catalogue_passes_strictly` add:
`assert "Closed-book: 48 retrieval-dependent (at least 32), 0 known, 0 not screened, 0 not judged" in report.lines`.

Append:

```python
def test_unscreened_catalogue_warns_in_draft_and_fails_strictly(corpus, tmp_path, pilot):
    report = run_check(corpus, tmp_path, valid_rows(), pilot, screen=False)
    assert report.errors == []
    assert any(f.startswith("closed-book: not screened Q001, Q002") for f in report.findings)
    assert exit_code(report, draft=True) == 0 and exit_code(report, draft=False) == 1


def test_too_many_hits_is_a_finding(corpus, tmp_path, pilot):
    rows = valid_rows()
    write_screen_for(tmp_path / "closed_book_screen.csv", rows, hits=17)
    report = run_check(corpus, tmp_path, rows, pilot, screen=False)
    assert "closed-book: 17 questions hit without context, at most 16 of 48 (ADR 0038)" in (
        report.findings
    )


def test_malformed_screen_file_is_an_error(corpus, tmp_path, pilot):
    (tmp_path / "closed_book_screen.csv").write_text("id,text\n", encoding="utf-8")
    report = run_check(corpus, tmp_path, valid_rows(), pilot, screen=False)
    assert any("closed_book_screen.csv has columns" in e for e in report.errors)


def test_check_uses_the_redirected_screen_file(closed_book_file, tmp_path):
    assert catalogue.CLOSED_BOOK_FILE == closed_book_file == tmp_path / "closed_book_screen.csv"


def test_cli_screen_answers_and_logs_a_run(cli, tmp_path):
    write_catalogue(tmp_path, valid_rows()[:2])  # the cli fixture's files, now two questions
    runs = tmp_path / "generation_runs.jsonl"
    assert catalogue.run_screen(completer=FakeCompleter(), runs_file=runs) == 0
    record = json.loads(runs.read_text(encoding="utf-8"))
    assert record["step"] == "closed_book_screen" and record["answers"] == 2
    assert record["prompt_tokens"] == 51 + 52 and record["completion_tokens"] == 11 + 12
    assert set(record["outputs_sha256"]) == {"closed_book_screen.csv"}


def test_cli_screen_logs_a_partial_run(cli, tmp_path, capsys):
    write_catalogue(tmp_path, valid_rows()[:3])
    runs = tmp_path / "generation_runs.jsonl"
    assert catalogue.run_screen(completer=FakeCompleter({2: "length"}), runs_file=runs) == 1
    assert "Q002" in capsys.readouterr().err
    assert json.loads(runs.read_text(encoding="utf-8"))["answers"] == 1


def test_cli_screen_refuses_after_the_freeze(cli, tmp_path, capsys):
    (tmp_path / "freeze.json").write_text("{}", encoding="utf-8")  # cli's CATALOGUE_FREEZE_FILE
    assert catalogue.run_screen(completer=FakeCompleter(), runs_file=tmp_path / "r.jsonl") == 1
    assert "frozen" in capsys.readouterr().err
```

Add to the imports of `tests/test_catalogue.py`: `import json` (top), `write_screen_for` in the conftest import, and
`from test_closed_book import FakeCompleter` (pytest puts `tests/` on `sys.path`, as for `conftest`). The `cli`
fixture (existing, `tests/test_catalogue.py`) already redirects `QUESTIONS_FILE`, `GROUND_TRUTH_FILE` and
`CATALOGUE_FREEZE_FILE` to `tmp_path`; the autouse fixture redirects `CLOSED_BOOK_FILE`.

In `tests/test_freeze.py`: import `write_screen_for` from conftest; in the `main_catalogue` fixture add
`write_screen_for(tmp_path / "closed_book_screen.csv", valid_rows())` before `return`. In
`test_freeze_writes_hashes_counts_and_date` add `"closed_book_screen.csv": sha256_of(tmp_path / "closed_book_screen.csv"),`
to the expected `sha256` dict and change the last line to:

```python
    assert stored["closed_book"] == {"dependent": 48, "known": 0}
    assert set(stored) == {"date", "questions", "types", "classes", "closed_book", "sha256"}
```

Append to `tests/test_freeze.py`:

```python
def test_freeze_refuses_too_many_hits(corpus, main_catalogue, pilot, tmp_path):
    questions, truth, sections, documents = main_catalogue
    write_screen_for(tmp_path / "closed_book_screen.csv", valid_rows(), hits=17)
    out = tmp_path / "catalogue_freeze.json"
    with pytest.raises(ValueError, match="strict check"):
        freeze_catalogue(
            corpus,
            questions,
            truth,
            out,
            pilot,
            sections,
            documents,
            plan_file=write_plan_for(tmp_path, valid_rows()),
            review_file=tmp_path / "catalogue_review.csv",
            fresh_plan=fresh_plan_for(valid_rows()),
        )
    assert not out.exists()
```

- [ ] **Step 3: Run them to verify they fail**

Run: `uv run pytest tests/test_catalogue.py tests/test_freeze.py -q`
Expected: FAIL — the new closed-book findings/lines are missing and `run_screen` does not exist.

- [ ] **Step 4: Implement in `src/catalogue.py`**

Docstring command list, after the `freeze` line:
`    screen              answer every new or changed question without context (ADR 0040; calls the API)`.

Imports: add `import closed_book`; from config add `CLOSED_BOOK_FILE` and `GENERATION_RUNS_FILE`; add
`from llm_client import Completer, Completion, complete` and `from run_log import append_generation_run, sha256_of`.

In `check`, new last parameter `closed_book_file: Path | None = None`; directly before
`plan_lines.append(review_summary(review))` insert:

```python
    n_quota = sum(QUESTION_TYPES.values())
    try:
        screen_rows = closed_book.read_screen(closed_book_file or CLOSED_BOOK_FILE)
    except ValueError as error:
        report.errors.append(str(error))
        screen_rows = []
    errors, findings = closed_book.findings(screen_rows, questions, truth, n_quota)
    report.errors += errors
    report.findings += findings
    report.closed_book = closed_book.counts(screen_rows, questions, truth)
    plan_lines.append(closed_book.summary(report.closed_book, n_quota))
```

In the `Report` dataclass add `closed_book: dict[str, int] = field(default_factory=dict)`.

In `freeze_catalogue`, new last parameter `closed_book_file: Path | None = None`; resolve it first
(`closed_book_file = closed_book_file or CLOSED_BOOK_FILE`), pass it to `check(...)` as keyword, add to `summary`:

```python
        "closed_book": {k: report.closed_book[k] for k in ("dependent", "known")},
```

and record the file: `recorded = tuple(p for p in (plan_file, review_file, closed_book_file) if p.exists())`.

New function before `main`:

```python
def run_screen(completer: Completer = complete, runs_file: Path = GENERATION_RUNS_FILE) -> int:
    """`screen`: closed-book answers for new or changed questions, then one run record (ADR 0040)."""
    if CATALOGUE_FREEZE_FILE.exists():
        print("the catalogue is frozen (ADR 0030); the screen is final", file=sys.stderr)
        return 1
    try:
        questions = read_rows(
            QUESTIONS_FILE, "question catalogue", QUESTIONS_HEADER, QUESTIONS_REQUIRED
        )
        truth_rows = read_rows(
            GROUND_TRUTH_FILE, "ground truth", GROUND_TRUTH_HEADER, GROUND_TRUTH_HEADER
        )
    except (FileNotFoundError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    questions.sort(key=lambda q: q["question_id"])
    truth = {row["question_id"]: row for row in truth_rows}
    done: list[Completion] = []
    code = 0
    try:
        closed_book.screen(questions, truth, completer, CLOSED_BOOK_FILE, done)
    except Exception as error:  # API errors included: log what was paid for, then stop
        print(error, file=sys.stderr)
        code = 1
    if done:
        append_generation_run(
            {
                "step": "closed_book_screen",
                "answers": len(done),
                "model_reported": sorted({d.model for d in done}),
                "system_fingerprint": sorted({d.system_fingerprint or "" for d in done}),
                "outputs_sha256": {CLOSED_BOOK_FILE.name: sha256_of(CLOSED_BOOK_FILE)},
            },
            sum(d.prompt_tokens for d in done),
            sum(d.completion_tokens for d in done),
            runs_file,
        )
    print(f"{len(done)} questions answered without context -> {CLOSED_BOOK_FILE}")
    return code
```

In `main`: add `commands.add_parser("screen", help="closed-book answers of new or changed questions (ADR 0040)")`
after the `plan` parser, and before `corpus = load_corpus(...)`:

```python
    if args.command == "screen":
        return run_screen()
```

Pass `closed_book_file=CLOSED_BOOK_FILE` explicitly in `main`'s calls of `check(...)` and `freeze_catalogue(...)`
(the module global, which the autouse fixture redirects in tests).

Note: `QUESTIONS_FILE`, `GROUND_TRUTH_FILE`, `CATALOGUE_FREEZE_FILE` and `CLOSED_BOOK_FILE` must be read as module
globals at call time inside `run_screen` (no default arguments), so the tests' `monkeypatch.setattr(module, ...)`
works.

- [ ] **Step 5: Run the tests**

Run: `uv run pytest tests/test_catalogue.py tests/test_freeze.py tests/test_closed_book.py -q`
Expected: all pass.

- [ ] **Step 6: Full suite and lint**

Run: `uv run pytest -q > "$WS/suite.txt" 2>&1; tail -3 "$WS/suite.txt"` and `uvx pre-commit run --all-files`
Expected: all pass (603 before this plan plus the new tests); pre-commit clean. A failing older test that calls
`check(...)`/`freeze_catalogue(...)` strictly without a screen file gets `write_screen_for(...)` in its setup (ledger a
ruling for each).

- [ ] **Step 7: Commit**

```bash
git add src/catalogue.py tests/conftest.py tests/test_catalogue.py tests/test_freeze.py
git commit -m "feat(catalogue): Befehl screen, Closed-Book-Befunde in Prüfung und Einfrieren"
```

---

### Task 4: Editor tab "Closed-book"

**Files:**
- Modify: `src/catalogue_store.py` (import `CLOSED_BOOK_FILE`, `closed_book`; new `judge_closed_book`)
- Modify: `app/catalogue_page.py` (sidebar line, new `closed_book_tab`, `main`)
- Modify: `app/ui_theme.py` (`CSS`: two rules)
- Test: `tests/test_catalogue_editor.py`

**Interfaces:**
- Consumes: `closed_book.read_screen`, `states`, `counts`, `summary`, `NOT_JUDGED`, `NOT_SCREENED`, `judge`.
- Produces: `catalogue_store.CLOSED_BOOK_FILE` (module global, patched by tests),
  `catalogue_store.judge_closed_book(question_id: str, verdict: str, note: str, today: str) -> dict`.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_catalogue_editor.py`; in the `app` fixture add
  `"CLOSED_BOOK_FILE": tmp_path / "closed_book_screen.csv",` to `paths`)

```python
def save_and_screen(at, paths):
    """Write Q001 through the editor, then screen it with a fake completer."""
    import closed_book
    from test_closed_book import FakeCompleter

    at.text_area(key="question_S01").input("What does it return?")
    at.text_area(key="answer_S01").input("A reactive ref object.")
    at.button(key="save").click().run()
    questions, truth = store.load_catalogue()
    closed_book.screen(questions, truth, FakeCompleter(), paths["CLOSED_BOOK_FILE"], [])
    at.run()


def test_closed_book_tab_asks_to_screen_first(app):
    at, _ = app
    at.text_area(key="question_S01").input("What does it return?")
    at.text_area(key="answer_S01").input("A ref.")
    at.button(key="save").click().run()
    assert any("catalogue.py screen" in i.value for i in at.info)


def test_closed_book_verdict_is_saved(app):
    import closed_book

    at, paths = app
    save_and_screen(at, paths)
    assert any("Guess 1." in h.proto.body for h in at.get("html"))
    at.text_input(key="cb_note_Q001").input("knows the return value")
    at.button(key="cb_hit_Q001").click().run()
    assert not at.exception
    row = closed_book.read_screen(paths["CLOSED_BOOK_FILE"])[0]
    assert row["core_point"] == "hit" and row["note"] == "knows the return value"
    assert any("0 retrieval-dependent (at least 32), 1 known" in c.value for c in at.sidebar.caption)


def test_a_verdict_can_be_changed(app):
    import closed_book

    at, paths = app
    save_and_screen(at, paths)
    at.button(key="cb_miss_Q001").click().run()
    at.button(key="cb_flip_Q001").click().run()
    assert not at.exception
    assert closed_book.read_screen(paths["CLOSED_BOOK_FILE"])[0]["core_point"] == "hit"


def test_closed_book_tab_is_read_only_when_frozen(app):
    at, paths = app
    save_and_screen(at, paths)
    paths["CATALOGUE_FREEZE_FILE"].write_text("{}", encoding="utf-8")
    at.run()
    assert at.button(key="cb_hit_Q001").disabled and at.button(key="cb_miss_Q001").disabled


def test_judge_closed_book_refuses_after_the_freeze(app):
    at, paths = app
    save_and_screen(at, paths)
    paths["CATALOGUE_FREEZE_FILE"].write_text("{}", encoding="utf-8")
    with pytest.raises(PermissionError, match="frozen"):
        store.judge_closed_book("Q001", "hit", "", "2026-10-21")


def test_write_tab_shows_no_model_answer(app):
    at, paths = app
    save_and_screen(at, paths)
    at.selectbox(key="slot").select("S01").run()
    write_tab_html = [h.proto.body for h in at.tabs[0].get("html")]
    assert not any("Guess 1." in body for body in write_tab_html)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_catalogue_editor.py -q`
Expected: the six new tests FAIL (no tab, no `judge_closed_book`, no `cb_*` keys).

- [ ] **Step 3: Store wrapper** (`src/catalogue_store.py`)

Add `import closed_book` (after `from catalogue_review import ...`) and `CLOSED_BOOK_FILE` to the config import.
Append after `reject_suggestion`:

```python
def judge_closed_book(question_id: str, verdict: str, note: str, today: str) -> dict:
    """Jonas' closed-book verdict for the current question and reference (ADR 0040)."""
    _refuse_if_frozen()
    questions, truth = load_catalogue()
    question = next((q for q in questions if q["question_id"] == question_id), None)
    if question is None:
        raise ValueError(f"{question_id} is not in the catalogue")
    reference = truth.get(question_id, {}).get("expected_answer", "")
    return closed_book.judge(
        CLOSED_BOOK_FILE, question_id, question["question"], reference, verdict, note, today
    )
```

- [ ] **Step 4: Styles** (`app/ui_theme.py`, inside `CSS`, after the `.checks .ok ...` line)

```css
.cb-reference {color: var(--muted); border-left: 1px solid var(--line); padding-left: 0.85rem;
  white-space: pre-wrap; overflow-wrap: anywhere; margin-bottom: 0.5rem;}
.cb-answer {font-family: "Source Serif", "Source Serif 4", Georgia, serif; font-size: 1.02rem;
  line-height: 1.6; color: var(--ink); background: var(--surface); border: 1px solid var(--line);
  border-radius: 6px; padding: 0.75rem 1.25rem; white-space: pre-wrap; overflow-wrap: anywhere;}
```

- [ ] **Step 5: Tab and sidebar** (`app/catalogue_page.py`)

Add `import closed_book  # noqa: E402` after `import catalogue_plan`. Change `sidebar` to take the screen rows and
the truth: signature `sidebar(questions, truth, plan, review, screen_rows)`; after
`st.caption(catalogue_review.review_summary(review))` add:

```python
        counts = closed_book.counts(screen_rows, questions, truth)
        st.caption(closed_book.summary(counts, total))
```

New function after `review_tab`:

```python
VERDICT_LABELS = {"hit": "Hits the core point", "miss": "Misses it"}


def closed_book_tab(screen_rows, questions, truth, frozen: bool) -> None:
    """Jonas' verdict on each answer without context (ADR 0040); the editor never calls the API."""
    rows = {r["question_id"]: r for r in screen_rows}
    found = closed_book.states(screen_rows, questions, truth)
    unscreened = [qid for qid, s in found.items() if s == closed_book.NOT_SCREENED]
    pending = [q for q in questions if found[q["question_id"]] == closed_book.NOT_JUDGED]
    judged = [q for q in questions if found[q["question_id"]] in VERDICT_LABELS]
    if unscreened:
        st.info(
            f"{len(unscreened)} question(s) without an answer yet: run "
            "`uv run python src/catalogue.py screen`."
        )
    elif not pending and questions:
        st.info("Every question is judged.")
    today = date.today().isoformat()

    def record(qid: str, verdict: str, note: str) -> None:
        try:
            store.judge_closed_book(qid, verdict, note, today)
            st.rerun()
        except (ValueError, PermissionError) as error:
            st.error(str(error))

    for q in pending:
        qid = q["question_id"]
        with st.container(border=True):
            st.markdown(f"**{qid}**: {q['question']}")
            reference = html.escape(truth.get(qid, {}).get("expected_answer", ""))
            st.html(f'<div class="cb-reference">Reference answer: {reference}</div>')
            st.caption("Answer without context")
            st.html(f'<div class="cb-answer">{html.escape(rows[qid]["answer"])}</div>')
            note = st.text_input("Note", key=f"cb_note_{qid}") or ""
            a, b = st.columns(2)
            if a.button(VERDICT_LABELS["hit"], key=f"cb_hit_{qid}", disabled=frozen):
                record(qid, "hit", note)
            if b.button(VERDICT_LABELS["miss"], key=f"cb_miss_{qid}", disabled=frozen):
                record(qid, "miss", note)
    if judged:
        with st.expander(f"Judged ({len(judged)})"):
            for q in judged:
                qid, verdict = q["question_id"], found[q["question_id"]]
                other = "miss" if verdict == "hit" else "hit"
                note = rows[qid]["note"]
                st.markdown(
                    f"**{qid}** {VERDICT_LABELS[verdict].lower()}: {q['question']}"
                    + (f" ({note})" if note else "")
                )
                if st.button(
                    f"Change to: {VERDICT_LABELS[other].lower()}",
                    key=f"cb_flip_{qid}",
                    disabled=frozen,
                ):
                    record(qid, other, note)
```

In `main`, after `review = catalogue_review.read_review(...)`:

```python
    try:
        screen_rows = closed_book.read_screen(store.CLOSED_BOOK_FILE)
    except ValueError as error:
        st.error(str(error))
        return
```

Change `sidebar(questions, plan, review)` to `sidebar(questions, truth, plan, review, screen_rows)` and the tabs to:

```python
    unjudged = sum(
        1 for s in closed_book.states(screen_rows, questions, truth).values()
        if s == closed_book.NOT_JUDGED
    )
    write, rev, cb = st.tabs(
        [
            "Write",
            f"Review ({open_count})" if open_count else "Review",
            f"Closed-book ({unjudged})" if unjudged else "Closed-book",
        ]
    )
    with write:
        write_tab(corpus, plan, questions, truth, frozen)
    with rev:
        review_tab(corpus, review, questions, frozen)
    with cb:
        closed_book_tab(screen_rows, questions, truth, frozen)
```

Update the module docstring's first paragraph: "Shows only the corpus, the catalogue files and the closed-book
answers (ADR 0040); never chunks, strategies, retrieval results or scores (ADR 0027)."

- [ ] **Step 6: Run the tests**

Run: `uv run pytest tests/test_catalogue_editor.py -q`
Expected: all pass. If `at.tabs[0].get("html")` is not supported by AppTest 1.58, assert instead on the HTML elements
outside the third tab: `at.tabs[2]` holds the answer, `at.tabs[0]` must not (ledger the adjustment as a ruling).

- [ ] **Step 7: Browser check** (UI rule: 320, 768 and 1280 px, light and dark)

The running editor (background task, 100.85.180.27:8501) reloads the page on the next rerun; restart it only if
it does not. It reads the real files: `closed_book_screen.csv` does not exist yet, so the tab shows the screen notice.
For the card state, start a preview on port 8502 against synthetic files in the scratchpad (`$SCRATCH`), never the
real data. Write `$SCRATCH/cb_preview.py`:

```python
"""Preview of the closed-book tab on synthetic files (not part of the repo)."""
import runpy
import shutil
import sys
from pathlib import Path

REPO = Path("/home/jonas/Documents/Code/PaperLab/scientific-papers/thesis/thesis-semester-7-rag-chunking_jonas/code")
HERE = Path(__file__).resolve().parent / "cb_data"
sys.path.insert(0, str(REPO / "src"))
import catalogue_store as store  # noqa: E402

HERE.mkdir(exist_ok=True)
for name in ("catalogue_plan.csv", "catalogue_review.csv"):
    if not (HERE / name).exists():
        shutil.copy(REPO / "data" / "evaluation" / name, HERE / name)
store.QUESTIONS_FILE = HERE / "questions.csv"
store.GROUND_TRUTH_FILE = HERE / "ground_truth.csv"
store.CATALOGUE_PLAN_FILE = HERE / "catalogue_plan.csv"
store.CATALOGUE_REVIEW_FILE = HERE / "catalogue_review.csv"
store.CATALOGUE_FREEZE_FILE = HERE / "catalogue_freeze.json"
store.CLOSED_BOOK_FILE = HERE / "closed_book_screen.csv"
runpy.run_path(str(REPO / "app" / "catalogue_page.py"), run_name="__main__")
```

Save two synthetic questions through the preview (slot S01 and S02, text like "Preview question one?"), then fill
`cb_data/closed_book_screen.csv` with `closed_book.screen(...)` and a fake completer from a Python one-liner in the
scratchpad (no API), judge one of them in the tab, and screenshot:

```bash
uv run streamlit run "$SCRATCH/cb_preview.py" --server.port 8502 --server.address 100.85.180.27 --server.headless true  # background
playwright-cli screenshot --viewport-size=1280,900 --wait-for-timeout=9000 http://100.85.180.27:8502 "$SCRATCH/cb-1280.png"
playwright-cli screenshot --viewport-size=768,1000 --wait-for-timeout=9000 http://100.85.180.27:8502 "$SCRATCH/cb-768.png"
playwright-cli screenshot --viewport-size=320,900 --wait-for-timeout=9000 http://100.85.180.27:8502 "$SCRATCH/cb-320.png"
```

The screenshots open on the Write tab; to reach the third tab use `playwright-cli --help` for a click/eval option
(e.g. click the text "Closed-book"); if the CLI has none, rely on AppTest for the tab content and say so in the
report. Check: tab label with count, notice, card layout (reference quieter than the answer), no horizontal scroll at
320 px, sidebar line wraps cleanly, light and dark (`prefers-color-scheme`). Stop the preview afterwards; the
scratch files stay outside the repo.

- [ ] **Step 8: Commit**

```bash
git add src/catalogue_store.py app/catalogue_page.py app/ui_theme.py tests/test_catalogue_editor.py
git commit -m "feat(editor): Tab Closed-book für das Urteil über Antworten ohne Kontext"
```

---

### Task 5: ADR 0040 and documentation

**Files:**
- Create: `docs/adr/0040-closed-book-pruefung.md`
- Modify: `docs/adr/README.md`, `docs/adr/0038-korpus-e2e.md` (status line), `docs/reference/data-formats.md`,
  `docs/reference/configuration.md`, `docs/how-to/build-the-question-catalogue.md`,
  `docs/reference/question-catalogue.md`, `docs/plan.md`, `.serena/memories/pipeline.md`

- [ ] **Step 1: ADR 0040** (`docs/adr/0040-closed-book-pruefung.md`)

```markdown
# 0040. Closed-Book-Prüfung des Fragenkatalogs

## Status

Angenommen (19.10.2026; füllt die offene Frage aus [ADR 0038](0038-korpus-e2e.md), wer den Kernpunkt beurteilt;
ergänzt [ADR 0030](0030-einfrieren-des-fragenkatalogs.md) und [ADR 0031](0031-stichprobenplan-und-ki-durchsicht.md))

## Kontext

- ADR 0038 verlangt, jede Katalogfrage vor dem Einfrieren ohne Kontext beantworten zu lassen; trifft die Antwort den
  Kernpunkt, ist die Frage retrieval-unabhängig. Mindestens zwei Drittel müssen retrieval-abhängig sein.
- In der Diagnose beantwortete das Antwortmodell 1 von 20 e2e-Fragen ohne Dokumentation richtig. Bei so seltenen
  Treffern schwankt ein Übereinstimmungsmaß wie κ stark: eine abweichende Beurteilung bewegt es zwischen 1 und 0.
- Der RAG-Prompt bindet das Modell an die Ausschnitte; ohne Ausschnitte lehnt es fast immer ab und zeigt nicht, was es
  weiß.
- Der Katalog entsteht in Blöcken von 8 Fragen mit einer KI-Durchsicht nach jedem Block (ADR 0031).

## Entscheidung

Wir werden nach jedem Block mit `catalogue.py screen` jede neue oder geänderte Frage vom Antwortmodell (Modell,
Temperatur 0, Seed und Token-Limit der Antwortgenerierung) mit einem eigenen Closed-Book-Prompt beantworten lassen;
derselbe Prompt dient der Kontrolle K0 ([Prompts](../reference/prompts.md#closed-book-prompt-prüfung-und-k0)).
Wir werden die Antworten in `data/evaluation/closed_book_screen.csv` ablegen; Jonas beurteilt im Editor-Tab
„Closed-book“, ob eine Antwort den Kernpunkt seiner Referenzantwort vollständig trifft (`hit`) oder nicht (`miss`,
auch bei teilweise richtig). Der Editor ruft die API nie auf; beim Schreiben sind keine Modellantworten sichtbar.
Wir werden eine `hit`-Frage im Katalog lassen und markieren; Jonas darf sie umformulieren, dann fragt `screen` neu.
Wir werden das Einfrieren verweigern, solange eine Frage auf ihrem aktuellen Text ungeprüft oder unbeurteilt ist oder
mehr als 16 von 48 Fragen `hit` sind (`config.CLOSED_BOOK_MIN_DEPENDENT_SHARE`); der Freeze-Record hält die Zahlen fest.

## Konsequenzen

- Positiv: Der Katalog misst nachweislich überwiegend Retrieval; die Markierung erlaubt, die Ergebnisse getrennt für
  retrieval-abhängige und -unabhängige Fragen zu berichten. Prüfung und K0 messen dieselbe Bedingung.
- Negativ: Jonas beurteilt Antworten auf seine eigenen Fragen, nicht blind; das steht als Grenze in der Arbeit. Ein
  LLM-Richter mit κ-Prüfung wurde verworfen (instabil bei seltenen Treffern, kaum Zeitersparnis bei 48 Fragen).
- Neutral: Antworten ohne Kontext dürfen zum Umformulieren führen. Sie enthalten keine Information über Retrieval,
  Chunks oder Strategien; der Vergleich C1–C3 bleibt unverzerrt (ADR 0017, 0027). Ein gezieltes Ersetzen aller
  bekannten Fragen ist nicht verlangt, damit der Katalog nicht auf abseitige Details gefiltert wird.
- Neutral: Jeder Lauf steht mit Modell, Tokens und Kosten in `generation_runs.jsonl` (Schritt `closed_book_screen`).
```

- [ ] **Step 2: Index and ADR 0038**

`docs/adr/README.md`: add a row for 0040 after 0039 in the same format as the 0039 row
("Closed-Book-Prüfung des Fragenkatalogs", Datum 19.10.2026, Status angenommen), and extend the number range in the
intro from "0019–0039" to "0019–0040". In `docs/adr/0038-korpus-e2e.md`, append to the status line's parenthesis:
"; wer den Kernpunkt beurteilt: [ADR 0040](0040-closed-book-pruefung.md)".

- [ ] **Step 3: Data formats** (`docs/reference/data-formats.md`)

After the `catalogue_review.csv` block, add:

````markdown
**`closed_book_screen.csv`** (`data/evaluation/`, versioniert; `catalogue.py screen` schreibt Antworten, Jonas die
Urteile im Editor; [ADR 0040](../adr/0040-closed-book-pruefung.md)): eine Zeile je Katalogfrage, sortiert nach ID.
```
question_id,question_sha256,reference_sha256,answer,model,core_point,note,date
Q001,5d1f…,a90c…,I don't know which command installs the skill.,gpt-6-luna-2026-05-18,miss,,2026-10-21
```
`question_sha256` = SHA-256 des Fragetexts, zu dem die Antwort gehört (geänderte Frage: `screen` fragt neu, das Urteil
wird geleert); `reference_sha256` = SHA-256 der Referenzantwort, zu der das Urteil gehört (geänderte Referenz: Urteil
offen). `core_point` ∈ `config.CLOSED_BOOK_VERDICTS`: leer = offen, `hit` = trifft den Kernpunkt (Frage
retrieval-unabhängig), `miss` = trifft ihn nicht oder nur teilweise.
````

Replace the two Vue example rows of `catalogue_review.csv` with e2e rows:

```
1,Q001,missing_section,The CLI page lists the same install command.,D009#install,accepted,,2026-10-21
1,Q002,wording,Name the command instead of "it".,,rejected,the slot asks for a paraphrase,2026-10-21
```

(Use a real `D…#…` section ID from `data/processed/sections.jsonl` for the first row:
`uv run python src/catalogue.py find "install"` and pick one; replace `D009#install` with it.)

In the freeze-record example and the sentence below it: add `"closed_book_screen.csv": "…"` to the recorded files, add
`"closed_book": {"dependent": 40, "known": 8}` to the example, and change the sentence to "Plan-, Durchsichts- und
Closed-Book-Datei werden nur aufgezeichnet; die Sperre in `retrieve.py` prüft die vier übrigen Dateien." In the
overview table of versioned files (the one with `key_points.csv`), add a row
`| closed_book_screen.csv | Antworten ohne Kontext und Urteile der Closed-Book-Prüfung ([ADR 0040](../adr/0040-closed-book-pruefung.md)) | ja |`.

- [ ] **Step 4: Configuration** (`docs/reference/configuration.md`)

Add rows in the matching sections (paths, catalogue, LLM/prompt), same column layout as the neighbouring rows:

```
| `CLOSED_BOOK_FILE` | `data/evaluation/closed_book_screen.csv` | Antworten ohne Kontext und Urteile | [ADR 0040](../adr/0040-closed-book-pruefung.md) |
| `CLOSED_BOOK_VERDICTS` | `("", "hit", "miss")` | Urteil: offen, trifft den Kernpunkt, trifft ihn nicht | [ADR 0040](../adr/0040-closed-book-pruefung.md) |
| `CLOSED_BOOK_MIN_DEPENDENT_SHARE` | `Fraction(2, 3)` | Mindestanteil retrieval-abhängiger Fragen (aufgerundet: 32 von 48) | [ADR 0038](../adr/0038-korpus-e2e.md) |
| `CLOSED_BOOK_SYSTEM_PROMPT`, `CLOSED_BOOK_USER_TEMPLATE` | siehe [Prompts](prompts.md#closed-book-prompt-prüfung-und-k0) | Prompt der Closed-Book-Prüfung und von K0 | [ADR 0040](../adr/0040-closed-book-pruefung.md) |
```

- [ ] **Step 5: How-to** (`docs/how-to/build-the-question-catalogue.md`)

After step 3 (AI review after each block) insert a new step 4 and renumber the following steps (5, 6):

````markdown
4. Nach jedem Block auch die Closed-Book-Prüfung ([ADR 0040](../adr/0040-closed-book-pruefung.md)): Das
   Antwortmodell beantwortet jede neue oder geänderte Frage ohne Kontext (ruft die API auf, wenige Cent je Block):

   ```bash
   uv run python src/catalogue.py screen
   ```

   Im Tab „Closed-book“ je Antwort entscheiden: „Hits the core point“, wenn sie den Kernpunkt der Referenzantwort
   vollständig trifft, sonst „Misses it“ (auch bei teilweise richtig). Höchstens 16 von 48 Fragen dürfen treffen; die
   Seitenleiste zeigt den Stand. Eine getroffene Frage darf bleiben; wer sie umformuliert, lässt `screen` erneut laufen.
````

In the check step, extend the `WARNING` list: "(Quoten, Bereiche, Klassenregeln, Dubletten, offene Vorschläge,
ungeprüfte oder unbeurteilte Closed-Book-Antworten)". In the freeze step, add `data/evaluation/closed_book_screen.csv`
to the `git add` line, and change "alle Vorschläge entschieden sind" to "alle Vorschläge und Closed-Book-Antworten
entschieden sind".

- [ ] **Step 6: Catalogue rules, plan, memory**

`docs/reference/question-catalogue.md`: in the rules section add a paragraph "**Closed-Book-Prüfung.** Jede Frage wird
ohne Kontext beantwortet; trifft die Antwort den Kernpunkt der Referenzantwort, ist die Frage retrieval-unabhängig und
bleibt markiert im Katalog. Mindestens `ceil(2/3 × 48)` = 32 Fragen müssen retrieval-abhängig sein; Einfrieren erst,
wenn jede Frage auf ihrem aktuellen Text geprüft und beurteilt ist ([ADR 0040](../adr/0040-closed-book-pruefung.md))."

`docs/plan.md` (Stand paragraph): change "(4b) Closed-Book-Prüfung im Editor" to "(4b) Closed-Book-Prüfung im Editor
(erledigt 19.10.2026, [ADR 0040](adr/0040-closed-book-pruefung.md))".

`.serena/memories/pipeline.md`: add one line in the catalogue part: "Closed-book screen: `catalogue.py screen` (API) →
`closed_book_screen.csv` → editor tab Closed-book; check/freeze need all judged and ≤ 16 hits. Code `src/closed_book.py`;
ADR 0040, docs/reference/data-formats.md."

- [ ] **Step 7: Verify links and suite**

Run: `uv run pytest -q > "$WS/suite.txt" 2>&1; tail -3 "$WS/suite.txt"` and `uvx pre-commit run --all-files`
Expected: all pass. Then `grep -rn "0040-closed-book-pruefung" docs | wc -l` (≥ 8 links) and check the anchor
`#closed-book-prompt-prüfung-und-k0` exists as the heading in `prompts.md`.

- [ ] **Step 8: Commit**

```bash
git add docs/adr/0040-closed-book-pruefung.md docs/adr/README.md docs/adr/0038-korpus-e2e.md \
  docs/reference/data-formats.md docs/reference/configuration.md docs/how-to/build-the-question-catalogue.md \
  docs/reference/question-catalogue.md docs/plan.md .serena/memories/pipeline.md
git commit -m "docs(adr): ADR 0040 Closed-Book-Prüfung des Fragenkatalogs"
```
