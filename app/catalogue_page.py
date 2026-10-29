"""Catalogue page (ADR 0029, 0031): write and annotate the question catalogue.

Shows only the corpus, the catalogue files and the closed-book answers (ADR 0040); never chunks,
strategies, retrieval results or scores (ADR 0027). All reading and writing goes through
src/catalogue_store.py. Opened through the router app/catalogue_editor.py.
"""

import html
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import streamlit as st  # noqa: E402

import catalogue  # noqa: E402
import catalogue_aids as aids  # noqa: E402
import catalogue_overlap  # noqa: E402
import catalogue_plan  # noqa: E402
import catalogue_review  # noqa: E402
import catalogue_store as store  # noqa: E402
import closed_book  # noqa: E402
from config import (  # noqa: E402
    AREA_MIN_QUESTIONS,
    CATALOGUE_CLASS_GUIDE,
    CATALOGUE_DUPLICATE_VISIBLE,
    CATALOGUE_SKIP_REASONS,
    DETAIL_MAX_ANSWER_WORDS,
    ID_SEPARATOR,
    QUESTION_CLASSES,
    QUESTION_TYPES,
)

VIEWS = ["Formatted", "Source text"]  # how the section is shown; the source text is what counts
SKIP_LABELS = {
    "code-or-links": "Only code or links",
    "too-short": "Too short to ask about",
    "duplicate-topic": "Same topic as an earlier slot",
    "no-answerable-content": "Nothing a question could ask",
}


@st.cache_resource
def load_corpus(documents: str, sections: str) -> catalogue.Corpus:
    return catalogue.load_corpus(Path(documents), Path(sections))


def source_page(
    corpus: catalogue.Corpus, section: dict, words: list[str], key: str, view: str = "Formatted"
) -> None:
    """The section either formatted as Markdown or as the exact source text (st.html)."""
    path = store.highlight(corpus.heading_path(section), words)
    if view == "Source text":
        body = store.page_html(corpus.text(section), words)
        st.html(f'<div class="heading-path">{path}</div><div class="source">{body}</div>')
        return
    body = store.formatted_html(corpus.text(section), words)
    st.html(f'<div class="heading-path">{path}</div><div class="formatted">{body}</div>')


def sidebar(
    questions: list[dict],
    truth: dict,
    plan: list[dict],
    review: list[dict],
    screen_rows: list[dict],
) -> None:
    total = sum(QUESTION_CLASSES.values())
    with st.sidebar:
        st.markdown(f"**{len(questions)} of {total} questions**")
        st.progress(min(len(questions) / total, 1.0))
        for title, field, quotas in (
            ("Type", "type", QUESTION_TYPES),
            ("Class", "difficulty", QUESTION_CLASSES),
        ):
            rows = [f"| {title} | Written |", "|---|---:|"]
            for value, quota in quotas.items():
                done = sum(1 for q in questions if q[field] == value)
                rows.append(f"| {value} | {done} of {quota} |")
            st.markdown("\n".join(rows))
        used = {r["question_id"]: r["area"] for r in plan if r["status"] == "used"}
        rows = ["| Area | Written |", "|---|---:|"]
        for a, n in AREA_MIN_QUESTIONS.items():
            rows.append(f"| {a} | {sum(1 for v in used.values() if v == a)} of {n} |")
        st.markdown("\n".join(rows))
        for line in catalogue_plan.plan_summary(plan):
            st.caption(line)
        st.caption(catalogue_review.review_summary(review))
        counts = closed_book.counts(screen_rows, questions, truth)
        st.caption(closed_book.summary(counts, total))


def checks(corpus, row, question, answer, sections, questions, qid) -> list[tuple[bool, str]]:
    draft = {
        "question_id": qid or "new",
        "question": question,
        "type": "",
        "difficulty": row["class"],
    }
    found = catalogue.class_findings(corpus, draft, {"expected_answer": answer}, sections)
    items = [(not found, f"class rule for {row['class']}" if not found else "; ".join(found))]
    words = len(answer.split())
    if row["class"] == "detail":
        items.append(
            (
                words <= DETAIL_MAX_ANSWER_WORDS,
                f"answer has {words} words, at most {DETAIL_MAX_ANSWER_WORDS}",
            )
        )
    key = catalogue.normalised_question(question)
    twin = next(
        (
            q["question_id"]
            for q in questions
            if q["question_id"] != qid and catalogue.normalised_question(q["question"]) == key
        ),
        None,
    )
    if question.strip():
        items.append(
            (
                twin is None,
                "no other question with this wording"
                if twin is None
                else f"same wording as {twin}",
            )
        )
    return items


