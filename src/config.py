"""Central configuration — all parameters live here.

Never hardcode paths, model names, or numeric constants outside this file.
Pin exact model/SDK versions at implementation time and document them here.
"""

from fractions import Fraction
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent

DATA_RAW = ROOT / "data" / "raw" / "e2e_docs_snapshot"
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
CLOSED_BOOK_FILE = (
    DATA_EVAL / "closed_book_screen.csv"
)  # answers without context and Jonas' verdicts (D38, D40)
RETRIEVED_RESULTS_FILE = DATA_EVAL / "retrieved_results.csv"
CONTROL_RETRIEVED_FILE = DATA_EVAL / "retrieved_results_control.csv"  # control K1 (D26)
GENERATED_ANSWERS_FILE = DATA_EVAL / "generated_answers.csv"
GENERATION_RUNS_FILE = DATA_EVAL / "generation_runs.jsonl"  # one line per run of generate.py (D33)
SCORES_FILE = DATA_EVAL / "scores.csv"
# Blind rubric scoring (D32): the rater fills the sheet while reading the packet; the key that maps
# each code to its strategy is opened only by `evaluate_answers.py --mode summarise`.
SCORING_SHEET_FILE = DATA_EVAL / "scoring_sheet.csv"
SCORING_PACKET_FILE = DATA_EVAL / "scoring_packet.md"
SCORING_KEY_FILE = DATA_EVAL / "scoring_key.csv"
SCORING_ITEMS_FILE = DATA_EVAL / "scoring_items.jsonl"  # blind items for the scoring page (D34)
KEY_POINTS_FILE = (
    DATA_EVAL / "key_points.csv"
)  # key points per question, frozen before scoring (D35)
SCORING_CHECKS_FILE = DATA_EVAL / "scoring_checks.csv"  # checks behind every derived score (D35)
# Retrieval metrics per question, strategy and relevance rule (src/evaluate_retrieval.py, D12)
RETRIEVAL_SCORES_FILE = DATA_EVAL / "retrieval_scores.csv"
CONTROL_RETRIEVAL_SCORES_FILE = DATA_EVAL / "retrieval_scores_control.csv"  # control K1 (D26)

