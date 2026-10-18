# Catalogue quotas and sampling plan on e2e: design

Date: 18.10.2026. Status: approved in chat (18.10.2026). Decision basis: [ADR 0038](../../adr/0038-korpus-e2e.md),
[ADR 0029](../../adr/0029-fragetypen-und-konstruktionsklassen.md),
[ADR 0031](../../adr/0031-stichprobenplan-und-ki-durchsicht.md). Step 4a of the corpus switch
([plan](../../plan.md#stand)); the closed-book screen (4b) and the control K0 (4c) get their own specs.

## Goal

The catalogue tools work on the 15 e2e areas: area slots, reserve and minimums replace the Vue keys, the stopword list
names the e2e product instead of Vue, and the e2e sampling plan is drawn once. Afterwards Jonas can write questions.
No OpenAI calls; catalogue size (48), types (4 × 12) and classes (12/12/6/6) stay.

Success criteria:

- `CATALOGUE_AREA_SLOTS`, `CATALOGUE_RESERVE`, `AREA_MIN_QUESTIONS` have exactly the keys of `CORPUS_AREAS`, in that
  order, with the values below; slots sum to 48.
- `data/evaluation/catalogue_plan.csv` holds the e2e draw (48 slots S01–S48 in navigation order, 48 reserve rows);
  the Vue plan lies unchanged at `data/evaluation/archive_vue/catalogue_plan.csv` (moved with `git mv`).
- The freeze check's plan comparison passes on the new plan.
- `uv run pytest` and `uvx pre-commit run --all-files` pass.

## Area quotas (decided 18.10.2026)

Slots proportional to the area's share of tokens after preprocessing (250,380 tokens), every area at least 1, the
remaining 33 slots distributed by largest remainder over the shares above 1 slot. Reserve = slots per area (as in
ADR 0031). Minimum questions with a relevant section in the area = slots (every area, unlike Vue's buffer area: with
15 areas none dominates as the Vue guide did with 71 %).

| Area | Tokens | Share | Slots = reserve = minimum | Candidate sections (innermost H2/H3) |
|---|---:|---:|---:|---:|
| Get started | 12,558 | 5.0 % | 2 | 29 |
| Platforms | 10,908 | 4.4 % | 2 | 26 |
| Features | 11,473 | 4.6 % | 2 | 43 |
| Models and agents | 11,962 | 4.8 % | 2 | 21 |
| Run in CI | 10,114 | 4.0 % | 2 | 31 |
| Hosted browsers and devices | 10,940 | 4.4 % | 2 | 45 |
| Extend | 6,703 | 2.7 % | 1 | 27 |
| Deep dive | 15,059 | 6.0 % | 3 | 48 |
| Migrate | 19,210 | 7.7 % | 4 | 26 |
| Test API | 37,134 | 14.8 % | 7 | 56 |
| Project | 61,029 | 24.4 % | 12 | 82 |
| Web | 11,033 | 4.4 % | 2 | 9 |
| Mobile | 10,203 | 4.1 % | 2 | 9 |
| Engine contract | 21,507 | 8.6 % | 4 | 18 |
| Examples | 547 | 0.2 % | 1 | 3 |

The values are written into `src/config.py` as literals, not computed at run time, so a corpus change cannot shift
them silently; the derivation lives in ADR 0039.

## Other settings

- `CATALOGUE_STOPWORDS`: `"e2e"` replaces `"v"` and `"vue"` (42 headings of the section index contain "e2e"; without
  it the paraphrase rule would flag every question naming the product).
- `CATALOGUE_SEED` stays `20261014` (ADR 0031: fixed, never tuned; a new seed would allow choosing a draw).

## Units

| Unit | Change |
|---|---|
| `src/config.py` | the three dicts and the stopwords as above; "Vue areas until step 4" comments go |
| `src/catalogue_plan.py`, `src/catalogue.py` | none expected: both read the dicts only; area names with spaces enter the hash `"{seed}:{area}:{k}"` and the CSV column `area` unchanged |
| `app/catalogue_page.py` | `AREA_NAMES` (Vue key → label) goes; areas are shown by their name |
| `data/evaluation/` | `git mv catalogue_plan.csv archive_vue/catalogue_plan.csv`, then `uv run python src/catalogue.py plan` writes the e2e plan |
| `docs/adr/0039-…` | new ADR: replaces the slot numbers of ADR 0031 and the area minimums of ADR 0029; seed, draw, skip reasons, AI review stay; Vue plan archived, not overwritten |

## Error handling

Unchanged: `plan` refuses to overwrite an existing plan; a draw that runs out of candidates or reserve raises with the
area name. The new config test fails if a dict's keys drift from `CORPUS_AREAS`.

## Testing

- Config test: keys of slots, reserve and minimums equal `CORPUS_AREAS` in order; slots sum to the catalogue size;
  every slot ≥ 1; minimum = slots; reserve = slots.
- Integration test on the real snapshot (skips without it): every area has at least slots + reserve candidate
  sections; drawing twice gives the same plan; the committed plan passes `plan_integrity` against a fresh draw.
- Unit tests of `catalogue_plan.py` and the editor keep their own small dicts (`api`, `guide`, …); they do not depend
  on the configuration.

## Documentation

`corpus.md` (Slots column in the areas table, link to ADR 0039), `configuration.md`, `how-to/build-the-question-catalogue.md`,
`experiment-record.md` (plan drawn, date, plan SHA-256), `adr/README.md`, `plan.md` (4a done), `.serena/memories`.

## Out of scope

Closed-book screen and its judge (4b), control K0 (4c), any question, reference answer or relevance judgement.
