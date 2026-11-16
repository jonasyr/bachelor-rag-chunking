import json

import pytest

from journal import Journal


def lines(path):
    return [json.loads(x) for x in path.read_text().splitlines()]


def test_a_new_journal_starts_with_its_settings_and_a_session(tmp_path):
    path = tmp_path / "j.jsonl"
    Journal(path, {"step": "generate", "seed": 1})
    kinds = [e["kind"] for e in lines(path)]
    assert kinds == ["start", "session"]
    assert lines(path)[0]["seed"] == 1


def test_a_reopened_journal_keeps_its_items_and_counts_the_session(tmp_path):
    path = tmp_path / "j.jsonl"
    first = Journal(path, {"step": "x"})
    first.append({"kind": "item", "n": 1})
    second = Journal(path, {"step": "x"})
    assert [e["n"] for e in second.of("item")] == [1]
    assert second.of("session")[-1]["resumed_entries"] == 1


def test_other_settings_are_never_continued(tmp_path):
    path = tmp_path / "j.jsonl"
    Journal(path, {"step": "x", "seed": 1})
    with pytest.raises(RuntimeError, match="differs in seed"):
        Journal(path, {"step": "x", "seed": 2})


def test_a_torn_last_line_is_dropped_and_the_rest_kept(tmp_path):
    path = tmp_path / "j.jsonl"
    j = Journal(path, {"step": "x"})
    j.append({"kind": "item", "n": 1})
    with path.open("a") as f:
        f.write('{"kind": "item", "n": 2')  # a write cut off by a kill
    again = Journal(path, {"step": "x"})
    assert [e["n"] for e in again.of("item")] == [1]
    assert all(lines(path))  # the file is valid JSONL again


def test_a_broken_line_inside_is_refused(tmp_path):
    path = tmp_path / "j.jsonl"
    j = Journal(path, {"step": "x"})
    j.append({"kind": "item"})
    text = path.read_text().splitlines()
    text.insert(1, "{broken")
    path.write_text("\n".join(text) + "\n")
    with pytest.raises(ValueError, match="line 2"):
        Journal(path, {"step": "x"})


def test_abort_records_the_error(tmp_path):
    path = tmp_path / "j.jsonl"
    j = Journal(path, {"step": "x"})
    j.abort(ConnectionError("down"), answers_received=3)
    last = lines(path)[-1]
    assert last["kind"] == "abort" and last["error"] == "ConnectionError: down"
    assert last["answers_received"] == 3
