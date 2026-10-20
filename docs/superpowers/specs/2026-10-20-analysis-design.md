# Analysis and reporting for the thesis results: design

Date: 20.10.2026. Status: decisions taken in chat 20.10.2026; for Jonas' review. Context: the catalogue is not written yet; this builds the last
pipeline step now, tested on the e2e pilot (`data/pilot/e2e`), so the results chapter only needs one run after the
freeze. Planned items: [evaluation.md](../../reference/evaluation.md) sections "Statistische Auswertung",
"Visualisierungen (geplant)" and the cost comparison under "Effizienz/Kosten"; delivery:
[deliver-results-to-thesis.md](../../how-to/deliver-results-to-thesis.md).

## Intent

One command turns the frozen experiment's result files into every table and figure the thesis needs (LaTeX tables,
PDF figures), plus the statistical tests that let the thesis say whether C1–C3 differ. It must be deterministic,
reproducible from the committed data, and impossible to run on the main catalogue before the freeze.

## Decisions by Jonas (20.10.2026)

| Question | Decision |
|---|---|
| Statistics | Descriptive as now, plus a test over C1–C3 per metric (paired by question), pairwise Wilcoxon signed-rank with Holm correction, effect sizes (Kendall's W for the omnibus test, r for pairs), Spearman correlation retrieval vs answer score (H2). Reported as exploratory, alpha 0.05. New dependency `scipy`. |
| Format | LaTeX tables with `booktabs` (the IU class loads it), German labels, decimal comma (`0,94`); PDF figures from matplotlib in black and greys. |
| Figures | All eight planned in evaluation.md. |
| Running | One script `src/analyse.py`; `--set DIR` runs it on a pilot set into that set's own output folder. |
| Test family (after the builder check) | Confirmatory: three primary metrics — R@5 and MRR (main relevance rule) and the answer total. Friedman per metric, Holm over the three omnibus p-values; pairwise Wilcoxon only for metrics whose omnibus test is significant (after Holm), Holm over those pairs. Everything else (Hit@5, P@5, single criteria, sensitivity rule, Kontext@5) descriptive with effect sizes, no p-values. |
| Cost view (after the builder check) | Side by side per strategy: mean generation cost and tokens per answer, the one-time embedding/index cost separately, next to answer total and R@5; no combined ratio. K0: generation cost only. |

## Goals

- Tables (`output/tables/*.tex`, each a complete `table` float with caption and label, ready for `\input`):
  1. Retrieval per strategy C1–C3 and K1: Hit@5, MRR, P@5, R@5, Kontext@5 (main relevance rule).
  2. The same for the sensitivity rule (appendix).
  3. Answer quality per strategy: five criteria and total for C1–C3; K0 on the four shared criteria
     (`config.CONTROL_CRITERIA`) next to C1–C3 on the same four.
  4. Tests for the three primary metrics: Friedman statistic, p, Holm-adjusted p, Kendall's W; for metrics with a
     significant omnibus test the pairs C1–C2, C1–C3, C2–C3 with Wilcoxon statistic, Holm-adjusted p and r. Other
     metrics: effect sizes only (W, pairwise r), no p-values.
  5. K0 versus each of C1–C3 (four-criteria total): mean differences and r, no p-values. *(Claude's call: K0 is a
     control outside the confirmatory family.)*
  6. Correlation (Spearman ρ, p) between per-question retrieval (R@5 and reciprocal rank, main rule) and answer total,
     per strategy and pooled.
  7. Efficiency: chunks, chunk length (median, mean), Kontext@5, index size, embedding tokens and cost, generation
     tokens and mean cost per answer (C1–C3, K0), per strategy; answer total and R@5 in the same table; no combined
     ratio (ADR 0008).
  8. Breakdown of answer total and R@5 per question type, construction class and closed-book verdict
     (`miss`/`hit`, main catalogue only): descriptive only.
- Figures (`output/figures/*.pdf`): the eight of evaluation.md — Recall@k bars and MRR bars (C1–C3, K1), answer-score
  boxplot (C1–C3, K0), heatmap question × strategy (answer total), scatter per-question R@5 vs answer total (H2),
  catalogue composition (types × classes), chunk-length histogram (C1–C3, K1), cost/token comparison.
- A short machine-readable summary `output/analysis.json` (all numbers the tables show) so the thesis text and tests can
  check values without parsing LaTeX.
- `--set DIR` for pilot sets: reads the set's files, writes to `DIR/output/` (not `output/`), skips what the set lacks
  (e.g. closed-book verdicts) with a note. *(Claude's call:)* for a set, chunk lengths, index size and embedding cost
  come from the shared `data/processed/` files the set's retrieval used; if they are missing, the efficiency table
  and the histogram are skipped with a note.

## Non-goals

- No interpretation text for the thesis; no RAGAS; no dashboard; no change to how scores or retrieval metrics are
  computed or stored (the analysis only reads `retrieval_scores*.csv`, `scores*.csv` and the logs).
- No tests per subgroup (type, class, verdict): too few questions per cell; those breakdowns are descriptive.

## Anti-goals

- Any result from the main catalogue before the freeze (the script refuses an unfrozen main catalogue, like
  `retrieve.py`).
- Choosing tests after seeing results: the test plan is fixed in ADR 0044 before the main run.
- Non-reproducible output: same inputs must give byte-identical `.tex`, `analysis.json` and PDFs.

## Constraints

- All parameters in `src/config.py` (output paths, alpha, figure size and font size, metric lists, rule for the
  correlation) — AGENTS.md.
- Tests never call an API; they run on synthetic data in `tmp_path`.
- Inputs must be the files of the latest runs, so the analysis cannot read stale results. *(Claude's call after the
  builder check:)* `evaluate_retrieval.py` and `evaluate_answers.py --mode summarise` (also `--control`) append a run
  record with input and output SHA-256 (steps `evaluate_retrieval`, `summarise`, `summarise_control`), and
  `analyse.py` checks them with `run_log.require_run`. How the scores are computed and stored stays unchanged.
  Regenerating the git-ignored inputs is a documented command chain (how-to); `analyse.py` does not run earlier steps.
- `retrieval_scores.csv` exists for the main experiment only: `evaluate_retrieval.py` gets a `--set DIR` option
  (same as the other steps) so pilot sets have it too.
- Thesis is German; numbers with decimal comma; tables with `booktabs` rules only; no colour.

## Left to the builder

- Module split (e.g. `src/analyse.py` CLI with `src/stats.py` and `src/report_tables.py`/`report_figures.py`), file
  names of the tables and figures (stable, documented in data-formats.md).
- Effect size for the binary Hit@5 (descriptive only now): e.g. Cochran's Q-based or difference in proportions;
  state it in ADR 0044.
- Handling of ties and zero differences in Wilcoxon (`zero_method`, exact vs. normal approximation) and how r is
  computed; must be deterministic and documented.
- Making matplotlib PDFs byte-reproducible (fixed `metadata`, no timestamps, fixed font).
- Caption and label wording (German), number of decimals per column (sensible, consistent).

## Units

| Unit | Change |
|---|---|
| `pyproject.toml`, `uv.lock` | `scipy` pinned |
| `src/config.py` | `OUTPUT_DIR`, `TABLES_DIR`, `FIGURES_DIR`, `ANALYSIS_FILE`, `ANALYSIS_ALPHA = 0.05`, figure settings, correlation rule |
| `src/evaluate_retrieval.py` | `--set DIR`; run record `evaluate_retrieval` |
| `src/evaluate_answers.py`, `src/control_k0.py` | run records `summarise`, `summarise_control` (no change to scores) |
| `src/analyse.py` (+ helpers) | the analysis; CLI `--set DIR` |
| `docs/adr/0044-…` | statistical analysis plan: the three primary metrics, Friedman + Holm, gated pairwise Wilcoxon + Holm, effect sizes, the Hit@5 choice if used descriptively, no subgroup tests, K0 descriptive |
| docs | evaluation.md (statistics and figures now implemented, link ADR 0044), how-to deliver (command), tooling, configuration, data-formats (`output/` files, `analysis.json`), plan.md, `.serena/memories` |

## Testing

- Statistics against hand-computed values on small synthetic inputs (Friedman/Cochran, Wilcoxon + Holm, W, r,
  Spearman).
- Formatting: decimal comma, booktabs, German labels; LaTeX escapes.
- Determinism: two runs give identical bytes for every output file.
- Refusals: unfrozen main catalogue; inputs not from the latest run (missing or mismatching `evaluate_retrieval` /
  `summarise` records).
- Gating: a non-significant omnibus test produces no pairwise p-values.
- `--set` on a synthetic pilot folder writes into the set's `output/`.
- A run on `data/pilot/e2e` (real, small) as the acceptance check; its output is not versioned.
