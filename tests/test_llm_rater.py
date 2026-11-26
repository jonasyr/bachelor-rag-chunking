import json
from types import SimpleNamespace

import pytest
from conftest import SCORING_CODES, write_scoring_set

import llm_rater
import scoring_rules as rules
import scoring_store
import second_rater
from atomic_csv import read_csv, write_csv
from config import (
    LLM_RATER_MAX_TOKENS,
    LLM_RATER_MODEL,
    LLM_RATER_REASONING_EFFORT,
    LLM_RATER_SEED,
    LLM_RATER_TEMPERATURE,
    RUBRIC_CRITERIA,
    RUBRIC_RULES_VERSION,
)
from evaluate_answers import SHEET_HEADER
from run_log import append_step_run, latest_run, sha256_of

POINTS = {"H01": ["Core one"], "H02": ["Core two", "Second two"]}


def valid(n: int, **override) -> dict:
    """A valid parsed answer for a question with n key points."""
    answer = {
        "declines": "no",
        "points": ["covered"] * n,
        "core_wrong": "no",
        "other_error": "no",
        "grounded": "all",
        "hallucination": "none",
        "answers_question": "yes",
        "direct": "yes",
        "wordy": "no",
        "reason": "Covers the core point.",
    }
    return answer | override


class FakeOpenAI:
    """Mimics client.chat.completions.create and client.models.retrieve (no network). The reply
    is built from the requested schema (the number of key points) by `reply(n, call)`."""

    def __init__(self, reply=None, finish_reason="stop", fail_at=None, created=1789406102):
        self.requests = []
        self.reply = reply or (lambda n, call: valid(n))
        self.finish_reason = finish_reason
        self.fail_at = fail_at  # 1-based call that raises (a network error)
        self.created = created
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        self.models = SimpleNamespace(retrieve=self.retrieve)

    def retrieve(self, model):
        return SimpleNamespace(id=model, created=self.created)

    def create(self, **kwargs):
        self.requests.append(kwargs)
        call = len(self.requests)
        if call == self.fail_at:
            raise ConnectionError("network down")
        n = kwargs["response_format"]["json_schema"]["schema"]["properties"]["points"]["minItems"]
        content = json.dumps(self.reply(n, call))
        return SimpleNamespace(
            model="gpt-6-sol-x",
            system_fingerprint="fp_1",
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=content), finish_reason=self.finish_reason
                )
            ],
            usage=SimpleNamespace(prompt_tokens=500, completion_tokens=60),
            model_dump=lambda mode: {"id": f"chatcmpl-{call}", "content": content},
        )


def own_set(p: dict) -> scoring_store.ScoringSet:
    return scoring_store.ScoringSet(
        "own",
        p["items_file"],
        p["sheet_file"],
        p["scores_file"],
        p["key_points_file"],
        p["checks_file"],
        p["runs_file"],
    )


@pytest.fixture
def pilot(tmp_path, monkeypatch):
    """A pilot set with six blind items (H01, H02), frozen key points and a draw of H01."""
    monkeypatch.setattr(llm_rater, "LLM_RATER_SCOPE", "all")
    folder = tmp_path / "pilot_set"
    write_scoring_set(folder)
    p = llm_rater.paths(folder)
    mine = own_set(p)
    items = scoring_store.load_items(mine)
    for qid, texts in POINTS.items():
        scoring_store.save_key_points(mine, items, qid, texts)
    scoring_store.freeze_key_points(mine, items)
    write_csv(
        p["sample_file"],
        second_rater.SAMPLE_HEADER,
        [{"question_id": "H01", "type": "factual", "difficulty": "hard"}],
    )
    append_step_run("second_rater_draw", "C1,C2,C3", [], [p["sample_file"]], p["runs_file"])
    return p


def outputs(p: dict) -> tuple[list[dict], list[dict]]:
    checks = read_csv(p["out_dir"] / "scoring_checks.csv", rules.CHECKS_HEADER)
    sheet = read_csv(p["out_dir"] / "scoring_sheet.csv", SHEET_HEADER)
    return checks, sheet


def journal(p: dict) -> list[dict]:
    path = p["out_dir"] / "llm_rater_journal.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_paths_pilot_and_main(tmp_path):
    p = llm_rater.paths(tmp_path)
    assert p["out_dir"] == tmp_path / "llm_rater"
    assert p["runs_file"] == tmp_path / "runs.jsonl"
    assert llm_rater.paths(None)["out_dir"] == llm_rater.LLM_RATER_DIR


