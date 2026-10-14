import pytest
from conftest import PAGES, build_corpus, valid_rows, write_catalogue, write_plan_for

import catalogue
import tokens
from catalogue import (
    check,
    class_findings,
    content_words,
    exit_code,
    find,
    forms,
    load_corpus,
    main,
    section_index,
    shared_words,
    show,
    write_section_index,
)
from config import (
    AREA_MIN_QUESTIONS,
    QUESTION_CLASSES,
    QUESTION_TYPES,
    VUE_DOCS_AREAS,
)


def test_config_quotas_are_consistent():
    assert sum(QUESTION_TYPES.values()) == sum(QUESTION_CLASSES.values()) == 48
    assert set(AREA_MIN_QUESTIONS) <= set(VUE_DOCS_AREAS)


def test_corpus_text_is_the_exact_token_slice(corpus):
    once = corpus.by_id["D002#once"]
    doc = corpus.docs["D002"]
    starts = tokens.token_starts(doc["text"])
    assert corpus.text(once) == doc["text"][starts[once["start_token"]] : starts[once["end_token"]]]
    assert corpus.text(once).startswith("### Once Watchers")


def test_heading_path_area_and_page_title(corpus):
    once = corpus.by_id["D002#once"]
    assert corpus.heading_path(once) == "Watchers › Deep Watchers › Once Watchers"
    assert corpus.heading_path(corpus.by_id["D001#core"]) == "Reactivity API: Core"
    assert corpus.area(once) == "guide"
    assert corpus.area(corpus.by_id["D003#multi-word"]) == "style-guide"
    assert corpus.page_title(once) == "Watchers"


def test_section_index_has_one_row_per_section_in_order(corpus):
    lines = section_index(corpus).splitlines()
    rows = [line for line in lines if line.startswith("| `")]
    assert [row.split("`")[1] for row in rows] == [s["section_id"] for s in corpus.sections]
    once = corpus.by_id["D002#once"]
    tokens_once = once["end_token"] - once["start_token"]
    assert (
        f"| `D002#once` | guide | guide/essentials/watchers.md | "
        f"Watchers › Deep Watchers › Once Watchers | {tokens_once} |"
    ) in rows


def test_section_index_escapes_pipes_in_titles(tmp_path):
    pages = {"guide/a.md": "# A | B {#a}\n\nText.\n"}
    index = section_index(load_corpus(*build_corpus(tmp_path, pages)))
    assert "| A \\| B |" in index


def test_write_section_index_is_deterministic(corpus, tmp_path):
    out = tmp_path / "index.md"
    assert write_section_index(corpus, out) == len(corpus.sections)
    first = out.read_bytes()
    write_section_index(corpus, out)
    assert out.read_bytes() == first


def test_find_reports_only_the_innermost_section(corpus):
    hits = find(corpus, "callback only")
    assert [s["section_id"] for s, _ in hits] == ["D002#once"]
    assert "callback only one time" in hits[0][1]


def test_find_is_case_insensitive_and_reports_each_owning_section(corpus):
    ids = [s["section_id"] for s, _ in find(corpus, "ONCE")]
    assert ids == ["D002#deep", "D002#once"]  # "Use the once option" is in Deep's own text


def test_find_matches_regex_characters_literally(corpus):
    assert [s["section_id"] for s, _ in find(corpus, "ref()")] == ["D001#ref"]
    assert find(corpus, "r.f") == []


def test_find_rejects_an_empty_term(corpus):
    with pytest.raises(ValueError, match="empty search term"):
        find(corpus, "  ")


def test_show_prints_heading_path_tokens_and_exact_text(corpus):
    once = corpus.by_id["D002#once"]
    out = show(corpus, "D002#once")
    assert out.splitlines()[0] == (
        f"D002#once  Watchers › Deep Watchers › Once Watchers  "
        f"({once['end_token'] - once['start_token']} tokens)"
    )
    assert out.endswith(corpus.text(once))


def test_show_rejects_an_unknown_section(corpus):
    with pytest.raises(ValueError, match="unknown section D009#x"):
        show(corpus, "D009#x")


def test_content_words_drop_stopwords_and_punctuation():
    assert content_words("How do I use ref() in Vue?") == {"use", "ref"}


def test_forms_fold_plural_endings_only_for_longer_words():
    assert forms("values") == {"values", "value", "valu"}
    assert forms("watches") == {"watches", "watche", "watch"}
    assert forms("dependencies") >= {"dependency"}
    assert forms("refs") == {"refs", "ref"}
    assert forms("its") == {"its"}  # shorter than CATALOGUE_FOLD_MIN_LENGTH


