"""Scoring page (ADR 0032, 0034, 0035): blind, rule-based rubric scoring of the generated answers.

Two steps: Key points (per question only the question and its reference answer, then frozen)
and Score (factual checks per answer; the five scores follow from src/scoring_rules.py). Shows
only a set's blind item file and its scoring sheet: no strategy, no chunk ID, and the key stays
closed. All reading and writing goes through src/scoring_store.py. Opened through the router
app/catalogue_editor.py.
"""

import html
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent  # also when the page runs on its own (tests)
sys.path.insert(0, str(APP_DIR.parent / "src"))
sys.path.insert(0, str(APP_DIR))

import streamlit as st  # noqa: E402
from ui_theme import SCORING_CSS  # noqa: E402

import scoring_rules as rules  # noqa: E402
import scoring_store as scoring  # noqa: E402
from config import KEY_POINTS_MAX, RUBRIC_CRITERIA  # noqa: E402

STEPS = ["Key points", "Score"]
LABELS = {
    "correctness": "Correctness",
    "completeness": "Completeness",
    "groundedness": "Grounded in the excerpts",
    "no_hallucination": "Free of hallucination",
    "clarity": "Clarity",
}
# the checks of ADR 0035 as the form asks them (docs/reference/evaluation.md)
QUESTIONS = {
    "declines": "Does the answer say the excerpts do not contain the answer, and give none?",
    "core_wrong": "Does it state the core point wrongly or contradict it?",
    "other_error": "Is any other statement factually wrong?",
    "grounded": "How many of its statements are backed by the excerpts?",
    "hallucination": "Does it contain anything that neither the excerpts nor the reference cover?",
    "answers_question": "Does it address what was asked?",
    "direct": "Is the answer given directly, in the first two sentences?",
    "wordy": "Is it repetitive, padded or confusing?",
}
OPTION_LABELS = {"minor": "Minor addition"}
GROUPS = {  # heading shown before the first check of each group
    "core_wrong": "Facts",
    "grounded": "Sources",
    "answers_question": "Clarity",
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
    st.html(f'<div class="formatted inert">{scoring.text_html(text)}</div>')


def question_cards(question: str, reference: str) -> None:
    st.markdown("**Question**")
    st.html(f'<div class="context inert">{scoring.text_html(question)}</div>')
    st.markdown("**Reference answer**")
    st.html(f'<div class="context reference inert">{scoring.text_html(reference)}</div>')


def point_label(n: int) -> str:
    return "Core point" if n == 1 else f"Point {n}"


def key_points_step(s: scoring.ScoringSet, items: list[dict], read_only: bool) -> None:
    """Write the key points per question; never shows an answer or an excerpt (ADR 0035)."""
    qs = scoring.questions(items)
    points = scoring.load_key_points(s)
    ids = [q["question_id"] for q in qs]
    with st.sidebar:
        done = sum(q in points for q in ids)
        st.markdown(f"**{done} of {len(ids)} questions have key points**")
        st.progress(done / len(ids) if ids else 0.0)
    pick_key = f"kp_question|{s.name}"
    if "kp_goto" in st.session_state:  # set by a button; allowed before the widget exists
        st.session_state[pick_key] = st.session_state.pop("kp_goto")
    if st.session_state.get(pick_key) not in ids:
        st.session_state[pick_key] = next((q for q in ids if q not in points), ids[0])
    qid = st.selectbox(
        "Go to question",
        ids,
        key=pick_key,
        format_func=lambda q: f"{q}, done" if q in points else q,
    )
    q = qs[ids.index(qid)]
    cards, inputs = st.columns([7, 5], gap="large")
    with cards:
        question_cards(q["question"], q["reference_answer"])
    with inputs:
        key_point_inputs(s, items, ids, qid, points.get(qid, []), read_only)
    if read_only:
        st.info("The key points are frozen.")
        return
    st.divider()
    confirm = st.checkbox(
        "Freeze the key points. They cannot be changed afterwards.", key="kp_confirm"
    )
    if st.button(
        "Freeze key points",
        key="kp_freeze",
        disabled=not confirm or any(x not in points for x in ids),
    ):
        try:
            scoring.freeze_key_points(s, items)
        except (ValueError, PermissionError) as error:
            st.error(str(error))
            return
        st.session_state["scoring_frozen_now"] = True
        st.rerun()


def key_point_inputs(
    s: scoring.ScoringSet,
    items: list[dict],
    ids: list[str],
    qid: str,
    saved: list[str],
    read_only: bool,
) -> None:
    texts = [
        st.text_input(
            point_label(n),
            value=saved[n - 1] if n <= len(saved) else "",
            key=f"kp|{s.name}|{qid}|{n}",
            disabled=read_only,
            help="The direct answer to the question" if n == 1 else None,
        )
        for n in range(1, KEY_POINTS_MAX + 1)
    ]
    used = [bool(t.strip()) for t in texts]
    filled = [t for t in texts if t.strip()]
    # point 1 is the core point: never renumber a later point into its place
    contiguous = bool(filled) and used == [True] * len(filled) + [False] * (
        len(texts) - len(filled)
    )
    if filled and not contiguous:
        st.caption("Fill the core point first and the other points in order, without gaps.")
    if st.button(
        "Save and next", key="kp_save", type="primary", disabled=read_only or not contiguous
    ):
        try:
            scoring.save_key_points(s, items, qid, filled)
        except (ValueError, PermissionError) as error:
            st.error(str(error))
            return
        rest = [x for x in ids if x not in scoring.load_key_points(s)]
        st.session_state["kp_goto"] = rest[0] if rest else qid
        st.rerun()


def control(label: str, options: tuple[str, ...], default, key: str, locked: bool):
    return st.segmented_control(
        label,
        list(options),
        default=default,
        key=key,
        disabled=locked,
        format_func=lambda o: OPTION_LABELS.get(o, o.capitalize()),
    )


def form(
    s: scoring.ScoringSet,
    item: dict,
    saved_notes: str,
    saved_checks: dict | None,
    key_points: list[str],
    codes: list[str],
    locked: bool,
) -> None:
    code = item["code"]
    question_cards(item["question"], item["reference_answer"])
    stored = saved_checks or {}
    # checks skipped while the answer was declining were never asked: they start empty
    declined_before = stored.get("declines") == "yes"
    answers = {
        "declines": control(
            QUESTIONS["declines"],
            rules.CHECKS["declines"],
            stored.get("declines"),
            f"{s.name}|{code}|declines",
            locked,
        )
    }
    declines = answers["declines"] == "yes"
    marks = []
    if not declines:
        st.markdown("**Key points**")
        for n, text in enumerate(key_points, start=1):
            marks.append(
                control(
                    f"{point_label(n)}: {text}",
                    rules.POINT_MARKS,
                    None
                    if declined_before or n > len(stored.get("points", []))
                    else stored["points"][n - 1],
                    f"{s.name}|{code}|point_{n}",
                    locked,
                )
            )
    for check in list(rules.CHECKS)[1:]:
        skipped = check in rules.SKIPPED_WHEN_DECLINING
        if declines and skipped:
            continue
        default = None if declined_before and skipped else stored.get(check)
        if check in GROUPS:
            st.markdown(f"**{GROUPS[check]}**")
        answers[check] = control(
            QUESTIONS[check], rules.CHECKS[check], default, f"{s.name}|{code}|{check}", locked
        )
    answered = all(v is not None for v in answers.values()) and None not in marks
    checks = rules.declined(answers | {"points": marks}, len(key_points)) if answered else None
    if checks:
        values = rules.derive(checks)
        rows = ["| Score | |", "|---|---:|"]
        rows += [f"| {LABELS[c]} | {values[c]} |" for c in RUBRIC_CRITERIA]
        st.markdown("\n".join(rows))
    else:
        st.caption("The five scores appear once every check is answered.")
    notes = st.text_input(
        "Notes",
        value=saved_notes,
        key=f"{s.name}|{code}|notes",
        disabled=locked,
        placeholder="e.g. a rule did not fit",
    )
    back, forward = st.columns(2)
    position = codes.index(code)
    if back.button("Previous", key="scoring_previous", disabled=position == 0, width="stretch"):
        st.session_state["scoring_goto"] = codes[position - 1]
        st.rerun()
    if forward.button(
        "Save and next",
        key="scoring_save",
        type="primary",
        disabled=locked or checks is None,
        width="stretch",
    ):
        try:
            scoring.save_score(s, code, checks, notes)
        except (ValueError, PermissionError) as error:
            st.error(str(error))
            return
        st.session_state["scoring_goto"] = scoring.next_code(codes, code, scoring.load_scores(s))
        st.session_state["scoring_saved"] = code
        st.rerun()


def main() -> None:
    st.markdown(SCORING_CSS, unsafe_allow_html=True)
    sets = scoring.scoring_sets()
    if not sets:
        st.info(
            "Nothing to score yet. Run `uv run python src/evaluate_answers.py --mode scaffold` "
            "(with `--set DIR` for a pilot set) after generating the answers; run it again to "
            "restore a lost item file, the scores in the sheet stay."
        )
        return
    s = choose_set(sets)
    try:
        items, scores = scoring.load_items(s), scoring.load_scores(s)
        key_points, checks = scoring.load_key_points(s), scoring.load_checks(s)
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        return
    locked = scoring.is_read_only(s)
    if locked:
        st.info("The scores of this set were unblinded (scores.csv exists), so it is read-only.")
    frozen = scoring.is_frozen(s)
    step_key = f"scoring_step|{s.name}"
    if not frozen:  # no Score step without a freeze for the current scaffold
        st.session_state[step_key] = "Key points"
    elif st.session_state.pop("scoring_frozen_now", False) or step_key not in st.session_state:
        st.session_state[step_key] = "Score"
    step = st.segmented_control(
        "Step", STEPS, key=step_key, label_visibility="collapsed", required=True
    )
    if step == "Key points" or not frozen:
        if not frozen:
            st.caption("Scoring opens once the key points are frozen.")
        key_points_step(s, items, frozen or locked)
        return
    try:
        scoring.require_frozen_key_points(s)
    except PermissionError as error:  # e.g. key_points.csv edited by hand after the freeze
        st.error(str(error))
        return

    sidebar(items, scores)
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
    if not key_points.get(item["question_id"]):
        with side:
            st.error(
                f"{item['question_id']} has no frozen key points: the set was scaffolded again "
                "with more questions after the freeze. Its answers cannot be scored by the rules; "
                "scaffold the set as it was frozen, or start a new set."
            )
        return
    with side:
        form(
            s,
            item,
            scores[code]["notes"],
            checks.get(code),
            key_points.get(item["question_id"], []),
            codes,
            locked,
        )


main()
