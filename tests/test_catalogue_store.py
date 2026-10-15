import pytest

import catalogue_store as store
from catalogue_plan import read_plan, write_plan
from catalogue_review import REVIEW_HEADER, read_review, save_review

SMALL = {
    "slots": {"api": 1, "style-guide": 1, "guide": 1},
    "reserve": {"api": 1, "style-guide": 0, "guide": 1},
    "classes": {"single": 1, "multi-section": 1, "paraphrase": 1},
}


@pytest.fixture
def files(corpus, tmp_path, monkeypatch):
    paths = {
        "QUESTIONS_FILE": tmp_path / "questions.csv",
        "GROUND_TRUTH_FILE": tmp_path / "ground_truth.csv",
        "CATALOGUE_PLAN_FILE": tmp_path / "catalogue_plan.csv",
        "CATALOGUE_REVIEW_FILE": tmp_path / "catalogue_review.csv",
        "CATALOGUE_FREEZE_FILE": tmp_path / "catalogue_freeze.json",
    }
    for name, path in paths.items():
        monkeypatch.setattr(store, name, path)
    write_plan(corpus, paths["CATALOGUE_PLAN_FILE"], seed=3, **SMALL)
    return paths


def test_empty_catalogue_loads_and_numbers_from_q001(files):
    assert store.load_catalogue() == ([], {})
    assert store.next_question_id([]) == "Q001"
    assert store.next_question_id([{"question_id": "Q009"}, {"question_id": "Q010"}]) == "Q011"


def test_save_writes_both_files_and_uses_the_slot(corpus, files):
    plan = read_plan(files["CATALOGUE_PLAN_FILE"])
    s01 = next(r for r in plan if r["slot_id"] == "S01")
    qid = store.save_question(
        corpus,
        "S01",
        " What does ref() return? ",
        "factual",
        "A reactive ref object.",
        "",
        ["D002#once"],
    )
    assert qid == "Q001"
    questions, truth = store.load_catalogue()
    assert questions == [
        {
            "question_id": "Q001",
            "question": "What does ref() return?",
            "type": "factual",
            "difficulty": s01["class"],
            "notes": "",
        }
    ]
    sids = truth["Q001"]["relevant_section_ids"].split(";")
    assert sids[0] == s01["section_id"] and "D002#once" in sids  # starting section always first
    docs = truth["Q001"]["relevant_doc_ids"].split(";")
    assert docs == list(dict.fromkeys(s.split("#")[0] for s in sids))
    row = next(r for r in read_plan(files["CATALOGUE_PLAN_FILE"]) if r["slot_id"] == "S01")
    assert (row["status"], row["question_id"]) == ("used", "Q001")
    assert files["QUESTIONS_FILE"].read_text(encoding="utf-8").endswith("\n")


def test_edit_keeps_id_and_cannot_drop_the_starting_section(corpus, files):
    store.save_question(corpus, "S01", "Q one?", "factual", "A.", "", [])
    s01 = next(r for r in read_plan(files["CATALOGUE_PLAN_FILE"]) if r["slot_id"] == "S01")
    store.save_question(
        corpus,
        "S01",
        "Q one, edited?",
        "conceptual",
        "B.",
        "n",
        ["D002#cleanup"],
        question_id="Q001",
    )
    questions, truth = store.load_catalogue()
    assert [q["question"] for q in questions] == ["Q one, edited?"]
    assert truth["Q001"]["relevant_section_ids"].split(";")[0] == s01["section_id"]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"question": " "}, "question is empty"),
        ({"answer": ""}, "reference answer is empty"),
        ({"qtype": "trivia"}, "unknown type"),
        ({"section_ids": ["D099#x"]}, "unknown section"),
        ({"slot_id": "S09"}, "no slot S09"),
    ],
)
def test_save_refuses_invalid_input(corpus, files, kwargs, message):
    args = {
        "slot_id": "S01",
        "question": "Q?",
        "qtype": "factual",
        "answer": "A.",
        "notes": "",
        "section_ids": [],
    } | kwargs
    with pytest.raises(ValueError, match=message):
        store.save_question(corpus, **args)
    assert not files["QUESTIONS_FILE"].exists()


def test_save_refuses_after_the_freeze(corpus, files):
    files["CATALOGUE_FREEZE_FILE"].write_text("{}", encoding="utf-8")
    with pytest.raises(PermissionError, match="frozen"):
        store.save_question(corpus, "S01", "Q?", "factual", "A.", "", [])


