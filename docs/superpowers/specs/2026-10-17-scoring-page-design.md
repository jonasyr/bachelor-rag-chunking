# Scoring page in the app: design

Date: 17.10.2026. Status: approved in chat (structure, blindness, page layout, testing). Decision: new ADR 0034
(scoring in the app, blind item file, read-only after unblinding); extends
[ADR 0032](../../adr/0032-blinde-rubrik-bewertung.md) and keeps [ADR 0027](../../adr/0027-blinde-annotation.md).

## Goal

Score the answers of the blind rubric scoring in the browser instead of reading `scoring_packet.md` and typing into
`scoring_sheet.csv`. The page belongs to the existing app (same start command, same look) and is used first for the
pilot set `data/pilot/hard` (24 answers of H01–H08), later for the main run (144 answers).

Success: all 24 pilot answers can be scored in the app, scores survive a restart, and
`evaluate_answers.py --mode summarise` reads the sheet unchanged.

## Constraints

- Blind (ADR 0032): the page never shows a strategy or chunk ID and never reads `scoring_key.csv`.
- The sheet stays the primary record: same file, same header (`docs/reference/data-formats.md`), written atomically
  (`src/atomic_csv.py`); `summarise`, its checks and its tests do not change.
- Codes appear in the order of the packet (the shuffled order of `scaffold`).
- The catalogue page keeps its guarantee: it never loads chunks, answers, retrieval results or scores (ADR 0027).
- English UI, sentence case, Streamlit 1.58 (theme via `.streamlit/config.toml`, limited CSS), local only, light and
  dark, works at 320, 768 and 1280 px.

## Structure

- `app/catalogue_editor.py` stays the entry point (`uv run streamlit run app/catalogue_editor.py`, unchanged in all
  docs). It becomes a router with `st.navigation`: pages **Catalogue** (default; today's editor, behaviour
  unchanged) and **Scoring**. `st.set_page_config` is called once in the router.
- `app/ui_theme.py` (new): the shared CSS, `LIGHT`/`DARK` palettes and `palette_css()`, moved out of the editor
  without change; both pages import it.
- `app/catalogue_page.py` (new): the editor's page code moved out of `catalogue_editor.py` unchanged
  (`write_tab`, `review_tab`, sidebar, checks); its docstring keeps the ADR 0027 guarantee.
- `app/scoring_page.py` (new): the scoring page; display only.
- `src/scoring_store.py` (new): all scoring logic, tested without Streamlit: finding sets, loading items, reading and
  saving the sheet, progress, the read-only rule.

## Blind item file

`evaluate_answers.py --mode scaffold` additionally writes `scoring_items.jsonl` (`config.SCORING_ITEMS_FILE`; in a
pilot set the same name in the set folder), one JSON object per code in packet order:

```json
{"code": "H01-A", "question_id": "H01", "question": "...", "reference_answer": "...", "answer": "...", "excerpts": ["...", "..."]}
```

- `excerpts`: the texts of the chunks in rank order, exactly what the prompt showed (`src/prompt.py`), no IDs.
- No strategy, no chunk ID, nothing derived from the key; a test checks that no item contains a strategy key or a
  chunk-ID pattern.
- Derived from answers and chunk files like the packet, so ignored by git (`data/evaluation/scoring_items.jsonl`,
  `data/pilot/**/scoring_items.jsonl`). The packet stays for the second rater (ADR 0032).
- Written in the same `scaffold` call as packet, sheet and key; like them it never overwrites an existing sheet or key.

The pilot sheet `data/pilot/hard/scoring_sheet.csv` is still empty. To get the item file, sheet and key are moved
away and `scaffold --set data/pilot/hard --limit 8` runs again with the new code: the fixed `SCORING_SEED` yields the
same codes in the same order (a test asserts determinism), so the committed key does not change in content.

## Store (`src/scoring_store.py`)

- `scoring_sets() -> list[ScoringSet]`: the main set (`data/evaluation`) and every folder below `config.PILOT_DIR`
  that holds an item file; each with a display name ("Main catalogue", "Pilot: hard"), its item, sheet and scores
  paths. Never the key path.