@pytest.mark.parametrize(
    ("question", "heading", "shared"),
    [
        ("Which values can it hold?", "Value Bindings", ["values"]),
        ("How do props work?", "Prop Validation", ["props"]),
        ("What are refs?", "ref()", ["refs"]),
        ("What does a dependency do?", "Optional Dependencies", ["dependency"]),
        ("How do I skip later renders?", "v-once", []),
        # derivations keep the stem: not a paraphrase (task 3 review)
        ("How do I watch nested objects deeply?", "Deep Watchers", ["deeply", "watch"]),
        ("When is a component mounted?", "Mounting", ["mounted"]),
        ("What does watching do?", "Watchers", ["watching"]),
        ("What is a reactive object?", "Reactivity Fundamentals", ["reactive"]),
        ("What happens on update?", "Updated", ["update"]),
        ("Which emitted events exist?", "Emitting Events", ["emitted", "events"]),
        ("Which props are passed?", "Props Passing", ["passed", "props"]),
        ("How do I bind it?", "Bindings", ["bind"]),
        # code identifiers are also compared by their camelCase parts
        ("How do I define props?", "defineProps()", ["define", "props"]),
        ("What does defineProps return?", "Define Props", ["define", "defineprops", "props"]),
        # unrelated words with a short common start stay apart
        ("Is the compiler involved?", "Computed Properties", []),
        ("Which template is used?", "Temporary State", []),
    ],
)
def test_shared_words(question, heading, shared):
    assert shared_words(question, [heading]) == shared


def question(difficulty, text="Question number one"):
    return {"question_id": "Q001", "question": text, "type": "factual", "difficulty": difficulty}


def truth(answer="Short answer."):
    return {"question_id": "Q001", "expected_answer": answer}


def test_single_needs_exactly_one_section(corpus):
    one, two = [corpus.by_id["D001#ref"]], [corpus.by_id["D001#ref"], corpus.by_id["D002#once"]]
    assert class_findings(corpus, question("single"), truth(), one) == []
    assert class_findings(corpus, question("single"), truth(), two) == [
        "single needs exactly 1 relevant section, has 2"
    ]


def test_multi_section_needs_two_sections(corpus):
    one, two = [corpus.by_id["D001#ref"]], [corpus.by_id["D001#ref"], corpus.by_id["D002#once"]]
    assert class_findings(corpus, question("multi-section"), truth(), two) == []
    assert class_findings(corpus, question("multi-section"), truth(), one) == [
        "multi-section needs at least 2 relevant sections, has 1"
    ]


def test_detail_limits_the_answer_length(corpus):
    one = [corpus.by_id["D002#once"]]
    assert class_findings(corpus, question("detail"), truth("word " * 30), one) == []
    assert class_findings(corpus, question("detail"), truth("word " * 31), one) == [
        "detail answer has 31 words, at most 30"
    ]


def test_paraphrase_must_not_share_section_or_page_heading_words(corpus):
    once = [corpus.by_id["D002#once"]]  # headings "Once Watchers" and page title "Watchers"
    ok = question("paraphrase", "How do I run a callback a single time?")
    assert class_findings(corpus, ok, truth(), once) == []
    section_word = question("paraphrase", "Does it fire only once?")  # "Once" is section-only
    assert class_findings(corpus, section_word, truth(), once) == [
        "paraphrase shares heading words ['once']"
    ]
    page_word = question("paraphrase", "How do watchers fire?")
    assert class_findings(corpus, page_word, truth(), once) == [
        "paraphrase shares heading words ['watchers']"
    ]


def run_check(corpus, tmp_path, rows, pilot_dir):
    questions, truth = write_catalogue(tmp_path, rows)
    plan = write_plan_for(tmp_path, rows)
    review = tmp_path / "catalogue_review.csv"
    return check(corpus, questions, truth, pilot_dir=pilot_dir, plan_file=plan, review_file=review)


def test_valid_catalogue_passes_strictly(corpus, tmp_path, pilot):
    report = run_check(corpus, tmp_path, valid_rows(), pilot)
    assert report.errors == [] and report.findings == []
    assert exit_code(report, draft=False) == 0
    assert report.types == QUESTION_TYPES and report.classes == QUESTION_CLASSES
    text = "\n".join(report.lines)
    assert "| total |" in text and "api 12 (at least 12)" in text


def test_format_errors_fail_even_in_draft(corpus, tmp_path, pilot):
    rows = valid_rows()
    rows[0] = (*rows[0][:5], ["D009#missing"])
    report = run_check(corpus, tmp_path, rows, pilot)
    assert any("unknown section IDs ['D009#missing']" in e for e in report.errors)
    assert exit_code(report, draft=True) == 1


