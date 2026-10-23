"""Analysis of the experiment (ADR 0044): tables, figures and analysis.json for the thesis.

Reads the result files of the latest runs (analysis_data), computes descriptive statistics, the
confirmatory tests and effect sizes (stats), and writes LaTeX tables, PDF figures and
analysis.json. The main catalogue must be frozen; a pilot set (`--set DIR`) writes into
`DIR/output/` and never into the thesis' `output/`.

Usage: uv run python src/analyse.py [--set DIR]
"""

import argparse
import sys
from pathlib import Path

import agreement
import analysis_data
import report_figures
import report_tables
from atomic_csv import write_csv
from config import (
    ANALYSIS_ALPHA,
    ANALYSIS_FILE,
    FIGURES_DIR,
    OUTPUT_DIR,
    SECOND_RATER_DISAGREEMENTS_FILE_NAME,
    TABLES_DIR,
)


def run(data: analysis_data.AnalysisData, out_dir: Path) -> dict:
    """Write tables, figures and analysis.json below `out_dir`; return the results."""
    results = report_tables.build_results(data, ANALYSIS_ALPHA)
    tables = out_dir / TABLES_DIR.relative_to(OUTPUT_DIR)
    figures = out_dir / FIGURES_DIR.relative_to(OUTPUT_DIR)
    report_figures.write_figures(data, results, figures)  # appends skip notes to results
    report_tables.write_tables(results, tables)
    report_tables.write_json(results, out_dir / ANALYSIS_FILE.relative_to(OUTPUT_DIR))
    disagreements = out_dir / SECOND_RATER_DISAGREEMENTS_FILE_NAME
    if data.second_rating is not None:  # for the discussion with R2; no strategy in it
        write_csv(
            disagreements,
            agreement.DISAGREEMENTS_HEADER,
            agreement.disagreements(data.second_rating["paired"]),
        )
    else:
        disagreements.unlink(missing_ok=True)  # no stale list from an earlier run
    return results


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Tables, figures and tests for the thesis (ADR 0044).")
    p.add_argument(
        "--set", type=Path, metavar="DIR", help="a pilot set (e.g. data/pilot/e2e) instead"
    )
    args = p.parse_args(argv)
    if args.set:
        data = analysis_data.load(analysis_data.set_paths(args.set), main=False)
        out_dir = args.set / OUTPUT_DIR.name
    else:
        data = analysis_data.load_main()
        out_dir = OUTPUT_DIR
    results = run(data, out_dir)
    for note in results["notes"]:
        print(f"note: {note}")
    print(f"tables, figures and analysis.json -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