def test_schema_enums_match_rules():
    s = llm_rater.schema(3)
    assert s["type"] == "object" and s["additionalProperties"] is False
    assert s["required"] == ["declines", "points", *list(rules.CHECKS)[1:], "reason"]
    assert set(s["properties"]) == set(s["required"])
    for check, options in rules.CHECKS.items():
        assert s["properties"][check] == {"type": "string", "enum": list(options)}
    points = s["properties"]["points"]
    assert points["minItems"] == points["maxItems"] == 3
    assert points["items"] == {"type": "string", "enum": list(rules.POINT_MARKS)}
    assert s["properties"]["reason"] == {"type": "string"}


def test_to_checks_declines_forces_skipped():
    parsed = valid(2, declines="yes", core_wrong="yes", grounded="none", hallucination="minor")
    checks = llm_rater.to_checks(parsed, 2)
    assert checks["points"] == ["missing", "missing"]
    assert {c: checks[c] for c in rules.SKIPPED_WHEN_DECLINING} == rules.SKIPPED_WHEN_DECLINING
    assert "reason" not in checks
    assert checks["answers_question"] == "yes"


@pytest.mark.parametrize(
    "parsed",
    [
        valid(2, grounded="most"),  # option outside the list
        valid(2, points=["covered"]),  # wrong number of key points
        valid(2, points=["covered", "partly"]),
        {k: v for k, v in valid(2).items() if k != "wordy"},
        valid(2, extra="x"),
        valid(2, reason=None),
    ],
)
def test_to_checks_refuses_invalid_answers(parsed):
    with pytest.raises(ValueError):
        llm_rater.to_checks(parsed, 2)


def test_messages_have_no_strategy():
    item = {
        "code": "Q001-A",
        "question_id": "Q001",
        "question": "How do retries work?",
        "reference_answer": "Set `retries`.",
        "answer": "Strategy C1, C2 or C3 do not matter here.",
        "excerpts": ["Excerpt one.", "Excerpt two."],
    }
    msgs = llm_rater.messages(item, ["Set retries", "Per test"])
    assert [m["role"] for m in msgs] == ["system", "user"]
    text = "\n".join(m["content"] for m in msgs).replace(item["answer"], "")
    for word in ("C1", "C2", "C3", "strategy", "Strategy", "Q001-A"):
        assert word not in text
    user = msgs[1]["content"]
    for part in (item["question"], item["reference_answer"], "1. Set retries", "2. Per test"):
        assert part in user
    assert user.index("Excerpt one.") < user.index("Excerpt two.") < user.index(item["answer"])


def test_system_prompt_uses_the_app_wording():
    from config import RUBRIC_CHECK_HELP, RUBRIC_CHECK_QUESTIONS, RUBRIC_POINT_HELP

    system = llm_rater.messages(
        {"question": "q", "reference_answer": "r", "answer": "a", "excerpts": ["e"]}, ["p"]
    )[0]["content"]
    for text in [*RUBRIC_CHECK_QUESTIONS.values(), *RUBRIC_CHECK_HELP.values(), RUBRIC_POINT_HELP]:
        assert text in system


def test_app_imports_the_wording_from_config():
    """The app (which runs its page on import) takes the wording from config, never its own."""
    from config import ROOT, RUBRIC_CHECK_QUESTIONS, RUBRIC_POINT_HELP

    source = (ROOT / "app" / "scoring_page.py").read_text(encoding="utf-8")
    for name in (
        "RUBRIC_CHECK_QUESTIONS",
        "RUBRIC_CONTROL_QUESTIONS",
        "RUBRIC_POINT_HELP",
        "RUBRIC_CHECK_HELP",
    ):
        assert name in source
    assert RUBRIC_CHECK_QUESTIONS["declines"] not in source
    assert RUBRIC_POINT_HELP[:40] not in source


