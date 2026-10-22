import importlib.util

import pytest

from config import (
    CONTROL_RETRIEVED_FILE,
    GROUND_TRUTH_FILE,
    PILOT_RUNS_FILE_NAME,
    QUERY_EMBEDDINGS_FILE,
    QUESTIONS_FILE,
    RETRIEVED_RESULTS_FILE,
    ROOT,
)


def load_probe():
    spec = importlib.util.spec_from_file_location(
        "difficulty_probe", ROOT / "scripts" / "difficulty_probe.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_set_dir_is_required():
    with pytest.raises(SystemExit, match="SET_DIR"):
        load_probe().pilot_dir(["difficulty_probe.py"])


def test_a_named_pilot_set_is_resolved_from_the_repo_root():
    probe = load_probe()
    assert probe.pilot_dir(["difficulty_probe.py", "data/pilot/hard"]) == ROOT / "data/pilot/hard"


def test_pilot_file_names_come_from_the_config(tmp_path):
    files = load_probe().set_files(tmp_path)
    assert files == {
        "questions_file": tmp_path / QUESTIONS_FILE.name,
        "ground_truth_file": tmp_path / GROUND_TRUTH_FILE.name,
        "query_file": tmp_path / QUERY_EMBEDDINGS_FILE.name,
        "runs_file": tmp_path / PILOT_RUNS_FILE_NAME,
        "out_file": tmp_path / RETRIEVED_RESULTS_FILE.name,
        "control_out_file": tmp_path / CONTROL_RETRIEVED_FILE.name,
    }
