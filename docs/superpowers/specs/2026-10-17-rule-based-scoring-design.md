# Rule-based scoring: design

Date: 17.10.2026. Status: design A approved in chat (checklist with derived scores, key points before scoring, no
manual override). Decision: new ADR 0035 (operationalised rubric); extends
[ADR 0013](../../adr/0013-antwort-rubrik.md), [ADR 0032](../../adr/0032-blinde-rubrik-bewertung.md) and
[ADR 0034](../../adr/0034-bewertung-in-der-app.md).

## Goal

The five rubric scores (0–2) follow from factual checks through fixed rules instead of a holistic judgement: the same
checks always give the same scores, every score can be traced to its checks, and scoring is faster. Used first on the
pilot set `data/pilot/hard` (H01–H08, 24 answers); the rules are adjusted once after the pilot, then frozen for the
main run (144 answers).

Success: the 24 pilot answers can be scored through the checklist; the sheet holds the derived scores and
`summarise` reads it unchanged; changing a check changes the scores exactly as the rule table says.

## Constraints

- Blind as before (ADR 0032, 0034): no strategy, no chunk ID, the key stays closed.
- Key points are ground truth: Jonas writes them; Claude never writes or suggests them. They are written before any
  answer of the set is scored and frozen before scoring starts (in the spirit of ADR 0017).
- The key-point step never shows a generated answer or an excerpt.
- `scoring_sheet.csv` keeps its format; `summarise` keeps working on it.
- No manual override of a derived score. A rule that does not fit is noted in `notes` and fixed after the pilot.
- All thresholds in `src/config.py`; the rules are versioned (`config.RUBRIC_RULES_VERSION`).

## Key points

- File `key_points.csv` (`config.KEY_POINTS_FILE = DATA_EVAL / "key_points.csv"`; in a pilot set the same name in the
  set folder), versioned. One row per point:

  ```
  question_id,point,text
  H01,1,"defineModel() in the child component (Vue 3.4+)"
  ```

  `point` 1 is the **core point** (the direct answer to the question); 1 to `config.KEY_POINTS_MAX` (4) points per
  question, numbered without gaps; text non-empty, one line.
- Written on the Scoring page in a **Key points** step: per question only the question and its reference answer.
- **Freeze:** a button "Freeze key points", enabled once every question of the set has at least one point, appends
  `{"step":"key_points","outputs_sha256":{"key_points.csv":"…"}}` to the set's run log (`runs.jsonl` /
  `generation_runs.jsonl`, `run_log.append_key_points_run`). After the freeze the step is read-only.
- Every save of a score checks that `key_points.csv` still has the frozen checksum (latest `key_points` record);
  otherwise the save is refused (a hand edit after the freeze is caught).

## Checks per answer and the rules

Checks (stored per code; option values in brackets):

| Check | Question shown | Options |
|---|---|---|
| `point_<n>` | Key point *n*: is it in the answer with the same meaning? | `covered`, `missing` |
| `declines` | Does the answer say the excerpts do not contain the answer, and give none? | `yes`, `no` |
| `core_wrong` | Does the answer state the core point wrongly or contradict it? | `yes`, `no` |
| `other_error` | Is any other statement in the answer factually wrong? | `yes`, `no` |
| `grounded` | How many of the answer's statements are backed by the excerpts? | `all`, `some`, `none` |
| `hallucination` | Does the answer contain anything that neither the excerpts nor the reference cover? | `none`, `minor`, `substantive` |
| `answers_question` | Does the answer address what was asked? | `yes`, `no` |
| `direct` | Is the answer given directly, in the first two sentences? | `yes`, `no` |
| `wordy` | Is the answer repetitive, padded or confusing? | `yes`, `no` |

`minor` = an unsupported addition that does not change the answer; `substantive` = an unsupported or contradicting
claim that does. A point stated only partly counts as `missing`.

Rules (`src/scoring_rules.py`, `derive(checks, points) -> dict[criterion, int]`):

| Criterion | 2 | 1 | 0 |
|---|---|---|---|
| correctness | nothing wrong | `other_error` = yes, or `declines` = yes | `core_wrong` = yes |
| completeness | all points covered | covered / points ≥ `config.RUBRIC_COMPLETENESS_PARTIAL` (0.5) | otherwise |
| groundedness | `grounded` = all | `grounded` = some | `grounded` = none |
| no_hallucination | `hallucination` = none | `hallucination` = minor | `hallucination` = substantive |
| clarity | `answers_question` = yes, `direct` = yes, `wordy` = no | `answers_question` = yes, otherwise | `answers_question` = no |

