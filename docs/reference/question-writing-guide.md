# Question writing guide

*[Doku-Index](../README.md) · Referenz · Verwandt: [Fragenkatalog](question-catalogue.md), [Fragenkatalog erstellen](../how-to/build-the-question-catalogue.md), [Evaluation](evaluation.md#regelbasierte-bewertung)*

Working guide for writing the catalogue in the editor, in English like the questions. The binding rules live in
[Fragenkatalog](question-catalogue.md) and the ADRs linked there ([ADR 0029](../adr/0029-fragetypen-und-konstruktionsklassen.md),
[ADR 0027](../adr/0027-blinde-annotation.md), [ADR 0022](../adr/0022-h1-abschnitte-in-ground-truth.md),
[ADR 0040](../adr/0040-closed-book-pruefung.md)); values come from `src/config.py`. If this page and those disagree,
they win. Examples use placeholders only: real e2e examples are written by Jonas ([Backlog](../plan.md#backlog), item 10).

## One slot in five steps

1. **Read the class box** at the top. The plan fixes the class (`difficulty`) of the slot; you do not choose it.
2. **Read the starting section** and pick *one* thing in it that a developer would actually want to know.
3. **Check where else it stands:** "Also covered elsewhere" and "Find more sections" (or ask Claude for a mechanical
   `catalogue.py find` list). This decides whether the class still works (see the class rules below).
4. **Write the question, then the reference answer**, then pick the type by click.
5. **Add the relevant sections**, run through the [checklist](#checklist-before-save), save.

Order is free: do easy slots (`single`, `detail`) first when stuck; a slot's draw is fixed, not the order you work in.

## Construction classes (fixed by the plan)

| Class | Rule (checked) | What makes it work | Typical mistake |
|---|---|---|---|
| `single` | Exactly one relevant section; its **main content** is the answer. | Ask about what the section is mainly about. | The answer adds things from other sections, which turns it into two sections. |
| `multi-section` | At least two relevant sections, **each adds a needed part**. A section nested inside another listed one does not count. | Pick a task where this section gives one half and another section the other half (e.g. *set it up* here, *its limit* elsewhere). | Listing extra sections that only repeat a part already covered: each listed section must contribute to the answer. |
| `detail` | Exactly one section; the answer is **one single fact**, reference answer **at most 30 words**. | A value, name, default, limit, flag or package that stands **only in this section**. | The fact is duplicated elsewhere (tables, quickstarts), so a second section becomes relevant and the class breaks. Check "Also covered elsewhere" first. |
| `paraphrase` | Exactly one section; the question shares **no content word** with the section heading or its page title (H1). | Describe the thing in everyday words instead of its name. | Word forms still count as shared: the check matches plurals and common prefixes (e.g. *host* / *hosted*, *device* / *devices*). The editor highlights the words. |

Word comparison for `paraphrase`: lowercase words, stopwords removed (`config.CATALOGUE_STOPWORDS`, includes *how*,
*what*, *can*, *e2e*), camelCase split into parts; two words match on shared plural forms or a shared start of at least
max(4, shorter word length − 3) characters. In doubt the rule reports a match.

## Question types (you choose)

Quotas: `factual` 12, `procedural` 12, `conceptual` 12, `comparative` 6, `limitation` 6. Any type can go with any
class; the quotas count separately. The editor suggests a type from keywords (`config.QUESTION_TYPE_HINTS`); the
suggestion only matches words, so judge by what the question **asks**, not by a keyword (for example, *instead of*
triggers `comparative` although the question may just ask for a fact).

| Type | Asks for | Form | Use it when the section … |
|---|---|---|---|
| `factual` | a fact: which, what value, which name | *Which … does … support?* / *What is the default …?* | states values, options, names, defaults |
| `procedural` | steps or the way to do something | *How do I …?* | shows commands, config or a sequence |
| `conceptual` | what something is and why or when it matters | *What is … and why …?* / *When should I …?* | explains a mechanism or a reason |
| `comparative` | the difference between **two named things** | *What is the difference between … and …?* | contrasts two options, modes or tools |
| `limitation` | what fails, is not supported, or happens in an error case | *What happens if …?* / *Can … ?* (answer: no, because …) | states limits, errors, unsupported cases |

`comparative` and `limitation` are scarce (6 each): keep them for sections with a real contrast or failure case.

## Writing the question

- **English, one question, one ask.** "How are X stored, compared and updated?" is three questions; each ask becomes
  a key point the generated answers must all cover.
- **Self-contained:** understandable without seeing the section; name the feature (no "this", "it", "the table").
- **Specific to e2e:** ask what the documentation says, not general testing knowledge. At least 32 of 48 questions
  must be ones the model cannot answer without retrieval (closed-book check below), so general questions are expensive.
- **Like a real developer asks:** natural, not a copy of a heading or sentence from the section (for `paraphrase` this
  is a hard rule, for the others good practice).
- **Not from the pilot:** never reuse pilot questions; the check catches exact copies only.

## Writing the reference answer

The reference answer pre-fills the **key points** for scoring: the app splits it at semicolons and at sentence ends
before a capital letter, at most `config.KEY_POINTS_MAX` = 4 points (the rest stays in point 4); you check and edit the
points before scoring and freeze them. Point 1 is the **core point** (the direct answer). Generated answers are scored
on whether they contain each point ([Evaluation](evaluation.md#regelbasierte-bewertung),
[ADR 0037](../adr/0037-praezisierte-pruefregeln-und-vorbefuellte-kernpunkte.md)). The cleaner the answer, the less
editing later. So:

- **First sentence = the direct answer** to the question. Everything else supports it.
- **One sentence per point, at most four points.** A fifth sentence is merged into the fourth point. Start each
  sentence with a capital letter (not with a backticked name, which does not split) and avoid `;` inside a point.
- **Only what the annotated sections say.** Nothing from other sections, general knowledge or your own inference;
  that would be a point no correct RAG answer can be sure to contain.
- **Only what the question asks.** Extra but true details (costs, tips, side notes) become key points too and make
  correct answers look incomplete. Leave them out.
- **Exact names in backticks:** commands, options, packages, env variables as in the docs (`npx e2e run --flag`); a
  short code block is fine for commands.
- **Length:** `detail` at most 30 words (checked). Otherwise 1–4 sentences, about 20–80 words is a good range.
- **Spelling:** proofread once; the answer is part of the thesis data.

Template:

```
<Direct answer in one sentence>. <Needed detail 2>. <Needed detail 3, if asked>.
```

## Relevant sections

- The **starting section is always relevant**.
- Add **every section that contains a needed part of the answer**, also literal duplicates (the same table on two
  pages): if a part stands in two places, both are relevant. Search the whole corpus, also the Reference tab.
- Do **not** add a section nested inside one already listed (it adds no text; the check reports it).
- **H2/H3 sections only.** An H1 (whole page) only when the whole page is the answer, with the reason in `notes`.
- Annotation is **blind**: no retrieval or embedding search on the questions before the freeze
  ([ADR 0027](../adr/0027-blinde-annotation.md)).

## Notes, skips, checks

- **`notes`:** reason for an H1 section; anything unusual a later reader should know. Otherwise empty.
- **Skip a section** only with a fixed reason (`config.CATALOGUE_SKIP_REASONS`): `code-or-links`, `too-short`
  (under 50 tokens), `duplicate-topic` (same topic as an earlier slot), `no-answerable-content`, `content-elsewhere` (every statement
  a question could use is also stated in another section, so the class rule cannot hold; the sections are named in the
  review log, or for a slot without a question in the block's prep sheet,
  [ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md#nachtrag-11112026-sprunggrund-content-elsewhere)). "Hard to write" is
  not a reason.
- **AI review** after each block: Claude adds suggestions (missing section, wording, fact, class) in the Review tab;
  you accept or reject with a reason, and change the text yourself in Write ([ADR 0031](../adr/0031-stichprobenplan-und-ki-durchsicht.md)).
- **Closed-book check** after each block (`catalogue.py screen`): the model answers without context. Judge *hit* only
  if it gets the core point fully; a hit may stay in the catalogue, but at least 32 of 48 must be *miss*.

## Checklist before Save

- [ ] One question, one ask, in English, understandable on its own.
- [ ] Type matches what the question asks (not just the suggested keyword).
- [ ] Class rule holds: `single`/`detail`/`paraphrase` have exactly one section; `multi-section` sections each add a part.
- [ ] `detail`: the fact stands only in this section; answer ≤ 30 words.
- [ ] `paraphrase`: no highlighted heading word left in the question.
- [ ] Reference answer: first sentence is the direct answer; ≤ 4 sentences; nothing beyond the sections and the question.
- [ ] Every section with a needed part is listed; nothing nested; H1 only with a reason in `notes`.
- [ ] Spelling checked.
