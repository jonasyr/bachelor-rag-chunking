# Control K0 (answers without retrieval): design

Date: 19.10.2026. Status: approved in chat (19.10.2026). Decision basis: [ADR 0038](../../adr/0038-korpus-e2e.md)
(K0 answers the same questions without retrieval and is scored like the strategies; not in `config.STRATEGY_IDS`),
[ADR 0040](../../adr/0040-closed-book-pruefung.md) (closed-book prompt shared with K0),
[ADR 0033](../../adr/0033-antwortmodell.md), [ADR 0035](../../adr/0035-regelbasierte-bewertung.md).
Step 4c of the corpus switch ([plan](../../plan.md#stand)).

## Goal

The answer generation also writes one closed-book answer per catalogue question (control K0) in the same run as
C1–C3; after the C1–C3 scoring is summarised, Jonas scores the K0 answers on the scoring page with the same frozen
key points and a K0 variant of the rules; a summary compares K0 with C1–C3 on the four criteria both can have.

Success criteria:

- `generate.py` writes `generated_answers.csv` (C1–C3, unchanged) and `generated_answers_control.csv` (K0) in one
  run, or neither; the run record carries both hashes and K0's tokens.
- `evaluate_answers.py --mode scaffold --control` refuses until `scores.csv` exists; then writes the K0 scoring set.
- The scoring page offers the set "Control K0" with the K0 checks.
- `evaluate_answers.py --mode summarise --control` writes `scores_control.csv` and prints K0 next to C1–C3.
- `uv run pytest` and `uvx pre-commit run --all-files` pass; no test calls the OpenAI API.

## Decisions (19.10.2026)

| Question | Decision | Rejected |
|---|---|---|
| How K0 enters the scoring | Own scoring set after C1–C3; same frozen key points; K0 rule variant (no `grounded`; `declines` = says it does not know; hallucination relative to the reference); compared on correctness, completeness, no_hallucination, clarity | K0 as a fourth answer in the blind packet (recognisable without excerpts, anchors the C1–C3 judgement); only correctness and completeness (drops two criteria ADR 0038 implies) |
| When K0 answers are generated | In the same `generate.py` run as C1–C3, own file | Separate command (the model behind the alias may change between runs); reuse the screen answers (many runs over weeks, partly on older question texts) |
| Order of scoring | K0 only after C1–C3, enforced: scaffold refuses until `scores.csv` exists | Order only in the how-to (no technical guard, unlike ADR 0017/0027); K0 first (anchors the C1–C3 judgement) |

K0 is not scored blind (it cannot be: it has no excerpts); this is a stated limitation. Groundedness is reported for
C1–C3 only.

## Configuration (`src/config.py`)

- `CONTROL_ANSWER_STRATEGIES = {"K0": "closed_book"}`: separate from `CONTROL_STRATEGIES` (K1, retrieval only) and
  `STRATEGY_IDS`.
- `GENERATED_ANSWERS_CONTROL_FILE = DATA_EVAL / "generated_answers_control.csv"`.
- `SCORING_ITEMS_CONTROL_FILE`, `SCORING_SHEET_CONTROL_FILE`, `SCORING_CHECKS_CONTROL_FILE`, `SCORES_CONTROL_FILE`
  in `data/evaluation/` (`scoring_items_control.jsonl`, `scoring_sheet_control.csv`, `scoring_checks_control.csv`,
  `scores_control.csv`).
- `CONTROL_CRITERIA = ["correctness", "completeness", "no_hallucination", "clarity"]`.

## Generation (`src/generate.py`)

- After all local checks, the run answers every question for C1–C3 (unchanged) and then once with
  `prompt.closed_book_messages(question)`.
- Every answer passes the existing `checked()` (finish reason, empty, one model and fingerprint per run); the model's
  creation time must be the same before and after the run. Any failure writes neither file.
- Refuses if either output file exists (answers are generated once, ADR 0033).
- `generated_answers_control.csv` has the header of `generated_answers.csv`; `strategy` = `K0`, `sources` empty.
- The run record keeps `"strategy": "C1,C2,C3"` (what `evaluate_answers.py` checks), adds `K0` under `by_strategy`
  (prompt and completion tokens, cost) and both files under `outputs_sha256`.
- Pilot sets (`--set DIR`) get `generated_answers_control.csv` in their folder the same way.

## Rules (`src/scoring_rules.py`)

- `CONTROL_CHECKS`: `CHECKS` without `grounded`; `CONTROL_CHECKS_HEADER`; `SKIPPED_WHEN_DECLINING` without
  `grounded` for K0.
- `validate(checks, n_points, control=False)`, `declined(checks, n_points, control=False)`,
  `to_row(code, checks, control=False)`, `from_row(row, control=False)` take the variant.
- `derive_control(checks) -> dict[str, int]` returns the four `CONTROL_CRITERIA` by the same rules as `derive`
  (correctness, completeness, hallucination, clarity unchanged).
- The labels shown on the page for `declines` and `hallucination` differ for K0 (see page); the stored values and
  options are the same.

## Scoring set (`src/evaluate_answers.py`, `src/scoring_store.py`)

- `--mode scaffold --control` (main or `--set DIR`): refuses unless the folder's `scores.csv` exists; refuses unless
  `generated_answers_control.csv` matches the latest generation run's output hash and covers every catalogue question
  exactly once with `K0`; refuses an existing K0 sheet. Writes `scoring_items_control.jsonl` (per question: code
  `Q001-K0`, question, reference answer, answer, `excerpts: []`) and `scoring_sheet_control.csv`
  (`code, question_id, correctness, completeness, no_hallucination, clarity, notes`).
- `ScoringSet` gets `control: bool`; `scoring_sets()` adds "Control K0" (main) and "Pilot …: control K0" sets when
  their item file exists; the K0 set uses the folder's `key_points.csv` and requires it frozen (read-only on the page).
- `--mode summarise --control`: validates sheet and checks with the K0 rules (every row equals what its checks
  derive), writes `scores_control.csv` (`question_id, strategy, correctness, completeness, no_hallucination, clarity,
  total_score`; total = mean of the four), and prints mean, median and standard deviation of each of the four
  criteria and of their mean for K0 and for C1–C3 (recomputed from `scores.csv`), overall, per question type, per
  construction class, and per closed-book verdict (`miss` = retrieval-dependent, `hit` = known; from
  `closed_book_screen.csv`, main catalogue only).

## Scoring page (`app/scoring_page.py`)

- Lists the K0 set like the others.
- Where excerpts are shown: "Answered without excerpts (control K0)".
- K0 checks: no `grounded` control; label of `declines`: "Says it does not know the answer and gives none?"; label of
  `hallucination`: "Contains anything the reference does not cover?".
- Key points are shown read-only (frozen); save, lock and derived values as for C1–C3.

## Error handling

- Scaffold before `scores.csv`: "score and summarise C1–C3 first (ADR 0041)".
- Missing or unfrozen key points, foreign or missing questions in the K0 answers, changed answer file: refuse with the
  file name, like the C1–C3 scaffold.
- Summarise with an unfilled or inconsistent K0 sheet: refuse like the C1–C3 summarise.

## Testing

All without network (fake completer, synthetic files):

- generate: both files written in one run; K0 prompts have no excerpts; one cut-off K0 answer writes neither file;
  existing control file refused; run record has K0 tokens and both hashes; pilot set writes its control file.
- rules: K0 validate rejects `grounded`; declining K0 answer stores the skipped values without `grounded`;
  `derive_control` on the rule table.
- scaffold: refused without `scores.csv`; refused with unfrozen key points; writes items with empty excerpts and the
  sheet; refuses an existing sheet.
- summarise: `scores_control.csv` values; comparison lines for K0 and C1–C3 over the four criteria; split by
  closed-book verdict.
- page (AppTest): K0 set listed, no grounded control, K0 labels, excerpt notice, saving derives the four criteria.

## Documentation

New ADR 0041 "Kontrolle K0: Erzeugung und Bewertung" (decisions above, limitation not blind, groundedness C1–C3
only); `evaluation.md` (K0 section with the rule variant), `data-formats.md` (four new files, run record),
`configuration.md`, `how-to/run-the-experiment.md` (K0 scoring after C1–C3), `adr/README.md`, ADR 0038 status line,
`plan.md` (4c done), `.serena/memories`.

## Out of scope

Generating or scoring real answers (only after the freeze); K1; any change to the blind C1–C3 packet or `scores.csv`.