# ---------------------------------------------------------------------------
# Corpus (D19, D38)
# ---------------------------------------------------------------------------
CORPUS_REPO_URL = "https://github.com/tester-army/e2e.git"
CORPUS_COMMIT = "ef977f4856da009cac26d78d2e9bb14e5991ee41"  # 17.10.2026 (D38)
CORPUS_ROOT = "docs"  # documentation root in the repository; the snapshot mirrors it in DATA_RAW
CORPUS_PAGE_SUFFIX = ".mdx"  # page files below CORPUS_ROOT; they must equal the navigation's pages
CORPUS_NAV_FILE = "docs.json"  # Mintlify navigation: tabs, groups, pages
CORPUS_PROVIDER_SNIPPET = "snippets/model-provider.jsx"  # data of the <ModelProvider> component
CORPUS_SUPPORT_FILES = (CORPUS_NAV_FILE, CORPUS_PROVIDER_SNIPPET)  # copied with the pages
# Areas: the navigation groups in order; pages listed directly under a tab (Examples) form one area
# named after the tab (D38). ingest.py stops if the navigation differs.
CORPUS_AREAS = (
    "Get started",
    "Platforms",
    "Features",
    "Models and agents",
    "Run in CI",
    "Hosted browsers and devices",
    "Extend",
    "Deep dive",
    "Migrate",
    "Test API",
    "Project",
    "Web",
    "Mobile",
    "Engine contract",
    "Examples",
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
K1_CHUNK_SIZE = 375  # tokens; rounded mean of the C3 chunks at ef977f4, measured 18.10.2026
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
# Minimum number of questions with a relevant section in an area; a question counts for every area
# it touches (D29). Equal to the area's slots (ADR 0039).
AREA_MIN_QUESTIONS = {
    "Get started": 2, "Platforms": 2, "Features": 2, "Models and agents": 2, "Run in CI": 2,
    "Hosted browsers and devices": 2, "Extend": 1, "Deep dive": 3, "Migrate": 4, "Test API": 7,
    "Project": 12, "Web": 2, "Mobile": 2, "Engine contract": 4, "Examples": 1,
}  # fmt: skip
DETAIL_MAX_ANSWER_WORDS = 30  # `detail`: reference answer at most this many words (D29)
# Relevant sections per class (D29): `multi-section` at least this many independent sections
# (a section inside another listed one does not count); single/detail/paraphrase exactly this many.
MULTI_SECTION_MIN_SECTIONS = 2
SINGLE_CLASS_SECTIONS = 1
# `check` report only: count multi-section questions whose sections lie on at least this many pages
CATALOGUE_REPORT_MIN_PAGES = 2
CATALOGUE_EXCERPT_CHARS = 60  # `catalogue.py find`: context characters on each side of a match
CATALOGUE_HEADING_SEPARATOR = " › "  # heading path in section_index.md, find and show
# Editor: site-relative doc links ("/ci#mobile-jobs") in the formatted view point to the public docs
CORPUS_SITE_URL = "https://e2e.tester.army/docs"
# Random sampling plan (D31): one starting section per slot, drawn by text length from the
# innermost H2/H3 sections of an area with SHA-256 of "{seed}:{area}:{k}" (version-independent).
CATALOGUE_SEED = 20261014  # fixed on 14.10.2026, the date of the decision; never tuned
# Slots per area (ADR 0039): share of the corpus tokens, every area at least 1, the rest by largest
# remainder; written as literals so a corpus change cannot shift them. Sums to the catalogue size.
CATALOGUE_AREA_SLOTS = {
    "Get started": 2, "Platforms": 2, "Features": 2, "Models and agents": 2, "Run in CI": 2,
    "Hosted browsers and devices": 2, "Extend": 1, "Deep dive": 3, "Migrate": 4, "Test API": 7,
    "Project": 12, "Web": 2, "Mobile": 2, "Engine contract": 4, "Examples": 1,
}  # fmt: skip
CATALOGUE_RESERVE = dict(CATALOGUE_AREA_SLOTS)  # replacement sections per area (ADR 0039)
CATALOGUE_SKIP_REASONS = ("code-or-links", "too-short", "duplicate-topic", "no-answerable-content")
CATALOGUE_SKIP_MIN_TOKENS = 50  # `too-short`: starting section under this many tokens
CATALOGUE_PLAN_STATUSES = ("open", "used", "skipped", "reserve")
CATALOGUE_SLOT_FORMAT = "S{:02d}"  # slot IDs S01 … S48 in the plan
# AI review log (D31): kinds of suggestions and their decisions
CATALOGUE_REVIEW_KINDS = ("missing_section", "wording", "fact", "class")
CATALOGUE_REVIEW_DECISIONS = ("open", "accepted", "rejected")
# Closed-book screen (D38, D40): "" = not judged, "hit" = the answer without context hits the core
# point of the reference answer (retrieval-independent), "miss" = it does not or only partly.
CLOSED_BOOK_VERDICTS = ("", "hit", "miss")
CLOSED_BOOK_MIN_DEPENDENT_SHARE = Fraction(2, 3)  # at least this share retrieval-dependent (D38)
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
    "can", "could", "did", "do", "does", "done", "e2e", "for", "from", "had", "has", "have", "he",
    "here", "how", "i", "if", "in", "into", "is", "it", "its", "may", "me", "might", "must",
    "my", "no", "not", "of", "on", "onto", "or", "our", "over", "shall", "she", "should", "so",
    "than", "that", "the", "their", "them", "then", "there", "these", "they", "this", "those",
    "to", "under", "was", "we", "were", "what", "when", "where", "which", "who", "whom",
    "whose", "why", "will", "with", "without", "would", "you", "your",
)  # fmt: skip

# ---------------------------------------------------------------------------
# LLM / Embedding (D15, D16)
# ---------------------------------------------------------------------------
# Embedding model (D23): OpenAI offers only the alias as snapshot, so vectors are stored once (D24).
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 3072  # model default
EMBEDDING_BATCH_SIZE = 100  # API: <= 2048 inputs and <= 300,000 tokens per request
EMBEDDING_PRICE_PER_MTOK = 0.13  # USD per 1M input tokens, OpenAI model page, accessed 13.10.2026
# Answer model (D33): pinned 17.10.2026; OpenAI offers only the alias, so answers are generated
# once and the model the API reports is logged per run.
LLM_MODEL = "gpt-6-luna"
LLM_REASONING_EFFORT = "none"  # the only effort at which the API accepts a temperature (D33)
LLM_TEMPERATURE = 0.0  # constant for reproducibility (D14)
LLM_SEED = 20261017  # best-effort deterministic sampling on every request (D33); fixed, never tuned
LLM_MAX_TOKENS = 1024  # an answer cut off at this limit stops the run (D33)
LLM_PRICE_INPUT_PER_MTOK = 0.10  # USD per 1M input tokens, OpenAI model page, accessed 17.10.2026
LLM_PRICE_OUTPUT_PER_MTOK = 0.50  # USD per 1M output tokens, same page and date