def render_checks(items: list[tuple[bool, str]]) -> None:
    lis = "".join(
        f'<li class="{"ok" if ok else "problem"}">'
        f"{'Met' if ok else 'Not met'}: {html.escape(text)}</li>"
        for ok, text in items
    )
    st.markdown(f'<ul class="checks">{lis}</ul>', unsafe_allow_html=True)


def class_guide(cls: str) -> None:
    """The class rule and its prompts; the same for every section, so they suggest no content."""
    guide = CATALOGUE_CLASS_GUIDE[cls]
    with st.expander(f"How to write a {cls} question", expanded=True):
        prompts = "".join(f"<li>{html.escape(p)}</li>" for p in guide["prompts"])
        st.html(
            f'<div class="guide"><p class="guide-rule">{html.escape(guide["rule"])}</p>'
            f'<ul class="guide-prompts">{prompts}</ul></div>'
        )


def also_covered_box(corpus, seed, overlap, ids: list[str], extra_key: str, view, frozen) -> None:
    """Sections sharing text or content with the seed; Jonas adds the relevant ones (ADR 0049)."""
    rows = aids.also_covered(corpus, seed, overlap)
    listed = [corpus.by_id[i] for i in ids]
    with st.container(key="also"):
        st.markdown(f"**Also covered elsewhere** ({len(rows)})")
        st.caption(
            "Add every section that holds a part your answer needs. "
            + " ".join(
                text
                for kind, text in (
                    ("same text", "Same text: found by comparing words."),
                    ("related", "Related: listed beforehand by Claude, with what both share."),
                )
                if any(r["kind"] == kind for r in rows)
            )
            + ("" if rows else "No other section shares text with this one; use the search.")
        )
        visible = rows[:CATALOGUE_DUPLICATE_VISIBLE]
        if len(rows) > CATALOGUE_DUPLICATE_VISIBLE and st.toggle(
            f"Show all {len(rows)}", key=f"show_all_{seed['section_id']}"
        ):
            visible = rows
        for row in visible:
            section, sid = row["section"], row["section"]["section_id"]
            added = sid in ids
            inside = not added and any(catalogue.nested(section, s) for s in listed)
            with st.container(border=True, key=f"dup_{sid}"):
                badge = "added" if added else ("inside an added section" if inside else row["kind"])
                st.html(
                    f'<div class="dup-head"><span class="dup-path">'
                    f"{html.escape(corpus.heading_path(section))}</span>"
                    f'<span class="dup-badge {"is-added" if added else ""}">{badge}</span></div>'
                    f'<div class="dup-id">{html.escape(sid)}</div>'
                )
                if row["note"]:
                    st.caption(row["note"])
                if row["kind"] == "same text" and not row["note"]:
                    excerpt = html.escape(aids.plain_excerpt(row["detail"]))
                    st.html(f'<div class="dup-excerpt">“{excerpt}”</div>')
                read, add = st.columns([3, 1], vertical_alignment="center")
                shown = read.toggle("Read section", key=f"read_{sid}")
                if add.button(
                    "Added" if added else "Add",
                    key=f"add_dup_{sid}",
                    disabled=frozen or added,
                    use_container_width=True,
                ):
                    st.session_state[extra_key].append(sid)
                    st.rerun()
                if shown:  # rendered only when open: the box reruns on every keystroke
                    source_page(corpus, section, [], f"dup_{sid}", view)


def next_open(after: str) -> str:
    """The first open slot after `after` in slot order, else the first open one, else `after`."""
    plan = catalogue_plan.read_plan(store.CATALOGUE_PLAN_FILE)
    open_slots = sorted(r["slot_id"] for r in plan if r["status"] == "open")
    later = [s for s in open_slots if s > after]
    return (later or open_slots or [after])[0]