def test_run_writes_sheet_derived_from_checks(pilot):
    client = FakeOpenAI(reply=lambda n, call: valid(n, points=["missing"] * n, wordy="yes"))
    record = llm_rater.run(pilot, client=client)
    checks, sheet = outputs(pilot)
    assert [r["code"] for r in checks] == [r["code"] for r in sheet] == SCORING_CODES
    for c, s in zip(checks, sheet, strict=True):
        assert c["rules_version"] == RUBRIC_RULES_VERSION
        values = rules.derive(rules.from_row(c)[1])
        assert {k: int(s[k]) for k in RUBRIC_CRITERIA} == values
        assert s["question_id"] == c["code"].split("-")[0] and s["notes"] == ""
    assert record["step"] == "llm_rater" and record["answers"] == 6
    stored = latest_run(pilot["runs_file"], "llm_rater", "C1,C2,C3")
    assert stored == record
    assert stored["outputs_sha256"] == {
        name: sha256_of(pilot["out_dir"] / name)
        for name in ("scoring_checks.csv", "scoring_sheet.csv", "llm_rater_journal.jsonl")
    }
    assert set(stored["inputs_sha256"]) == {"scoring_items.jsonl", "key_points.csv"}
    assert stored["prompt_tokens"] == 6 * 500 and stored["completion_tokens"] == 6 * 60
    assert stored["cost_usd"] > 0
    assert stored["model"] == LLM_RATER_MODEL and stored["model_reported"] == "gpt-6-sol-x"
    assert stored["sessions"] == 1 and stored["aborts"] == 0
    for key in ("git_commit", "git_dirty", "session_commits", "http_errors", "prompts_sha256"):
        assert key in stored
    # Jonas' own files stay untouched
    assert read_csv(pilot["checks_file"], rules.CHECKS_HEADER) == []


def test_run_sends_the_pinned_settings_and_a_strict_schema(pilot):
    client = FakeOpenAI()
    llm_rater.run(pilot, client=client)
    request = client.requests[0]
    assert request["model"] == LLM_RATER_MODEL
    assert request["temperature"] == LLM_RATER_TEMPERATURE
    assert request["reasoning_effort"] == LLM_RATER_REASONING_EFFORT
    assert request["max_completion_tokens"] == LLM_RATER_MAX_TOKENS
    assert request["seed"] == LLM_RATER_SEED
    fmt = request["response_format"]
    assert fmt["type"] == "json_schema" and fmt["json_schema"]["strict"] is True
    assert fmt["json_schema"]["schema"] == llm_rater.schema(1)  # H01-B has one key point


def test_run_scope_all(pilot):
    client = FakeOpenAI()
    llm_rater.run(pilot, client=client)
    assert len(client.requests) == len(SCORING_CODES)


def test_run_scope_sample_only_36(pilot, monkeypatch):
    """Scope "sample": only the drawn questions (36 answers in the main run; here H01)."""
    monkeypatch.setattr(llm_rater, "LLM_RATER_SCOPE", "sample")
    client = FakeOpenAI()
    record = llm_rater.run(pilot, client=client)
    checks, sheet = outputs(pilot)
    assert [r["code"] for r in sheet] == [c for c in SCORING_CODES if c.startswith("H01")]
    assert len(client.requests) == 3 and record["answers"] == 3
    assert record["scope"] == "sample"
    assert "second_rater_sample.csv" in record["inputs_sha256"]


def test_run_scope_sample_needs_the_draw_record(pilot, monkeypatch):
    monkeypatch.setattr(llm_rater, "LLM_RATER_SCOPE", "sample")
    write_csv(pilot["sample_file"], second_rater.SAMPLE_HEADER, [])  # changed after the draw
    client = FakeOpenAI()
    with pytest.raises(RuntimeError, match="second_rater_sample.csv"):
        llm_rater.run(pilot, client=client)
    assert client.requests == []


def test_run_resumes_from_journal_without_calls(pilot):
    with pytest.raises(ConnectionError):
        llm_rater.run(pilot, client=FakeOpenAI(fail_at=6))
    assert not (pilot["out_dir"] / "scoring_checks.csv").exists()
    assert journal(pilot)[-1]["kind"] == "abort"
    again = FakeOpenAI()
    record = llm_rater.run(pilot, client=again)
    assert len(again.requests) == 1
    assert record["sessions"] == 2 and record["aborts"] == 1
    items = [e for e in journal(pilot) if e["kind"] == "item"]
    assert [e["code"] for e in items] == SCORING_CODES
    assert all("response" in e and "reason" not in e for e in items)
    assert json.loads(items[0]["response"]["content"])["reason"] == "Covers the core point."
    # once written, a third run calls nothing and refuses to overwrite
    with pytest.raises(FileExistsError):
        llm_rater.run(pilot, client=FakeOpenAI(fail_at=1))


def test_outputs_rebuilt_from_journal_with_zero_calls(pilot):
    llm_rater.run(pilot, client=FakeOpenAI())
    first = outputs(pilot)
    for name in ("scoring_checks.csv", "scoring_sheet.csv"):
        (pilot["out_dir"] / name).unlink()
    again = FakeOpenAI()
    llm_rater.run(pilot, client=again)
    assert again.requests == [] and outputs(pilot) == first


