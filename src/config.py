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
CHROMA_DIR = ROOT / "chroma_db"
DOCS_DIR = ROOT / "docs"

DOCUMENTS_FILE = DATA_PROCESSED / "documents.jsonl"
CHUNKS_C1_FILE = DATA_PROCESSED / "chunks_c1.jsonl"
CHUNKS_C2_FILE = DATA_PROCESSED / "chunks_c2.jsonl"
CHUNKS_C3_FILE = DATA_PROCESSED / "chunks_c3.jsonl"

QUESTIONS_FILE = DATA_EVAL / "questions.csv"
GROUND_TRUTH_FILE = DATA_EVAL / "ground_truth.csv"
RETRIEVED_RESULTS_FILE = DATA_EVAL / "retrieved_results.csv"
GENERATED_ANSWERS_FILE = DATA_EVAL / "generated_answers.csv"
SCORES_FILE = DATA_EVAL / "scores.csv"

# ---------------------------------------------------------------------------
# Chunking parameters (D5, D6)
# ---------------------------------------------------------------------------

# C1: fixed-size, no overlap
C1_CHUNK_SIZE = 500       # tokens
C1_OVERLAP = 0

# C2: fixed-size, with overlap  — strong baseline (Qu et al. 2025)
C2_CHUNK_SIZE = 500       # tokens
C2_OVERLAP = 100          # tokens

# C3: structure-based (Markdown H2/H3 boundaries)
C3_MAX_TOKENS = 800       # hard cap per chunk; oversized sections split by paragraph

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

CHROMA_COLLECTIONS = {
    "C1": "rag_c1",
    "C2": "rag_c2",
    "C3": "rag_c3",
}

# ---------------------------------------------------------------------------
# Retrieval parameters (D14)
# ---------------------------------------------------------------------------
TOP_K = 5   # constant — do NOT vary; would introduce a second independent variable

# ---------------------------------------------------------------------------
# LLM / Embedding (D15, D16)
# ---------------------------------------------------------------------------
# Pin exact versions at implementation time and document date of first use.
# Use neutral placeholders until then; replace before running experiments.
EMBEDDING_MODEL = "text-embedding-3-large"   # or text-embedding-3-small for cost focus
LLM_MODEL = "gpt-4o"                        # PLACEHOLDER — pin exact snapshot at impl time

LLM_TEMPERATURE = 0.0   # constant for reproducibility (D14)
LLM_MAX_TOKENS = 1024

# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
RUBRIC_CRITERIA = ["correctness", "completeness", "groundedness", "no_hallucination", "clarity"]
RUBRIC_MAX_SCORE = 2
