import json

import pytest
from conftest import (
    PAGES,
    build_corpus,
    fresh_plan_for,
    valid_rows,
    write_catalogue,
    write_plan_for,
    write_screen_for,
)
from test_closed_book import FakeCompleter

import catalogue
import tokens
from catalogue import (
    check,
    class_findings,
    content_words,
    exit_code,
    find,
    forms,
    h1_findings,
    load_corpus,
    main,
    section_index,
    shared_words,
    show,
    write_section_index,
)
from catalogue_review import ensure_review_file
from config import (
    AREA_MIN_QUESTIONS,
    CATALOGUE_AREA_SLOTS,
    QUESTION_CLASSES,
    QUESTION_TYPES,
)


def test_config_quotas_are_consistent():
    assert sum(QUESTION_TYPES.values()) == sum(QUESTION_CLASSES.values()) == 48
    assert set(AREA_MIN_QUESTIONS) <= set(CATALOGUE_AREA_SLOTS)


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
    assert content_words("How do I use expect() in e2e?") == {"use", "expect"}


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


def test_h1_section_needs_a_reason_in_notes(corpus):
    """ADR 0022: a whole page is relevant only with a reason in `notes`."""
    page = [corpus.by_id["D002#watchers"]]
    assert h1_findings(question("single") | {"notes": ""}, page) == [
        "D002#watchers is a whole page (H1); give the reason in notes (ADR 0022)"
    ]
    assert h1_findings(question("single") | {"notes": "the page is the answer"}, page) == []
    assert h1_findings(question("single") | {"notes": ""}, [corpus.by_id["D002#once"]]) == []


def run_check(corpus, tmp_path, rows, pilot_dir, screen=True):
    questions, truth = write_catalogue(tmp_path, rows)
    plan = write_plan_for(tmp_path, rows)
    review = tmp_path / "catalogue_review.csv"
    ensure_review_file(review)
    if screen:
        write_screen_for(tmp_path / "closed_book_screen.csv", rows)
    return check(
        corpus,
        questions,
        truth,
        pilot_dir=pilot_dir,
        plan_file=plan,
        review_file=review,
        fresh_plan=fresh_plan_for(rows),
    )


def test_check_reports_an_h1_section_without_reason(corpus, tmp_path, pilot):
    rows = valid_rows()
    qid, text, qtype, cls, answer, _ = rows[-1]
    rows[-1] = (qid, text, qtype, cls, answer, ["D002#watchers"])
    report = run_check(corpus, tmp_path, rows, pilot)
    assert f"{qid}: D002#watchers is a whole page (H1); give the reason in notes (ADR 0022)" in (
        report.findings
    )


def test_valid_catalogue_passes_strictly(corpus, tmp_path, pilot):
    report = run_check(corpus, tmp_path, valid_rows(), pilot)
    assert report.errors == [] and report.findings == []
    assert exit_code(report, draft=False) == 0
    assert report.types == QUESTION_TYPES and report.classes == QUESTION_CLASSES
    text = "\n".join(report.lines)
    assert "| total |" in text and "api 12 (at least 12)" in text
    assert (
        "Closed-book: 48 retrieval-dependent (at least 32), 0 known, 0 not screened, 0 not judged"
        in report.lines
    )


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
    ensure_review_file(tmp_path / "catalogue_review.csv")
    monkeypatch.setattr(catalogue, "draw_plan", lambda corpus: fresh_plan_for(valid_rows()))
    return tmp_path


def test_cli_sections_find_show(cli, capsys):
    assert main(["sections"]) == 0
    assert (cli / "section_index.md").exists()
    assert main(["find", "callback only"]) == 0
    assert "D002#once" in capsys.readouterr().out
    assert main(["show", "D009#x"]) == 1
    assert "unknown section D009#x" in capsys.readouterr().err


def test_cli_check_and_freeze(cli, capsys):
    write_screen_for(cli / "closed_book_screen.csv", valid_rows())
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