Declining answers: with `declines` = yes the form skips the point checks (all `missing`), `core_wrong`, `other_error`,
`grounded` and `hallucination`; they are stored as `missing`/`no`/`all`/`none`. Result: correctness 1 (between
correct and wrong, as an honest "not in the context"), completeness 0, groundedness 2, no_hallucination 2, clarity by
its checks. This is the one rule Jonas should look at deliberately in the spec review.

Correctness is checked in order: `core_wrong` = yes gives 0 (also when `other_error` is set); otherwise `other_error`
or `declines` gives 1; otherwise 2.

## Data

- `scoring_checks.csv` next to the sheet (`config.SCORING_CHECKS_FILE`; pilot: set folder), versioned like the sheet:
  it is the primary record of how each score came about. Header:

  ```
  code,rules_version,points,declines,core_wrong,other_error,grounded,hallucination,answers_question,direct,wordy
  H01-A,2026-10-17,covered;missing,no,no,no,all,none,yes,yes,no
  ```

  `points` lists the marks in point order, `;`-separated. One row per scored code, in sheet order, written atomically.
- `scoring_sheet.csv`: unchanged format; the five criteria are written from `derive`, `notes` from the form.
- `summarise` additionally checks, when the set has a checks file, that every sheet row equals `derive` of its checks
  under the recorded `rules_version` (a hand edit of a score is caught); a row from an older `rules_version` is
  reported as such. Without a checks file `summarise` behaves as today.

## Scoring page

- A segmented control at the top: **Key points** | **Score**. Before the freeze it opens on Key points and Score is
  disabled with a caption; after the freeze it opens on Score and Key points is read-only.
- **Key points step:** sidebar progress "6 of 8 questions have key points"; per question the question and the
  reference answer (muted card), then up to four text inputs ("Core point", "Point 2" …), "Save and next", and
  "Freeze key points" with a confirmation line saying it cannot be undone.
- **Score step:** reader column as today (answer, excerpts). The form column replaces the five 0/1/2 controls by
  the checks in the order of the table above (key points listed with their text), each a segmented control; a compact
  live table of the five derived scores below; notes; "Previous", "Save and next" (disabled until every shown check
  is answered), "Jump to". A saved code reopens with its checks.
- Read-only set (scores.csv exists): both steps disabled, as today.

## Configuration (new keys)

`KEY_POINTS_FILE`, `KEY_POINTS_MAX = 4`, `SCORING_CHECKS_FILE`, `RUBRIC_COMPLETENESS_PARTIAL = 0.5`,
`RUBRIC_RULES_VERSION = "2026-10-17"`.

## Documentation

ADR 0035 (new) and ADR README row; status notes in 0013, 0032, 0034; AGENTS.md (D1–D35); `docs/reference/evaluation.md`
(checks and rule table replace the adjective table as the operative definition, the adjectives stay as the summary);
`data-formats.md` (`key_points.csv`, `scoring_checks.csv`, `key_points` run record); `configuration.md`;
`run-the-experiment.md` (key points, freeze, scoring); `tooling.md` (versioned files); Serena memory `pipeline`.

## Out of scope

Re-scoring a sample for intra-rater agreement; a second rater; an LLM judge. Follow-ups after the pilot.

## Testing

- `tests/test_scoring_rules.py`: every row of the rule table, the completeness threshold at 1, 2, 3 and 4 points,
  the declining shortcut, invalid option values rejected.
- `tests/test_scoring_store.py`: key points saved and validated (numbering, max 4, empty text); freeze refused while
  a question has no point; freeze writes the run record; edits refused after the freeze; score save refused before
  the freeze and after a hand edit of `key_points.csv`; checks file and sheet written together, sheet equals
  `derive`.
- `tests/test_evaluate_answers.py`: `summarise` refuses a sheet row that differs from its checks; works without a
  checks file.
- `tests/test_scoring_page.py` (AppTest): Key points step shows no answer text and no excerpt; Score disabled before
  the freeze; scoring through the checks writes the derived scores; declining hides the skipped checks.
- Browser (playwright-cli) at 320, 768 and 1280 px, light and dark, both steps end to end on a copy of the pilot set;
  then impeccable `audit` and `polish`.