def test_accepting_a_missing_section_adds_it(corpus, files):
    store.save_question(corpus, "S01", "Q?", "factual", "A.", "", [])
    save_review(
        files["CATALOGUE_REVIEW_FILE"],
        [
            dict.fromkeys(REVIEW_HEADER, "")
            | {
                "round": "1",
                "question_id": "Q001",
                "kind": "missing_section",
                "suggestion": "Also cleanup.",
                "section_id": "D002#cleanup",
                "decision": "open",
            },
            dict.fromkeys(REVIEW_HEADER, "")
            | {
                "round": "1",
                "question_id": "Q001",
                "kind": "wording",
                "suggestion": "Name the hook.",
                "decision": "open",
            },
        ],
    )
    store.accept_suggestion(corpus, 0, "", "2026-10-20")
    assert "D002#cleanup" in store.load_catalogue()[1]["Q001"]["relevant_section_ids"]
    store.reject_suggestion(1, "already clear", "2026-10-20")
    assert [r["decision"] for r in read_review(files["CATALOGUE_REVIEW_FILE"])] == [
        "accepted",
        "rejected",
    ]


def test_highlight_marks_matching_words_and_escapes_html():
    out = store.highlight("Use <script setup> with Watchers.", ["watcher"])
    assert out == 'Use &lt;script setup&gt; with <mark class="hl">Watchers</mark>.'


def test_a_question_cannot_move_to_another_slot(corpus, files):
    store.save_question(corpus, "S01", "Q one?", "factual", "A.", "", [])
    with pytest.raises(ValueError, match="Q001 belongs to slot S01"):
        store.save_question(corpus, "S02", "Q two?", "factual", "B.", "", [], question_id="Q001")


@pytest.mark.parametrize(
    "line",
    ["Q002,Too many?,factual,single,,extra", "Q002,too short"],
)
def test_malformed_rows_are_refused_and_nothing_is_rewritten(corpus, files, line):
    store.save_question(corpus, "S01", "Q one?", "factual", "A.", "", [])
    path = files["QUESTIONS_FILE"]
    path.write_text(path.read_text(encoding="utf-8") + line + "\n", encoding="utf-8")
    before = path.read_bytes()
    with pytest.raises(ValueError, match="fields"):
        store.load_catalogue()
    with pytest.raises(ValueError, match="fields"):
        store.save_question(
            corpus, "S01", "Q one, edited?", "factual", "A.", "", [], question_id="Q001"
        )
    assert path.read_bytes() == before


