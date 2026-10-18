# Corpus selection: pre-registered criteria (fixed 18.10.2026, before probing new candidates)

Answer model: gpt-6-luna (knowledge cutoff 18.05.2026). Vue (current corpus), Blume and e2e were probed before
these criteria were written; they are scored with the same rules.

## Exclusion (all must hold)
1. First public release of project and docs after 31.05.2026, verified from primary sources (repo creation, first
   commit, first release tag); no evidence of a well-known predecessor whose docs it copies.
2. Docs as Markdown/MDX in a public git repository (pinnable commit).
3. Licence allows research use and quoting (MIT, Apache-2.0, BSD, CC-BY or similar).
4. English.
5. 80k–300k tokens after dropping translations (a coherent subset of whole areas is allowed).
6. Both conceptual/guide pages and reference pages (API, configuration or CLI).

## Measurement (identical for every corpus)
Cloze probe: per page at most 12 prose sentences with one inline code span masked (seed 20261018; spans in the
section or page title dropped); the model restores it closed-book and open-book (section text, masked); exact match
after normalisation. Misses with open-book success are classified by an independent agent into fact / example_name /
equivalent / ambiguous (same prompt for all corpora). Gap rate = fact misses / well-posed probes, with 95% CI.

## Score (weights sum to 100)
- 35 Parametric unknownness: gap rate (higher is better).
- 15 Markdown cleanliness: share of well-posed probes and JSX component lines per 10k tokens.
- 15 Structure for chunking: headings per page and page-length spread close to the current pipeline's assumptions
  (median h2–h4 per page >= 5).
- 15 Documentation quality: separated guide vs reference (Diátaxis-like), consistent heading hierarchy, titles in
  frontmatter, code examples, little generated or boilerplate text.
- 10 Stability: docs commits in the last 30 days (fewer is better), tagged releases to pin.
- 10 Fit to the research question: documentation of a real, used software project (library, framework, CLI,
  protocol); not marketing; not predominantly AI-written.

Each criterion is rated 0–4 from the measured values; total = sum(weight × rating / 4). Ties: higher gap rate wins.
The decision also needs a question-level confirmation in Jonas's first catalogue block (closed-book screen).
