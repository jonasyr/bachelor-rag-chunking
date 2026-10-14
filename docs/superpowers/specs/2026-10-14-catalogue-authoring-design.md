# Catalogue authoring support: design

Date: 14.10.2026. Status: approved in chat (sections 1–3). Decisions: new ADR 0031 (random sampling plan, skip rule,
AI review procedure); builds on [ADR 0017](../../adr/0017-fragenkatalog.md),
[ADR 0027](../../adr/0027-blinde-annotation.md), [ADR 0029](../../adr/0029-fragetypen-und-konstruktionsklassen.md),
[ADR 0030](../../adr/0030-einfrieren-des-fragenkatalogs.md).

## Goal

Make writing the 48-question catalogue easy and methodologically stronger, while Jonas keeps writing every question,
reference answer and relevance judgement (exposé: "manuell kuratierter Fragenkatalog"; ADR 0017:
Eigenleistung; IU KI-Richtlinie: AI must not replace data collection meant to be done by a person):

1. **Sampling plan:** a seeded, reproducible draw of one starting section per slot, so topics are a random sample of
   the documentation instead of the author's choice.
2. **Catalogue editor:** a local browser editor for writing and annotating, with live rule checks and progress.
3. **Review rounds with a log:** AI suggestions (missed sections, wording, facts, class) recorded as rows that Jonas
   accepts or rejects; the log feeds the AI disclosure.

Out of scope: second human rater (recorded in `docs/plan.md` as "later, if time allows"); answer scoring.

Success criteria:

- `catalogue.py plan` writes the same plan for the same corpus and seed on any machine and Python version.
- `check` enforces slot, class, starting section and skip rules; `freeze` refuses with open review suggestions.
- The editor writes `questions.csv`/`ground_truth.csv` in the exact documented format, never shows chunks,
  strategies, retrieval or scores, and is read-only after the freeze.
- `uv run pytest`, pre-commit and Pyright pass; the editor is checked in a browser (playwright-cli) at 320, 768 and 1280 px and passes
  the `impeccable` audit.

## Decisions and evidence

| Decision | Evidence | Alternatives rejected |
|---|---|---|
| Draw starting sections by text length: a random token position in the area's innermost H2/H3 sections, the section containing it is drawn (ADR 0031) | Every piece of text equally likely; 644 innermost H2/H3 sections (guide 431, API 183, style guide 30), median 190 tokens, 30 under 50 tokens. Equal weight per section would over-represent tiny sections, where C3 chunks coincide with section borders, and so could favour C3. | Every section equally (C3-favouring risk); every page equally (short pages over-weighted). |
| Slot fixes area and class; type chosen by Jonas (ADR 0031) | Areas: 12 API, 3 style guide, 33 guide (area floors of ADR 0029). Classes 12 each, randomly spread. The content of a random section often does not suit a forced type; class works on any section. | Area + class + type (awkward questions, many skips); area only (class chosen by convenience). |
| Skips only with a fixed reason, replacement from a pre-drawn reserve of the same area, every skip logged and reported (ADR 0031) | Some sections are code listings, link lists or repeat a topic; a fixed reason list and fixed reserve order keep the sample auditable. | Free skips (selection bias); no skips (forced, poor questions). |
| Hash-based draw instead of a library RNG (this spec) | Python only guarantees the `random()` stream across versions, NumPy's `Generator` streams may change; SHA-256 of `"{seed}:{area}:{k}"` is stable everywhere. | `random.choices`/NumPy (reproducibility not guaranteed across versions). |
| AI review as logged suggestions, decisions by Jonas (ADR 0031) | IU KI-Richtlinie: AI as Hilfsmittel allowed, responsibility and independent performance stay with the student, disclosure recommended. The pilot's post-hoc annotation shifted Recall@5 by up to 0.07: missed sections are the largest measured risk. The review reads only questions, annotation and corpus text (blind, ADR 0027). | AI writes questions or annotation (contradicts exposé and KI-RL); no review (missed sections). |
| Freeze records plan and review hashes; refuses open suggestions (ADR 0031, extends ADR 0030) | The record alone then shows that topics were drawn and every suggestion was decided before retrieval. The retrieval gate keeps checking only its inputs (questions, ground truth, sections, documents). | Gate on plan/review too (they do not influence retrieval). |

## Sampling plan

`catalogue.py plan` (refuses to overwrite an existing plan, like the freeze record):

- Candidates per area: innermost sections of level 2 or 3 (no other section inside them), in `sections.jsonl` order;
  the area is the first path segment of the document. An area's token line is the concatenation of its candidates'
  token spans in that order.
