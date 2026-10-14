# Question catalogue tools: design

Date: 14.10.2026. Status: approved in chat (sections 1–3). Decisions: new ADR 0029 (question types and construction
classes, refines [ADR 0017](../../adr/0017-fragenkatalog.md)), new ADR 0030 (freeze lock); existing
[ADR 0009](../../adr/0009-hypothesen.md), [ADR 0017](../../adr/0017-fragenkatalog.md),
[ADR 0022](../../adr/0022-h1-abschnitte-in-ground-truth.md), [ADR 0025](../../adr/0025-korpus-guide-api-styleguide.md),
[ADR 0027](../../adr/0027-blinde-annotation.md), [ADR 0028](../../adr/0028-c4-bedingung.md).

## Goal

Give Jonas the tools to write and annotate the question catalogue (48 questions, ADR 0029 within the range of ADR 0017) against the
813 sections of the corpus, and make the catalogue's composition a checked, pre-registered property instead of a
judgement made while writing:

1. Fixed values for `type` and `difficulty` in `questions.csv`, with rules that can be checked against the annotation.
2. A section lookup list, a text search and a section viewer, so relevant sections are found across all three areas.
3. A coverage check that enforces quotas, class rules and area floors.
4. A freeze that records the final catalogue and makes retrieval on any other version impossible.

Jonas writes every question, reference answer and relevance judgement; the tools only find, show and check.

Success criteria:

- `catalogue.py sections|find|show|check|freeze` run on the real corpus; `section_index.md` has 813 rows and every
  `section_id` in it resolves in `sections.jsonl`.
- `check` fails on every rule violation listed below and passes on a valid synthetic catalogue; `--draft` reports
  without failing on quotas.
- `retrieve.py` refuses the main catalogue without a matching freeze record, before any API call; pilot sets are
  unaffected.
- No tool reads embeddings, Chroma, chunks or retrieval results, and none calls the OpenAI API.
- `uv run pytest`, pre-commit and Pyright pass.

## Decisions and evidence