def test_duplicate_ids_are_refused(corpus, files):
    store.save_question(corpus, "S01", "Q one?", "factual", "A.", "", [])
    path = files["GROUND_TRUTH_FILE"]
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join([*lines, lines[1]]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate question_id"):
        store.load_catalogue()


def test_a_failed_write_keeps_the_old_file(corpus, files, monkeypatch):
    import atomic_csv

    store.save_question(corpus, "S01", "Q one?", "factual", "A.", "", [])
    before = files["QUESTIONS_FILE"].read_bytes()

    def broken(*args):
        raise OSError("disk full")

    monkeypatch.setattr(atomic_csv.os, "replace", broken)
    with pytest.raises(OSError):
        store.save_question(
            corpus, "S01", "Q one, edited?", "factual", "A.", "", [], question_id="Q001"
        )
    assert files["QUESTIONS_FILE"].read_bytes() == before
    assert not list(files["QUESTIONS_FILE"].parent.glob("*.tmp"))


def test_the_plan_is_written_first_so_a_retry_reuses_the_id(corpus, files, monkeypatch):
    real = store.write_rows

    def fail_on_truth(path, header, rows):
        if path == files["GROUND_TRUTH_FILE"]:
            raise OSError("disk full")
        real(path, header, rows)

    monkeypatch.setattr(store, "write_rows", fail_on_truth)
    with pytest.raises(OSError):
        store.save_question(corpus, "S01", "Q one?", "factual", "A.", "", [])
    monkeypatch.setattr(store, "write_rows", real)
    assert store.save_question(corpus, "S01", "Q one?", "factual", "A.", "", []) == "Q001"


def test_next_question_id_also_counts_the_plan():
    plan = [{"status": "used", "question_id": "Q005"}, {"status": "open", "question_id": ""}]
    assert store.next_question_id([{"question_id": "Q002"}], plan) == "Q006"


def test_highlight_splits_camel_case_like_the_rule():
    assert store.highlight("Use onMounted().", ["mounted"]) == (
        'Use <mark class="hl">onMounted</mark>().'
    )


def test_page_html_sets_fenced_code_in_monospace_and_keeps_highlights():
    text = "Use the hook.\n\n```ts\nonMounted(() => {})\n```\nDone."
    out = store.page_html(text, ["mounted"])
    code = '```ts\n<mark class="hl">onMounted</mark>(() =&gt; {})\n```'
    assert f'<span class="code">{code}</span>' in out
    assert out.startswith("Use the hook.") and out.endswith("Done.")


def test_skip_is_refused_after_the_freeze(corpus, files):
    files["CATALOGUE_FREEZE_FILE"].write_text("{}", encoding="utf-8")
    before = files["CATALOGUE_PLAN_FILE"].read_bytes()
    with pytest.raises(PermissionError, match="frozen"):
        store.skip_slot(corpus, "S01", "code-or-links")
    assert files["CATALOGUE_PLAN_FILE"].read_bytes() == before


def test_unknown_sections_are_value_errors(corpus, files):
    store.save_question(corpus, "S01", "Q?", "factual", "A.", "", [])
    save_review(
        files["CATALOGUE_REVIEW_FILE"],
        [
            dict.fromkeys(REVIEW_HEADER, "")
            | {
                "round": "1",
                "question_id": "Q001",
                "kind": "missing_section",
                "suggestion": "x",
                "section_id": "D009#nope",
                "decision": "open",
            },
        ],
    )
    with pytest.raises(ValueError, match="D009#nope"):
        store.accept_suggestion(corpus, 0, "", "2026-10-20")
    rows = read_plan(files["CATALOGUE_PLAN_FILE"])
    next(r for r in rows if r["slot_id"] == "S02")["section_id"] = "D999#gone"
    from catalogue_plan import save_plan

    save_plan(files["CATALOGUE_PLAN_FILE"], rows)
    with pytest.raises(ValueError, match="D999#gone"):
        store.save_question(corpus, "S02", "Q2?", "factual", "B.", "", [])


def test_markdown_view_marks_prose_but_leaves_code_alone():
    text = (
        "## onMounted()\n\nRuns when `onMounted` fires after mounted.\n\n"
        "```ts\nonMounted(() => {})\n```\n"
    )
    out = store.markdown_with_highlights(text, ["mounted"])
    assert '## <mark class="hl">onMounted</mark>()' in out
    assert "`onMounted`" in out  # inline code untouched
    assert 'after <mark class="hl">mounted</mark>.' in out
    assert "```ts\nonMounted(() => {})\n```" in out  # fenced code untouched


def test_markdown_view_shows_tags_in_prose_as_text_and_fixes_doc_links():
    text = "Use <script setup> with [defineProps](/api/sfc-script-setup#defineprops)."
    out = store.markdown_with_highlights(text, ["props", "script"])
    assert "&lt;" in out and "<script" not in out
    assert "(https://vuejs.org/api/sfc-script-setup#defineprops)" in out  # link target not marked
    assert '[<mark class="hl">defineProps</mark>]' in out  # whole token, like the source view


@pytest.mark.parametrize(
    "block",
    [
        "~~~md\nSee [API](/api/foo) when mounted.\n~~~",
        "````md\n```js\nmounted [API](/api/foo)\n```\n````",
    ],
)
def test_every_fence_form_of_the_preprocessing_stays_verbatim(block):
    text = f"Before mounted.\n\n{block}\n\nAfter."
    out = store.markdown_with_highlights(text, ["mounted"])
    assert block in out  # no link rewrite, no marks inside the code block
    assert 'Before <mark class="hl">mounted</mark>.' in out
    page = store.page_html(text, ["mounted"])
    assert '<span class="code">' + block.split("\n")[0] in page


def test_multi_backtick_code_spans_stay_whole():
    text = "Use ``foo ` mounted`` and ```a `` b mounted``` then mounted. A lone ` mounted."
    out = store.markdown_with_highlights(text, ["mounted"])
    assert "``foo ` mounted``" in out and "```a `` b mounted```" in out
    assert 'then <mark class="hl">mounted</mark>.' in out
    assert 'A lone ` <mark class="hl">mounted</mark>.' in out  # unmatched backtick is plain text