def write_tab(corpus, plan, questions, truth, overlap, frozen: bool) -> None:
    slots = sorted({r["slot_id"] for r in plan if r["status"] in ("open", "used")})
    first_open = next(
        (r["slot_id"] for r in sorted(plan, key=lambda r: r["slot_id"]) if r["status"] == "open"),
        slots[0],
    )

    def label(sid: str) -> str:
        row = catalogue_plan.slot_row(plan, sid)
        return f"{sid}, {row['question_id']}" if row["status"] == "used" else f"{sid}, open"

    if "goto" in st.session_state:  # set by Save/Skip; allowed before the widget exists
        st.session_state["slot"] = st.session_state.pop("goto")
    title, picker = st.columns([7, 5], vertical_alignment="bottom", gap="large")
    with picker:
        sid = (
            st.selectbox(
                "Slot", slots, index=slots.index(first_open), format_func=label, key="slot"
            )
            or first_open
        )
    row = catalogue_plan.slot_row(plan, sid)
    seed = corpus.by_id[row["section_id"]]
    qid = row["question_id"] if row["status"] == "used" else None
    saved_q = next((q for q in questions if q["question_id"] == qid), None)
    saved_t = truth.get(qid or "", {})
    title.html(f'<h2 class="slot-title">Slot {sid} <span>{row["area"]}, {row["class"]}</span></h2>')
    class_guide(row["class"])

    # Reload the form when the saved rows changed on disk (hand edit, review decision).
    fingerprint = (row["section_id"], tuple((saved_q or {}).values()), tuple(saved_t.values()))
    if st.session_state.get(f"saved_{sid}", fingerprint) != fingerprint:
        forget_slot(sid)
    st.session_state[f"saved_{sid}"] = fingerprint

    extra_key = f"extra_{sid}"
    if extra_key not in st.session_state:
        saved_ids = saved_t.get("relevant_section_ids", "").split(ID_SEPARATOR) if saved_t else []
        st.session_state[extra_key] = [s for s in saved_ids if s and s != seed["section_id"]]

    # Two rows in working order; on narrow screens they stack as section, form, other sections,
    # relevant sections and save, search.
    left, right = st.columns([7, 5], gap="large")
    left_b, right_b = st.columns([7, 5], gap="large")
    with right:
        question = (
            st.text_area(
                "Question",
                value=saved_q["question"] if saved_q else "",
                key=f"question_{sid}",
                height=110,
            )
            or ""
        )
        types = list(QUESTION_TYPES)
        type_key = f"qtype_{sid}"
        qtype = st.selectbox(
            "Type",
            types,
            key=type_key,
            index=(
                types.index(saved_q["type"])
                if saved_q and saved_q["type"] in types and type_key not in st.session_state
                else None
            ),
            placeholder="Choose a type",
            format_func=lambda t: f"{t} · {aids.type_quota_left(questions, t, qid)} left",
        )
        hint = catalogue.suggest_type(question)
        if hint and hint[0] != qtype:
            st.button(
                f"Looks like {hint[0]} (“{hint[1]}”) · use it",
                key="use_type",
                disabled=frozen,
                type="tertiary",
                on_click=lambda k=type_key, t=hint[0]: st.session_state.update({k: t}),
            )
        answer = (
            st.text_area(
                "Reference answer",
                value=saved_t.get("expected_answer", ""),
                key=f"answer_{sid}",
                height=130,
            )
            or ""
        )
        notes = (
            st.text_input("Notes", value=saved_q["notes"] if saved_q else "", key=f"notes_{sid}")
            or ""
        )
    with right_b:
        ids = [seed["section_id"], *st.session_state[extra_key]]
        sections = [corpus.by_id[s] for s in ids]
        st.markdown(f"**Relevant sections** ({len(sections)})")
        for s in sections:
            cols = st.columns([5, 1], vertical_alignment="center")
            cols[0].html(
                f'<div class="rel-path">{html.escape(corpus.heading_path(s))}</div>'
                f'<div class="dup-id">{html.escape(s["section_id"])}</div>'
            )
            if s["section_id"] != seed["section_id"] and cols[1].button(
                "Remove", key=f"remove_{s['section_id']}", disabled=frozen, type="tertiary"
            ):
                st.session_state[extra_key].remove(s["section_id"])
                st.rerun()
        items = checks(corpus, row, question, answer, sections, questions, qid)
        render_checks(items)
        blocker = aids.save_blocker(question, answer, qtype, items, questions, qid)
        if blocker:
            st.caption(blocker)
        if st.button(
            "Save question",
            type="primary",
            key="save",
            disabled=frozen or blocker is not None,
            use_container_width=True,
        ):
            try:
                saved = store.save_question(
                    corpus,
                    sid,
                    question,
                    qtype or "",
                    answer,
                    notes,
                    st.session_state[extra_key],
                    question_id=qid,
                )
                st.toast(f"Saved {saved}")
                st.session_state["goto"] = next_open(sid)
                st.rerun()
            except (ValueError, PermissionError) as error:
                st.error(str(error))
        if row["status"] == "open":
            with st.expander("Skip this section"):
                reason = (
                    st.selectbox(
                        "Reason",
                        list(CATALOGUE_SKIP_REASONS),
                        key="skip_reason",
                        format_func=lambda r: str(SKIP_LABELS.get(r, r)),
                    )
                    or CATALOGUE_SKIP_REASONS[0]
                )
                if st.button("Skip this section", key="skip", disabled=frozen):
                    try:
                        store.skip_slot(corpus, sid, reason)
                        forget_slot(sid)  # the draft belonged to the skipped section
                        st.session_state[f"extra_{sid}"] = []
                        st.rerun()
                    except (ValueError, PermissionError) as error:
                        st.error(str(error))

    with left, st.container(key="reader"):
        words = (
            catalogue.shared_words(question, catalogue.heading_texts(corpus, sections))
            if question
            else []
        )
        view = (
            st.segmented_control(
                "View", VIEWS, default=VIEWS[0], key="view", label_visibility="collapsed"
            )
            or VIEWS[0]
        )
        source_page(corpus, seed, words, "seed", view)
    with left_b:
        also_covered_box(corpus, seed, overlap, ids, extra_key, view, frozen)

    # Search below the form: next to the relevant sections on wide screens, last on narrow ones.
    with right_b, st.container(key="search"):
        term = st.text_input(
            "Find more sections", key="find", placeholder="Search the documentation"
        )
        if term.strip():
            hits = catalogue.find(corpus, term)
            if not hits:
                st.caption("No section contains this text.")
            else:
                options = {h[0]["section_id"]: h for h in hits}
                pick = st.selectbox(
                    f"{len(hits)} sections",
                    list(options),
                    key="hit",
                    format_func=lambda s: f"{s}  {corpus.heading_path(options[s][0])}",
                ) or next(iter(options))
                source_page(corpus, options[pick][0], words, "hit", view)
                if st.button("Add this section", key="add_section", disabled=frozen or pick in ids):
                    st.session_state[extra_key].append(pick)
                    st.rerun()