| Decision | Evidence | Alternatives rejected |
|---|---|---|
| 48 questions (ADR 0029) | ADR 0017 allows 30–60 and the reference page names 40–50 as optimal; the exposé says "etwa 40". The standard error of a mean falls with √n: 48 instead of 40 lowers it by about 9 %, 60 by about 18 %. Power (paired t-test, 80 %, two-sided α = 0.05, computed with SciPy's noncentral t): with 12 questions per class only large effects (d ≈ 0.89; 10 per class: 1.00) are detectable, so per-class results stay exploratory (ADR 0009); over all 48 questions d ≈ 0.41 (40: 0.45). Cost is Jonas' time: about 8 more hours of writing and blind annotation and 24 more answers to score by hand than with 40; the freeze milestone 09.11. stays reachable (ADR 0028). The thesis states the deviation from the exposé. | 40 (no gain, but safest for the milestone); 60 (about 20 more hours and 60 more answers to score; type quotas no longer divide cleanly; puts the milestone at risk). |
| `type` ∈ {`factual`, `procedural`, `conceptual`, `comparative`, `limitation`}, quotas 12/12/12/6/6 (ADR 0029) | ADR 0017 fixes the five types and the ratio 2:2:2:1:1 (10/10/10/5/5 for 40); the spellings are those the pilot sets already use. H3 needs the type (ADR 0009). | New names (pilot files would disagree). |
| `difficulty` holds the construction class ∈ {`single`, `multi-section`, `detail`, `paraphrase`} (ADR 0029) | Pilot probe 2 (experiment record, 14.10.2026): easy questions reach Hit@5 = 1.0 for every strategy (ceiling), while the construction classes separate C3 and K1 (multi-section and detail favour C3, paraphrase favours K1). H3 names "abschnittsübergreifende" questions, which is a construction property. The class is assigned when the question is written and checked against Jonas' own annotation, never against results. | Subjective easy/medium/hard (judgement a grader can question; class only in `notes`, fragile to analyse); an additional column (format change, `difficulty` stays subjective). |
| Class quotas 12/12/12/12 (ADR 0029) | Equal group sizes give the most reliable per-class comparison with n = 48; a 25 % share of `single` questions keeps realistic everyday questions and shows the ceiling effect openly. | Hard-heavy 6/12/10/12 (less representative, small `single` group); floors only (split decided while writing). |
| Area floors: ≥ 12 questions with a relevant section in `api`, ≥ 3 in `style-guide`; a question counts for every area it touches (ADR 0029) | Corpus tokens (ADR 0025): guide 117,694 (71 %), API 42,488 (26 %), style guide 5,541 (3 %). 26 % of 48 ≈ 12; 3 % of 48 ≈ 1, raised to 3 so the area is measurable. Without a floor, questions drift to the guide. | Strict proportional split (1 style-guide question is not measurable; many answers span guide and API); report only. |
| Class rules (below) check only the annotation and the wording (ADR 0029) | Blind annotation (ADR 0027): nothing derived from retrieval may shape questions or judgements. Pilot measurements: H2/H3 sections median 211 tokens (p25 120, p75 356); pilot `detail` sections 22–546 tokens, so "detail" is about the answer, not the section length; 5 of 7 pilot paraphrases share no heading word, 2 share one. | Thresholds from retrieval results (circular); section-length rule for `detail` (contradicted by the pilot). |
| Lexical `find` over cleaned section texts (this spec) | Equal for all strategies, uses no chunk, vector or rank; it only helps Jonas look beyond the obvious page (rule in `question-catalogue.md`: search the whole corpus including the API). | Embedding search (would be retrieval before the freeze, ADR 0027). |
| Freeze lock: `freeze` writes SHA-256 of `questions.csv`, `ground_truth.csv` and `sections.jsonl`; `retrieve.py` refuses the main catalogue unless all three hashes match (ADR 0030) | ADR 0017 and 0027 require the ground truth to be final before any retrieval; a recorded hash turns this into a check the code enforces and gives the 09.11. milestone (ADR 0028) a citable record. | Convention only (a promise, not evidence). |

## Class rules

Words are compared after a fixed normalisation: lowercase, words matched by `[a-z0-9]+`, words in
`config.CATALOGUE_STOPWORDS` dropped; a camelCase identifier also counts by its parts (`defineProps` → `defineprops`,
`define`, `props`). Two words match if (a) their plural forms intersect: each word of at least four characters also
stands for itself without a trailing `s`, without `es`, and with `ies` → `y`; or (b) they share a common prefix of at
least max(4, length of the shorter word − 3) characters (`watch`/`watchers`, `mounted`/`mounting`,
`reactive`/`reactivity`; not `compiler`/`computed`). The rule errs towards reporting a shared word, the safe direction
for a check that must catch overlap; plural folding alone missed derivations (task 3 review, 14.10.2026), and with (b)
5 of the 7 pilot paraphrase questions would fail. The heading words of a question are the words of the `title` of each
relevant section plus the `title` of the H1 section of its document.

| Class | Rule | Checked by `check` |
|---|---|---|
| `single` | Exactly 1 relevant section; the answer is that section's main content. | number of sections = 1 |
| `multi-section` | ≥ 2 relevant sections; the answer needs all of them. | number of sections ≥ 2; report also counts questions whose sections lie on ≥ 2 pages |
| `detail` | Exactly 1 relevant section; the answer is one specific fact that takes a small part of the section. | number of sections = 1; `expected_answer` ≤ `config.DETAIL_MAX_ANSWER_WORDS` (30) words; the report shows section tokens next to answer words for the manual "small part" judgement |
| `paraphrase` | Exactly 1 relevant section; the question uses no heading word. | number of sections = 1; overlap of normalised question words with heading words = 0 |

Only `single` questions may reuse heading words. The report lists, for `detail` and `multi-section` questions, the
heading words they share, so wording that makes them easy is visible.

## Components

All in `src/catalogue.py` (CLI with subcommands, like the other steps); parameters in `src/config.py`.

| Subcommand | Reads | Writes / prints |
|---|---|---|
| `sections` | `documents.jsonl`, `sections.jsonl` | `config.SECTION_INDEX_FILE` = `data/processed/section_index.md`: Markdown table, one row per section in `sections.jsonl` order: `section_id`, area (first path segment: `api`, `guide`, `style-guide`, the keys of the area floors), page path, heading path (`H1 › H2 › H3`), tokens. Deterministic; header states source and that it is generated. |
| `find TERM` | same | sections whose cleaned text contains `TERM` (case-insensitive, plain substring), in `sections.jsonl` order, with `section_id`, heading path and a one-line excerpt around the first match. Innermost section wins: a match inside an H3 is reported for the H3, not again for its H2/H1 parents. |
| `show SECTION_ID` | same | the section's heading path, token count and exact text (the same slice `relevance.py` uses). Unknown ID: error, exit 1. |
| `check [--draft]` | `questions.csv`, `ground_truth.csv`, `sections.jsonl`, `documents.jsonl`, pilot `questions.csv` files under `config.PILOT_DIR` | format validation as `retrieve.py` (shared functions, not a copy); allowed values; class rules; quotas; area floors; duplicate questions (normalised text equal) within the catalogue and against every pilot set. Prints a type × class table, the area split and every finding with its `question_id`. Strict mode exits 1 on any finding; `--draft` exits 1 only on format errors and unknown values/IDs, and reports quota and rule findings as warnings. |
| `freeze` | as `check` | runs `check` strictly; on success writes `config.CATALOGUE_FREEZE_FILE` = `data/evaluation/catalogue_freeze.json` with `date`, `questions`, the counts per type and class and `sha256` of both CSV files and `sections.jsonl` (added after the final review: the record alone shows which segmentation the section IDs refer to). Refuses to overwrite an existing record (a re-freeze needs a new ADR and a manual delete). |

`retrieve.py`: when `questions_file` or `ground_truth_file` resolves to `config.QUESTIONS_FILE` or
`config.GROUND_TRUTH_FILE`, it reads the freeze record and aborts before embedding the questions unless the hashes of
both CSV files and `sections.jsonl` match ("catalogue not frozen" / "catalogue changed since freeze"). Other files (pilot sets, `difficulty_probe.py`,
tests) are not affected.

## Configuration (new keys, all in `configuration.md`)

`QUESTION_TYPES` (dict value → quota), `QUESTION_CLASSES` (dict value → quota), `AREA_MIN_QUESTIONS`
(`{"api": 12, "style-guide": 3}`), `DETAIL_MAX_ANSWER_WORDS = 30`, `CATALOGUE_STOPWORDS` (tuple, English function
words and question words, listed in the ADR), `SECTION_INDEX_FILE`, `CATALOGUE_FREEZE_FILE`. The quotas sum to 48, so
the strict check requires exactly 48 questions.

## Documentation

- ADR 0029 and ADR 0030 (Nygard format, German like the other ADRs); ADR 0017 gets a status back-link.
- `docs/reference/data-formats.md`: allowed values, `section_index.md`, `catalogue_freeze.json`.
- `docs/reference/question-catalogue.md`: values, quotas, class rules, area floors; the comparative example
  "Options API vs Composition API" is replaced by one that fits the Composition-only corpus (ADR 0025).
- New how-to `docs/how-to/build-the-question-catalogue.md`: `sections` → `find`/`show` → write → `check --draft` →
  `freeze`.
- `docs/reference/tooling.md`, `docs/reference/configuration.md`, `docs/plan.md#stand` (open decision on
  `type`/`difficulty` closed), Serena memories (summary plus link).

## Testing

TDD; synthetic fixtures in `tmp_path`, no network, no API.

- Normalisation: lowercase, stopwords, `s`/`es` folding, short words untouched.
- Each class rule: one passing and one failing question.
- Quotas, area floors (a cross-area question counts for both), unknown `type`/`difficulty`, duplicate within the
  catalogue, duplicate of a pilot question.
- `--draft` vs strict exit codes.
- `sections`: deterministic output, one row per section; `find`: innermost match only; `show`: exact slice, unknown ID.
- `freeze`: record content, refusal to overwrite, refusal on a failing check.
- `retrieve.py`: main catalogue without record, with changed file, with matching record (stub embedder, no API);
  pilot paths unaffected.
- Integration test on the real corpus (skips without the snapshot, like the others): 813 rows, every ID resolves.

## Out of scope

Writing the questions and annotations themselves; second rater (open decision in `plan.md`); evaluation scripts;
C4 (ADR 0028).