- Draw `k = 0, 1, 2, …` per area: position `p = int(sha256(f"{seed}:{area}:{k}")) mod total tokens of the area`; the
  candidate containing `p` is drawn unless it was drawn before (then `k` moves on). Draw until the area has
  `CATALOGUE_AREA_SLOTS[area] + CATALOGUE_RESERVE[area]` distinct sections.
- The first `CATALOGUE_AREA_SLOTS[area]` draws of an area are slots, the rest its reserve, in draw order. Slots are
  numbered `S01`… in area order `api`, `style-guide`, `guide` and draw order.
- Classes: the 48 class values (12 each, `config.QUESTION_CLASSES`) are ordered by `sha256(f"{seed}:class:{i}")` of
  their index `i` and assigned to `S01`… in that order.
- `data/evaluation/catalogue_plan.csv` (versioned), one row per drawn section:
  `area,draw,section_id,slot_id,class,status,skip_reason,question_id`; `status` ∈ {`open`, `used`, `skipped`,
  `reserve`}. A slot row starts `open`; reserve rows have empty `slot_id` and `class`.
- **Skip:** the open row becomes `skipped` with a reason from `config.CATALOGUE_SKIP_REASONS`
  (`code-or-links`, `too-short` (under `CATALOGUE_SKIP_MIN_TOKENS` = 50 tokens), `duplicate-topic`,
  `no-answerable-content`); the first `reserve` row of the same area takes over `slot_id` and `class` and becomes
  `open`. No reserve left: error (enlarge the reserve by a new ADR).
- **Use:** saving a question for a slot sets the row to `used` with the `question_id`.

Rules added to `check` (findings; errors for format): plan file present and well-formed; every question belongs to
exactly one `used` row; its `difficulty` equals the row's class; the row's `section_id` is among its
`relevant_section_ids`; every `skipped` row has an allowed reason; reported: skipped count per area and reasons.

## Editor

`app/catalogue_editor.py` (Streamlit, already a dependency; `app/streamlit_app.py`, the later RAG demo, stays
untouched): `uv run streamlit run app/catalogue_editor.py`. All logic in tested functions of `src/catalogue.py`; the
editor only calls them.

- Sidebar: type × class grid against quotas, area floors, slots open/used/skipped, open review suggestions.
- Tab "Write": the next open slot (area, class, starting section text); search (`find`) with excerpts, a section
  viewer and "add section"; form for question, type, reference answer, notes; live checks (class rule, highlighted
  heading words, answer word count, duplicates); "Save" (writes both CSVs, marks the slot `used`), "Skip slot"
  (reason list), "Edit" for an existing question (same slot).
- Tab "Review": open suggestions with accept/reject and a reason; accepting `missing_section` adds the section to the
  question's annotation.
- Read-only once `catalogue_freeze.json` exists. Never shows chunks, strategies, retrieval results or scores.
- Writes are deterministic: rows sorted by `question_id`, `\n` line endings, documented headers only.
- Design process (loadout workflow, requested by Jonas): the `frontend-design` skill sets the direction (layout,
  hierarchy, theme via `.streamlit/config.toml`), then build, then `playwright-cli` renders the editor at 320, 768
  and 1280 px, exercises the main flows (write, add section, save, skip, review decision) and reads the console,
  then the `impeccable` skill's `audit` and `polish`. The editor is not done before that browser check.

### Visual design (frontend-design, approved goal: professional for a thesis, modern, pleasing, not cluttered)

Subject: a workbench for writing one well-formed question per slot without losing sight of the source. One user,
long focused sessions, much reading.

- **Concept, "reading desk":** the starting section is set like a printed page on the left (serif, comfortable
  measure under 80 characters); the form sits on the right. **The one memorable element:** while typing, question
  words that match heading words are marked in the source text and the heading like a highlighter stroke, so the
  paraphrase rule is visible, not just reported. Everything else is quiet.
- **Palette (light / dark):** paper `#FAFBFC` / `#15191E`; surface `#FFFFFF` / `#1D232A`; ink `#1F2933` / `#E4E8EC`;
  muted `#616E7C` / `#9AA5B1`; line `#D9DEE4` / `#2E3640`; accent ink blue `#2457A6` / `#3F72C9` (dark value raised to 4.71:1 for white button text after the audit); highlighter
  `#FFE58A` / `rgba(255, 214, 90, 0.35)`; ok `#2F7D4F`; problem `#B3261E`. Deliberately not the cream-and-terracotta
  or black-and-neon defaults.