def test_product_name_is_not_a_shared_word():
    assert shared_words("How does e2e retry a step?", ["e2e test lifecycle"]) == []


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
        corpus,
        questions,
        truth,
        pilot_dir=pilot,
        plan_file=plan,
        review_file=tmp_path / "r.csv",
        fresh_plan=fresh_plan_for(valid_rows()[1:]),
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
        fresh_plan=fresh_plan_for(rows),
        review_file=review,
    )
    assert report.errors == []
    assert "1 review suggestion(s) still open" in report.findings
    assert exit_code(report, draft=True) == 0 and exit_code(report, draft=False) == 1
    assert any(line.startswith("AI review: 1 suggestions") for line in report.lines)


def test_check_rejects_a_hand_edited_plan(corpus, tmp_path, pilot):
    rows = valid_rows()
    questions, truth = write_catalogue(tmp_path, rows)
    plan = write_plan_for(tmp_path, rows)
    fresh = fresh_plan_for(rows)
    fresh[0]["class"] = "detail" if fresh[0]["class"] != "detail" else "single"  # drawn differently
    report = check(
        corpus,
        questions,
        truth,
        pilot_dir=pilot,
        plan_file=plan,
        review_file=tmp_path / "r.csv",
        fresh_plan=fresh,
    )
    assert any("differs from the draw" in e for e in report.errors)


def test_check_rejects_too_short_skips_of_long_sections(corpus, tmp_path, pilot, monkeypatch):
    import catalogue_plan

    rows = valid_rows()
    questions, truth = write_catalogue(tmp_path, rows)
    plan = write_plan_for(tmp_path, rows)
    text = plan.read_text(encoding="utf-8")
    plan.write_text(
        text + "guide,49,D002#cleanup,S01,single,skipped,too-short,\n", encoding="utf-8"
    )
    monkeypatch.setattr(catalogue_plan, "CATALOGUE_SKIP_MIN_TOKENS", 1)
    report = check(
        corpus,
        questions,
        truth,
        pilot_dir=pilot,
        plan_file=plan,
        review_file=tmp_path / "r.csv",
        fresh_plan=None,
    )
    assert any("too-short needs fewer than 1 tokens" in e for e in report.errors)


def test_accepted_missing_sections_must_stay_annotated(corpus, tmp_path, pilot):
    rows = valid_rows()
    questions, truth = write_catalogue(tmp_path, rows)
    review = tmp_path / "catalogue_review.csv"
    review.write_text(
        "round,question_id,kind,suggestion,section_id,decision,reason,date\n"
        "1,Q001,missing_section,Also cleanup.,D002#cleanup,accepted,,2026-10-20\n",
        encoding="utf-8",
    )
    report = check(
        corpus,
        questions,
        truth,
        pilot_dir=pilot,
        plan_file=write_plan_for(tmp_path, rows),
        review_file=review,
        fresh_plan=fresh_plan_for(rows),
    )
    assert (
        "Q001: accepted section D002#cleanup (review row 2) is no longer annotated"
        in report.findings
    )


def test_unscreened_catalogue_warns_in_draft_and_fails_strictly(corpus, tmp_path, pilot):
    report = run_check(corpus, tmp_path, valid_rows(), pilot, screen=False)
    assert report.errors == []
    assert any(f.startswith("closed-book: not screened Q001, Q002") for f in report.findings)
    assert exit_code(report, draft=True) == 0 and exit_code(report, draft=False) == 1


def test_too_many_hits_is_a_finding(corpus, tmp_path, pilot):
    rows = valid_rows()
    write_screen_for(tmp_path / "closed_book_screen.csv", rows, hits=17)
    report = run_check(corpus, tmp_path, rows, pilot, screen=False)
    assert "closed-book: 17 questions hit without context, at most 16 of 48 (ADR 0038)" in (
        report.findings
    )


def test_malformed_screen_file_is_an_error(corpus, tmp_path, pilot):
    (tmp_path / "closed_book_screen.csv").write_text("id,text\n", encoding="utf-8")
    report = run_check(corpus, tmp_path, valid_rows(), pilot, screen=False)
    assert any("closed_book_screen.csv has columns" in e for e in report.errors)


