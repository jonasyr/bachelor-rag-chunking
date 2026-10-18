#!/usr/bin/env bash
# Rebuilds and probes one candidate of data/corpus_probe/candidates.csv at its pinned commit
# (ADR 0038): sparse clone of the docs folder, pages and statistics, probes, API run.
# The Vue row reads data/processed/documents.jsonl, so it only works on a checkout whose
# snapshot is still Vue at 40aa88a.
# Usage: scripts/corpus_probe/probe_corpus.sh NAME [--recorded]   (from the repo root; calls the
# OpenAI API). --recorded repeats the recorded probes instead of drawing a new sample.
set -euo pipefail
name=$1
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../.." && pwd)
data=$root/data/corpus_probe
row=$(python3 -c "import csv,sys; r={x['name']: x for x in csv.DictReader(open(sys.argv[1]))}[sys.argv[2]]; print('\t'.join([r['repo'], r['docs_path'], r['commit'], r['product']]))" "$data/candidates.csv" "$name")
IFS=$'\t' read -r repo docs commit product <<< "$row"
cd "$root"
if [ "$repo" = "local" ]; then
  source=$docs
else
  dir=$data/sources/$name
  if [ ! -d "$dir" ]; then
    git clone -q --filter=blob:none --no-checkout --sparse "https://github.com/$repo" "$dir"
  fi
  git -C "$dir" sparse-checkout set "$docs"
  git -C "$dir" checkout -q "$commit"
  source=$dir/$docs
fi
uv run python "$here/to_docs.py" "$name" "$source"
uv run python "$here/build_probes.py" "$name" ${2:-}
uv run python "$here/run_probes.py" "$name" "$product"