- `load_items(set) -> list[dict]`: items in file order; raises if the item codes differ from the sheet codes (stale
  item file).
- `load_scores(set) -> dict[code, dict]`: the sheet rows; a criterion is `None` while empty.
- `save_score(set, code, values: dict[str, int], notes: str)`: validates the code (in the sheet), every criterion
  (integer 0–`RUBRIC_MAX_SCORE`, all five set), then rewrites the whole sheet atomically with only that row changed.
- `is_read_only(set) -> bool`: true once the set's `scores.csv` exists (scores were unblinded; changing them now would
  no longer be blind).
- `progress(set) -> tuple[int, int]` and per-question counts for the sidebar.

## Scoring page

Layout (two columns from 640 px, stacked below; reuses the editor's classes):

- Sidebar: set selector (only sets from `scoring_sets()`), "**7 of 24 scored**" with a progress bar, a table
  question → "scored of answers" in the same style as the editor's tables, and a note when everything is scored
  (next step: `evaluate_answers.py --mode summarise`).
- Header: the code as title ("H03, answer B") with "question 3 of 8" in muted text, like the editor's slot title.
- Left column (reader): "Answer under review" as a formatted serif page (`.formatted`, rendered with
  `catalogue_store.formatted_html`, no highlights), below it "Excerpts the model saw" as tabs "1"…"5", each a
  formatted page that scrolls inside.
- Right column (form): question, reference answer in a muted card, then the five criteria in `RUBRIC_CRITERIA` order,
  each a segmented control 0 / 1 / 2 whose caption shows the rubric anchor of the chosen value (English rendering
  of `docs/reference/evaluation.md`, e.g. correctness: wrong / partly correct / correct), notes, then
  "Previous", "Save and next" (disabled until all five criteria are set) and a "Jump to" selector of codes.
- Opening the page selects the first unscored code; a scored code shows its saved values. After "Save and next" the
  next code in packet order opens (the next unscored one at the end).
- Read-only set: an info banner ("Scores were unblinded; the sheet is read-only"), controls disabled.
- Errors (missing item file, stale item file, malformed sheet): `st.error` with what to run, no traceback.

## Configuration (new keys)

- `SCORING_ITEMS_FILE = DATA_EVAL / "scoring_items.jsonl"`.
- English rubric anchors stay in `app/scoring_page.py` next to their only use, with a comment pointing to
  `docs/reference/evaluation.md` (display text, not an experiment parameter).

## Documentation

- ADR 0034 (new), ADR README row, 0032 status note "ergänzt durch 0034", AGENTS.md (D1–D34), docs/README.
- `docs/reference/data-formats.md`: `scoring_items.jsonl`, pilot file table.
- `docs/reference/tooling.md`: app row (two pages), versioned/ignored table, repo tree (`app/` files).
- `docs/how-to/run-the-experiment.md`: scoring in the app as the default, packet and sheet as fallback and for the
  second rater.
- `docs/reference/configuration.md`: `SCORING_ITEMS_FILE`. `.serena/memories/pipeline.md`: scoring page note.

## Testing

- `tests/test_scoring_store.py`: sets found (main and pilot, only with item file, never the key); items in order;
  stale item file rejected; save changes exactly one row, atomically, keeps the header; unknown code, value outside
  0–2, a missing criterion rejected; read-only once `scores.csv` exists (save refused); progress counts.
- `tests/test_evaluate_answers.py`: scaffold writes the item file in packet order with the prompt's excerpts; no
  strategy key or chunk ID in it; a second scaffold with the same seed yields identical codes and order.
- `tests/test_scoring_page.py` (AppTest): page renders without exception; save and next moves on and writes the sheet;
  read-only banner; the page source never contains `scoring_key` (static check on `app/scoring_page.py` and
  `src/scoring_store.py`).
- `tests/test_catalogue_editor.py` keeps passing unchanged against the router (default page Catalogue).
- Browser (playwright-cli) at 320, 768 and 1280 px, light and dark, main flow scored end to end on a copy of the pilot
  set; then the impeccable `audit` and `polish` passes.