def forget_slot(sid: str) -> None:
    """Drop a slot's form state so it is rebuilt from the files."""
    for name in ("extra", "question", "answer", "notes", "qtype"):
        st.session_state.pop(f"{name}_{sid}", None)


def forget_section_lists() -> None:
    """Drop cached section lists so they are reloaded from the ground truth file."""
    for key in [k for k in st.session_state if str(k).startswith("extra_")]:
        del st.session_state[key]


def review_tab(corpus, review: list[dict], questions: list[dict], frozen: bool) -> None:
    text = {q["question_id"]: q["question"] for q in questions}
    pending = [(i, r) for i, r in enumerate(review) if r["decision"] == "open"]
    if not pending:
        st.info("No open suggestions.")
    for i, r in pending:
        with st.container(border=True):
            st.markdown(f"**{r['question_id']}**: {text.get(r['question_id'], '')}")
            st.markdown(f"{r['kind'].replace('_', ' ').capitalize()}: {r['suggestion']}")
            if r["section_id"]:
                source_page(corpus, corpus.by_id[r["section_id"]], [], f"review_{i}")
            reason = st.text_input("Reason", key=f"reason_{i}")
            a, b = st.columns(2)
            today = date.today().isoformat()
            if a.button("Accept", key=f"accept_{i}", disabled=frozen):
                try:
                    store.accept_suggestion(corpus, i, reason or "", today)
                    forget_section_lists()
                    st.rerun()
                except (ValueError, PermissionError) as error:
                    st.error(str(error))
            if b.button("Reject", key=f"reject_{i}", disabled=frozen):
                try:
                    store.reject_suggestion(i, reason or "", today)
                    forget_section_lists()
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
    decided = [r for r in review if r["decision"] != "open"]
    if decided:
        with st.expander(f"Decided ({len(decided)})"):
            for r in decided:
                reason = r["reason"] or "no reason"
                st.markdown(f"{r['question_id']}, {r['kind']}: {r['decision']} ({reason})")


VERDICT_LABELS = {"hit": "Hits the core point", "miss": "Misses it"}


