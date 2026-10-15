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
SECTION_INDEX_FILE = DATA_PROCESSED / "section_index.md"  # lookup list for annotation (D29)
CORPUS_MANIFEST_FILE = DOCS_DIR / "corpus_manifest.csv"
CHUNKS_C1_FILE = DATA_PROCESSED / "chunks_c1.jsonl"
CHUNKS_C2_FILE = DATA_PROCESSED / "chunks_c2.jsonl"
CHUNKS_C3_FILE = DATA_PROCESSED / "chunks_c3.jsonl"

QUESTIONS_FILE = DATA_EVAL / "questions.csv"
GROUND_TRUTH_FILE = DATA_EVAL / "ground_truth.csv"
CATALOGUE_FREEZE_FILE = DATA_EVAL / "catalogue_freeze.json"  # SHA-256 of the frozen catalogue (D30)
CATALOGUE_PLAN_FILE = DATA_EVAL / "catalogue_plan.csv"  # random sampling plan of the slots (D31)
CATALOGUE_REVIEW_FILE = (
    DATA_EVAL / "catalogue_review.csv"
)  # AI review suggestions and decisions (D31)
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
# Chunking parameters (D5, D6, D21, D26)
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
# Question catalogue (D17, D29, D30)
# ---------------------------------------------------------------------------
# Allowed values of questions.csv `type` and `difficulty` with their quotas; both sum to the
# catalogue size (48). `difficulty` holds the construction class (D29).
QUESTION_TYPES = {
    "factual": 12,
    "procedural": 12,
    "conceptual": 12,
    "comparative": 6,
    "limitation": 6,
}
QUESTION_CLASSES = {"single": 12, "multi-section": 12, "detail": 12, "paraphrase": 12}
# Minimum number of questions with a relevant section in an area (keys of VUE_DOCS_AREAS); a
# question counts for every area it touches (D29).
AREA_MIN_QUESTIONS = {"api": 12, "style-guide": 3}
DETAIL_MAX_ANSWER_WORDS = 30  # `detail`: reference answer at most this many words (D29)
# Relevant sections per class (D29): `multi-section` at least this many independent sections
# (a section inside another listed one does not count); single/detail/paraphrase exactly this many.
MULTI_SECTION_MIN_SECTIONS = 2
SINGLE_CLASS_SECTIONS = 1
# `check` report only: count multi-section questions whose sections lie on at least this many pages
CATALOGUE_REPORT_MIN_PAGES = 2
CATALOGUE_EXCERPT_CHARS = 60  # `catalogue.py find`: context characters on each side of a match
CATALOGUE_HEADING_SEPARATOR = " › "  # heading path in section_index.md, find and show
# Editor: site-relative doc links ("/api/...") in the formatted view point to the public docs
VUE_DOCS_SITE_URL = "https://vuejs.org"
# Random sampling plan (D31): one starting section per slot, drawn by text length from the
# innermost H2/H3 sections of an area with SHA-256 of "{seed}:{area}:{k}" (version-independent).
CATALOGUE_SEED = 20261014  # fixed on 14.10.2026, the date of the decision; never tuned
CATALOGUE_AREA_SLOTS = {"api": 12, "style-guide": 3, "guide": 33}  # sums to the catalogue size
CATALOGUE_RESERVE = {"api": 12, "style-guide": 3, "guide": 33}  # replacement sections per area
CATALOGUE_SKIP_REASONS = ("code-or-links", "too-short", "duplicate-topic", "no-answerable-content")
CATALOGUE_SKIP_MIN_TOKENS = 50  # `too-short`: starting section under this many tokens
CATALOGUE_PLAN_STATUSES = ("open", "used", "skipped", "reserve")
CATALOGUE_SLOT_FORMAT = "S{:02d}"  # slot IDs S01 … S48 in the plan
# AI review log (D31): kinds of suggestions and their decisions
CATALOGUE_REVIEW_KINDS = ("missing_section", "wording", "fact", "class")
CATALOGUE_REVIEW_DECISIONS = ("open", "accepted", "rejected")
# Question IDs written by the editor: pattern for existing IDs and format of new ones
QUESTION_ID_PATTERN = r"Q\d+"
QUESTION_ID_FORMAT = "Q{:03d}"
# Word comparison for the paraphrase rule (D29): lowercase words matching the pattern, minus
# stopwords; camelCase identifiers also count by their parts. Words of at least
# CATALOGUE_FOLD_MIN_LENGTH characters also match without a trailing s/es and with ies -> y, and
# two words match if they share a prefix of at least max(CATALOGUE_PREFIX_MIN, length of the
# shorter word - CATALOGUE_PREFIX_SLACK) characters (watch/watchers, mounted/mounting). The rule
# errs towards reporting a shared word.
CATALOGUE_WORD_PATTERN = r"[a-z0-9]+"
CATALOGUE_CAMEL_BOUNDARY = r"(?<=[a-z0-9])(?=[A-Z])"
CATALOGUE_FOLD_MIN_LENGTH = 4
CATALOGUE_PREFIX_MIN = 4
CATALOGUE_PREFIX_SLACK = 3
CATALOGUE_STOPWORDS = (
    "a", "about", "am", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by",
    "can", "could", "did", "do", "does", "done", "for", "from", "had", "has", "have", "he",
    "here", "how", "i", "if", "in", "into", "is", "it", "its", "may", "me", "might", "must",
    "my", "no", "not", "of", "on", "onto", "or", "our", "over", "shall", "she", "should", "so",
    "than", "that", "the", "their", "them", "then", "there", "these", "they", "this", "those",
    "to", "under", "v", "vue", "was", "we", "were", "what", "when", "where", "which", "who", "whom",
    "whose", "why", "will", "with", "without", "would", "you", "your",
)  # fmt: skip

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
