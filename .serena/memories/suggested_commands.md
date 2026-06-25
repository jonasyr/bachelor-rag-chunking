# Suggested Commands

## Environment setup
```bash
uv sync                   # install all deps + dev group into .venv (reads uv.lock)
cp .env.example .env      # then fill in OPENAI_API_KEY
source .venv/bin/activate
```

Adding a new dependency:
```bash
uv add <package>          # updates pyproject.toml + uv.lock
uv add --group dev <pkg>  # dev-only dependency
```

## Pipeline entry points (under `src/` — all currently stubs)
```bash
python src/ingest.py
python src/preprocess.py
python src/chunking.py [--strategy C1|C2|C3|all]
python src/embed.py    [--strategy C1|C2|C3|all]
python src/retrieve.py [--strategy C1|C2|C3|all]
python src/generate.py [--strategy C1|C2|C3|all]
python src/evaluate_retrieval.py [--k 5]
python src/evaluate_answers.py --mode scaffold
python src/evaluate_answers.py --mode summarise
```

## Minimal prototype sequence (do this first)
```bash
python src/ingest.py
python src/preprocess.py
python src/chunking.py
python src/embed.py --strategy C1
python src/retrieve.py --strategy C1
python src/generate.py --strategy C1
```

## Analysis
```bash
jupyter notebook notebooks/analysis.ipynb
```

## Streamlit demo
```bash
streamlit run app/streamlit_app.py
```

## Corpus snapshot (Vue.js)
```bash
git clone https://github.com/vuejs/docs.git /tmp/vuejs-docs
# check out a specific commit, document the hash
# copy src/guide/essentials/, src/guide/components/,
#      src/guide/reusability/, src/guide/best-practices/
# into data/raw/vue_docs_snapshot/
# fill in docs/corpus_manifest.csv
```

## Git
```bash
rtk git status
rtk git log
rtk git diff
```