def test_check_uses_the_redirected_screen_file(closed_book_file, tmp_path):
    assert catalogue.CLOSED_BOOK_FILE == closed_book_file == tmp_path / "closed_book_screen.csv"


def test_cli_screen_answers_and_logs_a_run(cli, tmp_path):
    write_catalogue(tmp_path, valid_rows()[:2])  # the cli fixture's files, now two questions
    runs = tmp_path / "generation_runs.jsonl"
    assert catalogue.run_screen(completer=FakeCompleter(), runs_file=runs) == 0
    record = json.loads(runs.read_text(encoding="utf-8"))
    assert record["step"] == "closed_book_screen" and record["answers"] == 2
    assert record["prompt_tokens"] == 51 + 52 and record["completion_tokens"] == 11 + 12
    assert set(record["outputs_sha256"]) == {"closed_book_screen.csv"}


def test_cli_screen_logs_a_partial_run(cli, tmp_path, capsys):
    write_catalogue(tmp_path, valid_rows()[:3])
    runs = tmp_path / "generation_runs.jsonl"
    assert catalogue.run_screen(completer=FakeCompleter({2: "length"}), runs_file=runs) == 1
    assert "Q002" in capsys.readouterr().err
    record = json.loads(runs.read_text(encoding="utf-8"))
    assert record["answers"] == 2 and record["completion_tokens"] == 11 + 12


def test_cli_screen_refuses_after_the_freeze(cli, tmp_path, capsys):
    (tmp_path / "freeze.json").write_text("{}", encoding="utf-8")  # cli's CATALOGUE_FREEZE_FILE
    assert catalogue.run_screen(completer=FakeCompleter(), runs_file=tmp_path / "r.jsonl") == 1
    assert "frozen" in capsys.readouterr().err


DUPLICATE_PAGES = {
    "a/one.md": (
        "# One {#one}\n\n## Alpha {#alpha}\n\n"
        "Shared: the plugin installs all three skills for every project today. "
        "Then the cache keys on bundle id so recordings replay everywhere. Unique alpha text.\n\n"
        "### Inner {#inner}\n\n"
        "Again the plugin installs all three skills for every project today.\n"
    ),
    "b/two.md": (
        "# Two {#two}\n\n## Beta {#beta}\n\n"
        "Note that the plugin installs all three skills for every project today. "
        "Also the cache keys on bundle id so recordings replay everywhere.\n\n"
        "## Gamma {#gamma}\n\nGamma says plugin installs all three skills for every page.\n"
    ),
}


@pytest.fixture
def duplicate_corpus(tmp_path):
    return load_corpus(*build_corpus(tmp_path, DUPLICATE_PAGES))


def test_own_text_excludes_subsections(duplicate_corpus):
    own = catalogue.own_text(duplicate_corpus, duplicate_corpus.by_id["D001#alpha"])
    assert "Unique alpha text" in own
    assert "Again" not in own


def test_shared_passages_finds_text_shared_with_another_section(duplicate_corpus):
    hits = catalogue.shared_passages(duplicate_corpus, "D001#alpha")
    assert [s["section_id"] for s, _ in hits] == ["D002#beta"]
    assert "plugin installs all three skills for every project today" in hits[0][1]


def test_shared_passages_ignores_ancestors_and_descendants(duplicate_corpus):
    assert "D001#alpha" not in [
        s["section_id"] for s, _ in catalogue.shared_passages(duplicate_corpus, "D001#inner")
    ]
    assert "D001#inner" not in [
        s["section_id"] for s, _ in catalogue.shared_passages(duplicate_corpus, "D001#alpha")
    ]


def test_shared_passages_one_row_per_section(duplicate_corpus):
    hits = catalogue.shared_passages(duplicate_corpus, "D002#beta")
    ids = [s["section_id"] for s, _ in hits]
    assert ids.count("D001#alpha") == 1


def test_shared_passages_below_threshold_is_not_a_hit(duplicate_corpus):
    assert catalogue.shared_passages(duplicate_corpus, "D002#gamma") == []


