# Closed-book screen of the question catalogue: design

Date: 19.10.2026. Status: approved in chat (19.10.2026). Decision basis: [ADR 0038](../../adr/0038-korpus-e2e.md)
(closed-book screen of every catalogue question, at least two thirds retrieval-dependent; who judges was left to the
catalogue step), [ADR 0030](../../adr/0030-einfrieren-des-fragenkatalogs.md),
[ADR 0031](../../adr/0031-stichprobenplan-und-ki-durchsicht.md). Step 4b of the corpus switch
([plan](../../plan.md#stand)); the control K0 (4c) gets its own spec but reuses the prompt defined here.

## Goal

Every catalogue question is answered once by the answer model without any context; Jonas judges in the editor whether
that answer hits the core point of his reference answer. A question it hits is marked retrieval-independent and stays
in the catalogue. The strict check and the freeze refuse unless every question is screened and judged on its current
text and at least `ceil(2/3 × 48) = 32` questions are retrieval-dependent.

Success criteria:

- `uv run python src/catalogue.py screen` answers every question without a current answer and writes
  `data/evaluation/closed_book_screen.csv`; the editor never calls the API.
- The editor tab "Closed-book" records Jonas' verdict; the sidebar shows the count against the threshold.
- `catalogue.py check` reports the findings below (WARNING in `--draft`, ERROR when strict); `freeze` records the file
  and the counts.
- `uv run pytest` and `uvx pre-commit run --all-files` pass; no test calls the OpenAI API.

## Decisions (19.10.2026)

| Question | Decision | Rejected |
|---|---|---|
| Who judges the core point | Jonas, in the editor; not blind (he wrote the question), stated as a limitation | LLM judge validated with κ on ~20 questions: with ~1/20 hits κ is unstable (one disagreement moves it from 1 to 0); judge proposes, Jonas confirms: costliest, he reads every answer anyway |
| When the screen runs | After each block of 8 questions, with the AI review, as its own command | On save in the editor: needs network and key, slows saving, shows model answers while writing (invites questions tuned to fool the model); once at the end: quota problems surface late |
| Prompt | A closed-book prompt shared with K0, as close as possible to the RAG prompt without excerpts | RAG prompt with empty context (the model only declines); the diagnosis prompt of ADR 0038 (K0 would need a third prompt or get a 1–3 sentence limit the strategies do not have) |
| A question the model answers | Stays and is marked; Jonas may rephrase it (the next screen run asks again); the ⅔ rule is hard at freeze | Replace every marked question (filters the catalogue towards obscure details, contradicts the ⅔ room in ADR 0038); a fifth skip reason (filters the sampling plan by model knowledge, reserve may run short) |
| Partially correct | Counts as `miss`: a question is marked only if the answer fully hits the core point | — |

## Prompt

`config.CLOSED_BOOK_SYSTEM_PROMPT` and `config.CLOSED_BOOK_USER_TEMPLATE`:

```
You are a helpful assistant that answers questions about the e2e testing framework.
If you do not know the answer, state that explicitly.
```

```
Answer the following question.

Question: {question}

Answer:
```

`prompt.closed_book_messages(question) -> list[dict]` returns system and user message (braces in the question stay as
they are). Model, temperature 0, reasoning effort, seed and token limit are those of the answer generation
(`llm_client.complete`). `docs/reference/prompts.md` gets a section "Closed-Book-Prompt (Prüfung und K0)"; the existing
test that compares the prompt texts in `config.py` with that page covers it.

## Data: `data/evaluation/closed_book_screen.csv`

Versioned, one row per catalogue question, in catalogue order:

```
question_id,question_sha256,reference_sha256,answer,model,core_point,note,date
```

- `question_sha256`: SHA-256 of the question text the answer belongs to; `reference_sha256`: SHA-256 of the reference
  answer the verdict belongs to (UTF-8, text as stored in the CSV).
- `answer`: the model's reply; `model`: the model the API reported.
- `core_point` ∈ `config.CLOSED_BOOK_VERDICTS` = `("", "hit", "miss")`: empty = not judged; `hit` = the answer hits
  the core point of the reference answer (question marked retrieval-independent); `miss` = it does not or only partly.
- `note`: optional, Jonas' note; `date`: date of the verdict (ISO), empty while not judged.

States of a question:

| State | Condition |
|---|---|
| not screened | no row, or `question_sha256` differs from the current question text |
| not judged | row current, `core_point` empty or `reference_sha256` differs from the current reference answer |
| judged | row current, `core_point` set, `reference_sha256` current |

## Units

| Unit | Change |
|---|---|
| `src/config.py` | `CLOSED_BOOK_FILE`, `CLOSED_BOOK_SYSTEM_PROMPT`, `CLOSED_BOOK_USER_TEMPLATE`, `CLOSED_BOOK_VERDICTS`, `CLOSED_BOOK_MIN_DEPENDENT_SHARE = 2/3` |
| `src/prompt.py` | `closed_book_messages(question)` |
| `src/closed_book.py` (new) | read/save the CSV (atomic, header check), `status(rows, questions, truth)` per question, `screen(questions, truth, path, completer)` (answers every question without a current answer, saves after each answer, drops rows of questions no longer in the catalogue, aborts on `finish_reason != "stop"`, returns token counts and models), `judge(path, question_id, verdict, note, reference, today)`, `findings(rows, questions, truth, strict)` → (errors, warnings), `counts(...)` → dependent / known / not screened / not judged, `min_dependent(n_questions)` = `ceil(share × n)` |
| `src/catalogue.py` | subcommand `screen` (calls `closed_book.screen` with `llm_client.complete`, then appends a run record with step `closed_book_screen` to `generation_runs.jsonl` via `run_log.append_generation_run`); `check` adds the findings; `freeze` records the file and `"closed_book": {"dependent": n, "known": m}` |
| `app/catalogue_page.py` | tab "Closed-book"; sidebar line; read-only after the freeze |
| `docs/adr/0040-…` | new ADR: the decisions above; relation to ADR 0017 (closed-book answers may lead to rephrasing; they carry no retrieval or strategy information, so the comparison C1–C3 is not biased); closes the open point of ADR 0038 |

## Editor

Tab "Closed-book" next to "Write" and "Review":

- Lists the questions that are screened but not judged, in catalogue order. For each: the question, Jonas' reference
  answer, the closed-book answer (set apart as the model's answer), two buttons "Hits the core point" / "Misses it", an
  optional note. A verdict is saved at once and the next question follows.
- Judged questions are listed collapsed below; a verdict can be changed there.
- Questions not screened: a notice to run `uv run python src/catalogue.py screen`; the editor never calls the API.
- Sidebar: "Retrieval-dependent: N of 32 needed · K known · U not screened".
- The "Write" tab shows no model answers.
- After the freeze the tab is read-only, as the rest of the editor.

## Check and freeze

| Finding | `check --draft` | strict `check` / `freeze` |
|---|---|---|
| question not screened (no row, or question changed) | WARNING | ERROR |
| screened but not judged (new, or reference answer changed) | WARNING | ERROR |
| more than `48 − 32 = 16` questions marked `hit` (the threshold can no longer be reached) | WARNING | ERROR |
| fewer than 32 questions judged `miss` | — (covered by the two rows above) | ERROR |
| row for a question not in the catalogue, unknown `core_point`, wrong columns | ERROR | ERROR |

`freeze` records `closed_book_screen.csv` like the plan and review files (hash only; the lock in `retrieve.py` keeps
checking the four retrieval inputs) and adds `"closed_book": {"dependent": n, "known": m}` to the record.

## Error handling

- `screen` without `questions.csv` rows: nothing to do, prints so.
- An API error or a cut-off answer stops the run; answers saved so far stay (atomic save after each).
- A malformed CSV (header, field count) raises with the file name, like the review log.
- `screen`, the tab's buttons and `judge` refuse after the freeze.

## Testing

All with a fake completer (no network):

- `closed_book_messages` text and brace handling; prompts page matches `config.py`.
- `screen`: answers only missing and stale questions; a changed question gets a new answer and an empty verdict; a
  changed reference keeps the answer and clears only the verdict state; a removed question's row disappears; a cut-off
  answer aborts and keeps earlier rows; run record step and token counts.
- `findings`: every row of the table above, draft and strict; `min_dependent(48) == 32`.
- `freeze`: record contains the file hash and the counts; refuses with too few dependent questions.
- Editor (Streamlit AppTest, as the existing editor tests): the tab lists unjudged questions, a click saves the verdict,
  the sidebar count, the notice when nothing is screened, read-only after freeze.

## Documentation

`data-formats.md` (new file, freeze record; the `catalogue_review.csv` example switches from Vue to e2e rows),
`prompts.md`, `configuration.md`, `how-to/build-the-question-catalogue.md` (step after each block: `screen`, tab
"Closed-book"; the file in the freeze commit), `question-catalogue.md` (the rule), `adr/README.md`, ADR 0038 (status
line points to ADR 0040), `plan.md` (4b done), `.serena/memories`.

## Out of scope

K0 as an evaluation condition (4c); any question, reference answer, key point or verdict.