def closed_book_tab(screen_rows, questions, truth, frozen: bool) -> None:
    """Jonas' verdict on each answer without context (ADR 0040); the editor never calls the API."""
    rows = {r["question_id"]: r for r in screen_rows}
    found = closed_book.states(screen_rows, questions, truth)
    unscreened = [qid for qid, s in found.items() if s == closed_book.NOT_SCREENED]
    pending = [q for q in questions if found[q["question_id"]] == closed_book.NOT_JUDGED]
    judged = [q for q in questions if found[q["question_id"]] in VERDICT_LABELS]
    if unscreened:
        st.info(
            f"{len(unscreened)} question(s) without an answer yet: run "
            "`uv run python src/catalogue.py screen`."
        )
    elif not pending and questions:
        st.info("Every question is judged.")
    today = date.today().isoformat()

    def record(qid: str, verdict: str, note: str) -> None:
        try:
            store.judge_closed_book(qid, verdict, note, today)
            st.rerun()
        except (ValueError, PermissionError) as error:
            st.error(str(error))

    for q in pending:
        qid = q["question_id"]
        with st.container(border=True):
            st.markdown(f"**{qid}**: {q['question']}")
            reference = html.escape(truth.get(qid, {}).get("expected_answer", ""))
            st.html(f'<div class="cb-reference">Reference answer: {reference}</div>')
            st.caption("Answer without context")
            st.html(f'<div class="cb-answer">{html.escape(rows[qid]["answer"])}</div>')
            note = st.text_input("Note", key=f"cb_note_{qid}") or ""
            a, b = st.columns(2)
            if a.button(VERDICT_LABELS["hit"], key=f"cb_hit_{qid}", disabled=frozen):
                record(qid, "hit", note)
            if b.button(VERDICT_LABELS["miss"], key=f"cb_miss_{qid}", disabled=frozen):
                record(qid, "miss", note)
    if judged:
        with st.expander(f"Judged ({len(judged)})"):
            for q in judged:
                qid, verdict = q["question_id"], found[q["question_id"]]
                other = "miss" if verdict == "hit" else "hit"
                note = rows[qid]["note"]
                st.markdown(
                    f"**{qid}** {VERDICT_LABELS[verdict].lower()}: {q['question']}"
                    + (f" ({note})" if note else "")
                )
                if st.button(
                    f"Change to: {VERDICT_LABELS[other].lower()}",
                    key=f"cb_flip_{qid}",
                    disabled=frozen,
                ):
                    record(qid, other, note)


def unknown_sections(corpus, plan, truth, review, overlap=None) -> list[str]:
    """Section IDs in the plan, the ground truth, the review or the overlap list that the corpus
    does not have."""
    ids = {r["section_id"] for r in plan}
    ids |= {s for t in truth.values() for s in t["relevant_section_ids"].split(ID_SEPARATOR) if s}
    ids |= {r["section_id"] for r in review if r["section_id"]}
    ids |= catalogue_overlap.overlap_section_ids(overlap or {})
    return sorted(ids - set(corpus.by_id))


def main() -> None:
    corpus = load_corpus(str(store.DOCUMENTS_FILE), str(store.SECTIONS_FILE))
    try:
        plan = catalogue_plan.read_plan(store.CATALOGUE_PLAN_FILE)
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        return
    questions, truth = store.load_catalogue()
    review = catalogue_review.read_review(store.CATALOGUE_REVIEW_FILE)
    try:
        screen_rows = closed_book.read_screen(store.CLOSED_BOOK_FILE)
    except ValueError as error:
        st.error(str(error))
        return
    try:
        overlap = catalogue_overlap.read_overlap(store.CATALOGUE_OVERLAP_FILE)
    except ValueError as error:
        st.error(str(error))
        return
    unknown = unknown_sections(corpus, plan, truth, review, overlap)
    if unknown:
        st.error(
            f"Section IDs not in sections.jsonl: {', '.join(unknown)}. The corpus was rebuilt or a "
            "file was edited by hand; fix the files before editing."
        )
        return
    frozen = store.is_frozen()
    sidebar(questions, truth, plan, review, screen_rows)
    if frozen:
        st.info("The catalogue is frozen (ADR 0030). You can read it, but not change it.")
    open_count = sum(1 for r in review if r["decision"] == "open")
    unjudged = sum(
        1
        for s in closed_book.states(screen_rows, questions, truth).values()
        if s == closed_book.NOT_JUDGED
    )
    write, rev, cb = st.tabs(
        [
            "Write",
            f"Review ({open_count})" if open_count else "Review",
            f"Closed-book ({unjudged})" if unjudged else "Closed-book",
        ]
    )
    with write:
        write_tab(corpus, plan, questions, truth, overlap, frozen)
    with rev:
        review_tab(corpus, review, questions, frozen)
    with cb:
        closed_book_tab(screen_rows, questions, truth, frozen)


main()