def test_run_aborts_on_invalid_option(pilot):
    bad = FakeOpenAI(reply=lambda n, call: valid(n, grounded="most") if call == 2 else valid(n))
    with pytest.raises(ValueError, match="grounded"):
        llm_rater.run(pilot, client=bad)
    assert journal(pilot)[-1]["kind"] == "abort"
    assert not pilot["out_dir"].joinpath("scoring_checks.csv").exists()
    assert not pilot["out_dir"].joinpath("scoring_sheet.csv").exists()
    # the journaled answer is never discarded: every restart stops at it again (ADR 0050)
    again = FakeOpenAI()
    with pytest.raises(ValueError, match="grounded"):
        llm_rater.run(pilot, client=again)
    assert again.requests == []
    assert [e["kind"] for e in journal(pilot)].count("abort") == 2


def test_run_aborts_on_cut_off_answer(pilot):
    with pytest.raises(RuntimeError, match="finish_reason"):
        llm_rater.run(pilot, client=FakeOpenAI(finish_reason="length"))
    assert journal(pilot)[-1]["kind"] == "abort"
    assert not pilot["out_dir"].joinpath("scoring_sheet.csv").exists()


def test_run_aborts_when_the_model_changes(pilot):
    client = FakeOpenAI()
    stamps = iter([1, 2])
    client.retrieve = lambda model: SimpleNamespace(id=model, created=next(stamps))
    client.models = SimpleNamespace(retrieve=client.retrieve)
    with pytest.raises(RuntimeError, match="changed"):
        llm_rater.run(pilot, client=client)
    assert not pilot["out_dir"].joinpath("scoring_sheet.csv").exists()


def test_run_refuses_unfrozen_key_points(pilot):
    pilot["key_points_file"].write_text("question_id,point,text\nH01,1,Changed\n", encoding="utf-8")
    client = FakeOpenAI()
    with pytest.raises(RuntimeError, match="frozen"):
        llm_rater.run(pilot, client=client)
    assert client.requests == []
    assert not pilot["out_dir"].exists()


def test_run_refuses_a_journal_with_other_settings(pilot, monkeypatch):
    with pytest.raises(ConnectionError):
        llm_rater.run(pilot, client=FakeOpenAI(fail_at=2))
    monkeypatch.setattr(llm_rater, "LLM_RATER_SCOPE", "sample")
    client = FakeOpenAI()
    with pytest.raises(RuntimeError, match="other settings"):
        llm_rater.run(pilot, client=client)
    assert client.requests == []


def test_main_requires_clean_tree(monkeypatch):
    def dirty():
        raise RuntimeError("uncommitted changes")

    monkeypatch.setattr("run_log.require_clean_tree", dirty)
    monkeypatch.setattr(llm_rater, "run", lambda *a, **k: pytest.fail("ran"))
    with pytest.raises(RuntimeError, match="uncommitted"):
        llm_rater.main([])


def test_main_pilot_set_skips_the_tree_check(pilot, monkeypatch):
    seen = {}
    monkeypatch.setattr("run_log.require_clean_tree", lambda: pytest.fail("checked"))
    monkeypatch.setattr(llm_rater, "run", lambda p, client=None: seen.update(p=p) or {"answers": 0})
    llm_rater.main(["--set", str(pilot["out_dir"].parent)])
    assert seen["p"] == pilot


# --- control K0 (ADR 0041, 0051) ---------------------------------------------------------------

PROMPTS_SHA256_C1_C3 = "1e6468da61459fdbbfdee91122d4258dd0f26bcc4fdd06bf967690fac72e54c9"


def valid_control(n: int, **override) -> dict:
    answer = {k: v for k, v in valid(n).items() if k != "grounded"}
    return answer | override


@pytest.fixture
def k0_set(pilot):
    """The pilot set plus a K0 scaffold (items file and its scaffold record over K0)."""
    from conftest import write_control_set

    from run_log import append_scaffold_run

    folder = pilot["items_file"].parent
    write_control_set(folder)
    items_file = pilot["control_items_file"]
    append_scaffold_run("K0", 2, {items_file.name: sha256_of(items_file)}, pilot["runs_file"])
    return pilot


def control_outputs(p: dict) -> tuple[list[dict], list[dict]]:
    from control_k0 import CONTROL_SHEET_HEADER

    checks = read_csv(p["out_dir"] / "scoring_checks_control.csv", rules.checks_header(True))
    sheet = read_csv(p["out_dir"] / "scoring_sheet_control.csv", CONTROL_SHEET_HEADER)
    return checks, sheet