def test_unknown_values_are_errors_by_question(corpus, tmp_path, pilot):
    rows = valid_rows()
    rows[0] = (rows[0][0], rows[0][1], "trivia", "hard", *rows[0][4:])
    report = run_check(corpus, tmp_path, rows, pilot)
    assert "Q001: unknown type 'trivia'" in "\n".join(report.errors)
    assert "Q001: unknown difficulty 'hard'" in "\n".join(report.errors)
    assert exit_code(report, draft=True) == 1


def test_quota_and_floor_findings_are_warnings_in_draft(corpus, tmp_path, pilot):
    report = run_check(corpus, tmp_path, valid_rows()[:20], pilot)
    assert report.errors == []
    joined = "\n".join(report.findings)
    assert "type factual: 12 questions, quota 12" not in joined
    assert "type procedural: 8 questions, quota 12" in joined
    assert "difficulty multi-section: 8 questions, quota 12" in joined
    assert "area style-guide: 3 questions, at least 3" not in joined
    assert exit_code(report, draft=True) == 0
    assert exit_code(report, draft=False) == 1


def test_area_floor_counts_cross_area_questions_for_each_area(corpus, tmp_path, pilot):
    rows = valid_rows()
    rows = [r for r in rows if not r[5][0].startswith("D003")]  # drop the style-guide questions
    report = run_check(corpus, tmp_path, rows, pilot)
    assert "area style-guide: 0 questions, at least 3" in report.findings


def test_class_rule_findings_carry_the_question_id(corpus, tmp_path, pilot):
    rows = valid_rows()
    index = next(i for i, r in enumerate(rows) if r[3] == "paraphrase")
    qid = rows[index][0]
    rows[index] = (qid, "How do watchers fire?", *rows[index][2:])
    report = run_check(corpus, tmp_path, rows, pilot)
    assert f"{qid}: paraphrase shares heading words ['watchers']" in report.findings


def test_duplicates_within_the_catalogue_and_against_pilots(corpus, tmp_path, pilot):
    rows = valid_rows()
    rows[1] = (rows[1][0], "question NUMBER zq0!", *rows[1][2:])
    rows[2] = (rows[2][0], "How do I copy a pilot question", *rows[2][2:])
    report = run_check(corpus, tmp_path, rows, pilot)
    assert "Q002: same question as Q001" in report.findings
    assert "Q003: same question as pilot hard/H01" in report.findings


@pytest.fixture
def cli(corpus_files, tmp_path, monkeypatch, pilot):
    docs_file, sections_file = corpus_files
    monkeypatch.setattr(catalogue, "DOCUMENTS_FILE", docs_file)
    monkeypatch.setattr(catalogue, "SECTIONS_FILE", sections_file)
    monkeypatch.setattr(catalogue, "SECTION_INDEX_FILE", tmp_path / "section_index.md")
    questions, truth = write_catalogue(tmp_path, valid_rows())
    monkeypatch.setattr(catalogue, "QUESTIONS_FILE", questions)
    monkeypatch.setattr(catalogue, "GROUND_TRUTH_FILE", truth)
    monkeypatch.setattr(catalogue, "PILOT_DIR", pilot)
    monkeypatch.setattr(catalogue, "CATALOGUE_FREEZE_FILE", tmp_path / "freeze.json")
    monkeypatch.setattr(catalogue, "CATALOGUE_PLAN_FILE", write_plan_for(tmp_path, valid_rows()))
    monkeypatch.setattr(catalogue, "CATALOGUE_REVIEW_FILE", tmp_path / "catalogue_review.csv")
    return tmp_path


def test_cli_sections_find_show(cli, capsys):
    assert main(["sections"]) == 0
    assert (cli / "section_index.md").exists()
    assert main(["find", "callback only"]) == 0
    assert "D002#once" in capsys.readouterr().out
    assert main(["show", "D009#x"]) == 1
    assert "unknown section D009#x" in capsys.readouterr().err


def test_cli_check_and_freeze(cli, capsys):
    assert main(["check"]) == 0
    assert main(["freeze"]) == 0
    assert (cli / "freeze.json").exists()
    assert main(["freeze"]) == 1
    assert "ADR 0030" in capsys.readouterr().err


def test_find_excerpt_stays_inside_the_section(corpus):
    [(section, excerpt)] = find(corpus, "one time")
    assert section["section_id"] == "D002#once"
    assert "Cleanup" not in excerpt and "Deep" not in excerpt


def test_nested_sections_count_once_for_multi_section(corpus):
    deep, once = corpus.by_id["D002#deep"], corpus.by_id["D002#once"]  # H3 inside its H2
    assert class_findings(corpus, question("multi-section"), truth(), [deep, once]) == [
        "D002#once lies inside D002#deep",
        "multi-section needs at least 2 relevant sections, has 1",
    ]