# Prompt (docs/reference/prompts.md): identical for every strategy (D6); tests compare it with
# the documented text.
SYSTEM_PROMPT = """You are a helpful assistant that answers questions about the e2e testing framework
based solely on the provided documentation excerpts.
Do not use any knowledge outside the provided context.
If the context does not contain sufficient information to answer the question,
state that explicitly."""  # noqa: E501 (verbatim prompt text)
USER_PROMPT_TEMPLATE = """Answer the following question based exclusively on the documentation excerpts below.

Question: {question}

Documentation excerpts:
{context}

Answer:"""  # noqa: E501 (verbatim prompt text)
CONTEXT_SEPARATOR = "\n---\n"  # between the excerpts; each starts with "[Excerpt N]"
# Closed-book prompt (docs/reference/prompts.md): the screen of the catalogue and the control K0
# (D38, D40); the RAG prompt without excerpts, so the model may answer from its own knowledge.
CLOSED_BOOK_SYSTEM_PROMPT = """You are a helpful assistant that answers questions about the e2e testing framework.
If you do not know the answer, state that explicitly."""  # noqa: E501 (verbatim prompt text)
CLOSED_BOOK_USER_TEMPLATE = """Answer the following question.

Question: {question}

Answer:"""

# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
RUBRIC_CRITERIA = ["correctness", "completeness", "groundedness", "no_hallucination", "clarity"]
RUBRIC_MAX_SCORE = 2
KEY_POINTS_MAX = 4  # key points per question; point 1 is the core point (D35)
RUBRIC_COMPLETENESS_PARTIAL = 0.5  # share of covered key points for completeness 1 (D35)
RUBRIC_RULES_VERSION = "2026-10-18"  # version of the rules in src/scoring_rules.py (D35, D37)
SCORING_METHOD = "rules"  # mark of a scaffold that must be scored by the rules (D36)
SCORING_SEED = 20261016  # order of the blinded answers per question (D32); fixed, never tuned

# ---------------------------------------------------------------------------
# Corpus selection probe (D38): a diagnostic run once to choose the corpus, not part of the
# experiment; scripts/corpus_probe/, method in docs/reference/corpus-selection.md
# ---------------------------------------------------------------------------
CORPUS_PROBE_DIR = ROOT / "data" / "corpus_probe"
CORPUS_PROBE_SEED = 20261018  # order of the candidate sentences per page; fixed, never tuned
CORPUS_PROBE_PER_PAGE = 12  # probes per page at most, so long pages do not dominate
CORPUS_PROBE_SPAN_CHARS = (2, 40)  # length of a maskable inline code span
CORPUS_PROBE_SENTENCE_CHARS = (40, 400)  # length of a usable prose sentence
CORPUS_PROBE_CONTEXT_CHARS = 6000  # section text shown in the open-book run
CORPUS_PROBE_WORKERS = 8  # parallel API requests
CORPUS_PROBE_GUESS_CHARS = 120  # closed-book reply kept in misses/<name>.json
# Preregistered score (data/corpus_probe/preregistration.md): weights sum to 100, each criterion
# rated 0-4; the rating bands are in scripts/corpus_probe/summarise.py.
CORPUS_PROBE_WEIGHTS = {
    "unknown": 35,
    "clean": 15,
    "struct": 15,
    "quality": 15,
    "stable": 10,
    "fit": 10,
}
CORPUS_PROBE_SENSITIVITY = {  # alternative weightings; the ranking is reported for each
    "preregistered": CORPUS_PROBE_WEIGHTS,
    "equal": dict.fromkeys(CORPUS_PROBE_WEIGHTS, 1),
    "unknown50": {"unknown": 50, "clean": 10, "struct": 10, "quality": 10, "stable": 10, "fit": 10},
    "no_stability_fit": {
        "unknown": 35,
        "clean": 20,
        "struct": 20,
        "quality": 25,
        "stable": 0,
        "fit": 0,
    },
    "quality_heavy": {
        "unknown": 25,
        "clean": 15,
        "struct": 20,
        "quality": 25,
        "stable": 5,
        "fit": 10,
    },
}
CORPUS_PROBE_MIN_TOKENS = 80_000  # exclusion criterion 5, lower bound (sensitivity pool)
CORPUS_PROBE_TOP = 5  # candidates listed per weighting
CORPUS_PROBE_AI_RATING = {
    "low": 4,
    "medium": 3,
    "medium-high": 2,
    "high": 1,
}  # fit by AI-text share
CORPUS_PROBE_FEW_STARS = 100  # fewer GitHub stars lower the fit rating by one
# Question-level closed-book check of the candidates (D38): sections drawn with CORPUS_PROBE_SEED
CORPUS_QUESTIONS_PER_CORPUS = 20  # diagnostic questions per corpus, one per drawn section
CORPUS_QUESTIONS_MIN_WORDS = 60  # prose words (3+ letters, outside code) a drawn section needs
CORPUS_QUESTIONS_PER_PAGE = 2  # drawn sections per page at most
CORPUS_QUESTIONS_SECTION_CHARS = 5000  # section text shown to the question writer and open-book run
CORPUS_QUESTIONS_JUDGE_SEEDS = {1: 7, 2: 8}  # order of the blinded answers per judge batch