- **Type:** UI in Streamlit's sans-serif; the source text in a serif (Source Serif 4 with Georgia fallback, larger
  line-height); code in the source keeps monospace. Sentence case everywhere, no all-caps labels.
- **Layout:**

  ```
  1280 px                                                     320 px
  ┌ progress ┐┌ Slot S07: API reference, paraphrase ─────────┐ ┌ Slot S07 ┐
  │ 21 of 48 ││ Write | Review (3)                            │ │ source   │
  │ grid     ││ ┌ source page ─────────┐ ┌ your question ────┐ │ │ question │
  │ areas    ││ │ heading path          │ │ question          │ │ │ checks   │
  │ slots    ││ │ text with highlights  │ │ type, answer      │ │ │ find     │
  │          ││ └──────────────────────┘ │ sections, checks  │ │ └──────────┘
  │          ││ find more sections        │ Save · Skip       │ │
  └──────────┘└──────────────────────────────────────────────────┘
  ```

  Left-aligned throughout; on narrow screens the columns stack (source, question, checks, find) and the sidebar
  collapses.
- **Checks** are a short plain list (met / not met with the reason), not badges or cards. **Copy:** plain verbs that
  say what happens ("Save question", "Skip this section", "Accept", "Reject"); errors say what is wrong and how to fix
  it; an empty Review tab says "No open suggestions."
- **Motion:** none except Streamlit's own feedback on save.
- Theme via `.streamlit/config.toml` (`[theme.light]`, `[theme.dark]`); custom CSS only for the source page and the
  highlight; visible keyboard focus kept.

## Review log

`data/evaluation/catalogue_review.csv` (versioned):
`round,question_id,kind,suggestion,section_id,decision,reason,date`; `kind` ∈ {`missing_section`, `wording`, `fact`,
`class`}; `decision` ∈ {`open`, `accepted`, `rejected`}; `section_id` only for `missing_section`.

- Claude appends rows with `decision = open` after a block ("review block N"), reading only questions, annotation
  and corpus text; it never edits `questions.csv` or `ground_truth.csv`.
- Jonas decides in the editor; a decision needs a reason for `rejected`.
- `check` validates the format and reports open suggestions (warning in draft, finding in strict); `freeze` refuses
  while any row is `open`; the summary line (suggestions, accepted/rejected per kind) is printed by `check` and goes
  into the AI disclosure.

## Freeze (extends ADR 0030)

The record adds the SHA-256 of `catalogue_plan.csv` and `catalogue_review.csv`; `require_frozen` keeps checking the
four retrieval inputs.

## Configuration (new keys)

`CATALOGUE_SEED` (fixed now: `20261014`, the date of this decision; never tuned), `CATALOGUE_AREA_SLOTS`
(`{"api": 12, "style-guide": 3, "guide": 33}`, sum 48), `CATALOGUE_RESERVE` (per area, `{"api": 12,
"style-guide": 3, "guide": 33}`), `CATALOGUE_SKIP_REASONS`, `CATALOGUE_SKIP_MIN_TOKENS = 50`, `CATALOGUE_PLAN_FILE`,
`CATALOGUE_REVIEW_FILE`.

## Documentation

ADR 0031; ADR 0030 status back-link; `docs/how-to/build-the-question-catalogue.md` rewritten around plan → editor →
review rounds → freeze; `data-formats.md` (plan, review); `configuration.md`; `tooling.md`; `docs/plan.md` (blocks of
8, schedule to the freeze, second rater "later, if time allows"); memories.

## Testing

TDD, no network or API.

- Draw: same seed → identical plan; different seed → different plan; token position maps to the containing
  candidate; only innermost H2/H3; no duplicates; slot and reserve counts; class counts 12 each; refuses to
  overwrite.
- Skip: valid reason moves the slot to the next reserve row; invalid reason and empty reserve are errors.
- Check: question without slot, class mismatch, starting section missing from the annotation, bad skip reason, open
  review rows (warning in draft, finding in strict), review format errors.
- Editor functions: save new question (both CSVs, slot `used`, IDs and doc IDs derived), edit, decide review
  (accept adds the section), read-only after freeze.
- Editor UI: `streamlit.testing.v1.AppTest` smoke tests (renders, save, skip); browser check with playwright-cli at
  320/768/1280 px and the `impeccable` audit (see Editor).
- Freeze: record contains plan and review hashes; refuses with open review rows.