def test_duplicate_section_ids_are_a_format_error(corpus, tmp_path, pilot):
    rows = valid_rows()
    index = next(i for i, r in enumerate(rows) if r[3] == "multi-section")
    rows[index] = (*rows[index][:5], ["D002#once", "D002#once"])
    report = run_check(corpus, tmp_path, rows, pilot)
    assert any("duplicate section IDs ['D002#once']" in e for e in report.errors)


def test_find_excerpt_width_comes_from_config(corpus, monkeypatch):
    monkeypatch.setattr(catalogue, "CATALOGUE_EXCERPT_CHARS", 4)
    [(_, excerpt)] = find(corpus, "callback")
    assert excerpt == "the callback onl"  # 4 characters on each side


def test_find_keeps_spaces_in_the_term(corpus):
    assert [s["section_id"] for s, _ in find(corpus, " ref")] == ["D001#ref", "D001#computed"]
    assert find(corpus, "ref") != find(corpus, " ref")


def test_single_letter_directive_prefix_is_not_a_shared_word():
    assert shared_words("What does the v-if directive do?", ["v-show"]) == []


def test_empty_catalogue_says_no_questions_yet(corpus, tmp_path, pilot):
    report = run_check(corpus, tmp_path, [], pilot)
    assert report.errors == ["questions.csv has no questions yet"]


def test_malformed_pilot_file_is_an_error_not_a_crash(corpus, tmp_path, pilot):
    (pilot / "broken").mkdir()
    (pilot / "broken" / "questions.csv").write_text("id,text\nX,y\n", encoding="utf-8")
    report = run_check(corpus, tmp_path, valid_rows(), pilot)
    assert any("broken" in e and "columns" in e for e in report.errors)


def test_cli_find_with_an_empty_term_is_a_one_line_error(cli, capsys):
    assert main(["find", "  "]) == 1
    assert capsys.readouterr().err.strip() == "empty search term"


def test_section_counts_of_the_classes_come_from_config(corpus, monkeypatch):
    monkeypatch.setattr(catalogue, "MULTI_SECTION_MIN_SECTIONS", 3)
    monkeypatch.setattr(catalogue, "SINGLE_CLASS_SECTIONS", 2)
    two = [corpus.by_id["D001#ref"], corpus.by_id["D002#once"]]
    assert class_findings(corpus, question("multi-section"), truth(), two) == [
        "multi-section needs at least 3 relevant sections, has 2"
    ]
    assert class_findings(corpus, question("single"), truth(), two) == []


def test_page_spread_report_uses_the_configured_minimum(corpus, tmp_path, pilot, monkeypatch):
    rows = valid_rows()  # 3 multi-section rows pair D003 with D002; 9 stay on D002
    assert (
        "multi-section on at least 2 pages: 3 of 12"
        in run_check(corpus, tmp_path, rows, pilot).lines
    )
    monkeypatch.setattr(catalogue, "CATALOGUE_REPORT_MIN_PAGES", 3)
    assert (
        "multi-section on at least 3 pages: 0 of 12"
        in run_check(corpus, tmp_path, rows, pilot).lines
    )


def test_check_reports_a_missing_plan(corpus, tmp_path, pilot):
    questions, truth = write_catalogue(tmp_path, valid_rows())
    report = check(
        corpus,
        questions,
        truth,
        pilot_dir=pilot,
        plan_file=tmp_path / "none.csv",
        review_file=tmp_path / "r.csv",
    )
    assert any("catalogue.py plan" in e for e in report.errors)


def test_check_applies_the_plan_rules(corpus, tmp_path, pilot):
    rows = valid_rows()
    questions, truth = write_catalogue(tmp_path, rows)
    plan = write_plan_for(tmp_path, rows[1:])  # Q001 has no slot
    report = check(
        corpus, questions, truth, pilot_dir=pilot, plan_file=plan, review_file=tmp_path / "r.csv"
    )
    assert "Q001: belongs to 0 slots, needs exactly 1" in report.findings


def test_open_review_rows_warn_in_draft_and_fail_strictly(corpus, tmp_path, pilot):
    rows = valid_rows()
    questions, truth = write_catalogue(tmp_path, rows)
    review = tmp_path / "catalogue_review.csv"
    review.write_text(
        "round,question_id,kind,suggestion,section_id,decision,reason,date\n"
        "1,Q001,wording,Say which hook.,,open,,\n",
        encoding="utf-8",
    )
    report = check(
        corpus,
        questions,
        truth,
        pilot_dir=pilot,
        plan_file=write_plan_for(tmp_path, rows),
        review_file=review,
    )
    assert report.errors == []
    assert "1 review suggestion(s) still open" in report.findings
    assert exit_code(report, draft=True) == 0 and exit_code(report, draft=False) == 1
    assert any(line.startswith("AI review: 1 suggestions") for line in report.lines)