def test_control_schema_has_no_grounded():
    s = llm_rater.schema(2, control=True)
    assert "grounded" not in s["properties"]
    assert set(s["required"]) == {"points", *rules.CONTROL_CHECKS, "reason"}


def test_control_messages_have_no_excerpts():
    from config import LLM_RATER_CONTROL_SYSTEM_PROMPT

    item = {"question": "q?", "reference_answer": "r", "answer": "a", "excerpts": []}
    msgs = llm_rater.messages(item, ["p"], control=True)
    assert msgs[0] == {"role": "system", "content": LLM_RATER_CONTROL_SYSTEM_PROMPT}
    user = msgs[1]["content"]
    assert "## Reference answer" in user and "## Answer" in user
    assert "## Excerpts" not in user


def test_control_prompt_uses_k0_wording():
    from config import (
        LLM_RATER_CONTROL_SYSTEM_PROMPT,
        RUBRIC_CHECK_QUESTIONS,
        RUBRIC_CONTROL_QUESTIONS,
    )

    assert RUBRIC_CONTROL_QUESTIONS["hallucination"] in LLM_RATER_CONTROL_SYSTEM_PROMPT
    assert RUBRIC_CONTROL_QUESTIONS["declines"] in LLM_RATER_CONTROL_SYSTEM_PROMPT
    assert RUBRIC_CHECK_QUESTIONS["grounded"] not in LLM_RATER_CONTROL_SYSTEM_PROMPT


def test_control_declines_takes_fixed_values():
    parsed = valid_control(2, declines="yes", core_wrong="yes", hallucination="minor")
    checks = llm_rater.to_checks(parsed, 2, control=True)
    expected = rules.declined({k: v for k, v in parsed.items() if k != "reason"}, 2, control=True)
    assert checks == expected
    assert "reason" not in checks and "grounded" not in checks


def test_c1_c3_run_unchanged():
    assert llm_rater.prompts_sha256() == PROMPTS_SHA256_C1_C3
    assert llm_rater.prompts_sha256(control=True) != PROMPTS_SHA256_C1_C3


def test_run_control_writes_k0_files_and_record(k0_set):
    client = FakeOpenAI(reply=lambda n, call: valid_control(n, wordy="yes"))
    record = llm_rater.run(k0_set, client=client, control=True)
    checks, sheet = control_outputs(k0_set)
    assert [r["code"] for r in checks] == [r["code"] for r in sheet] == ["H01-K0", "H02-K0"]
    from config import CONTROL_CRITERIA

    for c, s in zip(checks, sheet, strict=True):
        values = rules.derive_control(rules.from_row(c, control=True)[1])
        assert {k: int(s[k]) for k in CONTROL_CRITERIA} == values and s["notes"] == ""
    assert len(client.requests) == 2
    assert (
        "grounded"
        not in client.requests[0]["response_format"]["json_schema"]["schema"]["properties"]
    )
    assert record["step"] == "llm_rater_control" and record["strategy"] == "K0"
    assert record["answers"] == 2 and record["control"] is True
    stored = latest_run(k0_set["runs_file"], "llm_rater_control", "K0")
    assert stored == record
    assert stored["outputs_sha256"] == {
        name: sha256_of(k0_set["out_dir"] / name)
        for name in (
            "scoring_checks_control.csv",
            "scoring_sheet_control.csv",
            "llm_rater_control_journal.jsonl",
        )
    }
    # the C1-C3 outputs are not touched
    assert not (k0_set["out_dir"] / "scoring_checks.csv").exists()


def test_run_control_needs_k0_scaffold(pilot):
    client = FakeOpenAI()
    with pytest.raises(RuntimeError):
        llm_rater.run(pilot, client=client, control=True)
    assert client.requests == []


def test_run_control_needs_scaffold_record(pilot):
    from conftest import write_control_set

    write_control_set(pilot["items_file"].parent)  # items, but no scaffold record
    client = FakeOpenAI()
    with pytest.raises(RuntimeError):
        llm_rater.run(pilot, client=client, control=True)
    assert client.requests == []


def test_run_control_refuses_changed_items(k0_set):
    with k0_set["control_items_file"].open("a", encoding="utf-8") as f:
        f.write("\n")
    client = FakeOpenAI()
    with pytest.raises(RuntimeError):
        llm_rater.run(k0_set, client=client, control=True)
    assert client.requests == []
