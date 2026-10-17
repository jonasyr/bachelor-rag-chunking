"""Scoring page (ADR 0032, 0034): blind rubric scoring of the generated answers.

Shows only a set's blind item file and its scoring sheet: no strategy, no chunk ID, and the key
stays closed. All reading and writing goes through src/scoring_store.py. Opened through the
router app/catalogue_editor.py.
"""

import html

import streamlit as st

import scoring_store as scoring
from config import RUBRIC_CRITERIA, RUBRIC_MAX_SCORE

SCORES = list(range(RUBRIC_MAX_SCORE + 1))
LABELS = {
    "correctness": "Correctness",
    "completeness": "Completeness",
    "groundedness": "Grounded in the excerpts",
    "no_hallucination": "Free of hallucination",
    "clarity": "Clarity",
}
# English rendering of the rubric in docs/reference/evaluation.md (scores 0, 1, 2)
ANCHORS = {
    "correctness": ("wrong", "partly correct", "correct"),
    "completeness": ("key points missing", "partly complete", "complete"),
    "groundedness": ("not supported", "partly supported", "clearly supported by the excerpts"),
    "no_hallucination": ("false or unsupported claims", "small unsupported additions", "none"),
    "clarity": ("unclear", "understandable with weaknesses", "clear and precise"),
}
SUMMARISE = (
    "Everything is scored. Unblind with `uv run python src/evaluate_answers.py --mode summarise`"
    " (for a pilot set add `--set DIR --limit N` as in scaffold)."
)


def choose_set(sets: list[scoring.ScoringSet]) -> scoring.ScoringSet:
    names = [s.name for s in sets]
    with st.sidebar:
        name = st.selectbox("Set", names, key="scoring_set") or names[0]
    return sets[names.index(name)]


def sidebar(items: list[dict], scores: dict[str, dict]) -> None:
    done, total = scoring.progress(items, scores)
    with st.sidebar:
        st.markdown(f"**{done} of {total} scored**")
        st.progress(done / total if total else 0.0)
        rows = ["| Question | Scored |", "|---|---:|"]
        rows += [f"| {q} | {d} of {n} |" for q, d, n in scoring.by_question(items, scores)]
        st.markdown("\n".join(rows))
        if done == total:
            st.caption(SUMMARISE)


def page(text: str) -> None:
    st.html(f'<div class="formatted">{scoring.text_html(text)}</div>')


def form(s: scoring.ScoringSet, item: dict, saved: dict, codes: list[str], locked: bool) -> None:
    code = item["code"]
    st.markdown("**Question**")
    st.html(f'<div class="formatted reference">{scoring.text_html(item["question"])}</div>')
    st.markdown("**Reference answer**")
    st.html(f'<div class="formatted reference">{scoring.text_html(item["reference_answer"])}</div>')
    values = {}
    for criterion in RUBRIC_CRITERIA:
        values[criterion] = st.segmented_control(
            LABELS[criterion],
            SCORES,
            default=saved["values"][criterion],
            key=f"{s.name}|{code}|{criterion}",
            disabled=locked,
        )
        anchors = ANCHORS[criterion]
        chosen = values[criterion]
        st.caption(
            anchors[chosen].capitalize()
            if chosen is not None
            else ", ".join(f"{n} {a}" for n, a in zip(SCORES, anchors, strict=True))
        )
    notes = st.text_input(
        "Notes", value=saved["notes"], key=f"{s.name}|{code}|notes", disabled=locked
    )
    back, forward = st.columns(2)
    position = codes.index(code)
    if back.button("Previous", key="scoring_previous", disabled=position == 0, width="stretch"):
        st.session_state["scoring_goto"] = codes[position - 1]
        st.rerun()
    incomplete = any(v is None for v in values.values())
    if forward.button(
        "Save and next",
        key="scoring_save",
        type="primary",
        disabled=locked or incomplete,
        width="stretch",
    ):
        try:
            scoring.save_score(s, code, values, notes)
        except (ValueError, PermissionError) as error:
            st.error(str(error))
            return
        st.session_state["scoring_goto"] = scoring.next_code(codes, code, scoring.load_scores(s))
        st.session_state["scoring_saved"] = code
        st.rerun()


def main() -> None:
    sets = scoring.scoring_sets()
    if not sets:
        st.info(
            "Nothing to score yet. Run `uv run python src/evaluate_answers.py --mode scaffold` "
            "(with `--set DIR` for a pilot set) after generating the answers."
        )
        return
    s = choose_set(sets)
    try:
        items, scores = scoring.load_items(s), scoring.load_scores(s)
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        return
    sidebar(items, scores)
    locked = scoring.is_read_only(s)
    if locked:
        st.info("The scores of this set were unblinded (scores.csv exists), so it is read-only.")
    codes = [i["code"] for i in items]
    key = f"scoring_code|{s.name}"
    if "scoring_goto" in st.session_state:  # set by a button; allowed before the widget exists
        st.session_state[key] = st.session_state.pop("scoring_goto")
    if st.session_state.get(key) not in codes:
        st.session_state[key] = scoring.first_unscored(codes, scores)
    if saved := st.session_state.pop("scoring_saved", None):
        st.toast(f"Saved {saved}")

    title, picker = st.columns([7, 5], vertical_alignment="bottom", gap="large")
    with picker:
        code = st.selectbox(
            "Jump to",
            codes,
            key=key,
            format_func=lambda c: f"{c}, scored" if scoring.is_scored(scores[c]) else c,
        )
    item = items[codes.index(code)]
    questions = list(dict.fromkeys(i["question_id"] for i in items))
    number = questions.index(item["question_id"]) + 1
    title.html(
        f'<h2 class="slot-title">{html.escape(item["question_id"])}, answer '
        f"{html.escape(code.rsplit('-', 1)[1])} "
        f"<span>question {number} of {len(questions)}</span></h2>"
    )
    reader, side = st.columns([7, 5], gap="large")
    with reader:
        st.markdown("**Answer under review**")
        page(item["answer"])
        st.markdown("**Excerpts the model saw**")
        tabs = st.tabs([str(n) for n in range(1, len(item["excerpts"]) + 1)])
        for tab, text in zip(tabs, item["excerpts"], strict=True):
            with tab:
                page(text)
    with side:
        form(s, item, scores[code], codes, locked)


main()
