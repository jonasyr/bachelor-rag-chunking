"""Central configuration — all parameters live here.

Never hardcode paths, model names, or numeric constants outside this file.
Pin exact model/SDK versions at implementation time and document them here.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent

DATA_RAW = ROOT / "data" / "raw" / "vue_docs_snapshot"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_EVAL = ROOT / "data" / "evaluation"
PILOT_DIR = ROOT / "data" / "pilot"  # pilot probes, not the catalogue (scripts/difficulty_probe.py)
PILOT_RUNS_FILE_NAME = "runs.jsonl"  # run log inside each pilot set; other pilot files reuse the
# names of the evaluation artefacts below (QUESTIONS_FILE.name, GROUND_TRUTH_FILE.name, ...)
CHROMA_DIR = ROOT / "chroma_db"
DOCS_DIR = ROOT / "docs"

DOCUMENTS_FILE = DATA_PROCESSED / "documents.jsonl"
SNAPSHOT_INFO_FILE = DOCS_DIR / "corpus_snapshot.txt"  # versioned: commit, dates, SHA-256 per file
SECTIONS_FILE = DATA_PROCESSED / "sections.jsonl"
CORPUS_MANIFEST_FILE = DOCS_DIR / "corpus_manifest.csv"
CHUNKS_C1_FILE = DATA_PROCESSED / "chunks_c1.jsonl"
CHUNKS_C2_FILE = DATA_PROCESSED / "chunks_c2.jsonl"
CHUNKS_C3_FILE = DATA_PROCESSED / "chunks_c3.jsonl"

QUESTIONS_FILE = DATA_EVAL / "questions.csv"
GROUND_TRUTH_FILE = DATA_EVAL / "ground_truth.csv"
RETRIEVED_RESULTS_FILE = DATA_EVAL / "retrieved_results.csv"
CONTROL_RETRIEVED_FILE = DATA_EVAL / "retrieved_results_control.csv"  # control K1 (D26)
GENERATED_ANSWERS_FILE = DATA_EVAL / "generated_answers.csv"
SCORES_FILE = DATA_EVAL / "scores.csv"

# ---------------------------------------------------------------------------
# Corpus (D19, D25)
# ---------------------------------------------------------------------------
VUE_DOCS_REPO_URL = "https://github.com/vuejs/docs.git"
VUE_DOCS_COMMIT = "40aa88af0094f7bab4aaf786e55c748a6a251d88"  # 15.09.2026 (D25)
VUE_DOCS_ROOT = "src"  # documentation root in the repository
# Areas below VUE_DOCS_ROOT; the snapshot mirrors them below DATA_RAW (D25).
VUE_DOCS_AREAS = ("api", "guide", "style-guide")
# Paths below VUE_DOCS_ROOT left out of the corpus (D25): Options-API-only reference pages and the
# generated API index. Each must exist at the commit, so the list cannot rot silently.
VUE_DOCS_EXCLUDED = (
    "api/component-instance.md",
    "api/index.md",
    "api/options-composition.md",
    "api/options-lifecycle.md",
    "api/options-misc.md",
    "api/options-rendering.md",
    "api/options-state.md",
)
TOKEN_ENCODING = "cl100k_base"  # tiktoken 0.13.0, pinned in pyproject.toml
SECTION_MAX_LEVEL = 3  # H1-H3 headings become sections (sections.jsonl, C3 boundaries; D19, D21)

# ---------------------------------------------------------------------------
# Chunking parameters (D5, D6)
# ---------------------------------------------------------------------------

# C1: fixed-size, no overlap
C1_CHUNK_SIZE = 500  # tokens
C1_OVERLAP = 0

# C2: fixed-size, with overlap  — strong baseline (Qu et al. 2025)
C2_CHUNK_SIZE = 500  # tokens
C2_OVERLAP = 100  # tokens

# C3: structure-based (H2/H3 boundaries; every document starts with its H1; D21)
C3_MAX_TOKENS = 800  # hard cap per chunk; oversized sections split by paragraph
C3_MIN_TOKENS = 50  # floor: shorter segments merge into a neighbour first (D21)

# Size-matched control (D26): fixed windows of the rounded mean C3 chunk length, no overlap;
# retrieval only. Not in STRATEGY_IDS: the experiment compares C1-C3 (D5). chunking.py aborts if
# this value no longer equals the rule (round half up of the mean C3 chunk length).
K1_CHUNK_SIZE = 231  # tokens; rounded mean of the C3 chunks at 40aa88a, measured 14.10.2026
K1_OVERLAP = 0
CONTROL_STRATEGIES = {"K1": f"fixed_{K1_CHUNK_SIZE}_no_overlap"}

STRATEGY_IDS = {
    "C1": "fixed_500_no_overlap",
    "C2": "fixed_500_overlap_100",
    "C3": "structure_h2h3",
}

CHUNK_FILES = {
    "C1": CHUNKS_C1_FILE,
    "C2": CHUNKS_C2_FILE,
    "C3": CHUNKS_C3_FILE,
}

EMBEDDING_FILES = {
    "C1": DATA_PROCESSED / "embeddings_c1.npz",
    "C2": DATA_PROCESSED / "embeddings_c2.npz",
    "C3": DATA_PROCESSED / "embeddings_c3.npz",
}
QUERY_EMBEDDINGS_FILE = DATA_EVAL / "query_embeddings.npz"
EMBEDDING_RUNS_FILE = DATA_PROCESSED / "embedding_runs.jsonl"

CHROMA_COLLECTIONS = {
    "C1": "rag_c1",
    "C2": "rag_c2",
    "C3": "rag_c3",
}

# Files and index of the control K1 (D26), kept apart from the experiment mappings above.
CONTROL_CHUNK_FILES = {"K1": DATA_PROCESSED / "chunks_k1.jsonl"}
CONTROL_EMBEDDING_FILES = {"K1": DATA_PROCESSED / "embeddings_k1.npz"}
CONTROL_COLLECTIONS = {"K1": "rag_k1"}

# ---------------------------------------------------------------------------
# Retrieval parameters (D14)
# ---------------------------------------------------------------------------
TOP_K = 5  # constant — do NOT vary; would introduce a second independent variable
SCORE_TOLERANCE = 1e-5  # Chroma vs exact NumPy cosine (float32), D24
# HNSW ef_search and ef_construction = max(collection size, this); >= size: exhaustive search (D24).
HNSW_MIN_BREADTH = 100  # Chroma default for both
# Chroma distance (D24). Results are read as similarity = 1 - distance and checked against exact
# cosine; for unit-length OpenAI vectors that holds for "cosine" (and "ip"), not for "l2".
CHROMA_SPACE = "cosine"
# Model-vintage check (D24): measured 13.10.2026, same model >= 0.99996, different chunks <= 0.84.
CANARY_MIN_COSINE = 0.999
CANARY_PROBE_POSITIONS = (
    0.0,
    0.5,
    1.0,
)  # relative positions of re-embedded texts: first, middle, last
ID_SEPARATOR = ";"  # several IDs in one ground_truth.csv field

# A chunk counts as relevant if its token span overlaps a relevant section by at least
# this many tokens (D19).
RELEVANCE_MIN_OVERLAP = 1
SENSITIVITY_MIN_OVERLAP = 100  # sensitivity check for the retrieval evaluation

# ---------------------------------------------------------------------------
# LLM / Embedding (D15, D16)
# ---------------------------------------------------------------------------
# Pin exact versions at implementation time and document date of first use.
# Use neutral placeholders until then; replace before running experiments.
# Embedding model (D23): OpenAI offers only the alias as snapshot, so vectors are stored once (D24).
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 3072  # model default
EMBEDDING_BATCH_SIZE = 100  # API: <= 2048 inputs and <= 300,000 tokens per request
EMBEDDING_PRICE_PER_MTOK = 0.13  # USD per 1M input tokens, OpenAI model page, accessed 13.10.2026
LLM_MODEL = "gpt-4o"  # PLACEHOLDER — pin exact snapshot at impl time

LLM_TEMPERATURE = 0.0  # constant for reproducibility (D14)
LLM_MAX_TOKENS = 1024

# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
RUBRIC_CRITERIA = ["correctness", "completeness", "groundedness", "no_hallucination", "clarity"]
RUBRIC_MAX_SCORE = 2