def test_shared_passages_excerpt_is_capped(duplicate_corpus):
    hits = catalogue.shared_passages(duplicate_corpus, "D001#alpha", excerpt_words=5)
    assert hits[0][1].endswith("…")
    assert len(hits[0][1].split()) == 6  # five words and the ellipsis


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("How do I install the plugin?", "procedural"),
        ("What is the difference between X and Y?", "comparative"),
        ("Why does e2e retry a step?", "conceptual"),
        ("Which models can’t use the forced tool choice?", "limitation"),
        ("What does init write?", "factual"),
        ("Install it", None),
    ],
)
def test_suggest_type(question, expected):
    found = catalogue.suggest_type(question)
    assert (found[0] if found else None) == expected


def test_suggest_type_names_the_matched_phrase():
    assert catalogue.suggest_type("HOW DO I install it?") == ("procedural", "how do i")


def test_class_guide_covers_every_class():
    from config import CATALOGUE_CLASS_GUIDE

    assert set(CATALOGUE_CLASS_GUIDE) == set(QUESTION_CLASSES)
    assert all(g["rule"] and 2 <= len(g["prompts"]) <= 3 for g in CATALOGUE_CLASS_GUIDE.values())


def test_shared_passages_skips_text_found_in_too_many_sections(duplicate_corpus):
    # alpha, beta and inner share "plugin installs all three skills …": three sections > 2
    hits = catalogue.shared_passages(duplicate_corpus, "D002#beta", max_sections=2)
    assert all("plugin installs" not in excerpt for _, excerpt in hits)
    assert [s["section_id"] for s, _ in hits] == ["D001#alpha"]  # still shares the cache sentence


def test_shared_passages_longest_shared_text_first(tmp_path):
    pages = {
        "a/one.md": (
            "# One {#one}\n\n## Short {#short}\n\none two three four five six seven eight\n"
        ),
        "b/two.md": (
            "# Two {#two}\n\n## Long {#long}\n\n"
            "red green blue cyan teal pink gold gray navy lime\n"
        ),
        "c/three.md": (
            "# Three {#three}\n\n## Seed {#seed}\n\n"
            "one two three four five six seven eight. "
            "red green blue cyan teal pink gold gray navy lime\n"
        ),
    }
    corpus = load_corpus(*build_corpus(tmp_path, pages))
    ids = [s["section_id"] for s, _ in catalogue.shared_passages(corpus, "D003#seed")]
    assert ids == ["D002#long", "D001#short"]


def test_shared_passages_excerpt_keeps_the_original_text(tmp_path):
    shared = "Run `npx e2e init` again After You Upgrade, so the Skill stays current."
    pages = {
        "a/one.md": f"# One {{#one}}\n\n## Seed {{#seed}}\n\nIntro. {shared}\n",
        "b/two.md": f"# Two {{#two}}\n\n## Copy {{#copy}}\n\nOther. {shared}\n",
    }
    corpus = load_corpus(*build_corpus(tmp_path, pages))
    [(_, excerpt)] = catalogue.shared_passages(corpus, "D001#seed")
    assert "`npx e2e init` again After You Upgrade" in excerpt


def test_shared_passages_ignores_typescript_examples_but_keeps_shell_commands(tmp_path):
    ts = (
        "```ts\nexport default { targets: [{ engine: web(), "
        "app: { url: 'http://localhost:3000' } }] }\n```"
    )
    sh = "```bash\nnpx e2e login openai then npx e2e login github-copilot for each plan\n```"
    pages = {
        "a/one.md": f"# One {{#one}}\n\n## Seed {{#seed}}\n\nIntro.\n\n{ts}\n\n{sh}\n",
        "b/two.md": f"# Two {{#two}}\n\n## Config {{#config}}\n\nOther.\n\n{ts}\n",
        "c/three.md": f"# Three {{#three}}\n\n## Login {{#login}}\n\nMore.\n\n{sh}\n",
    }
    corpus = load_corpus(*build_corpus(tmp_path, pages))
    ids = [s["section_id"] for s, _ in catalogue.shared_passages(corpus, "D001#seed")]
    assert ids == ["D003#login"]
